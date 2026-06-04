# ============================================================
# config.py —— 硬件引脚与全局常量配置
#
# 面板版：ESP32-S3 触摸屏（ST7789 + CST816S，320×240 横屏）
# 闹钟版：ESP32-C3（WS2812 双灯 + MAX98357A 功放）
# ============================================================

# ── 设备型号（烧录时由 flash_device.py 注入）─────────────────
VARIANT = "panel"  # "panel" | "clock"

# ── 面板角色（可选值见 device/char_*.py）─────────────────────
# claude / cat / robot / ghost / among_us / creeper / kirby / pikachu
CHARACTER = "robot"

# ── 共用：BLE 配置 ────────────────────────────────────────────
BLE_NAME    = "Claude-Buddy"
NUS_SERVICE = "6e400001-b5a3-f393-e0a9-e50e24dcca9e"
NUS_RX      = "6e400002-b5a3-f393-e0a9-e50e24dcca9e"
NUS_TX      = "6e400003-b5a3-f393-e0a9-e50e24dcca9e"

# ── 共用：时序 ────────────────────────────────────────────────
FPS               = 20
HEARTBEAT_TIMEOUT = 30

# ── 共用：日志配置 ────────────────────────────────────────────
LOG_ENABLE = True           # 是否启用日志（False 时走串口输出）
LOG_MAX_FILES = 4           # 日志文件数量（循环轮转）
LOG_LINES_PER_FILE = 150    # 每个文件最大行数（总容量 4×150=600 行）

# ============================================================
# 面板版（ESP32-S3）引脚
# ============================================================

# ── 显示屏（ST7789，SPI）─────────────────────────────────────
LCD_WIDTH  = 240
LCD_HEIGHT = 320
SCREEN_W   = 320
SCREEN_H   = 240
SPI_BUS    = 2
SPI_FREQ   = 40_000_000
LCD_SCLK   = 39
LCD_MOSI   = 38
LCD_MISO   = 40
LCD_DC     = 42
LCD_CS     = 45
LCD_BL     = 1
FB_SIZE    = 28800

# ── 触摸屏（CST816S，I2C）────────────────────────────────────
I2C_BUS    = 0
I2C_FREQ   = 400_000
TP_SDA     = 48
TP_SCL     = 47
TP_ADDR    = 0x15
TP_REGBITS = 8

# ── 麦克风（I2S，面板版）─────────────────────────────────────
PANEL_MIC_SCK = 11
PANEL_MIC_WS  = 12
PANEL_MIC_SD  = 13

# ── 扬声器 MAX98357A（I2S，面板版）───────────────────────────
PANEL_SPK_SCK      = 14
PANEL_SPK_WS       = 15
PANEL_SPK_SD       = 16
PANEL_AMP_SD_PIN   = 17
PANEL_AMP_GAIN_PIN = 18

# ── SD 卡（SPI，面板版）─────────────────────────────────────
PANEL_SD_SPI_BUS = 1        # SPI 外设编号（1 或 2，避开屏幕的 SPI 2）
PANEL_SD_MOSI    = 38
PANEL_SD_SCLK    = 39
PANEL_SD_MISO    = 40
PANEL_SD_CS      = 41

# ============================================================
# 不带屏幕版（闹钟版）引脚
# ============================================================

# ── WS2812 双灯（闹钟版）─────────────────────────────────────
CLOCK_LED_PIN   = 21
CLOCK_LED_COUNT = 2

# ── 扬声器 MAX98357A（I2S，闹钟版）───────────────────────────
CLOCK_SPK_LRC      = 9   # I2S 左右声道时钟
CLOCK_SPK_BCLK     = 8   # I2S 位时钟
CLOCK_SPK_DIN      = 7   # I2S 数据输入
CLOCK_AMP_GAIN_PIN = 6   # 增益控制
CLOCK_AMP_SD_PIN   = 5   # 关断 / 静音控制

# ============================================================
# 语音配置（闹钟版）
# ============================================================

VOICE_ASSETS_DIR    = "/assets"
VOICE_HISTORY_DEPTH = 10
VOICE_WORK_MIN_S    = 20    # 工作中偶发播报最短间隔（秒）
VOICE_WORK_MAX_S    = 60    # 工作中偶发播报最长间隔（秒）
VOICE_IDLE_MIN_S    = 20    # 空闲偶发播报最短间隔（秒）
VOICE_IDLE_MAX_S    = 60    # 空闲偶发播报最长间隔（秒）

# ── BLE 传输参数 ──────────────────────────────────────────────
BLE_ADV_TIMEOUT_US  = 250_000
BLE_RECV_TIMEOUT_MS = 200
BLE_CHUNK_SIZE      = 20

# ── I2S 音频参数 ──────────────────────────────────────────────
I2S_BITS        = 16
I2S_RATE        = 8000
I2S_IBUF        = 4096
I2S_READ_BUF    = 1024

# ── 灯光渲染参数 ──────────────────────────────────────────────
LIGHT_MIN_QUEUE_FRAMES  = 20   # 队列状态最少显示帧数（×50ms）
LIGHT_RAINBOW_FRAMES    = 60   # 启动彩虹动画帧数
LIGHT_CONNECT_FRAMES    = 30   # 连接白闪帧数
LIGHT_DISCONNECT_FRAMES = 30   # 断线淡出帧数
LIGHT_CONNECT_BRIGHTNESS = 80  # 连接白闪亮度

LIGHT_IDLE_PERIOD   = 30   # 空闲呼吸 sin 周期（帧）
LIGHT_IDLE_MAX_V    = 40   # 空闲蓝色最大亮度

LIGHT_WORK_PERIOD   = 6    # 工作流水切换周期（帧）

LIGHT_PEND_PERIOD   = 24   # 待审批闪烁周期（帧）
LIGHT_PEND_ON       = 16   # 待审批亮帧数

LIGHT_DONE_FLASH_FRAMES = 18   # 完成快闪持续帧数
LIGHT_DONE_FLASH_PERIOD = 6    # 完成快闪周期（帧）
LIGHT_DONE_FLASH_ON     = 3    # 完成快闪亮帧数
LIGHT_DONE_PERIOD       = 30   # 完成呼吸 sin 周期（帧）
LIGHT_DONE_MAX_V        = 30   # 完成绿色最大亮度

LIGHT_ERR_PERIOD    = 2    # 出错交替周期（帧）

# ── 显示渲染参数 ──────────────────────────────────────────────
MAX_SESSIONS        = 5
HISTORY_MAX_LEN     = 20
BLINK_INTERVAL_S    = 0.4

# ── 语音引脚别名（voice_task.py 统一使用，两版本共用）────────
SPK_BCLK   = PANEL_SPK_SCK    if VARIANT == "panel" else CLOCK_SPK_BCLK
SPK_LRC    = PANEL_SPK_WS     if VARIANT == "panel" else CLOCK_SPK_LRC
SPK_DIN    = PANEL_SPK_SD     if VARIANT == "panel" else CLOCK_SPK_DIN
AMP_SD_PIN = PANEL_AMP_SD_PIN if VARIANT == "panel" else CLOCK_AMP_SD_PIN

# ── 日志配置 ──────────────────────────────────────────────────
LOG_ENABLE  = True       # True = 写文件；False = 走串口
LOG_STORAGE = "flash"    # "flash" | "sd"
LOG_FILE    = "/log/run.log"
LOG_LEVEL   = 20         # INFO=20, DEBUG=10

