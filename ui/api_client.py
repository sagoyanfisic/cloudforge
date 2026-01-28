"""HTTP Client for CloudForge API

Handles all communication with the FastAPI backend.
"""

import requests
from typing import Optional, Any


class CloudForgeAPIClient:
    """Client for CloudForge REST API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        """Initialize API client.

        Args:
            base_url: Base URL of CloudForge API (default: localhost:8000)
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()

    def health_check(self) -> dict[str, Any]:
        """Check API health status."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "status": "error",
                "pipeline_enabled": False,
                "message": f"API connection failed: {str(e)}",
            }

    def refine_description(self, description: str) -> dict[str, Any]:
        """Refine a brief architecture description into a detailed prompt.

        Args:
            description: Brief or vague architecture description

        Returns:
            Dictionary with success status, original and refined descriptions
        """
        try:
            payload = {"description": description}
            response = self.session.post(
                f"{self.base_url}/v1/diagrams/refine",
                json=payload,
                timeout=60,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "original": description,
                "refined": description,
                "message": f"Refinement request failed: {str(e)}",
            }

    def generate_diagram(self, description: str, name: str) -> dict[str, Any]:
        """Generate diagram from natural language description."""
        try:
            payload = {
                "description": description,
                "name": name,
            }
            response = self.session.post(
                f"{self.base_url}/v1/diagrams/generate",
                json=payload,
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Generation request failed: {str(e)}",
                "errors": [str(e)],
            }

    def get_image_url(self, filename: str) -> str:
        """Get full URL for diagram image."""
        return f"{self.base_url}/images/{filename}"

    def list_diagrams(self, tag: Optional[str] = None) -> dict[str, Any]:
        """List saved diagrams."""
        try:
            params = {}
            if tag:
                params["tag"] = tag

            response = self.session.get(
                f"{self.base_url}/v1/diagrams",
                params=params,
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Failed to list diagrams: {str(e)}",
                "diagrams": [],
            }

    def get_diagram(self, diagram_id: str) -> dict[str, Any]:
        """Get specific diagram details."""
        try:
            response = self.session.get(
                f"{self.base_url}/v1/diagrams/{diagram_id}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Failed to get diagram: {str(e)}",
            }

    def delete_diagram(self, diagram_id: str) -> dict[str, Any]:
        """Delete a saved diagram."""
        try:
            response = self.session.delete(
                f"{self.base_url}/v1/diagrams/{diagram_id}",
                timeout=10,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "message": f"Failed to delete diagram: {str(e)}",
            }
