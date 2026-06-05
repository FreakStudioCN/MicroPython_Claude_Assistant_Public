# MicroPython Claude Assistant (Codex Buddy)

> [🇨🇳 中文](README.md) · [🇬🇧 English](README_EN.md)

Ever had this happen? Claude Code is running a long task — you're not sure if it's thinking, writing code, or already done. So you tab back to the terminal every 10 seconds. Sometimes it's stuck on an approval waiting for you, and you're deep in another article — ten minutes go by. If it's running pytest, you don't even dare leave your desk in case something fails.

**The Clock edition** is built for exactly this — a small hardware device on your desk that uses colored lights and voice announcements to tell you what Claude Code is doing, without you having to stare at the terminal.

It works simply: the device connects to a daemon on your PC via BLE Bluetooth. Every time Claude Code runs a tool — reading a file, executing a command, searching code — the status is pushed to the device in real time. Blue glow means idle, cyan sweep means working, yellow slow blink means approval needed, green flash means task complete, red alternating means error. Each state change has a voice announcement synthesized by the Doubao TTS engine — pick from 200+ voices, adjust speed and pitch.

What does this mean for you? It means you can walk away while Claude Code runs batch tasks. Grab coffee, hear "Task complete!" and know it's time to check results. Working on something else when yellow light blinks + "Please check your terminal" reminds you there's an approval waiting. Coding late at night with lights off? Voice announcements keep you informed without looking at the screen. It extends Claude Code's state from the screen into physical space — perceive with your peripheral vision and ears, not with mouse clicks.

The Clock hardware is minimal: an ESP32-C3 driving two WS2812B LEDs and a MAX98357A speaker in a small enclosure. Just USB power. Flashing and configuration are done through a GUI tool in two steps. Swap voices anytime (200+ Doubao options). No management portal, no subscription, no cloud dependency — everything runs over Bluetooth on your local machine.

Multiple Claude Code windows? The device tracks all sessions and surfaces the most important one. It doesn't store your code, doesn't upload anything — it's just a faithful status indicator.

At its heart, it's a simple idea: most of the time you're coding, you don't need to watch the terminal. Let the device watch it for you.

---

Real-time visualization of Claude Code tool execution status as an ESP32 desktop pet — BLE-pushed states translated into LED glow, voice announcements, and screen animations.

**Two hardware forms**:
- **Clock (ESP32-C3)**: WS2812B dual LEDs + Doubao TTS voice, colors change with state
- **Panel (ESP32-S3)**: 2.4-inch TFT screen + LVGL animation + TTS voice, 8 preset characters, multi-session history

**Customizable**: Panel characters (8 presets + custom), voice timbres (200+ Doubao options) — switch via `config.py`.

