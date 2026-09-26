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


@pytest.fixture
def parsed_doc():
    """The generated sample paper, parsed, sectioned, and chunked (small chunks)."""
    from app.parsing.chunker import chunk_document
    from app.parsing.pymupdf_parser import PyMuPDFParser
    from app.parsing.sectioner import detect_sections
    from tests.pdf_factory import make_pdf

    doc = PyMuPDFParser().parse(make_pdf(), paper_id="paper_0123456789ab", file_name="sample.pdf")
    doc = doc.model_copy(update={"sections": detect_sections(doc)})
    return doc.model_copy(update={"chunks": chunk_document(doc, size=300, overlap=50)})


def build_knowledge(paper_id: str, extraction=None):
    """Parse the sample PDF under `paper_id` and extract knowledge with the fake LLM."""
    from app.parsing.chunker import chunk_document
    from app.parsing.pymupdf_parser import PyMuPDFParser
    from app.parsing.sectioner import detect_sections
    from app.services.extraction import KnowledgeExtractor
    from tests.fake_llm import FakeLLM
    from tests.pdf_factory import make_pdf

    doc = PyMuPDFParser().parse(make_pdf(), paper_id=paper_id, file_name=f"{paper_id}.pdf")
    doc = doc.model_copy(update={"sections": detect_sections(doc)})
    doc = doc.model_copy(update={"chunks": chunk_document(doc, size=300, overlap=50)})
    llm = FakeLLM(extraction=extraction) if extraction else FakeLLM()
    knowledge = KnowledgeExtractor(llm, window_chars=100_000, max_attempts=2).extract(doc)
    return doc, knowledge
