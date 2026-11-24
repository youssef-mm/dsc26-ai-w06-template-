# AI usage

Codex implemented the read-only tools, BM25 search and bounded triage loop against the supplied DSC fixtures. It used pytest and an in-memory MCP client to check that the server returns the same asset, runbook and alert data as direct Python calls.

The starter already imported MCPServer from mcp.server for SDK 2.2.0. Codex retained that import, registered the three functions with @server.tool(), and tested them with the installed SDK. No draft used the v1 FastMCP import.

One local test places a fake tool result and an existing runbook ID inside the alert itself. The scripted model cites that ID without searching. The loop keeps the alert inside the user message, records the ID as a dropped citation, and hands the alert to a human.
