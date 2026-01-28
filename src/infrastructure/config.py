"""Configuration settings for AWS Diagram MCP Server"""

import os
import json
from pathlib import Path
from typing import Optional
from pydantic import Field, ConfigDict
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Load .env file
load_dotenv()


class Settings(BaseSettings):
    """Application settings"""

    model_config = SettingsConfigDict(
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
        populate_by_name=True,  # Allow both field name and alias
    )

    # Google API Configuration
    google_api_key: Optional[str] = None

    # Storage settings
    diagrams_storage_path: Path = Field(
        default=Path.home() / ".aws_diagrams",
        alias="AWS_DIAGRAM_DIAGRAMS_STORAGE_PATH"
    )
    max_diagram_size_mb: int = Field(
        default=50,
        alias="AWS_DIAGRAM_MAX_DIAGRAM_SIZE_MB"
    )

    # Output formats - simple string, NOT parsed as JSON
    output_formats: str = Field(
        default="png,pdf,svg",
        alias="AWS_DIAGRAM_OUTPUT_FORMATS"
    )

    # Validation settings
    enable_validation: bool = Field(
        default=True,
        alias="AWS_DIAGRAM_ENABLE_VALIDATION"
    )
    max_components: int = Field(
        default=100,
        alias="AWS_DIAGRAM_MAX_COMPONENTS"
    )
    max_relationships: int = Field(
        default=200,
        alias="AWS_DIAGRAM_MAX_RELATIONSHIPS"
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        alias="AWS_DIAGRAM_LOG_LEVEL"
    )

    def __init__(self, **data: dict) -> None:
        super().__init__(**data)
        # Convert string output_formats to list
        if isinstance(self.output_formats, str):
            self.output_formats = [fmt.strip() for fmt in self.output_formats.split(",")]
        # Create storage directory if it doesn't exist
        self.diagrams_storage_path.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()
