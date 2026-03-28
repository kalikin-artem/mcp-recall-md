"""End-to-end test: watcher indexes a file, then search retrieves it."""

import time
from pathlib import Path

import pytest
from watchdog.observers import Observer

from mcp_recall_md.chroma_backend import VectorStore
from mcp_recall_md.watcher import MarkdownHandler


@pytest.fixture()
def backend(tmp_path: Path) -> VectorStore:
    return VectorStore(db_path=tmp_path / "e2e_db", collection_name="e2e")


def test_file_drop_triggers_indexing_and_search(backend: VectorStore, tmp_path: Path):
    """Full cycle: drop a .md file -> watcher indexes it -> search finds it."""
    vault = tmp_path / "vault"
    vault.mkdir()

    handler = MarkdownHandler(backend)
    observer = Observer()
    observer.schedule(handler, str(vault), recursive=True)
    observer.start()

    try:
        article = vault / "kubernetes-networking.md"
        article.write_text(
            "Kubernetes uses a flat network model where every pod can reach every other pod. "
            "Services provide stable endpoints via ClusterIP, NodePort, or LoadBalancer types. "
            "Network policies control traffic flow between pods using label selectors.",
            encoding="utf-8",
        )

        time.sleep(3)

        results = backend.search("container networking and pod communication", limit=3)
        assert len(results) >= 1
        assert results[0]["key"] == "kubernetes-networking"
        assert "pod" in results[0]["content"].lower()

        # Modify the file and verify re-indexing
        article.write_text(
            "Kubernetes networking relies on CNI plugins like Calico, Cilium, or Flannel. "
            "Each plugin implements the Container Network Interface specification.",
            encoding="utf-8",
        )

        time.sleep(3)

        results = backend.search("CNI plugins", limit=1)
        assert results[0]["key"] == "kubernetes-networking"
        assert "CNI" in results[0]["content"]

    finally:
        observer.stop()
        observer.join()


def test_bulk_index_then_search(backend: VectorStore, tmp_path: Path):
    """Bulk-index existing files, then verify semantic search works across them."""
    from mcp_recall_md.watcher import index_existing

    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "python-asyncio.md").write_text(
        "asyncio is Python's built-in library for writing concurrent code using async/await syntax.",
        encoding="utf-8",
    )
    (vault / "rust-ownership.md").write_text(
        "Rust's ownership system ensures memory safety without a garbage collector through borrowing and lifetimes.",
        encoding="utf-8",
    )
    (vault / "sql-joins.md").write_text(
        "SQL JOIN operations combine rows from two or more tables based on a related column. "
        "Types include INNER JOIN, LEFT JOIN, RIGHT JOIN, and FULL OUTER JOIN.",
        encoding="utf-8",
    )

    count = index_existing(vault, backend)
    assert count == 3

    results = backend.search("concurrent programming in Python", limit=3)
    assert results[0]["key"] == "python-asyncio"

    results = backend.search("memory management without GC", limit=3)
    assert results[0]["key"] == "rust-ownership"

    results = backend.search("combining database tables", limit=3)
    assert results[0]["key"] == "sql-joins"
