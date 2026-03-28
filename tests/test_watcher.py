"""Tests for file watcher event handling."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from watchdog.events import FileCreatedEvent, FileModifiedEvent

from mcp_recall_md.watcher import MarkdownHandler, index_existing


@pytest.fixture()
def mock_backend():
    return MagicMock()


def test_handler_indexes_md_file(mock_backend, tmp_path: Path):
    md_file = tmp_path / "test-note.md"
    md_file.write_text("# Test\nSome content about testing.", encoding="utf-8")

    handler = MarkdownHandler(mock_backend)
    event = FileCreatedEvent(str(md_file))
    handler.on_created(event)

    mock_backend.index.assert_called_once_with("test-note", "# Test\nSome content about testing.")


def test_handler_ignores_non_md(mock_backend, tmp_path: Path):
    txt_file = tmp_path / "notes.txt"
    txt_file.write_text("plain text", encoding="utf-8")

    handler = MarkdownHandler(mock_backend)
    event = FileCreatedEvent(str(txt_file))
    handler.on_created(event)

    mock_backend.index.assert_not_called()


def test_handler_on_modified(mock_backend, tmp_path: Path):
    md_file = tmp_path / "updated.md"
    md_file.write_text("updated content", encoding="utf-8")

    handler = MarkdownHandler(mock_backend)
    event = FileModifiedEvent(str(md_file))
    handler.on_modified(event)

    mock_backend.index.assert_called_once_with("updated", "updated content")


def test_index_existing(mock_backend, tmp_path: Path):
    (tmp_path / "a.md").write_text("alpha", encoding="utf-8")
    (tmp_path / "b.md").write_text("beta", encoding="utf-8")
    (tmp_path / "sub").mkdir()
    (tmp_path / "sub" / "c.md").write_text("gamma", encoding="utf-8")
    (tmp_path / "skip.txt").write_text("ignored", encoding="utf-8")

    count = index_existing(tmp_path, mock_backend)
    assert count == 3
    assert mock_backend.index.call_count == 3
