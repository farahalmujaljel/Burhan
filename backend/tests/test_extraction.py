import json

import pytest

from app.llm.base import LLMOutputError
from app.schemas.evidence import VerificationStatus
from app.schemas.extraction import PaperKnowledge
from app.schemas.relations import RelationType
from app.services.extraction import (
    KnowledgeExtractor,
    _Candidate,
    build_windows,
    merge_candidates,
)
from tests.fake_llm import FakeLLM, sample_extraction, verdicts_by_claim


def extract(doc, llm=None, **kw) -> tuple[PaperKnowledge, FakeLLM]:
    llm = llm or FakeLLM()
    kw.setdefault("window_chars", 100_000)
    return KnowledgeExtractor(llm, max_attempts=2, **kw).extract(doc), llm


def test_extracts_grounded_knowledge_from_sample_paper(parsed_doc):
    k, llm = extract(parsed_doc)

    assert k.paper.id == parsed_doc.paper_id
    assert k.paper.abstract.startswith("We study citation intent classification")
    assert k.research_problem.text == "Assigning a purpose to each citation in a paper."
    assert [m.name for m in k.methods] == ["Graph attention network"]
    assert sorted(d.name for d in k.datasets) == ["ACL-ARC", "SciCite"]
    assert [m.name for m in k.metrics] == ["macro F1"]
    assert k.metrics[0].higher_is_better is True
    assert len(k.findings) == 1
    assert (
        k.limitations[0].name == "The study only covers English-language computer science papers."
    )
    assert k.future_work == []  # the hallucinated item was rejected
    assert k.meta.provider == "fake"
    assert k.meta.models == ["fake-model"]
    assert llm.extraction_calls == 1


def test_every_evidence_is_located_and_complete(parsed_doc):
    k, _ = extract(parsed_doc)
    chunks = {c.id: c for c in parsed_doc.chunks}
    evidence = k.all_evidence()
    assert evidence
    for ev in evidence:
        assert ev.paper_id == parsed_doc.paper_id
        assert parsed_doc.text[ev.span.char_start : ev.span.char_end] == ev.quote
        chunk = chunks[ev.chunk_id]
        assert chunk.char_start <= ev.span.char_start and ev.span.char_end <= chunk.char_end
        assert ev.span.page == parsed_doc.page_for_offset(ev.span.char_start)
        assert ev.section == chunk.section_title
        assert 0 < ev.confidence <= 1
        assert ev.extracted_by == "knowledge_extraction"
        assert ev.model == "fake-model"
        assert ev.verification_status == VerificationStatus.VERIFIED


def test_ungrounded_and_hallucinated_items_are_dropped_with_reasons(parsed_doc):
    k, _ = extract(parsed_doc)
    reasons = {d.text: d.reason for d in k.meta.dropped}
    assert reasons["The model is state of the art."] == "no evidence quote provided"
    assert "not found verbatim" in reasons["Extend the model to multilingual corpora."]
    assert k.meta.stats.items_dropped == len(k.meta.dropped)


def test_relations_link_paper_to_entities(parsed_doc):
    k, _ = extract(parsed_doc)
    by_type = {}
    for r in k.relations:
        by_type.setdefault(r.type, []).append(r)

    assert by_type[RelationType.USES][0].properties == {"role": "proposed"}
    assert len(by_type[RelationType.EVALUATES]) == 2
    assert len(by_type[RelationType.CLAIMS]) == 1
    assert len(by_type[RelationType.STATES]) == 1

    [reports] = by_type[RelationType.REPORTS]
    acl = next(d for d in k.datasets if d.name == "ACL-ARC")
    assert reports.properties["value"] == "0.71"
    assert reports.properties["dataset_id"] == acl.id
    assert reports.properties["method_id"] == k.methods[0].id
    assert reports.target_id == k.metrics[0].id
    assert reports.evidence  # REPORTS is a claim and carries its own evidence


