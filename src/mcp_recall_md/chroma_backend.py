"""ChromaDB vector store backend for mcp-recall-md."""

import logging
from pathlib import Path

import chromadb

log = logging.getLogger("mcp_recall_md")

DEFAULT_DB_PATH = Path.home() / ".mcp-recall-md" / "db"
DEFAULT_COLLECTION = "kb_articles"
MIN_SIMILARITY = 0.15


def resolve_db_path(db_path: str | None = None) -> Path:
    """Resolve the database path, defaulting to ~/.mcp-recall-md/db."""
    if db_path:
        path = Path(db_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        return path
    return DEFAULT_DB_PATH


class VectorStore:
    """Wraps a ChromaDB collection for storing and querying document embeddings."""

    def __init__(self, db_path: str | Path, collection_name: str = DEFAULT_COLLECTION):
        db_path = Path(db_path).resolve()
        db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        log.info("vector store ready  db=%s  collection=%s", db_path, collection_name)

    def index(self, key: str, content: str, metadata: dict | None = None) -> None:
        """Index a document, replacing any existing one with the same key."""
        kwargs: dict = {"ids": [key], "documents": [content]}
        if metadata:
            kwargs["metadatas"] = [metadata]
        self._collection.upsert(**kwargs)
        log.debug("indexed  key=%s  chars=%d", key, len(content))

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Semantic similarity search. Returns list of {key, content, similarity, source}."""
        count = self._collection.count()
        if count == 0:
            log.debug("search skipped — collection is empty")
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(limit, count),
            include=["documents", "distances", "metadatas"],
        )
        items = []
        for i, doc_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i] if results.get("distances") else 0
            similarity = round(1 - distance, 3)
            if similarity < MIN_SIMILARITY:
                continue
            meta = (results["metadatas"][0][i] or {}) if results.get("metadatas") else {}
            item = {
                "key": doc_id,
                "content": results["documents"][0][i],
                "similarity": similarity,
            }
            if meta.get("source"):
                item["source"] = meta["source"]
            if meta.get("vault"):
                item["vault"] = meta["vault"]
            items.append(item)
        log.info("search  query=%r  results=%d/%d", query[:80], len(items), count)
        return items

    def remove(self, key: str) -> bool:
        """Remove a document by key. Returns True if it existed."""
        existing = self._collection.get(ids=[key])
        if not existing["ids"]:
            return False
        self._collection.delete(ids=[key])
        log.info("removed  key=%s", key)
        return True

    def get_metadata(self, key: str) -> dict | None:
        """Get metadata for a document by key. Returns None if not found."""
        result = self._collection.get(ids=[key], include=["metadatas"])
        if not result["ids"]:
            return None
        return result["metadatas"][0] or {}

    def count(self) -> int:
        """Return the number of indexed documents."""
        return self._collection.count()
