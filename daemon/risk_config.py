#!/usr/bin/env python3
# risk_config.py —— 设备离线时的风险分级配置
#
# 用途：当设备离线时，根据操作风险等级决定是否自动批准：
#   - safe（只读）：自动批准
#   - normal（可逆写）：自动批准
#   - critical（破坏性）：CLI 提示用户确认
#
# 用户可编辑此文件自定义风险规则。

# ── 关键路径（写入这些路径视为 critical）──────────────
CRITICAL_PATHS = {
    # Git 配置和钩子
    ".git/config",
    ".git/hooks",

    # 敏感凭证
    ".env",
    "credentials.json",
    "id_rsa",
    "id_ed25519",
    ".ssh/",

    # 系统关键目录
    "/etc/",
    "C:\\Windows\\",
}

# ── 破坏性 Bash 命令模式（包含这些模式视为 critical）──
CRITICAL_BASH_PATTERNS = [
    # Git 破坏性操作
    "git branch -D",
    "git push --force",
    "git push -f",
    "git reset --hard",

    # 文件删除
    "rm -rf",
    "rm -fr",

    # 磁盘操作
    "dd if=",
    "> /dev/",
    "mkfs",
    "fdisk",
    "format ",

    # Windows 删除
    "del /s",
    "rmdir /s",
]

# ── 只读工具（始终 safe）────────────────────────────────
SAFE_TOOLS = {
    "Read",
    "Glob",
    "Grep",
    "WebFetch",
    "WebSearch",
}

# ── 需要审批的工具（来自 hook_bridge.py）─────────────────
APPROVAL_TOOLS = {
    "Bash",
    "Write",
    "Edit",
}
