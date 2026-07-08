# Claude Assistant Setup Visual Guide

> [🇨🇳 中文](setup_tool_guide.md) · [🇬🇧 English](setup_tool_guide_EN.md)

This guide walks through the one-click flashing tool (`Claude_Assistant_Setup.exe` or `python -m setup_tool`) step by step with screenshots — from launch to bridge diagnostics, covering **D-Shell (ESP32-S3, official panel with touch+LED strip)**, **Panel (ESP32-S3 dev board, display+animation)**, **Clock (ESP32-C3, LED+voice)**, and **WizFi360 (RP2040 + WiFi, TCP communication)** — four branching paths.

---

## Step 1: Project Root — Launch the Installer

![exe1](docs/exe1.png)

Navigate to the `MicroPython_Claude_Assistant_Public` directory (contains `.claude`, `daemon`, `device` folders etc.), double-click `Claude_Assistant_Setup.exe` to start the flashing tool.

> `device/` is the firmware code root directory required in later steps.

---

## Step 2: Main Interface — Maximize the Window

![exe2](docs/exe2.png)

Claude Buddy Flashing Tool main interface with 5 configuration steps: ① Select Code → ② Hardware → ③ Connect Device → ④ Parameters → ⑤ Flash. Click the maximize button to expand the full interface for easier configuration.

---

## Step 3: Step ① — Select Firmware Code Directory

![exe3](docs/exe3.png)

Click the **Browse** button next to the code directory field, navigate to and select the `device/` folder. Once selected, a **✓ Valid** badge appears to the right. The folder contains `assets/` (voice resources) and `lib/` (libraries).

---

## Step 3a: Step ② — WizFi360 Hardware Selection (RP2040 + WiFi TCP)

![chosee_wifi](docs/chosee_wifi.png)

Select **WizFi360 (RP2040+WiFi)**: Based on the WizFi360-EVB-Pico dev board, communicates with PC via WiFi TCP (no Bluetooth needed). After selection, a WiFi configuration area appears below — enter your router's **SSID (WiFi name)** and **password**. These are automatically injected into the device during flashing.

> WizFi360 uses RP2040 as the main controller and controls the WizFi360 WiFi module via AT commands. Communication mode auto-switches to "Ethernet (WiFi)".

---

## Step 3b: Step ③ — Select Ethernet (WiFi) Communication

![chosee_wifi2](docs/chosee_wifi2.png)

After selecting WizFi360, the device connection area's communication mode auto-switches to **Ethernet (WiFi)**. After flashing, the PC connects to the device via TCP (default port 57321) — no BLE Bluetooth pairing needed.

> The PC auto-scans the LAN for a free IP and assigns a static IP to the device, ensuring the IP stays fixed across reboots.

---

## Step 4: Step ② — Clock Hardware Selection (LED + Voice, No Screen)

![exe4](docs/exe4.png)

Select **Clock (ESP32-C3)**: LED + Voice mode. The tool auto-matches the C3 firmware bin. C3 boards require PCM voice files generated beforehand — click the **Generate Voice Files** button (marked in red) to proceed.

---

## Step 5: Doubao PCM Voice Generator — API Key Verification

![exe5](docs/exe5.png)

After clicking "Generate Voice", the voice tool window opens. Enter your Doubao Open Platform App ID and Access Token, then click **Verify**. A "Verification successful ✓" message unlocks online TTS synthesis.

