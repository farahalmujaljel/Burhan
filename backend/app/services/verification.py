"""Semantic evidence verification: does the (already located) quote support the claim?

Runs after deterministic grounding. Checks are batched to limit LLM calls. If the verifier
fails, affected evidence stays `unverified`; it is never silently marked as verified.
"""

import json
import logging
from dataclasses import dataclass, field

from app.core.errors import BurhanError
from app.llm.base import ChatMessage, LLMClient
from app.llm.prompts import render_prompt
from app.llm.structured import generate_structured
from app.schemas.evidence import Evidence, VerificationStatus
from app.schemas.extraction import DraftVerdict, DraftVerificationBatch, Verdict

logger = logging.getLogger(__name__)

VERIFIER = "evidence_verification"
MAX_QUOTE_CHARS_FOR_CHECK = 1200


@dataclass(frozen=True)
class ClaimCheck:
    id: str  # evidence id
    kind: str
    claim: str
    quote: str


@dataclass
class VerificationOutcome:
    verdicts: dict[str, DraftVerdict] = field(default_factory=dict)
    models: set[str] = field(default_factory=set)
    llm_calls: int = 0
    warnings: list[str] = field(default_factory=list)


class EvidenceVerifier:
    def __init__(
        self, llm: LLMClient, *, batch_size: int = 12, max_attempts: int = 3, max_tokens: int = 2048
    ) -> None:
        self.llm = llm
        self.batch_size = batch_size
        self.max_attempts = max_attempts
        self.max_tokens = max_tokens

    def verify(self, checks: list[ClaimCheck]) -> VerificationOutcome:
        outcome = VerificationOutcome()
        for i in range(0, len(checks), self.batch_size):
            batch = checks[i : i + self.batch_size]
            items = "\n".join(
                json.dumps(
                    {
                        "id": c.id,
                        "kind": c.kind,
                        "claim": c.claim,
                        "quote": c.quote[:MAX_QUOTE_CHARS_FOR_CHECK],
                    },
                    ensure_ascii=False,
                )
                for c in batch
            )
            messages = [
                ChatMessage("system", render_prompt("verification_system")),
                ChatMessage("user", render_prompt("verification_user", items=items)),
            ]
            try:
                result = generate_structured(
                    self.llm,
                    messages,
                    DraftVerificationBatch,
                    max_attempts=self.max_attempts,
                    max_tokens=self.max_tokens,
                )
            except BurhanError as exc:
                outcome.llm_calls += self.max_attempts
                batch_no = i // self.batch_size + 1
                outcome.warnings.append(f"Verification batch {batch_no} failed: {exc}")
                logger.warning("Verification batch failed: %s", exc)
                continue
            outcome.llm_calls += result.attempts
            outcome.models.add(result.model)
            wanted = {c.id for c in batch}
            for verdict in result.value.results:
                if verdict.id in wanted:
                    outcome.verdicts[verdict.id] = verdict
        return outcome


def apply_verdict(evidence: Evidence, verdict: DraftVerdict | None, model: str | None) -> None:
    """Update evidence status/confidence from the verifier's verdict (in place)."""
    if verdict is None:
        evidence.verification_status = VerificationStatus.UNVERIFIED
        evidence.verification_note = _join(evidence.verification_note, "semantic check unavailable")
        return

    reason = f"{verdict.verdict.value}: {verdict.reason or 'no reason given'}"
    if model:
        reason += f" [{VERIFIER}, {model}]"
    if verdict.verdict == Verdict.SUPPORTED:
        evidence.verification_status = VerificationStatus.VERIFIED
        evidence.confidence = round(min(evidence.confidence, verdict.confidence), 3)
    else:
        cap = 0.5 if verdict.verdict == Verdict.PARTIALLY_SUPPORTED else 0.2
        evidence.verification_status = VerificationStatus.FLAGGED
        evidence.confidence = round(min(evidence.confidence, verdict.confidence, cap), 3)
    evidence.verification_note = _join(evidence.verification_note, reason)


def _join(existing: str | None, extra: str) -> str:
    return f"{existing}; {extra}" if existing else extra
