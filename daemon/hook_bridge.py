#!/usr/bin/env python3
# hook_bridge.py —— Claude Code hook 上位机接收层 (v5 纯展示版)
#
# 链路: Claude Code hook → stdin → 字段规整 → v2 envelope → TCP 57320
#       → ble_daemon.py → BLE → ESP32
#
# v5 变化: 设备仅展示状态，不参与审批
#   - 所有 hook 事件推送到 daemon → 设备显示状态
#   - 审批由 Claude Code 自己在终端 UI 完成
#   - hook_bridge 始终返回 {}，不干预审批流程
#
# 字段规整覆盖 8 类已观测真实触发的 hook (依据 ~/.claude_buddy/probe.jsonl 实测):
#   PreToolUse / PostToolUse / PostToolUseFailure / PostToolBatch /
#   SubagentStart / Notification / UserPromptSubmit / StopFailure
# 其余 21 类 settings.json 注册了但当前 Claude Code 版本未冒,fallback 走 unknown.
#
# 阻塞语义: 无阻塞，所有 hook 立即返回 {}。
# daemon 不可达时 fail-open (返回 {}),保证硬件离线不会拖死 Claude Code.

import json
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path

# 导入风险分级配置（package 模式优先，script 模式 fallback，都失败用内置默认）
try:
    from .risk_config import (
        CRITICAL_PATHS, CRITICAL_BASH_PATTERNS,
        SAFE_TOOLS, APPROVAL_TOOLS
    )
except ImportError:
    try:
        from risk_config import (
            CRITICAL_PATHS, CRITICAL_BASH_PATTERNS,
            SAFE_TOOLS, APPROVAL_TOOLS
        )
    except ImportError:
        # 内置默认（risk_config.py 不存在时）
        CRITICAL_PATHS = {".git/config", ".git/hooks", ".env", "credentials.json",
                          "id_rsa", "id_ed25519", ".ssh/", "/etc/", "C:\\Windows\\"}
        CRITICAL_BASH_PATTERNS = [
            "git branch -D", "git push --force", "git push -f", "git reset --hard",
            "rm -rf", "rm -fr", "dd if=", "> /dev/", "mkfs", "fdisk", "format ",
            "del /s", "rmdir /s"
        ]
        SAFE_TOOLS = {"Read", "Glob", "Grep", "WebFetch", "WebSearch"}
        APPROVAL_TOOLS = {"Bash", "Write", "Edit"}

HOST = "127.0.0.1"
# CLAUDE_BUDDY_PORT 让 e2e 测试用临时端口避开生产 daemon。生产默认 57320。
PORT = int(os.environ.get("CLAUDE_BUDDY_PORT", "57320"))
# v2.2 §A-2: 缩短 timeout, 让 daemon 死的时候不卡 CLI 秒级
CONNECT_TIMEOUT = 0.3     # localhost connect 应该 ms 级
RECV_TIMEOUT = 0.5        # daemon 立刻回 JSON，0.5s 远超正常
MAX_STDIN_BYTES = 1 << 20  # 1MB hook payload 上限,防超大 tool_response 内存炸

# v2.2 §A-2: daemon 装在用户本地 `~/.claude-buddy/`（独立于 plugin 生命周期）。
# 用 `Path.home()` 运行时解析——不依赖 Claude Code 对 `${HOME}` 的展开行为
# （后者不在官方保证列表里，github issue #46889）。
DAEMON_ROOT = Path.home() / ".claude-buddy"
# NotebookEdit 归 edit 类但不需审批：notebook 编辑操作危险性低于直接文件写入，
# 且 notebook cell 输出可在 Claude Code UI 中直接查看，无需额外硬件确认。

def _classify_risk(tool: str, tool_input: dict) -> str:
    """分类操作风险等级：safe（只读）/ normal（可逆写）/ critical（破坏性）。
    设备离线时：safe/normal 自动批准，critical 回退 CLI 提示。
    风险规则可在 risk_config.py 中自定义。"""
    if tool in SAFE_TOOLS:
        return "safe"

    if tool == "Bash":
        cmd = tool_input.get("command", "")
        if any(p in cmd for p in CRITICAL_BASH_PATTERNS):
            return "critical"
        return "normal"

    if tool in {"Write", "Edit"}:
        path = tool_input.get("file_path", "")
        if any(cp in path for cp in CRITICAL_PATHS):
            return "critical"
        return "normal"

    return "normal"

# ── 5 桶 tool_category (research/hook_to_device_mapping_v1.md) ───
_TOOL_CATEGORY = {
    "Bash":         "exec",
    "Write":        "edit",
    "Edit":         "edit",
    "NotebookEdit": "edit",
    "Read":         "read",
    "Glob":         "read",
    "Grep":         "read",
    "WebFetch":     "web",
    "WebSearch":    "web",
    "Task":         "agent",
    "Subagent":     "agent",
}


