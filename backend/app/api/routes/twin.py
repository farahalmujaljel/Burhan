"""Research Digital Twin, knowledge graph, and evidence search endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_twin
from app.knowledge.vector_store.base import RecordKind, VectorHit
from app.schemas.entities import EntityType
from app.schemas.graph import GraphView, NodeDetail
from app.schemas.twin import TwinSnapshot, TwinSummary, TwinUpdate
from app.twin.service import TwinService

router = APIRouter(tags=["twin"])

Twin = Annotated[TwinService, Depends(get_twin)]


@router.post("/twin/papers/{paper_id}", response_model=TwinUpdate)
def apply_paper(paper_id: str, twin: Twin) -> TwinUpdate:
    """Merge a paper's extracted knowledge into the twin (idempotent; runs automatically
    after a successful extraction). Returns what was added, strengthened, changed, or removed."""
    return twin.apply_paper(paper_id)


@router.delete("/twin/papers/{paper_id}", response_model=TwinUpdate)
def remove_paper(paper_id: str, twin: Twin) -> TwinUpdate:
    """Remove a paper's contribution; shared entities keep other papers' support."""
    return twin.remove_paper(paper_id)


@router.get("/twin/summary", response_model=TwinSummary)
def twin_summary(twin: Twin) -> TwinSummary:
    return twin.summary()


@router.get("/twin/snapshot", response_model=TwinSnapshot)
def twin_snapshot(twin: Twin) -> TwinSnapshot:
    """The full twin as validated entities, relations (with evidence), and update history."""
    return twin.snapshot()


@router.get("/twin/updates", response_model=list[TwinUpdate])
def twin_updates(
    twin: Twin, limit: Annotated[int | None, Query(ge=1, le=500)] = 50
) -> list[TwinUpdate]:
    """Change history, newest first."""
    return twin.updates(limit)


@router.get("/graph", response_model=GraphView)
def graph(
    twin: Twin,
    paper_id: str | None = None,
    type: Annotated[list[EntityType] | None, Query(description="Filter node types")] = None,
    limit: Annotated[int, Query(ge=1, le=5000)] = 500,
) -> GraphView:
    """Nodes and the edges between them, for graph visualization."""
    return twin.graph_view(paper_id=paper_id, types=type, limit=limit)


@router.get("/graph/nodes/{node_id}", response_model=NodeDetail)
def graph_node(node_id: str, twin: Twin) -> NodeDetail:
    """A node with its edges, neighbors, and the full evidence behind them."""
    return twin.node_detail(node_id)


@router.get("/evidence/search", response_model=list[VectorHit])
def search_evidence(
    twin: Twin,
    q: Annotated[str, Query(min_length=2)],
    paper_id: str | None = None,
    kind: RecordKind | None = None,
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
) -> list[VectorHit]:
    """Semantic search over indexed evidence quotes and chunks (local embeddings)."""
    return twin.search(q, limit=limit, paper_id=paper_id, kind=kind)
