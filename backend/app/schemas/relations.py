"""Typed relationships of the Scientific Knowledge Graph (see docs/ARCHITECTURE.md)."""

from enum import StrEnum

from pydantic import Field, model_validator

from app.schemas.common import BurhanModel, new_id
from app.schemas.entities import EntityType as E
from app.schemas.evidence import Evidence


class RelationType(StrEnum):
    AUTHORED = "AUTHORED"
    CITES = "CITES"
    USES = "USES"
    EVALUATES = "EVALUATES"
    REPORTS = "REPORTS"
    CLAIMS = "CLAIMS"
    STATES = "STATES"
    COMPARES = "COMPARES"
    IMPROVES = "IMPROVES"
    CONTRADICTS = "CONTRADICTS"
    SUGGESTS = "SUGGESTS"


ALLOWED_ENDPOINTS: dict[RelationType, set[tuple[E, E]]] = {
    RelationType.AUTHORED: {(E.AUTHOR, E.PAPER)},
    RelationType.CITES: {(E.PAPER, E.PAPER)},
    RelationType.USES: {(E.PAPER, E.METHOD)},
    RelationType.EVALUATES: {(E.PAPER, E.DATASET), (E.METHOD, E.DATASET)},
    RelationType.REPORTS: {(E.PAPER, E.METRIC)},
    RelationType.CLAIMS: {(E.PAPER, E.FINDING)},
    RelationType.STATES: {(E.PAPER, E.LIMITATION), (E.PAPER, E.FUTURE_WORK)},
    RelationType.COMPARES: {(E.METHOD, E.METHOD)},
    RelationType.IMPROVES: {(E.METHOD, E.METHOD)},
    RelationType.CONTRADICTS: {(E.FINDING, E.FINDING)},
    RelationType.SUGGESTS: {
        (E.LIMITATION, E.RESEARCH_GAP),
        (E.FUTURE_WORK, E.RESEARCH_GAP),
        (E.FINDING, E.RESEARCH_GAP),
    },
}

# Relations that assert a scientific claim, rather than document structure, need evidence.
EVIDENCE_REQUIRED: set[RelationType] = {
    RelationType.REPORTS,
    RelationType.COMPARES,
    RelationType.IMPROVES,
    RelationType.CONTRADICTS,
    RelationType.SUGGESTS,
}


class Relation(BurhanModel):
    id: str = Field(default_factory=lambda: new_id("rel"))
    type: RelationType
    source_id: str = Field(min_length=1)
    source_type: E
    target_id: str = Field(min_length=1)
    target_type: E
    properties: dict[str, str | int | float | bool | None] = Field(
        default_factory=dict,
        description="e.g. REPORTS: {value: 0.91, unit: 'F1', dataset_id: ..., method_id: ...}",
    )
    evidence: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_schema(self) -> "Relation":
        if (self.source_type, self.target_type) not in ALLOWED_ENDPOINTS[self.type]:
            raise ValueError(
                f"{self.type} not allowed from {self.source_type} to {self.target_type}"
            )
        if self.type in EVIDENCE_REQUIRED and not self.evidence:
            raise ValueError(f"{self.type} relations require evidence")
        if self.source_id == self.target_id:
            raise ValueError("self-referencing relations are not allowed")
        return self
