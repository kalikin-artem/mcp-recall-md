"""Integration tests for the ChromaDB vector store backend."""

from pathlib import Path

import pytest

from mcp_recall_md.chroma_backend import VectorStore


@pytest.fixture()
def backend(tmp_path: Path) -> VectorStore:
    return VectorStore(db_path=tmp_path / "test_db", collection_name="test")


def test_index_and_search(backend: VectorStore):
    backend.index("aws-bedrock", "AWS Bedrock is a managed service for foundation models.")
    backend.index("docker-basics", "Docker containers package applications with their dependencies.")

    results = backend.search("cloud AI models", limit=2)
    assert len(results) >= 1
    assert results[0]["key"] == "aws-bedrock"
    assert "Bedrock" in results[0]["content"]
    assert results[0]["score"] is not None


def test_search_empty(backend: VectorStore):
    results = backend.search("anything")
    assert results == []


def test_remove(backend: VectorStore):
    backend.index("temp-note", "This is temporary content.")
    assert backend.remove("temp-note") is True
    results = backend.search("temporary content", limit=1)
    assert all(r["key"] != "temp-note" for r in results)


def test_remove_nonexistent(backend: VectorStore):
    assert backend.remove("does-not-exist") is False


def test_index_overwrites(backend: VectorStore):
    backend.index("note", "original content about cats")
    backend.index("note", "updated content about quantum computing")
    results = backend.search("quantum", limit=1)
    assert results[0]["key"] == "note"
    assert "quantum" in results[0]["content"]
