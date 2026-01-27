"""MCP Client - Direct module-based access to MCP Server tools"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MCPDirectClient:
    """Direct client for accessing MCP server tools via Python imports"""

    def __init__(self):
        """Initialize MCP direct client"""
        self._connected = False
        self.server = None

    def connect(self) -> bool:
        """Initialize MCP server tools

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Import server tools directly
            from .server import (
                generate_diagram,
                validate_diagram,
                list_diagrams,
                get_diagram,
                delete_diagram,
                generate_from_description,
            )

            self.generate_diagram = generate_diagram
            self.validate_diagram = validate_diagram
            self.list_diagrams = list_diagrams
            self.get_diagram = get_diagram
            self.delete_diagram = delete_diagram
            self.generate_from_description = generate_from_description

            self._connected = True
            logger.info("✅ MCP tools imported successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to import MCP tools: {str(e)}")
            self._connected = False
            return False

    def close(self) -> None:
        """Close MCP connection"""
        self._connected = False
        logger.info("✅ MCP client closed")

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected


# Global singleton instance
_mcp_client: Optional[MCPDirectClient] = None


def get_mcp_client() -> MCPDirectClient:
    """Get or create global MCP client instance"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPDirectClient()
    return _mcp_client
