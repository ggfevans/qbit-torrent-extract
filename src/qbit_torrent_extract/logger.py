"""Simple logging setup for qbit-torrent-extract."""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


def setup_logging(
    level: str = "INFO",
    log_dir: Optional[str] = None,
    log_file: str = "qbit-torrent-extract.log",
) -> logging.Logger:
    """Set up logging with optional file output.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Optional directory for log files
        log_file: Name of the log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("qbit_torrent_extract")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Clear existing handlers
    logger.handlers.clear()

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    ))
    logger.addHandler(console)

    # File handler (optional)
    if log_dir:
        log_path = Path(log_dir).expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            log_path / log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=3,
        )
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        ))
        logger.addHandler(file_handler)

    return logger


def get_logger() -> logging.Logger:
    """Get the logger instance."""
    return logging.getLogger("qbit_torrent_extract")
