"""CloudForge Streamlit UI - Web interface for AWS architecture diagram generation"""

import os
import sys
from pathlib import Path

import streamlit as st
from api_client import CloudForgeAPIClient

# Set page configuration
st.set_page_config(
    page_title="CloudForge",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Add custom CSS
st.markdown(
    """
    <style>
    .validation-panel {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-top: 1rem;
    }
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize API client
# Use api:8000 for requests from Docker, localhost:8000 for browser access to images
api_base_url = os.getenv("CLOUDFORGE_API_URL", "http://localhost:8000")
api_client = CloudForgeAPIClient(base_url=api_base_url)

# For images, always use localhost since the browser needs to access it
# (even when running in Docker)
image_base_url = os.getenv("CLOUDFORGE_IMAGE_URL", "http://localhost:8000")

# Initialize session state
if "current_diagram" not in st.session_state:
    st.session_state.current_diagram = None
if "generation_in_progress" not in st.session_state:
    st.session_state.generation_in_progress = False
if "pending_generation" not in st.session_state:
    st.session_state.pending_generation = False
if "pending_description" not in st.session_state:
    st.session_state.pending_description = ""
if "pending_name" not in st.session_state:
    st.session_state.pending_name = ""


# ============================================================================
# Header
# ============================================================================


def render_header():
    """Render page header"""
    st.markdown(
        """
    # 🔥 CloudForge
    ### AI-Powered AWS Architecture Diagram Generator
    Generate professional AWS architecture diagrams from natural language descriptions.
    """
    )


# ============================================================================
# Main Editor Panel
# ============================================================================


def _handle_generate_click(description: str, diagram_name: str):
    """Callback for Generate button - stores pending request in session state

    Args:
        description: Architecture description
        diagram_name: Diagram name
    """
    if not description or not description.strip():
        st.error("Please enter an architecture description")
        return
    if not diagram_name or not diagram_name.strip():
        st.error("Please enter a diagram name")
        return

    # Store pending request
    st.session_state.pending_description = description.strip()
    st.session_state.pending_name = diagram_name.strip()
    st.session_state.pending_generation = True


def render_editor_panel():
    """Render the main diagram editor panel"""
    st.markdown("## 📝 Architecture Description")

    description = st.text_area(
        "Describe your AWS architecture:",
        height=200,
        placeholder="Example: An IoT system where sensors send data to Kinesis, which triggers Lambda functions that process and store results in DynamoDB, with CloudWatch monitoring.",
        label_visibility="collapsed",
        key="editor_description",
    )

    diagram_name = st.text_input(
        "Diagram Name:",
        placeholder="e.g., iot_pipeline, microservices_app, etc.",
        label_visibility="collapsed",
        key="editor_name",
    )

    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        st.button(
            "🚀 Generate Architecture",
            use_container_width=True,
            type="primary",
            on_click=_handle_generate_click,
            args=(description, diagram_name),
            disabled=st.session_state.generation_in_progress,
        )

    with col2:
        st.button(
            "🔄 Reset",
            use_container_width=True,
            on_click=lambda: st.session_state.update({
                "current_diagram": None,
                "pending_generation": False,
                "pending_description": "",
                "pending_name": "",
            }),
            disabled=st.session_state.generation_in_progress,
        )

    with col3:
        api_status = "✅ Connected" if api_client.health_check() else "❌ Offline"
        st.info(api_status, icon="🔌")

    return description, diagram_name


# ============================================================================
# Validation Panel
# ============================================================================


def render_validation_panel(diagram: dict):
    """Render AST validation panel with complete analysis

    Args:
        diagram: The generated diagram response dictionary
    """
    if not diagram or not diagram.get("validation"):
        return

    st.markdown("## ✔️ Code Validation (AST Analysis)")

    validation = diagram.get("validation", {})

    # Overall status
    if validation.get("is_valid"):
        st.success("✅ Code validation passed", icon="✅")
    else:
        st.error("❌ Validation failed", icon="❌")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Components",
            validation.get("component_count", 0),
            help="Number of AWS components detected",
        )

    with col2:
        st.metric(
            "Relationships",
            validation.get("relationship_count", 0),
            help="Number of connections between components",
        )

    with col3:
        error_count = len(validation.get("errors", []))
        st.metric(
            "Errors",
            error_count,
            help="Critical issues that prevent diagram generation",
        )

    with col4:
        warning_count = len(validation.get("warnings", []))
        st.metric(
            "Warnings",
            warning_count,
            help="Non-critical issues and security concerns",
        )

    # Errors
    errors = validation.get("errors", [])
    if errors:
        st.error(f"**{len(errors)} Validation Error(s):**")
        for error in errors:
            with st.expander(f"❌ {error.get('field', 'Unknown')}"):
                st.write(f"**Message:** {error.get('message', 'No message')}")
                st.write(f"**Severity:** {error.get('severity', 'unknown')}")

    # Warnings
    warnings = validation.get("warnings", [])
    if warnings:
        st.warning(f"**{len(warnings)} Warning(s):**")
        for warning in warnings:
            with st.expander(f"⚠️ {warning.get('field', 'Unknown')}"):
                st.write(f"**Message:** {warning.get('message', 'No message')}")
                st.write(f"**Severity:** {warning.get('severity', 'unknown')}")

    # Security analysis
    security_warnings = [
        w for w in warnings if w.get("field") == "security"
    ]
    if security_warnings:
        with st.expander("🔒 Security Analysis"):
            for sw in security_warnings:
                st.warning(sw.get("message", "No message"))


# ============================================================================
# Code Panel
# ============================================================================


def render_code_panel(diagram: dict):
    """Render generated code panel

    Args:
        diagram: The generated diagram response dictionary
    """
    if not diagram or not diagram.get("code"):
        return

    st.markdown("## 💻 Generated Python Code")

    code = diagram.get("code", "")

    with st.expander("View Generated Code", expanded=False):
        st.code(code, language="python")

        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇️ Download Code",
                code,
                file_name=f"{diagram.get('name', 'diagram')}.py",
                mime="text/plain",
            )


# ============================================================================
# Blueprint Panel
# ============================================================================


def render_blueprint_panel(diagram: dict):
    """Render technical blueprint panel

    Args:
        diagram: The generated diagram response dictionary
    """
    if not diagram or not diagram.get("blueprint"):
        return

    st.markdown("## 📋 Technical Blueprint")

    blueprint = diagram.get("blueprint", "")

    with st.expander("View Technical Blueprint", expanded=False):
        st.markdown(blueprint)


# ============================================================================
# Image Display Panel
# ============================================================================


def render_image_panel(diagram: dict):
    """Render generated diagram images

    Args:
        diagram: The generated diagram response dictionary
    """
    if not diagram or not diagram.get("output_files"):
        return

    st.markdown("## 🖼️ Generated Diagram")

    output_files = diagram.get("output_files", {})

    # Display PNG if available
    if "png" in output_files:
        # Use image_base_url for browser access, not api_base_url
        png_url = f"{image_base_url}{output_files['png']}"
        try:
            st.image(png_url, caption="Architecture Diagram (PNG)")
        except Exception as e:
            st.error(f"Failed to load PNG image: {str(e)}")
            # Show debug info if image fails to load
            with st.expander("📍 Debug Info"):
                st.write(f"URL attempted: {png_url}")
                st.write(f"API URL: {api_base_url}")
                st.write(f"Image URL: {image_base_url}")

    # Download options for other formats
    col1, col2 = st.columns(2)

    with col1:
        if "pdf" in output_files:
            pdf_url = f"{image_base_url}{output_files['pdf']}"
            st.markdown(f"[📄 Download PDF]({pdf_url})")

    with col2:
        if "svg" in output_files:
            svg_url = f"{image_base_url}{output_files['svg']}"
            st.markdown(f"[🎨 Download SVG]({svg_url})")


# ============================================================================
# History Panel
# ============================================================================


def render_history_panel():
    """Render recent diagrams history panel"""
    st.markdown("## 📚 Recent Diagrams")

    try:
        history_response = api_client.get_history()

        if not history_response.get("success"):
            st.info("No diagrams found yet")
            return

        diagrams = history_response.get("diagrams", [])

        if not diagrams:
            st.info("No diagrams in history")
            return

        for diagram_info in diagrams[:5]:
            with st.expander(
                f"📊 {diagram_info.get('name', 'Unnamed')} - {diagram_info.get('created_at', '')[:10]}"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.metric(
                        "Errors",
                        diagram_info.get("error_count", 0),
                    )

                with col2:
                    st.metric(
                        "Warnings",
                        diagram_info.get("warning_count", 0),
                    )

                if st.button(
                    "Load",
                    key=f"load_{diagram_info.get('id')}",
                ):
                    # Load the diagram
                    load_response = api_client.get_diagram(diagram_info.get("id"))
                    if load_response.get("success"):
                        st.session_state.current_diagram = load_response
                        st.rerun()
                    else:
                        st.error(
                            f"Failed to load diagram: {load_response.get('message')}"
                        )

    except Exception as e:
        st.error(f"Failed to load history: {str(e)}")


# ============================================================================
# Main Application
# ============================================================================


def main():
    """Main application entry point"""
    render_header()

    # Handle pending generation request
    if st.session_state.pending_generation:
        st.session_state.generation_in_progress = True

        # Use columns to contain the spinner
        col_spinner, _ = st.columns([1, 2])

        with col_spinner:
            with st.spinner("🔄 Generating diagram..."):
                result = api_client.generate_diagram(
                    st.session_state.pending_description,
                    st.session_state.pending_name,
                )

        # Reset pending flag
        st.session_state.pending_generation = False
        st.session_state.generation_in_progress = False

        # Handle result
        if result.get("success"):
            st.session_state.current_diagram = result
            st.success("✅ Diagram generated successfully!")
            st.rerun()
        else:
            st.error(
                f"❌ Generation failed: {result.get('message', 'Unknown error')}"
            )

    # Main content area
    tab1, tab2 = st.tabs(["🚀 Generator", "📚 History"])

    with tab1:
        # Left column - Editor
        col_left, col_right = st.columns([1, 2])

        with col_left:
            description, diagram_name = render_editor_panel()

        with col_right:
            if st.session_state.current_diagram:
                render_image_panel(st.session_state.current_diagram)
            else:
                st.info("👈 Enter a description and click Generate to create a diagram")

        # Show validation panel if diagram exists
        if st.session_state.current_diagram:
            st.divider()
            render_validation_panel(st.session_state.current_diagram)

            st.divider()
            col_code, col_blueprint = st.columns(2)

            with col_code:
                render_code_panel(st.session_state.current_diagram)

            with col_blueprint:
                render_blueprint_panel(st.session_state.current_diagram)

    with tab2:
        render_history_panel()

    # Footer
    st.divider()
    st.markdown(
        """
    ---
    **CloudForge** | AI-Powered AWS Architecture Diagram Generator
    """
    )


if __name__ == "__main__":
    main()
