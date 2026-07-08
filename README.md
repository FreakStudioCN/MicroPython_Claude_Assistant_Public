# MicroPython Claude Assistant（码克助手）

> [🇨🇳 中文](README.md) · [🇬🇧 English](README_EN.md)

做开发的时候，你有没有这样的经历——Claude Code 正在跑一个长任务，你不确定它是在思考、在写代码、还是已经跑完了，于是你每隔十几秒就切回终端看一眼。有时它卡在一个审批上等你确认，而你还在另一篇文章里翻找，一转头十分钟过去了。如果跑的是 pytest，你甚至不敢离开座位太久，怕错过报错信息。

这些场景每天都会发生。**码克助手的闹钟版（Clock）** 就是来解决这个问题的——一个放在桌角的硬件小设备，通过灯光颜色和语音播报，让你不用盯着终端也知道 Claude Code 正在做什么。

它的工作方式很直接：设备通过 BLE 蓝牙（或 WiFi TCP）和 PC 上的守护进程保持连接。Claude Code 每执行一个工具——无论是读取文件、运行命令还是搜索代码——状态都会实时推送到这个桌面设备上。蓝色灯光代表空闲待命，青色流水表示正在执行，黄色慢闪提醒你有审批待处理，绿色快闪告诉你任务完成，红色交替闪说明出了错误。每种状态变化都有对应的语音播报，用豆包 TTS 引擎合成，音色可选，语速语调可调。

这意味着什么？意味着你可以在 Claude Code 跑批量任务的时候安心做别的事。跑去倒杯咖啡，听到设备说"任务完成啦"就知道可以回来检查结果。工作到一半切出去查资料，黄灯闪起 + 语音"请查看终端"提醒你有审批需要处理。深夜写代码不想被灯光打扰，语音播报也能让你感知任务进度而不需要转头看屏幕。这其实就是把 Claude Code 的执行状态从屏幕上延伸到了物理空间里——用你的余光、用你的耳朵去感知，而不是用手指去点击切换窗口。

闹钟版的硬件本身非常简洁。ESP32-C3（或 RP2040）芯片驱动两颗 WS2812B LED 灯珠和一个 MAX98357A 扬声器，装在一个小盒子里放桌上不占地方。整个设备只需要 USB 供电，烧录和配置走 GUI 工具，两步就能搞定。你也可以自己换语音音色（豆包两百多种音色可选），设备背后没有需要学习的管理页面，没有订阅服务，也没有远程服务器依赖——所有通信都在你的局域网和蓝牙链路内完成。

如果你同时开多个 Claude Code 窗口处理不同项目，设备会自动追踪所有 session，聚合显示其中最重要的那个状态。它不存储你的代码，不联网上传任何数据，只是一个忠实的状态提示器。

本质上，它是一个很简单的想法：写代码这件事的大部分时间里，你其实不需要一直看着终端。让设备替你看着，你做你的，偶尔看一眼灯光、听一句语音就够了。

---

将 Claude Code 的工具执行状态实时可视化为桌面设备——通过 BLE / WiFi TCP 推送状态，转化为灯光闪烁、语音播报、屏幕动画，让代码执行过程触手可及。

**四种硬件形态**：
- **dshell 面板版**（ESP32-S3）：2.4寸 TFT 屏幕 + GT911 触摸 + LVGL 动画 + WS2812×8 彩虹灯带 + TTS 语音播报，8 种预设角色可选，支持多 session 历史记录（**正式硬件**）
- **panel 面板版**（ESP32-S3）：2.4寸 TFT 屏幕 + LVGL 动画 + TTS 语音播报，8 种预设角色可选，支持多 session 历史记录（Waveshare 开发板）
- **clock 闹钟版**（ESP32-C3）：WS2812 双灯 + 豆包 TTS 语音播报，灯光颜色随状态变化
- **wizfi360 WiFi版**（RP2040 + WizFi360）：WS2812 双灯 + 豆包 TTS 语音播报 + 振动传感器/马达，WiFi TCP 通信（无需蓝牙）

**可定制**：面板角色（8 种预设 + 自定义）、语音音色（200+ 豆包音色）均可通过 `config.py` 一行配置切换。

