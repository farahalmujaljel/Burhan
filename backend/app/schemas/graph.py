"""Storage-agnostic graph records for the Scientific Knowledge Graph.

Nodes and edges carry `paper_ids` (which papers support them) and `evidence_ids` (which
Evidence records back them). Evidence itself is stored separately and looked up by ID.
"""

from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import BurhanModel
from app.schemas.entities import EntityType
from app.schemas.evidence import Evidence
from app.schemas.relations import EVIDENCE_REQUIRED, RelationType

PropertyValue = str | int | float | bool | list[str] | None

# Node types whose existence is itself a claim: they must always be backed by evidence.
CLAIM_NODE_TYPES = {EntityType.FINDING, EntityType.LIMITATION, EntityType.FUTURE_WORK}
# Node types shared across papers and merged by entity resolution.
RESOLVABLE_TYPES = {EntityType.METHOD, EntityType.DATASET, EntityType.METRIC}


class GraphNode(BurhanModel):
    id: str
    type: EntityType
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    description: str | None = None
    paper_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    properties: dict[str, PropertyValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _claims_need_evidence(self) -> "GraphNode":
        if self.type in CLAIM_NODE_TYPES and not self.evidence_ids:
            raise ValueError(f"{self.type} node {self.id} must reference evidence")
        return self


class GraphEdge(BurhanModel):
    id: str
    type: RelationType
    source_id: str
    source_type: EntityType
    target_id: str
    target_type: EntityType
    paper_ids: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    properties: dict[str, PropertyValue] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _claims_need_evidence(self) -> "GraphEdge":
        if self.type in EVIDENCE_REQUIRED and not self.evidence_ids:
            raise ValueError(f"{self.type} edge {self.id} must reference evidence")
        return self


class GraphView(BurhanModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]


class NodeDetail(BurhanModel):
    node: GraphNode
    edges: list[GraphEdge]
    neighbors: list[GraphNode]
    evidence: list[Evidence]


class ResolutionDecision(BurhanModel):
    """How an extracted entity name was mapped to a canonical graph node."""

    entity_type: EntityType
    original_name: str
    canonical_id: str
    canonical_name: str
    method: Literal["new", "exact", "normalized", "acronym", "fuzzy"]
    confidence: float = Field(ge=0.0, le=1.0)


class PossibleDuplicate(BurhanModel):
    """A similar-but-not-merged pair, surfaced for human review instead of auto-merging."""

    entity_type: EntityType
    name: str
    candidate_id: str
    candidate_name: str
    score: float
