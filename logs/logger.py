"""
Logger — Core Python logging configuration.
=============================================

Sets up the standard Python logging framework with file rotation,
console output, and structured formatting.

Features:
    • RotatingFileHandler (avoids huge log files)
    • StreamHandler (console output)
    • Standardized format string for all modules
    • Log level configuration (INFO, DEBUG, ERROR, etc.)
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger(
    log_dir: str | Path = "logs",
    log_file: str = "agent.log",
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 3,
) -> logging.Logger:
    """
    Configure the root logger for the Pinterest Agent.

    Sets up both a rotating file handler and a console stream handler.

    Args:
        log_dir:      Directory to store log files.
        log_file:     Name of the primary log file.
        level:        Logging level (e.g., logging.INFO, logging.DEBUG).
        max_bytes:    Maximum size of a single log file before rotation.
        backup_count: Number of backup log files to keep.

    Returns:
        The configured root logger.
    """
    path = Path(log_dir)
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / log_file

    # Create root logger for the agent namespace
    logger = logging.getLogger("pinterest_agent")
    logger.setLevel(level)

    # Prevent adding multiple handlers if setup_logger is called twice
    if logger.hasHandlers():
        logger.handlers.clear()

    # Standard formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s │ %(levelname)-8s │ %(name)-20s │ %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 1. Rotating File Handler
    file_handler = RotatingFileHandler(
        filename=file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # 2. Console (Stream) Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Log initial startup
    logger.info("Logger initialized  │  level=%s  file=%s", logging.getLevelName(level), file_path)

    return logger
