# firmware 目录说明

## 文件命名规范

```
claude-buddy-{variant}-{board}-v{major}.{minor}.bin
```

| 字段 | 说明 | 示例 |
|------|------|------|
| `variant` | 硬件形态 | `clock` / `panel` / `dshell` |
| `board` | 目标板型（芯片或开发板型号） | `esp32c3` / `waveshare-esp32s3-2inch` |
| `major.minor` | 固件版本（只到 minor，patch 版本不触发固件更新） | `v0.9` |

**版本策略**：固件版本号只跟随 major.minor 变化。v0.9.x 系列代码迭代（v0.9.4～v0.9.9）不重新烧录固件，固件文件名保持 `v0.9`。

## 当前文件

| 文件 | 形态 | 目标板 | 说明 |
|------|------|--------|------|
| `claude-buddy-dshell-esp32s3-v0.9.bin` | dshell | ESP32-S3 | D-Shell 正式面板版，GT911 触摸 + WS2812×8 灯带，含 LVGL（**正式硬件**） |
| `claude-buddy-panel-waveshare-esp32s3-2inch-v0.9.bin` | panel | Waveshare ESP32-S3 2inch | 测试开发板，CST816S 触摸，含 LVGL |
| `claude-buddy-clock-esp32c3-v0.9.bin` | clock | ESP32-C3 | 灯光+语音版，MicroPython 固件 |

## 烧录

```bash
python scripts/flash_device.py --variant dshell  # dshell 形态（正式面板）
python scripts/flash_device.py --variant panel   # panel 形态（开发板）
python scripts/flash_device.py --variant clock   # clock 形态
```

烧录脚本会自动选择对应固件，并注入 `VARIANT` 和 `BLE_NAME` 字段。
