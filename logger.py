"""
logger.py
=========
Shared logging configuration for the Spotify Music Evolution pipeline.

Every pipeline script calls get_logger(__name__) to receive a logger
that writes to both the console and a rotating log file.

Usage:
    from logger import get_logger
    log = get_logger(__name__)
    log.info("Pipeline started")
    log.warning("Missing column — skipping")
    log.error("Database not found")
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ─── ANSI colour codes for console output ────────────────────────────────────
_COLOURS = {
    "DEBUG":    "\033[36m",   # Cyan
    "INFO":     "\033[32m",   # Green
    "WARNING":  "\033[33m",   # Yellow
    "ERROR":    "\033[31m",   # Red
    "CRITICAL": "\033[35m",   # Magenta
}
_RESET = "\033[0m"


class _ColourFormatter(logging.Formatter):
    """Applies ANSI colour to the levelname in console output."""

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelname, "")
        record.levelname = f"{colour}{record.levelname:<8}{_RESET}"
        return super().format(record)


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Return a named logger with console + rotating-file handlers.

    Parameters
    ----------
    name  : typically __name__ of the calling module
    level : logging level (default INFO)

    Returns
    -------
    logging.Logger
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers on repeated calls
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # ── Console handler (coloured) ────────────────────────────────────────────
    console_fmt = _ColourFormatter(
        fmt="%(levelname)s %(name)s — %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # ── File handler (rotating, plain text) ───────────────────────────────────
    try:
        # Lazy import to avoid circular dependency if config imports logger
        from config import PATHS
        log_dir = PATHS["logs"]
    except ImportError:
        log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", "logs")

    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "pipeline.log")

    file_fmt = logging.Formatter(
        fmt="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=5 * 1024 * 1024,   # 5 MB per file
        backupCount=3,               # Keep last 3 rotated logs
        encoding="utf-8",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    return logger
