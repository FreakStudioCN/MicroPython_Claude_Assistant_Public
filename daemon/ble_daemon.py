#!/usr/bin/env python3
# ble_daemon.py —— 长驻 BLE 桥接守护进程 (v6 纯展示版)
#
# 输入: hook_bridge.py 通过 TCP 57320 推 v2 envelope
#       {type:"event", v:2, event:{kind, ...}, generic:{session_id, ...}}
# 输出: 翻译为 protocol.py v6 精简 wire（1-5 BLE chunks）
#       {"ss":[{"n":"proj","s":"I","slot":"cd501167"}]}                    → 2 chunks
#       {"ss":[{"n":"proj","s":"W","m":"Bash","slot":"cd501167"}]}         → 3 chunks
#       {"ss":[{"n":"proj","s":"W","m":"Read: main.py","slot":"cd501167"}]} → 3 chunks
#       {"ss":[{"n":"proj","s":"W","m":"Bash: git log --oneline --graph","slot":"cd501167"}]} → 5 chunks
#       状态码: I=IDLE W=WORKING P=PENDING E=ERROR C=CELEBRATE
#       消息长度: m 字段最长 60 字符（设备端跑马灯滚动显示）
#       通过 BLE NUS 写到 ESP32
#
# v6 变化: wire 新增 slot 字段，修复槽位漂移 bug
#   - 每个 session entry 带 slot 字段（SID 去连字符后取后 8 位）
#   - device 端按 slot_id 而非数组下标映射槽位
#   - session 沉默重连后回到原槽位，历史记录不误清
#
# 状态机: 每个 session_id 独立 _Session 对象
#
# 推断兜底 (Stop hook 不冒,只能从沉默期推):
#   session._tools==0 and now-last_activity > threshold
#     → completed=True 短暂 (CELEBRATE 触发后清掉)
#     threshold = 8s if has_subagent else 4s
#
# 5Hz 节流: 状态变化只标 dirty, 单独 _pusher_task 每 200ms 推一次
#
# session 生命周期:
#   活跃 (has_tools or recently_active or special_state) → 纳入 wire sessions 数组
#   30s 无活动且无工具 → 清理
#
# stub 模式: --stub 不启 BLE,_send 改 stdout 打印,用于无设备 e2e 测试

import argparse
import asyncio
import json
import os
import sys
import time
from typing import Optional

try:
    from .transport import BleTransport, TcpDeviceTransport
except ImportError:  # 直接 `python daemon/ble_daemon.py` 跑时
    from transport import BleTransport, TcpDeviceTransport

HOST = "127.0.0.1"
# CLAUDE_BUDDY_PORT 让 e2e 测试用临时端口避开生产 daemon。生产默认 57320。
PORT = int(os.environ.get("CLAUDE_BUDDY_PORT", "57320"))

# 业务常量
PUSH_INTERVAL_S = 0.2          # 5Hz throttle
TASK_COMPLETE_QUIET_S = 4.0    # PostTool 后 N 秒无新 PreTool → 推断 task_complete
COMPLETED_HOLD_S = 2.0         # completed=True 持续秒数 (覆盖 CELEBRATE 3s)
DIZZY_HOLD_S = 3.0             # tool_error / task_error msg="error" 持续秒数
SESSION_ACTIVE_TIMEOUT_S = 10.0  # 超过此时间无活动的 IDLE session 不纳入 wire
SESSION_CLEANUP_S = 10.0         # 超过此时间清理 session 对象

# 设备 wire msg 字段值
MSG_ERROR = "error"
MSG_COMPLETED = "completed"
APPROVE_PREFIX = "approve: "

# ── per-session 状态 ──────────────────────────────────────


class _Session:
    def __init__(self):
        self.tools: dict = {}       # tool_use_id → {tool, category, summary, status, ts}
        self.has_subagent: bool = False
        self.waiting: int = 0
        self.cwd: str = ""
        self.display_name: str = ""
        self.current_error: str = ""
        self.current_interrupted: bool = False
        self.last_activity_ts: float = 0.0
        self.completed_until: float = 0.0
        self.completed_inferred_for_ts: float = 0.0
        self.dizzy_until: float = 0.0
        self.last_tool_start_ts: float = 0.0   # 最近一次 tool_start 时间（保证W至少推一次）
        self.last_stop_ts: float = 0.0          # 最近一次 stop 时间（过滤stop后乱序notification）
        self.turn_active: bool = False          # user_prompt→True, stop→False；无工具时也显示W


