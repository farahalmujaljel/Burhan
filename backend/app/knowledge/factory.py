"""Build the configured graph and vector stores (backends are chosen explicitly via settings)."""

from app.core.config import Settings
from app.knowledge.graph_store.base import GraphStore
from app.knowledge.graph_store.memory_store import MemoryGraphStore
from app.knowledge.vector_store.base import VectorStore


def create_graph_store(settings: Settings) -> GraphStore:
    if settings.graph_backend == "neo4j":
        from app.knowledge.graph_store.neo4j_store import Neo4jGraphStore

        return Neo4jGraphStore(
            settings.neo4j_uri,
            settings.neo4j_user,
            settings.neo4j_password.get_secret_value(),
            database=settings.neo4j_database,
        )
    return MemoryGraphStore(settings.twin_dir / "graph.json")


def create_vector_store(settings: Settings) -> VectorStore:
    from app.knowledge.vector_store.qdrant_store import QdrantStore

    if settings.vector_backend == "qdrant":
        key = settings.qdrant_api_key.get_secret_value() if settings.qdrant_api_key else None
        return QdrantStore(settings.qdrant_collection, url=settings.qdrant_url, api_key=key)
    settings.qdrant_local_path.mkdir(parents=True, exist_ok=True)
    return QdrantStore(settings.qdrant_collection, path=str(settings.qdrant_local_path))
