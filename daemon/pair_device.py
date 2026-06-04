#!/usr/bin/env python3
# daemon/pair_device.py
# 用户工具：扫描并配对 Claude-Buddy 设备

import asyncio
import json
import os
import sys
from pathlib import Path


def get_config_path() -> Path:
    """获取配置文件路径（跨平台）。"""
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", "~"))
    else:
        base = Path.home() / ".config"
    return base / "claude-buddy" / "device.json"


def load_config() -> dict:
    """加载现有配置。"""
    path = get_config_path()
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(config: dict):
    """保存配置到文件。"""
    path = get_config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print(f"\n✓ 配置已保存到: {path}")


async def scan_devices(timeout: float = 5.0) -> list[tuple[str, str]]:
    """扫描附近的 Claude-Buddy-* 设备。

    返回: [(设备名称, MAC地址), ...]
    """
    try:
        from bleak import BleakScanner
    except ImportError:
        print("[错误] 未安装 bleak 库，请运行: pip install bleak")
        sys.exit(1)

    print(f"[扫描中] 正在搜索附近的 Claude-Buddy 设备（{timeout}秒）...")
    devices = await BleakScanner.discover(timeout=timeout)

    found = []
    for d in devices:
        if d.name and d.name.startswith("Claude-Buddy-"):
            found.append((d.name, d.address))

    return found


def display_devices(devices: list[tuple[str, str]]):
    """显示设备列表。"""
    print("\n" + "=" * 60)
    print("发现的设备:")
    print("=" * 60)
    for i, (name, mac) in enumerate(devices, 1):
        mac_suffix = name.split("-")[-1] if "-" in name else "????"
        print(f"  [{i}] {name}")
        print(f"      MAC: {mac} (后缀: {mac_suffix})")
    print("=" * 60)


def prompt_selection(devices: list[tuple[str, str]]) -> tuple[str, str]:
    """提示用户选择设备。

    返回: (设备名称, MAC地址)
    """
    while True:
        choice = input(f"\n请输入设备编号 (1-{len(devices)}) 或 'q' 退出: ").strip()

        if choice.lower() == "q":
            print("已取消配对")
            sys.exit(0)

        try:
            idx = int(choice) - 1
            if 0 <= idx < len(devices):
                return devices[idx]
            else:
                print(f"[错误] 请输入 1 到 {len(devices)} 之间的数字")
        except ValueError:
            print("[错误] 请输入有效的数字")


async def async_main():
    print("=" * 60)
    print("Claude-Buddy 设备配对工具")
    print("=" * 60)

    # 显示当前配置
    current_config = load_config()
    if current_config.get("paired_mac"):
        print(f"\n当前已配对设备: {current_config.get('device_name', '未知')}")
        print(f"MAC 地址: {current_config['paired_mac']}")

        choice = input("\n是否重新配对? [y/N]: ").strip().lower()
        if choice != "y":
            print("已取消")
            return

    # 扫描设备
    devices = await scan_devices(timeout=5.0)

    if not devices:
        print("\n[错误] 未发现任何 Claude-Buddy 设备")
        print("请确保:")
        print("  1. 设备已开机并运行 main.py")
        print("  2. 设备蓝牙已启用")
        print("  3. PC 蓝牙已开启")
        sys.exit(1)

    # 显示并选择
    display_devices(devices)
    device_name, device_mac = prompt_selection(devices)

    # 保存配置
    config = {
        "device_name": device_name,
        "paired_mac": device_mac,
        "mac_suffix": device_name.split("-")[-1] if "-" in device_name else "",
    }
    save_config(config)

    print(f"\n✓ 已配对设备: {device_name}")
    print(f"  MAC: {device_mac}")
    print("\n下次运行 daemon 时将自动连接到此设备")


def main() -> None:
    """同步 entrypoint，给 `claude-buddy-pair` console_script 用。"""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\n\n已取消")
        sys.exit(0)


if __name__ == "__main__":
    main()
