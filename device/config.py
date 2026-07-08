# ============================================================
# config.py —— 硬件引脚与全局常量配置
#
# D-Shell 正式面板版：ESP32-S3（ST7789 + GT911 触摸 + WS2812×8 灯带）
# Panel 开发版面版：ESP32-S3（ST7789 + CST816S 触摸，320×240 横屏）
# Clock 闹钟版：ESP32-C3（WS2812 双灯 + MAX98357A 功放）
# ============================================================

# ── 设备型号（烧录时由 flash_device.py 注入）─────────────────
VARIANT = "panel"  # "panel" | "dshell" | "clock"

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
# D-Shell 面板版（ESP32-S3，第二面板硬件）
# ============================================================

# ── 显示屏（ST7789，SPI1）───────────────────────────────────
DSHELL_LCD_WIDTH  = 240
DSHELL_LCD_HEIGHT = 320
DSHELL_SCREEN_W   = 320
DSHELL_SCREEN_H   = 240
DSHELL_SPI_HOST   = 1
DSHELL_SPI_FREQ   = 40_000_000
DSHELL_LCD_SCK    = 39
DSHELL_LCD_MOSI   = 38
DSHELL_LCD_MISO   = -1     # 未连接
DSHELL_LCD_DC     = 45
DSHELL_LCD_CS     = 48
DSHELL_LCD_RST    = 40
DSHELL_LCD_BL     = 47
DSHELL_FB_SIZE    = 28800

# ── 触摸屏（GT911，I2C0）────────────────────────────────────
DSHELL_I2C_HOST   = 0
DSHELL_I2C_FREQ   = 100_000
DSHELL_TP_RST     = 1
DSHELL_TP_INT     = 2
DSHELL_TP_SCL     = 41
DSHELL_TP_SDA     = 42
DSHELL_TP_ADDR    = 0x5D
DSHELL_TP_REGBITS = 16

# ── 扬声器 MAX98357A（I2S1，D-Shell）─────────────────────────
DSHELL_SPK_SCK      = 17
DSHELL_SPK_WS       = 18
DSHELL_SPK_SD       = 16
DSHELL_AMP_SD_PIN   = 15
DSHELL_AMP_GAIN_PIN = 8

# ── WS2812（D-Shell 自带灯带）────────────────────────────────
DSHELL_LED_PIN   = 46
DSHELL_LED_COUNT = 8

# ── 按键（D-Shell）───────────────────────────────────────────
DSHELL_KEY_UP   = 9
DSHELL_KEY_DOWN = 3

# ── 蜂鸣器（D-Shell）─────────────────────────────────────────
DSHELL_BEEP_PIN = 5

# ============================================================
# 不带屏幕版（闹钟版）引脚
# ============================================================

# ── WS2812 双灯（闹钟版）─────────────────────────────────────
CLOCK_LED_PIN   = 21
CLOCK_LED_COUNT = 2
CLOCK_TIMER_ID  = 0   # machine.Timer ID（ESP32 硬件定时器）

# ── 扬声器 MAX98357A（I2S，闹钟版）───────────────────────────
CLOCK_SPK_LRC      = 9   # I2S 左右声道时钟
CLOCK_SPK_BCLK     = 8   # I2S 位时钟
CLOCK_SPK_DIN      = 7   # I2S 数据输入
CLOCK_AMP_GAIN_PIN = 6   # 增益控制
CLOCK_AMP_SD_PIN   = 5   # 关断 / 静音控制

# ── 振动传感器与马达（闹钟版）───────────────────────────────
CLOCK_VIB_SENSOR_PIN = 10  # 振动传感器（外部中断触发）
CLOCK_VIB_MOTOR_PIN  = 20  # 振动马达（输出）
VIB_SENSOR_ENABLE    = True  # 拍击检测开关（GPIO10 → 触发语音）
VIB_MOTOR_ENABLE     = True  # 振动马达开关（GPIO20 → 状态反馈）

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
LIGHT_BRIGHTNESS        = 80   # 全局亮度系数（1-100）

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

# ── 引脚别名（display_renderer.py / voice_task.py / main.py 统一使用）─
#   通过 VARIANT 自动选择对应硬件平台的引脚定义
if VARIANT == "dshell":
    # ── 显示 ──
    SPI_BUS   = DSHELL_SPI_HOST
    SPI_FREQ  = DSHELL_SPI_FREQ
    LCD_SCLK  = DSHELL_LCD_SCK
    LCD_MOSI  = DSHELL_LCD_MOSI
    LCD_MISO  = DSHELL_LCD_MISO
    LCD_DC    = DSHELL_LCD_DC
    LCD_CS    = DSHELL_LCD_CS
    LCD_BL    = DSHELL_LCD_BL
    LCD_WIDTH = DSHELL_LCD_WIDTH
    LCD_HEIGHT = DSHELL_LCD_HEIGHT
    SCREEN_W  = DSHELL_SCREEN_W
    SCREEN_H  = DSHELL_SCREEN_H
    FB_SIZE   = DSHELL_FB_SIZE
    # ── 触摸 ──
    I2C_BUS    = DSHELL_I2C_HOST
    I2C_FREQ   = DSHELL_I2C_FREQ
    TP_SCL     = DSHELL_TP_SCL
    TP_SDA     = DSHELL_TP_SDA
    TP_ADDR    = DSHELL_TP_ADDR
    TP_REGBITS = DSHELL_TP_REGBITS
    # ── 扬声器 ──
    SPK_BCLK   = DSHELL_SPK_SCK
    SPK_LRC    = DSHELL_SPK_WS
    SPK_DIN    = DSHELL_SPK_SD
    AMP_SD_PIN = DSHELL_AMP_SD_PIN
    # ── SD 卡（D-Shell 暂不支持）─
    PANEL_SD_CS = -1
