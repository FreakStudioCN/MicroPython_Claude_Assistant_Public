# Cross-CLI Plugin Distribution Plan v2.3

**Date**: 2026-05-12  
**Status**: current planning baseline before push  
**Scope**: Claude Buddy V1 install/onboarding path for developer users on Windows and macOS.

---

## 0. Corrections From Review

### 0.1 Windows first install is a ship blocker

The previous plan treated Bash/POSIX commands as the default install surface:

- `/tmp`, `cat`, `uname`, `grep`, `head`, `which`
- `nohup`, `sleep`, `tail`, `lsof`, `ss`
- mixed `pkill || taskkill`

That is not a valid Windows product path. V1 explicitly targets Win-x64, so the onboarding skill must branch by OS and use native commands:

- Windows: PowerShell-first, using `$env:USERPROFILE`, `$env:APPDATA`, `Test-Path`, `Get-Command`, `Start-Process`, `Get-NetTCPConnection` or `netstat`.
- macOS: zsh/bash is acceptable, using `$HOME`, `nohup`, `lsof`, `tail`.
- WSL: detect and stop with a clear message. BLE is not part of the V1 WSL path.

After Python 3.11+ exists, prefer small Python helper scripts for cross-platform checks instead of maintaining long shell snippets in the skill.

### 0.2 Skill distribution is independent

The setup skill is not required to be discovered through the Claude Code plugin. We can distribute it ourselves.

V1 decision:

- Skill is the onboarding product surface.
- Plugin is only the hook delivery mechanism.
- Daemon runtime is installed separately at `~/.claude-buddy`.
- The repo may keep `skill.md` as the source copy, but the shipping package must install it into the expected skill location or deliver it through our own installer/npm path.

Implication: a root-level `skill.md` in the repo is acceptable as source material, but plugin install alone must not be assumed to expose the skill.

### 0.3 Current hook command choice

For V1, the current hook command is acceptable:

```json
"command": "python \"${CLAUDE_PLUGIN_ROOT}/daemon/hook_bridge.py\""
```

Reason: `hook_bridge.py` is stdlib-only and can fail-open quickly. It can spawn the runtime daemon from `~/.claude-buddy` without requiring the hook command itself to run inside the daemon venv.

Do not keep claiming that V1 hook command must use `claude-buddy-hook-bridge` entrypoint. The entrypoint remains useful for direct/manual execution and smoke tests, but the plugin hook can use the bundled script.

---

## 1. Product Architecture

### Components

| Component | Owner | Installed Where | Purpose |
|---|---|---|---|
| Setup skill | our distribution path | Claude skill location or ad-hoc installer path | Guided install, repair, update, diagnose |
| Plugin | Claude Code plugin system | Claude plugin cache | Registers hooks |
| Hook bridge | bundled in plugin | `${CLAUDE_PLUGIN_ROOT}/daemon/hook_bridge.py` | Sends hook envelopes to local daemon; auto-spawns daemon best-effort |
| Daemon runtime | git clone + uv | `~/.claude-buddy` | BLE daemon, pair tool, smoke tool |
| Config | runtime | `~/.config/claude-buddy` for V1 | `device.json`, user config |

### V1 user promise

User gets from "install Claude Buddy" to hardware response in under 5 minutes on:

- Windows 11 x64
- macOS arm64/x64

V1 does not support:

- WSL BLE path
- Linux consumer path
- OS boot autostart
- signed native installer
- PyInstaller binary packaging

---

## 2. Install Flow v2.3

### Phase 0: Detect

Skill first detects OS and chooses a native command path.

Windows detection must use PowerShell:

```powershell
$result = [ordered]@{
  os = "Windows"
  python = (python --version 2>$null)
  uv = (uv --version 2>$null)
  git = (git --version 2>$null)
  claude = (claude --version 2>$null)
  codex = (codex --version 2>$null)
  daemon_installed = Test-Path "$env:USERPROFILE\.claude-buddy\pyproject.toml"
}
$result | ConvertTo-Json -Compress
```

macOS detection can use shell:

```bash
python --version
uv --version
git --version
claude --version
test -f "$HOME/.claude-buddy/pyproject.toml"
```

No `/tmp` script generation in Windows flow. No `uname` as the primary Windows detector.

### Phase 1: Bootstrap dependencies

Only install what is missing.

Windows:

- Python: `winget install --id Python.Python.3.11 --silent`
- uv: `winget install --id astral-sh.uv --silent`
- git: `winget install --id Git.Git --silent`
- After installs, open a new shell or refresh PATH before continuing.
- Detect Microsoft Store Python alias and instruct the user to disable it if `where python` points to `WindowsApps`.

macOS:

- Python: `brew install python@3.11`
- uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- git: `xcode-select --install` or `brew install git`

Permission model: do not ask for one blanket approval covering unrelated install, network, background-process, and delete operations. Ask at phase boundaries with the exact commands that will run.

### Phase 2: Clone and sync runtime

Windows:

```powershell
git clone https://github.com/freakstudio/claude-buddy "$env:USERPROFILE\.claude-buddy"
Set-Location "$env:USERPROFILE\.claude-buddy"
uv sync --frozen
```

