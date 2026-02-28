"""CloudForge Streamlit Web UI

Interactive interface for generating AWS architecture diagrams from natural language.
Two-step process: Refine Description → Review → Generate Diagram
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

# Build browser-accessible image URL
def get_browser_image_url(filename: str) -> str:
    """Get image URL that works in the browser.

    Converts internal Docker hostname (api:8000) to localhost:8000 for browser access.
    """
    if "api:8000" in API_URL:
        browser_url = API_URL.replace("api:8000", "localhost:8000")
        return f"{browser_url}/images/{filename}"
    return f"{API_URL}/images/{filename}"

# Initialize session state
if "original_description" not in st.session_state:
    st.session_state.original_description = ""
if "refined_description" not in st.session_state:
    st.session_state.refined_description = ""
if "current_diagram" not in st.session_state:
    st.session_state.current_diagram = None
if "step" not in st.session_state:
    st.session_state.step = "input"  # input → review → generated
if "detected_patterns" not in st.session_state:
    st.session_state.detected_patterns = []
if "recommended_services" not in st.session_state:
    st.session_state.recommended_services = []


# ============================================================================
# Utility Functions
# ============================================================================


def render_validation_panel(validation: dict) -> None:
    """Render AST validation panel."""
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


def render_blueprint_panel(blueprint: dict) -> None:
    """Render blueprint panel."""
    if not blueprint:
        return

    st.markdown("### 📋 Architecture Blueprint")

    # Blueprint info
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Title**: {blueprint.get('title', 'N/A')}")
    with col2:
        st.markdown(f"**Services**: {len(blueprint.get('nodes', []))}")

    # Services
    with st.expander("📊 Services Detected"):
        nodes = blueprint.get("nodes", [])
        for node in nodes:
            st.markdown(f"- **{node.get('name')}** ({node.get('service_type')})")

    # Relationships
    if blueprint.get("relationships"):
        with st.expander("🔗 Relationships"):
            rels = blueprint.get("relationships", [])
            for rel in rels:
                st.markdown(f"- {rel.get('source')} → {rel.get('destination')} [{rel.get('connection_type')}]")

    # Best practices
    if blueprint.get("best_practices"):
        with st.expander("🎯 AWS Best Practices"):
            for practice in blueprint.get("best_practices", []):
                st.markdown(f"✓ {practice}")


def render_code_panel(code: str) -> None:
    """Render generated code panel."""
    if not code:
        return

    st.markdown("### 💻 Generated Code")
    st.code(code, language="python")


# ============================================================================
# Main UI Layout
# ============================================================================

# Header
st.markdown("# 🏗️ CloudForge - AWS Architecture Diagram Generator")
st.markdown("Generate professional AWS architecture diagrams from natural language descriptions.")

# Tabs for different sections
tab1, tab2, tab3 = st.tabs(["📝 Generate", "📚 History", "ℹ️ About"])

with tab1:
    # Two-step workflow
    col_left, col_right = st.columns([2, 1], gap="large")

    with col_left:
        st.markdown("## Step 1: Describe Your Architecture")
        st.markdown("*Enter a brief or detailed description of your AWS architecture*")

        # Input area
        user_input = st.text_area(
            "Architecture Description:",
            value=st.session_state.original_description,
            height=150,
            placeholder="Example: API Gateway with Lambda processing and DynamoDB storage\n\nOr brief: Lambda, API, DB",
            key="description_input",
        )

        diagram_name = st.text_input(
            "Diagram Name:",
            value="my_architecture",
            placeholder="e.g., serverless_api",
        )

        # Step 1: Refine Button
        if st.button("🔧 Refine Prompt", type="primary", use_container_width=True):
            if not user_input.strip():
                st.error("❌ Please enter an architecture description")
            else:
                st.session_state.original_description = user_input

                with st.spinner("✨ Refining description..."):
                    try:
                        refine_result = api_client.refine_description(user_input)

                        if refine_result.get("success"):
                            st.session_state.refined_description = refine_result.get("refined", "")
                            st.session_state.detected_patterns = refine_result.get("patterns", [])
                            st.session_state.recommended_services = refine_result.get("recommended_services", [])
                            st.session_state.step = "review"
                            st.rerun()
                        else:
                            st.error(f"❌ Refinement failed: {refine_result.get('message')}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")

    with col_right:
        st.markdown("### 📊 Workflow Status")

        # Status indicators
        if st.session_state.step == "input":
            st.info("📝 **Step 1**: Describe your architecture")
        elif st.session_state.step == "review":
            st.info("✅ **Step 1**: Complete\n📋 **Step 2**: Review refined prompt")
        elif st.session_state.step == "generated":
            st.success("✅ **All Steps**: Complete")

    # Step 2: Review Refined Description
    if st.session_state.step in ["review", "generated"]:
        st.divider()
        st.markdown("## Step 2: Review & Approve Refined Description")
        st.markdown("*The AI has enhanced your description with architectural details*")

        with st.expander("📋 Original Description", expanded=False):
            st.markdown(f"```\n{st.session_state.original_description}\n```")

        # Show detected AWS patterns
        if st.session_state.detected_patterns:
            st.markdown("### 🎯 Detected AWS Architecture Patterns")
            pattern_cols = st.columns(min(len(st.session_state.detected_patterns), 4))
            for i, pattern in enumerate(st.session_state.detected_patterns):
                with pattern_cols[i % len(pattern_cols)]:
                    st.success(f"**{pattern}**")

        if st.session_state.recommended_services:
            with st.expander("🔧 Recommended AWS Services (from Pattern Analysis)", expanded=False):
                svc_cols = st.columns(2)
                for i, svc in enumerate(st.session_state.recommended_services):
                    with svc_cols[i % 2]:
                        st.markdown(f"**{svc.get('service', '')}**")
                        st.caption(svc.get("role", ""))

        st.markdown("### 🔄 Refined Description (AI Enhanced)")
        st.markdown("*Includes data flows, layers, technical context, and AWS best practices*")

        refined_edited = st.text_area(
            "Edit if needed:",
            value=st.session_state.refined_description,
            height=250,
            key="refined_input",
        )

        st.session_state.refined_description = refined_edited

        # Approval buttons
        col_approve, col_edit = st.columns(2)

        with col_approve:
            if st.button("✅ Looks Good! Generate Diagram", type="primary", use_container_width=True):
                if not diagram_name.strip():
                    st.error("❌ Please enter a diagram name")
                else:
                    st.session_state.step = "generating"
                    st.rerun()

        with col_edit:
            if st.button("✏️ Edit Description", use_container_width=True):
                st.session_state.step = "input"
                st.rerun()

    # Step 3: Generate Diagram
    if st.session_state.step == "generating":
        st.divider()
        st.markdown("## Step 3: Generating Diagram...")

        with st.spinner("🎨 Generating architecture diagram (this may take a moment)..."):
            try:
                result = api_client.generate_diagram(
                    st.session_state.refined_description,
                    diagram_name,
                )

                if result.get("success"):
                    st.session_state.current_diagram = result
                    st.session_state.step = "generated"
                    st.success("✅ Diagram generated successfully!")
                    st.rerun()
                else:
                    st.error(f"❌ Generation failed: {result.get('message')}")
                    if st.button("🔙 Back to Review"):
                        st.session_state.step = "review"
                        st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
                if st.button("🔙 Back to Review"):
                    st.session_state.step = "review"
                    st.rerun()

    # Display Generated Diagram
    if st.session_state.step == "generated" and st.session_state.current_diagram:
        st.divider()
        st.markdown("## 🎉 Architecture Diagram Generated!")

        diagram = st.session_state.current_diagram

        # Diagram image
        output_files = diagram.get("output_files", {})
        if output_files.get("png"):
            png_url = get_browser_image_url(Path(output_files["png"]).name)
            st.image(png_url, use_column_width=True, caption="AWS Architecture Diagram")

        # Tabs for details
        detail_tab1, detail_tab2, detail_tab3, detail_tab4 = st.tabs(
            ["📋 Blueprint", "💻 Code", "✔️ Validation", "📁 Files"]
        )

        with detail_tab1:
            render_blueprint_panel(diagram.get("blueprint"))

        with detail_tab2:
            render_code_panel(diagram.get("code"))

        with detail_tab3:
            render_validation_panel(diagram.get("validation"))

        with detail_tab4:
            st.markdown("### 📁 Generated Files")
            for fmt, path in output_files.items():
                st.markdown(f"✓ **{fmt.upper()}**: `{Path(path).name}`")

        # Action buttons
        col_new, col_export = st.columns(2)
        with col_new:
            if st.button("🆕 Create Another Diagram", use_container_width=True):
                st.session_state.step = "input"
                st.session_state.original_description = ""
                st.session_state.refined_description = ""
                st.session_state.current_diagram = None
                st.session_state.detected_patterns = []
                st.session_state.recommended_services = []
                st.rerun()

        with col_export:
            st.info("💾 Download images from the browser (right-click on diagram)")

with tab2:
    st.markdown("## 📚 Recent Diagrams")
    st.info("Recent diagrams will appear here")
    # TODO: Implement history fetching

with tab3:
    st.markdown("## ℹ️ About CloudForge")
    st.markdown("""
    **CloudForge** is an AI-powered AWS architecture diagram generator.

    ### Features:
    - 🤖 **AI-Powered**: Uses advanced LLM to understand architecture descriptions
    - 🔧 **Smart Refinement**: Automatically enhances vague descriptions with technical details
    - 📚 **AWS Best Practices**: Integrates AWS documentation for recommended patterns
    - ✅ **Validation**: Validates generated code for security and structure
    - 🎨 **Beautiful Diagrams**: Generates professional-quality architecture diagrams

    ### Two-Step Workflow:
    1. **Refine**: Describe your architecture (brief or detailed)
    2. **Review**: Approve the AI-enhanced description
    3. **Generate**: Get your diagram instantly

    ### Supported AWS Services:
    Lambda, API Gateway, RDS, DynamoDB, S3, CloudFront, Kinesis, SQS, SNS,
    CloudWatch, IAM, and many more!

    ---
    Made with ❤️ by the CloudForge team
    """)
