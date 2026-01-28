"""Pydantic models for FastAPI endpoints"""

from typing import Any, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request to generate diagram from natural language description"""

    description: str = Field(
        ..., description="Natural language description of the architecture"
    )
    name: str = Field(..., description="Diagram name")


class RefineRequest(BaseModel):
    """Request to refine architecture description"""

    description: str = Field(
        ..., description="Brief or vague architecture description to refine"
    )


class RefineResponse(BaseModel):
    """Response from description refinement endpoint"""

    success: bool = Field(..., description="Whether refinement was successful")
    original: str = Field(..., description="Original input description")
    refined: str = Field(..., description="Refined and detailed description")
    message: str = Field(..., description="Status message")


class ValidationErrorResponse(BaseModel):
    """Single validation error or warning"""

    field: str = Field(..., description="Field that caused the error")
    message: str = Field(..., description="Error message")
    severity: str = Field(
        default="error", description="Severity level: error, warning, info"
    )


class ValidationResponse(BaseModel):
    """Complete validation result for generated code"""

    is_valid: bool = Field(..., description="Whether code is valid")
    errors: list[ValidationErrorResponse] = Field(
        default_factory=list, description="List of validation errors"
    )
    warnings: list[ValidationErrorResponse] = Field(
        default_factory=list, description="List of warnings and security concerns"
    )
    component_count: int = Field(..., description="Number of AWS components detected")
    relationship_count: int = Field(..., description="Number of relationships detected")


class GenerateResponse(BaseModel):
    """Response from diagram generation endpoint"""

    success: bool = Field(..., description="Whether generation was successful")
    message: str = Field(..., description="Status message")
    blueprint: Optional[dict[str, Any]] = Field(
        None, description="Technical blueprint generated from description"
    )
    code: Optional[str] = Field(None, description="Generated Python code")
    validation: Optional[ValidationResponse] = Field(
        None, description="AST validation results"
    )
    output_files: dict[str, str] = Field(
        default_factory=dict, description="Format -> URL mapping for generated files"
    )


class DiagramSummary(BaseModel):
    """Summary of a saved diagram"""

    id: str = Field(..., description="Diagram ID")
    name: str = Field(..., description="Diagram name")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    tags: list[str] = Field(default_factory=list, description="Diagram tags")
    error_count: int = Field(default=0, description="Number of validation errors")
    warning_count: int = Field(default=0, description="Number of validation warnings")


class HistoryResponse(BaseModel):
    """Response for diagram history endpoint"""

    success: bool = Field(..., description="Whether request was successful")
    diagrams: list[DiagramSummary] = Field(
        default_factory=list, description="List of recent diagrams"
    )
    total_count: int = Field(default=0, description="Total number of saved diagrams")


class DiagramDetailResponse(BaseModel):
    """Response for getting a specific diagram"""

    success: bool = Field(..., description="Whether request was successful")
    message: str = Field(..., description="Status message")
    id: Optional[str] = Field(None, description="Diagram ID")
    name: Optional[str] = Field(None, description="Diagram name")
    code: Optional[str] = Field(None, description="Python source code")
    blueprint: Optional[dict[str, Any]] = Field(None, description="Technical blueprint")
    validation: Optional[ValidationResponse] = Field(
        None, description="Validation results"
    )
    created_at: Optional[str] = Field(None, description="Creation timestamp")
    output_files: dict[str, str] = Field(
        default_factory=dict, description="Format -> URL mapping"
    )