[![演示文稿](https://img.shields.io/badge/📊_演示文稿-GitHub_Pages-00d4ff?style=for-the-badge)](https://freakstudiocn.github.io/MicroPython_Claude_Assistant_Public/presentation.html)
[![备用链接](https://img.shields.io/badge/备用-htmlpreview-555555?style=for-the-badge)](https://htmlpreview.github.io/?https://github.com/FreakStudioCN/MicroPython_Claude_Assistant_Public/blob/main/presentation.html)

| clock 闹钟版 | panel 面板版 |
|:---:|:---:|
| ![](docs/claude-knock.jpg) | ![](docs/claude-panel.jpg) |
| ![](docs/claude-knock2.png) | ![](docs/claude-panel2.jpg) |
| ![](docs/claude-knock3.jpg) | ![](docs/claude-panel3.jpg) |

### 使用场景实拍
| ![](docs/claude-knock4.png) | ![](docs/claude-knock5.png) |
| ![](docs/claude-knock6.png) | ![](docs/claude-knock7.png) |

---

## 硬件形态

| 形态 | 主控 | 输出 | 特性 |
|------|------|------|------|
| **dshell**（D-Shell面板） | ESP32-S3 | ST7789 2.4寸屏 + GT911触摸 + LVGL + WS2812×8 + MAX98357A扬声器 | 小人动画 + 触摸交互 + TTS语音播报 + 多session历史记录 + 彩虹灯带 |
| **panel**（状态面板） | ESP32-S3 | ST7789 2.4寸屏 + CST816S触摸 + LVGL + MAX98357A扬声器 | 小人动画 + 触摸交互 + TTS语音播报 + 多session历史记录（Waveshare 开发板） |
| **clock**（闹钟灯） | ESP32-C3 | WS2812×2 + MAX98357A扬声器 | 灯光状态 + TTS语音播报 |
| **wizfi360**（WiFi闹钟灯） | RP2040 + WizFi360 | WS2812×2 + MAX98357A扬声器 + 振动传感器/马达 | 灯光状态 + TTS语音播报 + WiFi TCP（无需蓝牙） |

四种形态共用同一份固件代码，`config.py` 中 `VARIANT` 字段区分。

---

## 安装部署

> **推荐：以 Claude Code Plugin 方式安装**（自动注册 hook，无需手动改配置）
>
> **在线安装**（需要访问 GitHub）：
> ```bash
> claude plugin marketplace add https://github.com/ChrisWu132/claude-buddy-plugin.git
> claude plugin install claude-buddy-bridge@claude-buddy
> ```
>
> **离线安装**（无网络/无法访问 GitHub 的用户）：
> 克隆公开仓库到本地，在 Claude Code 中打开该目录，命令 Claude Code 读取 `skill.md` 和 `plugin_plan/PLAN.md` 进行安装：
> ```bash
> git clone https://github.com/FreakStudioCN/MicroPython_Claude_Assistant_Public
> cd MicroPython_Claude_Assistant_Public
> claude .
> ```
>
> Plugin 安装后 hook 自动生效。

### 前置要求

**PC端**：
- Python 3.11+
- Windows 10/11（BLE 或 WiFi 支持）

**设备端**：
- ESP32 已刷入 MicroPython 固件（[官方下载](https://micropython.org/download/)），或 RP2040（WizFi360-EVB-Pico，出厂自带 MicroPython）
- USB 数据线连接 PC

**可选自定义**：
- 修改 `device/config.py` 中 `CHARACTER` 字段切换面板角色（8 种预设：claude/cat/robot/ghost/among_us/creeper/kirby/pikachu）
- 运行 `scripts/gen_voice_assets.py` 自定义语音音色（200+ 豆包音色可选）

---

### 安装 PC 依赖

```bash
pip install -e .
```

### 命令行烧录固件（备选方案）

除了 GUI 工具，也可以通过命令行直接烧录：

```bash
python scripts/flash_device.py --variant clock      # Clock 闹钟版（ESP32-C3）
python scripts/flash_device.py --variant panel      # Panel 面板版（ESP32-S3）
python scripts/flash_device.py --variant dshell     # D-Shell 正式面板版
python scripts/flash_device.py --variant wizfi360   # WizFi360 WiFi 版（RP2040 + WiFi TCP）
```

> **WizFi360 注意**：RP2040 出厂已自带 MicroPython，无需 esptool 烧录底层固件。如需手动刷入 .uf2 固件：按住 **BOOTSEL 按钮** 的同时连接 USB，将 `firmware/claude-buddy-clock-wizfi360-v0.9.uf2` 拖入弹出的 RPI-RP2 磁盘驱动器即可，烧录完成后自动重启。

### 设备配对（命令行）

```bash
python daemon/pair_device.py   # BLE 形态：蓝牙扫描；WiFi 形态：TCP 扫描
```

配对配置保存至 `%APPDATA%\claude-buddy\device.json`，后续 daemon 启动时自动连接。

### 一键 GUI 烧录配置工具

`setup_tool` 整合了烧录固件、选择角色、生成语音、BLE/WiFi 配对等全部装机步骤，**一个界面搞定所有操作**。

![setup_tool GUI](docs/setuptool.png)

运行 `dist/Claude_Assistant_Setup.exe`（从 Releases 页面下载）。

**图形界面操作步骤**（6 步主流程）：

![步骤1](docs/exe1.png) ![步骤2](docs/exe2.png) ![步骤3](docs/exe3.png) ![步骤4](docs/exe4.png)

1. **选代码目录**：双击 EXE 启动 → 最大化窗口 → 点击【浏览】选择 `device/` 目录
2. **选硬件**：Clock（ESP32-C3 灯光+语音）/ Panel（ESP32-S3 屏幕+角色）/ D-Shell（正式面板+灯带）/ WizFi360（RP2040+WiFi），Panel/D-Shell 可选 8 种预设角色或导入自定义角色
3. **连设备 + 配置**：USB 连接设备，选择串口；首次使用勾选"烧录底层固件"和"清空文件系统"；WizFi360 需输入 WiFi SSID/密码
4. **开始烧录**：点击按钮，进度条显示实时状态（擦除→烧录→校验→重启）
5. **配对设备**：烧录完成后点击"配对设备"——ESP32 形态走 BLE 蓝牙配对，WizFi360 走 WiFi TCP 配对
6. **启动桥接**：点击"启动桥接"，GUI 内嵌守护进程连接设备并实时推送 Claude Code 执行状态（所有形态通用）

![桥接运行](docs/gui_daemen.png)

> 完整截图操作指南（含 Clock/Panel/D-Shell/WizFi360 分叉路径、豆包 TTS 语音生成、自定义角色导入、WiFi 配对、启动桥接等细节）见 **[setup_tool_guide.md](setup_tool_guide.md)** 或 **[setup_tool_guide_EN.md](setup_tool_guide_EN.md)**。
>
> GUI 工具会自动扫描串口、匹配固件文件、检查依赖，无需手动执行 CLI 步骤。

### 手动注册 Hook（Plugin 安装失败时的备选方案）

如果 `claude plugin install` 不可用，手动注册 hook：

打开 `~/.claude/settings.json`（Windows：`C:\Users\<用户名>\.claude\settings.json`），添加以下 `hooks` 段（合并到已有配置中），将 `<你的项目路径>` 替换为实际绝对路径：

```json
{
  "hooks": {
    "UserPromptSubmit": [{"hooks": [{"type": "command", "command": "pythonw \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "PreToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "pythonw \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "PostToolUse": [{"matcher": "*", "hooks": [{"type": "command", "command": "pythonw \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "PostToolUseFailure": [{"matcher": "*", "hooks": [{"type": "command", "command": "pythonw \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "Notification": [{"hooks": [{"type": "command", "command": "pythonw \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "Stop": [{"hooks": [{"type": "command", "command": "python \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "StopFailure": [{"hooks": [{"type": "command", "command": "python \"<你的项目路径>/daemon/hook_bridge.py\""}]}],
    "SessionEnd": [{"hooks": [{"type": "command", "command": "python \"<你的项目路径>/daemon/hook_bridge.py\""}]}]
  }
}
```

修改后**重启 Claude Code** 生效。

### 启动守护进程

```bash
python daemon/ble_daemon.py
```

daemon 启动后自动搜索并连接设备（BLE 或 WiFi TCP），连接成功后设备播放连接语音/动画。

### 验证

```bash
python daemon/smoke.py               # 验证daemon TCP可达（退出码0=正常）
```

smoke 通过后，在 Claude Code 中执行任意工具（如 Read 文件），设备应出现对应灯光/动画。

### 日常使用流程

```
每次使用：
  1. 开机设备（USB供电或电池）
  2. PC 启动 daemon：python daemon/ble_daemon.py
  3. 打开 Claude Code，正常使用即可
  4. 设备自动反映 Claude 工作状态
```

---

## 自定义

### 换语音音色

使用 `scripts/gen_voice_assets.py` 重新生成 PCM 文件，再烧录到设备：

```bash
python scripts/gen_voice_assets.py    # 打开 GUI，选音色/调参数/逐状态生成
```

1. 在豆包[语音控制台](https://console.volcengine.com/speech/service/10007)获取 App ID 和 Access Token
2. GUI 中选择音色（200+ 种可选）、调节语速/语调/音量，逐状态生成
3. 文件自动保存到 `device/assets/`，烧录时一并上传

**空间限制**：ESP32-C3 / ESP32-S3 Flash 有限，每状态建议保留 1-4 个变体，总 PCM ≤ 2MB。

---

### 换面板角色形象（panel 形态）

**方式一：使用预设角色**

修改 `device/config.py` 中的 `CHARACTER` 字段，然后重新烧录：

```python
CHARACTER = "kirby"   # claude / cat / robot / ghost / among_us / creeper / kirby / pikachu
```

**方式二：使用 `/create-character` Skill（推荐）**

在 Claude Code 中输入 `/create-character`，AI 会引导你完成角色创建全流程：

1. **描述需求** — 告诉 AI 想要什么形象（参考图片、文字描述、像素图均可）
2. **AI 生成代码** — 自动创建 `device/char_<name>.py`，含 5 状态配色 + 8 帧摆动动画
3. **自动注册** — 写入 `device/config.py` 的 `CHARACTER` 字段
4. **重新烧录** — 运行 setup_tool 或 `flash_device.py` 即可看到新角色

---

### 调整语音行为参数

编辑 `device/config.py`（烧录时自动生成，修改后需重新烧录）：

```python
VOICE_HISTORY_DEPTH = 10    # 语音上下文历史深度
VOICE_WORK_MIN_S    = 20    # 工作中偶发播报最短间隔（秒）
VOICE_WORK_MAX_S    = 60    # 工作中偶发播报最长间隔（秒）
VOICE_IDLE_MIN_S    = 20    # 空闲偶发播报最短间隔（秒）
VOICE_IDLE_MAX_S    = 60    # 空闲偶发播报最长间隔（秒）
```

修改后重新烧录：运行 setup_tool 重新烧录。

---

## 变更记录

| 版本 | 日期 | 内容 |
|------|------|------|
| v1.1.0 | 2026-07-08 | 新增 WizFi360 WiFi 版（RP2040 + WiFi TCP），静态 IP 分配，GUI WiFi 配置/配对，文档全面更新 |
| v1.0.0 | 2026-06-23 | 首个正式版本：新增 D-Shell 面板硬件形态（触摸屏+彩虹灯带），GUI 三形态选择，文档全面更新 |
| v0.12.0 | 2026-06-08 | 闹钟版振动传感器/马达 + 全局亮度控制 |
| v0.11.0 | 2026-06-07 | EXE 跨电脑兼容性重构 + 版本号系统 |
| v0.10.1 | 2026-06-05 | 双语文档体系 + 25 步图文装机指南 + GUI 烧录工具优化 |
| v0.10.0 | 2026-05-30 | GUI 烧录工具 + 面板语音补齐 + 角色创建 Skill |
| v0.9.0 | 2026-05-18 | MVP 可用：双硬件形态 + 灯光语音完整功能 |

---

> 项目源码和开发者文档，联系 wx:lzs110614011
