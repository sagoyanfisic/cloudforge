"""Diagram Coder - Agent 2 of the NLP pipeline.

Generates executable Python code from architecture blueprints.
"""

import ast
import logging
import os
import re
from typing import Optional

import google.generativeai as genai

from .models import ArchitectureBlueprint

logger = logging.getLogger(__name__)


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
5. ONLY import from these modules: compute, database, network, storage, integration

CORRECT IMPORT MAPPING:
- compute: Lambda, EC2, ECS, Batch, ElasticBeanstalk
- database: RDS, ElastiCache, Redshift
- network: APIGateway, ALB, NLB, NATGateway, Route53
- storage: S3, EBS, EFS
- integration: SQS, SNS, Kinesis (NOT from queue!)

DO NOT IMPORT (use Clusters instead):
DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy, DBProxy

MINIMAL TEMPLATE (modify ONLY variable names):
import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.network import APIGateway
from diagrams.aws.integration import SQS

os.makedirs("output", exist_ok=True)

with Diagram("Title", show=False, filename="output/diagram", direction="TB"):
    api = APIGateway("API")
    func = Lambda("Func")
    queue = SQS("Queue")
    db = RDS("DB")
    api >> func >> queue >> db

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
        logger.info("Diagram Coder generating Python code...")

        blueprint_text = str(blueprint)
        logger.debug(f"Blueprint input:\n{blueprint_text}")

        is_serverless = any(term in blueprint_text.lower() for term in ["lambda", "api gateway", "dynamodb", "rds proxy"])
        system_prompt = self._get_serverless_coder_prompt() if is_serverless else self.SYSTEM_PROMPT

        try:
            response = self.model.generate_content(
                [system_prompt, f"\nBlueprint:\n{blueprint_text}"],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.05,
                    max_output_tokens=5000,
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

            logger.info("Code generated successfully")
            return code

        except Exception as e:
            logger.error(f"Code generation failed: {str(e)}")
            raise

    def _fix_incomplete_strings(self, code: str) -> str:
        """Fix incomplete strings that were truncated by Gemini."""
        lines = code.split("\n")
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.rstrip()

            if not stripped or stripped.startswith("#"):
                fixed_lines.append(line)
                continue

            # Detect and fix unterminated strings
            double_quote_count = 0
            single_quote_count = 0
            in_escape = False

            for char in stripped:
                if char == '\\':
                    in_escape = True
                elif char == '"' and not in_escape:
                    double_quote_count += 1
                elif char == "'" and not in_escape:
                    single_quote_count += 1
                else:
                    in_escape = False

            if double_quote_count % 2 == 1:
                logger.warning(f"Line {i+1} has unclosed double-quoted string: {stripped[-50:]}")
                if 'Cluster' in stripped or 'Diagram' in stripped:
                    line = stripped + '")'
                else:
                    line = stripped + '"'

            if single_quote_count % 2 == 1:
                logger.warning(f"Line {i+1} has unclosed single-quoted string: {stripped[-50:]}")
                line = stripped + "'"

            # Detect truncated parameter patterns
            if any(stripped.endswith(p) for p in ['direction="', 'filename="', 'direction=', 'filename=']):
                logger.warning(f"Line {i+1} has truncated parameter: {stripped[-40:]}")

                if stripped.endswith('direction="'):
                    line = stripped + 'TB")'
                elif stripped.endswith('direction='):
                    line = stripped + '"TB")'
                elif stripped.endswith('filename="'):
                    line = stripped + 'output/diagram")'
                elif stripped.endswith('filename='):
                    line = stripped + '"output/diagram")'

            elif stripped.endswith('('):
                logger.warning(f"Line {i+1} has unclosed parenthesis: {stripped[-40:]}")
                line = stripped + ')'

            # Check for unmatched parentheses
            open_parens = line.count('(')
            close_parens = line.count(')')
            if open_parens > close_parens:
                paren_diff = open_parens - close_parens
                logger.warning(f"Line {i+1} missing {paren_diff} closing paren(s): {line[:60]}...")
                line = line + ')' * paren_diff

            if stripped.endswith(">>"):
                logger.warning(f"Line {i+1} ends with incomplete arrow operator")
                line = stripped + " None"

            fixed_lines.append(line)

        fixed_code = "\n".join(fixed_lines)

        # Final pass: balance any remaining parentheses
        total_open = fixed_code.count('(')
        total_close = fixed_code.count(')')
        if total_open > total_close:
            remaining_parens = total_open - total_close
            logger.warning(f"Code is missing {remaining_parens} closing paren(s), adding to end")
            if '\n' in fixed_code:
                lines_fixed = fixed_code.split('\n')
                lines_fixed[-1] = lines_fixed[-1] + ')' * remaining_parens
                fixed_code = '\n'.join(lines_fixed)
            else:
                fixed_code = fixed_code + ')' * remaining_parens

        return fixed_code

    def _validate_code_syntax(self, code: str, blueprint_text: str) -> None:
        """Validate Python code syntax and diagrams imports."""
        import_section = code.split("os.makedirs")[0]

        invalid_module_mappings = {
            "diagrams.aws.queue": "diagrams.aws.integration (for SQS, SNS, Kinesis)",
            "diagrams.aws.monitoring": "Monitoring should use Clusters, not imports (CloudWatch, CloudTrail, etc.)",
            "diagrams.aws.security": "Security concepts should use Clusters (SecurityGroup, etc.)",
            "diagrams.aws.network_management": "Network management should use Clusters (VPC, NAT, etc.)",
        }

        for invalid_module, correct_module in invalid_module_mappings.items():
            if f"from {invalid_module}" in import_section:
                logger.error(f"Invalid module in imports: {invalid_module}")
                raise ValueError(
                    f"Generated code imports from invalid module '{invalid_module}'. "
                    f"Use '{correct_module}' instead."
                )

        invalid_import_classes = [
            "SecurityGroup", "Subnet", "VPC", "CloudFlare", "DBProxy", "RDSProxy",
            "DynamoDB", "CloudWatch", "CloudTrail", "NATGateway", "Route53"
        ]
        for invalid_class in invalid_import_classes:
            if f"from diagrams" in import_section and invalid_class in import_section:
                logger.error(f"Invalid class in imports: {invalid_class}")

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
            logger.debug(f"Generated code:\n{code}")
            raise ValueError(
                f"Generated code has syntax error at line {e.lineno}: {e.msg}. "
                "This may indicate the AI model needs a better prompt. Check logs for details."
            )

    def _get_serverless_coder_prompt(self) -> str:
        """Get specialized code generation prompt for serverless architectures."""
        return """You are CloudForge-Serverless Coder. Generate Python diagrams code for Serverless architectures.

CRITICAL: ONLY import these classes:
Lambda, APIGateway, RDS, S3, SQS, SNS, Kinesis, EC2, ECS

DO NOT IMPORT these (use Clusters instead):
DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy, NATGateway, Route53

SERVERLESS PATTERN RULES:
1. APIGateway -> Lambda -> RDS (import RDS)
2. Lambda -> DynamoDB (use Cluster("DynamoDB Tables"))
3. Lambda -> Monitoring (use Cluster("Monitoring"))
4. VPC/Subnets (use Clusters only, not imports)

TEMPLATE FOR SERVERLESS (CORRECT):
import os
from diagrams import Diagram, Cluster
from diagrams.aws.network import APIGateway
from diagrams.aws.compute import Lambda
from diagrams.aws.database import RDS
from diagrams.aws.integration import SQS, SNS, Kinesis

os.makedirs("output", exist_ok=True)

with Diagram("Serverless API", show=False, filename="output/serverless", direction="TB"):
    api = APIGateway("REST API")

    with Cluster("VPC - Private Subnet"):
        func = Lambda("Lambda")
        queue = SQS("Order Queue")
        with Cluster("Database"):
            db = RDS("PostgreSQL")

    with Cluster("DynamoDB Tables"):
        pass  # DynamoDB is a Cluster concept

    api >> func >> queue >> db

CORRECT MODULE MAPPING:
- compute: Lambda, EC2, ECS, Batch
- database: RDS, ElastiCache, Redshift
- network: APIGateway, ALB, NLB, NATGateway, Route53
- storage: S3, EBS, EFS
- integration: SQS, SNS, Kinesis (NOT diagrams.aws.queue!)

RULES:
1. Return ONLY Python code (no markdown, no explanations)
2. Import SQS, SNS, Kinesis FROM diagrams.aws.integration (NOT queue)
3. Never import: DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy, NATGateway
4. Use Clusters for: DynamoDB, Monitoring, VPC, Subnets, Security Groups, NAT Gateway
5. Visual nodes are ONLY: Lambda, APIGateway, RDS, S3, SQS, SNS, Kinesis, EC2, ECS
"""
