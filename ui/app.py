"""CloudForge Streamlit Web UI

Interactive interface for generating AWS architecture diagrams from natural language.
Displays validation results, blueprints, code, and diagram images.
"""

import os
import sys
import streamlit as st
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.api_client import CloudForgeAPIClient

# Configure page
st.set_page_config(
    page_title="CloudForge",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Get API URL from environment or use default
API_URL = os.getenv("CLOUDFORGE_API_URL", "http://localhost:8000")

# Initialize API client
api_client = CloudForgeAPIClient(base_url=API_URL)

# Build browser-accessible image URL (convert api:8000 to localhost:8000 for browser access)
def get_browser_image_url(filename: str) -> str:
    """Get image URL that works in the browser.

    Converts internal Docker hostname (api:8000) to localhost:8000 for browser access.
    This ensures images can be displayed whether accessed locally or via Docker.

    Args:
        filename: Image filename from API response

    Returns:
        Full URL accessible from the browser
    """
    if "api:8000" in API_URL:
        # Convert Docker internal hostname to localhost for browser
        browser_url = API_URL.replace("api:8000", "localhost:8000")
        return f"{browser_url}/images/{filename}"
    # For local development, use API_URL as-is
    return f"{API_URL}/images/{filename}"

# Initialize session state
if "current_diagram" not in st.session_state:
    st.session_state.current_diagram = None
if "api_status" not in st.session_state:
    st.session_state.api_status = None


# ============================================================================
# Utility Functions
# ============================================================================


def render_validation_panel(validation: dict) -> None:
    """Render AST validation panel.
    
    Args:
        validation: Validation response from API
    """
    if not validation:
        return

    st.markdown("### ✔️ Validation Results")

    # Status badge
    if validation.get("is_valid"):
        st.success("✅ Code validation passed")
    else:
        st.error("❌ Code validation failed")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Components", validation.get("component_count", 0))
    with col2:
        st.metric("Relationships", validation.get("relationship_count", 0))
    with col3:
        st.metric("Errors", len(validation.get("errors", [])))
    with col4:
        st.metric("Warnings", len(validation.get("warnings", [])))

    # Errors
    errors = validation.get("errors", [])
    if errors:
        with st.expander(f"❌ Errors ({len(errors)})"):
            for error in errors:
                st.error(f"**{error.get('field', 'Unknown')}**: {error.get('message', 'No message')}")

    # Warnings
    warnings = validation.get("warnings", [])
    if warnings:
        with st.expander(f"⚠️ Warnings ({len(warnings)})"):
            for warning in warnings:
                st.warning(f"**{warning.get('field', 'Unknown')}**: {warning.get('message', 'No message')}")


def render_diagram_image(output_files: dict) -> None:
    """Render diagram image with expander for full size.
    
    Args:
        output_files: Dict of format -> file path from API
    """
    if not output_files or "png" not in output_files:
        st.warning("No diagram image available")
        return

    png_path = output_files.get("png", "")
    if not png_path:
        return

    # Get image URL that works in the browser (handles Docker hostname conversion)
    png_url = get_browser_image_url(Path(png_path).name)

    # Display thumbnail in columns
    col_thumb, col_expand = st.columns([3, 1])

    with col_thumb:
        st.image(png_url, use_column_width=True, caption="AWS Architecture Diagram")

    with col_expand:
        if st.button("🔍 Expand", key="expand_image"):
            st.session_state.show_full_image = True

    # Show full size in expander if requested
    if st.session_state.get("show_full_image"):
        with st.expander("Full Size Diagram", expanded=True):
            st.image(png_url, use_column_width=True)


def render_blueprint_panel(blueprint: dict) -> None:
    """Render blueprint details panel.
    
    Args:
        blueprint: Blueprint dict from API
    """
    if not blueprint:
        return

    with st.expander("📋 Technical Blueprint"):
        st.markdown(f"**Title**: {blueprint.get('title', 'N/A')}")
        st.markdown(f"**Description**: {blueprint.get('description', 'N/A')}")

        if blueprint.get("nodes"):
            st.markdown("**Services**:")
            for node in blueprint.get("nodes", []):
                st.markdown(
                    f"- {node.get('name')} ({node.get('service_type')}) "
                    f"[{node.get('region', 'default')}]"
                )

        if blueprint.get("relationships"):
            st.markdown("**Connections**:")
            for rel in blueprint.get("relationships", []):
                st.markdown(
                    f"- {rel.get('source')} → {rel.get('destination')} "
                    f"({rel.get('connection_type', 'default')})"
                )


def render_code_panel(code: str) -> None:
    """Render generated Python code panel.
    
    Args:
        code: Generated Python code
    """
    if not code:
        return

    with st.expander("💻 Generated Code"):
        st.code(code, language="python")


def render_history_panel() -> None:
    """Render recent diagrams history panel."""
    st.markdown("### 📚 Recent Diagrams")

    history = api_client.list_diagrams()
    diagrams = history.get("diagrams", [])

    if not diagrams:
        st.info("No diagrams saved yet")
        return

    # Show only last 5
    for diagram in diagrams[:5]:
        col1, col2, col3 = st.columns([2, 1, 1])

        with col1:
            st.markdown(f"**{diagram.get('name')}**")
            st.caption(diagram.get("created_at", "")[:10])

        with col2:
            if st.button("📖 View", key=f"view_{diagram.get('id')}"):
                st.session_state.view_diagram_id = diagram.get("id")
                st.rerun()

        with col3:
            if st.button("🗑️ Delete", key=f"delete_{diagram.get('id')}"):
                api_client.delete_diagram(diagram.get("id"))
                st.success("Diagram deleted")
                st.rerun()


# ============================================================================
# Main UI
# ============================================================================


def main():
    """Main Streamlit application."""
    st.markdown("# 🏗️ CloudForge - AI-Powered AWS Architecture Diagrams")
    st.markdown(
        "Generate AWS architecture diagrams from natural language descriptions "
        "with automated validation and code generation."
    )

    # Check API status
    health = api_client.health_check()
    st.session_state.api_status = health

    if health.get("status") == "error":
        st.error(
            f"❌ API Connection Failed: {health.get('message')}\n\n"
            f"Make sure the API is running:\n"
            f"```\n"
            f"uvicorn src.api:app --host 0.0.0.0 --port 8000\n"
            f"```"
        )
        return

    if not health.get("pipeline_enabled"):
        st.warning(
            "⚠️ LangGraph Pipeline not available. "
            "Set GOOGLE_API_KEY environment variable to enable diagram generation."
        )

    # Create two columns: main content and sidebar
    col_main, col_sidebar = st.columns([3, 1])

    # ========================================================================
    # Main Column: Editor and Results
    # ========================================================================

    with col_main:
        st.markdown("## 📝 Describe Your Architecture")

        # Input form
        col_desc, col_name = st.columns([2, 1])

        with col_desc:
            description = st.text_area(
                "Architecture Description",
                height=150,
                placeholder=(
                    "Example: IoT system with Kinesis for data ingestion, "
                    "Lambda for processing, and DynamoDB for storage"
                ),
            )

        with col_name:
            diagram_name = st.text_input(
                "Diagram Name",
                placeholder="my_architecture",
            )

        # Generate button
        if st.button("🚀 Generate Architecture", type="primary", use_container_width=True):
            if not description or not diagram_name:
                st.error("Please provide both description and diagram name")
            elif not health.get("pipeline_enabled"):
                st.error("LangGraph Pipeline not available")
            else:
                with st.spinner("🤖 Generating diagram..."):
                    result = api_client.generate_diagram(description, diagram_name)
                    st.session_state.current_diagram = result

                    if result.get("success"):
                        st.success("✅ Diagram generated successfully!")
                    else:
                        st.error(f"❌ Generation failed: {result.get('message')}")

        # Display results if available
        if st.session_state.current_diagram:
            result = st.session_state.current_diagram

            if result.get("success"):
                st.markdown("---")
                st.markdown("## 🎨 Generated Diagram")

                render_diagram_image(result.get("output_files", {}))

                st.markdown("## 📊 Analysis")

                # Validation panel
                validation = result.get("validation")
                if validation:
                    render_validation_panel(validation)

                st.markdown("---")

                # Blueprint and code panels
                col_blue, col_code = st.columns([1, 1])
                with col_blue:
                    render_blueprint_panel(result.get("blueprint"))
                with col_code:
                    render_code_panel(result.get("code"))

    # ========================================================================
    # Sidebar: History and Status
    # ========================================================================

    with col_sidebar:
        st.markdown("## 📡 Status")

        if health.get("pipeline_enabled"):
            st.success("✅ Pipeline Ready")
        else:
            st.warning("⚠️ Pipeline Unavailable")

        st.markdown("---")

        render_history_panel()


if __name__ == "__main__":
    main()