def _tool_category(name: str) -> str:
    return _TOOL_CATEGORY.get(name, "other")


def _generic(event: dict) -> dict:
    """v2 envelope 的 generic 字段,所有 hook 通用 5 字段。"""
    return {
        "session_id":      event.get("session_id", ""),
        "cwd":             event.get("cwd", ""),
        "hook_event_name": event.get("hook_event_name", ""),
        "transcript_path": event.get("transcript_path", ""),
        "permission_mode": event.get("permission_mode", ""),
    }


def _trunc(v, n: int) -> str:
    """把 str 截到 n 字, 非 str 返回空串。设备显示用,防长尾敏感数据。"""
    return v[:n] if isinstance(v, str) else ""


def _hint_from_tool_input(tool_input) -> str:
    """从 tool_input 抽一句给设备 LCD 显示的短提示, 80 字以内。
    优先级: command (Bash) > file_path (Read/Edit/Write) > description > 空串。
    没有已知 key 时返回空串而非序列化 dict，防止暴露敏感内容。"""
    if not isinstance(tool_input, dict):
        return ""
    for key in ("command", "file_path", "pattern", "url", "description"):
        v = tool_input.get(key)
        if isinstance(v, str) and v:
            return v[:80]
    return ""


# ── 6 类 normalizer (返回 v2 envelope) ──────────────────
def _normalize_pre_tool(event: dict) -> dict:
    tool = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":           "tool_start",
            "tool":           tool,
            "tool_category":  _tool_category(tool),
            "summary":        _hint_from_tool_input(tool_input),
            "needs_approval": False,
            "tool_use_id":    event.get("tool_use_id", ""),
            "risk_level":     _classify_risk(tool, tool_input),
        },
        "generic": _generic(event),
    }


def _normalize_post_tool(event: dict) -> dict:
    """PostToolUse 仅 success path,失败走 PostToolUseFailure 独立 hook。
    实测 tool_response 无 exit_code 字段,只能据 hook 名区分成功/失败。
    tool_response.interrupted 表示工具正常返回但实际是被用户中断的,需提取。"""
    tool = event.get("tool_name", "")
    tool_response = event.get("tool_response") or {}
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":          "tool_done",
            "tool":          tool,
            "tool_category": _tool_category(tool),
            "duration_ms":   event.get("duration_ms", 0),
            "tool_use_id":   event.get("tool_use_id", ""),
            "interrupted":   bool(tool_response.get("interrupted", False)),
        },
        "generic": _generic(event),
    }


def _normalize_post_tool_fail(event: dict) -> dict:
    err = _trunc(event.get("error", ""), 80)
    tool = event.get("tool_name", "")
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":          "tool_error",
            "tool":          tool,
            "tool_category": _tool_category(tool),
            "error_msg":     err,
            "is_interrupt":  event.get("is_interrupt", False),
            "duration_ms":   event.get("duration_ms", 0),
            "tool_use_id":   event.get("tool_use_id", ""),
        },
        "generic": _generic(event),
    }


def _normalize_post_batch(event: dict) -> dict:
    """一批并行 tool 完成统一发一条;daemon 用作 task_complete 推断的强信号。"""
    calls = event.get("tool_calls") or []
    tools = []
    for c in calls:
        if isinstance(c, dict) and c.get("tool_name"):
            tools.append(c["tool_name"])
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":       "tool_batch_done",
            "batch_size": len(calls),
            "tools":      tools[:8],  # 防设备显示过长
        },
        "generic": _generic(event),
    }


def _normalize_subagent_start(event: dict) -> dict:
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":       "subagent_start",
            "agent_id":   event.get("agent_id", ""),
            "agent_type": event.get("agent_type", ""),
        },
        "generic": _generic(event),
    }


def _normalize_notification(event: dict) -> dict:
    """实测 notification_type 见过 'permission_prompt';其它子类型未观测,字段透传。"""
    msg = _trunc(event.get("message", ""), 80)
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":              "notification",
            "notification_type": event.get("notification_type", ""),
            "message":           msg,
        },
        "generic": _generic(event),
    }


def _normalize_user_prompt(event: dict) -> dict:
    """用户提交 prompt → 强 turn_start 信号,daemon 用作清 idle / 启动 busy 状态。
    prompt 原文截 80 字给设备显示,避免敏感内容长尾。"""
    prompt = _trunc(event.get("prompt", ""), 80)
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":   "user_prompt",
            "prompt": prompt,
        },
        "generic": _generic(event),
    }


