"""CloudForge MCP Server

FastMCP implementation of CloudForge for AWS architecture diagram generation,
validation, and persistent storage."""

import logging
from typing import Any

from mcp.server import FastMCP

from .models import DiagramMetadata, DiagramType
from .validator import DiagramValidator
from .generator import DiagramGenerator
from .storage import DiagramStorage
from .config import settings

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Initialize FastMCP
server = FastMCP("cloudforge")

# Initialize components
validator = DiagramValidator()
generator = DiagramGenerator()
storage = DiagramStorage()


@server.tool()
def generate_diagram(
    code: str,
    name: str,
    description: str = "",
    validate: bool = True,
) -> dict[str, Any]:
    """Generate an AWS architecture diagram.

    Args:
        code: Python code using diagrams DSL
        name: Diagram name
        description: Diagram description
        validate: Validate before generating (default: True)

    Returns:
        Dictionary with generation result
    """
    try:
        # Validate if requested
        if validate:
            validation = validator.validate(code)
            if not validation.is_valid:
                errors = [f"{e.field}: {e.message}" for e in validation.errors]
                return {
                    "success": False,
                    "message": f"Validation failed:\n" + "\n".join(errors),
                    "errors": errors,
                }

        # Generate diagram
        output_files = generator.generate(code, name, settings.output_formats)

        if not output_files:
            return {
                "success": False,
                "message": "No output files generated",
            }

        # Format output
        output_text = f"Diagram generated successfully: {name}\n\n"
        output_text += "Generated formats:\n"
        for fmt, path in output_files.items():
            output_text += f"  - {fmt}: {path}\n"

        return {
            "success": True,
            "message": output_text,
            "output_files": output_files,
        }

    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        return {
            "success": False,
            "message": f"Generation failed: {str(e)}",
        }


@server.tool()
def validate_diagram(code: str) -> dict[str, Any]:
    """Validate diagram code.

    Args:
        code: Python code to validate

    Returns:
        Validation result with errors and warnings
    """
    validation = validator.validate(code)

    output = f"Validation Result: {'Valid' if validation.is_valid else 'Invalid'}\n\n"
    output += f"Components: {validation.component_count}\n"
    output += f"Relationships: {validation.relationship_count}\n\n"

    errors_list = []
    if validation.errors:
        output += "Errors:\n"
        for error in validation.errors:
            msg = f"{error.field}: {error.message}"
            output += f"  - {msg}\n"
            errors_list.append(msg)

    warnings_list = []
    if validation.warnings:
        output += "\nWarnings:\n"
        for warning in validation.warnings:
            msg = f"{warning.field}: {warning.message}"
            output += f"  - {msg}\n"
            warnings_list.append(msg)

    return {
        "is_valid": validation.is_valid,
        "message": output,
        "component_count": validation.component_count,
        "relationship_count": validation.relationship_count,
        "errors": errors_list,
        "warnings": warnings_list,
    }


@server.tool()
def list_diagrams(tag: str = None) -> dict[str, Any]:
    """List all saved diagrams.

    Args:
        tag: Optional tag to filter by

    Returns:
        List of diagrams with metadata
    """
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


@server.tool()
def get_diagram(diagram_id: str) -> dict[str, Any]:
    """Get a specific diagram.

    Args:
        diagram_id: Diagram ID to retrieve

    Returns:
        Diagram details
    """
    if not diagram_id:
        return {
            "success": False,
            "message": "diagram_id is required",
        }

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


@server.tool()
def delete_diagram(diagram_id: str) -> dict[str, Any]:
    """Delete a saved diagram.

    Args:
        diagram_id: Diagram ID to delete

    Returns:
        Deletion result
    """
    if not diagram_id:
        return {
            "success": False,
            "message": "diagram_id is required",
        }

    if storage.delete_diagram(diagram_id):
        return {
            "success": True,
            "message": f"Diagram deleted: {diagram_id}",
        }

    return {
        "success": False,
        "message": f"Diagram not found: {diagram_id}",
    }


def main() -> None:
    """Main entry point for CloudForge"""
    logger.info("🔥 Starting CloudForge - AI-Powered AWS Architecture Diagrams")
    server.run()


if __name__ == "__main__":
    main()
