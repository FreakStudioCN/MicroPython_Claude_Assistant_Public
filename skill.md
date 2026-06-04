---
name: claude-buddy-setup
description: Set up the Claude Buddy hardware desktop pet — installs runtime, pairs BLE device, registers CLI hooks. Use when user asks to install/configure/update/repair/diagnose/uninstall Claude Buddy / 装/配/修/卸载 桌宠/Claude Buddy 硬件.
---

# Claude Buddy 装机 Skill

你正在帮用户装 Claude Buddy 硬件桌宠。**所有阶段都在用户机器上执行——不要 fork agent，不要 WebFetch，直接用 Bash 和 AskUserQuestion**。

## 全流程（6 phase）

按顺序跑，每个 phase 失败时停下来给用户报错。任何阶段碰到 unexpected → 用 AskUserQuestion 让用户决定继续 / 终止。

---

## Phase 0: Detect

```bash
# 写一个临时脚本检测环境，输出 JSON
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

**判定**:
- `is_wsl=true` → 退场：「WSL 里跑 BLE 不可用，请用 Native Windows 的 Claude Code」
- `daemon_installed=true && plugin_installed=true` → 跳子菜单：AskUserQuestion「Claude Buddy 已装。你要做什么？」选项：update / repair / uninstall / diagnose / exit
- `daemon_installed=true && plugin_installed=false` → 跳 Phase 4 注册 plugin（daemon 已就位但 plugin 没装）
- `daemon_installed=false` → 走完整 Phase 2-6
- `claude=missing && codex=missing` → 退场：「需要先装 Claude Code 或 Codex CLI」
- `python` 不是 3.11+ → Phase 1 装
- `uv=missing` 或 `git=missing` → Phase 1 装

---

## Phase 1: Bootstrap deps

只在缺时跑。**头部一次性 AskUserQuestion** 列出全部要跑的命令，用户一次 yes 批准所有 bash。

```
我要跑这些命令完成装机：
1. 装 Python 3.11+（如果缺）
2. 装 uv（Python 包管理器）
3. 装 git（如果缺）
4. clone https://github.com/freakstudio/claude-buddy 到 ~/.claude-buddy
5. uv sync --frozen 装 Python 依赖
6. 扫蓝牙配对桌宠
7. 给 Claude Code 注册 hook

全部允许吗？
```

### 装 Python（如果缺）

- macOS: `brew install python@3.11`
- Windows: `winget install --id Python.Python.3.11 --silent`
  - **重要**：装完后 `refreshenv` 或新开 shell（不然 PATH 没刷新）
  - 检测 Store Python alias 劫持：`where python` 看是不是 `WindowsApps\python.exe` 那个 alias——是的话让用户在「设置 → 应用 → 应用别名」关掉

### 装 uv

- macOS / Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows: `winget install --id astral-sh.uv --silent`
- fallback: `pip install --user uv`

### 装 git

- macOS: `xcode-select --install` 或 `brew install git`
- Windows: `winget install --id Git.Git --silent`

### Windows 加测

```powershell
# PowerShell ExecutionPolicy
$policy = Get-ExecutionPolicy -Scope CurrentUser
if ($policy -eq 'Restricted') {
    # 提示用户运行：
    # Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
}

# 检测 HTTP_PROXY / HTTPS_PROXY
if ($env:HTTP_PROXY) { echo "代理: $env:HTTP_PROXY" }
```

---

## Phase 2: Clone & sync

```bash
# Primary
git clone https://github.com/freakstudio/claude-buddy "$HOME/.claude-buddy" 2>&1
# Fallback if GitHub fails (国内用户)
# git clone https://gitee.com/freakstudio/claude-buddy-mirror "$HOME/.claude-buddy"

cd "$HOME/.claude-buddy"

