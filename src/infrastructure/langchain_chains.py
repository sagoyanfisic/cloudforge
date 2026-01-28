"""LangChain chains for CloudForge pipeline

Replaces manual Gemini calls with LangChain chains featuring:
- Automatic retries and fallbacks
- Structured output parsing
- Better error handling
- Observability via LangSmith
"""

import os
import logging
from typing import Optional, Any
from datetime import datetime
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from pydantic import BaseModel, Field

from ..domain.models import DiagramValidation, ValidationError

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


# ============================================================================
# Output Models (Structured)
# ============================================================================


class BlueprintNode(BaseModel):
    """Single AWS service node"""
    name: str = Field(..., description="Service name")
    variable: str = Field(..., description="Python variable name")
    service_type: str = Field(..., description="AWS service class")
    region: Optional[str] = Field(None, description="AWS region")


class BlueprintRelationship(BaseModel):
    """Connection between services"""
    source: str = Field(..., description="Source variable")
    destination: str = Field(..., description="Destination variable")
    connection_type: str = Field(default="default")


class BlueprintAnalysisOutput(BaseModel):
    """Structured blueprint analysis output"""
    title: str = Field(..., description="Architecture name")
    description: str = Field(..., description="Architecture description")
    nodes: list[BlueprintNode] = Field(default_factory=list, description="AWS services")
    relationships: list[BlueprintRelationship] = Field(default_factory=list, description="Connections")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DiagramCodeOutput(BaseModel):
    """Structured code generation output"""
    code: str = Field(..., description="Generated Python code")
    imports: list[str] = Field(default_factory=list, description="Import statements")
    classes_used: list[str] = Field(default_factory=list, description="AWS classes used")


# ============================================================================
# LangChain Chains
# ============================================================================


class BlueprintArchitectChain:
    """LangChain chain for blueprint generation"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize blueprint architect chain

        Args:
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
        """
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Provide it via:\n"
                "  - api_key parameter\n"
                "  - GOOGLE_API_KEY environment variable\n"
                "  - .env file with GOOGLE_API_KEY=your_key"
            )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.05,
            max_output_tokens=5000,
        ).with_retry(
            stop_after_attempt=3,
            wait_exponential_jitter=True,
        )

        self.parser = PydanticOutputParser(pydantic_object=BlueprintAnalysisOutput)

        # System prompt
        system_prompt = """You are CloudForge Blueprint Architect. Analyze AWS architecture descriptions.

OUTPUT FORMAT (JSON):
{{
  "title": "Architecture Name",
  "description": "Brief description",
  "nodes": [
    {{"name": "API Gateway", "variable": "api_gw", "service_type": "APIGateway", "region": "us-east-1"}},
    {{"name": "Lambda", "variable": "lambda_func", "service_type": "Lambda", "region": "us-east-1"}}
  ],
  "relationships": [
    {{"source": "api_gw", "destination": "lambda_func", "connection_type": "triggers"}}
  ],
  "metadata": {{
    "pattern": "serverless",
    "services_count": 2,
    "environment": "production",
    "service_categories": ["Network", "Compute", "Database"]
  }}
}}

CONNECTION TYPES (use these for relationships):
- "triggers": Event-driven (API calls, Lambda invocations)
- "reads_writes": Database access
- "pulls": Data retrieval (ECR → EKS, S3 → instances)
- "forwards": Load balancing / traffic
- "manages": Control plane / configuration
- "monitors": Observability / logging

ENVIRONMENT DETECTION:
- Look for keywords: prod, production, staging, dev, development, sandbox
- Default to "production" if not specified
- Add to metadata: "environment": "production|staging|development|sandbox"

CATEGORIZE SERVICES:
- Network: APIGateway, ALB, NLB, CloudFront, Route53, VPC
- Compute: Lambda, EC2, ECS, EKS, Batch
- Database: RDS, DynamoDB, ElastiCache, Redshift
- Storage: S3, EBS, EFS
- Integration: SQS, SNS, Kinesis
- Monitoring: CloudWatch, CloudTrail
- Security: IAM, KMS, Secrets Manager

RULES:
1. Extract ALL AWS services mentioned
2. Create logical variable names (snake_case)
3. Map to correct service types
4. Use specific connection_type for relationships (not "default")
5. Return valid JSON
6. Detect environment and add to metadata
7. Categorize services and list in metadata
8. Do NOT include abstract concepts as nodes (VPC, Subnet, SecurityGroup) - they become Clusters in visualization
"""

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{description}"),
        ])

    def invoke(self, description: str) -> dict[str, Any]:
        """Generate blueprint from description

        Args:
            description: Architecture description

        Returns:
            dict: Parsed blueprint

        Raises:
            ValueError: If generation fails
        """
        logger.info("🏗️ Blueprint Architect analyzing text with LangChain...")

        try:
            chain = (
                self.prompt
                | self.llm
                | self.parser
            )

            result = chain.invoke({"description": description})
            logger.info(f"✅ Blueprint generated: {result.title} ({len(result.nodes)} nodes)")

            return {
                "title": result.title,
                "description": result.description,
                "nodes": [node.dict() for node in result.nodes],
                "relationships": [rel.dict() for rel in result.relationships],
                "metadata": result.metadata,
            }

        except Exception as e:
            logger.error(f"❌ Blueprint generation failed: {str(e)}")
            raise ValueError(f"Blueprint generation failed: {str(e)}")


