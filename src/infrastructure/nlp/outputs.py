"""Pydantic output models for the NLP pipeline.

Shared by DescriptionRefinerChain, BlueprintArchitectChain, DiagramCoderChain,
and the multi-agent skill pipeline.
"""

from typing import Any

from pydantic import BaseModel, Field

from .models import BlueprintCluster, BlueprintNode, BlueprintRelationship


class AwsServiceRecommendation(BaseModel):
    """Single AWS service recommendation for a detected pattern"""

    service: str = Field(..., description="AWS service name (e.g. 'Amazon Bedrock')")
    role: str = Field(..., description="Role in the architecture (e.g. 'LLM inference and embeddings')")


class AwsPatternSkillOutput(BaseModel):
    """Structured output from AWS pattern detection skill"""

    pattern_labels: list[str] = Field(
        default_factory=list,
        description="Human-readable detected pattern names (e.g. 'RAG / Semantic Search')",
    )
    recommended_services: list[AwsServiceRecommendation] = Field(
        default_factory=list,
        description="AWS services recommended for detected patterns (6-8 most important)",
    )
    skill_notes: str = Field(
        default="",
        description="Brief architectural insight for the detected patterns",
    )


class BlueprintAnalysisOutput(BaseModel):
    """Structured blueprint analysis output"""

    title: str = Field(..., description="Architecture name")
    description: str = Field(..., description="Architecture description")
    nodes: list[BlueprintNode] = Field(default_factory=list, description="AWS services")
    clusters: list[BlueprintCluster] = Field(default_factory=list, description="VPC/subnet/logical groupings")
    relationships: list[BlueprintRelationship] = Field(default_factory=list, description="Connections")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DiagramCodeOutput(BaseModel):
    """Structured code generation output"""

    code: str = Field(..., description="Generated Python code")
    imports: list[str] = Field(default_factory=list, description="Import statements")
    classes_used: list[str] = Field(default_factory=list, description="AWS classes used")
