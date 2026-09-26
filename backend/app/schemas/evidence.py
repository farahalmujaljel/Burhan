"""Evidence and provenance: every scientific claim in Burhan must link back to source text."""

from enum import StrEnum

from pydantic import Field, model_validator

from app.schemas.common import BurhanModel, new_id


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"  # extracted, not yet checked
    VERIFIED = "verified"  # quote found in source and supports the claim
    FLAGGED = "flagged"  # quote missing from source or does not support the claim


class ConfidenceLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


def confidence_level(score: float) -> ConfidenceLevel:
    if score >= 0.8:
        return ConfidenceLevel.HIGH
    if score >= 0.5:
        return ConfidenceLevel.MEDIUM
    return ConfidenceLevel.LOW


class SourceSpan(BurhanModel):
    """Location of a quote inside the parsed paper text."""

    page: int | None = Field(default=None, ge=1)
    char_start: int | None = Field(default=None, ge=0)
    char_end: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def _check_offsets(self) -> "SourceSpan":
        if (self.char_start is None) != (self.char_end is None):
            raise ValueError("char_start and char_end must be provided together")
        if self.char_start is not None and self.char_end <= self.char_start:
            raise ValueError("char_end must be greater than char_start")
        return self


class Evidence(BurhanModel):
    id: str = Field(default_factory=lambda: new_id("ev"))
    paper_id: str = Field(min_length=1)
    quote: str = Field(min_length=1, description="Verbatim text from the source paper")
    section: str | None = None
    chunk_id: str | None = None
    span: SourceSpan | None = None
    extracted_by: str = Field(min_length=1, description="Agent that produced this evidence")
    model: str | None = Field(default=None, description="LLM used, if any")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    verification_note: str | None = None

    @property
    def confidence_level(self) -> ConfidenceLevel:
        return confidence_level(self.confidence)
