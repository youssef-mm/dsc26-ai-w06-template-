import json

import anyio
from mcp import Client

from hisn.agent import SYSTEM_PROMPT, run_triage
from hisn.llm import ScriptedLLM
from hisn.server import server
from hisn.tools import lookup_asset, search_runbooks

ALERT = {"id": "A007", "timestamp": "2026-11-14T02:35:00Z",
         "rule": {"id": "5712", "level": 10, "description": "SSHD brute force"},
         "agent": {"name": "web-01"}, "data": {"srcip": "203.0.113.7"},
         "full_log": "Failed password for root from 203.0.113.7 port 52211 ssh2"}

NOTE = {"severity": "high", "summary": "Repeated SSH failures on web-01 from one external IP.",
        "action": "investigate", "next_step": "Check for a successful login after the failures.",
        "citations": ["RB-01"]}


def test_tools_answer_directly():
    assert lookup_asset("WEB-01 ")["criticality"] == "high"
    assert lookup_asset("unknown-host")["known"] is False
    assert search_runbooks("ssh brute force failed logins", k=3)[0]["id"] == "RB-01"


def test_mcp_server_exposes_the_three_tools():
    async def main():
        async with Client(server) as client:
            listed = await client.list_tools()
            return sorted(t.name for t in listed.tools)
    assert anyio.run(main) == ["lookup_asset", "related_alerts", "search_runbooks"]


def test_happy_path_with_a_scripted_model():
    llm = ScriptedLLM([
        {"type": "tool_call", "id": "c1", "name": "search_runbooks", "arguments": {"query": "ssh brute force"}},
        {"type": "final", "content": json.dumps(NOTE)},
    ])
    result = run_triage(ALERT, llm)
    assert result.status == "ok"
    assert result.note.citations == ["RB-01"]
    assert result.steps == 2


def test_alert_text_never_reaches_the_system_prompt():
    llm = ScriptedLLM([{"type": "final", "content": json.dumps(NOTE)}])
    run_triage(ALERT, llm)
    sent = llm.calls[0]["messages"]
    assert sent[0] == {"role": "system", "content": SYSTEM_PROMPT}
    assert "203.0.113.7" not in sent[0]["content"]
    assert "<alert>" in sent[1]["content"] and "203.0.113.7" in sent[1]["content"]


def test_citation_the_agent_never_retrieved_is_dropped():
    llm = ScriptedLLM([{"type": "final", "content": json.dumps(NOTE)}])   # cites RB-01 without searching
    result = run_triage(ALERT, llm)
    assert result.status == "needs_human"
    assert result.dropped_citations == ["RB-01"]
