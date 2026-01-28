"""Diagram generation module"""

import subprocess
from pathlib import Path
from typing import Optional
import logging
import re

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

            # Inject output configuration and dynamic imports
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
        """Inject dynamic imports and output configuration into the code

        Prepends wildcard imports for all diagrams modules, similar to AWS MCP Server approach.
        Also ensures show=False and proper output filename.
        """
        # Get absolute path for the output
        output_filename = str((self.temp_dir / diagram_name).expanduser().absolute())

        # Prepend dynamic imports (wildcard imports like AWS MCP Server)
        imports = """import os
from diagrams import Diagram, Cluster, Edge
from diagrams.aws.cost import *
from diagrams.aws.ar import *
from diagrams.aws.general import *
from diagrams.aws.database import *
from diagrams.aws.management import *
from diagrams.aws.ml import *
from diagrams.aws.game import *
from diagrams.aws.enablement import *
from diagrams.aws.network import *
from diagrams.aws.quantum import *
from diagrams.aws.iot import *
from diagrams.aws.robotics import *
from diagrams.aws.migration import *
from diagrams.aws.mobile import *
from diagrams.aws.compute import *
from diagrams.aws.media import *
from diagrams.aws.engagement import *
from diagrams.aws.security import *
from diagrams.aws.devtools import *
from diagrams.aws.integration import *
from diagrams.aws.business import *
from diagrams.aws.analytics import *
from diagrams.aws.blockchain import *
from diagrams.aws.storage import *
from diagrams.aws.satellite import *
from diagrams.aws.enduser import *
from diagrams.onprem.vcs import *
from diagrams.onprem.database import *
from diagrams.onprem.gitops import *
from diagrams.onprem.workflow import *
from diagrams.onprem.etl import *
from diagrams.onprem.inmemory import *
from diagrams.onprem.identity import *
from diagrams.onprem.network import *
from diagrams.onprem.cd import *
from diagrams.onprem.container import *
from diagrams.onprem.certificates import *
from diagrams.onprem.mlops import *
from diagrams.onprem.dns import *
from diagrams.onprem.compute import *
from diagrams.onprem.logging import *
from diagrams.onprem.registry import *
from diagrams.onprem.security import *
from diagrams.onprem.client import *
from diagrams.onprem.groupware import *
from diagrams.onprem.iac import *
from diagrams.onprem.analytics import *
from diagrams.onprem.messaging import *
from diagrams.onprem.tracing import *
from diagrams.onprem.ci import *
from diagrams.onprem.search import *
from diagrams.onprem.storage import *
from diagrams.onprem.auth import *
from diagrams.onprem.monitoring import *
from diagrams.onprem.aggregator import *
from diagrams.onprem.queue import *
from diagrams.k8s.others import *
from diagrams.k8s.rbac import *
from diagrams.k8s.network import *
from diagrams.k8s.ecosystem import *
from diagrams.k8s.compute import *
from diagrams.k8s.chaos import *
from diagrams.k8s.infra import *
from diagrams.k8s.podconfig import *
from diagrams.k8s.controlplane import *
from diagrams.k8s.clusterconfig import *
from diagrams.k8s.storage import *
from diagrams.k8s.group import *
from diagrams.generic.database import *
from diagrams.generic.blank import *
from diagrams.generic.network import *
from diagrams.generic.virtualization import *
from diagrams.generic.place import *
from diagrams.generic.device import *
from diagrams.generic.compute import *
from diagrams.generic.os import *
from diagrams.generic.storage import *
from diagrams.saas.crm import *
from diagrams.saas.identity import *
from diagrams.saas.chat import *
from diagrams.saas.recommendation import *
from diagrams.saas.cdn import *
from diagrams.saas.communication import *
from diagrams.saas.media import *
from diagrams.saas.logging import *
from diagrams.saas.security import *
from diagrams.saas.social import *
from diagrams.saas.alerting import *
from diagrams.saas.analytics import *
from diagrams.saas.automation import *
from diagrams.saas.filesharing import *

"""

        # Remove existing imports from user code to avoid duplicates
        lines = code.split('\n')
        filtered_lines = []
        for line in lines:
            stripped = line.strip()
            if not stripped.startswith('import ') and not stripped.startswith('from '):
                filtered_lines.append(line)

        user_code = '\n'.join(filtered_lines)

        # Process the code to ensure show=False and proper filename
        if 'with Diagram(' in user_code:
            # Find all instances of Diagram constructor
            diagram_pattern = r'with\s+Diagram\s*\((.*?)\)'
            matches = re.findall(diagram_pattern, user_code)

            for match in matches:
                original_args = match.strip()
                new_args = original_args

                # Check if filename parameter exists
                has_filename = 'filename=' in original_args
                has_show = 'show=' in original_args

                # Replace or add filename parameter
                if has_filename:
                    # Replace existing filename
                    filename_pattern = r'filename\s*=\s*[\'"][^\'"]*[\'"]'
                    new_args = re.sub(filename_pattern, f"filename='{output_filename}'", new_args)
                else:
                    # Add filename parameter
                    if new_args and not new_args.endswith(','):
                        new_args += ', '
                    new_args += f"filename='{output_filename}'"

                # Add show=False if not present
                if not has_show:
                    if new_args and not new_args.endswith(','):
                        new_args += ', '
                    new_args += 'show=False'

                # Replace in code
                user_code = user_code.replace(
                    f'with Diagram({original_args})',
                    f'with Diagram({new_args})'
                )

        # Combine imports with processed user code
        modified_code = imports + user_code

        logger.debug(f"Injected dynamic imports and set filename to: {output_filename}")
        return modified_code
