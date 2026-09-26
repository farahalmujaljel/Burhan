"""Scientific extraction: ParsedDocument -> drafts -> grounding -> verification -> PaperKnowledge.

Pipeline for one paper:
  1. Window: group consecutive chunks into LLM-sized windows (chunk IDs stay visible to the LLM).
  2. Extract: one schema-constrained LLM call per window -> DraftExtraction.
  3. Merge: deduplicate items across windows by normalized name/statement.
  4. Ground: locate every quote in the parsed text (deterministic); items without a located
     quote are dropped and recorded in `meta.dropped`.
  5. Verify: LLM judges whether each located quote supports its claim.
  6. Build: convert to strict entity/relation schemas and validate as `PaperKnowledge`.
"""

import logging
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime

from pydantic import ValidationError

from app.core.errors import BurhanError, ConflictError
from app.llm.base import ChatMessage, LLMClient, LLMOutputError
from app.llm.prompts import PROMPT_VERSION, render_prompt
from app.llm.structured import generate_structured
from app.schemas.documents import (
    Chunk,
    ExtractionStatus,
    PaperRecord,
    PaperStatus,
    ParsedDocument,
    SectionKind,
)
from app.schemas.entities import (
    Dataset,
    Finding,
    FutureWork,
    Limitation,
    Method,
    Metric,
    Paper,
)
from app.schemas.evidence import Evidence, SourceSpan, VerificationStatus
from app.schemas.extraction import (
    DraftExtraction,
    DraftQuote,
    DroppedItem,
    ExtractionMeta,
    ExtractionStats,
    PaperKnowledge,
    ResearchStatement,
)
from app.schemas.relations import Relation, RelationType
from app.services.document_store import DocumentStore
from app.services.quote_locator import QuoteLocator, normalize_with_map
from app.services.verification import ClaimCheck, EvidenceVerifier, apply_verdict

logger = logging.getLogger(__name__)

EXTRACTOR = "knowledge_extraction"
MAX_EVIDENCE_PER_ITEM = 3
MAX_ABSTRACT_CHARS = 3000

ENTITY_KINDS = ("method", "dataset", "metric")


