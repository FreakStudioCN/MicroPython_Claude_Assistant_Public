# Daemon 状态机规格

本文档描述 `daemon/ble_daemon.py` 当前生产状态机。这里的“状态”指发送给设备的 wire 状态：

```json
{"ss": [{"n": "project", "s": "W", "m": "Read: README.md", "slot": "ab12cd34"}]}
```

daemon 内部没有单独保存一个 `state` enum。设备状态由每个 `_Session` 的字段实时推导出来：

| 内部字段 | 含义 |
| --- | --- |
| `tools` | 正在运行的工具集合，非空时通常显示 `W`，并带 `m` 工具描述 |
| `waiting` | 等待用户审批/选择/输入的计数，`>0` 时显示 `P` |
| `turn_active` | 从 `UserPromptSubmit` 到 `Stop` / `SessionEnd` 之间的 assistant turn |
| `completed_until` | 完成庆祝 `C` 的截止时间 |
| `dizzy_until` | 错误/失败 `E` 的截止时间 |
| `last_stop_ts` | 最近一次 stop 时间，用来过滤 stop 后乱序 `permission_prompt` |
| `last_activity_ts` | 最近活动时间，用于清理长期 idle session |

## 设备状态定义

| 状态 | 名称 | 设备语义 | 典型来源 |
| --- | --- | --- | --- |
| `I` | Idle | 当前 session 空闲或无可显示活动 | 无工具、无等待、无完成庆祝、无错误、turn 不活跃 |
| `W` | Working | Claude Code 正在处理、思考或运行工具 | `UserPromptSubmit`、`PreToolUse`、工具完成后等待 `Stop` |
| `P` | Pending | 需要用户在 Claude Code 终端里选择/审批/回答 | `Notification(permission_prompt)`、`Notification(elicitation_dialog)` |
| `C` | Completed | 本轮完成后的短庆祝态 | `Stop` 或兜底 `SessionEnd` |
| `E` | Error | 工具失败或 assistant turn 失败后的短错误态 | `PostToolUseFailure`、`StopFailure` |

## 显示优先级

`_session_to_wire()` 每次推送时按以下顺序推导显示状态。前面的条件命中后直接返回。

| 优先级 | 条件 | 输出状态 | 备注 |
| --- | --- | --- | --- |
| 1 | `dizzy_until > now` | `E` | 错误态最高优先级，避免被 P/W/C 覆盖 |
| 2 | `waiting > 0` | `P` | 用户交互优先于工具和完成庆祝 |
| 3 | 任一 `tools[*].status == "running"` | `W` + `m` | 工具运行优先于旧 `C` |
| 4 | `completed_until > now` | `C` | 仅当没有错误、等待、运行中工具时显示 |
| 5 | `turn_active == True` | `W` | 无工具时表示 Claude Code 正在思考 |
| 6 | `now - last_tool_start_ts < 0.4s` | `W` | 快速工具兜底，保证至少推一次 W |
| 7 | 以上都不满足 | `I` | 空闲 |

## 事件转换表

