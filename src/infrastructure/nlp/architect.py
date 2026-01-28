"""Blueprint Architect - Agent 1 of the NLP pipeline.

Analyzes raw text and generates structured architecture blueprints.
"""

import logging
import os
import re
from typing import Optional

import google.generativeai as genai

from .models import ArchitectureBlueprint

# AWS MCP Clients (optional for best practices enrichment)
try:
    from ..aws_mcp_client import get_aws_documentation_client
    HAS_AWS_MCP = True
except ImportError:
    HAS_AWS_MCP = False
    get_aws_documentation_client = None

logger = logging.getLogger(__name__)


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
        logger.info("Blueprint Architect analyzing text...")

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
                    temperature=0.05,
                    max_output_tokens=5000,
                ),
            )

            blueprint_text = response.text.strip()
            logger.debug(f"Raw response: {blueprint_text[:500]}")

            try:
                blueprint_dict = self._parse_blueprint_text(blueprint_text)
            except ValueError as parse_error:
                logger.error(f"Parse error: {str(parse_error)}")
                logger.error(f"Full response received:\n{blueprint_text[:1000]}")
                raise ValueError(f"Blueprint format invalid. Got: {blueprint_text[:200]}...") from parse_error

            if not blueprint_dict.get("nodes"):
                logger.warning("No nodes parsed from blueprint. Response may be incomplete.")
                logger.warning(f"Blueprint text (first 500 chars):\n{blueprint_text[:500]}")

            blueprint = ArchitectureBlueprint(**blueprint_dict)

            logger.info(f"Blueprint created: {blueprint.title} ({len(blueprint.nodes)} nodes)")
            return blueprint

        except Exception as e:
            logger.error(f"Blueprint generation failed: {str(e)}")
            raise

    def _parse_blueprint_text(self, text: str) -> dict:
        """Parse text-based blueprint format to dictionary.

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
            logger.warning("END_BLUEPRINT marker not found - response may be truncated, using end of text")
            end_idx = len(text)

        # Try alternative markers if primary not found
        if start_idx == -1:
            start_marker = "BEGIN_BLUEPRINT"
            start_idx = text.find(start_marker)

        if end_idx == -1 or (start_idx == -1):
            if start_idx == -1:
                raise ValueError("Blueprint start marker not found in response")
            if end_idx == -1:
                logger.warning("Using end of text as response may be incomplete")
                end_idx = len(text)

        # Calculate proper marker length
        marker_len = len("---BEGIN_BLUEPRINT---") if "---BEGIN_BLUEPRINT---" in text[max(0, start_idx-10):start_idx+30] else len("BEGIN_BLUEPRINT")
        blueprint_content = text[start_idx + marker_len : end_idx].strip()

        # Parse sections
        blueprint_dict: dict = {
            "title": "Generated Architecture",
            "description": "Architecture blueprint from natural language",
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
                cluster_name = line[8:].strip()
                cluster_members: list[str] = []

                while i < len(lines):
                    next_line = lines[i].strip()
                    if not next_line or next_line.startswith("-"):
                        break

                    if next_line.startswith("Members:"):
                        members_str = next_line[8:].strip()
                        cluster_members = [m.strip() for m in members_str.split(",")]

                    i += 1

                blueprint_dict["clusters"].append(
                    {"name": cluster_name, "nodes": cluster_members}
                )

            elif line.startswith("-") and current_section == "relationships":
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

        logger.info(f"Parsed blueprint: Title='{blueprint_dict['title']}', Nodes={len(blueprint_dict['nodes'])}, Clusters={len(blueprint_dict['clusters'])}, Relationships={len(blueprint_dict['relationships'])}")

        return blueprint_dict

    def _detect_serverless(self, text: str) -> bool:
        """Detect if architecture is serverless-based."""
        serverless_keywords = [
            "lambda", "serverless", "api gateway", "dynamodb", "rds proxy",
            "private subnet", "vpc", "security group", "rest api",
            "function", "event-driven", "managed database"
        ]
        text_lower = text.lower()
        return sum(1 for keyword in serverless_keywords if keyword in text_lower) >= 3

    def _enrich_with_aws_best_practices(self, text: str) -> str:
        """Enrich analysis with AWS best practices from AWS Documentation MCP."""
        if not HAS_AWS_MCP or get_aws_documentation_client is None:
            return ""

        if os.getenv("CLOUDFORGE_DISABLE_AWS_MCP", "1") == "1":
            return ""

        try:
            logger.info("Enriching with AWS best practices from documentation server...")
            doc_client = get_aws_documentation_client()

            if not doc_client.is_connected():
                if not doc_client.connect():
                    logger.debug("AWS Documentation server not available (optional feature)")
                    return ""

            services = []
            common_services = ["lambda", "dynamodb", "rds", "api gateway", "s3", "sqs", "sns", "kinesis", "cloudwatch"]
            for service in common_services:
                if service in text.lower():
                    services.append(service)

            if not services:
                return ""

            enrichment = "\n\n--- AWS Best Practices ---\n"

            for service in services[:3]:
                pattern = "serverless" if "lambda" in text.lower() else "general"
                practices = doc_client.get_best_practices(service, pattern)
                if practices:
                    enrichment += f"\n{service.upper()}:\n{practices}\n"

            logger.info(f"Enriched with best practices for: {', '.join(services)}")
            return enrichment

        except Exception as e:
            logger.warning(f"Could not enrich with AWS best practices: {str(e)}")
            return ""

    def _get_serverless_prompt(self) -> str:
        """Get specialized prompt for serverless architectures."""
        return """You are the CloudForge Serverless Architect, expert in AWS Lambda, API Gateway, DynamoDB, and RDS.

GOAL: Design enterprise-grade Serverless architectures with VPC, multi-database support, and RDS connection pooling.

ARCHITECTURE PATTERNS FOR SERVERLESS:

1. **VPC & Security**:
   - Public Subnets: API Gateway endpoints, NAT Gateway
   - Private Subnets: Lambda functions, RDS, DynamoDB
   - Security Groups: Restrict Lambda -> RDS/DynamoDB access

2. **Multi-Database Strategy**:
   - DynamoDB: High-velocity, low-latency NoSQL data (real-time analytics, caching)
   - RDS: Transactional relational data (PostgreSQL/MySQL)
   - RDSProxy: Connection pooling layer between Lambda and RDS (CRITICAL)

3. **API & Compute**:
   - API Gateway: Regional or Private endpoints for REST API
   - Lambda: Serverless compute in private subnets (VPC-enabled)
   - No EC2/ECS unless specifically mentioned

4. **Data Flow**:
   - User -> API Gateway -> Lambda (private subnet)
   - Lambda -> RDSProxy -> RDS (managed connections)
   - Lambda -> DynamoDB (direct, high-speed)
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
