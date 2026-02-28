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

    Two-phase process:
    1. AwsMultiAgentSkillPipeline (Architect + Critic → Reviewer) detects patterns
       and enriches context with concrete AWS services.
    2. A Gemini LLM uses that context to produce a technically precise description.

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

    def invoke(self, description: str) -> dict:
        """Refine architecture description with AWS pattern-aware enrichment.

        Returns:
            dict with keys:
              - refined (str): Enhanced description ready for diagram generation
              - patterns (list[str]): Human-readable detected pattern labels
              - recommended_services (list[dict]): [{service, role}] from pattern skill
        """
        logger.info("🔧 Refining architecture description...")

        skill_result = self._skill_chain.invoke(description)
        pattern_context = self._build_pattern_context(skill_result)

        system = self._system_prompt
        if pattern_context:
            system += (
                "\n\n## AWS Domain Skills Context\n"
                "Use the information below to guide your refinement:\n\n"
                + pattern_context
            )

        try:
            messages = [
                SystemMessage(content=system),
                HumanMessage(content=(
                    f"Original architecture description:\n{description}\n\n"
                    "Please refine and enhance this description for diagram generation."
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
            max_output_tokens=8000,
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
            max_output_tokens=8000,
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
            # Monitoring/Observability
            r'CloudWatch\(': 'Cloudwatch(',
            r'X-Ray\(': 'XRay(',
            # Security/Secrets Management
            r'\bSecrets\(': 'SecretsManager(',
            r'Secrets Manager\(': 'SecretsManager(',
        }

        for pattern, replacement in replacements.items():
            original_code = code
            code = re.sub(pattern, replacement, code)
            if code != original_code:
                logger.info(f"🔧 Fixed service name: {pattern} → {replacement}")

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
