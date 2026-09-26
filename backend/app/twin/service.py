"""Research Digital Twin service: applies papers to the knowledge layer and serves read models."""

import logging
import threading
from collections import Counter
from datetime import UTC, datetime

from app.core.errors import NotFoundError
from app.knowledge.graph_store.base import GraphStore
from app.knowledge.vector_store.base import RecordKind, VectorHit
from app.schemas.entities import (
    Dataset,
    EntityType,
    Finding,
    FutureWork,
    Limitation,
    Method,
    Metric,
    Paper,
)
from app.schemas.evidence import VerificationStatus
from app.schemas.graph import GraphEdge, GraphNode, GraphView, NodeDetail
from app.schemas.relations import Relation
from app.schemas.twin import RankedEntity, TwinSnapshot, TwinStats, TwinSummary, TwinUpdate
from app.services.document_store import DocumentStore
from app.twin.builder import BuildResult, TwinBuilder
from app.twin.evidence_index import EvidenceIndex
from app.twin.repository import TwinUpdateLog

logger = logging.getLogger(__name__)

_ENTITY_CLASSES = {
    EntityType.METHOD: Method,
    EntityType.DATASET: Dataset,
    EntityType.METRIC: Metric,
    EntityType.FINDING: Finding,
    EntityType.LIMITATION: Limitation,
    EntityType.FUTURE_WORK: FutureWork,
}
TOP_N = 10


