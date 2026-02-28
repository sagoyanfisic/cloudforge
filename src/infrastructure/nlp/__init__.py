"""NLP subpackage for the CloudForge pipeline.

Provides:
  - Data models (models.py, outputs.py)
  - AWS pattern skill + multi-agent pipeline (skill.py)
  - LangChain chains for refinement, blueprinting, and code generation (chains.py)
"""

from .models import (
    ArchitectureBlueprint,
    BlueprintCluster,
    BlueprintNode,
    BlueprintRelationship,
)
from .outputs import (
    AwsPatternSkillOutput,
    AwsServiceRecommendation,
    BlueprintAnalysisOutput,
    DiagramCodeOutput,
)
from .skill import (
    AwsMultiAgentSkillPipeline,
    AwsPatternSkillChain,
)
from .chains import (
    BlueprintArchitectChain,
    DescriptionRefinerChain,
    DiagramCoderChain,
)

__all__ = [
    # models
    "ArchitectureBlueprint",
    "BlueprintCluster",
    "BlueprintNode",
    "BlueprintRelationship",
    # outputs
    "AwsPatternSkillOutput",
    "AwsServiceRecommendation",
    "BlueprintAnalysisOutput",
    "DiagramCodeOutput",
    # skill pipeline
    "AwsMultiAgentSkillPipeline",
    "AwsPatternSkillChain",
    # chains
    "BlueprintArchitectChain",
    "DescriptionRefinerChain",
    "DiagramCoderChain",
]
