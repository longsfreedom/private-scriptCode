from __future__ import annotations

import logging
from logging import Logger
from pathlib import Path


_LOGGER_CACHE: dict[str, Logger] = {}


def get_logger(name: str, log_dir: str = "runtime/logs") -> Logger:
    if name in _LOGGER_CACHE:
        return _LOGGER_CACHE[name]

    Path(log_dir).mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        file_handler = logging.FileHandler(
            Path(log_dir) / "automation.log",
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    _LOGGER_CACHE[name] = logger
    return logger
