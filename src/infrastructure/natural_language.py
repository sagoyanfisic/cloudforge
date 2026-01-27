"""Natural Language to Diagram generation using Google Gemini AI.

This module implements a two-agent system:
1. BlueprintArchitect: Analyzes raw text and creates a structured blueprint
2. DiagramCoder: Generates Python code from the blueprint

Following Clean Code principles: single responsibility, clear naming, error handling.
"""

import logging
import os
import re
import ast
from typing import Optional

import google.generativeai as genai
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class BlueprintNode(BaseModel):
    """Represents a single AWS service node in the architecture."""

    name: str = Field(..., description="Human-readable service name")
    variable: str = Field(..., description="Python variable name")
    service_type: str = Field(..., description="AWS service class (e.g., Lambda, S3)")
    region: Optional[str] = Field(None, description="AWS region")


class BlueprintCluster(BaseModel):
    """Represents a logical grouping of services."""

    name: str = Field(..., description="Cluster name")
    nodes: list[str] = Field(default_factory=list, description="Node variables in cluster")


class BlueprintRelationship(BaseModel):
    """Represents a connection between two services."""

    source: str = Field(..., description="Source node variable")
    destination: str = Field(..., description="Destination node variable")
    connection_type: str = Field(default="default", description="Type of connection")


class ArchitectureBlueprint(BaseModel):
    """Structured technical blueprint extracted from raw text."""

    title: str = Field(..., description="Architecture name")
    description: str = Field(..., description="Brief description")
    nodes: list[BlueprintNode] = Field(default_factory=list)
    clusters: list[BlueprintCluster] = Field(default_factory=list)
    relationships: list[BlueprintRelationship] = Field(default_factory=list)

    def __str__(self) -> str:
        """Format blueprint as text for code generation."""
        output = f"---BEGIN_BLUEPRINT---\n"
        output += f"Title: {self.title}\n"
        output += f"Description: {self.description}\n\n"

        output += "Nodes:\n"
        for node in self.nodes:
            output += f"- {node.name} as {node.variable} (Type: {node.service_type})\n"

        if self.clusters:
            output += "\nClusters:\n"
            for cluster in self.clusters:
                output += f"- {cluster.name} contains {', '.join(cluster.nodes)}\n"

        output += "\nRelationships:\n"
        for rel in self.relationships:
            output += f"- {rel.source} >> {rel.destination}\n"

        output += "---END_BLUEPRINT---\n"
        return output


