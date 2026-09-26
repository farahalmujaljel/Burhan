"""Evidence index: embeds chunks and evidence locally and stores them in the vector store.

Two record kinds per paper:
  chunk     every parsed chunk (for later grounded retrieval)
  evidence  every evidence quote, embedded together with the claim it supports

Re-indexing a paper deletes its previous vectors first, and point IDs derive from chunk/evidence
IDs, so indexing is idempotent.
"""

import threading
from collections.abc import Callable

from app.embeddings.base import Embedder
from app.knowledge.vector_store.base import (
    RecordKind,
    VectorHit,
    VectorPayload,
    VectorRecord,
    VectorStore,
)
from app.schemas.documents import ParsedDocument
from app.schemas.evidence import Evidence
from app.twin.builder import EvidenceLink

BATCH_SIZE = 64


class EvidenceIndex:
    def __init__(self, store_factory: Callable[[], VectorStore], embedder: Embedder) -> None:
        # The store is created lazily: embedded Qdrant locks its folder when opened.
        self._store_factory = store_factory
        self._store: VectorStore | None = None
        self._lock = threading.Lock()
        self.embedder = embedder

    @property
    def store(self) -> VectorStore:
        with self._lock:
            if self._store is None:
                self._store = self._store_factory()
            return self._store

    def index_paper(
        self, doc: ParsedDocument, evidence: list[Evidence], links: dict[str, EvidenceLink]
    ) -> tuple[int, int]:
        """(Re)index a paper. Returns (chunks_indexed, evidence_indexed)."""
        payloads: list[tuple[str, str, VectorPayload]] = []  # (id, text_to_embed, payload)
        for c in doc.chunks:
            payloads.append(
                (
                    c.id,
                    c.text,
                    VectorPayload(
                        kind="chunk",
                        paper_id=doc.paper_id,
                        text=c.text,
                        chunk_id=c.id,
                        page=c.page,
                        page_end=c.page_end,
                        section=c.section_title,
                        char_start=c.char_start,
                        char_end=c.char_end,
                    ),
                )
            )
        for ev in evidence:
            link = links.get(ev.id)
            claim = link.claim if link else None
            span = ev.span
            payloads.append(
                (
                    ev.id,
                    f"{claim}\n{ev.quote}" if claim else ev.quote,
                    VectorPayload(
                        kind="evidence",
                        paper_id=ev.paper_id,
                        text=ev.quote,
                        chunk_id=ev.chunk_id,
                        page=span.page if span else None,
                        section=ev.section,
                        char_start=span.char_start if span else None,
                        char_end=span.char_end if span else None,
                        evidence_id=ev.id,
                        entity_id=link.subject_id if link else None,
                        entity_type=link.subject_type if link else None,
                        claim=claim,
                        verification_status=ev.verification_status.value,
                        confidence=ev.confidence,
                    ),
                )
            )

        store = self.store
        store.delete_paper(doc.paper_id)
        if payloads:
            store.ensure_collection(self.embedder.dim)
        for i in range(0, len(payloads), BATCH_SIZE):
            batch = payloads[i : i + BATCH_SIZE]
            vectors = self.embedder.embed_documents([text for _, text, _ in batch])
            store.upsert(
                [
                    VectorRecord(id=rid, vector=vec, payload=payload)
                    for (rid, _, payload), vec in zip(batch, vectors, strict=True)
                ]
            )
        return len(doc.chunks), len(evidence)

    def remove_paper(self, paper_id: str) -> None:
        self.store.delete_paper(paper_id)

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        paper_id: str | None = None,
        kind: RecordKind | None = None,
    ) -> list[VectorHit]:
        vector = self.embedder.embed_query(query)
        # One quote can back several claims (e.g. a Method and a Finding), each indexed as its
        # own record. Over-fetch, then keep the best-scoring record per source span.
        hits = self.store.search(vector, limit=limit * 3, paper_id=paper_id, kind=kind)
        seen: set[tuple] = set()
        unique: list[VectorHit] = []
        for hit in hits:
            p = hit.payload
            key = (
                p.kind,
                p.paper_id,
                p.char_start,
                p.char_end,
                p.text if p.char_start is None else "",
            )
            if key not in seen:
                seen.add(key)
                unique.append(hit)
        return unique[:limit]

    def count(self) -> int:
        return self.store.count()
