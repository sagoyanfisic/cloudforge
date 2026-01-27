"""Diagram generation module"""

import subprocess
from pathlib import Path
from typing import Optional
import logging

from src.infrastructure.config import settings

logger = logging.getLogger(__name__)


class DiagramGenerator:
    """Generates diagrams using the diagrams package"""

    def __init__(self) -> None:
        self.temp_dir = settings.diagrams_storage_path
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        code: str,
        diagram_name: str,
        output_formats: list[str],
    ) -> dict[str, str]:
        """Generate diagram from Python code

        Args:
            code: Python code to execute
            diagram_name: Name for the diagram
            output_formats: Output formats (png, pdf, svg)

        Returns:
            Dictionary mapping format -> file path
        """
        output_files: dict[str, str] = {}

        try:
            # Create a temporary script file
            script_file = self.temp_dir / f"{diagram_name}_script.py"

            # Inject output configuration
            modified_code = self._inject_output_config(code, diagram_name)
            script_file.write_text(modified_code, encoding="utf-8")

            # Execute the script
            result = subprocess.run(
                ["python", str(script_file)],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(self.temp_dir),
            )

            if result.returncode != 0:
                logger.error(f"Diagram generation failed: {result.stderr}")
                raise RuntimeError(f"Generation error: {result.stderr}")

            # Check for generated files
            for fmt in output_formats:
                output_file = self.temp_dir / f"{diagram_name}.{fmt}"
                if output_file.exists():
                    output_files[fmt] = str(output_file)
                    logger.info(f"Generated {fmt} diagram: {output_file}")

            return output_files

        except subprocess.TimeoutExpired:
            logger.error("Diagram generation timeout")
            raise RuntimeError("Generation timeout")
        except Exception as e:
            logger.error(f"Generation error: {str(e)}")
            raise

    def _inject_output_config(self, code: str, diagram_name: str) -> str:
        """Inject output directory configuration into the code

        Replaces the filename parameter in the Diagram context manager with the
        proper temporary directory path.
        """
        import re

        # Pattern to match: with Diagram(..., filename="...", show=...)
        # We need to replace filename parameter while keeping other parameters
        pattern = r'(with\s+Diagram\s*\([^)]*filename\s*=\s*)"[^"]*"'

        replacement = f'\\1"{self.temp_dir / diagram_name}"'

        modified_code = re.sub(pattern, replacement, code, count=1)

        # Also ensure show=False is set
        if 'show=False' not in modified_code:
            # If show parameter is missing, add it
            pattern = r'(with\s+Diagram\s*\([^)]*)'
            if 'direction=' in modified_code:
                # If direction is specified, add show=False before it
                pattern = r'(direction\s*=\s*)'
                modified_code = re.sub(pattern, r'show=False, \1', modified_code, count=1)
            else:
                # Otherwise add it at the end before the closing paren
                pattern = r'(\):\s*$)'
                modified_code = re.sub(pattern, r', show=False\1', modified_code, count=1, flags=re.MULTILINE)

        logger.debug(f"Modified code filename parameter to: {self.temp_dir / diagram_name}")
        return modified_code
