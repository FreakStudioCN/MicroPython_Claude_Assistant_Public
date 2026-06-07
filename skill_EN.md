---
name: claude-buddy-setup
description: Set up the Claude Buddy hardware desktop pet — installs runtime, pairs BLE device, registers CLI hooks. Use when user asks to install/configure/update/repair/diagnose/uninstall Claude Buddy.
---

> [🇨🇳 中文](skill.md) · [🇬🇧 English](skill_EN.md)

# Claude Buddy Setup Skill

> **v0.11.0 Update: GUI tool is now the recommended way to install.**  
> Download `Claude_Assistant_Setup.exe` (or run `python -m setup_tool`) and follow the 25-step visual guide at [setup_tool_guide_EN.md](setup_tool_guide_EN.md) to complete flashing + BLE pairing.  
> The CLI flow below is for **headless environments or script automation**.

You are helping the user set up a Claude Buddy hardware desktop pet. **All phases execute on the user's machine — do NOT fork agents, do NOT use WebFetch, use Bash and AskUserQuestion directly**.

## Full Flow (6 phases)

Run in order. On each phase failure, stop and report the error to the user. If anything unexpected happens at any phase, use AskUserQuestion to let the user decide whether to continue or abort.

---

## Phase 0: Detect

```bash
cat > /tmp/cb_detect.sh << 'EOF'
echo "{"
echo "  \"os\": \"$(uname -s 2>/dev/null || echo Windows)\","
echo "  \"is_wsl\": $([ -f /proc/version ] && grep -qi microsoft /proc/version && echo true || echo false),"
echo "  \"python\": \"$(python --version 2>&1 | head -1)\","
echo "  \"uv\": \"$(uv --version 2>&1 | head -1 || echo missing)\","
echo "  \"git\": \"$(git --version 2>&1 | head -1 || echo missing)\","
echo "  \"claude\": \"$(claude --version 2>&1 | head -1 || echo missing)\","
echo "  \"codex\": \"$(codex --version 2>&1 | head -1 || echo missing)\","
echo "  \"daemon_installed\": $([ -f "$HOME/.claude-buddy/pyproject.toml" ] && echo true || echo false),"
echo "  \"plugin_installed\": $(claude plugin list 2>/dev/null | grep -q claude-buddy-bridge && echo true || echo false)"
echo "}"
EOF
bash /tmp/cb_detect.sh
```

**Decision**:
- `is_wsl=true` → Exit: "BLE is unavailable in WSL. Please use Native Windows Claude Code."
- `daemon_installed=true && plugin_installed=true` → Submenu: AskUserQuestion "Claude Buddy is already installed. What would you like to do?" Options: update / repair / uninstall / diagnose / exit
- `daemon_installed=true && plugin_installed=false` → Jump to Phase 4 (daemon ready but plugin not installed)
- `daemon_installed=false` → Full Phase 2-6 flow
- `claude=missing && codex=missing` → Exit: "Claude Code or Codex CLI must be installed first"
- `python` not 3.11+ → Install via Phase 1
- `uv=missing` or `git=missing` → Install via Phase 1

---

## Phase 1: Bootstrap deps

Only run when dependencies are missing. **One upfront AskUserQuestion** listing all commands to run — user approves all with a single yes.

```
I need to run these commands to complete setup:
1. Install Python 3.11+ (if missing)
2. Install uv (Python package manager)
3. Install git (if missing)
4. Clone https://github.com/freakstudio/claude-buddy to ~/.claude-buddy
5. uv sync --frozen to install Python dependencies
6. Scan Bluetooth and pair the desktop pet
7. Register hook with Claude Code

Allow all?
```

### Install Python (if missing)

- macOS: `brew install python@3.11`
- Windows: `winget install --id Python.Python.3.11 --silent`
  - **Important**: Run `refreshenv` or open a new shell after installation (PATH is not updated otherwise)
  - Detect Store Python alias hijack: `where python` — if it points to `WindowsApps\python.exe`, tell the user to disable it in "Settings → Apps → App execution aliases"

### Install uv

- macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `winget install --id astral-sh.uv --silent`
- fallback: `pip install --user uv`

### Install git

- macOS: `xcode-select --install` or `brew install git`
- Windows: `winget install --id Git.Git --silent`

### Windows Additional Checks

```powershell
# PowerShell ExecutionPolicy
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq 'Restricted') {
    # Prompt user to run:
    # Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
}

# Detect HTTP_PROXY / HTTPS_PROXY
if ($env:HTTP_PROXY) { echo "Proxy: $env:HTTP_PROXY" }
```

---

## Phase 2: Clone & sync

```bash
# Primary
git clone https://github.com/freakstudio/claude-buddy "$HOME/.claude-buddy" 2>&1
# Fallback if GitHub fails
# git clone https://gitee.com/freakstudio/claude-buddy-mirror "$HOME/.claude-buddy"

cd "$HOME/.claude-buddy"

# uv sync --frozen locks the lockfile, preventing new dependencies
uv sync --frozen 2>&1
```

Error handling:
- `git clone` GitHub fails → fallback to Gitee mirror
- `uv sync --frozen` fails → check lockfile drift / network / Python version, retry once; if still failing, ask the user to paste stderr