> Get your keys at: [Doubao Voice Console](https://console.volcengine.com/speech/service/10007)

---

## Step 6: Voice Timbre Selection

![exe6](docs/exe6.png)

Open the timbre dropdown menu. Multiple built-in voices are available (default BV701 female voice, BV700 V2 male voice, etc.). Adjust speed, pitch, and volume parameters as needed.

---

## Step 7: Voice Synthesis

![exe7](docs/exe7.png)

After configuring timbre, parameters, and broadcast text, click the **Generate** button in the bottom-left corner. The tool calls the Doubao API to convert text to 8000Hz hardware-compatible PCM audio.

---

## Step 8: Save Synthesized Voice

![exe8](docs/exe8.png)

After generation completes, click **Save**. The save dialog defaults to the `device/assets/` folder. All broadcast audio must be saved to this directory — the tool automatically bundles them during flashing.

---

## Step 9: Step ② — Screen Hardware Selection (Panel / D-Shell)

![exe9](docs/exe9.png)

Two screen variants for ESP32-S3 boards with LCD display:

- **D-Shell (ESP32-S3)  Screen+Character+LED Strip**: Official panel hardware, GT911 touch + WS2812×8 rainbow LED strip. Character selection also available.
- **Panel (ESP32-S3)  Screen+Animation**: Waveshare dev board, CST816S touch. A "Panel Character" dropdown appears with pixel art character animations.

---

## Step 10: Built-in Screen Characters

![exe10](docs/exe10.png)

Open the "Panel Character" dropdown (available for both Panel and D-Shell) to see 8 preset characters: `claude`, `cat`, `robot`, `ghost`, `among_us`, `creeper`, `kirby`, `pikachu`. Select one and flash to see the animation on screen.

---

## Step 11: Built-in Character Preview

![exe11](docs/exe11.png)

Select a panel character (e.g. `among_us`), click the **Preview** button. A popup shows all character color variations and animation frames, allowing you to preview the effect before flashing.

---

## Step 12: Import Custom Character

![exe12](docs/exe12.png)

Click the **Import Custom Character…** button in the top-right corner. Navigate to the `device/` directory and select a custom character source file (e.g. `char_ghost.py`, a ghost pixel character Python script).

---

## Step 13: Custom Character Import Success

![exe13](docs/exe13.png)

A success message appears: "Import successful, character file has been imported to the device directory. Panel set to 'Custom' automatically." The panel character changes to `Custom(char_ghost)` and the source is written to the project.

---

## Step 14: Preview Custom Character

![exe14](docs/exe14.png)

Click **Preview Custom Character** to view the ghost character's multi-color pixel animation frames, verifying that the custom character assets are parsed correctly with no missing textures.

---

## Step 15: Automatic Firmware File Matching

![exe15](docs/exe15.png)

The firmware dropdown auto-matches based on hardware selection:
- **D-Shell (S3 official panel)** → `claude-buddy-dshell-esp32s3-v0.9.bin` (GT911 touch + LED strip firmware)
- **Panel (S3 dev board)** → `claude-buddy-panel-waveshare-esp32s3-2inch-v0.9.bin` (CST816S touch firmware)
- **Clock (C3)** → `claude-buddy-clock-esp32c3-v0.9.bin` (C3 no-screen firmware)
- **WizFi360 (RP2040)** → `claude-buddy-clock-wizfi360-v0.9.uf2` (RP2040 drag-and-drop firmware)

Firmware is stored in the system temp cache directory — no manual download needed.

---

## Step 16: COM Port Selection & First-time Flash Configuration

![exe16](docs/exe16.png)

- **COM Port Dropdown**: Click Refresh, select the device's COM port (example: COM75)
- **Flash Base MicroPython Firmware**: MUST check for brand-new blank chips (flashes the base OS)
- **Clear Device Filesystem**: Check for first-time flashing (full format, irreversible); uncheck for subsequent upgrades

Communication mode defaults to BLE (Bluetooth). When WizFi360 is selected, it auto-switches to "Ethernet (WiFi)".

> **WizFi360 Note**: WizFi360 uses RP2040 — the GUI skips esptool for "Flash Base Firmware" (RP2040 ships with MicroPython pre-installed). To manually flash .uf2 firmware: hold **BOOTSEL** + plug USB → drag .uf2 to RPI-RP2 drive → auto-reboot.

---

## Step 17: Start Flashing

![exe17](docs/exe17.png)

Click **Start Flashing**. Note the red notice on the right: for first-time flashing, press and hold the **BOOT button** (ESP32) / **BOOTSEL button** (RP2040) while powering on, then click Start Flashing. The bottom log area shows real-time progress.

---

## Step 18: Flashing in Progress (Erasing Flash)

![exe18](docs/exe18.png)

Progress bar shows green. Log displays `Erasing flash`. **Do NOT disconnect the USB cable** during this process.

---

## Step 19: Firmware 100% Written

![exe19](docs/exe19.png)

Log shows 100% write complete, hash verification passed, firmware flashing done. Device is rebooting. When this line appears, **manually press the RST button** on the device to restart hardware (WizFi360/RP2040 auto-reboots after .uf2 drag-and-drop — no manual reset needed).

---

## Step 20: Refresh COM Port After Flashing

![exe20](docs/exe20.png)

After the device reboots, click the **Refresh** button in the COM port section to re-enumerate the device's serial port, ready for BLE pairing.

---

## Step 21: All Resources Flashed

![exe21](docs/exe21.png)

Top progress bar fully green. Log shows each `assets/` PCM voice file verified ✅. Device restarts automatically at the end. Bottom-left shows flash complete and device BLE name (e.g. `Claude-Buddy-E522`). Three action buttons and 3-step pairing guide below.

---

## Step 22w: WiFi TCP Pairing — Enter Device IP

![pair_wifi](docs/pair_wifi.png)

After WizFi360 flashing completes, click the **Pair Device** button. The dialog auto-scans the LAN to find the device, or you can manually enter the device IP address (the device prints its IP via serial after boot). Click confirm — TCP connection is verified and pairing config is saved locally.

> Unlike BLE pairing, WiFi pairing uses TCP connection verification — no Bluetooth scanning needed.

---

## Step 23w: Static IP Confirmation — Pairing Config Saved

![static_ip](docs/static_ip.png)

During flashing, the PC auto-scans the LAN for a free IP and injects it as a static IP on the device. After pairing completes, the status bar shows the device name and assigned IP address.

> Static IP ensures the device IP stays the same across reboots — no re-pairing needed. To change the IP, re-flash the device.

---

## Step 22: Pairing Device Entry

![exe22](docs/exe22.png)

Click **Pair Device** in the bottom-left corner — this is the only entry point to open the BLE Bluetooth scan window. Wait for the device to power on and start BLE advertising before clicking.

---

## Step 23: BLE Pairing — Start Scanning

![exe23](docs/exe23.png)

Popup title "Device Pairing - BLE Bluetooth Low Energy". Ensure the device is powered on with Bluetooth enabled. Click **Start Pairing** — the tool scans for 5 seconds.

---

## Step 24: Bluetooth Pairing Successful

![exe24](docs/exe24.png)

Scanned hardware device found (e.g. `Claude-Buddy-E522` + MAC address `44:1B:F6:85:E5:22`), status shows "Paired". Pairing config is automatically saved to a local JSON config file. Button changes to "Completed".

---

## Step 25: Read Device Logs

![exe25](docs/exe25.png)

Click **Read Device Logs** (only available after successful pairing). A popup shows the device boot log:

- `INFO`: Memory, screen, Bluetooth initialization normal
- `ERROR: SD card mount failed`: Normal — no TF card inserted, no action needed

Use this for daily debugging and troubleshooting.

---

## Step 26: Start Bridge (All Forms)

![gui_daemen](docs/gui_daemen.png)

After flashing and pairing, click the **Start Bridge** button. The GUI's embedded daemon runs in the background, connecting to the device and receiving Claude Code Hook status data via TCP port 57320, forwarding it to the device in real time (5Hz refresh).

- **BLE forms** (panel/dshell/clock): Bridge connects to device via BLE Bluetooth
- **WiFi form** (wizfi360): Bridge connects to device via TCP (port 57321)
- Status indicator shows current bridge state and active session count
- Click **Stop Bridge** to disconnect at any time
- Bridge auto-stops when closing the GUI window

> After starting the bridge, execute any tool in Claude Code — the device will show corresponding light/voice/animation feedback.

---

## Quick Reference

| Scenario | Key Steps | Screenshots |
|----------|-----------|-------------|
| **First-time Clock Flash** | 1→2→3→4→5→6→7→8→16→17→18→19→20→21→22→23→24→26 | exe1~8, exe16~24, gui_daemen |
| **First-time Panel/D-Shell Flash** | 1→2→3→9→10→(optional 11~14)→15→16→17→18→19→20→21→22→23→24→26 | exe1~3, exe9~24, gui_daemen |
| **First-time WizFi360 Flash** | 1→2→3→3a→3b→16→17→18→19→20→21→22w→23w→26 | exe1~3, chosee_wifi, chosee_wifi2, exe16~21, pair_wifi, static_ip, gui_daemen |
| **Firmware Upgrade (Clock/Panel)** | 1→2→3→4/9→16(uncheck base firmware + clear)→17→18→19→20→21 | skip exe5~8 |
| **Change Character Only (Panel)** | 1→2→3→9→10→16(parameters only)→17 | skip firmware flash |
| **View Device Logs** | Launch tool → 24→Pair→25 | exe24~25 |
| **Start Bridge (All Forms)** | Pairing complete → click "Start Bridge" → observe status | gui_daemen |

> **Tip**: First-time flashing MUST check both "Flash Base MicroPython Firmware" and "Clear Device Filesystem". Subsequent upgrades should uncheck both and only upload application code.
