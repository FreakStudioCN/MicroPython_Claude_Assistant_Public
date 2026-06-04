"""Claude Buddy daemon package.

Modules:
    ble_daemon       Long-running BLE bridge daemon (TCP 57320 -> BLE).
    hook_bridge      Claude Code / Codex hook entrypoint (stdin -> TCP 57320).
    transport        Transport abstraction (BLE / future Wi-Fi / UART).
    pair_device      Interactive BLE pairing CLI.
    smoke            V1 smoke test: push fake envelope, verify daemon reachable.
    risk_config      Risk classification constants used by hook_bridge.
"""
