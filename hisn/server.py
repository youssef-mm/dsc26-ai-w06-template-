"""Expose the three read-only triage tools over MCP."""

from mcp.server import MCPServer

from hisn import tools

server = MCPServer("hisn-triage")


@server.tool()
def lookup_asset(host: str) -> dict:
    """Look up a host's owner, criticality and environment."""
    return tools.lookup_asset(host)


@server.tool()
def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Search the local runbooks for guidance relevant to the query."""
    return tools.search_runbooks(query, k)


@server.tool()
def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict:
    """Find alerts for this rule and agent in the preceding time window."""
    return tools.related_alerts(rule_id, agent, around, window_minutes)


if __name__ == "__main__":
    server.run()
