"""Research Digital Twin: the evolving, evidence-backed model of a research field."""

from datetime import UTC, datetime
from typing import Literal

from pydantic import Field, model_validator

from app.schemas.common import BurhanModel, new_id
from app.schemas.entities import Entity, EntityType, ResearchGap
from app.schemas.evidence import Evidence
from app.schemas.graph import PossibleDuplicate, ResolutionDecision
from app.schemas.relations import Relation


def _now() -> datetime:
    return datetime.now(UTC)


class Contradiction(BurhanModel):
    id: str = Field(default_factory=lambda: new_id("contra"))
    finding_a_id: str
    finding_b_id: str
    explanation: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=2, description="At least one quote per finding")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _distinct(self) -> "Contradiction":
        if self.finding_a_id == self.finding_b_id:
            raise ValueError("a finding cannot contradict itself")
        return self


class ComparisonCell(BurhanModel):
    paper_id: str
    method_id: str | None = None
    dataset_id: str | None = None
    metric_id: str | None = None
    value: str | float | None = None
    evidence_id: str | None = None


class Comparison(BurhanModel):
    """A cross-paper table, e.g. methods x datasets with reported metric values."""

    id: str = Field(default_factory=lambda: new_id("cmp"))
    title: str
    dimension: str = Field(description="e.g. 'method_dataset', 'limitations'")
    cells: list[ComparisonCell] = Field(default_factory=list)


class GapCard(BurhanModel):
    gap: ResearchGap
    rank: int = Field(ge=1)


class TwinUpdate(BurhanModel):
    """Changelog entry recording how one ingestion run changed the twin.

    - added: new nodes/edges
    - strengthened: existing nodes/edges that gained supporting papers or evidence
    - changed: existing nodes/edges whose content changed without gaining support
      (e.g. new aliases, or re-extraction replaced their evidence)
    - removed: nodes/edges no longer supported by any paper (e.g. after re-extraction)
    """

    id: str = Field(default_factory=lambda: new_id("upd"))
    created_at: datetime = Field(default_factory=_now)
    operation: Literal["apply", "remove"] = "apply"
    paper_ids: list[str] = Field(default_factory=list)
    added_entity_ids: list[str] = Field(default_factory=list)
    strengthened_entity_ids: list[str] = Field(default_factory=list)
    changed_entity_ids: list[str] = Field(default_factory=list)
    removed_entity_ids: list[str] = Field(default_factory=list)
    added_relation_ids: list[str] = Field(default_factory=list)
    strengthened_relation_ids: list[str] = Field(default_factory=list)
    changed_relation_ids: list[str] = Field(default_factory=list)
    removed_relation_ids: list[str] = Field(default_factory=list)
    new_contradiction_ids: list[str] = Field(default_factory=list)
    new_gap_ids: list[str] = Field(default_factory=list)
    resolutions: list[ResolutionDecision] = Field(
        default_factory=list, description="Entity names merged into existing canonical nodes"
    )
    possible_duplicates: list[PossibleDuplicate] = Field(default_factory=list)
    evidence_indexed: int = 0
    chunks_indexed: int = 0
    summary: str | None = None

    @property
    def is_noop(self) -> bool:
        return not any(
            (
                self.added_entity_ids,
                self.strengthened_entity_ids,
                self.changed_entity_ids,
                self.removed_entity_ids,
                self.added_relation_ids,
                self.strengthened_relation_ids,
                self.changed_relation_ids,
                self.removed_relation_ids,
            )
        )


class TwinStats(BurhanModel):
    entity_counts: dict[str, int]
    relation_count: int
    contradiction_count: int
    verified_evidence: int
    flagged_evidence: int


class RankedEntity(BurhanModel):
    id: str
    name: str
    paper_count: int


class TwinSummary(BurhanModel):
    """Dashboard-level view of the Research Digital Twin."""

    domain: str
    paper_count: int
    stats: TwinStats
    unverified_evidence: int
    relation_counts: dict[str, int]
    indexed_vectors: int
    top_methods: list[RankedEntity]
    top_datasets: list[RankedEntity]
    top_metrics: list[RankedEntity]
    last_update: TwinUpdate | None = None


class TwinSnapshot(BurhanModel):
    domain: str
    generated_at: datetime = Field(default_factory=_now)
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    contradictions: list[Contradiction] = Field(default_factory=list)
    comparisons: list[Comparison] = Field(default_factory=list)
    updates: list[TwinUpdate] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_integrity(self) -> "TwinSnapshot":
        ids = [e.id for e in self.entities]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate entity ids")
        types = {e.id: e.type for e in self.entities}
        paper_ids = {i for i, t in types.items() if t == EntityType.PAPER}

        for r in self.relations:
            for end_id, end_type in ((r.source_id, r.source_type), (r.target_id, r.target_type)):
                if types.get(end_id) != end_type:
                    raise ValueError(f"relation {r.id} references unknown {end_type} {end_id}")

        for c in self.contradictions:
            for fid in (c.finding_a_id, c.finding_b_id):
                if types.get(fid) != EntityType.FINDING:
                    raise ValueError(f"contradiction {c.id} references unknown finding {fid}")

        for ev in self.all_evidence():
            if ev.paper_id not in paper_ids:
                raise ValueError(f"evidence {ev.id} cites unknown paper {ev.paper_id}")
        return self

    def all_evidence(self) -> list[Evidence]:
        return [
            *(ev for e in self.entities for ev in e.evidence),
            *(ev for r in self.relations for ev in r.evidence),
            *(ev for c in self.contradictions for ev in c.evidence),
        ]

    @property
    def gaps(self) -> list[ResearchGap]:
        return [e for e in self.entities if isinstance(e, ResearchGap)]
