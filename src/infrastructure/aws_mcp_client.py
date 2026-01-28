"""AWS MCP Remote Client - Access AWS diagram and documentation servers

This client connects to AWS Labs MCP servers (awslabs.aws-diagram-mcp-server and
awslabs.aws-documentation-mcp-server) via stdio to enhance CloudForge with:

1. AWS Diagram Server: Alternative diagram generation with AWS best practices
2. AWS Documentation Server: Real-time AWS documentation for best practices enrichment
"""

import logging
import subprocess
import json
from typing import Any, Optional, Dict
import sys

logger = logging.getLogger(__name__)


class AWSDocumentationMCPClient:
    """Client for AWS Documentation MCP Server

    Provides tools to:
    - search_documentation: Search AWS docs for best practices
    - read_documentation: Get specific documentation
    - recommend: Get recommendations for architecture patterns
    """

    def __init__(self):
        """Initialize AWS Documentation MCP Client"""
        self._connected = False
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    def connect(self) -> bool:
        """Start AWS Documentation MCP server process

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("🔗 Connecting to AWS Documentation MCP server...")

            # Start the documentation server as subprocess
            self.process = subprocess.Popen(
                ["uvx", "awslabs.aws-documentation-mcp-server@latest"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            self._connected = True
            logger.info("✅ AWS Documentation MCP server connected")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to AWS Documentation server: {str(e)}")
            self._connected = False
            return False

    def search_documentation(self, query: str) -> Dict[str, Any]:
        """Search AWS documentation

        Args:
            query: Search query (e.g., "serverless best practices")

        Returns:
            dict: Search results with relevant documentation
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to MCP server"}

        try:
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "tools/call",
                "params": {
                    "name": "search_documentation",
                    "arguments": {"query": query}
                }
            }

            # Send request
            if self.process and self.process.stdin:
                self.process.stdin.write(json.dumps(request) + "\n")
                self.process.stdin.flush()

                # Read response
                if self.process.stdout:
                    response_text = self.process.stdout.readline()
                    response = json.loads(response_text)

                    logger.debug(f"Documentation search result: {response}")
                    return response.get("result", {})

            return {"success": False, "error": "Failed to send request"}

        except Exception as e:
            logger.error(f"❌ Documentation search failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def get_best_practices(self, service: str, pattern: str) -> str:
        """Get AWS best practices for a specific service and pattern

        Args:
            service: AWS service (e.g., "Lambda", "DynamoDB", "RDS")
            pattern: Architecture pattern (e.g., "serverless", "microservices")

        Returns:
            str: Best practices recommendations
        """
        query = f"best practices for {service} in {pattern} architectures"
        result = self.search_documentation(query)

        if result.get("success"):
            return result.get("content", "No recommendations found")

        return f"Unable to retrieve best practices for {service}"

    def close(self) -> None:
        """Close MCP server connection"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.warning(f"Error closing AWS Documentation server: {str(e)}")

        self._connected = False
        logger.info("✅ AWS Documentation MCP client closed")

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self.process is not None and self.process.poll() is None


class AWSDiagramMCPClient:
    """Client for AWS Diagram MCP Server

    Alternative diagram generation using AWS Labs implementation.
    Can be used as:
    1. Validation of CloudForge-generated diagrams
    2. Fallback if Gemini generation fails
    3. Comparison/benchmarking
    """

    def __init__(self):
        """Initialize AWS Diagram MCP Client"""
        self._connected = False
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    def connect(self) -> bool:
        """Start AWS Diagram MCP server process

        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info("🔗 Connecting to AWS Diagram MCP server...")

            # Start the diagram server as subprocess
            self.process = subprocess.Popen(
                ["uvx", "awslabs.aws-diagram-mcp-server"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            self._connected = True
            logger.info("✅ AWS Diagram MCP server connected")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to AWS Diagram server: {str(e)}")
            self._connected = False
            return False

    def generate_diagram(self, description: str, name: str = "diagram") -> Dict[str, Any]:
        """Generate diagram using AWS MCP server

        Args:
            description: Architecture description in natural language
            name: Diagram name

        Returns:
            dict: Generated diagram info (code, image path, etc.)
        """
        if not self._connected:
            return {"success": False, "error": "Not connected to MCP server"}

        try:
            self.request_id += 1
            request = {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "tools/call",
                "params": {
                    "name": "create_diagram",
                    "arguments": {
                        "description": description,
                        "diagram_name": name
                    }
                }
            }

            # Send request
            if self.process and self.process.stdin:
                self.process.stdin.write(json.dumps(request) + "\n")
                self.process.stdin.flush()

                # Read response
                if self.process.stdout:
                    response_text = self.process.stdout.readline()
                    response = json.loads(response_text)

                    logger.debug(f"AWS Diagram generation result: {response}")
                    return response.get("result", {})

            return {"success": False, "error": "Failed to send request"}

        except Exception as e:
            logger.error(f"❌ AWS Diagram generation failed: {str(e)}")
            return {"success": False, "error": str(e)}

    def close(self) -> None:
        """Close MCP server connection"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.warning(f"Error closing AWS Diagram server: {str(e)}")

        self._connected = False
        logger.info("✅ AWS Diagram MCP client closed")

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self.process is not None and self.process.poll() is None


# Global singleton instances
_aws_doc_client: Optional[AWSDocumentationMCPClient] = None
_aws_diagram_client: Optional[AWSDiagramMCPClient] = None


def get_aws_documentation_client() -> AWSDocumentationMCPClient:
    """Get or create AWS Documentation MCP client"""
    global _aws_doc_client
    if _aws_doc_client is None:
        _aws_doc_client = AWSDocumentationMCPClient()
    return _aws_doc_client


def get_aws_diagram_client() -> AWSDiagramMCPClient:
    """Get or create AWS Diagram MCP client"""
    global _aws_diagram_client
    if _aws_diagram_client is None:
        _aws_diagram_client = AWSDiagramMCPClient()
    return _aws_diagram_client
