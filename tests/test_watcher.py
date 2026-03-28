"""Tests for file watcher event handling."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from watchdog.events import FileCreatedEvent, FileDeletedEvent, FileModifiedEvent

from mcp_recall_md.watcher import MarkdownHandler, index_existing, load_ignore_spec


@pytest.fixture()
def mock_backend():
    return MagicMock()


def _vault_key(tmp_path: Path, rel: str) -> str:
    """Expected key format: vault_dir_name/relative_path."""
    return f"{tmp_path.resolve().name}/{rel}"


def test_handler_indexes_md_file(mock_backend, tmp_path: Path):
    md_file = tmp_path / "test-note.md"
    md_file.write_text("# Test\nSome content about testing.", encoding="utf-8")

    handler = MarkdownHandler(mock_backend, tmp_path)
    event = FileCreatedEvent(str(md_file))
    handler.on_created(event)

    mock_backend.index.assert_called_once()
    args, kwargs = mock_backend.index.call_args
    assert args[0] == _vault_key(tmp_path, "test-note.md")
    assert args[1] == "# Test\nSome content about testing."
    assert kwargs["metadata"]["source"] == str(md_file.resolve())


def test_handler_ignores_non_md(mock_backend, tmp_path: Path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("plain text", encoding="utf-8")

    handler = MarkdownHandler(mock_backend, tmp_path)
    event = FileCreatedEvent(str(txt_file))
    handler.on_created(event)

    mock_backend.index.assert_not_called()


def test_handler_on_modified(mock_backend, tmp_path: Path):
    md_file = tmp_path / "updated.md"
    md_file.write_text("updated content", encoding="utf-8")

    handler = MarkdownHandler(mock_backend, tmp_path)
    event = FileModifiedEvent(str(md_file))
    handler.on_modified(event)

    mock_backend.index.assert_called_once()
    assert mock_backend.index.call_args[0][0] == _vault_key(tmp_path, "updated.md")


def test_handler_on_deleted(mock_backend, tmp_path: Path):
    md_file = tmp_path / "removed.md"

    handler = MarkdownHandler(mock_backend, tmp_path)
    event = FileDeletedEvent(str(md_file))
    handler.on_deleted(event)

    mock_backend.remove.assert_called_once_with(_vault_key(tmp_path, "removed.md"))


def test_key_uses_relative_path_with_vault_prefix(mock_backend, tmp_path: Path):
    sub = tmp_path / "sub"
    sub.mkdir()
    md_file = sub / "deep.md"
    md_file.write_text("nested", encoding="utf-8")

    handler = MarkdownHandler(mock_backend, tmp_path)
    event = FileCreatedEvent(str(md_file))
    handler.on_created(event)

    assert mock_backend.index.call_args[0][0] == _vault_key(tmp_path, "sub/deep.md")


def test_index_existing(mock_backend, tmp_path: Path):
    (tmp_path / "a.md").write_text("alpha", encoding="utf-8")
    (tmp_path / "b.md").write_text("beta", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("gamma", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("ignored", encoding="utf-8")

    count = index_existing(tmp_path, mock_backend)
    assert count == 3
    assert mock_backend.index.call_count == 3

    keys = [c[0][0] for c in mock_backend.index.call_args_list]
    assert _vault_key(tmp_path, "sub/c.md") in keys


def test_metadata_includes_source_and_vault(mock_backend, tmp_path: Path):
    md_file = tmp_path / "note.md"
    md_file.write_text("content", encoding="utf-8")

    count = index_existing(tmp_path, mock_backend)
    assert count == 1
    meta = mock_backend.index.call_args[1]["metadata"]
    assert meta["source"] == str(md_file.resolve())
    assert meta["vault"] == str(tmp_path.resolve())
    assert "mtime" in meta


def test_recallignore_excludes_folders(mock_backend, tmp_path: Path):
    (tmp_path / ".recallignore").write_text("drafts/\n", encoding="utf-8")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "good.md").write_text("keep", encoding="utf-8")
    (tmp_path / "drafts").mkdir()
    (tmp_path / "drafts" / "wip.md").write_text("skip", encoding="utf-8")

    spec = load_ignore_spec(tmp_path)
    count = index_existing(tmp_path, mock_backend, spec)
    assert count == 1
    assert mock_backend.index.call_args[0][0] == _vault_key(tmp_path, "notes/good.md")


def test_recallignore_handler_skips_ignored(mock_backend, tmp_path: Path):
    (tmp_path / ".recallignore").write_text(".obsidian/\n", encoding="utf-8")
    (tmp_path / ".obsidian").mkdir()
    md_file = tmp_path / ".obsidian" / "plugin-readme.md"
    md_file.write_text("internal", encoding="utf-8")

    spec = load_ignore_spec(tmp_path)
    handler = MarkdownHandler(mock_backend, tmp_path, spec)
    event = FileCreatedEvent(str(md_file))
    handler.on_created(event)

    mock_backend.index.assert_not_called()


def test_no_recallignore_indexes_everything(mock_backend, tmp_path: Path):
    (tmp_path / "a.md").write_text("alpha", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "b.md").write_text("beta", encoding="utf-8")

    spec = load_ignore_spec(tmp_path)
    assert spec is None
    count = index_existing(tmp_path, mock_backend, spec)
    assert count == 2


def test_multiple_vaults(mock_backend, tmp_path: Path):
    vault_a = tmp_path / "work"
    vault_b = tmp_path / "personal"
    vault_a.mkdir()
    vault_b.mkdir()
    (vault_a / "meeting.md").write_text("standup notes", encoding="utf-8")
    (vault_b / "journal.md").write_text("dear diary", encoding="utf-8")

    total = 0
    for vault in [vault_a, vault_b]:
        spec = load_ignore_spec(vault)
        total += index_existing(vault, mock_backend, spec)

    assert total == 2
    assert mock_backend.index.call_count == 2


def test_multiple_vaults_independent_recallignore(mock_backend, tmp_path: Path):
    vault_a = tmp_path / "work"
    vault_b = tmp_path / "personal"
    vault_a.mkdir()
    vault_b.mkdir()

    (vault_a / ".recallignore").write_text("drafts/\n", encoding="utf-8")
    (vault_a / "doc.md").write_text("work doc", encoding="utf-8")
    (vault_a / "drafts").mkdir()
    (vault_a / "drafts" / "wip.md").write_text("skip this", encoding="utf-8")

    (vault_b / "note.md").write_text("personal note", encoding="utf-8")
    (vault_b / "drafts").mkdir()
    (vault_b / "drafts" / "idea.md").write_text("keep this", encoding="utf-8")

    total = 0
    for vault in [vault_a, vault_b]:
        spec = load_ignore_spec(vault)
        total += index_existing(vault, mock_backend, spec)

    assert total == 3
    assert mock_backend.index.call_count == 3


def test_multiple_vaults_no_key_collision(mock_backend, tmp_path: Path):
    """Two vaults with same filename get different keys due to vault prefix."""
    vault_a = tmp_path / "work"
    vault_b = tmp_path / "personal"
    vault_a.mkdir()
    vault_b.mkdir()
    (vault_a / "setup.md").write_text("work setup", encoding="utf-8")
    (vault_b / "setup.md").write_text("personal setup", encoding="utf-8")

    for vault in [vault_a, vault_b]:
        index_existing(vault, mock_backend)

    assert mock_backend.index.call_count == 2
    keys = [c[0][0] for c in mock_backend.index.call_args_list]
    assert keys[0] != keys[1]
    assert "work/setup.md" in keys[0]
    assert "personal/setup.md" in keys[1]
