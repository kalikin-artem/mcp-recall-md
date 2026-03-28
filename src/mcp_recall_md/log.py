"""Logging setup. File logging always on, stderr with --verbose."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path.home() / ".mcp-recall-md"
LOG_FILE = LOG_DIR / "server.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
FORMAT = "%(asctime)s  %(levelname)-8s  %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

log = logging.getLogger("mcp_recall_md")


def setup(verbose: bool = False) -> None:
    """Configure logging. Call once at startup."""
    log.setLevel(logging.DEBUG if verbose else logging.INFO)

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=MAX_BYTES, backupCount=BACKUP_COUNT, encoding="utf-8",
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(FORMAT, datefmt=DATE_FORMAT))
    log.addHandler(file_handler)

    if verbose and sys.stderr:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setLevel(logging.DEBUG)
        stderr_handler.setFormatter(logging.Formatter(FORMAT, datefmt=DATE_FORMAT))
        log.addHandler(stderr_handler)
