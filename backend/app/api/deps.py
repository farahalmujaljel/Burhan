from fastapi import Request

from app.core.config import Settings
from app.services.extraction import ExtractionService
from app.services.ingestion import IngestionService
from app.twin.service import TwinService


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_ingestion(request: Request) -> IngestionService:
    return request.app.state.ingestion


def get_extraction(request: Request) -> ExtractionService:
    return request.app.state.extraction


def get_twin(request: Request) -> TwinService:
    return request.app.state.twin
