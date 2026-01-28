"""Configuration settings for AWS Diagram MCP Server"""

from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Storage settings
    diagrams_storage_path: Path = Path.home() / ".aws_diagrams"
    max_diagram_size_mb: int = 50

    # Output formats
    output_formats: list[str] = ["png", "pdf", "svg"]

    # Validation settings
    enable_validation: bool = True
    max_components: int = 100
    max_relationships: int = 200

    # Logging
    log_level: str = "INFO"

    class Config:
        env_prefix = "AWS_DIAGRAM_"
        case_sensitive = False

    def __init__(self, **data: dict) -> None:
        super().__init__(**data)
        # Create storage directory if it doesn't exist
        self.diagrams_storage_path.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()
