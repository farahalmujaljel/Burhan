"""Qdrant implementation of the vector store.

One class covers all three modes:
  - server:   QdrantStore(url="http://localhost:6333")   (Docker)
  - local:    QdrantStore(path="data/qdrant_local")      (embedded, on disk; demo default)
  - memory:   QdrantStore(location=":memory:")          (tests)
"""

import uuid

from qdrant_client import QdrantClient, models

from app.core.errors import ProviderError
from app.knowledge.vector_store.base import (
    RecordKind,
    VectorHit,
    VectorPayload,
    VectorRecord,
    VectorStore,
)

# Qdrant point IDs must be UUIDs or ints; derive stable UUIDs from our source IDs.
_NAMESPACE = uuid.UUID("6f1c3b1e-4d0a-4b8e-9d2c-2a7b5e9f0c11")


def point_id(source_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, source_id))


def _filter(paper_id: str | None, kind: str | None) -> models.Filter | None:
    must = [
        models.FieldCondition(key=key, match=models.MatchValue(value=value))
        for key, value in (("paper_id", paper_id), ("kind", kind))
        if value is not None
    ]
    return models.Filter(must=must) if must else None


class QdrantStore(VectorStore):
    def __init__(
        self,
        collection: str,
        *,
        url: str | None = None,
        api_key: str | None = None,
        path: str | None = None,
        location: str | None = None,
    ) -> None:
        self.collection = collection
        if url:
            self.backend = "qdrant"
            self._client = QdrantClient(url=url, api_key=api_key)
        elif path:
            self.backend = "qdrant-local"
            self._client = QdrantClient(path=path)
        else:
            self.backend = "qdrant-memory"
            self._client = QdrantClient(location=location or ":memory:")
        self._dim: int | None = None

    def ensure_collection(self, dim: int) -> None:
        if self._dim == dim:
            return
        try:
            if self._client.collection_exists(self.collection):
                existing = self._client.get_collection(self.collection).config.params.vectors.size
                if existing != dim:
                    raise ProviderError(
                        f"Qdrant collection '{self.collection}' has dimension {existing} but the "
                        f"embedding model produces {dim}. Use a new QDRANT_COLLECTION or delete "
                        "the old collection and re-index."
                    )
            else:
                self._client.create_collection(
                    self.collection,
                    vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
                )
                if self.backend == "qdrant":  # payload indexes are a server feature
                    for field in ("paper_id", "kind"):
                        self._client.create_payload_index(
                            self.collection, field, models.PayloadSchemaType.KEYWORD
                        )
        except ProviderError:
            raise
        except Exception as exc:
            raise ProviderError(f"Qdrant is unavailable: {exc}") from exc
        self._dim = dim

    def _exists(self) -> bool:
        return self._client.collection_exists(self.collection)

    def upsert(self, records: list[VectorRecord]) -> None:
        if not records:
            return
        self.ensure_collection(len(records[0].vector))
        self._client.upsert(
            self.collection,
            points=[
                models.PointStruct(
                    id=point_id(r.id), vector=r.vector, payload=r.payload.model_dump(mode="json")
                )
                for r in records
            ],
        )

    def delete_paper(self, paper_id: str) -> None:
        if not self._exists():
            return
        self._client.delete(
            self.collection,
            points_selector=models.FilterSelector(filter=_filter(paper_id, None)),
        )

    def search(self, vector, *, limit=10, paper_id=None, kind=None):
        if not self._exists():
            return []
        result = self._client.query_points(
            self.collection,
            query=vector,
            query_filter=_filter(paper_id, kind),
            limit=limit,
            with_payload=True,
        )
        return [
            VectorHit(score=p.score, payload=VectorPayload.model_validate(p.payload))
            for p in result.points
        ]

    def count(self, *, paper_id: str | None = None, kind: RecordKind | None = None) -> int:
        if not self._exists():
            return 0
        return self._client.count(self.collection, count_filter=_filter(paper_id, kind)).count

    def close(self) -> None:
        self._client.close()
