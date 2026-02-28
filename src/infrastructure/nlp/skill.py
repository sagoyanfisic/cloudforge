"""AWS pattern skill and multi-agent pipeline.

Three-agent pipeline that enriches architecture descriptions with AWS domain knowledge:
  - ArchitectAgent  : detects patterns, recommends services  ─┐ (parallel)
  - CriticAgent     : identifies gaps and anti-patterns       ─┤
  - ReviewerAgent   : synthesizes both into a concise insight  ┘ → AwsPatternSkillOutput

Agent personas are loaded from src/infrastructure/skills/agents/*.md.
The pattern catalog is loaded from src/infrastructure/skills/aws_patterns.md.
"""

import os
import json
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

from .outputs import AwsServiceRecommendation, AwsPatternSkillOutput

logger = logging.getLogger(__name__)

_SKILLS_DIR = Path(__file__).parent.parent / "skills"
_CHAINS_DIR = _SKILLS_DIR / "chains"


def _load_chain_prompt(filename: str) -> str:
    """Load a chain system prompt from skills/chains/<filename>."""
    path = _CHAINS_DIR / filename
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        logger.warning(f"⚠️ Chain prompt file not found: {path}")
        return ""


# ---------------------------------------------------------------------------
# Internal model (used only in this module)
# ---------------------------------------------------------------------------

class CriticOutput(BaseModel):
    """Structured output from the Critic agent"""

    gaps: list[str] = Field(default_factory=list, description="Missing critical components")
    risks: list[str] = Field(default_factory=list, description="Anti-patterns or scalability risks")
    suggestions: list[str] = Field(default_factory=list, description="Concrete additions to fix the gaps")


# ---------------------------------------------------------------------------
# Single-shot pattern chain (lightweight, no multi-agent overhead)
# ---------------------------------------------------------------------------

class AwsPatternSkillChain:
    """Detects AWS architecture patterns from user descriptions and recommends specific services.

    Acts as a domain-expert pre-processor: maps high-level intent (e.g. 'RAG system',
    'data pipeline') to concrete AWS services, key data flows, and critical constraints —
    enriching the refinement context before the description is finalized.

    The pattern catalog is loaded from:
        src/infrastructure/skills/aws_patterns.md

    Edit that file to add/update patterns without touching this code.
    """

    _SKILLS_FILE = _SKILLS_DIR / "aws_patterns.md"

    @classmethod
    def _load_pattern_catalog(cls) -> str:
        try:
            return cls._SKILLS_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning(f"⚠️ Skills file not found: {cls._SKILLS_FILE}. Pattern detection will be limited.")
            return ""

    def __init__(self, api_key: Optional[str] = None):
        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.0,
            max_output_tokens=1200,
        ).with_retry(stop_after_attempt=2, wait_exponential_jitter=True)

        pattern_catalog = self._load_pattern_catalog()
        template = _load_chain_prompt("pattern_skill.md")
        self._system_prompt = template.replace("{PATTERN_CATALOG}", pattern_catalog)

    def invoke(self, description: str) -> AwsPatternSkillOutput:
        """Detect AWS architecture patterns and recommend services.

        Returns empty output (not raises) on failure so the pipeline can continue.
        """
        try:
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=f"Architecture description:\n{description}"),
            ]
            response = self.llm.invoke(messages)
            content = response.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            result = AwsPatternSkillOutput(
                pattern_labels=data.get("pattern_labels", []),
                recommended_services=[
                    AwsServiceRecommendation(**s) for s in data.get("recommended_services", [])
                ],
                skill_notes=data.get("skill_notes", ""),
            )
            logger.info(f"🎯 AWS patterns detected: {result.pattern_labels}")
            return result
        except Exception as e:
            logger.warning(f"⚠️ Pattern detection failed (non-critical): {str(e)}")
            return AwsPatternSkillOutput()


# ---------------------------------------------------------------------------
# Multi-agent pipeline
# ---------------------------------------------------------------------------

class BaseSkillAgent:
    """Base class for skill agents — loads persona/instructions from a SKILL.md file.

    To add a new agent:
    1. Create  src/infrastructure/skills/agents/<name>.md
    2. Subclass BaseSkillAgent and implement invoke()
    3. Register it in AwsMultiAgentSkillPipeline
    """

    _AGENTS_DIR = _SKILLS_DIR / "agents"

    def __init__(self, skill_filename: str, api_key: Optional[str] = None, temperature: float = 0.0):
        self._skill_content = self._load_skill(skill_filename)

        if api_key is None:
            api_key = os.getenv("GOOGLE_API_KEY")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=temperature,
            max_output_tokens=1200,
        ).with_retry(stop_after_attempt=2, wait_exponential_jitter=True)

    def _load_skill(self, filename: str) -> str:
        path = self._AGENTS_DIR / filename
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning(f"⚠️ Skill file not found: {path}")
            return ""


