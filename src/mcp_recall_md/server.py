"""MCP server exposing semantic memory tools over stdio."""

import argparse
from pathlib import Path

from fastmcp import FastMCP

from mcp_recall_md.chroma_backend import VectorStore
from mcp_recall_md.config import DEFAULT_COLLECTION, resolve_db_path
from mcp_recall_md.log import log, setup

mcp = FastMCP("mcp-recall-md")
_backend: VectorStore | None = None
_cli_args: argparse.Namespace | None = None


def _get_backend() -> VectorStore:
    """Lazy-init the vector store on first tool call."""
    global _backend
    if _backend is None:
        db_path = resolve_db_path(getattr(_cli_args, "db_path", None))
        _backend = VectorStore(db_path=db_path, collection_name=DEFAULT_COLLECTION)
    return _backend


@mcp.tool()
def index(key: str, content: str) -> str:
    """Index a knowledge base article. Replaces any existing article with the same key."""
    _get_backend().index(key, content)
    return f"Indexed: {key}"


@mcp.tool()
def search(query: str, limit: int = 5) -> list[dict]:
    """Semantic search across the knowledge base.

    Returns up to `limit` articles ranked by relevance, each with key, content, and similarity score.
    """
    return _get_backend().search(query, limit)


@mcp.tool()
def remove(key: str) -> str:
    """Remove an article from the knowledge base by key."""
    removed = _get_backend().remove(key)
    return f"Removed: {key}" if removed else f"Not found: {key}"


def main():
    global _cli_args
    parser = argparse.ArgumentParser(description="mcp-recall-md MCP server")
    parser.add_argument("--db-path", help="Path to ChromaDB storage (default: .mcp-recall-md)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    _cli_args = parser.parse_args()
    setup(verbose=_cli_args.verbose)
    log.info("server starting")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
