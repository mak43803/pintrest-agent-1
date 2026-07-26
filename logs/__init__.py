"""
Logs Module — Unified logging, exception handling, and metrics.
================================================================

Provides both file-based rotating logs and SQLite-persisted logs.
Also includes decorators for performance tracking and a global exception
hook to catch fatal application crashes.

Quick Start::

    from database import Database
    from logs import setup_logger, LogManager, setup_global_exception_handler
    
    # Setup root logger (writes to console + file)
    setup_logger()
    
    # Setup SQLite logger
    db = Database(...)
    log_manager = LogManager(db)
    
    # Catch global crashes
    setup_global_exception_handler(log_manager)

Public API:
    - setup_logger                   — File & Stream logging init
    - LogManager                     — SQLite logs, filtering, export
    - LogRecord                      — Data class for DB logs
    - setup_global_exception_handler — sys.excepthook override
    - log_execution                  — Decorator for perf & errors
"""

from logs.logger import setup_logger
from logs.log_manager import LogManager, LogRecord
from logs.error_handler import setup_global_exception_handler, log_execution

__all__ = [
    "setup_logger",
    "LogManager",
    "LogRecord",
    "setup_global_exception_handler",
    "log_execution",
]
