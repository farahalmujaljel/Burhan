from fastapi import APIRouter, Request

from app.core.config import Settings
from app.schemas.api import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings: Settings = request.app.state.settings
    return HealthResponse(
        app=settings.app_name,
        version=settings.app_version,
        environment=settings.app_env,
        llm_provider=settings.llm_provider,
        llm_configured=settings.llm_configured,
        graph_backend=settings.graph_backend,
        vector_backend=settings.vector_backend,
    )