class BlueprintArchitect:
    """Agent 1: Analyzes raw text and generates structured blueprint.

    Responsibilities:
    - Parse unstructured text
    - Identify AWS services
    - Extract relationships
    - Create technical blueprint
    """

    SYSTEM_PROMPT = """You are the CloudForge Blueprint Architect, an expert solution architect specializing in AWS and the Python `diagrams` library.

GOAL: Transform natural language architectural descriptions into a STRICT, PARSEABLE BLUEPRINT. Your output acts as the instruction set for a code generator.

ANALYSIS PROTOCOL:
1. Scan for Services: Map user requests to specific AWS Service Classes in the `diagrams` library (e.g., "Serverless DB" -> Dynamodb or Aurora).
2. Determine Category: Identify the library module (compute, database, network, storage, integration, analytics).
3. Structure: Group related nodes into logical Clusters (VPC, Subnets, Autoscaling Groups).
4. Flow: Define directional relationships (>>) representing data or traffic flow.

RULES:
1. Valid Classes: Use ONLY valid class names from `diagrams.aws`.
2. Python-Safe IDs: All unique_ids must be lowercase, snake_case, and valid Python variable names (e.g., user_db, not User DB).
3. Inference: If the input is vague (e.g., "a database"), infer the industry standard for the context (e.g., RDS for relational, DynamoDB for high scale) and note it in Metadata.
4. Security: Mark public-facing databases as High Risk in Metadata.

OUTPUT FORMAT (STRICT TEMPLATE - do not add intro/outro text):
---BEGIN_BLUEPRINT---
Title: [Project Name]
Description: [Brief summary]

Nodes:
- [Display Name] | ID: [var_name] | Type: [Class] | Category: [module_name]

Clusters:
- Cluster: [Display Name]
  Type: [Logical/VPC/Subnet]
  Members: [list_of_var_names]

Relationships:
- [source_var] >> [dest_var]

Metadata:
- Inferred_Decisions: [List specific choices made by you, e.g., "Chose RDS for generic SQL request"]
- Security_Risk: [Low/Medium/High]
---END_BLUEPRINT---
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize architect with Gemini API.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
        """
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def analyze(self, raw_text: str) -> ArchitectureBlueprint:
        """Analyze raw text and generate blueprint.

        Args:
            raw_text: Unstructured description of architecture

        Returns:
            ArchitectureBlueprint: Structured technical blueprint

        Raises:
            ValueError: If API call fails or blueprint parsing fails
        """
        logger.info("🏗️ Blueprint Architect analyzing text...")

        try:
            response = self.model.generate_content(
                [self.SYSTEM_PROMPT, f"\nUser input:\n{raw_text}"],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Low for analytical thinking
                    max_output_tokens=2000,
                ),
            )

            blueprint_text = response.text.strip()
            logger.debug(f"Raw response: {blueprint_text}")

            # Extract blueprint from text format
            blueprint_dict = self._parse_blueprint_text(blueprint_text)
            blueprint = ArchitectureBlueprint(**blueprint_dict)

            logger.info(f"✅ Blueprint created: {blueprint.title} ({len(blueprint.nodes)} nodes)")
            return blueprint

        except Exception as e:
            logger.error(f"❌ Blueprint generation failed: {str(e)}")
            raise

    def _parse_blueprint_text(self, text: str) -> dict:
        """Parse text-based blueprint format to dictionary.

        Expected format:
        ---BEGIN_BLUEPRINT---
        Title: [name]
        Description: [desc]
        Nodes:
        - [Service Name] as [var_name] (Type: [ServiceType])
        Clusters:
        - [Cluster Name] contains [var1, var2, ...]
        Relationships:
        - [source_var] >> [dest_var]
        ---END_BLUEPRINT---

        Args:
            text: Blueprint text to parse

        Returns:
            dict: Parsed blueprint as dictionary

        Raises:
            ValueError: If blueprint format is invalid
        """
        # Extract content between markers
        start_marker = "---BEGIN_BLUEPRINT---"
        end_marker = "---END_BLUEPRINT---"

        start_idx = text.find(start_marker)
        end_idx = text.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            raise ValueError(f"Blueprint markers not found in response")

        blueprint_content = text[start_idx + len(start_marker) : end_idx].strip()

        # Parse sections
        blueprint_dict = {
            "title": "",
            "description": "",
            "nodes": [],
            "clusters": [],
            "relationships": [],
        }

        current_section = None
        lines = blueprint_content.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if line.startswith("Title:"):
                blueprint_dict["title"] = line[6:].strip()
            elif line.startswith("Description:"):
                blueprint_dict["description"] = line[12:].strip()
            elif line == "Nodes:":
                current_section = "nodes"
            elif line == "Clusters:":
                current_section = "clusters"
            elif line == "Relationships:":
                current_section = "relationships"
            elif line.startswith("-") and current_section:
                content = line[1:].strip()

                if current_section == "nodes":
                    # Parse: [Service Name] as [var_name] (Type: [ServiceType])
                    match = re.search(
                        r"^(.+?)\s+as\s+(\w+)\s+\(Type:\s+(.+?)\)$", content
                    )
                    if match:
                        blueprint_dict["nodes"].append(
                            {
                                "name": match.group(1),
                                "variable": match.group(2),
                                "service_type": match.group(3),
                                "region": None,
                            }
                        )

                elif current_section == "clusters":
                    # Parse: [Cluster Name] contains [var1, var2, ...]
                    match = re.search(r"^(.+?)\s+contains\s+(.+)$", content)
                    if match:
                        vars_str = match.group(2)
                        vars_list = [v.strip() for v in vars_str.split(",")]
                        blueprint_dict["clusters"].append(
                            {"name": match.group(1), "nodes": vars_list}
                        )

                elif current_section == "relationships":
                    # Parse: [source_var] >> [dest_var]
                    match = re.search(r"^(\w+)\s*>>\s*(\w+)$", content)
                    if match:
                        blueprint_dict["relationships"].append(
                            {
                                "source": match.group(1),
                                "destination": match.group(2),
                                "connection_type": "default",
                            }
                        )

        return blueprint_dict


