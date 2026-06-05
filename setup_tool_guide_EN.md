# Claude Assistant Setup Visual Guide

> [🇨🇳 中文](setup_tool_guide.md) · [🇬🇧 English](setup_tool_guide_EN.md)

This guide walks through the one-click flashing tool (`Claude_Assistant_Setup.exe` or `python -m setup_tool`) step by step with 25 screenshots — from launch to log diagnostics, covering both **Clock (ESP32-C3, LED + Voice)** and **Panel (ESP32-S3, Display + Animation)** paths.

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

## Step 9: Step ② — Panel Hardware Selection (Screen + Character Animation)

![exe9](docs/exe9.png)

Select **Panel (ESP32-S3)**: Screen + Animation mode for LCD-equipped S3 boards. A "Panel Character" dropdown appears with pixel art character animations.

---

## Step 10: Built-in Panel Characters

![exe10](docs/exe10.png)

Open the "Panel Character" dropdown to see 8 preset characters: `claude`, `cat`, `robot`, `ghost`, `among_us`, `creeper`, `kirby`, `pikachu`. Select one and flash to see the animation on screen.

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
- **S3 selected** → `claude-buddy-panel-waveshare-esp32s3-2inch-v0.9.bin` (2-inch screen firmware)
- **C3 selected** → C3 firmware (no screen)

Firmware is stored in the system temp cache directory — no manual download needed.

---

## Step 16: COM Port Selection & First-time Flash Configuration

![exe16](docs/exe16.png)

- **COM Port Dropdown**: Click Refresh, select the device's COM port (example: COM75)
- **Flash Base MicroPython Firmware**: MUST check for brand-new blank chips (flashes the base OS)
- **Clear Device Filesystem**: Check for first-time flashing (full format, irreversible); uncheck for subsequent upgrades

Communication mode defaults to BLE (Bluetooth).

---

## Step 17: Start Flashing

![exe17](docs/exe17.png)

Click **Start Flashing**. Note the red notice on the right: for first-time flashing, press and hold the **BOOT button** while powering on, then click Start Flashing. The bottom log area shows real-time progress.

---

## Step 18: Flashing in Progress (Erasing Flash)

![exe18](docs/exe18.png)

Progress bar shows green. Log displays `Erasing flash`. **Do NOT disconnect the USB cable** during this process.

---

## Step 19: Firmware 100% Written

![exe19](docs/exe19.png)

Log shows 100% write complete, hash verification passed, firmware flashing done. Device is rebooting. When this line appears, **manually press the RST button** on the device to restart hardware.

---

## Step 20: Refresh COM Port After Flashing

![exe20](docs/exe20.png)

After the device reboots, click the **Refresh** button in the COM port section to re-enumerate the device's serial port, ready for BLE pairing.

---

## Step 21: All Resources Flashed

![exe21](docs/exe21.png)

Top progress bar fully green. Log shows each `assets/` PCM voice file verified ✅. Device restarts automatically at the end. Bottom-left shows flash complete and device BLE name (e.g. `Claude-Buddy-E522`). Three action buttons and 3-step pairing guide below.

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

## Quick Reference

| Scenario | Key Steps | Screenshots |
|----------|-----------|-------------|
| **First-time Clock Flash** | 1→2→3→4→5→6→7→8→16→17→18→19→20→21→22→23→24 | exe1~8, exe16~24 |
| **First-time Panel Flash** | 1→2→3→9→10→(optional 11~14)→15→16→17→18→19→20→21→22→23→24 | exe1~3, exe9~24 |
| **Firmware Upgrade (Clock/Panel)** | 1→2→3→4/9→16(uncheck base firmware + clear)→17→18→19→20→21 | skip exe5~8 |
| **Change Character Only (Panel)** | 1→2→3→9→10→16(parameters only)→17 | skip firmware flash |
| **View Device Logs** | Launch tool → 24→Pair→25 | exe24~25 |

> **Tip**: First-time flashing MUST check both "Flash Base MicroPython Firmware" and "Clear Device Filesystem". Subsequent upgrades should uncheck both and only upload application code.
