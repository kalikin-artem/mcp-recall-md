"""Configuration for mcp-recall-md. All config comes from CLI args."""

from pathlib import Path

DEFAULT_DB_PATH = ".mcp-recall-md"
DEFAULT_COLLECTION = "kb_articles"


def resolve_db_path(db_path: str | None = None) -> Path:
    """Resolve the database path, defaulting to .mcp-recall-md in cwd."""
    path = Path(db_path) if db_path else Path(DEFAULT_DB_PATH)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path
