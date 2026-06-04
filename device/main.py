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
            _log.info("user config loaded: LOG_STORAGE=%s", cfg.LOG_STORAGE)
    except OSError:
        _log.info("no user config, using defaults")

    if cfg.VARIANT == "clock":
        from light_renderer import LightRenderer
        _renderer = LightRenderer()
    else:
        from display_renderer import DisplayRenderer
        _renderer = DisplayRenderer()

    await _renderer.init()
    gc.collect()
    _log.info("after renderer: free=%d alloc=%d", gc.mem_free(), gc.mem_alloc())

    from transport import BleTransport
    _transport = BleTransport()
    gc.collect()
    _log.info("after BLE: free=%d alloc=%d", gc.mem_free(), gc.mem_alloc())

    _msg_queue = Queue()
    await asyncio.gather(ble_recv_task(), render_task())


asyncio.run(_main())
