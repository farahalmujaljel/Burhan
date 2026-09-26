import pytest

from app.embeddings.base import HashingEmbedder
from app.knowledge.graph_store.memory_store import MemoryGraphStore
from app.schemas.entities import EntityType
from app.schemas.graph import CLAIM_NODE_TYPES
from app.schemas.relations import EVIDENCE_REQUIRED, RelationType
from app.services.document_store import DocumentStore
from app.twin.evidence_index import EvidenceIndex
from app.twin.repository import TwinUpdateLog
from app.twin.service import TwinService
from tests.conftest import build_knowledge
from tests.fake_llm import sample_extraction_renamed
from tests.stores import memory_qdrant

PAPER_A = "paper_aaaaaaaaaaaa"
PAPER_B = "paper_bbbbbbbbbbbb"
# Paper B names the same concepts differently, as another author would.
RENAMES = {
    "ACL-ARC": "ACL ARC",
    "Graph attention network": "Graph Attention Networks",
    "macro F1": "macro-F1 (MF1)",
}


class Harness:
    """A TwinService over memory stores, with papers registered in a temp DocumentStore."""

    def __init__(self, tmp_path, graph=None):
        self.docs = DocumentStore(tmp_path / "uploads")
        self.graph = graph or MemoryGraphStore()
        self.index = EvidenceIndex(memory_qdrant, HashingEmbedder(128))
        self.twin = TwinService(
            self.docs, self.graph, self.index, TwinUpdateLog(), domain="Citation analysis"
        )

    def add_paper(self, paper_id, extraction=None):
        doc, knowledge = build_knowledge(paper_id, extraction)
        (self.docs.root / paper_id).mkdir(parents=True, exist_ok=True)
        from app.schemas.documents import PaperRecord, PaperStatus

        self.docs.save_record(
            PaperRecord(
                paper_id=paper_id,
                file_name=doc.file_name,
                sha256=paper_id,
                size_bytes=1,
                status=PaperStatus.PARSED,
            )
        )
        self.docs.save_document(doc)
        self.docs.save_knowledge(knowledge)
        return doc, knowledge


@pytest.fixture
def h(tmp_path):
    return Harness(tmp_path)


def assert_integrity(graph):
    """Every evidence ID on a node/edge resolves to stored Evidence from a supporting paper."""
    stored = {e.id: e for e in graph.all_evidence()}
    for item in [*graph.find_nodes(), *graph.find_edges()]:
        for eid in item.evidence_ids:
            assert eid in stored, f"{item.id} references missing evidence {eid}"
            assert stored[eid].paper_id in item.paper_ids, f"{item.id} has foreign evidence"


def node_named(graph, type_, name):
    return next(n for n in graph.find_nodes(types=[type_]) if n.name == name)


def test_first_paper_builds_graph_with_evidence(h):
    doc, k = h.add_paper(PAPER_A)
    update = h.twin.apply_paper(PAPER_A)

    assert update.operation == "apply"
    assert PAPER_A in update.added_entity_ids
    assert len(update.added_relation_ids) == len(h.graph.find_edges())
    assert update.resolutions == []  # nothing to merge into yet
    assert update.summary.startswith("Applied")

    # Every claim node and claim edge keeps evidence IDs that resolve to stored Evidence.
    stored = {e.id for e in h.graph.all_evidence()}
    for n in h.graph.find_nodes():
        assert set(n.evidence_ids) <= stored
        if n.type in CLAIM_NODE_TYPES:
            assert n.evidence_ids
    for e in h.graph.find_edges():
        assert set(e.evidence_ids) <= stored
        if e.type in EVIDENCE_REQUIRED:
            assert e.evidence_ids

    # Evidence and chunks were indexed with full provenance metadata.
    assert update.chunks_indexed == len(doc.chunks)
    assert update.evidence_indexed == len({e.id for e in k.all_evidence()})
    assert h.index.count() == update.chunks_indexed + update.evidence_indexed