_sessions: dict = {}   # session_id → _Session
_dirty = False         # 全局 dirty 标志（pusher 用）

# ── stub 模式 ─────────────────────────────────────────────
_stub = False
_force_offline = False  # --offline 标志：强制 device_online=False，覆盖 stub 的在线假设
_tcp_device = False     # --tcp-device 标志：用 TcpDeviceTransport 替代 BLE

# ── Transport ─────────────────────────────────────────────
_transport: Optional[BleTransport] = None

# ── 业务层全局 ────────────────────────────────────────────
_lock = None
_last_pushed_wire = None       # 最后推送的 wire（pusher 用，防止重复推送）


# ── BLE 回调（业务层处理） ────────────────────────────────────
def _on_transport_connect():
    """BLE 重连成功：有活跃 session 时触发状态推送。"""
    print("[daemon] connected" if _transport.connected() else "")
    if _sessions:
        _mark_dirty()


def _on_transport_disconnect():
    print("[daemon] disconnected, will reconnect...")


async def _send(payload: dict) -> bool:
    """推送 wire JSON（stub 打印 / 走 transport）。返回是否真送出去了。

    v2.2 §A-4: BLE 抖动 / 距离过远 / 设备断电时 ``_transport.send`` 会抛
    ``BleakError`` 或其它 ``Exception``。原代码不接，异常透出会让
    ``_pusher_task`` 退出，再被 ``asyncio.gather`` 拉倒整个 daemon——
    实际表现是用户走出房间几秒回来，桌宠永久不再更新。

    包 try/except：丢这条 payload，warning 后继续 loop，
    transport 自己的重连循环会把 BLE 重新拉回来。

    §A-5: 返回 bool。失败 / 未连接时返回 False，让 ``_pusher_tick`` 不更新
    ``last_pushed_wire``——否则 BLE 重连后状态相同会被 dedup 误吞，
    彻底修复 §A-4 commit message 里那个"走出房间回来桌宠永远不动"场景。
    """
    if _stub:
        print(f"[stub-send] t={time.time():.3f} {json.dumps(payload, ensure_ascii=False)}")
        return True
    if not _transport.connected():
        print(f"[send] skipped (not connected): {payload}")
        return False
    try:
        await _transport.send(payload)
        return True
    except Exception as e:
        # 丢一条 payload，不打断 pusher loop；transport._connect_loop 会重连
        print(f"[send] failed, dropped: {type(e).__name__}: {e}")
        return False


# ── per-session 状态翻译 ───────────────────────────────────

def _get_running_count(sess: _Session) -> int:
    return sum(1 for t in sess.tools.values() if t["status"] == "running")


def _get_current_category(sess: _Session) -> str:
    for t in sess.tools.values():
        if t["status"] == "running":
            return t.get("category", "")
    return ""


def _build_msg(sess: _Session) -> str:
    now = time.time()
    if sess.dizzy_until > now:
        return MSG_ERROR
    if sess.completed_until > now:
        return MSG_COMPLETED
    for t in sess.tools.values():
        if t["status"] == "running":
            summary = t["summary"][:80] if t["summary"] else ""
            return f"{t['tool']}: {summary}" if summary else t["tool"]
    return ""


