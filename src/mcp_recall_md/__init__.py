"""mcp-recall-md — local semantic search for markdown notes."""

try:
    from importlib.metadata import version
    __version__ = version("mcp-recall-md")
except Exception:
    __version__ = "0.0.0-dev"
