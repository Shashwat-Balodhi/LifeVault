"""
LifeVault Logger
-----------------
Provides a pre-configured logger with console + file output.
Usage:
    from backend.utils.logger import get_logger
    logger = get_logger(__name__)
"""

import logging
import sys
from pathlib import Path

# ── Log file location ────────────────────────────────────────────────────────
LOG_DIR = Path(__file__).resolve().parents[2] / "data" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "lifevault.log"


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Create or retrieve a named logger with consistent formatting."""
    logger = logging.getLogger(name)

    if logger.handlers:  # avoid duplicate handlers on reimport
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)-30s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger
