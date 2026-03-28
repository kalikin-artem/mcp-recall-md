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
    assert 0 < results[0]["similarity"] <= 1


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


def test_get_metadata(backend: VectorStore):
    backend.index("doc", "some content", metadata={"source": "/path/to/doc.md", "vault": "/notes"})
    meta = backend.get_metadata("doc")
    assert meta is not None
    assert meta["source"] == "/path/to/doc.md"
    assert meta["vault"] == "/notes"


def test_get_metadata_nonexistent(backend: VectorStore):
    assert backend.get_metadata("ghost") is None


def test_get_metadata_without_metadata(backend: VectorStore):
    backend.index("plain", "no metadata here")
    meta = backend.get_metadata("plain")
    assert meta is not None  # returns empty dict, not None


def test_similarity_filtering(backend: VectorStore):
    """Irrelevant queries should return fewer or no results due to MIN_SIMILARITY threshold."""
    backend.index("python", "Python is a programming language used for web development and data science.")
    backend.index("cooking", "How to make a perfect risotto with parmesan and mushrooms.")

    results = backend.search("Italian food recipes", limit=5)
    # Should find cooking, might filter out python
    for r in results:
        assert r["similarity"] >= 0.15


def test_search_returns_source_and_vault(backend: VectorStore):
    backend.index("doc", "content about testing", metadata={"source": "/a/b.md", "vault": "/a"})
    results = backend.search("testing", limit=1)
    assert len(results) >= 1
    assert results[0]["source"] == "/a/b.md"
    assert results[0]["vault"] == "/a"