| 现态 | 转换条件 / hook | daemon 内部动作 | 次态 | 备注 |
| --- | --- | --- | --- | --- |
| 无 session | 任意已识别 hook 带新 `session_id` | 创建 `_Session`，根据 `cwd` 生成 `display_name` | 取决于事件 | 同 basename 多 session 会追加 session suffix |
| `I` | `UserPromptSubmit` | `turn_active=True`，清 `waiting/current_error` | `W` | 新 turn 开始 |
| `C` | `UserPromptSubmit`，无新工具/等待 | `turn_active=True`，不清 `completed_until` | `C` 到期后 `W` | 保留完成庆祝，避免连发 prompt 截断 C |
| `P` | `UserPromptSubmit` | 清 `waiting`，`turn_active=True` | `W` 或 `C` | 用户继续输入后离开旧等待态 |
| `P` 的旧 session | 新 session 同 `cwd` 收到 `user_prompt`，旧 session 无工具且 `turn_active=False` | 删除旧 stale waiting session | 新 session 为 `W` | 修复重启 Claude Code 后旧 P 残留 |
| 任意 | `PreToolUse`（`needs_approval=False`） | 写入 `tools`，清 `completed_until` | `W` + `m` | 真实工具活动优先于旧 C |
| `W` | `PostToolUse`，仍有其他 running tools | 删除完成的 tool | `W` + `m` | 显示下一个仍在运行的工具 |
| `W` | `PostToolUse`，tools 空且 `turn_active=True` | 保留 `turn_active` | `W` | 工具完成后 Claude 可能仍在生成回答 |
| 任意 | `PostToolUseFailure`（非 interrupt） | 删除对应 tool，进入错误态 | `E`，到期后按字段推导 | `dizzy_until = now + 3s` |
| 任意 | `Notification(permission_prompt)` | 若不在 stop 后 1s 乱序窗口：`waiting=1`，清 `completed_until` | `P` | 真实选择题/审批的主要路径 |
| 任意 | `Notification(elicitation_dialog)` | `waiting=1`，清 `completed_until` | `P` | Claude Code 主动询问用户输入 |
| 任意 | `Notification(idle_prompt)` | 只打印日志，不改状态 | 不变 | idle 不是选择题，不能让设备常驻 P |
| `W` / `P` / `I` | `Stop`，当前不在错误态 | 清 `tools/waiting`，`turn_active=False`，`completed_until=now+2s` | `C` | 正常完成 |
| `E` | `Stop`，`dizzy_until > now` 或仍有 `current_error` | 清 `tools/waiting/turn_active`，不设置 C | `E` 到期后 `I` | 错误结束不庆祝 |
| 任意 | `SessionEnd`，距离最近 `Stop < 10s` | 忽略 | 不变 | 防止 Stop 后重复庆祝 |
| `W` / `P` / `I` | `SessionEnd`，没有近期 Stop 且不在错误态 | 清 `tools/waiting/turn_active`，`completed_until=now+2s` | `C` | Stop 缺失时的完成兜底 |
| 任意 | `StopFailure` | `turn_active=False`，`waiting=0`，清 tools，进入错误态 | `E` | assistant turn 失败 |
| 任意 | 未识别 hook | 忽略 | 不变 | fail-open |

## 计时器转换表

不由 hook 直接触发，由 `_pusher_tick()` 按时间推进。

| 现态 | 条件 | 动作 | 次态 |
| --- | --- | --- | --- |
| `C` | `completed_until <= now` | mark dirty | 按字段推导（通常 `I` 或 `W`） |
| `E` | `dizzy_until <= now` | 清错误字段 | 按字段推导（通常 `I`） |
| 长期 idle session | `not tools`、`not turn_active`、`completed_until/dizzy_until` 到期，且 `now - last_activity_ts > 10s` | 删除 session | 从 `ss` 数组消失 |

## 多 session 显示名

设备 wire 的 `n` 字段最长 **12 字符**，由 `daemon.ble_daemon._generate_display_name` 生成：

- **无冲突**：`os.path.basename(cwd)[:12]`
- **同 basename 冲突**（同一 cwd 多个 Claude Code 终端，或不同 cwd 但 basename 相同）：`basename[:7] + "-" + session_id 后 4 位`，共 12 字符

后缀仅用于显示消歧；session 真正的唯一性靠 `session_id`，display name 不保证全局唯一。

## 关键不变量

| 不变量 | 原因 |
| --- | --- |
| `E` 必须能自动退出 | `dizzy_until` 到期后清错误字段，避免生产卡 E |
| `P` 只能来自真实用户交互 | `idle_prompt` 不得进入 P，否则 Claude 完成后可能假等待 |
| 工具运行时必须优先于 `C` 和 `turn_active` | 设备 panel 需要看到工具名 `m`，真实活动不能被庆祝遮挡 |
| `Stop` / `SessionEnd` 必须清 `tools/waiting/turn_active` | 完成后不能继续 W/P |
| `UserPromptSubmit` 不清 `completed_until` | 连发 prompt 时保留完整 C 动画 |
| 新 turn 的 `tool_start` / 真实等待会清 `completed_until` | 一旦有真实活动，旧 C 必须让位 |
| 同 cwd 旧 waiting session 可被新 session 回收 | Claude Code 重启后旧 P 不能长期残留 |
