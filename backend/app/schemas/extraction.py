"""Extraction contracts.

`Draft*` models describe raw LLM output. They ignore unknown keys (so a chatty model does not
force a retry) but are otherwise validated. Drafts never enter the twin directly: they are
grounded against the parsed document and converted into the strict entity schemas, producing
a `PaperKnowledge` result.
"""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.schemas.common import BurhanModel
from app.schemas.documents import ExtractionStatus  # noqa: F401 - re-exported
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
from app.schemas.evidence import Evidence
from app.schemas.relations import Relation

# --- LLM output (drafts) ------------------------------------------------------


class DraftModel(BaseModel):
    model_config = ConfigDict(extra="ignore", str_strip_whitespace=True)


class DraftQuote(DraftModel):
    chunk_id: str | None = None
    quote: str = Field(min_length=1)


class _DraftGrounded(DraftModel):
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    evidence: list[DraftQuote] = Field(default_factory=list)


class DraftStatement(_DraftGrounded):
    text: str = Field(min_length=1)


class DraftEntity(_DraftGrounded):
    name: str = Field(min_length=1)
    description: str | None = None


class DraftMethod(DraftEntity):
    role: Literal["proposed", "baseline", "other"] | None = None


class DraftMetric(DraftEntity):
    higher_is_better: bool | None = None


class DraftResult(_DraftGrounded):
    metric: str = Field(min_length=1)
    value: str | float | None = None
    method: str | None = None
    dataset: str | None = None


class DraftExtraction(DraftModel):
    research_problem: DraftStatement | None = None
    research_questions: list[DraftStatement] = Field(default_factory=list)
    methods: list[DraftMethod] = Field(default_factory=list)
    datasets: list[DraftEntity] = Field(default_factory=list)
    metrics: list[DraftMetric] = Field(default_factory=list)
    results: list[DraftResult] = Field(default_factory=list)
    findings: list[DraftStatement] = Field(default_factory=list)
    limitations: list[DraftStatement] = Field(default_factory=list)
    future_work: list[DraftStatement] = Field(default_factory=list)


class Verdict(StrEnum):
    SUPPORTED = "supported"
    PARTIALLY_SUPPORTED = "partially_supported"
    NOT_SUPPORTED = "not_supported"


class DraftVerdict(DraftModel):
    id: str
    verdict: Verdict
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str | None = None


class DraftVerificationBatch(DraftModel):
    results: list[DraftVerdict] = Field(default_factory=list)


# --- Final, validated result --------------------------------------------------


class ResearchStatement(BurhanModel):
    """A research problem or question, grounded in the paper like any other claim."""

    text: str = Field(min_length=1)
    evidence: list[Evidence] = Field(min_length=1)


class DroppedItem(BurhanModel):
    """An LLM-proposed item rejected during grounding, kept for transparency."""

    kind: str
    text: str
    reason: str


class ExtractionStats(BurhanModel):
    windows_total: int = 0
    windows_failed: int = 0
    llm_calls: int = 0
    items_proposed: int = 0
    items_kept: int = 0
    items_dropped: int = 0
    evidence_verified: int = 0
    evidence_flagged: int = 0
    evidence_unverified: int = 0


class ExtractionMeta(BurhanModel):
    provider: str
    models: list[str] = Field(default_factory=list)
    prompt_version: str
    started_at: datetime
    finished_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    stats: ExtractionStats = Field(default_factory=ExtractionStats)
    dropped: list[DroppedItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class PaperKnowledge(BurhanModel):
    """Structured, evidence-backed knowledge extracted from one paper (input to the KG)."""

    paper: Paper
    research_problem: ResearchStatement | None = None
    research_questions: list[ResearchStatement] = Field(default_factory=list)
    methods: list[Method] = Field(default_factory=list)
    datasets: list[Dataset] = Field(default_factory=list)
    metrics: list[Metric] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    limitations: list[Limitation] = Field(default_factory=list)
    future_work: list[FutureWork] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)
    meta: ExtractionMeta

    def entities(self) -> list:
        return [
            self.paper,
            *self.methods,
            *self.datasets,
            *self.metrics,
            *self.findings,
            *self.limitations,
            *self.future_work,
        ]

    def all_evidence(self) -> list[Evidence]:
        statements = [s for s in [self.research_problem, *self.research_questions] if s]
        return [
            *(ev for e in self.entities() for ev in e.evidence),
            *(ev for s in statements for ev in s.evidence),
            *(ev for r in self.relations for ev in r.evidence),
        ]

    @model_validator(mode="after")
    def _check_integrity(self) -> "PaperKnowledge":
        pid = self.paper.id
        for ev in self.all_evidence():
            if ev.paper_id != pid:
                raise ValueError(f"evidence {ev.id} cites paper {ev.paper_id}, expected {pid}")
            if ev.span is None or ev.span.page is None or ev.span.char_start is None:
                raise ValueError(f"evidence {ev.id} is missing its page/offset location")
            if not ev.section or not ev.chunk_id:
                raise ValueError(f"evidence {ev.id} is missing its section or chunk")

        types: dict[str, EntityType] = {e.id: e.type for e in self.entities()}
        if len(types) != len(self.entities()):
            raise ValueError("duplicate entity ids")
        for r in self.relations:
            if types.get(r.source_id) != r.source_type or types.get(r.target_id) != r.target_type:
                raise ValueError(f"relation {r.id} references an entity not in this paper")
        return self
