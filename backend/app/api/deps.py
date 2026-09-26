from fastapi import Request

from app.core.config import Settings
from app.services.ingestion import IngestionService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_ingestion(request: Request) -> IngestionService:
    return request.app.state.ingestion
