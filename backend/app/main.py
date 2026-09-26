from collections.abc import Callable

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, papers, twin
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.embeddings.base import Embedder
from app.embeddings.factory import create_embedder
from app.knowledge.factory import create_graph_store, create_vector_store
from app.knowledge.graph_store.base import GraphStore
from app.knowledge.vector_store.base import VectorStore
from app.llm.base import LLMClient
from app.llm.factory import create_llm_client
from app.parsing.pymupdf_parser import PyMuPDFParser
from app.services.document_store import DocumentStore
from app.services.extraction import ExtractionService
from app.services.ingestion import IngestionService
from app.twin.evidence_index import EvidenceIndex
from app.twin.repository import TwinUpdateLog
from app.twin.service import TwinService


def create_app(
    settings: Settings | None = None,
    *,
    llm_client: LLMClient | None = None,
    graph_store: GraphStore | None = None,
    vector_store_factory: Callable[[], VectorStore] | None = None,
    embedder: Embedder | None = None,
) -> FastAPI:
    """Build the app. Keyword overrides replace configured backends (used by tests)."""
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description="Agentic AI Research Scientist - Research Digital Twin backend",
    )
    app.state.settings = settings
    store = DocumentStore(settings.uploads_dir)
    app.state.ingestion = IngestionService(
        store=store,
        parser=PyMuPDFParser(),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        max_upload_bytes=settings.max_upload_bytes,
    )
    app.state.twin = TwinService(
        store,
        graph_store or create_graph_store(settings),
        EvidenceIndex(
            vector_store_factory or (lambda: create_vector_store(settings)),
            embedder or create_embedder(settings),
        ),
        TwinUpdateLog(settings.twin_dir / "updates.jsonl"),
        domain=settings.research_domain,
    )
    app.state.extraction = ExtractionService(
        store,
        # Created lazily so the API starts without GROQ_API_KEY; extraction then returns 503.
        (lambda: llm_client) if llm_client else (lambda: create_llm_client(settings)),
        window_chars=settings.extraction_window_chars,
        verification_batch_size=settings.verification_batch_size,
        max_attempts=settings.llm_max_retries + 1,
        max_output_tokens=settings.llm_max_output_tokens,
        on_completed=app.state.twin.apply_paper_safely,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    for router in (health.router, papers.router, twin.router):
        app.include_router(router, prefix=settings.api_prefix)
    return app


app = create_app()
