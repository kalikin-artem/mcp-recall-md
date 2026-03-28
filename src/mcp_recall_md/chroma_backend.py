"""ChromaDB vector store backend for mcp-recall-md."""

import logging
from pathlib import Path

import chromadb

log = logging.getLogger("mcp_recall_md")


class VectorStore:
    """Wraps a ChromaDB collection for storing and querying document embeddings."""

    def __init__(self, db_path: str | Path, collection_name: str = "kb_articles"):
        db_path = Path(db_path).resolve()
        db_path.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(db_path))
        self._collection = self._client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        log.info("vector store ready  db=%s  collection=%s", db_path, collection_name)

    def index(self, key: str, content: str) -> None:
        """Index a document, replacing any existing one with the same key."""
        self._collection.upsert(ids=[key], documents=[content])
        log.debug("indexed  key=%s  chars=%d", key, len(content))

    def search(self, query: str, limit: int = 5) -> list[dict]:
        """Semantic similarity search. Returns list of {key, content, score}."""
        count = self._collection.count()
        if count == 0:
            log.debug("search skipped — collection is empty")
            return []
        results = self._collection.query(
            query_texts=[query],
            n_results=min(limit, count),
        )
        items = []
        for i, doc_id in enumerate(results["ids"][0]):
            items.append({
                "key": doc_id,
                "content": results["documents"][0][i],
                "score": results["distances"][0][i] if results.get("distances") else None,
            })
        log.info("search  query=%r  results=%d", query[:80], len(items))
        return items

    def remove(self, key: str) -> bool:
        """Remove a document by key. Returns True if it existed."""
        existing = self._collection.get(ids=[key])
        if not existing["ids"]:
            log.debug("remove  key=%s  not found", key)
            return False
        self._collection.delete(ids=[key])
        log.info("removed  key=%s", key)
        return True

    def count(self) -> int:
        """Return the number of indexed documents."""
        return self._collection.count()
