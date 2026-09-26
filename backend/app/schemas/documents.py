"""Parsed paper representation.

Offsets index into `ParsedDocument.text` so evidence quotes can be anchored to source.
"""

from bisect import bisect_right
from datetime import UTC, datetime
from enum import StrEnum

from pydantic import ConfigDict, Field, model_validator

from app.schemas.common import BurhanModel, new_id

# Parsed text is whitespace-sensitive: stripping would break character offsets.
_RAW_TEXT = ConfigDict(str_strip_whitespace=False)


class SectionKind(StrEnum):
    FRONT_MATTER = "front_matter"
    ABSTRACT = "abstract"
    INTRODUCTION = "introduction"
    RELATED_WORK = "related_work"
    METHODS = "methods"
    EXPERIMENTS = "experiments"
    RESULTS = "results"
    DISCUSSION = "discussion"
    LIMITATIONS = "limitations"
    FUTURE_WORK = "future_work"
    CONCLUSION = "conclusion"
    ACKNOWLEDGMENTS = "acknowledgments"
    REFERENCES = "references"
    APPENDIX = "appendix"
    OTHER = "other"


class PageSpan(BurhanModel):
    """Where one PDF page's text lives inside `ParsedDocument.text`."""

    page_number: int = Field(ge=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)


class Section(BurhanModel):
    id: str = Field(default_factory=lambda: new_id("sec"))
    title: str = Field(min_length=1)
    kind: SectionKind = SectionKind.OTHER
    page_start: int | None = Field(default=None, ge=1)
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)


class Chunk(BurhanModel):
    model_config = _RAW_TEXT

    id: str = Field(default_factory=lambda: new_id("chunk"))
    paper_id: str = Field(min_length=1)
    section_id: str | None = None
    section_title: str | None = None
    text: str = Field(min_length=1)
    page: int | None = Field(default=None, ge=1, description="Page where the chunk starts")
    page_end: int | None = Field(default=None, ge=1, description="Page where the chunk ends")
    char_start: int = Field(ge=0)
    char_end: int = Field(ge=0)


class ParsedDocument(BurhanModel):
    model_config = _RAW_TEXT

    paper_id: str = Field(min_length=1)
    file_name: str
    title: str | None = None
    parser: str = Field(description="e.g. 'pymupdf' or 'docling'")
    page_count: int = Field(ge=0)
    text: str
    pages: list[PageSpan] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    chunks: list[Chunk] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_offsets(self) -> "ParsedDocument":
        n = len(self.text)
        prev_end = 0
        for p in self.pages:
            if not prev_end <= p.char_start <= p.char_end <= n:
                raise ValueError(f"page {p.page_number} offsets out of order or range")
            prev_end = p.char_end
        for s in self.sections:
            if not 0 <= s.char_start < s.char_end <= n:
                raise ValueError(f"section {s.id} offsets out of range")
        for c in self.chunks:
            if c.paper_id != self.paper_id:
                raise ValueError(f"chunk {c.id} belongs to another paper")
            if self.text[c.char_start : c.char_end] != c.text:
                raise ValueError(f"chunk {c.id} text does not match document offsets")
        return self

    def page_for_offset(self, offset: int) -> int | None:
        """Return the 1-based page containing `offset` (separators map to the preceding page)."""
        if not self.pages or offset < self.pages[0].char_start:
            return None
        idx = bisect_right([p.char_start for p in self.pages], offset) - 1
        return self.pages[idx].page_number


class PaperStatus(StrEnum):
    UPLOADED = "uploaded"
    PARSED = "parsed"
    FAILED = "failed"


class ExtractionStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PaperRecord(BurhanModel):
    """Ingestion bookkeeping for one uploaded PDF."""

    paper_id: str
    file_name: str
    sha256: str
    size_bytes: int = Field(ge=0)
    status: PaperStatus = PaperStatus.UPLOADED
    error: str | None = None
    title: str | None = None
    parser: str | None = None
    page_count: int | None = None
    section_count: int | None = None
    chunk_count: int | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    parsed_at: datetime | None = None
    extraction_status: ExtractionStatus | None = None
    extraction_error: str | None = None
    extracted_at: datetime | None = None
    twin_updated_at: datetime | None = None
    twin_error: str | None = None