def test_reapplying_same_paper_is_a_noop(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    counts, vectors = h.graph.counts(), h.index.count()

    again = h.twin.apply_paper(PAPER_A)
    assert again.is_noop
    assert "no changes" in again.summary
    assert h.graph.counts() == counts
    assert h.index.count() == vectors


def test_second_paper_merges_variants_and_strengthens_shared_entities(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    acl = node_named(h.graph, EntityType.DATASET, "ACL-ARC")

    h.add_paper(PAPER_B, sample_extraction_renamed(RENAMES))
    update = h.twin.apply_paper(PAPER_B)

    merged = {(r.original_name, r.canonical_name, r.method) for r in update.resolutions}
    assert ("ACL ARC", "ACL-ARC", "exact") in merged
    assert ("Graph Attention Networks", "Graph attention network", "normalized") in merged
    assert ("macro-F1 (MF1)", "macro F1", "acronym") in merged

    assert acl.id in update.strengthened_entity_ids
    shared = h.graph.get_nodes([acl.id])[acl.id]
    assert shared.paper_ids == sorted([PAPER_A, PAPER_B])
    assert "ACL ARC" in shared.aliases  # original names preserved
    assert len(h.graph.find_nodes(types=[EntityType.DATASET])) == 2  # ACL-ARC, SciCite
    assert PAPER_B in update.added_entity_ids
    assert_integrity(h.graph)

    summary = h.twin.summary()
    assert summary.paper_count == 2
    assert summary.top_datasets[0].paper_count == 2


def test_removing_a_paper_keeps_other_papers_support(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    counts_a, vectors_a = h.graph.counts(), h.index.count()
    h.add_paper(PAPER_B, sample_extraction_renamed(RENAMES))
    h.twin.apply_paper(PAPER_B)

    update = h.twin.remove_paper(PAPER_B)
    assert update.operation == "remove"
    assert PAPER_B in update.removed_entity_ids
    acl = node_named(h.graph, EntityType.DATASET, "ACL-ARC")
    assert acl.paper_ids == [PAPER_A]
    assert h.graph.counts()["nodes"] == counts_a["nodes"]
    assert h.graph.counts()["edges"] == counts_a["edges"]
    assert h.graph.evidence_ids_for_paper(PAPER_B) == set()
    assert h.index.count() == vectors_a
    assert_integrity(h.graph)


def test_reextraction_removes_claims_no_longer_supported(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    limitation = h.graph.find_nodes(types=[EntityType.LIMITATION])[0]

    # Re-extraction that no longer finds the limitation.
    doc, k = build_knowledge(PAPER_A)
    h.docs.save_knowledge(
        k.model_copy(
            update={
                "limitations": [],
                "relations": [r for r in k.relations if r.type != RelationType.STATES],
            }
        )
    )
    update = h.twin.apply_paper(PAPER_A)

    assert limitation.id in update.removed_entity_ids
    assert update.removed_relation_ids
    assert h.graph.find_nodes(types=[EntityType.LIMITATION]) == []
    assert_integrity(h.graph)
    assert h.graph.evidence_ids_for_paper(PAPER_A) == {
        e.id for e in h.docs.get_knowledge(PAPER_A).all_evidence()
    }


def test_reextracting_identical_content_keeps_node_ids(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    before = {n.id for n in h.graph.find_nodes()}

    _, fresh = build_knowledge(PAPER_A)  # same content, new random entity/evidence IDs
    h.docs.save_knowledge(fresh)
    update = h.twin.apply_paper(PAPER_A)

    assert update.added_entity_ids == [] and update.removed_entity_ids == []
    assert update.added_relation_ids == [] and update.removed_relation_ids == []
    assert update.changed_entity_ids  # evidence was replaced, so claims changed
    assert {n.id for n in h.graph.find_nodes()} == before
    assert_integrity(h.graph)


def test_reports_edges_remap_ids_to_canonical_nodes(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    [reports] = [e for e in h.graph.find_edges() if e.type == RelationType.REPORTS]
    nodes = h.graph.get_nodes([reports.properties["dataset_id"], reports.properties["method_id"]])
    assert {n.name for n in nodes.values()} == {"ACL-ARC", "Graph attention network"}
    assert reports.properties["value"] == "0.71"
    assert reports.evidence_ids


def test_snapshot_validates_and_node_detail_includes_evidence(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    snap = h.twin.snapshot()  # TwinSnapshot re-validates integrity on construction
    assert snap.domain == "Citation analysis"
    assert len(snap.entities) == h.graph.counts()["nodes"]
    assert len(snap.updates) == 1

    limitation = h.graph.find_nodes(types=[EntityType.LIMITATION])[0]
    detail = h.twin.node_detail(limitation.id)
    assert detail.evidence and detail.evidence[0].quote.startswith("Our study is limited")
    assert [n.id for n in detail.neighbors] == [PAPER_A]


def test_evidence_search_returns_traceable_hits(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    hits = h.twin.search("English-language computer science papers", kind="evidence")
    top = hits[0].payload
    assert top.kind == "evidence"
    assert top.paper_id == PAPER_A
    assert top.page == 3 and top.section == "4 Limitations"
    assert top.chunk_id and top.evidence_id and top.entity_id
    assert top.verification_status == "verified"


def test_search_collapses_records_sharing_a_quote(h):
    h.add_paper(PAPER_A)
    h.twin.apply_paper(PAPER_A)
    # The ACL-ARC and SciCite datasets share one quote, so it is indexed twice.
    hits = h.twin.search("ACL-ARC dataset and the SciCite dataset", kind="evidence", limit=5)
    spans = [(x.payload.char_start, x.payload.char_end) for x in hits]
    assert len(spans) == len(set(spans))
    assert hits[0].payload.text.startswith("We evaluate on the ACL-ARC dataset")


def test_twin_persists_across_restarts(tmp_path):
    path = tmp_path / "graph.json"
    first = Harness(tmp_path, MemoryGraphStore(path))
    first.add_paper(PAPER_A)
    first.twin.apply_paper(PAPER_A)
    reopened = MemoryGraphStore(path)
    assert reopened.counts() == first.graph.counts()
