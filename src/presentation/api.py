"""CloudForge FastAPI Server - Presentation Layer

REST API endpoints para acceder a los servicios de la aplicación.
Usa inyección de dependencias para desacoplamiento.
"""

import logging
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from ..infrastructure.config import settings
from ..infrastructure.mcp_client import get_mcp_client
from ..infrastructure.storage import DiagramStorage
from ..infrastructure.validator import DiagramValidator
from ..infrastructure import server as mcp_server
from ..application.services import (
    create_diagram_generation_service,
    create_nl_diagram_service,
)
from ..domain.models import (
    GenerationDomainError,
    ValidationDomainError,
)
from .api_models import (
    GenerateRequest,
    GenerateResponse,
    ValidationResponse,
    ValidationErrorResponse,
    HistoryResponse,
    DiagramSummary,
    DiagramDetailResponse,
)

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Initialize components
mcp_client = get_mcp_client()
storage = DiagramStorage()
validator = DiagramValidator()
_generation_service = None
_nl_service = None


# ============================================================================
# Dependency Injection Helpers
# ============================================================================


def get_generation_service():
    """Get or create generation service - Lazy initialization"""
    global _generation_service
    if _generation_service is None:
        _generation_service = create_diagram_generation_service()
    return _generation_service


def get_nl_service():
    """Get or create NL service - Lazy initialization"""
    global _nl_service
    if _nl_service is None:
        nl_processor = mcp_client.generate_from_description
        _nl_service = create_nl_diagram_service(nl_processor)
    return _nl_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage API lifecycle - startup and shutdown

    Inicializa servicios y cliente MCP al iniciar.
    """
    # Startup
    logger.info("🔥 Starting CloudForge API")
    if mcp_client.connect():
        logger.info("✅ MCP client connected")
    else:
        logger.warning("⚠️ MCP client connection failed")

    # Initialize services
    get_generation_service()
    get_nl_service()
    logger.info("✅ Services initialized")

    yield

    # Shutdown
    logger.info("🛑 Shutting down CloudForge API")
    mcp_client.close()
    logger.info("✅ MCP client closed")


# Create FastAPI app
app = FastAPI(
    title="CloudForge API",
    description="REST API for AWS architecture diagram generation from natural language",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware for Streamlit
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Helper Functions
# ============================================================================


def _validation_to_response(validation: Any) -> ValidationResponse:
    """Convert validator.DiagramValidation or dict to API ValidationResponse"""
    # Handle both object and dict formats
    if isinstance(validation, dict):
        is_valid = validation.get("is_valid", False)
        errors_list = validation.get("errors", [])
        warnings_list = validation.get("warnings", [])
        component_count = validation.get("component_count", 0)
        relationship_count = validation.get("relationship_count", 0)
    else:
        is_valid = validation.is_valid
        errors_list = validation.errors
        warnings_list = validation.warnings
        component_count = validation.component_count
        relationship_count = validation.relationship_count

    # Convert errors
    errors = []
    for e in errors_list:
        if isinstance(e, dict):
            errors.append(ValidationErrorResponse(
                field=e.get("field", "unknown"),
                message=e.get("message", ""),
                severity=e.get("severity", "error"),
            ))
        else:
            errors.append(ValidationErrorResponse(
                field=e.field,
                message=e.message,
                severity=e.severity,
            ))

    # Convert warnings
    warnings = []
    for w in warnings_list:
        if isinstance(w, dict):
            warnings.append(ValidationErrorResponse(
                field=w.get("field", "unknown"),
                message=w.get("message", ""),
                severity=w.get("severity", "warning"),
            ))
        else:
            warnings.append(ValidationErrorResponse(
                field=w.field,
                message=w.message,
                severity=w.severity,
            ))

    return ValidationResponse(
        is_valid=is_valid,
        errors=errors,
        warnings=warnings,
        component_count=component_count,
        relationship_count=relationship_count,
    )


def _get_storage_path() -> Path:
    """Get the storage directory for diagrams"""
    storage_path = settings.diagrams_storage_path / "diagrams"
    storage_path.mkdir(parents=True, exist_ok=True)
    return storage_path


def _validate_filename(filename: str) -> bool:
    """Validate filename for security"""
    # Check for path traversal attempts
    if ".." in filename or "/" in filename or "\\" in filename:
        return False
    # Only allow image and document files
    if not filename.endswith((".png", ".pdf", ".svg")):
        return False
    return True


# ============================================================================
# Health Check Endpoint
# ============================================================================


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mcp_connected": mcp_client.is_connected(),
        "pipeline_enabled": mcp_server.pipeline_enabled,
    }


# ============================================================================
# Diagram Generation Endpoints
# ============================================================================


@app.post("/v1/diagrams/generate", response_model=GenerateResponse)
async def generate_diagram(request: GenerateRequest) -> GenerateResponse:
    """Generate AWS architecture diagram from natural language description.

    Usa NaturalLanguageDiagramService para orquestar el proceso.
    - Validación de entrada
    - Llamada a servicio de NL
    - Manejo de errores con excepciones de dominio
    - Construcción de respuesta

    Args:
        request: GenerateRequest with description and name

    Returns:
        GenerateResponse with generated code, blueprint, validation, and image URLs
    """
    logger.info(f"📝 Generating diagram: {request.name}")

    try:
        # Get service with dependency injection
        nl_service = get_nl_service()

        # Call service to generate from description
        logger.info("🤖 Generating from description using AI")
        result = nl_service.generate_from_description(
            request.description, request.name
        )

        if not result.get("success"):
            return GenerateResponse(
                success=False,
                message=result.get("message", "Generation failed"),
                output_files={},
            )

        # Extract generated code and blueprint
        generated_code = result.get("code", "")
        blueprint = result.get("blueprint", "")
        output_files_result = result.get("output_files", {})

        if not generated_code:
            return GenerateResponse(
                success=False,
                message="No code generated",
                output_files={},
            )

        # Get validation from service result
        validation = result.get("validation")
        validation_response = _validation_to_response(validation) if validation else None

        # Build output files response with image URLs
        storage_path = _get_storage_path()
        output_files = {}

        for fmt, file_path in output_files_result.items():
            source_path = Path(file_path)
            if source_path.exists():
                # Copy to storage directory so it can be served
                filename = source_path.name
                dest_path = storage_path / filename
                try:
                    import shutil
                    shutil.copy2(source_path, dest_path)
                    output_files[fmt] = f"/images/{filename}"
                    logger.info(f"✅ Generated {fmt}: {filename}")
                except Exception as e:
                    logger.error(f"Failed to copy {fmt} file: {e}")
                    # Still add it but with the full path as fallback
                    output_files[fmt] = f"/images/{file_path}"

        return GenerateResponse(
            success=True,
            message=f"✅ Diagram generated successfully: {request.name}",
            blueprint=blueprint,
            code=generated_code,
            validation=validation_response,
            output_files=output_files,
        )

    except (GenerationDomainError, ValidationDomainError) as e:
        """Errores de dominio - esperados y manejables"""
        logger.warning(f"⚠️ Domain error: {str(e)}")
        return GenerateResponse(
            success=False,
            message=f"Generation error: {str(e)}",
            output_files={},
        )

    except Exception as e:
        """Errores inesperados"""
        logger.error(f"❌ Unexpected error: {str(e)}")
        return GenerateResponse(
            success=False,
            message=f"Generation failed: {str(e)}",
            output_files={},
        )


# ============================================================================
# Diagram History Endpoints
# ============================================================================


@app.get("/v1/diagrams/history", response_model=HistoryResponse)
async def get_history() -> HistoryResponse:
    """Get list of recently generated diagrams.

    Returns:
        HistoryResponse with list of diagram summaries
    """
    try:
        diagrams = storage.list_diagrams()
        logger.info(f"📚 Found {len(diagrams)} diagrams in history")

        summaries = []
        for diagram in diagrams[:10]:  # Return last 10
            summary = DiagramSummary(
                id=diagram.diagram_id,
                name=diagram.metadata.name,
                created_at=diagram.metadata.created_at.isoformat(),
                tags=diagram.metadata.tags,
                error_count=0,  # Could add validation summary if stored
                warning_count=0,
            )
            summaries.append(summary)

        return HistoryResponse(
            success=True,
            diagrams=summaries,
            total_count=len(diagrams),
        )

    except Exception as e:
        logger.error(f"❌ Failed to get history: {str(e)}")
        return HistoryResponse(
            success=False,
            diagrams=[],
            total_count=0,
        )


@app.get("/v1/diagrams/{diagram_id}", response_model=DiagramDetailResponse)
async def get_diagram(diagram_id: str) -> DiagramDetailResponse:
    """Get a specific diagram by ID.

    Args:
        diagram_id: The diagram ID

    Returns:
        DiagramDetailResponse with diagram details
    """
    try:
        diagram = storage.get_diagram(diagram_id)

        if not diagram:
            return DiagramDetailResponse(
                success=False,
                message=f"Diagram not found: {diagram_id}",
            )

        # Validate the stored code
        validation = validator.validate(diagram.code)
        validation_response = _validation_to_response(validation)

        # Build output files response with URLs
        output_files = {}
        for fmt, file_path in diagram.file_paths.items():
            filename = Path(file_path).name
            output_files[fmt] = f"/images/{filename}"

        return DiagramDetailResponse(
            success=True,
            message="Diagram retrieved successfully",
            id=diagram.diagram_id,
            name=diagram.metadata.name,
            code=diagram.code,
            validation=validation_response,
            created_at=diagram.metadata.created_at.isoformat(),
            output_files=output_files,
        )

    except Exception as e:
        logger.error(f"❌ Failed to get diagram: {str(e)}")
        return DiagramDetailResponse(
            success=False,
            message=f"Failed to get diagram: {str(e)}",
        )


# ============================================================================
# Image Serving Endpoint
# ============================================================================


@app.get("/images/{filename}")
async def serve_image(filename: str) -> FileResponse:
    """Serve generated diagram images.

    Args:
        filename: Name of the image file

    Returns:
        FileResponse with the image file

    Raises:
        HTTPException: If filename is invalid or file not found
    """
    # Validate filename for security
    if not _validate_filename(filename):
        logger.warning(f"⚠️ Invalid filename requested: {filename}")
        raise HTTPException(
            status_code=400,
            detail="Invalid filename",
        )

    storage_path = _get_storage_path()
    file_path = storage_path / filename

    # Verify path is within storage directory
    try:
        file_path.resolve().relative_to(storage_path.resolve())
    except ValueError:
        logger.warning(f"⚠️ Path traversal attempt detected: {filename}")
        raise HTTPException(
            status_code=400,
            detail="Invalid path",
        )

    if not file_path.exists():
        logger.warning(f"⚠️ Image not found: {filename}")
        raise HTTPException(
            status_code=404,
            detail="Image not found",
        )

    logger.debug(f"📥 Serving image: {filename}")

    # Determine media type based on extension
    if filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".pdf"):
        media_type = "application/pdf"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"
    else:
        media_type = "application/octet-stream"

    return FileResponse(file_path, media_type=media_type)


# ============================================================================
# Root Endpoints
# ============================================================================


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint with API information"""
    return {
        "name": "CloudForge API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
    )
