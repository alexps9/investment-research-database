"""Shared logging setup. Writes to stderr + rotating file in HH_LOG_DIR."""

from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str = "hh_research", level: str = "INFO") -> logging.Logger:
    """Return a configured logger. Idempotent — safe to call multiple times."""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)-5s %(name)s :: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Stderr
    sh = logging.StreamHandler(sys.stderr)
    sh.setFormatter(fmt)
    logger.addHandler(sh)

    # Rotating file
    log_dir = Path(os.getenv("HH_LOG_DIR", "./data/logs"))
    log_dir.mkdir(parents=True, exist_ok=True)
    fh = RotatingFileHandler(
        log_dir / f"{name}.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    logger.propagate = False
    return logger
