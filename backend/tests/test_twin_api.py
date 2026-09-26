import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import ProviderError
from app.embeddings.base import HashingEmbedder
from app.knowledge.graph_store.memory_store import MemoryGraphStore
from app.main import create_app
from tests.fake_llm import FakeLLM
from tests.pdf_factory import make_pdf
from tests.stores import memory_qdrant


def make_client(tmp_path, embedder=None) -> TestClient:
    settings = Settings(
        _env_file=None, app_env="test", data_dir=tmp_path, research_domain="Citation analysis"
    )
    app = create_app(
        settings,
        llm_client=FakeLLM(),
        graph_store=MemoryGraphStore(),
        vector_store_factory=memory_qdrant,
        embedder=embedder or HashingEmbedder(128),
    )
    return TestClient(app)


@pytest.fixture
def client(tmp_path):
    return make_client(tmp_path)


def ingest(client) -> str:
    files = [("files", ("paper.pdf", make_pdf(), "application/pdf"))]
    pid = client.post("/api/papers", files=files).json()["results"][0]["paper"]["paper_id"]
    record = client.post(f"/api/papers/{pid}/extract?wait=true").json()
    assert record["extraction_status"] == "completed"
    return pid


def test_extraction_automatically_updates_twin(client):
    pid = ingest(client)
    record = client.get(f"/api/papers/{pid}").json()
    assert record["twin_updated_at"] and record["twin_error"] is None

    summary = client.get("/api/twin/summary").json()
    assert summary["domain"] == "Citation analysis"
    assert summary["paper_count"] == 1
    assert summary["stats"]["entity_counts"]["Dataset"] == 2
    assert summary["stats"]["verified_evidence"] > 0
    assert summary["indexed_vectors"] > 0
    assert summary["last_update"]["paper_ids"] == [pid]
    assert {d["name"] for d in summary["top_datasets"]} == {"ACL-ARC", "SciCite"}


def test_graph_endpoints(client):
    pid = ingest(client)
    graph = client.get("/api/graph").json()
    ids = {n["id"] for n in graph["nodes"]}
    assert pid in ids
    assert all(e["source_id"] in ids and e["target_id"] in ids for e in graph["edges"])

    datasets = client.get("/api/graph", params={"type": "Dataset"}).json()
    assert {n["type"] for n in datasets["nodes"]} == {"Dataset"}
    assert datasets["edges"] == []  # no edges between datasets

    limitation = next(n for n in graph["nodes"] if n["type"] == "Limitation")
    detail = client.get(f"/api/graph/nodes/{limitation['id']}").json()
    assert detail["evidence"][0]["span"]["page"] == 3
    assert detail["neighbors"][0]["id"] == pid

    assert client.get("/api/graph/nodes/missing").status_code == 404


def test_evidence_search(client):
    ingest(client)
    hits = client.get(
        "/api/evidence/search",
        params={"q": "limited to English-language papers", "kind": "evidence"},
    ).json()
    assert hits and hits[0]["payload"]["section"] == "4 Limitations"
    assert client.get("/api/evidence/search", params={"q": "x"}).status_code == 422


def test_apply_is_idempotent_and_history_is_recorded(client):
    pid = ingest(client)  # first update happens automatically
    again = client.post(f"/api/twin/papers/{pid}").json()
    assert "no changes" in again["summary"]

    history = client.get("/api/twin/updates").json()
    assert len(history) == 2
    assert history[0]["id"] == again["id"]  # newest first

    snapshot = client.get("/api/twin/snapshot").json()
    assert snapshot["domain"] == "Citation analysis"
    assert len(snapshot["updates"]) == 2


def test_remove_paper_from_twin(client):
    pid = ingest(client)
    update = client.delete(f"/api/twin/papers/{pid}").json()
    assert update["operation"] == "remove"
    assert pid in update["removed_entity_ids"]
    summary = client.get("/api/twin/summary").json()
    assert summary["paper_count"] == 0 and summary["indexed_vectors"] == 0
    assert client.get(f"/api/papers/{pid}").json()["twin_updated_at"] is None


def test_apply_without_extraction_is_404(client):
    files = [("files", ("paper.pdf", make_pdf(), "application/pdf"))]
    pid = client.post("/api/papers", files=files).json()["results"][0]["paper"]["paper_id"]
    assert client.post(f"/api/twin/papers/{pid}").status_code == 404


class BrokenEmbedder(HashingEmbedder):
    def embed_documents(self, texts):
        raise ProviderError("embedding model unavailable")


def test_twin_failure_is_recorded_without_failing_extraction(tmp_path):
    client = make_client(tmp_path, embedder=BrokenEmbedder(128))
    pid = ingest(client)  # asserts extraction completed
    record = client.get(f"/api/papers/{pid}").json()
    assert record["twin_error"] == "embedding model unavailable"
    assert record["twin_updated_at"] is None
