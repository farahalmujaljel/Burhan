import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.schemas import Evidence, Finding, Method, Paper


@pytest.fixture
def settings() -> Settings:
    # _env_file=None keeps tests independent of a developer's local .env
    return Settings(_env_file=None, app_env="test", groq_api_key=None)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


@pytest.fixture
def paper() -> Paper:
    return Paper(id="paper_a", name="Attention Is All You Need", year=2017)


@pytest.fixture
def make_evidence():
    def _make(paper_id: str = "paper_a", quote: str = "The Transformer achieves 28.4 BLEU.", **kw):
        return Evidence(paper_id=paper_id, quote=quote, extracted_by="knowledge_extraction", **kw)

    return _make


@pytest.fixture
def finding(make_evidence) -> Finding:
    return Finding(
        id="finding_a",
        name="Transformer outperforms RNN baselines on WMT14 En-De",
        paper_id="paper_a",
        evidence=[make_evidence()],
    )


@pytest.fixture
def method() -> Method:
    return Method(id="method_transformer", name="Transformer")
