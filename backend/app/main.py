from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, papers
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.parsing.pymupdf_parser import PyMuPDFParser
from app.services.document_store import DocumentStore
from app.services.ingestion import IngestionService


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    app = FastAPI(
        title=f"{settings.app_name} API",
        version=settings.app_version,
        description="Agentic AI Research Scientist - Research Digital Twin backend",
    )
    app.state.settings = settings
    app.state.ingestion = IngestionService(
        store=DocumentStore(settings.uploads_dir),
        parser=PyMuPDFParser(),
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        max_upload_bytes=settings.max_upload_bytes,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.include_router(health.router, prefix=settings.api_prefix)
    app.include_router(papers.router, prefix=settings.api_prefix)
    return app


app = create_app()
