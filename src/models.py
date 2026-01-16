"""Data models for AWS Diagrams"""

from datetime import datetime
from typing import Any, Optional
from enum import Enum
from pydantic import BaseModel, Field


class DiagramType(str, Enum):
    """Supported diagram types"""

    AWS_ARCHITECTURE = "aws_architecture"
    SEQUENCE = "sequence"
    FLOW = "flow"
    CLASS = "class"


class ValidationError(BaseModel):
    """Validation error model"""

    field: str
    message: str
    severity: str = Field(default="error", description="error, warning, info")


class DiagramMetadata(BaseModel):
    """Metadata for a diagram"""

    name: str = Field(..., description="Diagram name")
    description: Optional[str] = Field(None, description="Diagram description")
    diagram_type: DiagramType = Field(default=DiagramType.AWS_ARCHITECTURE)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    author: Optional[str] = Field(None, description="Diagram author")
    tags: list[str] = Field(default_factory=list, description="Tags for organization")


class DiagramRequest(BaseModel):
    """Request to generate a diagram"""

    code: str = Field(..., description="Python code to generate the diagram")
    metadata: DiagramMetadata
    validate: bool = Field(default=True, description="Validate before generating")


class DiagramResponse(BaseModel):
    """Response from diagram generation"""

    success: bool
    diagram_id: Optional[str] = None
    message: str
    file_path: Optional[str] = None
    output_formats: dict[str, str] = Field(default_factory=dict)
    validation_errors: list[ValidationError] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class StoredDiagram(BaseModel):
    """Stored diagram information"""

    diagram_id: str = Field(..., description="Unique diagram identifier")
    metadata: DiagramMetadata
    code: str = Field(..., description="Original Python code")
    file_paths: dict[str, str] = Field(
        default_factory=dict, description="Format -> file path mapping"
    )
    file_size_bytes: int
    checksum: str = Field(..., description="SHA256 checksum of code")


class DiagramValidation(BaseModel):
    """Diagram validation result"""

    is_valid: bool
    errors: list[ValidationError] = Field(default_factory=list)
    warnings: list[ValidationError] = Field(default_factory=list)
    component_count: int = 0
    relationship_count: int = 0
    analysis: dict[str, Any] = Field(default_factory=dict)
