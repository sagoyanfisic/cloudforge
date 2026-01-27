"""HTTP client for CloudForge API"""

import requests
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class CloudForgeAPIClient:
    """Client for CloudForge REST API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client

        Args:
            base_url: Base URL of the CloudForge API
        """
        self.base_url = base_url
        self.session = requests.Session()

    def generate_diagram(self, description: str, name: str) -> dict[str, Any]:
        """Generate diagram from natural language description

        Args:
            description: Natural language description of the architecture
            name: Diagram name

        Returns:
            Response dictionary with generated code, blueprint, validation, and image URLs
        """
        try:
            response = self.session.post(
                f"{self.base_url}/v1/diagrams/generate",
                json={
                    "description": description,
                    "name": name,
                },
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "message": "Request timeout - generation may be taking longer than expected",
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "message": f"Cannot connect to API at {self.base_url}. Is it running?",
            }
        except requests.exceptions.HTTPError as e:
            return {
                "success": False,
                "message": f"API error: {e.response.status_code} - {e.response.text}",
            }
        except Exception as e:
            logger.error(f"Error generating diagram: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
            }

    def get_history(self) -> dict[str, Any]:
        """Get list of recent diagrams

        Returns:
            Response dictionary with diagram summaries
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/diagrams/history",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting history: {str(e)}")
            return {
                "success": False,
                "diagrams": [],
                "total_count": 0,
            }

    def get_diagram(self, diagram_id: str) -> dict[str, Any]:
        """Get a specific diagram

        Args:
            diagram_id: The diagram ID

        Returns:
            Response dictionary with diagram details
        """
        try:
            response = self.session.get(
                f"{self.base_url}/v1/diagrams/{diagram_id}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error getting diagram: {str(e)}")
            return {
                "success": False,
                "message": f"Error: {str(e)}",
            }

    def health_check(self) -> bool:
        """Check if API is healthy

        Returns:
            True if API is healthy, False otherwise
        """
        try:
            response = self.session.get(
                f"{self.base_url}/health",
                timeout=5,
            )
            return response.status_code == 200
        except Exception:
            return False
