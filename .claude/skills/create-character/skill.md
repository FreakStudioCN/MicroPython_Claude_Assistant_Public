# 创建面板角色 (create-character)

帮助用户为 ESP32-S3 面板版创建新的 LVGL 动画角色。

## 前置知识

### 角色系统架构

角色代码位于 `device/char_<name>.py`，在设备端运行（MicroPython + LVGL）。`display_renderer.py` 启动时自动加载：

```python
_char_mod = __import__("char_" + cfg.CHARACTER)
_CharClass = getattr(_char_mod, "<Name>Character")
self._character = _CharClass()
self._character.build(panel, face_x, face_y, FACE_SIZE)  # face_x=105, face_y=45, FACE_SIZE=110
```

注册角色：修改 `device/config.py` 的 `CHARACTER = "<name>"` 字段。

### Character 基类 API

`device/character.py` 定义了三个方法，子类只需实现 `build` 和 `tick`：

```
class Character:
    def build(self, panel, x, y, size)     # 创建所有 LVGL 对象
    def tick(self, state, frame) -> (ox, oy)  # 返回偏移量
    def apply_swing(self, ox, oy)          # 基类实现，遍历 _objs 整体偏移
```

- `build()`：在 `panel`（lv.obj 容器）上创建所有 `lv.obj`，坐标相对于 `(x, y)`，大小上限 `size×size`
- `tick()`：每 150ms 调用一次，`frame` 在 0~7 循环
- `apply_swing()`：遍历 `self._objs`，把每个对象的 base_x/base_y + (ox, oy) 设回去

### 状态常量

```python
S_IDLE    = "I"  # 空闲
S_WORKING = "W"  # 工作中
S_PENDING = "P"  # 待审批
S_DONE    = "C"  # 完成
S_ERROR   = "E"  # 出错
```

### LVGL 可用 API（ESP32-S3 MicroPython 约束）

面板版使用 **ST7789 320×240 横屏**，角色渲染区 110×110 像素。可用 API 仅限基本形状：

| API | 用途 |
|-----|------|
| `lv.obj(panel)` | 创建矩形/圆形容器 |
| `obj.set_pos(x, y)` | 绝对坐标 |
| `obj.set_size(w, h)` | 宽高 |
| `obj.set_style_radius(r, lv.PART.MAIN)` | 圆角 (`lv.RADIUS_CIRCLE` = 圆形) |
| `obj.set_style_bg_color(color, lv.PART.MAIN)` | 背景色 |
| `obj.set_style_border_width(0, lv.PART.MAIN)` | 关掉边框（通常需要） |

不支持：外部图片、canvas 绘图、字体图标、svg。

颜色用 `lv.color_hex(0xRRGGBB)` 创建。

### 文件与类命名约定

| 文件名 | 类名 | CHARACTER 字段 |
|--------|------|----------------|
| `char_cat.py` | `CatCharacter` | `cat` |
| `char_robot.py` | `RobotCharacter` | `robot` |
| `char_ghost.py` | `GhostCharacter` | `ghost` |
| `char_among_us.py` | `AmongUsCharacter` | `among_us` |
| `char_creeper.py` | `CreeperCharacter` | `creeper` |
| `char_kirby.py` | `KirbyCharacter` | `kirby` |
| `char_pikachu.py` | `PikachuCharacter` | `pikachu` |

命名规则：`char_<name>.py` → 将 `<name>` 按 `_` 拆分，每部分首字母大写 + `Character`。

## 工作流程

### 步骤 1：理解需求

询问用户想要什么角色（参考图片、文字描述、已有的像素图等）。明确：
- 角色大小（建议在 100×100 像素以内）
- 主要颜色搭配
- 不同状态的颜色变化（建议关键状态有明显差异）
- 是否需要动画（跳、晃、颜色闪）

### 步骤 2：创建角色文件

在 `device/` 下创建 `char_<name>.py`，使用以下模板：

