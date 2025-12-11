"""Logging configuration for rally-tui."""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from rally_tui.user_settings import UserSettings

# Module-level logger
logger = logging.getLogger("rally_tui")

# Flag to track if logging has been initialized
_initialized = False


def setup_logging(settings: UserSettings | None = None) -> logging.Logger:
    """Configure logging for rally-tui.

    Sets up both file and stderr handlers. File logs go to
    ~/.config/rally-tui/rally-tui.log with rotation.

    Args:
        settings: User settings to get log level. If None, uses INFO.

    Returns:
        The configured logger instance.
    """
    global _initialized

    if _initialized:
        return logger

    # Import here to avoid circular imports
    from rally_tui.user_settings import UserSettings

    if settings is None:
        settings = UserSettings()

    # Get log level from settings
    level_name = settings.log_level
    level = getattr(logging, level_name, logging.INFO)

    # Configure the rally_tui logger
    logger.setLevel(level)

    # Prevent propagation to root logger
    logger.propagate = False

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler with rotation (5MB max, keep 3 backups)
    log_file = settings.LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)

    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5MB
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Stderr handler for ERROR and above (visible if app crashes)
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.ERROR)
    stderr_handler.setFormatter(formatter)
    logger.addHandler(stderr_handler)

    _initialized = True
    logger.info(f"Logging initialized at level {level_name}")

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Get a logger for a specific module.

    Args:
        name: Module name (e.g., 'rally_tui.app'). If None, returns root rally_tui logger.

    Returns:
        Logger instance for the module.
    """
    if name is None:
        return logger
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """Change the log level at runtime.

    Args:
        level: New log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    level_value = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level_value)

    # Update file handler level (first handler)
    for handler in logger.handlers:
        if isinstance(handler, RotatingFileHandler):
            handler.setLevel(level_value)
            break

    logger.info(f"Log level changed to {level.upper()}")