def _normalize_stop_failure(event: dict) -> dict:
    """assistant turn 失败 (API timeout / stream error 等)。
    daemon 用作 task_error 信号,设备可显示 dizzy 状态。"""
    err = _trunc(event.get("error", ""), 80)
    last_msg = _trunc(event.get("last_assistant_message", ""), 80)
    return {
        "type": "event",
        "v": 2,
        "event": {
            "kind":                  "task_error",
            "error":                 err,
            "last_assistant_message": last_msg,
        },
        "generic": _generic(event),
    }


def _normalize_stop(event: dict) -> dict:
    return {
        "type": "event",
        "v": 2,
        "event": {"kind": "stop"},
        "generic": _generic(event),
    }


def _normalize_session_end(event: dict) -> dict:
    return {
        "type": "event",
        "v": 2,
        "event": {"kind": "session_end"},
        "generic": _generic(event),
    }


def _normalize_fallback(event: dict) -> dict:
    """未识别 hook (Stop / SessionStart / ... 23 类),daemon 会忽略 kind=unknown。"""
    return {
        "type": "event",
        "v": 2,
        "event": {"kind": "unknown"},
        "generic": _generic(event),
    }


NORMALIZERS = {
    "PreToolUse":         _normalize_pre_tool,
    "PostToolUse":        _normalize_post_tool,
    "PostToolUseFailure": _normalize_post_tool_fail,
    "PostToolBatch":      _normalize_post_batch,
    "SubagentStart":      _normalize_subagent_start,
    "Notification":       _normalize_notification,
    "UserPromptSubmit":   _normalize_user_prompt,
    "StopFailure":        _normalize_stop_failure,
    "Stop":               _normalize_stop,
    "SessionEnd":         _normalize_session_end,
}


def _spawn_daemon_detached() -> None:
    """启动 daemon detached（best effort，失败吞掉）。

    v2.2 §A-2 lite 版：不做 negative cache，不 poll 等 daemon ready——
    本次 hook 直接 fail-open，下一次 hook 时 daemon 已起来就能连上。

    uv 解析顺序：PATH 上的 ``uv`` 优先；找不到则 ``<python> -m uv``。
    Windows 上 ``pip install --user uv`` 把 uv 装到 ``%APPDATA%\\Python\\..\\Scripts``
    通常不在 PATH——但同一 Python 的 site-packages 含 uv 模块，``-m uv`` 仍能跑。
    """
    uv_bin = shutil.which("uv")
    if uv_bin:
        cmd = [uv_bin, "run", "--project", str(DAEMON_ROOT), "claude-buddy-daemon"]
    else:
        cmd = [sys.executable, "-m", "uv", "run",
               "--project", str(DAEMON_ROOT), "claude-buddy-daemon"]
    try:
        if sys.platform == "win32":
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_PROCESS_GROUP = 0x00000200
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
                close_fds=True,
            )
        else:
            subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
    except Exception:
        # 任何失败都吞掉——hook 永远不能阻塞 CLI
        pass


def _call_daemon(envelope: dict) -> dict:
    """同步 socket 调用。daemon 不可达 / 超时 / JSON 错都 fail-open 返回 {}。
    v5: daemon 立即返回，无需长超时等待。
    v2.2 §A-2: 连不上时尝试 spawn daemon detached，本次 fail-open。"""
    try:
        with socket.create_connection((HOST, PORT), timeout=CONNECT_TIMEOUT) as s:
            s.settimeout(RECV_TIMEOUT)
            s.sendall(json.dumps(envelope).encode("utf-8"))
            s.shutdown(socket.SHUT_WR)
            buf = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
            if not buf:
                return {}
            return json.loads(buf.decode("utf-8"))
    except (ConnectionRefusedError, socket.timeout, OSError):
        # daemon 不可达：直接尝试 spawn 拉起来，下次 hook 接力。
        # 用户没装 daemon runtime（~/.claude-buddy/ 不存在）时 spawn 会失败，
        # 静默吞掉——hook 永远不能阻塞 CLI。
        _spawn_daemon_detached()
        return {}
    except Exception:
        return {}


def main():
    # 上限读 1MB:超大 tool_response (例如 Bash 长输出) 不该把 hook_bridge 撑爆,
    # 设备只能显几十字,后面又会再截 80 字,1MB 已经远超有用范围
    raw = sys.stdin.read(MAX_STDIN_BYTES).strip()
    if not raw:
        print(json.dumps({}))
        return
    try:
        event = json.loads(raw)
    except json.JSONDecodeError:
        print(json.dumps({}))
        return

    hook = event.get("hook_event_name", "")
    normalize = NORMALIZERS.get(hook, _normalize_fallback)
    envelope = normalize(event)

    # v5: 所有事件推送到 daemon，让设备显示状态
    # 不干预审批流程，始终返回 {}
    _call_daemon(envelope)
    print(json.dumps({}))


if __name__ == "__main__":
    main()