def _session_to_wire(sid: str, sess: _Session) -> dict:
    now = time.time()
    result = {"n": sess.display_name or "?"}

    # v6 协议：计算 slot 标识（SID 后 8 位）
    compact_sid = sid.replace("-", "")
    result["slot"] = compact_sid[-8:] if len(compact_sid) >= 8 else compact_sid

    if sess.dizzy_until > now:
        result["s"] = "E"
        return result
    if sess.waiting > 0:
        result["s"] = "P"
        return result
    # tools 优先：工具运行时把工具名带在 m 里（panel 形态显示用）。
    # 必须在 turn_active 分支之前，否则 turn_active=True + tools 非空时
    # 提前 return W{无 m}，panel 文字栏看不到当前工具，是 v0.9 前的回归。
    # 同时也必须优先于 C：新 turn 已经在跑工具时，旧 turn 的庆祝不能遮挡真实活动。
    for t in sess.tools.values():
        if t["status"] == "running":
            summary = t.get("summary", "")[:50]
            m = f"{t['tool']}: {summary}" if summary else t["tool"]
            result["s"] = "W"
            result["m"] = m[:60]
            return result
    if sess.completed_until > now:
        result["s"] = "C"
        return result
    # turn_active：user_prompt 到 stop 之间、且当前无工具运行 → W（思考中 / 处理结果中）
    if sess.turn_active:
        result["s"] = "W"
        return result
    # 快速工具保证：tool_start后400ms内至少显示一次W
    if sess.last_tool_start_ts > 0 and (now - sess.last_tool_start_ts) < 0.4:
        result["s"] = "W"
        return result
    result["s"] = "I"
    return result


def _to_device_wire() -> dict:
    now = time.time()
    active = []
    for sid, sess in list(_sessions.items()):
        has_tools = bool(sess.tools)
        recently  = sess.last_activity_ts > 0 and (now - sess.last_activity_ts) < SESSION_ACTIVE_TIMEOUT_S
        special   = sess.completed_until > now or sess.dizzy_until > now
        if has_tools or recently or special or sess.turn_active:
            active.append(_session_to_wire(sid, sess))
    return {"ss": active}


def _display_basename(cwd: str) -> str:
    """设备端显示用的 basename：basename(cwd) 截断到 12 字符。

    同 basename 冲突时由 _generate_display_name 加 session_id 后缀消歧，
    总长仍保持 12 字符以内。
    """
    basename = os.path.basename(cwd) if cwd else "unknown"
    return basename[:12]


def _generate_display_name(session_id: str, cwd: str) -> str:
    """生成 session 显示名（设备端 wire 字段 n）。

    - 无冲突：basename(cwd)[:12]
    - 同 basename 冲突：basename[:7] + "-" + session_id 后 4 位（共 12 字符）

    后缀仅用于显示消歧；session 真正的唯一性靠 session_id，不靠 display name。
    """
    basename = _display_basename(cwd)

    # 检查是否已有同 basename 的 session。即使 cwd 相同，不同 terminal
    # 里的 Claude Code 也需要区分，否则设备端会显示两个同名状态。
    conflict = any(
        sid != session_id and _display_basename(s.cwd) == basename
        for sid, s in _sessions.items()
        if s.display_name
    )

    if conflict:
        compact_sid = session_id.replace("-", "")
        suffix = compact_sid[-4:] if len(compact_sid) >= 4 else compact_sid or session_id
        return f"{basename[:7]}-{suffix}"
    return basename


def _mark_dirty():
    global _dirty
    _dirty = True


def _retire_stale_waiting_sessions(current_sid: str, cwd: str) -> None:
    """A fresh prompt in the same cwd means an old idle/question session was abandoned."""
    if not cwd:
        return
    retired = []
    for sid, old in list(_sessions.items()):
        if sid == current_sid:
            continue
        if old.cwd != cwd:
            continue
        if old.tools or old.turn_active:
            continue
        if old.waiting > 0:
            retired.append(sid)
    for sid in retired:
        del _sessions[sid]
    if retired:
        print(f"[session] retired stale waiting sessions: {retired}")
        _mark_dirty()


def _clear_dirty():
    global _dirty
    _dirty = False


def _enter_error_state(sess: _Session, now: float, hard_reset: bool, error_msg: str, is_interrupt: bool) -> None:
    if hard_reset:
        sess.tools.clear()

    sess.current_error = error_msg[:80] if error_msg else ""
    sess.current_interrupted = is_interrupt
    sess.dizzy_until = now + DIZZY_HOLD_S if not is_interrupt else 0.0
    sess.completed_until = 0.0
    sess.last_tool_start_ts = 0.0
    sess.last_activity_ts = now
    sess.completed_inferred_for_ts = sess.last_activity_ts
    _mark_dirty()