def test_entity_mentions_verified_deterministically(parsed_doc):
    k, llm = extract(parsed_doc)
    method_ev = k.methods[0].evidence[0]
    assert "name appears in quote" in method_ev.verification_note
    # Only claims were sent to the LLM verifier, not dataset/metric/method mentions.
    sent = [
        json.loads(line)["kind"]
        for c in llm.calls[1:]
        for line in c[-1].content.splitlines()
        if line.startswith("{")
    ]
    assert set(sent) <= {"research_problem", "result", "finding", "limitation"}


def test_unsupported_claims_are_flagged_not_dropped(parsed_doc):
    llm = FakeLLM(
        verification=verdicts_by_claim(
            {"English-language": "not_supported", "Graph structure": "partially_supported"}
        )
    )
    k, _ = extract(parsed_doc, llm)
    lim_ev = k.limitations[0].evidence[0]
    assert lim_ev.verification_status == VerificationStatus.FLAGGED
    assert lim_ev.confidence <= 0.2
    assert lim_ev.verification_note.count("not_supported") == 1
    finding_ev = k.findings[0].evidence[0]
    assert finding_ev.verification_status == VerificationStatus.FLAGGED
    assert finding_ev.confidence <= 0.5
    assert k.meta.stats.evidence_flagged == 2


def test_verifier_failure_leaves_evidence_unverified(parsed_doc):
    llm = FakeLLM(verification=lambda _m: "definitely not json")
    k, _ = extract(parsed_doc, llm)
    lim_ev = k.limitations[0].evidence[0]
    assert lim_ev.verification_status == VerificationStatus.UNVERIFIED
    assert "semantic check unavailable" in lim_ev.verification_note
    assert any("Verification batch" in w for w in k.meta.warnings)
    assert k.meta.stats.evidence_unverified > 0


def test_malformed_extraction_output_is_retried(parsed_doc):
    replies = iter(["```json\n{broken", None])

    def flaky(messages):
        reply = next(replies)
        return reply if reply is not None else sample_extraction(messages)

    k, llm = extract(parsed_doc, FakeLLM(extraction=flaky))
    assert llm.extraction_calls == 2
    assert k.limitations
    assert k.meta.stats.llm_calls >= 2


def test_all_windows_failing_raises(parsed_doc):
    with pytest.raises(LLMOutputError, match="All"):
        extract(parsed_doc, FakeLLM(extraction=lambda _m: "garbage"))


def test_partial_window_failure_is_reported(parsed_doc):
    calls = {"n": 0}

    def first_fails(messages):
        calls["n"] += 1
        return "garbage" if calls["n"] <= 2 else sample_extraction(messages)

    k, _ = extract(parsed_doc, FakeLLM(extraction=first_fails), window_chars=1000)
    assert k.meta.stats.windows_total > 1
    assert k.meta.stats.windows_failed == 1
    assert any("window 1/" in w for w in k.meta.warnings)


def test_items_are_deduplicated_across_windows(parsed_doc):
    k, llm = extract(parsed_doc, window_chars=1000)
    assert llm.extraction_calls > 1
    # The hallucinated item is proposed by every window but dropped once, after merging.
    assert [d.text for d in k.meta.dropped].count("Extend the model to multilingual corpora.") == 1
    names = [d.name for d in k.datasets]
    assert len(names) == len(set(names))


def test_knowledge_roundtrips_through_json(parsed_doc):
    k, _ = extract(parsed_doc)
    assert PaperKnowledge.model_validate_json(k.model_dump_json()) == k


def test_build_windows_respects_budget(parsed_doc):
    windows = build_windows(parsed_doc.chunks, 700)
    assert [c for w in windows for c in w] == parsed_doc.chunks
    for w in windows:
        assert len(w) == 1 or sum(len(c.text) for c in w) <= 700


def test_merge_candidates_combines_evidence_and_attrs():
    a = _Candidate("method", "BERT-base", 0.6, "m", attrs={"role": None})
    b = _Candidate("method", "bert base", 0.9, "m", description="d", attrs={"role": "baseline"})
    [merged] = merge_candidates([a, b])
    assert merged.confidence == 0.9
    assert merged.description == "d"
    assert merged.attrs["role"] == "baseline"
