"""
Entry point for running SQUIT MCP Server.

Usage:
    python -m app.mcp_server

Environment Variables:
    MCP_TRANSPORT: "stdio" (default) or "http"
    MCP_LOG_LEVEL: "DEBUG", "INFO" (default), "WARNING", "ERROR"
    PORT: HTTP port (default: 8000)
    GOOGLE_APPLICATION_CREDENTIALS: Path to GCP service account JSON
"""

from .server import main

if __name__ == "__main__":
    main()
