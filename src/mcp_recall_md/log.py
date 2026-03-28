"""Logging setup. Disabled by default, enable with --verbose."""

import logging
import sys

log = logging.getLogger("mcp_recall_md")


def setup(verbose: bool = False) -> None:
    """Configure logging. Call once at startup."""
    if not verbose:
        return
    handlers: list[logging.Handler] = []
    if sys.stdout:
        handlers.append(logging.StreamHandler(sys.stdout))
    if handlers:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s  %(levelname)-8s  %(message)s",
            datefmt="%H:%M:%S",
            handlers=handlers,
        )
