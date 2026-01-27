"""Pydantic models for CloudForge API

Defines request/response models for REST API endpoints.
"""

from typing import Any, Optional, List
from pydantic import BaseModel, Field


# ============================================================================
# Request Models
# ============================================================================


class GenerateRequest(BaseModel):
    """Request to generate diagram from description"""
    description: str = Field(..., description="Natural language architecture description")
    name: str = Field(..., description="Diagram name")


# ============================================================================
# Validation Models
# ============================================================================


class ValidationError(BaseModel):
    """Single validation error or warning"""
    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Error message")


class ValidationResponse(BaseModel):
    """AST validation results"""
    is_valid: bool = Field(..., description="Whether code passed validation")
    errors: List[ValidationError] = Field(default_factory=list, description="Validation errors")
    warnings: List[ValidationError] = Field(default_factory=list, description="Validation warnings")
    component_count: int = Field(default=0, description="Number of components found")
    relationship_count: int = Field(default=0, description="Number of relationships found")


# ============================================================================
# Blueprint Models
# ============================================================================


class BlueprintNode(BaseModel):
    """AWS service node in blueprint"""
    name: str = Field(..., description="Service name")
    variable: str = Field(..., description="Python variable name")
    service_type: str = Field(..., description="AWS service class")
    region: Optional[str] = Field(None, description="AWS region")


class BlueprintRelationship(BaseModel):
    """Connection between services"""
    source: str = Field(..., description="Source variable")
    destination: str = Field(..., description="Destination variable")
    connection_type: str = Field(default="default", description="Type of connection")


class BlueprintResponse(BaseModel):
    """Technical blueprint response"""
    title: str = Field(..., description="Architecture name")
    description: str = Field(..., description="Architecture description")
    nodes: List[BlueprintNode] = Field(default_factory=list, description="AWS services")
    relationships: List[BlueprintRelationship] = Field(default_factory=list, description="Connections")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


# ============================================================================
# Generation Response Models
# ============================================================================


class GenerateResponse(BaseModel):
    """Response from diagram generation"""
    success: bool = Field(..., description="Whether generation succeeded")
    message: str = Field(..., description="Human-readable message")
    blueprint: Optional[dict[str, Any]] = Field(None, description="Technical blueprint")
    code: Optional[str] = Field(None, description="Generated Python code")
    validation: Optional[ValidationResponse] = Field(None, description="AST validation results")
    output_files: dict[str, str] = Field(default_factory=dict, description="Generated file paths")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")


class DiagramMetadata(BaseModel):
    """Metadata about a saved diagram"""
    id: str = Field(..., description="Diagram ID")
    name: str = Field(..., description="Diagram name")
    created_at: str = Field(..., description="Creation timestamp (ISO format)")
    tags: List[str] = Field(default_factory=list, description="Diagram tags")
    formats: List[str] = Field(default_factory=list, description="Available formats")


class ListDiagramsResponse(BaseModel):
    """Response listing diagrams"""
    success: bool = Field(..., description="Whether listing succeeded")
    message: str = Field(..., description="Human-readable message")
    diagrams: List[DiagramMetadata] = Field(default_factory=list, description="List of diagrams")


class DiagramDetailsResponse(BaseModel):
    """Response with full diagram details"""
    success: bool = Field(..., description="Whether retrieval succeeded")
    message: str = Field(..., description="Human-readable message")
    diagram: Optional[dict[str, Any]] = Field(None, description="Diagram details")


class HealthResponse(BaseModel):
    """API health status"""
    status: str = Field(..., description="Health status (healthy/degraded)")
    pipeline_enabled: bool = Field(..., description="Whether LangGraph pipeline is available")
    message: str = Field(..., description="Status message")
