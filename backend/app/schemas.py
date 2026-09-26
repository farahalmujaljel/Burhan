from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class PaperMetadata(BaseModel):
    title: str
    authors: list[str] = Field(default_factory=list)
    year: int | None = None
    abstract: str = ""
    sections: dict[str, str] = Field(default_factory=dict)


class ScientificExtraction(BaseModel):
    problem: str
    objective: str
    method: str
    dataset: str
    metrics: list[str] = Field(default_factory=list)
    findings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    future_work: list[str] = Field(default_factory=list)
    evidence_quotes: list[str] = Field(default_factory=list)


class PaperRecord(BaseModel):
    id: str
    filename: str
    local_path: str
    metadata: PaperMetadata
    extraction: ScientificExtraction


class GraphNode(BaseModel):
    id: str
    type: Literal["Paper", "Method", "Dataset", "Metric", "Finding", "Limitation", "ResearchGap"]
    label: str
    metadata: dict[str, str | int | list[str] | None] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    type: Literal["USES", "EVALUATES", "COMPARES", "CITES", "IMPROVES", "CONTRADICTS", "REPORTS", "CLAIMS", "STATES", "SUGGESTS"]


class CrossPaperAnalysis(BaseModel):
    most_common_methods: list[str]
    most_common_datasets: list[str]
    repeated_limitations: list[str]
    contradictions: list[str]
    common_metrics: list[str]


class ResearchGap(BaseModel):
    title: str
    description: str
    supporting_papers: list[str]
    evidence: list[str]


class GroundedAnswer(BaseModel):
    question: str
    answer: str
    citations: list[str]
    evidence: list[str]


class TwinState(BaseModel):
    run_id: str
    created_at: datetime
    papers: list[PaperRecord]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    analysis: CrossPaperAnalysis
    research_gap: ResearchGap
    grounded_answer: GroundedAnswer | None = None


class RunSummary(BaseModel):
    run_id: str
    status: Literal["queued", "parsing", "extracting", "storing", "reasoning", "complete", "failed"]
    progress: int
    message: str
    twin: TwinState | None = None