class TwinService:
    def __init__(
        self,
        documents: DocumentStore,
        graph: GraphStore,
        index: EvidenceIndex,
        log: TwinUpdateLog,
        *,
        domain: str,
    ) -> None:
        self.documents = documents
        self.graph = graph
        self.index = index
        self.log = log
        self.domain = domain
        self.builder = TwinBuilder(graph)
        self._lock = threading.Lock()  # one twin mutation at a time

    # --- updates -----------------------------------------------------------------

    def apply_paper(self, paper_id: str) -> TwinUpdate:
        """Merge a paper's extracted knowledge into the graph and evidence index."""
        knowledge = self.documents.get_knowledge(paper_id)
        doc = self.documents.get_document(paper_id)
        with self._lock:
            result = self.builder.apply(knowledge)
            chunks, evidence = self.index.index_paper(doc, result.evidence, result.links)
            update = result.update
            update.chunks_indexed, update.evidence_indexed = chunks, evidence
            update.summary = self._summarize(knowledge.paper.name, result)
            self.log.append(update)
        self._mark_record(paper_id, updated=True, error=None)
        return update

    def apply_paper_safely(self, paper_id: str) -> None:
        """Hook for the extraction pipeline: failures are recorded, never raised."""
        try:
            self.apply_paper(paper_id)
        except Exception as exc:
            logger.exception("Twin update failed for %s", paper_id)
            message = getattr(exc, "message", None) or str(exc)
            self._mark_record(paper_id, updated=False, error=message)

    def remove_paper(self, paper_id: str) -> TwinUpdate:
        self.documents.get_record(paper_id)  # 404 for unknown papers
        with self._lock:
            result = self.builder.remove(paper_id)
            self.index.remove_paper(paper_id)
            result.update.summary = self._summarize(paper_id, result)
            self.log.append(result.update)
        self._mark_record(paper_id, updated=False, error=None, clear=True)
        return result.update

    def _mark_record(self, paper_id: str, *, updated: bool, error: str | None, clear=False):
        record = self.documents.get_record(paper_id)
        changes: dict = {"twin_error": error}
        if updated:
            changes["twin_updated_at"] = datetime.now(UTC)
        if clear:
            changes["twin_updated_at"] = None
        self.documents.save_record(record.model_copy(update=changes))

    @staticmethod
    def _summarize(title: str, result: BuildResult) -> str:
        u = result.update
        if u.is_noop:
            return f"'{title}': no changes (already up to date)."
        verb = "Applied" if u.operation == "apply" else "Removed"
        parts = [
            f"+{len(u.added_entity_ids)} entities",
            f"+{len(u.added_relation_ids)} relations",
            f"{len(u.strengthened_entity_ids)} entities strengthened",
            f"{len(u.changed_entity_ids) + len(u.changed_relation_ids)} changed",
            f"{len(u.removed_entity_ids) + len(u.removed_relation_ids)} removed",
        ]
        if u.resolutions:
            parts.append(f"{len(u.resolutions)} names merged into existing entities")
        return f"{verb} '{title}': " + ", ".join(parts) + "."

    # --- read models -------------------------------------------------------------

    def summary(self) -> TwinSummary:
        nodes = self.graph.find_nodes()
        edges = self.graph.find_edges()
        evidence = self.graph.all_evidence()
        statuses = Counter(e.verification_status for e in evidence)

        def top(t: EntityType) -> list[RankedEntity]:
            ranked = sorted(
                (n for n in nodes if n.type == t), key=lambda n: (-len(n.paper_ids), n.name)
            )
            return [
                RankedEntity(id=n.id, name=n.name, paper_count=len(n.paper_ids))
                for n in ranked[:TOP_N]
            ]

        return TwinSummary(
            domain=self.domain,
            paper_count=sum(n.type == EntityType.PAPER for n in nodes),
            stats=TwinStats(
                entity_counts=dict(Counter(str(n.type) for n in nodes)),
                relation_count=len(edges),
                contradiction_count=0,  # contradiction detection arrives in a later phase
                verified_evidence=statuses[VerificationStatus.VERIFIED],
                flagged_evidence=statuses[VerificationStatus.FLAGGED],
            ),
            unverified_evidence=statuses[VerificationStatus.UNVERIFIED],
            relation_counts=dict(Counter(str(e.type) for e in edges)),
            indexed_vectors=self.index.count(),
            top_methods=top(EntityType.METHOD),
            top_datasets=top(EntityType.DATASET),
            top_metrics=top(EntityType.METRIC),
            last_update=self.log.last(),
        )

    def graph_view(
        self,
        *,
        paper_id: str | None = None,
        types: list[EntityType] | None = None,
        limit: int = 500,
    ) -> GraphView:
        nodes = self.graph.find_nodes(types=types, paper_id=paper_id, limit=limit)
        ids = {n.id for n in nodes}
        edges = [
            e
            for e in self.graph.find_edges(node_ids=list(ids))
            if e.source_id in ids and e.target_id in ids
        ]
        return GraphView(nodes=nodes, edges=edges)

    def node_detail(self, node_id: str) -> NodeDetail:
        node = self.graph.get_nodes([node_id]).get(node_id)
        if node is None:
            raise NotFoundError(f"Graph node '{node_id}' not found", details={"node_id": node_id})
        edges = self.graph.find_edges(node_ids=[node_id])
        neighbor_ids = {e.source_id for e in edges} | {e.target_id for e in edges}
        neighbor_ids.discard(node_id)
        evidence_ids = sorted({*node.evidence_ids, *(i for e in edges for i in e.evidence_ids)})
        return NodeDetail(
            node=node,
            edges=edges,
            neighbors=list(self.graph.get_nodes(sorted(neighbor_ids)).values()),
            evidence=self.graph.get_evidence(evidence_ids),
        )

    def search(
        self,
        query: str,
        *,
        limit: int = 10,
        paper_id: str | None = None,
        kind: RecordKind | None = None,
    ) -> list[VectorHit]:
        return self.index.search(query, limit=limit, paper_id=paper_id, kind=kind)

    def updates(self, limit: int | None = None) -> list[TwinUpdate]:
        return self.log.list(limit)

    def snapshot(self) -> TwinSnapshot:
        """Full twin as validated domain entities (integrity is re-checked on construction)."""
        nodes = self.graph.find_nodes()
        edges = self.graph.find_edges()
        evidence = {e.id: e for e in self.graph.all_evidence()}
        return TwinSnapshot(
            domain=self.domain,
            entities=[self._entity(n, evidence) for n in nodes],
            relations=[self._relation(e, evidence) for e in edges],
            updates=self.log.list(),
        )

    @staticmethod
    def _entity(node: GraphNode, evidence: dict):
        ev = [evidence[i] for i in node.evidence_ids if i in evidence]
        common = dict(
            id=node.id,
            name=node.name,
            aliases=node.aliases,
            description=node.description,
            evidence=ev,
        )
        p = node.properties
        if node.type == EntityType.PAPER:
            return Paper(
                **common,
                year=p.get("year"),
                venue=p.get("venue"),
                doi=p.get("doi"),
                file_name=p.get("file_name"),
                abstract=p.get("abstract"),
            )
        cls = _ENTITY_CLASSES[node.type]
        if node.type == EntityType.METRIC:
            return cls(**common, higher_is_better=p.get("higher_is_better"))
        if node.type in (EntityType.FINDING, EntityType.LIMITATION, EntityType.FUTURE_WORK):
            return cls(**common, paper_id=node.paper_ids[0])
        return cls(**common)

    @staticmethod
    def _relation(edge: GraphEdge, evidence: dict) -> Relation:
        return Relation(
            id=edge.id,
            type=edge.type,
            source_id=edge.source_id,
            source_type=edge.source_type,
            target_id=edge.target_id,
            target_type=edge.target_type,
            properties={k: v for k, v in edge.properties.items() if not isinstance(v, list)},
            evidence=[evidence[i] for i in edge.evidence_ids if i in evidence],
            confidence=edge.confidence,
        )
