import os

import pytest
from pydantic import ValidationError

from app.core.errors import ProviderError
from app.embeddings.base import HashingEmbedder
from app.embeddings.local import FastEmbedEmbedder
from app.knowledge.graph_store.memory_store import MemoryGraphStore
from app.knowledge.graph_store.neo4j_store import _label, _rel_type
from app.knowledge.vector_store.base import VectorPayload, VectorRecord
from app.knowledge.vector_store.qdrant_store import QdrantStore
from app.schemas.entities import EntityType
from app.schemas.evidence import Evidence, SourceSpan
from app.schemas.graph import GraphEdge, GraphNode
from app.schemas.relations import RelationType


def _stores():
    stores = [pytest.param("memory", id="memory")]
    # Run the same contract against a real Neo4j when one is available, e.g.
    # NEO4J_TEST_URI=bolt://localhost:7687 NEO4J_TEST_PASSWORD=... pytest
    stores.append(
        pytest.param(
            "neo4j",
            id="neo4j",
            marks=pytest.mark.skipif(not os.getenv("NEO4J_TEST_URI"), reason="no Neo4j"),
        )
    )
    return stores


@pytest.fixture(params=_stores())
def graph(request):
    if request.param == "memory":
        yield MemoryGraphStore()
        return
    from app.knowledge.graph_store.neo4j_store import Neo4jGraphStore

    store = Neo4jGraphStore(
        os.environ["NEO4J_TEST_URI"], "neo4j", os.environ.get("NEO4J_TEST_PASSWORD", "")
    )
    store._run("MATCH (n) DETACH DELETE n")
    yield store
    store._run("MATCH (n) DETACH DELETE n")
    store.close()


def ev(eid="ev_1", paper="paper_a"):
    return Evidence(
        id=eid,
        paper_id=paper,
        quote="We use the Transformer.",
        section="Methods",
        chunk_id="chunk_1",
        span=SourceSpan(page=2, char_start=10, char_end=33),
        extracted_by="knowledge_extraction",
        confidence=0.9,
    )


def node(nid, type_=EntityType.METHOD, **kw):
    return GraphNode(id=nid, type=type_, name=kw.pop("name", nid), **kw)


# --- graph store contract -----------------------------------------------------


def test_graph_store_roundtrip(graph):
    paper = node("paper_a", EntityType.PAPER, paper_ids=["paper_a"], properties={"year": 2017})
    method = node("method_x", aliases=["X-net"], paper_ids=["paper_a"], evidence_ids=["ev_1"])
    graph.upsert_nodes([paper, method])
    edge = GraphEdge(
        id="rel_1",
        type=RelationType.USES,
        source_id="paper_a",
        source_type=EntityType.PAPER,
        target_id="method_x",
        target_type=EntityType.METHOD,
        paper_ids=["paper_a"],
        properties={"role": "proposed"},
    )
    graph.upsert_edges([edge])
    graph.upsert_evidence([ev()])

    assert graph.get_nodes(["method_x"])["method_x"] == method
    assert graph.find_nodes(types=[EntityType.PAPER]) == [paper]
    assert {n.id for n in graph.find_nodes(paper_id="paper_a")} == {"paper_a", "method_x"}
    assert graph.find_edges(paper_id="paper_a") == [edge]
    assert graph.find_edges(node_ids=["method_x"]) == [edge]
    assert graph.get_evidence(["ev_1"]) == [ev()]
    assert graph.evidence_ids_for_paper("paper_a") == {"ev_1"}
    assert graph.counts() == {"nodes": 2, "edges": 1, "evidence": 1}


def test_graph_store_upsert_replaces_and_delete_cascades(graph):
    graph.upsert_nodes([node("a", EntityType.PAPER), node("m")])
    graph.upsert_nodes([node("m", aliases=["M2"])])  # replace, not merge
    assert graph.get_nodes(["m"])["m"].aliases == ["M2"]
    graph.upsert_edges(
        [
            GraphEdge(
                id="r",
                type=RelationType.USES,
                source_id="a",
                source_type=EntityType.PAPER,
                target_id="m",
                target_type=EntityType.METHOD,
            )
        ]
    )
    graph.delete_nodes(["m"])
    assert graph.find_edges() == []
    graph.upsert_evidence([ev("e1"), ev("e2", paper="paper_b")])
    graph.delete_evidence_for_paper("paper_a")
    assert [e.id for e in graph.get_evidence(["e1", "e2"])] == ["e2"]


def test_memory_store_rejects_edges_to_unknown_nodes():
    g = MemoryGraphStore()
    g.upsert_nodes([node("a", EntityType.PAPER)])
    with pytest.raises(ValueError, match="unknown nodes"):
        g.upsert_edges(
            [
                GraphEdge(
                    id="r",
                    type=RelationType.USES,
                    source_id="a",
                    source_type=EntityType.PAPER,
                    target_id="missing",
                    target_type=EntityType.METHOD,
                )
            ]
        )


