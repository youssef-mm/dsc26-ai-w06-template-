"""Hisn's three tools: asset lookup, runbook search, related-alert count. You write this file."""
from __future__ import annotations

from hisn.retrieval import search_runbooks  # re-exported: tests import it from here too

__all__ = ["lookup_asset", "related_alerts", "search_runbooks", "TOOLS", "TOOL_SCHEMAS"]


def lookup_asset(host: str) -> dict:
    """Owner, criticality and environment of a host.

    Match ignoring case and surrounding spaces. Known host: the asset's fields (from
    hisn/data/assets.json) plus `"known": True`. Unknown host: `{"host": host, "known": False}`.
    """
    raise NotImplementedError


def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict:
    """Count alerts with the same rule on the same agent in the window before a time.

    Alerts from hisn/data/alerts.jsonl with the same `rule.id` and `agent.name` (agent compared
    ignoring case), with `around - window_minutes <= timestamp <= around` (both ends inclusive).
    Returns `{"count": int, "alert_ids": [...]}` in file order.
    `ValueError` unless `1 <= window_minutes <= 1440`.
    """
    raise NotImplementedError


# You write these two:
#
# TOOLS: dict mapping each tool's name to the Python function above (plus search_runbooks from
#        retrieval.py), so the agent loop can call `TOOLS[name](**arguments)`.
# TOOL_SCHEMAS: a list of three dicts {"name", "description", "input_schema"}, one per tool, in
#        the same shape `hisn/server.py` and the agent loop expect: `input_schema` is a JSON
#        Schema object with "type": "object", "properties", "required" and
#        "additionalProperties": False. Parameter types are only "string" or "integer".
TOOLS: dict = {}
TOOL_SCHEMAS: list = []
