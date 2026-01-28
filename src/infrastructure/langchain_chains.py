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
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from .nlp.models import BlueprintNode, BlueprintRelationship

# Load .env file
load_dotenv()

logger = logging.getLogger(__name__)


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


class DescriptionRefinerChain:
    """LangChain chain for refining vague architecture descriptions into detailed prompts"""

    def __init__(self, api_key: Optional[str] = None):
        """Initialize description refiner chain

        Args:
            api_key: Google API key (if None, uses GOOGLE_API_KEY env var)
        """
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
            temperature=0.3,  # Lower temp for structured refinement
            max_output_tokens=2000,
        ).with_retry(
            stop_after_attempt=2,
            wait_exponential_jitter=True,
        )

        self.system_prompt = """You are a Senior Solution Architect specializing in AWS cloud architectures.

Your task is to enhance and refine vague or brief architecture descriptions into detailed, technically precise prompts optimized for diagram generation.

REFINEMENT INSTRUCTIONS:

1. **Preserve Core Services** - Do NOT add new AWS services unless they are implicit dependencies:
   - Example: Adding VPC, NAT Gateway, or Route 53 if they're needed for described services to work
   - Example: DO NOT add services that weren't mentioned or implied

2. **Detail Data Flows** - Specify interaction patterns:
   - HTTP/HTTPS requests
   - Synchronous vs asynchronous calls
   - Database reads/writes
   - Message queues and event streams
   - Example: "Users access via HTTPS to API Gateway" instead of "Users access API Gateway"

3. **Organize in Layers**:
   - Presentation/Frontend Layer (Users, CloudFront, API Gateway)
   - Application/Compute Layer (Lambda, EC2, ECS)
   - Data Layer (RDS, DynamoDB, S3, ElastiCache)
   - Integration Layer (SQS, SNS, Kinesis, EventBridge)
   - Security/Monitoring Layer (IAM, Secrets Manager, CloudWatch, X-Ray)

4. **Add Technical Context**:
   - Regions and availability zones if relevant
   - Authentication/Authorization mechanisms
   - VPC configuration if applicable
   - High availability patterns
   - Caching strategies
   - Do NOT change the fundamental architecture

5. **Ensure Clarity**:
   - Use clear language
   - Specify connection types
   - Include throughput/scale hints if available
   - Mention disaster recovery or failover patterns if needed

OUTPUT FORMAT:
Return a refined, detailed description that:
- Maintains all original services
- Adds technical interaction details
- Organizes services logically
- Is ready for architecture diagram generation
- Stays focused on AWS services and patterns

IMPORTANT: Only enhance, never remove services mentioned by the user.
"""

    def invoke(self, description: str) -> str:
        """Refine architecture description

        Args:
            description: User's brief or vague architecture description

        Returns:
            str: Refined, detailed description optimized for diagram generation
        """
        logger.info("🔧 Refining architecture description...")

        try:
            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", f"Original architecture description:\n{description}\n\nPlease refine and enhance this description for diagram generation."),
            ])

            chain = prompt | self.llm

            response = chain.invoke({})
            refined = response.content.strip()

            logger.info("✅ Description refined successfully")
            return refined

        except Exception as e:
            logger.warning(f"⚠️ Description refinement failed: {str(e)}")
            logger.info("ℹ️ Proceeding with original description")
            return description  # Fallback to original


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
    """LangChain chain for code generation

    Generates Python code using the diagrams library. All diagrams symbols
    (AWS, K8S, on-prem, generic, SaaS) are pre-imported by the DiagramGenerator.
    """

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
   - Do NOT include "```python" or "```" markers
   - Do NOT include explanatory text before or after the code

4. **NO IMPORT STATEMENTS** - All diagrams symbols are pre-imported
   - Do NOT write "from diagrams import" or "import" statements
   - All AWS services, Kubernetes, on-prem, generic icons are available

5. **ONE LINE PER NODE** - Never split node creation across lines

6. **CLUSTER STRUCTURE - CRITICAL RULE**
   - Nodes INSIDE a Cluster (indented after "with Cluster(...)"):
     * Can only connect to OTHER nodes inside the SAME Cluster
     * Cannot connect to nodes in other Clusters
   - Nodes OUTSIDE Clusters:
     * CAN connect to nodes in other Clusters
   - TO CONNECT BETWEEN CLUSTERS: Place one representative node in EACH cluster at the same level
     * Example: cluster1_node = Lambda(...) inside Cluster1
     * Example: cluster2_node = RDS(...) inside Cluster2
     * Then connect: cluster1_node >> Edge(...) >> cluster2_node

7. **NO CLUSTER-TO-CLUSTER CONNECTIONS** - Only node >> node, NEVER Cluster >> Cluster

8. **PROPER INDENTATION** - Nodes inside Cluster MUST be indented with 4-8 spaces

═══════════════════════════════════════════════════════════════════════════════
VISUAL ORGANIZATION RULES:
═══════════════════════════════════════════════════════════════════════════════

KEEP IT SIMPLE - Define all nodes at the root level first:
  node1 = Lambda("Function")
  node2 = RDS("Database")
  node3 = S3("Storage")

Then connect them:
  node1 >> Edge(label="...") >> node2
  node2 >> Edge(label="...") >> node3

OPTIONAL: Group related services in Clusters for visual organization:
- Use Clusters ONLY for secondary services or grouped monitoring
- Example: Cluster("Monitoring") containing CloudWatch, X-Ray
- Example: Cluster("Storage") containing S3, EBS
- But keep main architecture nodes (entry points, processing, data) outside Clusters

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
AVAILABLE AWS SERVICES - ALL SYMBOLS ARE PRE-IMPORTED:
═══════════════════════════════════════════════════════════════════════════════

