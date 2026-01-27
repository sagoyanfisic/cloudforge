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

    SYSTEM_PROMPT = """You are the CloudForge Blueprint Architect. Transform AWS architecture descriptions into structured blueprints.

OUTPUT ONLY the blueprint between the markers. Do NOT add intro/outro text.

---BEGIN_BLUEPRINT---
Title: [Project Name]
Description: [Brief description]

Nodes:
- [Service Name] | ID: [service_id] | Type: [AWSClass] | Category: [category]

Clusters:
- Cluster: [Group Name]
  Type: [Logical/VPC/Subnet]
  Members: [service_id1, service_id2]

Relationships:
- [source_id] >> [dest_id]

Metadata:
- Inferred_Decisions: ["decision 1", "decision 2"]
- Security_Risk: [Low/Medium/High]
---END_BLUEPRINT---

RULES:
1. Use valid AWS service class names (e.g., EC2, Lambda, DynamoDB, RDS, APIGateway, VPC, Subnet, SecurityGroup, NATGateway, RDSProxy, DynamoDBTable)
2. Node IDs must be lowercase, snake_case (user_api, rds_proxy, private_subnet)
3. For Serverless APIs: Include Lambda, APIGateway, DynamoDB, and if accessing RDS, add RDSProxy
4. For Database Architectures: Distinguish between DynamoDB (NoSQL), RDS (SQL), and RDSProxy (connection pooling)
5. For VPC Security: Show Private Subnets, Security Groups, NAT Gateway flow
6. Mark databases exposed to internet as Security_Risk: High
7. Include all network components: VPC, Subnets, gateways, security groups

COMMON PATTERNS:
- Serverless API: APIGateway -> Lambda -> DynamoDB + RDS (via RDSProxy)
- Database Access: Private Lambda -> RDSProxy -> RDS (secure connection pooling)
- VPC Setup: Public Subnet (NAT) -> Private Subnet (Lambda, Databases)
- Multi-DB: DynamoDB for fast NoSQL + RDS for relational + ElastiCache for caching
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

        # Detect if this is a serverless architecture
        is_serverless = self._detect_serverless(raw_text)
        system_prompt = self._get_serverless_prompt() if is_serverless else self.SYSTEM_PROMPT

        try:
            response = self.model.generate_content(
                [system_prompt, f"\nUser input:\n{raw_text}"],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Low for analytical thinking
                    max_output_tokens=2000,
                ),
            )

            blueprint_text = response.text.strip()
            logger.debug(f"Raw response: {blueprint_text[:500]}")  # Log first 500 chars

            # Extract blueprint from text format
            try:
                blueprint_dict = self._parse_blueprint_text(blueprint_text)
            except ValueError as parse_error:
                logger.error(f"❌ Parse error: {str(parse_error)}")
                logger.error(f"Full response received:\n{blueprint_text[:1000]}")
                raise ValueError(f"Blueprint format invalid. Got: {blueprint_text[:200]}...") from parse_error

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
        - [Display Name] | ID: [var_name] | Type: [Class] | Category: [module_name]

        Clusters:
        - Cluster: [Display Name]
          Type: [Logical/VPC/Subnet]
          Members: [var1, var2, ...]

        Relationships:
        - [source_var] >> [dest_var]

        Metadata:
        - Inferred_Decisions: [...]
        - Security_Risk: [Low/Medium/High]
        ---END_BLUEPRINT---

        Args:
            text: Blueprint text to parse

        Returns:
            dict: Parsed blueprint as dictionary

        Raises:
            ValueError: If blueprint format is invalid
        """
        # Extract content between markers (flexible whitespace)
        start_marker = "---BEGIN_BLUEPRINT---"
        end_marker = "---END_BLUEPRINT---"

        start_idx = text.find(start_marker)
        end_idx = text.find(end_marker)

        if start_idx == -1 or end_idx == -1:
            # Try alternative markers
            start_marker_alt = "BEGIN_BLUEPRINT"
            end_marker_alt = "END_BLUEPRINT"
            start_idx = text.find(start_marker_alt)
            end_idx = text.find(end_marker_alt)

            if start_idx == -1 or end_idx == -1:
                raise ValueError(f"Blueprint markers not found. Looked for '---BEGIN_BLUEPRINT---' or 'BEGIN_BLUEPRINT'")

        # Calculate proper marker length
        marker_len = len(start_marker) if text[start_idx:start_idx+len(start_marker)] == start_marker else len(start_marker_alt)
        blueprint_content = text[start_idx + marker_len : end_idx].strip()

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
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            i += 1

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
            elif line == "Metadata:":
                current_section = "metadata"
            elif line.startswith("-") and current_section == "nodes":
                # Parse: [Display Name] | ID: [var_name] | Type: [Class] | Category: [module_name]
                content = line[1:].strip()
                parts = [p.strip() for p in content.split("|")]

                if len(parts) >= 3:
                    name = parts[0]
                    var_id = ""
                    service_type = ""

                    for part in parts[1:]:
                        if part.startswith("ID:"):
                            var_id = part[3:].strip()
                        elif part.startswith("Type:"):
                            service_type = part[5:].strip()

                    if var_id and service_type:
                        blueprint_dict["nodes"].append(
                            {
                                "name": name,
                                "variable": var_id,
                                "service_type": service_type,
                                "region": None,
                            }
                        )

            elif line.startswith("Cluster:") and current_section == "clusters":
                # Parse cluster definition
                cluster_name = line[8:].strip()
                cluster_type = ""
                cluster_members = []

                # Look ahead for Type and Members
                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line or next_line.startswith("-"):
                        break

                    if next_line.startswith("Type:"):
                        cluster_type = next_line[5:].strip()
                    elif next_line.startswith("Members:"):
                        members_str = next_line[8:].strip()
                        cluster_members = [m.strip() for m in members_str.split(",")]

                    i += 1

                blueprint_dict["clusters"].append(
                    {"name": cluster_name, "nodes": cluster_members}
                )

            elif line.startswith("-") and current_section == "relationships":
                # Parse: [source_var] >> [dest_var]
                content = line[1:].strip()
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

    def _detect_serverless(self, text: str) -> bool:
        """Detect if architecture is serverless-based.

        Args:
            text: Architecture description

        Returns:
            bool: True if serverless patterns detected
        """
        serverless_keywords = [
            "lambda", "serverless", "api gateway", "dynamodb", "rds proxy",
            "private subnet", "vpc", "security group", "rest api",
            "function", "event-driven", "managed database"
        ]
        text_lower = text.lower()
        return sum(1 for keyword in serverless_keywords if keyword in text_lower) >= 3

    def _get_serverless_prompt(self) -> str:
        """Get specialized prompt for serverless architectures.

        Returns:
            str: Gemini system prompt for serverless designs
        """
        return """You are the CloudForge Serverless Architect, expert in AWS Lambda, API Gateway, DynamoDB, and RDS.

GOAL: Design enterprise-grade Serverless architectures with VPC, multi-database support, and RDS connection pooling.

ARCHITECTURE PATTERNS FOR SERVERLESS:

1. **VPC & Security**:
   - Public Subnets: API Gateway endpoints, NAT Gateway
   - Private Subnets: Lambda functions, RDS, DynamoDB
   - Security Groups: Restrict Lambda → RDS/DynamoDB access

2. **Multi-Database Strategy**:
   - DynamoDB: High-velocity, low-latency NoSQL data (real-time analytics, caching)
   - RDS: Transactional relational data (PostgreSQL/MySQL)
   - RDSProxy: Connection pooling layer between Lambda and RDS (CRITICAL)

3. **API & Compute**:
   - API Gateway: Regional or Private endpoints for REST API
   - Lambda: Serverless compute in private subnets (VPC-enabled)
   - No EC2/ECS unless specifically mentioned

4. **Data Flow**:
   - User → API Gateway → Lambda (private subnet)
   - Lambda → RDSProxy → RDS (managed connections)
   - Lambda → DynamoDB (direct, high-speed)
   - Optional: CloudWatch, CloudTrail for monitoring

OUTPUT ONLY the blueprint. Do NOT add intro/outro text.

---BEGIN_BLUEPRINT---
Title: [Project Name]
Description: [Brief description emphasizing security & multi-database design]

Nodes:
- [Service Name] | ID: [service_id] | Type: [AWSClass] | Category: [category]

Clusters:
- Cluster: Public Subnet
  Type: VPC
  Members: [api_gateway, nat_gateway]
- Cluster: Private Subnet
  Type: VPC
  Members: [lambda_function, rds_proxy, dynamodb, rds]
- Cluster: Monitoring
  Type: Logical
  Members: [cloudwatch, cloudtrail]

Relationships:
- api_gateway >> lambda_function
- lambda_function >> rds_proxy
- rds_proxy >> rds
- lambda_function >> dynamodb
- lambda_function >> cloudwatch

Metadata:
- Inferred_Decisions: ["VPC with private subnets for Lambda", "RDSProxy for connection pooling", "DynamoDB for NoSQL high-speed access", "Security Groups for network isolation"]
- Security_Risk: Low
---END_BLUEPRINT---

RULES FOR SERVERLESS:
1. Always include API Gateway for REST APIs
2. Always include RDSProxy if RDS is mentioned (connection pooling is critical)
3. Always show VPC structure (Public/Private Subnets)
4. Mark databases in private subnets (safe) vs public (HIGH RISK)
5. Include Security Groups for Lambda access control
6. Distinguish between DynamoDB tables and RDS instances
7. Include monitoring services (CloudWatch, CloudTrail)
"""

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