def test_memory_store_persists_to_json(tmp_path):
    path = tmp_path / "graph.json"
    g = MemoryGraphStore(path)
    g.upsert_nodes([node("m", paper_ids=["p"], properties={"higher_is_better": True})])
    g.upsert_evidence([ev()])
    reopened = MemoryGraphStore(path)
    assert reopened.get_nodes(["m"]) == g.get_nodes(["m"])
    assert reopened.get_evidence(["ev_1"]) == [ev()]


def test_graph_records_enforce_evidence_for_claims():
    with pytest.raises(ValidationError, match="must reference evidence"):
        GraphNode(id="f", type=EntityType.FINDING, name="A claim", paper_ids=["p"])
    with pytest.raises(ValidationError, match="must reference evidence"):
        GraphEdge(
            id="r",
            type=RelationType.REPORTS,
            source_id="p",
            source_type=EntityType.PAPER,
            target_id="m",
            target_type=EntityType.METRIC,
        )


def test_neo4j_labels_only_come_from_enums():
    assert _label(EntityType.METHOD) == "Method"
    assert _rel_type("USES") == "USES"
    with pytest.raises(ValueError):
        _label("Method`) DETACH DELETE (n")
    with pytest.raises(ValueError):
        _rel_type("USES]->() DELETE r//")


# --- vector store -------------------------------------------------------------


EMBEDDER = HashingEmbedder(64)


def rec(rid, text, paper="paper_a", kind="chunk", embedder=EMBEDDER):
    return VectorRecord(
        id=rid,
        vector=embedder.embed_query(text),
        payload=VectorPayload(kind=kind, paper_id=paper, text=text, page=1, section="Intro"),
    )


def test_qdrant_upsert_search_filter_delete():
    store = QdrantStore("t", location=":memory:")
    emb = HashingEmbedder(64)
    store.upsert(
        [
            rec("c1", "graph neural networks for citations"),
            rec("c2", "image segmentation with convolutions"),
            rec("e1", "graph neural networks improve accuracy", kind="evidence"),
            rec("c3", "graph neural networks for citations", paper="paper_b"),
        ]
    )
    assert store.count() == 4
    hits = store.search(emb.embed_query("graph neural networks"), limit=2, paper_id="paper_a")
    assert all(h.payload.paper_id == "paper_a" for h in hits)
    assert hits[0].payload.text.startswith("graph neural networks")
    assert [h.payload.kind for h in store.search(emb.embed_query("graph"), kind="evidence")] == [
        "evidence"
    ]

    store.upsert([rec("c1", "graph neural networks for citations")])  # same ID: no duplicate
    assert store.count(paper_id="paper_a") == 3
    store.delete_paper("paper_a")
    assert store.count() == 1


def test_qdrant_rejects_dimension_mismatch():
    store = QdrantStore("t", location=":memory:")
    store.ensure_collection(64)
    store._dim = None  # simulate a restart with a different embedding model
    with pytest.raises(ProviderError, match="dimension"):
        store.ensure_collection(128)


def test_qdrant_local_mode_persists(tmp_path):
    store = QdrantStore("t", path=str(tmp_path / "q"))
    store.upsert([rec("c1", "hello world")])
    store.close()
    reopened = QdrantStore("t", path=str(tmp_path / "q"))
    assert reopened.count() == 1
    reopened.close()


def test_search_on_empty_store_returns_nothing():
    store = QdrantStore("t", location=":memory:")
    assert store.search([0.1] * 8) == []
    assert store.count() == 0


# --- embedders ----------------------------------------------------------------


def test_hashing_embedder_is_deterministic_and_normalized():
    emb = HashingEmbedder(128)
    a, b = emb.embed_documents(["graph neural network", "graph neural network"])
    assert a == b
    assert abs(sum(x * x for x in a) - 1.0) < 1e-9
    similar = sum(x * y for x, y in zip(a, emb.embed_query("neural graph"), strict=True))
    unrelated = sum(x * y for x, y in zip(a, emb.embed_query("protein folding"), strict=True))
    assert similar > unrelated


def test_model2vec_downloads_only_needed_files(monkeypatch, tmp_path):
    import huggingface_hub
    import model2vec

    from app.embeddings.local import Model2VecEmbedder

    calls = {}

    def fake_snapshot(repo_id, allow_patterns):
        calls["patterns"] = allow_patterns
        return str(tmp_path)

    class FakeModel:
        dim = 4

        @classmethod
        def from_pretrained(cls, path, force_download):
            calls["path"], calls["force"] = path, force_download
            return cls()

    monkeypatch.setattr(huggingface_hub, "snapshot_download", fake_snapshot)
    monkeypatch.setattr(model2vec, "StaticModel", FakeModel)
    assert Model2VecEmbedder("org/some-model").dim == 4
    assert not any("onnx" in p for p in calls["patterns"])
    assert calls == {"patterns": calls["patterns"], "path": str(tmp_path), "force": False}


def test_fastembed_backend_reports_missing_dependency():
    with pytest.raises(ProviderError, match="pip install fastembed"):
        FastEmbedEmbedder("BAAI/bge-small-en-v1.5").embed_documents(["x"])
