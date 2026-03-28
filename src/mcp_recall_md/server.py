"""MCP server exposing semantic memory tools over stdio."""

import argparse
from pathlib import Path

from fastmcp import FastMCP
from watchdog.observers import Observer

from mcp_recall_md.chroma_backend import VectorStore, resolve_db_path
from mcp_recall_md.log import log, setup
from mcp_recall_md.watcher import MarkdownHandler, index_existing, load_ignore_spec

mcp = FastMCP("mcp-recall-md")
_backend: VectorStore | None = None


def _get_backend() -> VectorStore:
    global _backend
    if _backend is None:
        raise RuntimeError("Backend not initialized — call main() first")
    return _backend


@mcp.tool()
def index(key: str, content: str) -> str:
    """Index a knowledge base article. Replaces any existing article with the same key."""
    _get_backend().index(key, content)
    return f"Indexed: {key}"


@mcp.tool()
def search(query: str, limit: int = 5) -> list[dict]:
    """Semantic search across the knowledge base.

    Returns up to `limit` articles ranked by similarity, each with key, content,
    similarity (0-1, higher is better), and source file path.
    Low-relevance results are automatically filtered out.
    """
    return _get_backend().search(query, limit)


@mcp.tool()
def remove(key: str) -> str:
    """Remove an article from the knowledge base by key."""
    removed = _get_backend().remove(key)
    return f"Removed: {key}" if removed else f"Not found: {key}"


def _start_watchers(vaults: list[str], backend: VectorStore) -> Observer:
    """Index existing files and start watching all vaults. Returns the observer."""
    observer = Observer()
    for vault_str in vaults:
        vault_path = Path(vault_str)
        if not vault_path.is_dir():
            log.warning("vault not found, skipping: %s", vault_path)
            continue
        spec = load_ignore_spec(vault_path)
        if spec:
            log.info("loaded .recallignore from %s", vault_path)
        count = index_existing(vault_path, backend, spec)
        log.info("indexed %d files from %s", count, vault_path)
        handler = MarkdownHandler(backend, vault_path, spec)
        observer.schedule(handler, str(vault_path), recursive=True)
    observer.start()
    return observer


def main():
    global _backend
    parser = argparse.ArgumentParser(description="mcp-recall-md MCP server")
    parser.add_argument("--vaults", nargs="+", help="Paths to markdown note folders to index and watch")
    parser.add_argument("--db-path", help="Path to ChromaDB storage (default: ~/.mcp-recall-md/db)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()
    setup(verbose=args.verbose)

    _backend = VectorStore(db_path=resolve_db_path(args.db_path))

    observer = None
    if args.vaults:
        observer = _start_watchers(args.vaults, _backend)
        log.info("watching %d vault(s)", len(args.vaults))

    log.info("server starting")
    try:
        mcp.run(transport="stdio")
    finally:
        if observer:
            observer.stop()
            observer.join()


if __name__ == "__main__":
    main()
