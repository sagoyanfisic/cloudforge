"""LangChain chains for the CloudForge NLP pipeline.

Three chains, each focused on one stage:
  - DescriptionRefinerChain  : vague text → enriched description  (uses multi-agent skill)
  - BlueprintArchitectChain  : enriched description → structured blueprint
  - DiagramCoderChain        : blueprint → Python diagrams code

System prompts are loaded from src/infrastructure/skills/chains/*.md — edit those
files to tune behaviour without touching Python code.
"""

import os
import logging
import re
from pathlib import Path
from typing import Any, Optional

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser

from .models import BlueprintNode, BlueprintRelationship
from .outputs import AwsPatternSkillOutput, BlueprintAnalysisOutput
from .skill import AwsMultiAgentSkillPipeline
from .well_architected_skill import WellArchitectedSkill, WellArchitectedAssessment

load_dotenv()

logger = logging.getLogger(__name__)

_CHAINS_DIR = Path(__file__).parent.parent / "skills" / "chains"


def _load_chain_prompt(filename: str) -> str:
    """Load a chain system prompt from skills/chains/<filename>."""
    path = _CHAINS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(f"⚠️ Chain prompt file not found: {path}")
        return ""


# ---------------------------------------------------------------------------
# DescriptionRefinerChain
# ---------------------------------------------------------------------------

class DescriptionRefinerChain:
    """Refines vague architecture descriptions into detailed, diagram-ready prompts.

    Three-phase process:
    1. AwsMultiAgentSkillPipeline (Architect + Critic → Reviewer) detects patterns
       and enriches context with concrete AWS services.
    2. WellArchitectedSkill evaluates against the 5 AWS Well-Architected pillars
       and recommends missing services for production-grade architecture.
    3. A Gemini LLM uses that context to produce a technically precise description.

    System prompt: skills/chains/refiner.md
    """

    def __init__(self, api_key: Optional[str] = None):
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
            temperature=0.3,
            max_output_tokens=4000,
        ).with_retry(stop_after_attempt=2, wait_exponential_jitter=True)

        self._system_prompt = _load_chain_prompt("refiner.md")
        self._skill_chain = AwsMultiAgentSkillPipeline(api_key)
        self._wellarch_skill = WellArchitectedSkill(api_key)

    def invoke(self, description: str) -> dict:
        """Refine architecture description with AWS pattern-aware and Well-Architected enrichment.

        Returns:
            dict with keys:
              - refined (str): Enhanced description ready for diagram generation
              - patterns (list[str]): Human-readable detected pattern labels
              - recommended_services (list[dict]): [{service, role}] from pattern skill
              - wellarch_assessment (dict): Well-Architected evaluation per pillar
        """
        logger.info("🔧 Refining architecture description...")

        # Step 1: Detect patterns and domain-specific services
        skill_result = self._skill_chain.invoke(description)
        pattern_context = self._build_pattern_context(skill_result)

        # Step 2: Evaluate against Well-Architected Framework
        logger.info("🏛️ Evaluating against Well-Architected Framework...")
        wellarch_result = self._wellarch_skill.invoke(description)
        wellarch_context = self._build_wellarch_context(wellarch_result)

        # Step 3: Build enriched system prompt with both contexts
        system = self._system_prompt
        if pattern_context:
            system += (
                "\n\n## AWS Domain Skills Context\n"
                "Use the information below to guide your refinement:\n\n"
                + pattern_context
            )
        if wellarch_context:
            system += (
                "\n\n## Well-Architected Framework Assessment\n"
                "Ensure the refined description addresses these recommendations:\n\n"
                + wellarch_context
            )

        try:
            messages = [
                SystemMessage(content=system),
                HumanMessage(content=(
                    f"Original architecture description:\n{description}\n\n"
                    "Please refine and enhance this description for diagram generation, "
                    "ensuring it follows AWS best practices for production-grade systems."
                )),
            ]
            response = self.llm.invoke(messages)
            refined = response.content.strip()
            logger.info("✅ Description refined successfully")
        except Exception as e:
            logger.warning(f"⚠️ Description refinement failed: {str(e)}")
            refined = description

        return {
            "refined": refined,
            "patterns": skill_result.pattern_labels,
            "recommended_services": [s.dict() for s in skill_result.recommended_services],
            "wellarch_assessment": {
                "overall_score": wellarch_result.overall_score,
                "pillars": [
                    {
                        "pillar": p.pillar,
                        "score": p.score,
                        "gaps": p.gaps,
                        "recommendations": p.recommendations,
                    }
                    for p in wellarch_result.pillars
                ],
            } if wellarch_result.pillars else {},
        }

    def _build_pattern_context(self, skill_result: AwsPatternSkillOutput) -> str:
        if not skill_result.pattern_labels and not skill_result.recommended_services:
            return ""

        parts = []
        if skill_result.pattern_labels:
            parts.append(f"Detected patterns: {', '.join(skill_result.pattern_labels)}")
        if skill_result.skill_notes:
            parts.append(f"Architectural insight: {skill_result.skill_notes}")
        if skill_result.recommended_services:
            svc_lines = "\n".join(
                f"  - {s.service}: {s.role}"
                for s in skill_result.recommended_services
            )
            parts.append(f"Recommended AWS services to include:\n{svc_lines}")

        return "\n".join(parts)

    def _build_wellarch_context(self, assessment: WellArchitectedAssessment) -> str:
        """Build context from Well-Architected assessment for refinement."""
        if not assessment.pillars:
            return ""

        parts = [f"Overall Well-Architected Score: {assessment.overall_score}/100"]

        for pillar in assessment.pillars:
            pillar_text = f"\n**{pillar.pillar}** (Score: {pillar.score}/100)"
            if pillar.gaps:
                pillar_text += f"\n  Gaps: {', '.join(pillar.gaps)}"
            if pillar.recommendations:
                pillar_text += f"\n  Add: {', '.join(pillar.recommendations)}"
            parts.append(pillar_text)

        return "\n".join(parts)