You do NOT need to write import statements. All diagrams symbols are automatically available.

AWS SERVICES BY CATEGORY:

COMPUTE: Lambda, EC2, ECS, Batch, Lightsail
DATABASE: RDS, DynamodbTable, ElastiCache, Redshift, Aurora, DocumentDB, Neptune, DAX
STORAGE: S3, EBS, EFS, Glacier, StorageGateway
NETWORK: APIGateway, ALB, NLB, Route53, NATGateway, CloudFront, VPCEndpoint
INTEGRATION: SQS, SNS, Kinesis, EventBridge, MQ
MESSAGING: Kinesis, MSK, SQS, SNS
ANALYTICS: Athena, EMR, Redshift, QuickSight
MONITORING: Cloudwatch, CloudwatchLogs, CloudtrailLogs
SECURITY: IAM, Secrets, ACM, WAF, GuardDuty
GENERAL: Users (generic users), Internet

IMPORTANT:
- DO NOT write import statements - they are pre-loaded
- Use class names exactly as they appear in diagrams package
- Example: DynamodbTable (not DynamoDB)
- Example: Cloudwatch (not CloudWatch)
- If a service has spaces, join them: CloudFront, EventBridge, etc.

INVALID NODES (use as Cluster labels only, not as nodes):
VPC, Subnet, SecurityGroup, RDSProxy, CloudTrail (use as monitoring label)

═══════════════════════════════════════════════════════════════════════════════
SIMPLE WORKING EXAMPLE - RECOMMENDED STRUCTURE:
═══════════════════════════════════════════════════════════════════════════════

with Diagram("Production API", show=False, filename="diagram", direction="TB"):
    # Step 1: Define all main nodes at root level
    users = Users("End Users")
    api = APIGateway("API Gateway")
    func = Lambda("Processing")
    db = RDS("PostgreSQL")
    storage = S3("S3 Bucket")

    # Step 2: Connect them with Edge labels
    users >> Edge(label="Requests") >> api
    api >> Edge(label="Triggers") >> func
    func >> Edge(label="Reads/Writes") >> db
    func >> Edge(label="Stores") >> storage

═══════════════════════════════════════════════════════════════════════════════
OPTIONAL: Add Clusters for secondary/monitoring services:
═══════════════════════════════════════════════════════════════════════════════

with Diagram("Advanced API", show=False, filename="diagram", direction="TB"):
    users = Users("End Users")
    api = APIGateway("API")
    func = Lambda("Lambda")
    db = RDS("Database")

    with Cluster("Observability"):
        logs = Cloudwatch("Logs")
        traces = XRay("Traces")

    # Main flow connects root-level nodes
    users >> api >> func >> db

    # Monitoring is optional side connection
    func >> logs
    func >> traces

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

    def _generate_imports_hint(self, blueprint: dict[str, Any]) -> str:
        """Generate service context hint for the LLM

        Since all diagrams symbols are pre-imported via wildcard imports,
        this just provides a list of detected services as context.

        Args:
            blueprint: Parsed blueprint

        Returns:
            String with service context
        """
        services = set()
        for node in blueprint.get("nodes", []):
            service_type = node.get("service_type", "")
            if service_type:
                services.add(service_type)

        if not services:
            return ""

        hint = "DETECTED AWS SERVICES (all symbols already imported):\n"
        for service in sorted(services):
            hint += f"  • {service}\n"
        hint += "\n"

        return hint

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

            # Add import hints based on services
            imports_hint = self._generate_imports_hint(blueprint)

            full_prompt = f"Blueprint:\n{blueprint_text}"
            if imports_hint:
                full_prompt += f"\n{imports_hint}\n"

            prompt = ChatPromptTemplate.from_messages([
                ("system", self.system_prompt),
                ("human", full_prompt),
            ])

            chain = prompt | self.llm

            response = chain.invoke({})
            code = response.content.strip()

            # Clean markdown wrappers if present
            code = code.replace("```python", "").replace("```", "").strip()

            # Basic validation - must have Diagram
            if "Diagram" not in code:
                raise ValueError("Generated code missing Diagram context")

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

        for line in lines:
            # Find Cluster definitions
            cluster_match = re.search(r'with\s+Cluster\(["\']([^"\']+)["\']\)', line)
            if cluster_match:
                # Extract variable name if present
                var_match = re.search(r'(\w+)\s*=\s*Cluster', line)
                if var_match:
                    cluster_vars.add(var_match.group(1))

        # Check for >> connections between clusters
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
        text += "Services to visualize:\n"
        for node in blueprint.get("nodes", []):
            text += f"- {node['name']} (variable: {node['variable']}, type: {node['service_type']})\n"

        # Connections with types - CRITICAL for structure
        text += "\nConnections between services:\n"
        for rel in blueprint.get("relationships", []):
            conn_type = rel.get("connection_type", "default")
            text += f"- {rel['source']} >> {rel['destination']} [{conn_type}]\n"

        # Architecture advice
        text += "\n⚠️ IMPORTANT STRUCTURE ADVICE:\n"
        text += "- Define each service as a standalone variable OUTSIDE Clusters\n"
        text += "- Then create connections between variables: node1 >> Edge(...) >> node2\n"
        text += "- Use Clusters ONLY to group related services that are in same logical area\n"
        text += "- DO NOT try to connect a node inside a Cluster to nodes outside\n"
        text += "- Keep it simple: most services should be at the root level\n\n"

        # Include AWS best practices if available (from AWS MCP enrichment)
        best_practices = blueprint.get("best_practices", [])
        if best_practices:
            text += "🎯 AWS BEST PRACTICES TO APPLY:\n"
            text += "Ensure the generated code follows these recommendations:\n"
            for practice in best_practices:
                text += f"  {practice}\n"
            text += "\n"

        return text
