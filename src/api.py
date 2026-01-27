"""CloudForge FastAPI Server

REST API for AWS architecture diagram generation with natural language processing.
Provides endpoints for generating diagrams, validating code, and managing saved diagrams.
"""

import logging
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from src.api_models import (
    GenerateRequest,
    GenerateResponse,
    ListDiagramsResponse,
    DiagramDetailsResponse,
    HealthResponse,
)
from src.infrastructure.config import settings
from src.infrastructure.validator import DiagramValidator
from src.infrastructure.generator import DiagramGenerator
from src.infrastructure.storage import DiagramStorage
from src.infrastructure.langgraph_pipeline import DiagramPipeline

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="CloudForge",
    description="AI-Powered AWS Architecture Diagrams with Validation & Persistence",
    version="0.1.0",
)

# Add CORS middleware for Streamlit and other frontends
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (restrict in production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
validator = DiagramValidator()
generator = DiagramGenerator()
storage = DiagramStorage()

# Initialize LangGraph pipeline (optional - requires GOOGLE_API_KEY)
pipeline = None
pipeline_enabled = False
try:
    pipeline = DiagramPipeline(max_retries=3)
    pipeline_enabled = True
    logger.info("✅ LangGraph Pipeline enabled (with auto-retry)")
except ValueError as e:
    logger.warning(f"⚠️ LangGraph Pipeline disabled: {str(e)}")

# Storage path for diagram images
STORAGE_PATH = Path.home() / ".cloudforge" / "diagrams"
STORAGE_PATH.mkdir(parents=True, exist_ok=True)


# ============================================================================
# Health Check
# ============================================================================


@app.get("/health", response_model=HealthResponse)
async def health_check() -> dict[str, Any]:
    """Check API health and component status"""
    return {
        "status": "healthy" if pipeline_enabled else "degraded",
        "pipeline_enabled": pipeline_enabled,
        "message": "LangGraph pipeline available" if pipeline_enabled else "LangGraph pipeline unavailable",
    }


# ============================================================================
# Diagram Generation
# ============================================================================


@app.post("/v1/diagrams/generate", response_model=GenerateResponse)
async def generate_diagram(request: GenerateRequest) -> dict[str, Any]:
    """Generate AWS architecture diagram from natural language description.

    Uses LangGraph Pipeline with auto-retry for reliability:
    1. Blueprint Architect: Analyzes text → structured blueprint
    2. Diagram Coder: Blueprint → Python code (with LangChain retry)
    3. Validator: AST + security validation
    4. Generator: Code → diagram images (PNG, PDF, SVG)

    Args:
        request: GenerateRequest with description and diagram name

    Returns:
        GenerateResponse with blueprint, code, validation, and output files

    Requires:
        GOOGLE_API_KEY environment variable for Gemini API
    """
    if not pipeline_enabled:
        return {
            "success": False,
            "message": "LangGraph Pipeline not available. Set GOOGLE_API_KEY environment variable.",
            "errors": ["Pipeline disabled"],
        }

    try:
        logger.info(f"🤖 Processing with LangGraph Pipeline: {request.name}")

        # Run pipeline (with auto-retry logic)
        result = pipeline.generate(request.description, request.name)

        if not result.get("success"):
            logger.warning(f"⚠️ Pipeline failed: {result.get('errors', [])}")
            return {
                "success": False,
                "message": f"Pipeline failed: {', '.join(result.get('errors', ['Unknown error']))}",
                "errors": result.get("errors", []),
            }

        # Extract results
        blueprint = result.get("blueprint")
        code = result.get("code")
        validation = result.get("validation")
        output_files = result.get("output_files", {})

        # Format response with file URLs
        output_text = f"✅ Diagram generated from description: {request.name}\n\n"
        output_text += "📋 Technical Blueprint:\n"
        output_text += f"Title: {blueprint.get('title', 'N/A')}\n"
        output_text += f"Description: {blueprint.get('description', 'N/A')}\n"
        output_text += f"Services: {len(blueprint.get('nodes', []))}\n"
        output_text += f"Connections: {len(blueprint.get('relationships', []))}\n\n"

        if validation:
            output_text += "✔️ Validation Results:\n"
            output_text += f"  - Valid: {validation.get('is_valid', False)}\n"
            output_text += f"  - Components: {validation.get('component_count', 0)}\n"
            output_text += f"  - Relationships: {validation.get('relationship_count', 0)}\n"
            output_text += f"  - Errors: {len(validation.get('errors', []))}\n"
            output_text += f"  - Warnings: {len(validation.get('warnings', []))}\n\n"

        output_text += "Generated formats:\n"
        for fmt, path in output_files.items():
            output_text += f"  - {fmt}: {path}\n"

        logger.info(f"✅ Pipeline completed successfully")

        return {
            "success": True,
            "message": output_text,
            "blueprint": blueprint,
            "code": code,
            "validation": validation,
            "output_files": output_files,
            "errors": result.get("errors", []),
        }

    except Exception as e:
        logger.error(f"❌ Pipeline execution failed: {str(e)}")
        return {
            "success": False,
            "message": f"Pipeline failed: {str(e)}",
            "errors": [str(e)],
        }


# ============================================================================
# Image Serving
# ============================================================================


@app.get("/images/{filename}")
async def serve_image(filename: str) -> FileResponse:
    """Serve generated diagram images.

    Security: Validates filename to prevent path traversal attacks.

    Args:
        filename: Diagram filename (e.g., 'diagram_123.png')

    Returns:
        FileResponse with image file
    """
    # Validate filename (prevent path traversal)
    if ".." in filename or "/" in filename or "\\" in filename:
        logger.warning(f"🚨 Path traversal attempt: {filename}")
        raise HTTPException(status_code=400, detail="Invalid filename")

    # Validate file extension
    if not filename.endswith((".png", ".pdf", ".svg")):
        logger.warning(f"🚨 Invalid file type: {filename}")
        raise HTTPException(status_code=400, detail="Invalid file type")

    # Construct safe path
    file_path = STORAGE_PATH / filename

    # Verify file exists and is within STORAGE_PATH
    try:
        if not file_path.exists():
            logger.warning(f"❌ File not found: {filename}")
            raise HTTPException(status_code=404, detail="File not found")

        # Additional security check: ensure file is within storage path
        if not file_path.resolve().is_relative_to(STORAGE_PATH.resolve()):
            logger.warning(f"🚨 Path traversal detected: {filename}")
            raise HTTPException(status_code=400, detail="Invalid file path")

        # Determine media type
        media_type = "image/png"
        if filename.endswith(".pdf"):
            media_type = "application/pdf"
        elif filename.endswith(".svg"):
            media_type = "image/svg+xml"

        logger.debug(f"📤 Serving image: {filename}")
        return FileResponse(file_path, media_type=media_type)

    except ValueError:
        # is_relative_to not available, fall back to string comparison
        if not str(file_path.resolve()).startswith(str(STORAGE_PATH.resolve())):
            logger.warning(f"🚨 Path traversal detected: {filename}")
            raise HTTPException(status_code=400, detail="Invalid file path")

        logger.debug(f"📤 Serving image: {filename}")
        return FileResponse(file_path, media_type="image/png")


# ============================================================================
# Diagram Management
# ============================================================================


@app.get("/v1/diagrams", response_model=ListDiagramsResponse)
async def list_diagrams(tag: str = None) -> dict[str, Any]:
    """List saved diagrams.

    Args:
        tag: Optional tag to filter by

    Returns:
        ListDiagramsResponse with diagram list
    """
    try:
        diagrams = storage.list_diagrams(tag=tag)

        if not diagrams:
            return {
                "success": True,
                "message": "No diagrams found",
                "diagrams": [],
            }

        diagram_list = []
        output = f"Found {len(diagrams)} diagram(s):\n\n"
        for diagram in diagrams:
            diagram_list.append({
                "id": diagram.diagram_id,
                "name": diagram.metadata.name,
                "created_at": diagram.metadata.created_at.isoformat(),
                "tags": diagram.metadata.tags,
                "formats": list(diagram.file_paths.keys()),
            })
            output += f"ID: {diagram.diagram_id}\n"
            output += f"  Name: {diagram.metadata.name}\n"
            output += f"  Created: {diagram.metadata.created_at}\n"
            output += f"  Tags: {', '.join(diagram.metadata.tags)}\n"
            output += f"  Formats: {', '.join(diagram.file_paths.keys())}\n\n"

        return {
            "success": True,
            "message": output,
            "diagrams": diagram_list,
        }

    except Exception as e:
        logger.error(f"❌ Failed to list diagrams: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to list diagrams: {str(e)}",
            "diagrams": [],
        }


@app.get("/v1/diagrams/{diagram_id}", response_model=DiagramDetailsResponse)
async def get_diagram(diagram_id: str) -> dict[str, Any]:
    """Get specific diagram details.

    Args:
        diagram_id: Diagram ID to retrieve

    Returns:
        DiagramDetailsResponse with diagram information
    """
    if not diagram_id:
        raise HTTPException(status_code=400, detail="diagram_id is required")

    try:
        diagram = storage.get_diagram(diagram_id)
        if not diagram:
            return {
                "success": False,
                "message": f"Diagram not found: {diagram_id}",
            }

        output = f"Diagram: {diagram.metadata.name}\n"
        output += f"ID: {diagram.diagram_id}\n"
        output += f"Description: {diagram.metadata.description or 'N/A'}\n"
        output += f"Created: {diagram.metadata.created_at}\n"
        output += f"Size: {diagram.file_size_bytes} bytes\n"
        output += f"Formats: {', '.join(diagram.file_paths.keys())}\n"
        output += f"Checksum: {diagram.checksum}\n"

        return {
            "success": True,
            "message": output,
            "diagram": {
                "id": diagram.diagram_id,
                "name": diagram.metadata.name,
                "description": diagram.metadata.description,
                "created_at": diagram.metadata.created_at.isoformat(),
                "tags": diagram.metadata.tags,
                "size_bytes": diagram.file_size_bytes,
                "formats": diagram.file_paths,
                "checksum": diagram.checksum,
            },
        }

    except Exception as e:
        logger.error(f"❌ Failed to get diagram: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to get diagram: {str(e)}",
        }


@app.delete("/v1/diagrams/{diagram_id}")
async def delete_diagram(diagram_id: str) -> dict[str, Any]:
    """Delete a saved diagram.

    Args:
        diagram_id: Diagram ID to delete

    Returns:
        Dictionary with deletion result
    """
    if not diagram_id:
        raise HTTPException(status_code=400, detail="diagram_id is required")

    try:
        if storage.delete_diagram(diagram_id):
            logger.info(f"✅ Diagram deleted: {diagram_id}")
            return {
                "success": True,
                "message": f"Diagram deleted: {diagram_id}",
            }

        return {
            "success": False,
            "message": f"Diagram not found: {diagram_id}",
        }

    except Exception as e:
        logger.error(f"❌ Failed to delete diagram: {str(e)}")
        return {
            "success": False,
            "message": f"Failed to delete diagram: {str(e)}",
        }


# ============================================================================
# Startup/Shutdown
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("🔥 CloudForge API starting...")
    logger.info(f"📁 Storage path: {STORAGE_PATH}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("🛑 CloudForge API shutting down...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
