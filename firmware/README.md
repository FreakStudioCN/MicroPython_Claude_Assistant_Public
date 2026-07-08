# firmware 目录说明

## 文件命名规范

```
claude-buddy-{variant}-{board}-v{major}.{minor}.bin   # ESP32 固件（esptool 烧录）
claude-buddy-{variant}-{board}-v{major}.{minor}.uf2   # RP2040 固件（拖拽烧录）
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `variant` | 硬件形态 | `clock` / `panel` / `dshell` / `wizfi360` |
| `board` | 目标板型（芯片或开发板型号） | `esp32c3` / `waveshare-esp32s3-2inch` / `wizfi360` |
| `major.minor` | 固件版本（只到 minor，patch 版本不触发固件更新） | `v0.9` |

**版本策略**：固件版本号只跟随 major.minor 变化。v0.9.x 系列代码迭代（v0.9.4～v0.9.9）不重新烧录固件，固件文件名保持 `v0.9`。

**固件格式说明**：
- **`.bin`**：ESP32 系列（ESP32-S3 / ESP32-C3），通过 `esptool` 或 GUI 烧录工具烧录
- **`.uf2`**：RP2040 系列（WizFi360-EVB-Pico），通过拖拽到 RPI-RP2 磁盘驱动器烧录。按住 **BOOTSEL 按钮** 同时连接 USB，将 .uf2 文件拖入弹出的 RPI-RP2 磁盘即可，烧录完成后设备自动重启

## 当前文件

| 文件 | 形态 | 目标板 | 说明 |
|------|------|--------|------|
| `claude-buddy-dshell-esp32s3-v0.9.bin` | dshell | ESP32-S3 | D-Shell 正式面板版，GT911 触摸 + WS2812×8 灯带，含 LVGL（**正式硬件**） |
| `claude-buddy-panel-waveshare-esp32s3-2inch-v0.9.bin` | panel | Waveshare ESP32-S3 2inch | 测试开发板，CST816S 触摸，含 LVGL |
| `claude-buddy-clock-esp32c3-v0.9.bin` | clock | ESP32-C3 | 灯光+语音版，MicroPython 固件 |
| `claude-buddy-clock-wizfi360-v0.9.uf2` | wizfi360 | WizFi360-EVB-Pico (RP2040) | WiFi TCP 通信版，灯光+语音，无需蓝牙 |

## 烧录

```bash
python scripts/flash_device.py --variant dshell    # dshell 形态（正式面板）
python scripts/flash_device.py --variant panel     # panel 形态（开发板）
python scripts/flash_device.py --variant clock     # clock 形态（ESP32-C3）
python scripts/flash_device.py --variant wizfi360  # wizfi360 形态（RP2040 + WiFi）
```

烧录脚本会自动选择对应固件，并注入 `VARIANT` 和 `BLE_NAME`（或 WiFi 凭据）字段。

> **WizFi360 注意**：RP2040 出厂已自带 MicroPython，GUI 工具中"烧录底层固件"对 WizFi360 跳过 esptool 步骤。如需手动刷入 .uf2 固件，按住 **BOOTSEL** 接 USB → 拖入 .uf2 → 自动重启。

## device/lib/ 库文件说明

| 目录/文件 | 说明 |
|-----------|------|
| `aioble/` | BLE 蓝牙通信库（ESP32 BLE 形态使用） |
| `unittest/` | MicroPython 单元测试框架 |
| `wizfiatcontrol/` | **WizFi360 AT 指令控制库**（仅 wizfi360 形态使用），封装 WiFi 连接、TCP Server、AT 指令收发 |
| `logging.py` | 日志模块 |