# ---------------------------------------------------------------------------
# BlueprintArchitectChain
# ---------------------------------------------------------------------------

class BlueprintArchitectChain:
    """Converts an enriched description into a structured architecture blueprint.

    System prompt: skills/chains/blueprint.md
    """

    def __init__(self, api_key: Optional[str] = None):
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
            max_output_tokens=10000,
        ).with_retry(stop_after_attempt=3, wait_exponential_jitter=True)

        self._system_prompt = _load_chain_prompt("blueprint.md")
        self.parser = PydanticOutputParser(pydantic_object=BlueprintAnalysisOutput)

    def invoke(self, description: str) -> dict[str, Any]:
        """Generate blueprint from description.

        Raises:
            ValueError: If generation fails
        """
        logger.info("🏗️ Blueprint Architect analyzing text with LangChain...")

        try:
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=description),
            ]
            response = (self.llm | self.parser).invoke(messages)
            logger.info(f"✅ Blueprint generated: {response.title} ({len(response.nodes)} nodes)")

            return {
                "title": response.title,
                "description": response.description,
                "nodes": [node.dict() for node in response.nodes],
                "clusters": [c.dict() for c in response.clusters],
                "relationships": [rel.dict() for rel in response.relationships],
                "metadata": response.metadata,
            }
        except Exception as e:
            logger.error(f"❌ Blueprint generation failed: {str(e)}")
            raise ValueError(f"Blueprint generation failed: {str(e)}")


# ---------------------------------------------------------------------------
# DiagramCoderChain
# ---------------------------------------------------------------------------

