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
{
  "title": "Architecture Name",
  "description": "Brief description",
  "nodes": [
    {"name": "API Gateway", "variable": "api_gw", "service_type": "APIGateway", "region": "us-east-1"},
    {"name": "Lambda", "variable": "lambda_func", "service_type": "Lambda", "region": "us-east-1"}
  ],
  "relationships": [
    {"source": "api_gw", "destination": "lambda_func", "connection_type": "default"}
  ],
  "metadata": {"pattern": "serverless", "services_count": 2}
}

RULES:
1. Extract ALL AWS services mentioned
2. Create logical variable names (snake_case)
3. Map to correct service types
4. Include all relationships
5. Return valid JSON
6. Do NOT include abstract concepts (VPC, Subnet, SecurityGroup) as nodes - save for Clusters in code generation
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

        self.system_prompt = """You are CloudForge Diagram Coder. Generate Python diagrams code.

CRITICAL RULES:
1. EVERY string parameter MUST end with closing quote
2. EVERY opening parenthesis MUST have matching closing parenthesis
3. Return ONLY valid Python code (no explanations, no markdown)
4. All imports MUST be from correct modules

CORRECT IMPORT MAPPING:
- compute: Lambda, EC2, ECS, Batch
- database: RDS, ElastiCache, Redshift
- network: APIGateway, ALB, NLB, NATGateway, Route53
- storage: S3, EBS, EFS
- integration: SQS, SNS, Kinesis (NOT queue!)

VALID CLASSES TO IMPORT:
Lambda, EC2, ECS, RDS, S3, APIGateway, ALB, NLB, SQS, SNS, Kinesis, ElastiCache, NATGateway

DO NOT IMPORT (use Clusters instead):
DynamoDB, CloudWatch, CloudTrail, VPC, Subnet, SecurityGroup, RDSProxy

TEMPLATE:
import os
from diagrams import Diagram, Cluster
from diagrams.aws.compute import Lambda
from diagrams.aws.network import APIGateway
from diagrams.aws.database import RDS

os.makedirs("output", exist_ok=True)

with Diagram("Title", show=False, filename="output/diagram", direction="TB"):
    api = APIGateway("API")
    func = Lambda("Function")
    db = RDS("Database")
    api >> func >> db
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

            logger.info("✅ Code generated successfully")
            return code

        except Exception as e:
            logger.error(f"❌ Code generation failed: {str(e)}")
            raise ValueError(f"Code generation failed: {str(e)}")

    def _format_blueprint(self, blueprint: dict[str, Any]) -> str:
        """Format blueprint as text for prompt"""
        text = f"Title: {blueprint.get('title', 'Diagram')}\n"
        text += f"Description: {blueprint.get('description', '')}\n\n"

        text += "Services:\n"
        for node in blueprint.get("nodes", []):
            text += f"- {node['name']} ({node['service_type']})\n"

        text += "\nConnections:\n"
        for rel in blueprint.get("relationships", []):
            text += f"- {rel['source']} >> {rel['destination']}\n"

        return text
