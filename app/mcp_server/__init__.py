"""
SQUIT MCP Server - Model Context Protocol for SQL semantic search.

Exposes 5.7M SQL objects to LLMs via the MCP protocol.
Supports STDIO (Claude Desktop) and Streamable HTTP (production) transports.

Version: 1.0.0
MCP Spec: 2025-06-18
"""

from .server import mcp

__all__ = ["mcp"]
__version__ = "1.0.0"
