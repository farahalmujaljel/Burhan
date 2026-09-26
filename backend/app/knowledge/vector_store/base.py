"""Vector-store interface for the evidence index (RAG support subsystem)."""

from abc import ABC, abstractmethod
from typing import Literal

from pydantic import Field

from app.schemas.common import BurhanModel

RecordKind = Literal["chunk", "evidence"]


class VectorPayload(BurhanModel):
    """Metadata stored with every vector, so a hit always traces back to its source."""

    kind: RecordKind
    paper_id: str
    text: str
    chunk_id: str | None = None
    page: int | None = None
    page_end: int | None = None
    section: str | None = None
    char_start: int | None = None
    char_end: int | None = None
    # evidence records only
    evidence_id: str | None = None
    entity_id: str | None = None
    entity_type: str | None = None
    claim: str | None = None
    verification_status: str | None = None
    confidence: float | None = None


class VectorRecord(BurhanModel):
    id: str = Field(description="Stable source ID (chunk or evidence ID); drives idempotency")
    vector: list[float]
    payload: VectorPayload


class VectorHit(BurhanModel):
    score: float
    payload: VectorPayload


class VectorStore(ABC):
    backend: str

    @abstractmethod
    def ensure_collection(self, dim: int) -> None: ...

    @abstractmethod
    def upsert(self, records: list[VectorRecord]) -> None: ...

    @abstractmethod
    def delete_paper(self, paper_id: str) -> None: ...

    @abstractmethod
    def search(
        self,
        vector: list[float],
        *,
        limit: int = 10,
        paper_id: str | None = None,
        kind: RecordKind | None = None,
    ) -> list[VectorHit]: ...

    @abstractmethod
    def count(self, *, paper_id: str | None = None, kind: RecordKind | None = None) -> int: ...

    def close(self) -> None:  # noqa: B027 - optional hook
        pass
