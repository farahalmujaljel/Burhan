"""Scientific entities stored in the Research Digital Twin / Knowledge Graph.

Claim-like entities (Finding, Limitation, FutureWork, ResearchGap) must carry evidence.
Paper-bound entities may only cite evidence from their own paper.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, model_validator

from app.schemas.common import BurhanModel, new_id
from app.schemas.evidence import Evidence


class EntityType(StrEnum):
    PAPER = "Paper"
    AUTHOR = "Author"
    METHOD = "Method"
    DATASET = "Dataset"
    METRIC = "Metric"
    FINDING = "Finding"
    LIMITATION = "Limitation"
    FUTURE_WORK = "FutureWork"
    RESEARCH_GAP = "ResearchGap"


class EntityBase(BurhanModel):
    id: str
    name: str = Field(min_length=1)
    description: str | None = None
    aliases: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class Paper(EntityBase):
    type: Literal[EntityType.PAPER] = EntityType.PAPER
    id: str = Field(default_factory=lambda: new_id("paper"))
    year: int | None = Field(default=None, ge=1900, le=2100)
    venue: str | None = None
    doi: str | None = None
    url: str | None = None
    file_name: str | None = None
    abstract: str | None = None


class Author(EntityBase):
    type: Literal[EntityType.AUTHOR] = EntityType.AUTHOR
    id: str = Field(default_factory=lambda: new_id("author"))
    affiliation: str | None = None


class Method(EntityBase):
    type: Literal[EntityType.METHOD] = EntityType.METHOD
    id: str = Field(default_factory=lambda: new_id("method"))


class Dataset(EntityBase):
    type: Literal[EntityType.DATASET] = EntityType.DATASET
    id: str = Field(default_factory=lambda: new_id("dataset"))


class Metric(EntityBase):
    type: Literal[EntityType.METRIC] = EntityType.METRIC
    id: str = Field(default_factory=lambda: new_id("metric"))
    higher_is_better: bool | None = None


class _PaperBoundClaim(EntityBase):
    """A claim stated in one specific paper, backed by at least one quote from it."""

    paper_id: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)

    @model_validator(mode="after")
    def _evidence_from_own_paper(self) -> "_PaperBoundClaim":
        foreign = {e.paper_id for e in self.evidence} - {self.paper_id}
        if foreign:
            raise ValueError(
                f"evidence must come from paper {self.paper_id}, got {sorted(foreign)}"
            )
        return self


class Finding(_PaperBoundClaim):
    type: Literal[EntityType.FINDING] = EntityType.FINDING
    id: str = Field(default_factory=lambda: new_id("finding"))


class Limitation(_PaperBoundClaim):
    type: Literal[EntityType.LIMITATION] = EntityType.LIMITATION
    id: str = Field(default_factory=lambda: new_id("limitation"))


class FutureWork(_PaperBoundClaim):
    type: Literal[EntityType.FUTURE_WORK] = EntityType.FUTURE_WORK
    id: str = Field(default_factory=lambda: new_id("future"))


class GapSignal(StrEnum):
    """Structured signals a research gap can be derived from (see AI_METHODOLOGY.md)."""

    REPEATED_LIMITATION = "repeated_limitation"
    FUTURE_WORK = "future_work"
    CONTRADICTION = "contradiction"
    MISSING_COMPARISON = "missing_comparison"
    UNDEREXPLORED_METRIC = "underexplored_metric"
    WEAK_EVIDENCE = "weak_evidence"


class ResearchGap(EntityBase):
    """A cross-paper gap. Never speculative: it must cite signals, entities, and evidence."""

    type: Literal[EntityType.RESEARCH_GAP] = EntityType.RESEARCH_GAP
    id: str = Field(default_factory=lambda: new_id("gap"))
    rationale: str = Field(min_length=1)
    signals: list[GapSignal] = Field(min_length=1)
    supporting_entity_ids: list[str] = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @property
    def paper_ids(self) -> list[str]:
        return sorted({e.paper_id for e in self.evidence})


Entity = Annotated[
    Paper | Author | Method | Dataset | Metric | Finding | Limitation | FutureWork | ResearchGap,
    Field(discriminator="type"),
]