elif VARIANT == "panel":
    SPI_BUS    = 2
    SPI_FREQ   = 40_000_000
    LCD_SCLK   = 39
    LCD_MOSI   = 38
    LCD_MISO   = 40
    LCD_DC     = 42
    LCD_CS     = 45
    LCD_BL     = 1
    LCD_WIDTH  = 240
    LCD_HEIGHT = 320
    SCREEN_W   = 320
    SCREEN_H   = 240
    FB_SIZE    = 28800
    I2C_BUS    = 0
    I2C_FREQ   = 400_000
    TP_SDA     = 48
    TP_SCL     = 47
    TP_ADDR    = 0x15
    TP_REGBITS = 8
    SPK_BCLK   = PANEL_SPK_SCK
    SPK_LRC    = PANEL_SPK_WS
    SPK_DIN    = PANEL_SPK_SD
    AMP_SD_PIN = PANEL_AMP_SD_PIN
    # SD 卡引脚已在 PANEL_SD_* 中定义
else:  # clock / wizfi360（wizfi360 别名在下方 if 块末尾重设）
    SPK_BCLK   = CLOCK_SPK_BCLK
    SPK_LRC    = CLOCK_SPK_LRC
    SPK_DIN    = CLOCK_SPK_DIN
    AMP_SD_PIN = CLOCK_AMP_SD_PIN

# ── 日志配置 ──────────────────────────────────────────────────
LOG_ENABLE  = True       # True = 写文件；False = 走串口
LOG_STORAGE = "flash"    # "flash" | "sd"
LOG_FILE    = "/log/run.log"
LOG_LEVEL   = 20         # INFO=20, DEBUG=10

# ── WizFi360 WiFi TCP 配置（VARIANT == "wizfi360" 时生效）────────
#    此块独立于 BLE / ESP32 逻辑，新增不影响原有三种形态。
if VARIANT == "wizfi360":
    # ── WiFi 凭据（烧录时自动注入）──────────────────────────────
    WIFI_SSID       = "CU_kM7v"         # 烧录时自动注入
    WIFI_PASSWORD   = "a7tmyakw"        # 烧录时自动注入
    WIFI_STATIC_IP   = ""               # 静态 IP（空 = DHCP）
    WIFI_GATEWAY     = ""
    WIFI_NETMASK     = "255.255.255.0"
    # ── RP2040 UART → WizFi360 ──────────────────────────────────
    WIFI_UART_PORT  = 1                 # RP2040 UART1
    WIFI_UART_TX    = 4                 # GP4 → WizFi360 RX
    WIFI_UART_RX    = 5                 # GP5 → WizFi360 TX
    WIFI_UART_TXBUF = 1024
    WIFI_UART_RXBUF = 8192
    WIFI_RESET_PIN  = 20                # WizFi360 RST → RP2040 GP20
    TCP_PORT        = 57321             # 设备端 TCP Server 端口
    # ── WS2812 灯光 ──
    CLOCK_LED_PIN   = 16
    CLOCK_LED_COUNT = 2
    CLOCK_TIMER_ID  = -1  # machine.Timer ID（RP2040 虚拟定时器）
    # ── MAX98357A 扬声器（I2S）──
    CLOCK_SPK_BCLK     = 11             # I2S 位时钟 → MAX98357A BCLK
    CLOCK_SPK_LRC      = 12             # I2S 左右声道时钟 → MAX98357A LRC
    CLOCK_SPK_DIN      = 13             # I2S 数据输入 → MAX98357A DIN
    CLOCK_AMP_GAIN_PIN = 1              # 增益控制 → MAX98357A GAIN
    CLOCK_AMP_SD_PIN   = 0              # 关断 / 静音控制 → MAX98357A SD
    # ── 振动传感器与马达 ──
    CLOCK_VIB_SENSOR_PIN = 18           # 振动传感器（外部中断触发）
    CLOCK_VIB_MOTOR_PIN  = 17           # 振动马达（输出）
    # ── 引脚别名（必须在 CLOCK_* 覆盖之后，否则拿到 ESP32 默认值）─
    SPK_BCLK   = CLOCK_SPK_BCLK
    SPK_LRC    = CLOCK_SPK_LRC
    SPK_DIN    = CLOCK_SPK_DIN
    AMP_SD_PIN = CLOCK_AMP_SD_PIN
    DEVICE_NAME     = "Claude-Buddy-WiFi-01"

