import pytest
from pydantic import TypeAdapter, ValidationError

from app.schemas import (
    Chunk,
    Contradiction,
    Entity,
    EntityType,
    Evidence,
    Finding,
    GapSignal,
    Limitation,
    Method,
    Paper,
    ParsedDocument,
    Relation,
    RelationType,
    ResearchGap,
    SourceSpan,
    TwinSnapshot,
)
from app.schemas.evidence import ConfidenceLevel

# --- Evidence -----------------------------------------------------------------


def test_evidence_defaults(make_evidence):
    ev = make_evidence(confidence=0.9)
    assert ev.id.startswith("ev_")
    assert ev.verification_status == "unverified"
    assert ev.confidence_level == ConfidenceLevel.HIGH


@pytest.mark.parametrize(
    "kwargs",
    [
        {"quote": "   "},
        {"confidence": 1.5},
        {"paper_id": ""},
    ],
)
def test_evidence_rejects_invalid(make_evidence, kwargs):
    with pytest.raises(ValidationError):
        make_evidence(**kwargs)


def test_evidence_rejects_unknown_fields(make_evidence):
    with pytest.raises(ValidationError):
        make_evidence(hallucinated_field="x")


@pytest.mark.parametrize(
    "span",
    [{"char_start": 10}, {"char_start": 10, "char_end": 10}, {"page": 0}],
)
def test_source_span_rejects_bad_offsets(span):
    with pytest.raises(ValidationError):
        SourceSpan(**span)


# --- Entities -----------------------------------------------------------------


def test_claims_require_evidence():
    with pytest.raises(ValidationError):
        Finding(name="Unsupported claim", paper_id="paper_a", evidence=[])
    with pytest.raises(ValidationError):
        Limitation(name="Unsupported limitation", paper_id="paper_a")


def test_claim_evidence_must_come_from_same_paper(make_evidence):
    with pytest.raises(ValidationError, match="must come from paper"):
        Finding(name="x", paper_id="paper_a", evidence=[make_evidence(paper_id="paper_b")])


def test_research_gap_requires_signals_and_evidence(make_evidence):
    with pytest.raises(ValidationError):
        ResearchGap(name="gap", rationale="r", signals=[], supporting_entity_ids=["l1"])
    gap = ResearchGap(
        name="No evaluation on low-resource languages",
        rationale="Two papers list this as a limitation.",
        signals=[GapSignal.REPEATED_LIMITATION],
        supporting_entity_ids=["lim_1", "lim_2"],
        evidence=[make_evidence("paper_a"), make_evidence("paper_b")],
    )
    assert gap.paper_ids == ["paper_a", "paper_b"]


def test_entity_union_discriminates_by_type(finding):
    adapter = TypeAdapter(Entity)
    parsed = adapter.validate_json(finding.model_dump_json())
    assert isinstance(parsed, Finding)
    assert parsed.type == EntityType.FINDING


# --- Relations ----------------------------------------------------------------


def test_relation_valid_structural():
    rel = Relation(
        type=RelationType.USES,
        source_id="paper_a",
        source_type=EntityType.PAPER,
        target_id="method_x",
        target_type=EntityType.METHOD,
    )
    assert rel.evidence == []


def test_relation_rejects_wrong_endpoint_types():
    with pytest.raises(ValidationError, match="not allowed"):
        Relation(
            type=RelationType.USES,
            source_id="method_x",
            source_type=EntityType.METHOD,
            target_id="paper_a",
            target_type=EntityType.PAPER,
        )


def test_claim_relations_require_evidence(make_evidence):
    kwargs = dict(
        type=RelationType.IMPROVES,
        source_id="m1",
        source_type=EntityType.METHOD,
        target_id="m2",
        target_type=EntityType.METHOD,
    )
    with pytest.raises(ValidationError, match="require evidence"):
        Relation(**kwargs)
    assert Relation(**kwargs, evidence=[make_evidence()]).type == RelationType.IMPROVES


def test_relation_rejects_self_reference(make_evidence):
    with pytest.raises(ValidationError, match="self-referencing"):
        Relation(
            type=RelationType.COMPARES,
            source_id="m1",
            source_type=EntityType.METHOD,
            target_id="m1",
            target_type=EntityType.METHOD,
            evidence=[make_evidence()],
        )


# --- Parsed documents ---------------------------------------------------------

TEXT = "Abstract\n  We propose X.\n\nResults\nX beats Y."


def test_parsed_document_preserves_whitespace_and_offsets():
    chunk_text = TEXT[9:25]
    doc = ParsedDocument(
        paper_id="paper_a",
        file_name="a.pdf",
        parser="pymupdf",
        page_count=1,
        text=TEXT,
        chunks=[Chunk(paper_id="paper_a", text=chunk_text, char_start=9, char_end=25)],
    )
    assert doc.text == TEXT
    assert doc.chunks[0].text == chunk_text  # leading spaces preserved


def test_parsed_document_rejects_misaligned_chunk():
    with pytest.raises(ValidationError, match="does not match"):
        ParsedDocument(
            paper_id="paper_a",
            file_name="a.pdf",
            parser="pymupdf",
            page_count=1,
            text=TEXT,
            chunks=[Chunk(paper_id="paper_a", text="Wrong text", char_start=0, char_end=10)],
        )


# --- Twin snapshot ------------------------------------------------------------


def _uses(paper_id: str, method_id: str) -> Relation:
    return Relation(
        type=RelationType.USES,
        source_id=paper_id,
        source_type=EntityType.PAPER,
        target_id=method_id,
        target_type=EntityType.METHOD,
    )


def test_twin_snapshot_roundtrip(paper, method, finding):
    snap = TwinSnapshot(
        domain="neural machine translation",
        entities=[paper, method, finding],
        relations=[_uses(paper.id, method.id)],
    )
    restored = TwinSnapshot.model_validate_json(snap.model_dump_json())
    assert restored == snap
    assert len(restored.all_evidence()) == 1


def test_twin_snapshot_rejects_dangling_relation(paper):
    with pytest.raises(ValidationError, match="unknown"):
        TwinSnapshot(domain="d", entities=[paper], relations=[_uses(paper.id, "method_missing")])


def test_twin_snapshot_rejects_evidence_from_unknown_paper(method, finding):
    with pytest.raises(ValidationError, match="unknown paper"):
        TwinSnapshot(domain="d", entities=[method, finding])  # paper_a missing


def test_twin_snapshot_rejects_duplicate_ids(paper):
    with pytest.raises(ValidationError, match="duplicate"):
        TwinSnapshot(domain="d", entities=[paper, Paper(id=paper.id, name="dup")])


def test_contradiction_needs_two_distinct_findings(make_evidence):
    evs = [make_evidence(), make_evidence()]
    with pytest.raises(ValidationError):
        Contradiction(finding_a_id="f1", finding_b_id="f1", explanation="x", evidence=evs)
    with pytest.raises(ValidationError):
        Contradiction(finding_a_id="f1", finding_b_id="f2", explanation="x", evidence=evs[:1])


def test_evidence_json_schema_is_exportable():
    # The LLM layer will use these JSON schemas for structured output.
    for model in (Evidence, Finding, Method, Relation):
        assert model.model_json_schema()["type"] == "object"
