"""Domain Layer - Lógica de negocio pura

DDD (Domain-Driven Design): Modelos, Agregados, Value Objects
Independiente de infraestructura.
"""

from .models import (
    DomainError,
    ValidationDomainError,
    GenerationDomainError,
    ValidationError,
    DiagramValidation,
    DiagramType,
    DiagramMetadata,
    StoredDiagram,
    DiagramRequest,
    DiagramResponse,
)

__all__ = [
    "DomainError",
    "ValidationDomainError",
    "GenerationDomainError",
    "ValidationError",
    "DiagramValidation",
    "DiagramType",
    "DiagramMetadata",
    "StoredDiagram",
    "DiagramRequest",
    "DiagramResponse",
]
