"""Blueprint data models for natural language processing pipeline.

Shared models used by BlueprintArchitect, DiagramCoder, and LangChain chains.
"""

from typing import Optional

from pydantic import BaseModel, Field


class BlueprintNode(BaseModel):
    """Represents a single AWS service node in the architecture."""

    name: str = Field(..., description="Human-readable service name")
    variable: str = Field(..., description="Python variable name")
    service_type: str = Field(..., description="AWS service class (e.g., Lambda, S3)")
    region: Optional[str] = Field(None, description="AWS region")


class BlueprintCluster(BaseModel):
    """Represents a logical grouping of services."""

    name: str = Field(..., description="Cluster name")
    nodes: list[str] = Field(default_factory=list, description="Node variables in cluster")


class BlueprintRelationship(BaseModel):
    """Represents a connection between two services."""

    source: str = Field(..., description="Source node variable")
    destination: str = Field(..., description="Destination node variable")
    connection_type: str = Field(default="default", description="Type of connection")


class ArchitectureBlueprint(BaseModel):
    """Structured technical blueprint extracted from raw text."""

    title: str = Field(..., description="Architecture name")
    description: str = Field(..., description="Brief description")
    nodes: list[BlueprintNode] = Field(default_factory=list)
    clusters: list[BlueprintCluster] = Field(default_factory=list)
    relationships: list[BlueprintRelationship] = Field(default_factory=list)

    def __str__(self) -> str:
        """Format blueprint as text for code generation."""
        output = "---BEGIN_BLUEPRINT---\n"
        output += f"Title: {self.title}\n"
        output += f"Description: {self.description}\n\n"

        output += "Nodes:\n"
        for node in self.nodes:
            output += f"- {node.name} as {node.variable} (Type: {node.service_type})\n"

        if self.clusters:
            output += "\nClusters:\n"
            for cluster in self.clusters:
                output += f"- {cluster.name} contains {', '.join(cluster.nodes)}\n"

        output += "\nRelationships:\n"
        for rel in self.relationships:
            output += f"- {rel.source} >> {rel.destination}\n"

        output += "---END_BLUEPRINT---\n"
        return output