# uv sync --frozen 锁死 lockfile，避免拉到新依赖
uv sync --frozen 2>&1
```

失败处理：
- `git clone` GitHub 不通 → fallback Gitee
- `uv sync --frozen` 失败 → 检查 lockfile drift / 网络 / Python 版本，重试一次；还失败让用户贴 stderr

---

## Phase 3: BLE 配对

**先提醒**:「macOS 第一次会弹蓝牙权限给终端 app，请点允许。」

直接跑 TUI 配对工具（V1 保留 TUI，AskUserQuestion 介入太复杂，V2 再拆 JSON 入口）：

```bash
cd "$HOME/.claude-buddy"
uv run claude-buddy-pair
```

pair_device.py 会扫蓝牙、列设备、让用户选、写 `device.json`（含 `paired_mac`）。退出码 0 表示配对成功。

验证：

```bash
# macOS / Linux: ~/.config/claude-buddy/device.json
# Windows:      %APPDATA%\claude-buddy\device.json
cat "$HOME/.config/claude-buddy/device.json" 2>/dev/null || \
cat "$APPDATA/claude-buddy/device.json" 2>/dev/null
```

字段必须含 `paired_mac`。没有就让用户重跑 `claude-buddy-pair`。

---

## Phase 4: Plugin 注册

repo 自己就是 Claude Code marketplace + plugin（`source: "./"`）。注册 + 装两步：

### Claude Code

```bash
cd "$HOME/.claude-buddy"
claude plugin marketplace add .
claude plugin install claude-buddy-bridge@claude-buddy
```

验证装好：

```bash
claude plugin list  # 应该看到 claude-buddy-bridge
```

### Codex（V1 同样用 marketplace 流程）

```bash
cd "$HOME/.claude-buddy"
codex plugin marketplace add .
codex plugin install claude-buddy-bridge@claude-buddy
```

如果 `codex plugin install` / `codex plugin marketplace` 子命令不存在（Codex 版本太老），暂时跳过 Codex 注册——用户在 Claude Code 里桌宠会正常亮，等 Codex 升级后再装。

**hook command 用 `${CLAUDE_PLUGIN_ROOT}`**——Claude 把 plugin 缓存到自己的目录后由 hook 系统展开此变量。daemon runtime 已在 Phase 2 装到 `~/.claude-buddy/`，hook_bridge 内部用 `Path.home()` 找它，跟 plugin cache 解耦。

---

## Phase 5: Smoke test

```bash
# 起 daemon（detached）
cd "$HOME/.claude-buddy"
# macOS / Linux
nohup uv run claude-buddy-daemon > /tmp/cb-daemon.log 2>&1 &
# Windows PowerShell:
# Start-Process -WindowStyle Hidden uv run claude-buddy-daemon

sleep 2

# 跑 smoke
uv run claude-buddy-smoke
```

smoke 输出 `[smoke] OK` 表示协议链路通。然后 AskUserQuestion 问用户：

> 桌宠现在亮了吗？应该会闪一下或显示 W (working) 状态。
> A) 亮了
> B) 没亮 / 不知道

- A → 装机完成 banner（往下 Phase 6）
- B → 进 Phase 5.5 诊断

---

## Phase 5.5: Diagnostic

按顺序排查：

```bash
# 1. daemon 在跑吗
netstat -an | grep 57320 || ss -an | grep 57320 || lsof -i :57320

# 2. daemon log 看错误
cat /tmp/cb-daemon.log | tail -50

# 3. BLE 连上了吗
grep -i "connected" /tmp/cb-daemon.log
grep -i "error\|failed" /tmp/cb-daemon.log
```

诊断决策：

| 现象 | 原因 | 处理 |
|---|---|---|
| daemon 没在 57320 监听 | daemon 起不来 | 看 /tmp/cb-daemon.log 找 traceback，让用户贴给客服 |
| daemon 起来了，log 没 "connected" | 设备没开 / 距离远 / 配对错 | 让用户检查设备电源 + 拉近距离；不行重跑 Phase 3 |
| log 有 "connected" 但桌宠不动 | 固件问题 | 设备断电再上电；不行联系客服 |
| `os: Linux` (含 WSL2) | BLE 不支持 | 退场 |

---

## Phase 6: 教 self-service

```
桌宠装好了！以后随时可以对我说：
  - "更新 Claude Buddy" → 拉最新 daemon + 重启
  - "修一下 Claude Buddy 配对" → 重新扫蓝牙
  - "卸载 Claude Buddy"
  - "诊断 Claude Buddy"
```

每个分支对应：

### Update
```bash
# kill 老 daemon 然后 pull
pkill -f claude-buddy-daemon || taskkill /F /IM uv.exe /T 2>nul
cd "$HOME/.claude-buddy"
git pull
uv sync --frozen
echo "$(cat VERSION.txt)" > .installed
nohup uv run claude-buddy-daemon > /tmp/cb-daemon.log 2>&1 &
```

### Repair
重跑 Phase 3。

### Uninstall
```bash
pkill -f claude-buddy-daemon || taskkill /F /IM uv.exe /T 2>nul
claude plugin uninstall claude-buddy-bridge 2>/dev/null
codex plugin uninstall claude-buddy-bridge-codex 2>/dev/null
rm -rf "$HOME/.claude-buddy"
# 保留 device.json 方便重装恢复配对
echo "已卸载。device.json 保留在 ~/.config/claude-buddy/——彻底删请 rm -rf ~/.config/claude-buddy"
```

### Diagnose
重跑 Phase 5.5。

---

## 强约束

1. **每个 phase 用 AskUserQuestion 报进度** —— 用户能知道走到哪
2. **任何 bash 失败立刻停** —— 不要假装成功
3. **不要 push code / 不要改 daemon 代码** —— 这个 skill 只是装机，不改产品代码
4. **不要重复跑 phase** —— 检测到 `.installed` 直接走子菜单
