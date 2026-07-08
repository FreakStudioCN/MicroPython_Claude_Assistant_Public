# main.py —— MicroPython 设备入口（所有形态共用）
#
# panel / dshell : 屏幕 + BLE
# clock          : 灯光 + 语音 + 振动 + BLE
# wizfi360       : 灯光 + 语音 + 振动 + WiFi TCP

try:
    import uasyncio as asyncio
except ImportError:
    import asyncio

import gc
import os
import config as cfg
from queue import Queue
import protocol as p
import logging

if cfg.LOG_ENABLE:
    from rotating_logger import install as _log_install
    _log_install(
        log_dir="/log",
        max_files=cfg.LOG_MAX_FILES,
        lines_per_file=cfg.LOG_LINES_PER_FILE,
        prefix="run",
        fmt="%(levelname)s:%(name)s:%(message)s"
    )
    logging.getLogger().setLevel(logging.INFO)
else:
    logging.basicConfig(level=logging.INFO)

_log = logging.getLogger("main")

_transport = None
_msg_queue = None
_renderer  = None


async def ble_recv_task():
    while True:
        _log.info("waiting for PC connection...")
        await _transport.connect()
        await _renderer.on_connect()
        _log.info("connected")
        try:
            while _transport.connected():
                line = await _transport.recv_line()
                _msg_queue.put_nowait(p.parse(line))
        except OSError:
            pass
        await _renderer.on_disconnect()
        _log.info("disconnected")


async def wifi_recv_task():
    while True:
        _log.info("waiting for PC connection...")
        await _transport.connect()
        await _renderer.on_connect()
        _log.info("connected")
        try:
            while _transport.connected():
                lid, line = await _transport.recv_line()
                msg = p.parse(line)
                if isinstance(msg, dict) and "cmd" in msg:
                    _log.info("cmd: %s", msg["cmd"])
                    name = getattr(cfg, "DEVICE_NAME", cfg.BLE_NAME)
                    await _transport.send(p.build_ack(msg["cmd"], ok=True, name=name), link_id=lid)
                elif msg is not None:
                    _msg_queue.put_nowait(msg)
        except OSError:
            pass
        await _renderer.on_disconnect()
        _log.info("disconnected")


async def render_task():
    while True:
        msg = await _msg_queue.get()
        if msg is not None:
            await _renderer.render(msg)


async def _main():
    global _msg_queue, _renderer, _transport

    _log.info("waiting 3s for mpremote connection...")
    await asyncio.sleep(3)
    gc.collect()
    _log.info("startup: free=%d alloc=%d", gc.mem_free(), gc.mem_alloc())

    # ── 挂载 SD 卡（面板版）──────────────────────────────────
    if cfg.VARIANT == "panel":
        try:
            import machine, sdcard
            sd_spi = machine.SPI(
                cfg.PANEL_SD_SPI_BUS,
                sck=machine.Pin(cfg.PANEL_SD_SCLK),
                mosi=machine.Pin(cfg.PANEL_SD_MOSI),
                miso=machine.Pin(cfg.PANEL_SD_MISO)
            )
            sd = sdcard.SDCard(sd_spi, machine.Pin(cfg.PANEL_SD_CS))
            os.mount(sd, "/sd")
            _log.info("SD card mounted at /sd")
        except Exception as e:
            _log.error("SD card mount failed: %s", e)

    # ── 加载用户配置 ──────────────────────────────────────────
    try:
        with open("/config.json", "r") as f:
            try:
                import ujson
            except ImportError:
                import json as ujson
            user_cfg = ujson.load(f)
            cfg.LOG_STORAGE = user_cfg.get("LOG_STORAGE", cfg.LOG_STORAGE)
            if cfg.VARIANT in ("clock", "wizfi360"):
                cfg.LIGHT_BRIGHTNESS = user_cfg.get("LIGHT_BRIGHTNESS", cfg.LIGHT_BRIGHTNESS)
                cfg.VIB_SENSOR_ENABLE = user_cfg.get("VIB_SENSOR_ENABLE", cfg.VIB_SENSOR_ENABLE)
                cfg.VIB_MOTOR_ENABLE = user_cfg.get("VIB_MOTOR_ENABLE", cfg.VIB_MOTOR_ENABLE)
            _log.info("user config loaded")
    except OSError:
        _log.info("no user config, using defaults")

    # ── 渲染器 ──────────────────────────────────────────────
    if cfg.VARIANT in ("clock", "wizfi360"):
        from light_renderer import LightRenderer
        _renderer = LightRenderer()
    else:
        from display_renderer import DisplayRenderer
        _renderer = DisplayRenderer()

    await _renderer.init()
    gc.collect()
    _log.info("after renderer: free=%d alloc=%d", gc.mem_free(), gc.mem_alloc())

    # ── 传输层 ──────────────────────────────────────────────
    if cfg.VARIANT == "wizfi360":
        from machine import UART, Pin
        wifi_uart = UART(
            cfg.WIFI_UART_PORT,
            115200,
            tx=Pin(cfg.WIFI_UART_TX),
            rx=Pin(cfg.WIFI_UART_RX),
            txbuf=cfg.WIFI_UART_TXBUF,
            rxbuf=cfg.WIFI_UART_RXBUF,
        )
        _log.info("UART%d tx=GP%d rx=GP%d",
                  cfg.WIFI_UART_PORT, cfg.WIFI_UART_TX, cfg.WIFI_UART_RX)

        from transport import WifiTransport
        _transport = WifiTransport(wifi_uart, cfg.WIFI_SSID, cfg.WIFI_PASSWORD,
                                   reset_pin=cfg.WIFI_RESET_PIN)
        gc.collect()
        _log.info("after transport: free=%d alloc=%d", gc.mem_free(), gc.mem_alloc())

        _msg_queue = Queue()
        await asyncio.gather(wifi_recv_task(), render_task())
    else:
        from transport import BleTransport
        _transport = BleTransport()
        gc.collect()
        _log.info("after BLE: free=%d alloc=%d", gc.mem_free(), gc.mem_alloc())

        _msg_queue = Queue()
        await asyncio.gather(ble_recv_task(), render_task())


if __name__ == "__main__":
    asyncio.run(_main())
