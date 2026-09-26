from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.errors import NotFoundError, register_exception_handlers
from app.main import create_app


def test_health_ok(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["app"] == "Burhan"
    assert body["environment"] == "test"
    assert body["llm_provider"] == "groq"
    assert body["llm_configured"] is False
    assert body["graph_backend"] == "memory"
    assert body["vector_backend"] == "local"


def test_health_never_leaks_secrets():
    settings = Settings(_env_file=None, app_env="test", groq_api_key="gsk_super_secret")
    resp = TestClient(create_app(settings)).get("/api/health")
    assert resp.json()["llm_configured"] is True
    assert "gsk_super_secret" not in resp.text


def test_burhan_errors_render_consistent_shape():
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/boom")
    def boom():
        raise NotFoundError("paper not found", details={"paper_id": "x"})

    resp = TestClient(app).get("/boom")
    assert resp.status_code == 404
    assert resp.json() == {
        "error": {"code": "not_found", "message": "paper not found", "details": {"paper_id": "x"}}
    }