class DiagramCoder:
    """Agent 2: Generates Python code from blueprint using diagrams library.

    Responsibilities:
    - Convert blueprint to executable Python
    - Import correct AWS service classes
    - Create proper diagram structure
    - Ensure code is clean and runnable
    """

    SYSTEM_PROMPT = """You are CloudForge-Core. Your goal is to generate executable Python code using the `diagrams` library based EXACTLY on the provided Blueprint.

### CRITICAL RULES
1. **Output:** Return ONLY raw Python code. Do NOT use Markdown blocks (```).
2. **Imports:** Use specific sub-modules (e.g., `from diagrams.aws.compute import EC2`).
3. **Setup:** ALWAYS import `os` and run `os.makedirs("output", exist_ok=True)`.
4. **Diagram:** Use `with Diagram(..., show=False, filename="output/...", direction="TB"):`.

### REFERENCE TEMPLATE (MIMIC THIS CODING STYLE)
import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import ECS, Lambda
from diagrams.aws.database import RDS, DynamoDB
from diagrams.aws.network import ALB
from diagrams.aws.storage import S3
from diagrams.aws.integration import SQS

# 1. Setup Output Directory
os.makedirs("output", exist_ok=True)

# 2. Initialize Diagram
with Diagram("Architecture Name", show=False, filename="output/arch_name", direction="TB"):
    # 3. Define Global Nodes
    lb = ALB("Load Balancer")
    s3 = S3("Storage")

    # 4. Define Clusters (if any in Blueprint)
    with Cluster("Service Logic"):
        app = ECS("App Service")
        worker = Lambda("Worker Lambda")
        queue = SQS("Task Queue")

    # 5. Define Storage/DB
    db = RDS("Primary DB")
    cache = DynamoDB("Cache")

    # 6. Define Flows
    lb >> app
    app >> db
    app >> cache
    app >> queue
    queue >> worker
    worker >> s3

### INSTRUCTION
Convert the User's Blueprint into Python code following the Reference Template above. Return ONLY the Python code, no explanations.
"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize coder with Gemini API.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
        """
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        genai.configure(api_key=key)
        self.model = genai.GenerativeModel("gemini-2.5-flash")

    def generate_code(self, blueprint: ArchitectureBlueprint) -> str:
        """Generate Python code from blueprint.

        Args:
            blueprint: ArchitectureBlueprint to convert

        Returns:
            str: Valid Python code using diagrams library

        Raises:
            ValueError: If code generation fails
        """
        logger.info("💻 Diagram Coder generating Python code...")

        blueprint_text = str(blueprint)
        logger.debug(f"Blueprint input:\n{blueprint_text}")

        try:
            response = self.model.generate_content(
                [self.SYSTEM_PROMPT, f"\nBlueprint:\n{blueprint_text}"],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.1,  # Very low for code precision
                    max_output_tokens=3000,
                ),
            )

            code = response.text.strip()

            # Remove markdown formatting if present
            code = code.replace("```python", "").replace("```", "").strip()

            # Basic validation
            if "import" not in code or "Diagram" not in code:
                raise ValueError("Generated code missing required imports")

            # Syntax validation
            self._validate_code_syntax(code, blueprint_text)

            logger.info("✅ Code generated successfully")
            return code

        except Exception as e:
            logger.error(f"❌ Code generation failed: {str(e)}")
            raise

    def _validate_code_syntax(self, code: str, blueprint_text: str) -> None:
        """Validate Python code syntax.

        Args:
            code: Generated Python code to validate
            blueprint_text: Original blueprint for debugging

        Raises:
            ValueError: If code has syntax errors
        """
        try:
            ast.parse(code)
        except SyntaxError as e:
            logger.error(f"Generated code has syntax error at line {e.lineno}: {e.msg}")
            logger.error(f"Problem text: {e.text}")
            logger.debug(f"Generated code:\n{code}")
            logger.debug(f"Blueprint was:\n{blueprint_text}")
            raise ValueError(
                f"Generated code has syntax error at line {e.lineno}: {e.msg}. "
                "This may indicate the AI model needs a better prompt. Check logs for details."
            )


class NaturalLanguageProcessor:
    """Orchestrator: Manages two-agent pipeline.

    Pipeline:
    1. BlueprintArchitect analyzes raw text → blueprint
    2. DiagramCoder generates Python code → diagram
    3. Both are saved for user consumption

    Responsibilities:
    - Coordinate agents
    - Error handling
    - Output management
    - Logging
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize processor with both agents.

        Args:
            api_key: Google API key for both agents
        """
        self.architect = BlueprintArchitect(api_key)
        self.coder = DiagramCoder(api_key)

    def process(
        self, raw_text: str, output_filename: str = "generated_diagram"
    ) -> dict[str, str]:
        """Process natural language to complete diagram.

        Args:
            raw_text: Unstructured architecture description
            output_filename: Name for output Python file (without .py)

        Returns:
            dict with keys:
            - blueprint: The structured blueprint as text
            - code: Generated Python code
            - output_path: Path where code was saved

        Raises:
            ValueError: If processing fails at any stage
        """
        logger.info("🚀 Starting natural language to diagram pipeline...")

        try:
            # Step 1: Create blueprint
            blueprint = self.architect.analyze(raw_text)
            blueprint_text = str(blueprint)

            # Step 2: Generate code
            code = self.coder.generate_code(blueprint)

            # Step 3: Save code
            os.makedirs("output", exist_ok=True)
            output_path = f"output/{output_filename}.py"

            with open(output_path, "w") as f:
                f.write(code)

            logger.info(f"✅ Pipeline complete! Code saved to {output_path}")

            return {
                "blueprint": blueprint_text,
                "code": code,
                "output_path": output_path,
            }

        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            raise
