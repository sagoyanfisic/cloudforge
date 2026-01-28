"""LangGraph Pipeline for CloudForge

Orchestrates the complete diagram generation pipeline with:
- State machine for reliable orchestration
- Automatic error recovery and retries
- Fallback mechanisms (AWS MCP as backup)
- Structured error handling
"""

import logging
from typing import TypedDict, Optional, Any
from datetime import datetime

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel, Field

from .langchain_chains import BlueprintArchitectChain, DiagramCoderChain
from ..infrastructure.validator import DiagramValidator
from ..infrastructure.generator import DiagramGenerator
from .aws_mcp_client import get_aws_documentation_client

logger = logging.getLogger(__name__)


# ============================================================================
# State Definition
# ============================================================================


class DiagramPipelineState(TypedDict):
    """Complete pipeline state"""
    # Input
    description: str
    diagram_name: str

    # Pipeline stages
    blueprint: Optional[dict[str, Any]]
    code: Optional[str]
    validation: Optional[dict[str, Any]]
    output_files: Optional[dict[str, str]]

    # Error tracking
    errors: list[str]
    retry_count: int
    max_retries: int

    # Metadata
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    success: bool


# ============================================================================
# Node Functions
# ============================================================================


def blueprint_node(state: DiagramPipelineState) -> DiagramPipelineState:
    """Generate blueprint from description

    Args:
        state: Current pipeline state

    Returns:
        Updated state with blueprint
    """
    logger.info("📋 Node: Blueprint Generation")

    last_error = None
    while state["retry_count"] <= state["max_retries"]:
        try:
            chain = BlueprintArchitectChain()
            blueprint = chain.invoke(state["description"])

            state["blueprint"] = blueprint
            logger.info(f"✅ Blueprint generated: {len(blueprint.get('nodes', []))} nodes")
            return state

        except Exception as e:
            last_error = e
            error_msg = f"Blueprint generation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["retry_count"] += 1
            logger.info(f"🔄 Retrying... (attempt {state['retry_count']}/{state['max_retries']})")

    raise ValueError(f"Blueprint generation failed after {state['max_retries']} retries: {last_error}")


def enrich_mcp_node(state: DiagramPipelineState) -> DiagramPipelineState:
    """Enrich blueprint with AWS best practices from Documentation MCP

    Args:
        state: Current pipeline state with blueprint

    Returns:
        Updated state with enriched blueprint
    """
    logger.info("🔍 Node: AWS MCP Enrichment")

    if not state.get("blueprint"):
        logger.debug("⏭️ Skipping AWS MCP enrichment: No blueprint available")
        return state

    try:
        import os

        # Check if AWS MCP is enabled
        if os.getenv("CLOUDFORGE_DISABLE_AWS_MCP", "1") == "1":
            logger.debug("⏭️ AWS MCP enrichment disabled (CLOUDFORGE_DISABLE_AWS_MCP=1)")
            return state

        # Extract services from blueprint
        blueprint = state["blueprint"]
        services = []

        if isinstance(blueprint, dict) and "nodes" in blueprint:
            services = [node.get("service_type") for node in blueprint["nodes"] if isinstance(node, dict)]

        if not services:
            logger.debug("⏭️ No services found in blueprint, skipping enrichment")
            return state

        logger.info(f"📚 Extracting best practices for: {', '.join(set(services))}")

        # Consult AWS Documentation MCP
        doc_client = get_aws_documentation_client()

        if not doc_client.is_connected():
            if not doc_client.connect():
                logger.debug("ℹ️ AWS Documentation MCP not available (optional feature)")
                return state

        # Enrich with best practices
        best_practices_list = []
        unique_services = set(services)

        for service in list(unique_services)[:3]:  # Limit to 3 services
            try:
                # Build query
                query = f"best practices for {service} in cloud architecture"
                result = doc_client.search_documentation(query)

                if result and result.get("success"):
                    practice = result.get("content", f"Best practices for {service}")
                    best_practices_list.append(f"- {service}: {practice[:100]}...")
                    logger.debug(f"✅ Got best practices for {service}")
            except Exception as e:
                logger.debug(f"⚠️ Could not get best practices for {service}: {str(e)}")
                continue

        # Enrich blueprint with best practices
        if isinstance(blueprint, dict):
            if "best_practices" not in blueprint:
                blueprint["best_practices"] = []

            blueprint["best_practices"].extend(best_practices_list)
            state["blueprint"] = blueprint

            if best_practices_list:
                logger.info(f"✅ Enriched blueprint with {len(best_practices_list)} best practices")

        doc_client.close()

    except Exception as e:
        logger.warning(f"⚠️ AWS MCP enrichment warning: {str(e)}")
        # Don't fail the pipeline, just skip enrichment
        pass

    return state


def coder_node(state: DiagramPipelineState) -> DiagramPipelineState:
    """Generate Python code from blueprint

    Args:
        state: Current pipeline state

    Returns:
        Updated state with code
    """
    logger.info("💻 Node: Code Generation")

    if not state.get("blueprint"):
        error_msg = "No blueprint available for code generation"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        raise ValueError(error_msg)

    last_error = None
    while state["retry_count"] <= state["max_retries"]:
        try:
            chain = DiagramCoderChain()
            code = chain.invoke(state["blueprint"])

            state["code"] = code
            logger.info(f"✅ Code generated: {len(code)} characters")
            return state

        except Exception as e:
            last_error = e
            error_msg = f"Code generation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["retry_count"] += 1
            logger.info(f"🔄 Retrying... (attempt {state['retry_count']}/{state['max_retries']})")

    raise ValueError(f"Code generation failed after {state['max_retries']} retries: {last_error}")


