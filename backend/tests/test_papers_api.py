import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from tests.pdf_factory import CORRUPTED_PDF, make_pdf

PDF = "application/pdf"


@pytest.fixture
def client(tmp_path) -> TestClient:
    settings = Settings(
        _env_file=None,
        app_env="test",
        data_dir=tmp_path,
        chunk_size=300,
        chunk_overlap=50,
        max_files_per_upload=5,
        max_upload_mb=1,
    )
    return TestClient(create_app(settings))


def upload(client, *files):
    return client.post("/api/papers", files=[("files", f) for f in files])


def test_multi_file_upload_reports_each_file(client):
    resp = upload(
        client,
        ("paper1.pdf", make_pdf(), PDF),
        ("paper2.pdf", make_pdf(metadata_title="Second Paper"), PDF),
        ("notes.txt", b"hello", "text/plain"),
        ("broken.pdf", CORRUPTED_PDF, PDF),
        ("huge.pdf", b"%PDF-" + b"0" * (1024 * 1024), PDF),
    )
    assert resp.status_code == 200
    results = {r["file_name"]: r for r in resp.json()["results"]}

    assert results["paper1.pdf"]["paper"]["status"] == "parsed"
    assert results["paper2.pdf"]["paper"]["title"] == "Second Paper"
    assert results["notes.txt"]["paper"] is None
    assert results["notes.txt"]["error"]["code"] == "unsupported_file"
    assert results["broken.pdf"]["paper"]["status"] == "failed"
    assert results["huge.pdf"]["error"]["code"] == "file_too_large"

    listed = client.get("/api/papers").json()
    assert {p["file_name"] for p in listed} == {"paper1.pdf", "paper2.pdf", "broken.pdf"}


def test_get_paper_and_document(client):
    paper = upload(client, ("paper.pdf", make_pdf(), PDF)).json()["results"][0]["paper"]
    pid = paper["paper_id"]

    assert client.get(f"/api/papers/{pid}").json()["paper_id"] == pid

    doc = client.get(f"/api/papers/{pid}/document").json()
    assert doc["page_count"] == 3
    assert len(doc["pages"]) == 3
    assert len(doc["chunks"]) == paper["chunk_count"]
    for chunk in doc["chunks"]:
        assert doc["text"][chunk["char_start"] : chunk["char_end"]] == chunk["text"]
    assert any(s["kind"] == "limitations" for s in doc["sections"])


def test_duplicate_upload_flagged(client):
    data = make_pdf()
    first = upload(client, ("a.pdf", data, PDF)).json()["results"][0]
    second = upload(client, ("b.pdf", data, PDF)).json()["results"][0]
    assert not first["duplicate"]
    assert second["duplicate"]
    assert second["paper"]["paper_id"] == first["paper"]["paper_id"]


def test_process_endpoint_reparses(client):
    pid = upload(client, ("a.pdf", make_pdf(), PDF)).json()["results"][0]["paper"]["paper_id"]
    resp = client.post(f"/api/papers/{pid}/process")
    assert resp.status_code == 200
    assert resp.json()["status"] == "parsed"


def test_document_for_failed_paper_is_404(client):
    paper = upload(client, ("broken.pdf", CORRUPTED_PDF, PDF)).json()["results"][0]["paper"]
    resp = client.get(f"/api/papers/{paper['paper_id']}/document")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_unknown_paper_is_404(client):
    resp = client.get("/api/papers/paper_ffffffffffff")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_too_many_files_rejected(client):
    resp = upload(client, *[(f"p{i}.pdf", make_pdf(), PDF) for i in range(6)])
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "invalid_input"


def test_upload_without_files_is_422(client):
    assert client.post("/api/papers").status_code == 422
