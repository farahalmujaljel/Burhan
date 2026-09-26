"""Store factories for tests: everything in memory, no Docker, no downloads."""

from app.knowledge.vector_store.qdrant_store import QdrantStore


def memory_qdrant() -> QdrantStore:
    return QdrantStore("test_evidence", location=":memory:")
