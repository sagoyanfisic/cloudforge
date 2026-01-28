"""Configuration settings for AWS Diagram MCP Server"""

from pathlib import Path
from typing import Optional
from pydantic import Field, field_validator
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

    # Output formats - stored as str internally, parsed via property
    output_formats: str = Field(
        default="png,pdf,svg",
        alias="AWS_DIAGRAM_OUTPUT_FORMATS"
    )

    @field_validator("output_formats", mode="before")
    @classmethod
    def parse_output_formats(cls, v: object) -> str:
        if isinstance(v, list):
            return ",".join(v)
        return str(v)

    @property
    def output_formats_list(self) -> list[str]:
        """Return output formats as a list."""
        return [fmt.strip() for fmt in self.output_formats.split(",")]

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
        # Expand home directory if path contains tilde
        if isinstance(self.diagrams_storage_path, Path):
            self.diagrams_storage_path = self.diagrams_storage_path.expanduser()
        # Create storage directory if it doesn't exist
        self.diagrams_storage_path.mkdir(parents=True, exist_ok=True)


# Create global settings instance
settings = Settings()
