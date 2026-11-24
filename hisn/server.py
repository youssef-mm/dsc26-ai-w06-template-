"""MCP server exposing Hisn's three tools. You write this file (mcp 2.2.0, the v2 SDK)."""
from __future__ import annotations

from mcp.server import MCPServer

server = MCPServer("hisn-triage")

# You write: register lookup_asset, search_runbooks and related_alerts as tools on `server`
# with @server.tool(), using `hisn.tools` and `hisn.retrieval.search_runbooks` underneath. Each
# tool needs the same name and parameters as in tools.py, and a non-empty docstring (the SDK
# builds the tool's description from it and its JSON schema from the type hints).
#
# If an AI assistant writes `from mcp.server.fastmcp import FastMCP` here, that is v1 code: it
# will not import under mcp 2.2.0. Use `MCPServer` as above, and say so in AI_USAGE.md.


if __name__ == "__main__":
    server.run()  # stdio transport by default
