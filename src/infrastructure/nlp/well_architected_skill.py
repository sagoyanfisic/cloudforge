"""Well-Architected Framework Skill

Evaluates architecture descriptions against the 5 AWS Well-Architected Framework pillars:
  1. Operational Excellence
  2. Security
  3. Reliability
  4. Performance Efficiency
  5. Cost Optimization

Returns recommendations for missing services in each pillar.
"""

import os
import logging
from pathlib import Path
from typing import Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_SKILLS_DIR = Path(__file__).parent.parent / "skills"


class PillarRecommendation(BaseModel):
    """Recommendation for a specific pillar"""

    pillar: str = Field(description="Pillar name (Operational Excellence, Security, etc.)")
    score: int = Field(description="Compliance score 0-100")
    strengths: list[str] = Field(description="What the architecture does well for this pillar")
    gaps: list[str] = Field(description="Services or practices missing for this pillar")
    recommendations: list[str] = Field(description="Recommended services to add")


class WellArchitectedAssessment(BaseModel):
    """Complete Well-Architected assessment"""

    pillars: list[PillarRecommendation] = Field(description="Assessment for each pillar")
    overall_score: int = Field(description="Overall compliance score 0-100")
    summary: str = Field(description="Brief summary of the assessment")


class WellArchitectedSkill:
    """Evaluates architectures against AWS Well-Architected Framework principles.

    Recommendations are loaded from:
        src/infrastructure/skills/well_architected.md
    """

    _WELLARCH_FILE = _SKILLS_DIR / "well_architected.md"

    @classmethod
    def _load_wellarch_guide(cls) -> str:
        try:
            return cls._WELLARCH_FILE.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning(f"⚠️ Well-Architected guide not found: {cls._WELLARCH_FILE}")
            return ""

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
            max_output_tokens=2000,
        ).with_retry(stop_after_attempt=2, wait_exponential_jitter=True)

        self._wellarch_guide = self._load_wellarch_guide()

    def invoke(self, description: str) -> WellArchitectedAssessment:
        """Evaluate architecture against Well-Architected Framework.

        Returns assessment with scores and recommendations per pillar.
        """
        logger.info("🏛️ Evaluating architecture against Well-Architected Framework...")

        try:
            system_prompt = f"""You are an AWS Well-Architected Framework expert.

Evaluate the given architecture description against the 5 AWS Well-Architected Framework pillars:
1. Operational Excellence - run and monitor systems
2. Security - protect information and systems
3. Reliability - ensure resilience and recovery
4. Performance Efficiency - use resources efficiently
5. Cost Optimization - avoid unnecessary costs

For each pillar:
- Identify what the architecture does WELL (strengths)
- Identify GAPS and missing services
- Recommend specific AWS services to add
- Provide a score 0-100 (100 = fully compliant)

Return a JSON assessment with all 5 pillars and an overall score.

## Well-Architected Framework Guidelines
{self._wellarch_guide}

## Task
Evaluate this architecture:
"""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=description),
            ]

            response = self.llm.invoke(messages)
            content = response.content.strip()

            logger.info("✅ Well-Architected assessment completed")

            # Parse the response (simple JSON extraction)
            # In production, use proper JSON parsing with fallback
            import json

            try:
                # Try to extract JSON from response
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0]
                else:
                    json_str = content

                data = json.loads(json_str)
                assessment = WellArchitectedAssessment(**data)
                return assessment
            except Exception as parse_err:
                logger.warning(f"⚠️ Failed to parse assessment: {parse_err}")
                # Return a minimal assessment on parse failure
                return WellArchitectedAssessment(
                    pillars=[],
                    overall_score=0,
                    summary="Assessment parsing failed. Please check the architecture description.",
                )

        except Exception as e:
            logger.error(f"❌ Well-Architected assessment failed: {str(e)}")
            # Return empty assessment on failure (non-blocking)
            return WellArchitectedAssessment(
                pillars=[],
                overall_score=0,
                summary=f"Assessment failed: {str(e)}",
            )
