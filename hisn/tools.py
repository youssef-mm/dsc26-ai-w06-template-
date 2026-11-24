"""Read-only lookups for the Hisn triage loop."""

import json
from datetime import datetime, timedelta
from inspect import Parameter, signature
from pathlib import Path

from hisn.retrieval import search_runbooks

DATA = Path(__file__).parent / "data"


def lookup_asset(host: str) -> dict:
    """Look up a host's owner, criticality and environment."""
    key = host.strip().casefold()
    for asset in json.loads((DATA / "assets.json").read_text(encoding="utf-8")):
        if asset["host"].casefold() == key:
            return {**asset, "known": True}
    return {"host": host, "known": False}


def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict:
    """Find alerts on the same agent and rule in the inclusive preceding time window."""
    if type(window_minutes) is not int or not 1 <= window_minutes <= 1440:
        raise ValueError("window_minutes must be an integer between 1 and 1440")
    utc_format = "%Y-%m-%dT%H:%M:%SZ"
    end = datetime.strptime(around, utc_format)
    start = end - timedelta(minutes=window_minutes)
    host = agent.strip().casefold()
    ids = []
    with (DATA / "alerts.jsonl").open(encoding="utf-8") as stream:
        for line in stream:
            alert = json.loads(line)
            if str(alert["rule"]["id"]) != str(rule_id) or alert["agent"]["name"].strip().casefold() != host:
                continue
            if start <= datetime.strptime(alert["timestamp"], utc_format) <= end:
                ids.append(alert["id"])
    return {"count": len(ids), "alert_ids": ids}


TOOLS = {tool.__name__: tool for tool in (lookup_asset, search_runbooks, related_alerts)}


def _schema(tool) -> dict:
    parameters = signature(tool).parameters
    types = {str: "string", int: "integer"}
    return {
        "name": tool.__name__,
        "description": tool.__doc__,
        "input_schema": {
            "type": "object",
            "properties": {name: {"type": types[p.annotation]} for name, p in parameters.items()},
            "required": [name for name, p in parameters.items() if p.default is Parameter.empty],
            "additionalProperties": False,
        },
    }


TOOL_SCHEMAS = [_schema(tool) for tool in TOOLS.values()]
