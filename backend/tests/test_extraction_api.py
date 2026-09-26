import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.fake_llm import FakeLLM
from tests.pdf_factory import CORRUPTED_PDF, make_pdf
from tests.stores import memory_qdrant

PDF = "application/pdf"


def make_client(tmp_path, llm=None) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        data_dir=tmp_path,
        groq_api_key=None,
        embedding_backend="hashing",
    )
    return TestClient(create_app(settings, llm_client=llm, vector_store_factory=memory_qdrant))


@pytest.fixture
def client(tmp_path) -> TestClient:
    return make_client(tmp_path, FakeLLM())


def upload(client, data=None, name="paper.pdf") -> str:
    resp = client.post("/api/papers", files=[("files", (name, data or make_pdf(), PDF))])
    return resp.json()["results"][0]["paper"]["paper_id"]


def test_extract_synchronously_and_view_knowledge(client):
    pid = upload(client)
    resp = client.post(f"/api/papers/{pid}/extract?wait=true")
    assert resp.status_code == 200
    assert resp.json()["extraction_status"] == "completed"
    assert resp.json()["extracted_at"]

    knowledge = client.get(f"/api/papers/{pid}/knowledge").json()
    assert knowledge["paper"]["id"] == pid
    assert knowledge["limitations"][0]["evidence"][0]["verification_status"] == "verified"
    ev = knowledge["limitations"][0]["evidence"][0]
    assert {"quote", "section", "chunk_id", "span", "confidence"} <= ev.keys()
    assert ev["span"]["page"] == 3


def test_extract_in_background(client):
    pid = upload(client)
    resp = client.post(f"/api/papers/{pid}/extract")
    assert resp.status_code == 202
    assert resp.json()["extraction_status"] == "running"
    # TestClient runs background tasks before returning, so the result is ready now.
    assert client.get(f"/api/papers/{pid}").json()["extraction_status"] == "completed"
    assert client.get(f"/api/papers/{pid}/knowledge").status_code == 200


def test_knowledge_404_before_extraction(client):
    pid = upload(client)
    resp = client.get(f"/api/papers/{pid}/knowledge")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_cannot_extract_unparsed_paper(client):
    pid = upload(client, CORRUPTED_PDF, "broken.pdf")
    resp = client.post(f"/api/papers/{pid}/extract")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "conflict"


def test_cannot_start_twice(client):
    pid = upload(client)
    service = client.app.state.extraction
    service.start(pid)  # leaves it marked running
    resp = client.post(f"/api/papers/{pid}/extract")
    assert resp.status_code == 409


def test_missing_api_key_returns_503_without_marking_running(tmp_path):
    client = make_client(tmp_path, llm=None)
    pid = upload(client)
    resp = client.post(f"/api/papers/{pid}/extract")
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "llm_not_configured"
    assert client.get(f"/api/papers/{pid}").json()["extraction_status"] is None


def test_llm_failure_is_recorded_on_paper(tmp_path):
    client = make_client(tmp_path, FakeLLM(extraction=lambda _m: "not json"))
    pid = upload(client)
    resp = client.post(f"/api/papers/{pid}/extract?wait=true")
    assert resp.status_code == 200
    body = resp.json()
    assert body["extraction_status"] == "failed"
    assert "extraction calls failed" in body["extraction_error"]
    assert client.get(f"/api/papers/{pid}/knowledge").status_code == 404


def test_reparsing_invalidates_extraction(client):
    pid = upload(client)
    client.post(f"/api/papers/{pid}/extract?wait=true")
    assert client.get(f"/api/papers/{pid}/knowledge").status_code == 200

    record = client.post(f"/api/papers/{pid}/process").json()
    assert record["extraction_status"] is None
    assert client.get(f"/api/papers/{pid}/knowledge").status_code == 404