# ── 5Hz 推送 task ──────────────────────────────────────────
async def _pusher_tick(last_pushed_wire):
    global _dirty, _last_pushed_wire

    now = time.time()

    # 清理长期无活动 session（turn_active 期间不清理，防止思考阶段状态丢失）
    for sid in [k for k, s in list(_sessions.items())
                if not s.tools
                and not s.turn_active
                and s.last_activity_ts > 0
                and now - s.last_activity_ts > SESSION_CLEANUP_S
                and s.completed_until <= now
                and s.dizzy_until <= now]:
        del _sessions[sid]

    # completed 到期标 dirty
    for sess in _sessions.values():
        if sess.completed_until > 0 and sess.completed_until <= now:
            if last_pushed_wire:
                for s in last_pushed_wire.get("ss", []):
                    if s.get("s") == "C":
                        _mark_dirty()
                        break
        if sess.dizzy_until > 0 and sess.dizzy_until <= now:
            sess.dizzy_until = 0.0
            sess.current_error = ""
            sess.current_interrupted = False
            if last_pushed_wire:
                for s in last_pushed_wire.get("ss", []):
                    if s.get("s") == "E":
                        _mark_dirty()
                        break
        if (sess.last_tool_start_ts > 0
                and (now - sess.last_tool_start_ts) >= 0.4
                and not sess.tools
                and not sess.turn_active
                and sess.completed_until <= now
                and sess.dizzy_until <= now):
            sess.last_tool_start_ts = 0.0
            if last_pushed_wire:
                for s in last_pushed_wire.get("ss", []):
                    if s.get("s") == "W":
                        _mark_dirty()
                        break

    if _dirty:
        # 先清标志再捕获状态：await _send() 期间若有新事件调用 _mark_dirty()，
        # 下一 tick 能正确重新推送，避免 stop/tool_done 在 yield 窗口内写入的
        # dirty=True 被 send 返回后的赋值覆盖（§A-6 竞态修复）。
        _dirty = False
        wire = _to_device_wire()
        if wire != last_pushed_wire:
            # §A-5: 只在 _send 真送出去时才记 last_pushed_wire；失败时保持旧值，
            # 下一 tick 即便 wire 没变也会再试（修 §A-4 残留：重连后状态相同被 dedup 误吞）
            if await _send(wire):
                last_pushed_wire = wire
                _last_pushed_wire = wire
            else:
                _dirty = True   # 发送失败，恢复 dirty 等下一 tick 重试
    return last_pushed_wire


async def _pusher_task():
    last_pushed_wire = None
    while True:
        await asyncio.sleep(PUSH_INTERVAL_S)
        last_pushed_wire = await _pusher_tick(last_pushed_wire)