---

## Phase 3: BLE Pairing

**Reminder**: "macOS will prompt for Bluetooth permission for the terminal app — please allow it."

Run the TUI pairing tool directly:

```bash
cd "$HOME/.claude-buddy"
uv run claude-buddy-pair
```

`pair_device.py` scans Bluetooth, lists devices, lets the user choose, writes `device.json` (with `paired_mac`). Exit code 0 means pairing succeeded.

Verify:

```bash
# macOS / Linux: ~/.config/claude-buddy/device.json
# Windows:      %APPDATA%\claude-buddy\device.json
cat "$HOME/.config/claude-buddy/device.json" 2>/dev/null || \
cat "$APPDATA/claude-buddy/device.json" 2>/dev/null
```

Must contain `paired_mac`. If missing, ask the user to re-run `claude-buddy-pair`.

---

## Phase 4: Plugin Registration

The repo itself is the Claude Code marketplace + plugin (`source: "./"`). Two steps: register + install.

### Claude Code

```bash
cd "$HOME/.claude-buddy"
claude plugin marketplace add .
claude plugin install claude-buddy-bridge@claude-buddy
```

Verify:

```bash
claude plugin list  # should show claude-buddy-bridge
```

### Codex (V1 uses the same marketplace flow)

```bash
cd "$HOME/.claude-buddy"
codex plugin marketplace add .
codex plugin install claude-buddy-bridge@claude-buddy
```

If `codex plugin install` / `codex plugin marketplace` subcommands don't exist (older Codex version), skip Codex registration for now — the desktop pet will work fine with Claude Code.

**Hook command uses `${CLAUDE_PLUGIN_ROOT}`** — Claude expands this variable after caching the plugin. The daemon runtime was installed to `~/.claude-buddy/` in Phase 2; hook_bridge uses `Path.home()` internally to find it, decoupled from the plugin cache.

---

## Phase 5: Smoke test

```bash
# Start daemon (detached)
cd "$HOME/.claude-buddy"
# macOS / Linux
nohup uv run claude-buddy-daemon > /tmp/cb-daemon.log 2>&1 &
# Windows PowerShell:
# Start-Process -WindowStyle Hidden uv run claude-buddy-daemon

sleep 2

# Run smoke test
uv run claude-buddy-smoke
```

Smoke output `[smoke] OK` means the protocol link is working. Then AskUserQuestion:

> Is the desktop pet glowing now? It should flash briefly or show W (working) state.
> A) Yes, it's glowing
> B) No / Not sure

- A → Setup complete banner (continue to Phase 6)
- B → Enter Phase 5.5 Diagnostic

---

## Phase 5.5: Diagnostic

Check in order:

```bash
# 1. Is daemon running?
netstat -an | grep 57320 || ss -an | grep 57320 || lsof -i :57320

# 2. Check daemon log for errors
cat /tmp/cb-daemon.log | tail -50

# 3. Is BLE connected?
grep -i "connected" /tmp/cb-daemon.log
grep -i "error\|failed" /tmp/cb-daemon.log
```

Diagnostic decisions:

| Symptom | Cause | Action |
|---------|-------|--------|
| daemon not listening on 57320 | daemon failed to start | Check /tmp/cb-daemon.log for traceback, ask user to report to support |
| daemon running, log has no "connected" | device off / too far / wrong pairing | Ask user to check device power + move closer; if still failing, retry Phase 3 |
| log has "connected" but pet doesn't move | firmware issue | Power cycle the device; if still failing, contact support |
| `os: Linux` (including WSL2) | BLE not supported | Exit |

---

## Phase 6: Self-service guide

```
Desktop pet is ready! Anytime, just say:
  - "Update Claude Buddy" → pull latest daemon + restart
  - "Repair Claude Buddy pairing" → re-scan Bluetooth
  - "Uninstall Claude Buddy"
  - "Diagnose Claude Buddy"
```

Each branch:

### Update
```bash
# kill old daemon then pull
pkill -f claude-buddy-daemon || taskkill /F /IM uv.exe /T 2>nul
cd "$HOME/.claude-buddy"
git pull
uv sync --frozen
echo "$(cat VERSION.txt)" > .installed
nohup uv run claude-buddy-daemon > /tmp/cb-daemon.log 2>&1 &
```

### Repair
Re-run Phase 3.

### Uninstall
```bash
pkill -f claude-buddy-daemon || taskkill /F /IM uv.exe /T 2>nul
claude plugin uninstall claude-buddy-bridge 2>/dev/null
codex plugin uninstall claude-buddy-bridge-codex 2>/dev/null
rm -rf "$HOME/.claude-buddy"
# Keep device.json for easy re-pairing
echo "Uninstalled. device.json kept at ~/.config/claude-buddy/ — to fully remove, rm -rf ~/.config/claude-buddy"
```

### Diagnose
Re-run Phase 5.5.

---

## Hard Constraints

1. **Report progress with AskUserQuestion at each phase** — user always knows where we are
2. **Stop immediately on any bash failure** — do not pretend success
3. **Do NOT push code / modify daemon code** — this skill only installs, never changes product code
4. **Do NOT re-run completed phases** — detect `.installed` and go straight to submenu
