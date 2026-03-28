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


def _make_key(path: Path, vault_path: Path) -> str:
    """Key = vault directory name + relative posix path, globally unique across vaults."""
    vault_name = vault_path.resolve().name
    rel = path.relative_to(vault_path).as_posix()
    return f"{vault_name}/{rel}"


def _make_metadata(path: Path, vault_path: Path) -> dict:
    """Metadata stored alongside the document."""
    return {
        "source": str(path.resolve()),
        "vault": str(vault_path.resolve()),
        "mtime": str(path.stat().st_mtime),
    }


class MarkdownHandler(FileSystemEventHandler):
    """Handles created/modified/deleted .md files."""

    def __init__(self, backend: VectorStore, vault_path: Path, spec: pathspec.PathSpec | None = None):
        self._backend = backend
        self._vault_path = vault_path
        self._spec = spec

    def on_created(self, event: FileSystemEvent) -> None:
        self._index(event)

    def on_modified(self, event: FileSystemEvent) -> None:
        self._index(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix.lower() != ".md":
            return
        key = _make_key(path, self._vault_path)
        if self._backend.remove(key):
            log.info("removed (file deleted): %s", key)

    def _index(self, event: FileSystemEvent) -> None:
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
        key = _make_key(path, self._vault_path)
        meta = _make_metadata(path, self._vault_path)
        self._backend.index(key, content, metadata=meta)
        log.info("indexed: %s", key)


def index_existing(vault_path: Path, backend: VectorStore, spec: pathspec.PathSpec | None = None) -> int:
    """Bulk-index .md files. Skips files that haven't changed since last index. Returns count indexed."""
    indexed = 0
    skipped = 0
    for md_file in vault_path.rglob("*.md"):
        if is_ignored(md_file, vault_path, spec):
            continue
        key = _make_key(md_file, vault_path)
        current_mtime = str(md_file.stat().st_mtime)
        existing = backend.get_metadata(key)
        if existing and existing.get("mtime") == current_mtime:
            skipped += 1
            continue
        try:
            content = md_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        meta = _make_metadata(md_file, vault_path)
        backend.index(key, content, metadata=meta)
        indexed += 1
    if skipped:
        log.info("skipped %d unchanged files", skipped)
    return indexed
