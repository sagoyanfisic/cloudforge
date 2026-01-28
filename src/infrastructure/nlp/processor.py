"""Natural Language Processor - Orchestrator for the NLP pipeline.

Coordinates BlueprintArchitect and DiagramCoder agents.
"""

import logging
import os
from typing import Optional

from .architect import BlueprintArchitect
from .coder import DiagramCoder

logger = logging.getLogger(__name__)


class NaturalLanguageProcessor:
    """Orchestrator: Manages two-agent pipeline.

    Pipeline:
    1. BlueprintArchitect analyzes raw text -> blueprint
    2. DiagramCoder generates Python code -> diagram
    3. Both are saved for user consumption
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
        logger.info("Starting natural language to diagram pipeline...")

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

            logger.info(f"Pipeline complete! Code saved to {output_path}")

            return {
                "blueprint": blueprint_text,
                "code": code,
                "output_path": output_path,
            }

        except Exception as e:
            logger.error(f"Pipeline failed: {str(e)}")
            raise
