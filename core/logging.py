"""Logging setup. Logs to console and to data/outputs/run.log."""
import logging
import sys

from core import config

_CONFIGURED = False


def _configure() -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    formatter = logging.Formatter(fmt, datefmt="%H:%M:%S")

    root = logging.getLogger("ars")
    root.setLevel(logging.INFO)
    root.propagate = False

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    root.addHandler(stream)

    file_handler = logging.FileHandler(config.OUTPUTS_DIR / "run.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    _configure()
    return logging.getLogger(f"ars.{name}")