```python
import lvgl as lv
from character import Character
from state import S_IDLE, S_WORKING, S_PENDING, S_DONE, S_ERROR

# 8帧摆动表（可选，直接抄或自定义）
_SWING = {
    S_IDLE:    ( 0,  1,  2,  1,  0, -1, -2, -1),
    S_WORKING: ( 0,  2,  4,  2,  0, -2, -4, -2),
    S_PENDING: ( 0,  4,  0, -4,  0,  4,  0, -4),
    S_DONE:    ( 0,  2,  4,  2,  0, -2, -4, -2),
    S_ERROR:   ( 0,  4,  8,  4,  0, -4, -8, -4),
}
_JUMP_Y = (0, -3, -6, -3, 0, 0, 0, 0)

# 各状态颜色映射
_COLORS = {
    S_IDLE:    (lv.color_hex(0xF4A460), lv.color_hex(0xCD853F)),
    S_WORKING: (lv.color_hex(0x64B5F6), lv.color_hex(0x1E88E5)),
    S_PENDING: (lv.color_hex(0xFFD54F), lv.color_hex(0xF9A825)),
    S_DONE:    (lv.color_hex(0x81C784), lv.color_hex(0x388E3C)),
    S_ERROR:   (lv.color_hex(0xEF5350), lv.color_hex(0xC62828)),
}


class <Name>Character(Character):

    def build(self, panel, x, y, size):
        self._objs = []; self._bx = []; self._by = []

        def mk(px, py, pw, ph, color, r=4):
            o = lv.obj(panel)
            o.set_pos(x + px, y + py)
            o.set_size(pw, ph)
            o.set_style_radius(r, lv.PART.MAIN)
            o.set_style_bg_color(color, lv.PART.MAIN)
            o.set_style_border_width(0, lv.PART.MAIN)
            self._objs.append(o); self._bx.append(x + px); self._by.append(y + py)
            return o

        # ── 在这里用 mk() 构建你的角色 ──
        # 例如：头、身体、眼睛、嘴、腿等
        self._head = mk(10, 5, 90, 60, lv.color_hex(0xF4A460), 12)
        mk(30, 30, 20, 20, lv.color_hex(0xFFFFFF), 10)  # 左眼白
        mk(60, 30, 20, 20, lv.color_hex(0xFFFFFF), 10)  # 右眼白
        mk(35, 35, 10, 10, lv.color_hex(0x111111), 5)   # 左瞳孔
        mk(65, 35, 10, 10, lv.color_hex(0x111111), 5)   # 右瞳孔
        self._body = mk(20, 70, 70, 40, lv.color_hex(0xCD853F), 8)

    def tick(self, state, frame):
        if state == S_WORKING:
            self._head.set_style_bg_color(_COLORS[S_WORKING][0], lv.PART.MAIN)
            self._body.set_style_bg_color(_COLORS[S_WORKING][1], lv.PART.MAIN)
        elif state == S_ERROR:
            self._head.set_style_bg_color(_COLORS[S_ERROR][0], lv.PART.MAIN)
            self._body.set_style_bg_color(_COLORS[S_ERROR][1], lv.PART.MAIN)
        elif state == S_DONE:
            self._head.set_style_bg_color(_COLORS[S_DONE][0], lv.PART.MAIN)
            self._body.set_style_bg_color(_COLORS[S_DONE][1], lv.PART.MAIN)
        else:
            self._head.set_style_bg_color(_COLORS[S_IDLE][0], lv.PART.MAIN)
            self._body.set_style_bg_color(_COLORS[S_IDLE][1], lv.PART.MAIN)

        if state == S_DONE:
            return (_SWING[state][frame], _JUMP_Y[frame])
        return (_SWING[state][frame], 0)
```

### 步骤 3：注册角色

编辑 `device/config.py`，修改行：

```python
CHARACTER = "<name>"
```

### 步骤 4：告知用户

通知用户需要重新烧录设备才能看到新角色。

## 设计指导

### 布局参考

角色绘制区左上角 `(x, y)`，大小 110×110。布局参考：

- 头部：`mk(5~20, 0~25, 70~100, 40~70, ...)`
- 耳朵/天线：`mk(..., ..., 10~30, 10~34, ...)` 在头部上方
- 眼睛：`mk(..., ..., 10~24, 10~20, ...)` 在头部中间
- 嘴巴：`mk(..., ..., 10~50, 4~10, ...)` 在头部下方
- 身体：`mk(10~30, 65~80, 60~90, 25~45, ...)` 在头部下方
- 手臂/腿：可选，在身体两侧/下方

### 常用颜色

```python
_BK = lv.color_hex(0x000000)  # 黑
_WH = lv.color_hex(0xFFFFFF)  # 白
_GY = lv.color_hex(0x888888)  # 灰
_RD = lv.color_hex(0xE53935)  # 红
_GR = lv.color_hex(0x4CAF50)  # 绿
_BL = lv.color_hex(0x2196F3)  # 蓝
_YL = lv.color_hex(0xFFC107)  # 黄
_SK = lv.color_hex(0xFFCC80)  # 肤色
```

### 状态变化模式

**模式一：整体变色**（参考 `ClaudeCharacter` / `CatCharacter`）

整个角色跟随状态切换颜色，用 `_set_all()` / `_set_fur()` 批量修改。

**模式二：局部动画**（参考 `RobotCharacter`）

不同状态有不同的视觉表现：
- `S_WORKING`：眼睛交替闪烁（利用 frame 奇偶）
- `S_ERROR`：红色闪烁
- `S_DONE`：绿色 + 跳跃动画

**模式三：静止 + 仅颜色**（参考 `NinjaCharacter`）

形状不变，仅整体或局部换色，适合几何风格角色。

## 参考角色文件

查阅现有角色文件了解实现风格：
- `device/char_cat.py` — 猫（眼睛/胡须/耳朵，`_set_fur` 批量变色）
- `device/char_robot.py` — 机器人（天线/LED 眼，工作态交替眨眼）
- `device/char_ghost.py` — 幽灵
- `device/char_among_us.py` — Among Us 角色
- `device/char_creeper.py` — Minecraft Creeper
- `device/char_custom.py` — 忍者示例（简洁模板）