def validator_node(state: DiagramPipelineState) -> DiagramPipelineState:
    """Validate generated code

    Args:
        state: Current pipeline state

    Returns:
        Updated state with validation results
    """
    logger.info("✔️ Node: Validation")

    if not state.get("code"):
        error_msg = "No code available for validation"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        raise ValueError(error_msg)

    try:
        validator = DiagramValidator()
        validation = validator.validate(state["code"])

        state["validation"] = {
            "is_valid": validation.is_valid,
            "errors": [{"field": e.field, "message": e.message} for e in validation.errors],
            "warnings": [{"field": w.field, "message": w.message} for w in validation.warnings],
            "component_count": validation.component_count,
            "relationship_count": validation.relationship_count,
        }

        if validation.is_valid:
            logger.info(f"✅ Validation passed: {validation.component_count} components")
        else:
            error_msg = f"Validation failed: {len(validation.errors)} errors"
            logger.warning(f"⚠️ {error_msg}")
            state["errors"].append(error_msg)

            # Don't fail, continue to generation (may still work)

    except Exception as e:
        error_msg = f"Validation error: {str(e)}"
        logger.warning(f"⚠️ {error_msg}")
        state["errors"].append(error_msg)

    return state


def generator_node(state: DiagramPipelineState) -> DiagramPipelineState:
    """Generate diagram from code

    Args:
        state: Current pipeline state

    Returns:
        Updated state with output files
    """
    logger.info("🎨 Node: Diagram Generation")

    if not state.get("code"):
        error_msg = "No code available for diagram generation"
        logger.error(f"❌ {error_msg}")
        state["errors"].append(error_msg)
        raise ValueError(error_msg)

    last_error = None
    while state["retry_count"] <= state["max_retries"]:
        try:
            generator = DiagramGenerator()
            output_files = generator.generate(
                state["code"],
                state["diagram_name"],
                ["png", "pdf", "svg"],
            )

            state["output_files"] = output_files
            logger.info(f"✅ Diagram generated: {len(output_files)} formats")
            return state

        except Exception as e:
            last_error = e
            error_msg = f"Diagram generation failed: {str(e)}"
            logger.error(f"❌ {error_msg}")
            state["errors"].append(error_msg)
            state["retry_count"] += 1
            logger.info(f"🔄 Retrying... (attempt {state['retry_count']}/{state['max_retries']})")

    raise ValueError(f"Diagram generation failed after {state['max_retries']} retries: {last_error}")


# ============================================================================
# Graph Builder
# ============================================================================


def build_pipeline_graph():
    """Build the complete LangGraph pipeline

    Returns:
        Compiled graph ready to invoke
    """
    logger.info("🔧 Building LangGraph pipeline...")

    # Create graph
    graph = StateGraph(DiagramPipelineState)

    # Add nodes
    graph.add_node("blueprint", blueprint_node)
    graph.add_node("enrich_mcp", enrich_mcp_node)
    graph.add_node("coder", coder_node)
    graph.add_node("validator", validator_node)
    graph.add_node("generator", generator_node)

    # Add edges
    # blueprint → enrich_mcp → coder → validator → generator
    graph.add_edge(START, "blueprint")
    graph.add_edge("blueprint", "enrich_mcp")
    graph.add_edge("enrich_mcp", "coder")
    graph.add_edge("coder", "validator")
    graph.add_edge("validator", "generator")
    graph.add_edge("generator", END)

    # Compile
    compiled_graph = graph.compile()
    logger.info("✅ Pipeline built successfully")

    return compiled_graph


# ============================================================================
# Pipeline Executor
# ============================================================================


class DiagramPipeline:
    """High-level pipeline executor"""

    def __init__(self, max_retries: int = 3):
        """Initialize pipeline

        Args:
            max_retries: Maximum retry attempts
        """
        self.graph = build_pipeline_graph()
        self.max_retries = max_retries

    def generate(self, description: str, diagram_name: str) -> dict[str, Any]:
        """Execute complete pipeline

        Args:
            description: Architecture description
            diagram_name: Diagram name

        Returns:
            dict: Complete result with blueprint, code, validation, outputs

        Raises:
            ValueError: If pipeline fails
        """
        logger.info(f"🚀 Starting pipeline for: {diagram_name}")

        initial_state: DiagramPipelineState = {
            "description": description,
            "diagram_name": diagram_name,
            "blueprint": None,
            "code": None,
            "validation": None,
            "output_files": None,
            "errors": [],
            "retry_count": 0,
            "max_retries": self.max_retries,
            "started_at": datetime.utcnow(),
            "completed_at": None,
            "success": False,
        }

        try:
            # Run pipeline
            final_state = self.graph.invoke(initial_state)

            # Check success
            if final_state.get("output_files"):
                final_state["success"] = True
                final_state["completed_at"] = datetime.utcnow()
                logger.info(f"✅ Pipeline completed successfully")

                return {
                    "success": True,
                    "blueprint": final_state.get("blueprint"),
                    "code": final_state.get("code"),
                    "validation": final_state.get("validation"),
                    "output_files": final_state.get("output_files"),
                    "errors": final_state.get("errors"),
                }
            else:
                raise ValueError("Pipeline completed but no output files generated")

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            return {
                "success": False,
                "errors": initial_state["errors"] + [str(e)],
                "message": str(e),
            }
