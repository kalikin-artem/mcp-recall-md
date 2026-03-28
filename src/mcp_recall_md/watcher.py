"""File watcher that auto-indexes markdown files into the vector store."""

from pathlib import Path

import pathspec
from watchdog.events import FileSystemEvent, FileSystemEventHandler

from mcp_recall_md.chroma_backend import VectorStore
from mcp_recall_md.log import log

IGNORE_FILE = ".recallignore"


def load_ignore_spec(vault_path: Path) -> pathspec.PathSpec | None:
    """Load .recallignore from vault root. Returns None if no file."""
    ignore_file = vault_path / IGNORE_FILE
    if not ignore_file.is_file():
        return None
    lines = ignore_file.read_text(encoding="utf-8").splitlines()
    return pathspec.PathSpec.from_lines("gitignore", lines)


def is_ignored(path: Path, vault_path: Path, spec: pathspec.PathSpec | None) -> bool:
    """Check if a path should be ignored based on .recallignore."""
    if spec is None:
        return False
    rel = path.relative_to(vault_path).as_posix()
    return spec.match_file(rel)


class MarkdownHandler(FileSystemEventHandler):
    """Handles created/modified .md files by indexing them into the vector store."""

    def __init__(self, backend: VectorStore, vault_path: Path, spec: pathspec.PathSpec | None = None):
        self._backend = backend
        self._vault_path = vault_path
        self._spec = spec

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
        if is_ignored(path, self._vault_path, self._spec):
            log.debug("ignored: %s", path.name)
            return
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as e:
            log.warning("skip %s: %s", path.name, e)
            return
        key = path.stem
        self._backend.index(key, content)
        log.info("indexed: %s", key)


def index_existing(vault_path: Path, backend: VectorStore, spec: pathspec.PathSpec | None = None) -> int:
    """Bulk-index all existing .md files. Returns count."""
    count = 0
    for md_file in vault_path.rglob("*.md"):
        if is_ignored(md_file, vault_path, spec):
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        backend.index(md_file.stem, content)
        count += 1
    return count