[![Presentation](https://img.shields.io/badge/📊_Presentation-GitHub_Pages-00d4ff?style=for-the-badge)](https://freakstudiocn.github.io/MicroPython_Claude_Assistant/presentation_EN.html)
[![Mirror](https://img.shields.io/badge/mirror-htmlpreview-555555?style=for-the-badge)](https://htmlpreview.github.io/?https://github.com/FreakStudioCN/MicroPython_Claude_Assistant/blob/main/presentation_EN.html)

| Clock Edition | Panel Edition |
|:---:|:---:|
| ![](docs/claude-knock.jpg) | ![](docs/claude-panel.jpg) |
| ![](docs/claude-knock2.png) | ![](docs/claude-panel2.jpg) |
| ![](docs/claude-knock3.jpg) | ![](docs/claude-panel3.jpg) |

### Real-world usage
| ![](docs/claude-knock4.png) | ![](docs/claude-knock5.png) |
| ![](docs/claude-knock6.png) | ![](docs/claude-knock7.png) |

---

## Hardware Forms

| Form | MCU | Output | Features |
|------|-----|--------|----------|
| **Panel** (Status Display) | ESP32-S3 | ST7789 2.4" + LVGL + MAX98357A speaker | Character animation + TTS voice + multi-session history |
| **Clock** (Alert Light) | ESP32-C3 | WS2812×2 + MAX98357A speaker | LED state + TTS voice |

Both forms share the same firmware code, differentiated by the `VARIANT` field in `config.py`.

---

## Installation

> **Recommended: Install as Claude Code Plugin** (auto-registers hooks, no manual config)
>
> ```bash
> claude plugin install claude-buddy
> ```
>
> After plugin install, hooks work automatically.

### Prerequisites

**PC-side**:
- Python 3.11+
- Windows 10/11 (BLE support)

**ESP32-side**:
- ESP32 with MicroPython firmware ([Official Download](https://micropython.org/download/))
- USB data cable connected to PC

**Optional customizations**:
- Modify `CHARACTER` in `device/config.py` to switch panel characters (8 presets: claude/cat/robot/ghost/among_us/creeper/kirby/pikachu)
- Run `scripts/gen_voice_assets.py` to customize voice timbre (200+ Doubao options)

---

### Install PC Dependencies

```bash
pip install -e .
```

### One-Click GUI Flashing Tool

`setup_tool` integrates firmware flashing, character selection, voice generation, BLE pairing — **all in one interface**.

![setup_tool GUI](docs/setuptool.png)

Run `dist/Claude_Assistant_Setup.exe` (download from Releases page).

**GUI Steps** (5-step main flow):

![Step1](docs/exe1.png) ![Step2](docs/exe2.png) ![Step3](docs/exe3.png) ![Step4](docs/exe4.png)

1. **Select Code Directory**: Double-click EXE → Maximize window → Browse to `device/` directory
2. **Select Hardware**: Clock (ESP32-C3 LED+Voice) / Panel (ESP32-S3 screen+animation), Panel offers 8 presets or custom characters
3. **Connect Device + Configure**: USB connect ESP32, select COM port; first-time check "Flash base firmware" and "Clear filesystem"
4. **Start Flashing**: Click button, progress bar shows real-time status (erase→flash→verify→reboot)
5. **Pair Device**: After flashing, click "Pair Device" for BLE pairing, MAC address auto-saved

> Full 25-step visual guide (Clock/Panel branching paths, Doubao TTS voice generation, custom character import) at **[setup_tool_guide_EN.md](setup_tool_guide_EN.md)** or **[setup_tool_guide.md](setup_tool_guide.md)**.
>
> GUI tool auto-scans COM ports, matches firmware files, checks dependencies — no need to manually run CLI steps.

### Start the Daemon

```bash
python daemon/ble_daemon.py
```

Daemon auto-searches and connects to ESP32. On connection, device plays connect voice/animation.

### Verify

```bash
python daemon/smoke.py               # Verify daemon TCP reachable (exit 0 = OK)
```

If smoke passes, run any tool in Claude Code (e.g. Read a file) — the device should show corresponding lights/animation.

### Daily Use

```
Each session:
  1. Power on ESP32 device (USB or battery)
  2. Start daemon on PC: python daemon/ble_daemon.py
  3. Open Claude Code, use normally
  4. Device automatically reflects Claude's working state
```

---

## Customization

### Change Voice Timbre

Use `scripts/gen_voice_assets.py` to regenerate PCM files, then re-flash:

```bash
python scripts/gen_voice_assets.py    # Open GUI, select timbre/adjust params/generate per state
```

1. Get App ID and Access Token from [Doubao Voice Console](https://console.volcengine.com/speech/service/10007)
2. Select timbre (200+ options), adjust speed/pitch/volume, generate per state
3. Files auto-save to `device/assets/`, bundled during flashing

**Flash limitation**: ESP32-C3/S3 flash is limited. Keep 1-4 variants per state, total PCM ≤ 2MB.

---

### Change Panel Character (Panel Edition)

**Method 1: Use preset characters**

Edit `device/config.py`, then re-flash:

```python
CHARACTER = "kirby"   # claude / cat / robot / ghost / among_us / creeper / kirby / pikachu
```

**Method 2: Use `/create-character` Skill (recommended)**

Type `/create-character` in Claude Code — AI guides you through creation:

1. **Describe** — tell AI what character you want (reference image, text description, pixel art)
2. **AI generates code** — auto-creates `device/char_<name>.py` with 5-state colors + 8-frame swing animation
3. **Auto-register** — writes to `device/config.py`'s `CHARACTER` field
4. **Re-flash** — run setup_tool or `flash_device.py` to see the new character

---

### Adjust Voice Behavior

Edit `device/config.py` (auto-generated during flash, re-flash needed):

```python
VOICE_HISTORY_DEPTH = 10    # Voice context history depth
VOICE_WORK_MIN_S    = 20    # Min working broadcast interval (seconds)
VOICE_WORK_MAX_S    = 60    # Max working broadcast interval (seconds)
VOICE_IDLE_MIN_S    = 20    # Min idle broadcast interval (seconds)
VOICE_IDLE_MAX_S    = 60    # Max idle broadcast interval (seconds)
```

Re-flash: run setup_tool to re-flash.

---

## Changelog

| Version | Date | Description |
|---------|------|-------------|
| v0.10.1 | 2026-06-05 | Bilingual documentation + 25-step visual setup guide + GUI tool improvements |
| v0.10.0 | 2026-05-30 | GUI flashing tool + panel voice completion + character creation Skill |
| v0.9.0 | 2026-05-18 | MVP: dual hardware forms + LED/voice feature complete |

---

> 项目源码和开发者文档，联系 wx:lzs110614011
