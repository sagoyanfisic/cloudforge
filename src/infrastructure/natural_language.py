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

# AWS MCP Clients (optional for best practices enrichment)
try:
    from .aws_mcp_client import get_aws_documentation_client
    HAS_AWS_MCP = True
except ImportError:
    HAS_AWS_MCP = False
    get_aws_documentation_client = None

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

        # Optionally enrich with AWS best practices from documentation server
        aws_best_practices = self._enrich_with_aws_best_practices(raw_text)

        try:
            # Prepare messages: system prompt, best practices (if available), and user input
            messages = [system_prompt]
            if aws_best_practices:
                messages.append(f"Additional AWS Best Practices Context:{aws_best_practices}")
            messages.append(f"\nUser input:\n{raw_text}")

            response = self.model.generate_content(
                messages,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.05,  # Very low for analytical precision
                    max_output_tokens=5000,  # Increased to avoid truncation
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

            # If no nodes were parsed, this might be a truncated response
            if not blueprint_dict.get("nodes"):
                logger.warning(f"⚠️ No nodes parsed from blueprint. Response may be incomplete.")
                logger.warning(f"Blueprint text (first 500 chars):\n{blueprint_text[:500]}")

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

        # If start found but end not found, use end of text (response was truncated)
        if start_idx != -1 and end_idx == -1:
            logger.warning("⚠️ END_BLUEPRINT marker not found - response may be truncated, using end of text")
            end_idx = len(text)

        # Try alternative markers if primary not found
        if start_idx == -1:
            start_marker = "BEGIN_BLUEPRINT"
            start_idx = text.find(start_marker)

        if end_idx == -1 or (start_idx == -1):
            # Try with just the alternative marker
            if start_idx == -1:
                raise ValueError(f"Blueprint start marker not found in response")
            if end_idx == -1:
                logger.warning("⚠️ Using end of text as response may be incomplete")
                end_idx = len(text)

        # Calculate proper marker length
        marker_len = len("---BEGIN_BLUEPRINT---") if "---BEGIN_BLUEPRINT---" in text[max(0, start_idx-10):start_idx+30] else len("BEGIN_BLUEPRINT")
        blueprint_content = text[start_idx + marker_len : end_idx].strip()

        # Parse sections
        blueprint_dict = {
            "title": "Generated Architecture",
            "description": "Architecture blueprint from natural language",
            "nodes": [],
            "clusters": [],
            "relationships": [],
        }

        current_section = None
        lines = blueprint_content.split("\n")
        i = 0

        # Track if we successfully parsed at least some content
        parsed_any_content = False

        while i < len(lines):
            line = lines[i].strip()
            i += 1

            if not line:
                continue

            if line.startswith("Title:"):
                blueprint_dict["title"] = line[6:].strip()
                parsed_any_content = True
            elif line.startswith("Description:"):
                blueprint_dict["description"] = line[12:].strip()
                parsed_any_content = True
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
                    parsed_any_content = True

        # Log what we successfully parsed
        logger.info(f"✅ Parsed blueprint: Title='{blueprint_dict['title']}', Nodes={len(blueprint_dict['nodes'])}, Clusters={len(blueprint_dict['clusters'])}, Relationships={len(blueprint_dict['relationships'])}")

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

    def _enrich_with_aws_best_practices(self, text: str) -> str:
        """Enrich analysis with AWS best practices from AWS Documentation MCP

        Optionally calls AWS Documentation server to get real-time best practices.

        Args:
            text: Architecture description

        Returns:
            str: Best practices recommendations (or empty string if unavailable)
        """
        if not HAS_AWS_MCP or get_aws_documentation_client is None:
            return ""

        try:
            logger.info("🔍 Enriching with AWS best practices from documentation server...")
            doc_client = get_aws_documentation_client()

            if not doc_client.is_connected():
                if not doc_client.connect():
                    logger.warning("⚠️ Could not connect to AWS Documentation server")
                    return ""

            # Extract key services from description
            services = []
            common_services = ["lambda", "dynamodb", "rds", "api gateway", "s3", "sqs", "sns", "kinesis", "cloudwatch"]
            for service in common_services:
                if service in text.lower():
                    services.append(service)

            if not services:
                return ""

            # Get best practices for detected services
            enrichment = "\n\n--- AWS Best Practices ---\n"

            for service in services[:3]:  # Limit to 3 services to avoid overload
                pattern = "serverless" if "lambda" in text.lower() else "general"
                practices = doc_client.get_best_practices(service, pattern)
                if practices:
                    enrichment += f"\n{service.upper()}:\n{practices}\n"

            logger.info(f"✅ Enriched with best practices for: {', '.join(services)}")
            return enrichment

        except Exception as e:
            logger.warning(f"⚠️ Could not enrich with AWS best practices: {str(e)}")
            return ""

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

    SYSTEM_PROMPT = """Generate Python code using diagrams library. Output ONLY valid Python code.

CRITICAL RULES:
1. EVERY string parameter MUST end with closing quote
2. EVERY opening parenthesis MUST have matching closing parenthesis
3. NO markdown blocks, NO explanations, ONLY code
4. Keep code SHORT and COMPLETE (no truncation)

VALID CLASSES TO IMPORT (whitelist):
Lambda, EC2, ECS, RDS, S3, APIGateway, ALB, NLB, SQS, SNS, Kinesis, ElastiCache

DO NOT IMPORT (use Clusters instead):
DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy, NAT Gateway

MINIMAL TEMPLATE (modify ONLY variable names):
import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.network import APIGateway

os.makedirs("output", exist_ok=True)

with Diagram("Title", show=False, filename="output/diagram", direction="TB"):
    api = APIGateway("API")
    func = Lambda("Func")
    with Cluster("Database"):
        db = RDS("PostgreSQL")
    api >> func >> db

CLUSTER EXAMPLES (Logical groupings):
- Cluster("VPC - Private Subnet")
- Cluster("DynamoDB Tables")
- Cluster("Monitoring")
- Cluster("Security")
- Cluster("RDS Proxy")
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
        # Use gemini-2.5-flash for better stability and code generation
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

        # Detect if blueprint mentions serverless components
        is_serverless = any(term in blueprint_text.lower() for term in ["lambda", "api gateway", "dynamodb", "rds proxy"])
        system_prompt = self._get_serverless_coder_prompt() if is_serverless else self.SYSTEM_PROMPT

        try:
            response = self.model.generate_content(
                [system_prompt, f"\nBlueprint:\n{blueprint_text}"],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.05,  # Even lower for precision
                    max_output_tokens=5000,  # Increased to avoid truncation
                ),
            )

            code = response.text.strip()

            # Remove markdown formatting if present
            code = code.replace("```python", "").replace("```", "").strip()

            # Fix incomplete strings (safety fix for Gemini truncation)
            code = self._fix_incomplete_strings(code)

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

    def _fix_incomplete_strings(self, code: str) -> str:
        """Fix incomplete strings that were truncated by Gemini.

        Handles patterns like:
        - with Diagram("Title...", show=False, filename="output/...  (missing closing paren)
        - api >> func >> db_sql >> (missing target)
        - direction="  (missing quote and value)

        Args:
            code: Generated code (possibly with truncated strings)

        Returns:
            str: Code with fixed strings
        """
        lines = code.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.rstrip()

            # Skip empty lines and comments
            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # Detect truncated lines by looking for incomplete parameter patterns
            # Pattern: parameter_name="  or parameter_name=' or parameter_name=
            if any(stripped.endswith(p) for p in ['direction="', 'filename="', 'direction=', 'filename=']):
                logger.warning(f"⚠️ Line {i+1} has truncated parameter: {stripped[-40:]}")

                # Complete the parameter based on what's incomplete
                if stripped.endswith('direction="'):
                    line = stripped + 'TB")'
                elif stripped.endswith('direction='):
                    line = stripped + '"TB")'
                elif stripped.endswith('filename="'):
                    line = stripped + 'output/diagram")'
                elif stripped.endswith('filename='):
                    line = stripped + '"output/diagram")'

            # Check for lines ending with opening parenthesis without close
            elif stripped.endswith('('):
                logger.warning(f"⚠️ Line {i+1} has unclosed parenthesis: {stripped[-40:]}")
                # This is likely a continuation, add placeholder
                line = stripped + ')'

            # Check for unmatched parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            if open_parens > close_parens:
                paren_diff = open_parens - close_parens
                logger.warning(f"⚠️ Line {i+1} missing {paren_diff} closing paren(s): {line[:60]}...")
                line = line + ')' * paren_diff

            # Ensure arrow chains don't end abruptly
            if stripped.endswith(">>"):
                logger.warning(f"⚠️ Line {i+1} ends with incomplete arrow operator")
                line = stripped + " None"

            fixed_lines.append(line)

        fixed_code = "\n".join(fixed_lines)

        # Final pass: balance any remaining parentheses in the entire code
        total_open = fixed_code.count('(')
        total_close = fixed_code.count(')')
        if total_open > total_close:
            remaining_parens = total_open - total_close
            logger.warning(f"⚠️ Code is missing {remaining_parens} closing paren(s), adding to end")
            # Add closing parens before the last colon if it's a with statement
            if '\n' in fixed_code:
                lines_fixed = fixed_code.split('\n')
                lines_fixed[-1] = lines_fixed[-1] + ')' * remaining_parens
                fixed_code = '\n'.join(lines_fixed)
            else:
                fixed_code = fixed_code + ')' * remaining_parens

        return fixed_code

    def _validate_code_syntax(self, code: str, blueprint_text: str) -> None:
        """Validate Python code syntax and diagrams imports.

        Args:
            code: Generated Python code to validate
            blueprint_text: Original blueprint for debugging

        Raises:
            ValueError: If code has syntax errors or invalid imports
        """
        # Check for invalid AWS service class names in imports (not in Cluster names)
        import_section = code.split("os.makedirs")[0]  # Before diagram definition

        invalid_import_classes = [
            "SecurityGroup", "Subnet", "VPC", "CloudFlare", "DBProxy", "RDSProxy",
            "DynamoDB", "CloudWatch", "CloudTrail", "NATGateway", "Route53"
        ]
        for invalid_class in invalid_import_classes:
            # Check if it's being imported (in the import section)
            if f"from diagrams" in import_section and invalid_class in import_section:
                logger.error(f"❌ Invalid class in imports: {invalid_class} (not importable from diagrams.aws)")
                logger.error(f"Import section:\n{import_section}")

                # Provide specific guidance for each invalid class
                if invalid_class == "DynamoDB":
                    hint = "DynamoDB tables are logical concepts. Use: with Cluster('DynamoDB Tables'): ... instead."
                elif invalid_class in ["CloudWatch", "CloudTrail"]:
                    hint = f"{invalid_class} are monitoring concepts. Use: with Cluster('Monitoring'): ... instead."
                elif invalid_class in ["VPC", "Subnet", "SecurityGroup", "NATGateway"]:
                    hint = f"{invalid_class} are network/logical concepts. Use: with Cluster('{invalid_class}'): ... instead."
                else:
                    hint = f"{invalid_class} is not a valid diagrams.aws class."

                raise ValueError(
                    f"Generated code imports invalid class '{invalid_class}'. {hint}"
                )

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

    def _get_serverless_coder_prompt(self) -> str:
        """Get specialized code generation prompt for serverless architectures.

        Returns:
            str: Gemini system prompt for serverless diagrams
        """
        return """You are CloudForge-Serverless Coder. Generate Python diagrams code for Serverless architectures.

CRITICAL: ONLY import these classes:
Lambda, APIGateway, RDS, S3, SQS, SNS, Kinesis, EC2, ECS

DO NOT IMPORT these (use Clusters instead):
DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy, NATGateway, Route53

SERVERLESS PATTERN RULES:
1. APIGateway → Lambda → RDS (import RDS)
2. Lambda → DynamoDB (use Cluster("DynamoDB Tables"))
3. Lambda → Monitoring (use Cluster("Monitoring"))
4. VPC/Subnets (use Clusters only, not imports)

TEMPLATE FOR SERVERLESS (CORRECT):
import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS

os.makedirs("output", exist_ok=True)

with Diagram("Serverless API", show=False, filename="output/serverless", direction="TB"):
    api = APIGateway("REST API")

    with Cluster("VPC - Private Subnet"):
        func = Lambda("Lambda")
        with Cluster("Database"):
            db = RDS("PostgreSQL")

    with Cluster("DynamoDB Tables"):
        pass  # DynamoDB is a Cluster concept

    api >> func >> db

RULES:
1. Return ONLY Python code (no markdown, no explanations)
2. ONLY import from whitelist: Lambda, APIGateway, RDS, S3, SQS, SNS, Kinesis, EC2, ECS
3. Never import: DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy, NATGateway
4. Use Clusters for: DynamoDB, Monitoring, VPC, Subnets, Security Groups, NAT Gateway
5. Visual nodes are ONLY: Lambda, APIGateway, RDS, S3, SQS, SNS, Kinesis, EC2, ECS
"""


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