class ArchitectAgent(BaseSkillAgent):
    """Detects AWS architecture patterns and recommends services.
    Loads persona from agents/architect.md + knowledge from aws_patterns.md.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("architect.md", api_key)
        catalog = AwsPatternSkillChain._load_pattern_catalog()
        self._system_prompt = f"{self._skill_content}\n\n---\n\n{catalog}"

    def invoke(self, description: str) -> dict:
        try:
            messages = [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=f"Architecture description:\n{description}"),
            ]
            response = self.llm.invoke(messages)
            content = response.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            logger.info(f"🏗️ Architect detected patterns: {data.get('pattern_labels', [])}")
            return data
        except Exception as e:
            logger.warning(f"⚠️ ArchitectAgent failed: {str(e)}")
            return {}


class CriticAgent(BaseSkillAgent):
    """Identifies gaps, missing components, and anti-patterns.
    Loads persona from agents/critic.md.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("critic.md", api_key)

    def invoke(self, description: str) -> dict:
        try:
            messages = [
                SystemMessage(content=self._skill_content),
                HumanMessage(content=f"Architecture description:\n{description}"),
            ]
            response = self.llm.invoke(messages)
            content = response.content.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            logger.info(f"🔍 Critic found {len(data.get('gaps', []))} gaps, {len(data.get('risks', []))} risks")
            return data
        except Exception as e:
            logger.warning(f"⚠️ CriticAgent failed: {str(e)}")
            return {}


class ReviewerAgent(BaseSkillAgent):
    """Synthesizes Architect + Critic findings into a concise architectural insight.
    Loads persona from agents/reviewer.md.
    """

    def __init__(self, api_key: Optional[str] = None):
        super().__init__("reviewer.md", api_key, temperature=0.2)

    def synthesize(self, description: str, architect: dict, critic: dict) -> str:
        try:
            human_content = (
                f"Original description:\n{description}\n\n"
                f"Architect findings:\n{json.dumps(architect, indent=2)}\n\n"
                f"Critic findings:\n{json.dumps(critic, indent=2)}"
            )
            messages = [
                SystemMessage(content=self._skill_content),
                HumanMessage(content=human_content),
            ]
            response = self.llm.invoke(messages)
            result = response.content.strip()
            logger.info("📝 Reviewer synthesized architectural insight")
            return result
        except Exception as e:
            logger.warning(f"⚠️ ReviewerAgent failed: {str(e)}")
            notes = architect.get("skill_notes", "")
            if critic.get("gaps"):
                notes += f" Missing: {'; '.join(critic['gaps'][:2])}."
            return notes


class AwsMultiAgentSkillPipeline:
    """Multi-agent skill pipeline with parallel execution.

    Runs ArchitectAgent and CriticAgent in parallel (ThreadPoolExecutor),
    then ReviewerAgent synthesizes both outputs into the final enrichment context.

    To add a new agent:
    1. Create  src/infrastructure/skills/agents/<name>.md
    2. Add a subclass of BaseSkillAgent
    3. Add it to _run_parallel_agents() below

    Architecture:
        START
        ├── ArchitectAgent  ─┐  (parallel)
        └── CriticAgent     ─┤
                             ↓
                       ReviewerAgent  (synthesis)
                             ↓
                    AwsPatternSkillOutput
    """

    def __init__(self, api_key: Optional[str] = None):
        self._architect = ArchitectAgent(api_key)
        self._critic = CriticAgent(api_key)
        self._reviewer = ReviewerAgent(api_key)

    def _run_parallel_agents(self, description: str) -> tuple[dict, dict]:
        with ThreadPoolExecutor(max_workers=2) as executor:
            arch_future = executor.submit(self._architect.invoke, description)
            crit_future = executor.submit(self._critic.invoke, description)
            return arch_future.result(timeout=45), crit_future.result(timeout=45)

    def invoke(self, description: str) -> AwsPatternSkillOutput:
        """Run the full multi-agent pipeline.

        Returns empty output on failure so the pipeline never blocks.
        """
        try:
            arch_result, crit_result = self._run_parallel_agents(description)
            skill_notes = self._reviewer.synthesize(description, arch_result, crit_result)

            return AwsPatternSkillOutput(
                pattern_labels=arch_result.get("pattern_labels", []),
                recommended_services=[
                    AwsServiceRecommendation(**s)
                    for s in arch_result.get("recommended_services", [])
                    if isinstance(s, dict) and "service" in s and "role" in s
                ],
                skill_notes=skill_notes,
            )
        except Exception as e:
            logger.warning(f"⚠️ Multi-agent pipeline failed (non-critical): {str(e)}")
            return AwsPatternSkillOutput()
