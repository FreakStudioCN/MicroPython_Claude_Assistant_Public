#!/usr/bin/env python3
# daemon/smoke.py — V1 装机后烟测
#
# 验证 daemon 在 127.0.0.1:57320 可达、能消费 v2 envelope。
# 不验证 BLE 是否真连上 ESP32（那个由 daemon log + 用户肉眼确认）。
#
# 用法：
#   uv run claude-buddy-smoke
#
# Exit code:
#   0 — daemon 接受了两条 envelope
#   1 — daemon 不可达 / 推送失败 / 协议异常

import json
import socket
import sys
import time

HOST = "127.0.0.1"
PORT = 57320
CONNECT_TIMEOUT = 0.5
RECV_TIMEOUT = 1.0


def _push(envelope: dict):
    """同步推一条 envelope，等 daemon 回应。返回 daemon 回的 dict，失败返回 None。

    §A-5: 之前只 bool 返回"daemon 是否回合法 JSON"。但 daemon 的异常 handler
    （ble_daemon._handle_client）也会回合法 JSON `{"ok": True, "error": "..."}`，
    smoke 看不出区别——装机决策树最后一步靠 smoke 兜底，宽松等于装机失败也"成功"。
    改成返回 dict 让 main() 按 envelope 类型校验预期字段。
    """
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
                return None
            return json.loads(buf.decode("utf-8"))
    except Exception as e:
        print(f"[smoke] push failed: {e}", file=sys.stderr)
        return None


def main() -> None:
    print(f"[smoke] probing daemon at {HOST}:{PORT} ...")

    sid = "smoke-test-session"

    envelope_start = {
        "type": "event",
        "v": 2,
        "event": {
            "kind": "tool_start",
            "tool": "Bash",
            "tool_category": "exec",
            "summary": "smoke test ping",
            "tool_use_id": "smoke-1",
            "needs_approval": False,
            "risk_level": "safe",
        },
        "generic": {
            "session_id": sid,
            "cwd": "",
            "hook_event_name": "PreToolUse",
            "transcript_path": "",
            "permission_mode": "",
        },
    }

    envelope_done = {
        "type": "event",
        "v": 2,
        "event": {
            "kind": "tool_done",
            "tool": "Bash",
            "tool_category": "exec",
            "duration_ms": 100,
            "tool_use_id": "smoke-1",
            "interrupted": False,
        },
        "generic": {
            "session_id": sid,
            "cwd": "",
            "hook_event_name": "PostToolUse",
            "transcript_path": "",
            "permission_mode": "",
        },
    }

    # §A-5: 校验 daemon 回的就是 _handle_envelope 的预期字段，
    # 不是异常 handler 的 {"ok": True, "error": "..."} 兜底回包。
    resp = _push(envelope_start)
    if resp is None or "error" in resp or resp.get("decision") != "once":
        print(f"[smoke] FAIL — tool_start unexpected response: {resp}")
        sys.exit(1)
    print("[smoke] tool_start accepted")

    time.sleep(0.5)

    resp = _push(envelope_done)
    if resp is None or "error" in resp or not resp.get("ok"):
        print(f"[smoke] FAIL — tool_done unexpected response: {resp}")
        sys.exit(1)
    print("[smoke] tool_done accepted")

    print("[smoke] OK — daemon up and consuming envelopes")
    sys.exit(0)


if __name__ == "__main__":
    main()