# ── v2 envelope dispatch ───────────────────────────────────
async def _handle_envelope(env: dict) -> dict:
    """根据 event.kind 改对应 session 的状态。返回给 hook_bridge 的 dict。"""
    session_id = env.get("generic", {}).get("session_id", "") or "default"
    sess = _sessions.setdefault(session_id, _Session())

    # 提取 cwd 并生成 display_name（首次）
    if not sess.display_name:
        cwd = env.get("generic", {}).get("cwd", "")
        if cwd:
            sess.cwd = cwd
            sess.display_name = _generate_display_name(session_id, cwd)
            print(f"[session] {session_id!r} → display_name={sess.display_name!r}")

    event = env.get("event") or {}
    kind = event.get("kind", "")
    print(f"[req v2] session={session_id!r} kind={kind!r}")

    now = time.time()

    if kind == "tool_start":
        tool = event.get("tool", "")
        tool_use_id = event.get("tool_use_id", "")
        category = event.get("tool_category", "")
        summary = event.get("summary", "")

        if not tool_use_id:
            print(f"[warn] tool_start missing tool_use_id, ignoring")
            return {"decision": "once"}

        needs_approval = event.get("needs_approval", False)
        sess.tools[tool_use_id] = {
            "tool": tool,
            "category": category,
            "summary": summary,
            "status": "running",
            "ts": now,
            "needs_approval": needs_approval,
        }
        if needs_approval:
            sess.waiting += 1
            print(f"[approval] session={session_id!r} waiting={sess.waiting}")
        sess.last_activity_ts = now
        sess.last_tool_start_ts = now  # 保证快速工具W至少推一次
        # 新 turn 首次真实工作 → 抛弃上一轮的庆祝（避免 tool_done 后 C 闪回）
        sess.completed_until = 0.0
        _mark_dirty()
        return {"decision": "once"}

    if kind == "tool_done":
        tool_use_id = event.get("tool_use_id", "")
        interrupted = event.get("interrupted", False)

        if tool_use_id in sess.tools:
            if sess.tools[tool_use_id].get("needs_approval") and sess.waiting > 0:
                sess.waiting -= 1
                print(f"[approval] session={session_id!r} done, waiting={sess.waiting}")
            del sess.tools[tool_use_id]

        sess.last_activity_ts = now

        if len(sess.tools) == 0:
            sess.current_error = ""
            sess.current_interrupted = interrupted
            sess.waiting = 0  # 所有工具完成，待审批状态已消化

        _mark_dirty()
        return {"ok": True}

    if kind == "tool_error":
        tool_use_id = event.get("tool_use_id", "")
        error_msg = event.get("error_msg", "")
        is_interrupt = event.get("is_interrupt", False)

        if tool_use_id in sess.tools:
            if sess.tools[tool_use_id].get("needs_approval") and sess.waiting > 0:
                sess.waiting -= 1
                print(f"[approval] session={session_id!r} error, waiting={sess.waiting}")
            del sess.tools[tool_use_id]

        _enter_error_state(sess, now, hard_reset=False, error_msg=error_msg, is_interrupt=is_interrupt)
        return {"ok": True}

    if kind == "tool_batch_done":
        sess.last_activity_ts = now
        _mark_dirty()
        return {"ok": True}

    if kind == "notification":
        ntype = event.get("notification_type")
        if ntype in ("permission_prompt", "elicitation_dialog"):
            # stop后1秒内的permission_prompt乱序notification忽略。
            if ntype == "permission_prompt" and sess.last_stop_ts > 0 and (now - sess.last_stop_ts) < 1.0:
                return {"ok": True}
            if sess.waiting <= 0:
                sess.waiting = 1
            print(f"[approval] session={session_id!r} {ntype}, waiting={sess.waiting}")
            sess.last_activity_ts = now
            # 新 turn 等审批/用户输入也算真实工作 → 抛弃上一轮的庆祝
            sess.completed_until = 0.0
            _mark_dirty()
        elif ntype == "idle_prompt":
            # idle_prompt 只是 Claude Code 进入空闲、等待下一条用户输入。
            # 它不是选择题/审批本身，不能常驻 P，否则普通完成后会卡 P。
            print(f"[idle] session={session_id!r} idle_prompt ignored")
        return {"ok": True}

    if kind == "user_prompt":
        _retire_stale_waiting_sessions(session_id, sess.cwd)
        # 不清 completed_until：让上一轮 stop 的 C 状态自然过期（2s），避免连发 prompt
        # 把庆祝动画截短。优先级链 C(completed) > W(turn_active) 保证 C 期间不被 W 抢走。
        sess.last_activity_ts = now
        sess.completed_inferred_for_ts = now
        sess.has_subagent = False
        sess.current_error = ""
        sess.current_interrupted = False
        sess.waiting = 0
        sess.turn_active = True
        _mark_dirty()
        return {"ok": True}

    if kind == "stop":
        sess.tools.clear()
        sess.waiting = 0
        sess.turn_active = False
        sess.last_stop_ts = now
        sess.last_activity_ts = now
        if sess.dizzy_until < now and not sess.current_error:
            sess.completed_until = now + COMPLETED_HOLD_S
            sess.completed_inferred_for_ts = now
            _mark_dirty()
        return {"ok": True}

    if kind == "session_end":
        if sess.last_stop_ts > 0 and (now - sess.last_stop_ts) < 10.0:
            return {"ok": True}
        sess.tools.clear()
        sess.waiting = 0
        sess.turn_active = False
        sess.last_stop_ts = now
        sess.last_activity_ts = now
        if sess.dizzy_until < now and not sess.current_error:
            sess.completed_until = now + COMPLETED_HOLD_S
            sess.completed_inferred_for_ts = now
            _mark_dirty()
        return {"ok": True}

    if kind == "task_error":
        error_msg = event.get("error", "")
        sess.turn_active = False
        sess.waiting = 0
        _enter_error_state(sess, now, hard_reset=True, error_msg=error_msg, is_interrupt=False)
        return {"ok": True}

    if kind == "subagent_start":
        sess.has_subagent = True
        return {"ok": True}

    if kind in ("notification", "unknown"):
        return {"ok": True}

    return {"ok": True}


# ── TCP server ─────────────────────────────────────────────
MAX_ENVELOPE_BYTES = 64 * 1024


async def _handle_client(reader, writer):
    try:
        data = await asyncio.wait_for(reader.read(MAX_ENVELOPE_BYTES), timeout=35)
        env = json.loads(data.decode())
        async with _lock:
            resp = await _handle_envelope(env)
    except Exception as e:
        resp = {"ok": True, "error": str(e)}
    writer.write(json.dumps(resp).encode())
    await writer.drain()
    writer.close()


async def async_main():
    global _lock, _transport
    _lock = asyncio.Lock()
    if _tcp_device:
        _transport = TcpDeviceTransport()
    else:
        _transport = BleTransport()
    server = await asyncio.start_server(_handle_client, HOST, PORT)
    print(f"[daemon] listening on {HOST}:{PORT}  stub={_stub}  tcp_device={_tcp_device}")
    async with server:
        if _stub:
            await asyncio.gather(server.serve_forever(), _pusher_task())
        else:
            await asyncio.gather(
                server.serve_forever(),
                _transport.start(
                    on_recv=lambda msg: None,
                    on_connect=_on_transport_connect,
                    on_disconnect=_on_transport_disconnect,
                ),
                _pusher_task(),
            )


def main() -> None:
    """同步 entrypoint，给 `claude-buddy-daemon` console_script 用。

    console_scripts 入口必须是 sync callable；原 ``async def main()`` 改名为
    ``async_main()``，由本函数 ``asyncio.run`` 包起来。直接 ``python daemon/ble_daemon.py``
    跑也走这里。
    """
    global _stub, _force_offline, _tcp_device

    parser = argparse.ArgumentParser()
    parser.add_argument("--stub", action="store_true",
                        help="跳过 BLE 连接, _send 改 stdout 打印用于 e2e 测试")
    parser.add_argument("--offline", action="store_true",
                        help="强制模拟设备离线（覆盖 stub 在线假设），用于离线审批测试")
    parser.add_argument("--tcp-device", action="store_true",
                        help="用 TCP 57321 替代 BLE，配合 scripts/sim_device.py 使用")
    parser.add_argument("--log", type=str, default=None,
                        help="日志文件路径（默认：普通模式→logs/daemon.log，--tcp-device→scripts/sim_device/logs/daemon.log）")
    args = parser.parse_args()
    _stub = args.stub
    _force_offline = args.offline
    _tcp_device = args.tcp_device

    _ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if args.tcp_device:
        _default_log_dir = os.path.join(_ROOT, "scripts", "sim_device", "logs")
    else:
        _default_log_dir = os.path.join(_ROOT, "logs")
    os.makedirs(_default_log_dir, exist_ok=True)
    log_path = args.log or os.path.join(_default_log_dir, "daemon.log")

    class TeeOutput:
        def __init__(self, file_path, original_stream):
            self.file = open(file_path, 'w', encoding='utf-8', buffering=1)
            self.original = original_stream

        def write(self, data):
            self.original.write(data)
            self.file.write(data)
            self.file.flush()

        def flush(self):
            self.original.flush()
            self.file.flush()

    sys.stdout = TeeOutput(log_path, sys.stdout)
    sys.stderr = TeeOutput(log_path.replace('.log', '_err.log'), sys.stderr)
    print(f"[daemon] 日志文件: {log_path}")

    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n[daemon] bye")
        sys.exit(0)


if __name__ == "__main__":
    main()
