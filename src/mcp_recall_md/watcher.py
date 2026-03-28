"""File watcher that auto-indexes markdown files into the vector store."""

import argparse
import sys
import time
from pathlib import Path

from watchdog.events import FileSystemEvent, FileSystemEventHandler
from watchdog.observers import Observer

from mcp_recall_md.chroma_backend import VectorStore
from mcp_recall_md.config import DEFAULT_COLLECTION, resolve_db_path
from mcp_recall_md.log import log, setup


class MarkdownHandler(FileSystemEventHandler):
    """Handles created/modified .md files by indexing them into the vector store."""

    def __init__(self, backend: VectorStore):
        self._backend = backend

    def on_created(self, event: FileSystemEvent) -> None:
        self._process(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._process(event)

    def _process(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".md":
            return
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            log.warning("skip %s: %s", path.name, e)
            return
        key = path.stem
        self._backend.index(key, content)
        log.info("indexed: %s", key)


def index_existing(vault_path: Path, backend: VectorStore) -> int:
    """Bulk-index all existing .md files. Returns count."""
    count = 0
    for md_file in vault_path.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        backend.index(md_file.stem, content)
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description="mcp-recall-md file watcher")
    parser.add_argument("--vault", required=True, help="Path to markdown notes folder")
    parser.add_argument("--db-path", help="Path to ChromaDB storage (default: .mcp-recall-md)")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    args = parser.parse_args()

    setup(verbose=args.verbose)

    vault_path = Path(args.vault)
    if not vault_path.is_dir():
        print(f"Error: folder not found: {vault_path}")
        sys.exit(1)

    db_path = resolve_db_path(args.db_path)
    backend = VectorStore(db_path=db_path, collection_name=DEFAULT_COLLECTION)

    count = index_existing(vault_path, backend)
    print(f"Indexed {count} files from {vault_path}")

    handler = MarkdownHandler(backend)
    observer = Observer()
    observer.schedule(handler, str(vault_path), recursive=True)
    observer.start()
    print(f"Watching {vault_path} for changes... (Ctrl+C to stop)")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
