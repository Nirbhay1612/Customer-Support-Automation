
"""
Centralized logging configuration for AI Customer Support Automation.

Provides consistent console and file logging across application modules.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from config import settings


# ============================================================
# Paths & Constants
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "application.log"

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)

DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_HANDLER_MARKER = "_ai_customer_support_handler"


# ============================================================
# Logging Configuration
# ============================================================

def setup_logger() -> logging.Logger:
    """
    Configure application-wide logging.

    Adds console and file handlers without duplicating handlers
    when initialization is called multiple times.

    Returns:
        The configured root logger.
    """
    logger = logging.getLogger()

    log_level = getattr(
        logging,
        settings.LOG_LEVEL.upper(),
        logging.INFO,
    )

    logger.setLevel(log_level)

    # Reuse our own handlers if logging was already configured.
    existing_handler_types = {
        getattr(handler, _HANDLER_MARKER, None)
        for handler in logger.handlers
    }

    formatter = logging.Formatter(
        fmt=LOG_FORMAT,
        datefmt=DATE_FORMAT,
    )

    # Console handler
    if "console" not in existing_handler_types:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        setattr(console_handler, _HANDLER_MARKER, "console")
        logger.addHandler(console_handler)

    # File handler
    if "file" not in existing_handler_types:
        LOG_DIR.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            LOG_FILE,
            encoding="utf-8",
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        setattr(file_handler, _HANDLER_MARKER, "file")
        logger.addHandler(file_handler)

    return logger


# ============================================================
# Logger Factory
# ============================================================

def get_logger(name: str | None = None) -> logging.Logger:
    """
    Return a logger for an application module.

    Args:
        name: Module name, typically __name__.

    Returns:
        A standard Python logger.
    """
    return logging.getLogger(name or "ai_customer_support")


# ============================================================
# Initialize Logging
# ============================================================

app_logger = setup_logger()
