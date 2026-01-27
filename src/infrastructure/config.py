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
        env_prefix="AWS_DIAGRAM_",
        case_sensitive=False,
        extra="ignore",  # Ignore extra environment variables
    )

    # Storage settings
    diagrams_storage_path: Path = Path.home() / ".aws_diagrams"
    max_diagram_size_mb: int = 50

    # Output formats - simple string, NOT parsed as JSON
    output_formats: str = "png,pdf,svg"

    # Validation settings
    enable_validation: bool = True
    max_components: int = 100
    max_relationships: int = 200

    # Logging
    log_level: str = "INFO"

    def __init__(self, **data: dict) -> None:
        super().__init__(**data)
        # Convert string output_formats to list
        if isinstance(self.output_formats, str):
            self.output_formats = [fmt.strip() for fmt in self.output_formats.split(",")]
        # Create storage directory if it doesn't exist
        self.diagrams_storage_path.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()