class DiagramCoderChain:
    """LangChain chain for code generation"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize diagram coder chain

        Args:
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
        """
        # Get API key from parameter or environment
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not set. Provide it via:\n"
                "  - api_key parameter\n"
                "  - GOOGLE_API_KEY environment variable\n"
                "  - .env file with GOOGLE_API_KEY=your_key"
            )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.05,
            max_output_tokens=5000,
        ).with_retry(
            stop_after_attempt=3,
            wait_exponential_jitter=True,
        )

        self.system_prompt = """You are CloudForge Diagram Coder. Generate professional Python diagrams code ONLY.

═══════════════════════════════════════════════════════════════════════════════
CRITICAL RULES - MUST FOLLOW EXACTLY:
═══════════════════════════════════════════════════════════════════════════════

1. **STRING INTEGRITY** - EVERY STRING MUST BE COMPLETE
   - CORRECT: Lambda("Lambda Function")
   - WRONG: Lambda("Lambda Func  ← Missing closing quote!

2. **PARENTHESIS BALANCE** - EVERY ( MUST HAVE MATCHING )
   - CORRECT: APIGateway("API")
   - WRONG: APIGateway("API"  ← Missing closing parenthesis!

3. **RETURN ONLY VALID PYTHON CODE** - No explanations, markdown, code blocks, or comments

4. **ONE LINE PER NODE** - Never split node creation across lines

5. **NO CLUSTER-TO-CLUSTER CONNECTIONS** - Only node >> node, never Cluster >> Cluster

6. **PROPER INDENTATION** - Nodes inside Cluster MUST be indented

═══════════════════════════════════════════════════════════════════════════════
VISUAL ORGANIZATION RULES:
═══════════════════════════════════════════════════════════════════════════════

ORGANIZE CLUSTERS BY SERVICE CATEGORY:
- Compute: Lambda, EC2, ECS, Batch
- Database: RDS, ElastiCache, Redshift
- Storage: S3, EBS, EFS
- Network: APIGateway, ALB, NLB, Route53, NATGateway
- Integration: SQS, SNS, Kinesis
- External: Users, GitHub, Third-party services

ADD COLORS FOR ENVIRONMENTS:
- Production: "#E74C3C" (Red)
- Staging: "#F39C12" (Orange)
- Development: "#3498DB" (Blue)
- Management: "#27AE60" (Green)
- Monitoring: "#95A5A6" (Gray)
- Security: "#C0392B" (Dark Red)

USE EDGE LABELS FOR CONNECTION TYPES:
- "Triggers" for events
- "Pulls/Pushes" for data movement
- "Reads/Writes" for database access
- "Manages" for control plane
- "Monitors" for observability
- "Forwards" for traffic

CLUSTER BACKGROUND COLOR:
- Use graph_attr={{"bgcolor": "COLOR#10"}} to add background tint
- Example: graph_attr={{"bgcolor": "#E74C3C10"}} for light red background

═══════════════════════════════════════════════════════════════════════════════
IMPORT MAPPING (ONLY from these modules):
═══════════════════════════════════════════════════════════════════════════════

from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda, EC2, ECS, Batch
from diagrams.aws.database import RDS, ElastiCache, Redshift
from diagrams.aws.network import APIGateway, ALB, NLB, NATGateway, Route53
from diagrams.aws.storage import S3, EBS, EFS
from diagrams.aws.integration import SQS, SNS
from diagrams.aws.analytics import Kinesis
from diagrams.aws.general import Users
from diagrams.onprem.vcs import Github

VALID CLASSES: Lambda, EC2, ECS, Batch, RDS, ElastiCache, Redshift, S3, EBS, EFS, APIGateway, ALB, NLB, NATGateway, Route53, SQS, SNS, Kinesis, Users, Github

DO NOT IMPORT (use as Cluster labels only):
DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy

═══════════════════════════════════════════════════════════════════════════════
PROFESSIONAL EXAMPLE WITH COLORS, CLUSTERS, AND EDGE LABELS:
═══════════════════════════════════════════════════════════════════════════════

import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS
from diagrams.aws.storage import S3
from diagrams.aws.general import Users

os.makedirs("output", exist_ok=True)

COLOR_PROD = "#E74C3C"
COLOR_COMPUTE = "#3498DB"
COLOR_DATABASE = "#27AE60"
COLOR_STORAGE = "#F39C12"

with Diagram("Production API", show=False, filename="output/diagram", direction="TB"):
    users = Users("End Users")

    api = APIGateway("API Gateway")

    with Cluster("Compute", graph_attr={{"bgcolor": "{{COLOR_COMPUTE}}10"}}):
        func = Lambda("Processing")

    with Cluster("Data Layer", graph_attr={{"bgcolor": "{{COLOR_DATABASE}}10"}}):
        db = RDS("PostgreSQL")

    with Cluster("Static Assets", graph_attr={{"bgcolor": "{{COLOR_STORAGE}}10"}}):
        storage = S3("S3 Bucket")

    users >> Edge(label="Requests") >> api
    api >> Edge(label="Triggers") >> func
    func >> Edge(label="Reads/Writes") >> db
    func >> Edge(label="Stores") >> storage

═══════════════════════════════════════════════════════════════════════════════
FINAL CHECKLIST BEFORE RETURNING CODE:
═══════════════════════════════════════════════════════════════════════════════

✓ Every opening quote has closing quote on SAME LINE
✓ Every opening parenthesis has closing parenthesis
✓ All node definitions complete: variable = Service("Label")
✓ No lines cut off or incomplete
✓ All imports exist at top of file
✓ Connections only between nodes (var1 >> var2), never Cluster >> Cluster
✓ Edge labels describe connection purpose
✓ Clusters have meaningful names and colors
✓ Return ONLY valid Python code, NO explanations
"""

    def invoke(self, blueprint: dict[str, Any]) -> str:
        """Generate code from blueprint

        Args:
            blueprint: Parsed blueprint

        Returns:
            str: Generated Python code

        Raises:
            ValueError: If generation fails
        """
        logger.info("💻 Diagram Coder generating code with LangChain...")

        try:
            # Format blueprint for prompt
            blueprint_text = self._format_blueprint(blueprint)

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"Blueprint:\n{blueprint_text}"),
            ])

            chain = prompt | self.llm

            response = chain.invoke({})
            code = response.content.strip()

            # Clean markdown if present
            code = code.replace("```python", "").replace("```", "").strip()

            # Basic validation
            if "import" not in code or "Diagram" not in code:
                raise ValueError("Generated code missing required imports")

            # Validate for common issues
            self._validate_generated_code(code)

            logger.info("✅ Code generated successfully")
            return code

        except Exception as e:
            logger.error(f"❌ Code generation failed: {str(e)}")
            raise ValueError(f"Code generation failed: {str(e)}")

    def _generate_color_hints(self, environment: str) -> str:
        """Generate color palette recommendations based on environment.

        Args:
            environment: Target environment (production, staging, development, sandbox)

        Returns:
            String with color definitions for code generation
        """
        # Primary environment color
        env_colors = {
            "production": "#E74C3C",      # Red
            "prod": "#E74C3C",
            "staging": "#F39C12",         # Orange
            "development": "#3498DB",     # Blue
            "dev": "#3498DB",
            "sandbox": "#9B59B6",         # Purple
        }

        primary_color = env_colors.get(environment.lower(), "#E74C3C")

        # Note: Colors are formatted as plain text (not as f-string) to avoid template variable interpretation
        colors = ("# Environment: " + environment + "\n"
                 'COLOR_PRIMARY = "' + primary_color + '"        # Primary environment color\n'
                 'COLOR_COMPUTE = "#3498DB"              # Blue - Compute services\n'
                 'COLOR_DATABASE = "#27AE60"             # Green - Database services\n'
                 'COLOR_STORAGE = "#F39C12"              # Orange - Storage services\n'
                 'COLOR_NETWORK = "#E74C3C"              # Red - Network services\n'
                 'COLOR_SECURITY = "#C0392B"             # Dark Red - Security services\n'
                 'COLOR_MONITORING = "#95A5A6"           # Gray - Monitoring services\n'
                 'COLOR_INTEGRATION = "#16A085"          # Teal - Integration services')

        return colors

    def _validate_generated_code(self, code: str) -> None:
        """Validate generated code for common issues.

        Args:
            code: Generated Python code

        Raises:
            ValueError: If validation fails
        """
        import re

        lines = code.split("\n")

        # 1. Check for unterminated strings (strings without closing quote)
        for idx, line in enumerate(lines, 1):
            # Skip comments and lines without quotes
            if line.strip().startswith("#"):
                continue

            # Check for unterminated string literals
            # Count quotes and ensure they're balanced on each line (simple check)
            single_quotes = line.count("'")
            double_quotes = line.count('"')

            # Count escaped quotes to exclude them from count
            escaped_single = line.count("\\'")
            escaped_double = line.count('\\"')

            # Unescaped quotes should be even (paired)
            actual_single = single_quotes - escaped_single
            actual_double = double_quotes - escaped_double

            if actual_single % 2 != 0 or actual_double % 2 != 0:
                logger.warning(f"⚠️ Possible unterminated string on line {idx}: {line.strip()}")
                raise ValueError(f"Unterminated string on line {idx}: {line.strip()}")

        # 2. Check for unmatched parentheses
        open_parens = code.count("(")
        close_parens = code.count(")")
        if open_parens != close_parens:
            logger.warning(f"⚠️ Unmatched parentheses: {open_parens} open, {close_parens} close")
            raise ValueError(f"Unmatched parentheses in generated code")

        # 3. Check for Cluster >> Cluster pattern (common error)
        cluster_vars = set()
        node_vars = set()

        for line in lines:
            # Find Cluster definitions
            cluster_match = re.search(r'with\s+Cluster\(["\']([^"\']+)["\']\):', line)
            if cluster_match:
                # Extract variable name from previous line
                idx = lines.index(line)
                if idx > 0 and "=" in lines[idx - 1]:
                    var_match = re.search(r'(\w+)\s*=\s*Cluster', lines[idx - 1])
                    if var_match:
                        cluster_vars.add(var_match.group(1))

            # Find node definitions (Service classes)
            node_match = re.search(r'(\w+)\s*=\s*(Lambda|EC2|ECS|RDS|S3|APIGateway|ALB|NLB|SQS|SNS|Kinesis|ElastiCache|NATGateway|Batch|Route53|EBS|EFS|Redshift)\(', line)
            if node_match:
                node_vars.add(node_match.group(1))

        # Check for >> connections
        connection_pattern = re.compile(r'(\w+)\s*>>\s*(\w+)')
        for line in lines:
            matches = connection_pattern.findall(line)
            for source, dest in matches:
                # Warn if connecting Clusters (both are in cluster_vars)
                if source in cluster_vars and dest in cluster_vars:
                    logger.warning(
                        f"⚠️ Potential issue: Connecting Clusters directly "
                        f"({source} >> {dest}). Should connect nodes, not Clusters."
                    )

    def _format_blueprint(self, blueprint: dict[str, Any]) -> str:
        """Format blueprint as text for prompt with environment and categorization info"""
        text = f"Title: {blueprint.get('title', 'Diagram')}\n"
        text += f"Description: {blueprint.get('description', '')}\n\n"

        # Include metadata for visual organization
        metadata = blueprint.get("metadata", {})
        if metadata:
            environment = metadata.get("environment", "production")
            categories = metadata.get("service_categories", [])
            text += f"Environment: {environment}\n"
            if categories:
                text += f"Service Categories: {', '.join(categories)}\n"
            text += "\n"

        # Services with categorization hint
        text += "Services (organize into Clusters by category):\n"
        for node in blueprint.get("nodes", []):
            text += f"- {node['name']} ({node['service_type']})\n"

        # Connections with types
        text += "\nConnections (use appropriate Edge labels):\n"
        for rel in blueprint.get("relationships", []):
            conn_type = rel.get("connection_type", "default")
            text += f"- {rel['source']} >> {rel['destination']} [{conn_type}]\n"

        # Include AWS best practices if available (from AWS MCP enrichment)
        best_practices = blueprint.get("best_practices", [])
        if best_practices:
            text += "\n🎯 AWS BEST PRACTICES TO APPLY:\n"
            text += "Ensure the generated code follows these recommendations:\n"
            for practice in best_practices:
                text += f"  {practice}\n"
            text += "\n"

        return text