class DiagramCoderChain:
    """Generates Python diagrams code from a structured blueprint.

    All diagrams symbols (AWS, K8S, on-prem, generic, SaaS) are pre-imported
    by the DiagramGenerator — this chain must NOT emit import statements.

    System prompt: skills/chains/coder.md
    """

    def __init__(self, api_key: Optional[str] = None):
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
            max_output_tokens=10000,
        ).with_retry(stop_after_attempt=3, wait_exponential_jitter=True)

        self._system_prompt = _load_chain_prompt("coder.md")

    def invoke(self, blueprint: dict[str, Any]) -> str:
        """Generate Python diagrams code from blueprint.

        Raises:
            ValueError: If generation fails
        """
        logger.info("💻 Diagram Coder generating code with LangChain...")

        try:
            blueprint_text = self._format_blueprint(blueprint)
            imports_hint = self._generate_imports_hint(blueprint)

            human_content = f"Blueprint:\n{blueprint_text}"
            if imports_hint:
                human_content += f"\n{imports_hint}\n"

            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=human_content),
            ]
            response = self.llm.invoke(messages)
            code = response.content.strip().replace("```python", "").replace("```", "").strip()

            if "Diagram" not in code:
                raise ValueError("Generated code missing Diagram context")

            # Post-process: fix common invalid service names that cause NameError
            code = self._fix_invalid_service_names(code)

            # Validate: reject code with any import statements
            self._validate_no_imports(code)

            self._validate_generated_code(code)
            logger.info("✅ Code generated successfully")
            return code

        except Exception as e:
            logger.error(f"❌ Code generation failed: {str(e)}")
            raise ValueError(f"Code generation failed: {str(e)}")

    def _validate_no_imports(self, code: str) -> None:
        """Validate that code contains NO import statements.

        All symbols should be pre-imported by DiagramGenerator.
        Raises ValueError if any import lines are found.
        """
        for line in code.split("\n"):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                raise ValueError(
                    f"Generated code contains forbidden import statement:\n  {stripped}\n"
                    f"DiagramGenerator pre-imports all symbols. Code should start directly with 'with Diagram(...)'"
                )

    def _fix_invalid_service_names(self, code: str) -> str:
        """Fix common service name mistakes that cause NameError.

        The LLM sometimes generates invalid class names. This method fixes them
        automatically before code execution by mapping to actual diagrams symbols.
        """
        replacements = {
            # Database/Data services
            r'OpenSearch\(': 'AmazonOpensearchService(',
            r'Elasticsearch\(': 'ElasticsearchService(',
            r'DynamoDB\(': 'DynamodbTable(',
            # Integration/Messaging services
            r'EventBridge\(': 'Eventbridge(',  # diagrams has Eventbridge (lowercase b), not EventBridge
            # Compute services
            r'AutoScalingGroup\(': 'AutoScaling(',  # diagrams has AutoScaling, not AutoScalingGroup
            # Monitoring/Observability
            r'CloudWatch\(': 'Cloudwatch(',
            r'X-Ray\(': 'XRay(',
            # Security/Secrets Management
            r'Secrets\(': 'SecretsManager(',
            r'Secrets Manager\(': 'SecretsManager(',
            # Services not directly available in diagrams - use Rack fallback
            # Security services
            r'GuardDuty\(': 'Rack(',  # GuardDuty not available, use generic Rack
            r'Inspector\(': 'Rack(',  # Inspector not available, use generic Rack
            r'Macie\(': 'Rack(',      # Macie not available, use generic Rack
            # Media/Content services
            r'MediaConvert\(': 'Rack(',  # MediaConvert not available, use generic Rack
            r'MediaPackage\(': 'Rack(',  # MediaPackage not available, use generic Rack
            r'MediaLive\(': 'Rack(',     # MediaLive not available, use generic Rack
            # AI/ML services
            r'SageMaker\(': 'Rack(',  # SageMaker not available, use generic Rack
            r'Bedrock\(': 'Rack(',    # Bedrock not available, use generic Rack (may have icon in newer versions)
            # IoT services
            r'IoTDevice\(': 'Rack(',      # IoTDevice not available, use generic Rack
            r'IoT\(': 'Rack(',            # IoT not available, use generic Rack
            r'IoTCore\(': 'Rack(',        # IoTCore not available, use generic Rack
            r'IoTGreengrass\(': 'Rack(',  # IoTGreengrass not available, use generic Rack
            r'IoTSiteWise\(': 'Rack(',    # IoTSiteWise not available, use generic Rack
            r'IoTAnalytics\(': 'Rack(',   # IoTAnalytics not available, use generic Rack
            r'IoTEvents\(': 'Rack(',      # IoTEvents not available, use generic Rack
            r'IoTFleetHub\(': 'Rack(',    # IoTFleetHub not available, use generic Rack
            # On-Premise services
            r'OnPremise\(': 'Rack(',     # OnPremise not available, use generic Rack
            r'OnPremises\(': 'Rack(',    # OnPremises not available, use generic Rack
            # Other uncommon services
            r'AppFlow\(': 'Rack(',    # AppFlow not available, use generic Rack
            r'DataExchange\(': 'Rack(',  # DataExchange not available, use generic Rack
            r'FinSpace\(': 'Rack(',    # FinSpace not available, use generic Rack
            r'Forecast\(': 'Rack(',   # Forecast not available, use generic Rack
            r'Lookout\(': 'Rack(',    # Lookout not available, use generic Rack
            r'QuickSight\(': 'Rack(',   # QuickSight not available, use generic Rack
            r'Timestream\(': 'Rack(',   # Timestream not available, use generic Rack
        }

        for pattern, replacement in replacements.items():
            original_code = code
            code = re.sub(pattern, replacement, code)
            if code != original_code:
                logger.info(f"🔧 Fixed service name: {pattern} → {replacement}")

        # Catch-all: Replace any undefined class names with Rack (fallback)
        # This regex catches patterns like "UndefinedClass(" and replaces with "Rack("
        # Only applied if the class name follows AWS naming conventions (CamelCase with alphanumeric)
        code_before_catchall = code
        code = re.sub(r'\b([A-Z][a-zA-Z0-9]*)\(', lambda m: 'Rack(' if m.group(1) not in ['Diagram', 'Cluster', 'Edge', 'Users', 'Internet', 'Rack'] else m.group(0), code)

        if code != code_before_catchall:
            logger.info("🔧 Applied catch-all fallback for undefined service names")

        return code

    def _generate_imports_hint(self, blueprint: dict[str, Any]) -> str:
        services = {node.get("service_type", "") for node in blueprint.get("nodes", []) if node.get("service_type")}
        if not services:
            return ""
        hint = "DETECTED AWS SERVICES (all symbols already imported):\n"
        for service in sorted(services):
            hint += f"  • {service}\n"
        return hint + "\n"

    def _validate_generated_code(self, code: str) -> None:
        lines = code.split("\n")

        for idx, line in enumerate(lines, 1):
            if line.strip().startswith("#"):
                continue
            actual_single = line.count("'") - line.count("\\'")
            actual_double = line.count('"') - line.count('\\"')
            if actual_single % 2 != 0 or actual_double % 2 != 0:
                raise ValueError(f"Unterminated string on line {idx}: {line.strip()}")

        if code.count("(") != code.count(")"):
            raise ValueError("Unmatched parentheses in generated code")

        cluster_vars: set[str] = set()
        connection_pattern = re.compile(r'(\w+)\s*>>\s*(\w+)')
        for line in lines:
            var_match = re.search(r'(\w+)\s*=\s*Cluster', line)
            if var_match:
                cluster_vars.add(var_match.group(1))

        for line in lines:
            for source, dest in connection_pattern.findall(line):
                if source in cluster_vars and dest in cluster_vars:
                    logger.warning(
                        f"⚠️ Potential issue: Connecting Clusters directly "
                        f"({source} >> {dest}). Should connect nodes, not Clusters."
                    )

    def _format_blueprint(self, blueprint: dict[str, Any]) -> str:
        text = f"Title: {blueprint.get('title', 'Diagram')}\n"
        text += f"Description: {blueprint.get('description', '')}\n\n"

        metadata = blueprint.get("metadata", {})
        if metadata:
            environment = metadata.get("environment", "production")
            categories = metadata.get("service_categories", [])
            text += f"Environment: {environment}\n"
            if categories:
                text += f"Service Categories: {', '.join(categories)}\n"
            text += "\n"

        text += "Services to visualize:\n"
        for node in blueprint.get("nodes", []):
            text += f"- {node['name']} (variable: {node['variable']}, type: {node['service_type']})\n"

        clusters = blueprint.get("clusters", [])
        if clusters:
            text += "\nLogical groupings — create a Cluster block for each, nesting subnets inside their VPC:\n"
            for cluster in clusters:
                nodes_str = ", ".join(cluster.get("nodes", []))
                text += f"  - Cluster \"{cluster['name']}\": {nodes_str}\n"
            text += "\n"

        text += "\nConnections between services:\n"
        for rel in blueprint.get("relationships", []):
            conn_type = rel.get("connection_type", "default")
            text += f"- {rel['source']} >> {rel['destination']} [{conn_type}]\n"

        text += "\n⚠️ IMPORTANT STRUCTURE ADVICE:\n"
        text += "- Define each service as a standalone variable OUTSIDE Clusters\n"
        text += "- Then create connections between variables: node1 >> Edge(...) >> node2\n"
        text += "- Use Clusters ONLY to group related services that are in same logical area\n"
        text += "- DO NOT try to connect a node inside a Cluster to nodes outside\n"
        text += "- Keep it simple: most services should be at the root level\n\n"

        best_practices = blueprint.get("best_practices", [])
        if best_practices:
            text += "🎯 AWS BEST PRACTICES TO APPLY:\n"
            for practice in best_practices:
                text += f"  {practice}\n"
            text += "\n"

        return text