def normalize_key(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


@dataclass
class _Candidate:
    kind: str
    text: str  # entity name or claim statement
    confidence: float
    model: str
    quotes: list[DraftQuote] = field(default_factory=list)
    description: str | None = None
    attrs: dict = field(default_factory=dict)
    evidence: list[Evidence] = field(default_factory=list)

    @property
    def key(self) -> str:
        return normalize_key(self.text)


@dataclass
class _Run:
    """Mutable bookkeeping for one extraction run."""

    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    models: set[str] = field(default_factory=set)
    stats: ExtractionStats = field(default_factory=ExtractionStats)
    dropped: list[DroppedItem] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def drop(self, cand: _Candidate, reason: str) -> None:
        self.dropped.append(DroppedItem(kind=cand.kind, text=cand.text, reason=reason))


def build_windows(chunks: list[Chunk], max_chars: int) -> list[list[Chunk]]:
    windows: list[list[Chunk]] = []
    current: list[Chunk] = []
    size = 0
    for chunk in chunks:
        if current and size + len(chunk.text) > max_chars:
            windows.append(current)
            current, size = [], 0
        current.append(chunk)
        size += len(chunk.text)
    if current:
        windows.append(current)
    return windows


def _render_passages(chunks: list[Chunk]) -> str:
    return "\n\n".join(
        f"[chunk_id={c.id} | section={c.section_title or 'unknown'} | "
        f"pages={c.page}-{c.page_end}]\n{c.text}"
        for c in chunks
    )


def _draft_to_candidates(draft: DraftExtraction, model: str) -> list[_Candidate]:
    out: list[_Candidate] = []

    def stmt(kind: str, s) -> None:
        out.append(_Candidate(kind, s.text, s.confidence, model, list(s.evidence)))

    if draft.research_problem:
        stmt("research_problem", draft.research_problem)
    for s in draft.research_questions:
        stmt("research_question", s)
    for s in draft.findings:
        stmt("finding", s)
    for s in draft.limitations:
        stmt("limitation", s)
    for s in draft.future_work:
        stmt("future_work", s)
    for m in draft.methods:
        out.append(
            _Candidate(
                "method",
                m.name,
                m.confidence,
                model,
                list(m.evidence),
                m.description,
                {"role": m.role},
            )
        )
    for d in draft.datasets:
        out.append(
            _Candidate("dataset", d.name, d.confidence, model, list(d.evidence), d.description)
        )
    for m in draft.metrics:
        out.append(
            _Candidate(
                "metric",
                m.name,
                m.confidence,
                model,
                list(m.evidence),
                m.description,
                {"higher_is_better": m.higher_is_better},
            )
        )
    for r in draft.results:
        value = None if r.value is None else str(r.value)
        label = " ".join(p for p in (r.method, r.metric, value, r.dataset) if p)
        out.append(
            _Candidate(
                "result",
                label,
                r.confidence,
                model,
                list(r.evidence),
                None,
                {"metric": r.metric, "value": value, "method": r.method, "dataset": r.dataset},
            )
        )
    return out


def merge_candidates(candidates: list[_Candidate]) -> list[_Candidate]:
    """Deduplicate across windows: same kind + normalized text -> one item, evidence combined."""
    merged: dict[tuple[str, str], _Candidate] = {}
    for c in candidates:
        if not c.key:
            continue
        existing = merged.get((c.kind, c.key))
        if existing is None:
            merged[(c.kind, c.key)] = c
            continue
        existing.quotes.extend(c.quotes)
        existing.confidence = max(existing.confidence, c.confidence)
        existing.description = existing.description or c.description
        for k, v in c.attrs.items():
            if existing.attrs.get(k) is None:
                existing.attrs[k] = v
    return list(merged.values())


def _abstract(doc: ParsedDocument) -> str | None:
    section = next((s for s in doc.sections if s.kind == SectionKind.ABSTRACT), None)
    if not section:
        return None
    body = doc.text[section.char_start : section.char_end]
    body = re.sub(r"^\s*abstract\s*[—–:.\-]?\s*", "", body, flags=re.IGNORECASE)
    return " ".join(body.split())[:MAX_ABSTRACT_CHARS] or None


class KnowledgeExtractor:
    """Pure pipeline over one ParsedDocument (no storage, no status bookkeeping)."""

    def __init__(
        self,
        llm: LLMClient,
        *,
        window_chars: int = 12000,
        verification_batch_size: int = 12,
        max_attempts: int = 3,
        max_output_tokens: int = 4096,
    ) -> None:
        self.llm = llm
        self.window_chars = window_chars
        self.max_attempts = max_attempts
        self.max_output_tokens = max_output_tokens
        self.verifier = EvidenceVerifier(
            llm, batch_size=verification_batch_size, max_attempts=max_attempts
        )

    def extract(self, doc: ParsedDocument) -> PaperKnowledge:
        run = _Run()
        candidates = self._extract_candidates(doc, run)
        run.stats.items_proposed = len(candidates)

        grounded = self._ground(doc, merge_candidates(candidates), run)
        self._verify(grounded, run)
        knowledge = self._build(doc, grounded, run)
        return knowledge

    # 1-3. windowed LLM extraction ----------------------------------------------

    def _extract_candidates(self, doc: ParsedDocument, run: _Run) -> list[_Candidate]:
        windows = build_windows(doc.chunks, self.window_chars)
        run.stats.windows_total = len(windows)
        system = render_prompt("extraction_system")
        candidates: list[_Candidate] = []

        for i, window in enumerate(windows, start=1):
            user = render_prompt(
                "extraction_user",
                title=doc.title or doc.file_name,
                window_label=f"{i} of {len(windows)}",
                passages=_render_passages(window),
            )
            try:
                result = generate_structured(
                    self.llm,
                    [ChatMessage("system", system), ChatMessage("user", user)],
                    DraftExtraction,
                    max_attempts=self.max_attempts,
                    max_tokens=self.max_output_tokens,
                )
            except BurhanError as exc:
                run.stats.windows_failed += 1
                run.stats.llm_calls += self.max_attempts
                run.warnings.append(f"Extraction window {i}/{len(windows)} failed: {exc}")
                logger.warning("Extraction window %d failed for %s: %s", i, doc.paper_id, exc)
                continue
            run.stats.llm_calls += result.attempts
            run.models.add(result.model)
            candidates.extend(_draft_to_candidates(result.value, result.model))

        if windows and run.stats.windows_failed == len(windows):
            raise LLMOutputError(f"All {len(windows)} extraction calls failed; see server logs")
        return candidates

    # 4. deterministic grounding -------------------------------------------------

    def _ground(self, doc: ParsedDocument, cands: list[_Candidate], run: _Run) -> list[_Candidate]:
        locator = QuoteLocator(doc)
        kept: list[_Candidate] = []
        for cand in cands:
            if not cand.quotes:
                run.drop(cand, "no evidence quote provided")
                continue
            seen: set[tuple[int, int]] = set()
            for q in cand.quotes:
                match = locator.locate(q.quote, q.chunk_id)
                if match is None or (match.char_start, match.char_end) in seen:
                    continue
                seen.add((match.char_start, match.char_end))
                cand.evidence.append(
                    Evidence(
                        paper_id=doc.paper_id,
                        quote=match.text,
                        section=match.section,
                        chunk_id=match.chunk_id,
                        span=SourceSpan(
                            page=match.page, char_start=match.char_start, char_end=match.char_end
                        ),
                        extracted_by=EXTRACTOR,
                        model=cand.model,
                        confidence=round(cand.confidence * match.score / 100, 3),
                        verification_note=f"quote located in source ({match.method}"
                        + (f", score {match.score}" if match.method == "fuzzy" else "")
                        + ")",
                    )
                )
                if len(cand.evidence) >= MAX_EVIDENCE_PER_ITEM:
                    break
            if cand.evidence:
                kept.append(cand)
            else:
                run.drop(cand, "evidence quote not found verbatim in the paper")
        return kept

    # 5. semantic verification ---------------------------------------------------

    def _verify(self, cands: list[_Candidate], run: _Run) -> None:
        checks: list[ClaimCheck] = []
        by_id: dict[str, Evidence] = {}
        for cand in cands:
            for ev in cand.evidence:
                if cand.kind in ENTITY_KINDS and self._name_in_quote(cand.text, ev.quote):
                    ev.verification_status = VerificationStatus.VERIFIED
                    ev.verification_note += f"; {cand.kind} name appears in quote"
                    continue
                checks.append(ClaimCheck(ev.id, cand.kind, self._claim_text(cand), ev.quote))
                by_id[ev.id] = ev

        if not checks:
            return
        outcome = self.verifier.verify(checks)
        run.stats.llm_calls += outcome.llm_calls
        run.models |= outcome.models
        run.warnings.extend(outcome.warnings)
        model = next(iter(outcome.models), None)
        for ev_id, ev in by_id.items():
            apply_verdict(ev, outcome.verdicts.get(ev_id), model)

    @staticmethod
    def _name_in_quote(name: str, quote: str) -> bool:
        norm_name = normalize_with_map(name)[0]
        return len(norm_name) >= 2 and norm_name in normalize_with_map(quote)[0]

    @staticmethod
    def _claim_text(cand: _Candidate) -> str:
        a = cand.attrs
        match cand.kind:
            case "result":
                claim = f"{a.get('method') or 'The evaluated method'} achieves {a['metric']}"
                claim += f" of {a['value']}" if a.get("value") else ""
                claim += f" on {a['dataset']}" if a.get("dataset") else ""
                return claim
            case "method":
                return f"The paper proposes or uses the method '{cand.text}'."
            case "dataset":
                return f"The paper uses the dataset '{cand.text}'."
            case "metric":
                return f"The paper reports results using the metric '{cand.text}'."
            case _:
                return cand.text

    # 6. build validated PaperKnowledge -----------------------------------------

    def _build(self, doc: ParsedDocument, cands: list[_Candidate], run: _Run) -> PaperKnowledge:
        paper = Paper(
            id=doc.paper_id,
            name=doc.title or doc.file_name,
            file_name=doc.file_name,
            abstract=_abstract(doc),
        )
        kinds: dict[str, list[_Candidate]] = {}
        for c in cands:
            kinds.setdefault(c.kind, []).append(c)

        out: dict[str, list] = {
            k: []
            for k in (
                "methods",
                "datasets",
                "metrics",
                "findings",
                "limitations",
                "future_work",
                "relations",
                "research_questions",
            )
        }
        ids: dict[tuple[str, str], str] = {}

        def rel(rtype, src, tgt, evidence=(), **props) -> None:
            try:
                out["relations"].append(
                    Relation(
                        type=rtype,
                        source_id=src.id,
                        source_type=src.type,
                        target_id=tgt.id,
                        target_type=tgt.type,
                        properties={k: v for k, v in props.items() if v is not None},
                        evidence=list(evidence),
                        confidence=max((e.confidence for e in evidence), default=0.5),
                    )
                )
            except ValidationError as exc:
                run.warnings.append(f"Skipped {rtype} relation: {exc.errors()[0]['msg']}")

        def make(cand: _Candidate, factory, **kw):
            try:
                return factory(
                    name=cand.text, description=cand.description, evidence=cand.evidence, **kw
                )
            except ValidationError as exc:
                run.drop(cand, f"schema validation failed: {exc.errors()[0]['msg']}")
                return None

        entity_specs = [
            ("method", "methods", Method, RelationType.USES, lambda c: {}),
            ("dataset", "datasets", Dataset, RelationType.EVALUATES, lambda c: {}),
            (
                "metric",
                "metrics",
                Metric,
                None,
                lambda c: {"higher_is_better": c.attrs.get("higher_is_better")},
            ),
        ]
        for kind, bucket, factory, rtype, extra in entity_specs:
            for cand in kinds.get(kind, []):
                entity = make(cand, factory, **extra(cand))
                if entity:
                    out[bucket].append(entity)
                    ids[(kind, cand.key)] = entity.id
                    if rtype:
                        rel(rtype, paper, entity, role=cand.attrs.get("role"))

        claim_specs = [
            ("finding", "findings", Finding, RelationType.CLAIMS),
            ("limitation", "limitations", Limitation, RelationType.STATES),
            ("future_work", "future_work", FutureWork, RelationType.STATES),
        ]
        for kind, bucket, factory, rtype in claim_specs:
            for cand in kinds.get(kind, []):
                entity = make(cand, factory, paper_id=paper.id)
                if entity:
                    out[bucket].append(entity)
                    rel(rtype, paper, entity)

        for cand in kinds.get("result", []):
            self._build_result(cand, paper, out, ids, rel)

        problems = sorted(kinds.get("research_problem", []), key=lambda c: -c.confidence)
        for extra_problem in problems[1:]:
            run.drop(extra_problem, "additional research problem (kept highest-confidence one)")
        research_problem = (
            ResearchStatement(text=problems[0].text, evidence=problems[0].evidence)
            if problems
            else None
        )
        questions = [
            ResearchStatement(text=c.text, evidence=c.evidence)
            for c in kinds.get("research_question", [])
        ]

        knowledge = PaperKnowledge(
            paper=paper,
            research_problem=research_problem,
            research_questions=questions,
            methods=out["methods"],
            datasets=out["datasets"],
            metrics=out["metrics"],
            findings=out["findings"],
            limitations=out["limitations"],
            future_work=out["future_work"],
            relations=out["relations"],
            meta=ExtractionMeta(
                provider=self.llm.provider,
                prompt_version=PROMPT_VERSION,
                started_at=run.started_at,
            ),
        )
        return self._finalize(knowledge, run)

    @staticmethod
    def _build_result(cand, paper, out, ids, rel) -> None:
        a = cand.attrs
        metric_id = ids.get(("metric", normalize_key(a["metric"])))
        metric = next((m for m in out["metrics"] if m.id == metric_id), None)
        if metric is None:
            # The result names a metric the metric list missed; ground it on the result quote.
            metric = Metric(name=a["metric"], evidence=cand.evidence)
            out["metrics"].append(metric)
            ids[("metric", normalize_key(a["metric"]))] = metric.id
        method_id = ids.get(("method", normalize_key(a["method"]))) if a.get("method") else None
        dataset_id = ids.get(("dataset", normalize_key(a["dataset"]))) if a.get("dataset") else None
        rel(
            RelationType.REPORTS,
            paper,
            metric,
            cand.evidence,
            value=a.get("value"),
            method=a.get("method"),
            method_id=method_id,
            dataset=a.get("dataset"),
            dataset_id=dataset_id,
        )

    @staticmethod
    def _finalize(knowledge: PaperKnowledge, run: _Run) -> PaperKnowledge:
        unique = {ev.id: ev for ev in knowledge.all_evidence()}.values()
        stats = run.stats
        stats.items_dropped = len(run.dropped)
        stats.items_kept = (
            len(knowledge.entities())
            - 1
            + len(knowledge.research_questions)
            + (1 if knowledge.research_problem else 0)
            + sum(1 for r in knowledge.relations if r.type == RelationType.REPORTS)
        )
        stats.evidence_verified = sum(
            e.verification_status == VerificationStatus.VERIFIED for e in unique
        )
        stats.evidence_flagged = sum(
            e.verification_status == VerificationStatus.FLAGGED for e in unique
        )
        stats.evidence_unverified = sum(
            e.verification_status == VerificationStatus.UNVERIFIED for e in unique
        )
        knowledge.meta = knowledge.meta.model_copy(
            update={
                "models": sorted(run.models),
                "stats": stats,
                "dropped": run.dropped,
                "warnings": run.warnings,
                "finished_at": datetime.now(UTC),
            }
        )
        # Re-validate the complete object so provenance invariants are enforced on what we store.
        return PaperKnowledge.model_validate(knowledge.model_dump())


class ExtractionService:
    """Runs extraction for stored papers and tracks status on the PaperRecord."""

    def __init__(
        self,
        store: DocumentStore,
        llm_factory: Callable[[], LLMClient],
        *,
        window_chars: int,
        verification_batch_size: int,
        max_attempts: int,
        max_output_tokens: int,
        on_completed: Callable[[str], None] | None = None,
    ) -> None:
        self.store = store
        self._llm_factory = llm_factory
        self.on_completed = on_completed  # e.g. update the Research Digital Twin
        self._llm: LLMClient | None = None
        self.options = dict(
            window_chars=window_chars,
            verification_batch_size=verification_batch_size,
            max_attempts=max_attempts,
            max_output_tokens=max_output_tokens,
        )

    @property
    def llm(self) -> LLMClient:
        if self._llm is None:
            self._llm = self._llm_factory()  # raises LLMNotConfiguredError without an API key
        return self._llm

    def start(self, paper_id: str) -> PaperRecord:
        """Validate the paper can be extracted and mark it running."""
        record = self.store.get_record(paper_id)
        if record.status != PaperStatus.PARSED:
            raise ConflictError(
                f"Paper '{paper_id}' must be parsed before extraction (status: {record.status})"
            )
        if record.extraction_status == ExtractionStatus.RUNNING:
            raise ConflictError(f"Extraction for '{paper_id}' is already running")
        _ = self.llm  # fail fast if the LLM is not configured
        record = record.model_copy(
            update={"extraction_status": ExtractionStatus.RUNNING, "extraction_error": None}
        )
        self.store.save_record(record)
        return record

    def run(self, paper_id: str) -> PaperRecord:
        """Execute extraction for a paper already marked running. Never raises."""
        try:
            doc = self.store.get_document(paper_id)
            knowledge = KnowledgeExtractor(self.llm, **self.options).extract(doc)
            self.store.save_knowledge(knowledge)
            update = {
                "extraction_status": ExtractionStatus.COMPLETED,
                "extraction_error": None,
                "extracted_at": datetime.now(UTC),
            }
        except Exception as exc:  # background task: record every failure on the paper
            logger.exception("Extraction failed for %s", paper_id)
            message = exc.message if isinstance(exc, BurhanError) else f"Unexpected error: {exc}"
            update = {"extraction_status": ExtractionStatus.FAILED, "extraction_error": message}
        record = self.store.get_record(paper_id).model_copy(update=update)
        self.store.save_record(record)
        if self.on_completed and record.extraction_status == ExtractionStatus.COMPLETED:
            self.on_completed(paper_id)  # must not raise (see TwinService.apply_paper_safely)
            record = self.store.get_record(paper_id)
        return record