macOS:

```bash
git clone https://github.com/freakstudio/claude-buddy "$HOME/.claude-buddy"
cd "$HOME/.claude-buddy"
uv sync --frozen
```

Fallbacks:

- Gitee mirror for GitHub-blocked users.
- ZIP fallback only if git is blocked.

### Phase 3: Pair BLE device

V1 keeps the existing TUI pair flow:

```bash
uv run claude-buddy-pair
```

Acceptance:

- `device.json` exists.
- `paired_mac` is present.
- transport uses `paired_mac` before fallback to device name.

### Phase 4: Install plugin

Install plugin after runtime sync:

```bash
claude plugin marketplace add .
claude plugin install claude-buddy-bridge@claude-buddy
```

Codex remains manual/backlog unless the installed Codex CLI version supports equivalent plugin commands.

### Phase 5: Start daemon and smoke test

Windows:

```powershell
Set-Location "$env:USERPROFILE\.claude-buddy"
Start-Process -WindowStyle Hidden uv -ArgumentList "run claude-buddy-daemon"
Start-Sleep -Seconds 2
uv run claude-buddy-smoke
```

macOS:

```bash
cd "$HOME/.claude-buddy"
nohup uv run claude-buddy-daemon > /tmp/cb-daemon.log 2>&1 &
sleep 2
uv run claude-buddy-smoke
```

Smoke test validates daemon protocol acceptance. It does not prove BLE/display success; the skill still asks the user whether the hardware responded.

### Phase 5.5: Diagnose

Windows:

- Check port: `netstat -ano | findstr 57320`
- Check process: `Get-Process | Where-Object { $_.ProcessName -match "uv|python" }`
- Check log path shown by daemon startup.

macOS:

- Check port: `lsof -i :57320`
- Check log: `tail -50 /tmp/cb-daemon.log`
- Check BLE connected line in daemon log.

### Phase 6: Update / repair / uninstall

Keep destructive actions separate from install/update approval.

Update:

- Stop old daemon.
- `git pull`
- `uv sync --frozen`
- Restart daemon.
- Run smoke.

Repair:

- Re-run Phase 3 pair.
- Re-run Phase 5 smoke/confirm.

Uninstall:

- Uninstall plugin.
- Stop daemon.
- Remove `~/.claude-buddy` only after explicit confirmation.
- Preserve `device.json` by default.

---

## 3. Code Changes Required Before Push

### Required

1. Ignore or remove `codex_stderr.txt`.
   - It is a local transcript/debug artifact and should not be pushed.

2. Update `skill.md` to be OS-branching.
   - Replace Bash-only Phase 0 with Windows PowerShell + macOS shell variants.
   - Replace `nohup`/`grep`/`tail`/`lsof` commands with Windows equivalents in Windows sections.
   - Remove blanket "approve all bash" language.

3. Align docs with current hook command.
   - V1 plugin hook uses `python "${CLAUDE_PLUGIN_ROOT}/daemon/hook_bridge.py"`.
   - Do not document `uv run --project ~/.claude-buddy claude-buddy-hook-bridge` as the V1 plugin hook unless code is changed to match.

4. Add a clear "plugin-only install is insufficient" message to user-facing docs.
   - Product path starts with the setup skill.
   - Plugin install alone registers hooks but does not install runtime dependencies or pair BLE.

### Strongly Recommended

5. Add a small cross-platform installer helper after Python exists.
   - Example: `scripts/install_doctor.py` or `scripts/install_status.py`.
   - It returns JSON status for Python/uv/git/daemon/plugin/device/log.
   - This reduces duplicated PowerShell/bash logic inside `skill.md`.

6. Add a Windows smoke runbook.
   - Fresh Win11 VM.
   - No Python, no uv, no git.
   - Store Python alias enabled.
   - Corporate proxy/GitHub blocked case noted, even if not fully solved.

7. Decide whether `research/install_mechanism_v1.md` is historical.
   - If kept, mark it as superseded by this v2.3 plan.

---

## 4. Push Readiness Checklist

Do not push until:

- `git status --short` has no `codex_stderr.txt`.
- `skill.md` no longer assumes Bash on Windows.
- `hooks/hooks.json` and this plan describe the same hook command.
- `uv run claude-buddy-smoke` passes against a local daemon.
- Windows start command is validated with `Start-Process`, not `nohup`.
- macOS path still works with the existing shell flow.

Can push protocol/daemon commits separately if needed:

- A-1 pyproject + entrypoints
- A-2 hook auto-spawn
- A-3 paired_mac
- A-4 BLE send failure handling
- A-5 resend after BLE reconnect + smoke validation

But do not market the branch as "install flow ready" until the Windows skill path is fixed.

---

## 5. Backlog

V2/backlog, not required for V1 push:

- OS boot autostart via launchd / Task Scheduler / systemd user.
- Native signed installer.
- PyInstaller single-file daemon.
- BLE PIN/manufacturer_data pairing.
- JSON pair/scan API to replace TUI.
- Config path migration to OS-native locations.
- Log rotation and standard log directories.
- Protocol hello/version handshake.
