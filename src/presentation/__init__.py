"""Presentation Layer - Interfaces HTTP

FastAPI REST API endpoints.
Interfaces para que clientes accedan a los servicios.
"""

from .api import app
from .api_models import (
    GenerateRequest,
    GenerateResponse,
    ValidationResponse,
    HistoryResponse,
    DiagramDetailResponse,
)

__all__ = [
    "app",
    "GenerateRequest",
    "GenerateResponse",
    "ValidationResponse",
    "HistoryResponse",
    "DiagramDetailResponse",
]
