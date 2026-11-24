"""The model interface. Provided by DSC. Do not edit.

Messages are plain dicts:
  {"role": "system" | "user", "content": str}
  {"role": "assistant", "tool_call": {"id": str, "name": str, "arguments": dict}}
  {"role": "assistant", "content": str}                      # a final answer
  {"role": "tool", "tool_call_id": str, "name": str, "content": str, "is_error": bool}

LLM.complete returns one of:
  {"type": "tool_call", "id": str, "name": str, "arguments": dict}
  {"type": "final", "content": str}                          # should be TriageNote JSON
"""
from __future__ import annotations

import copy
from typing import Protocol


class LLM(Protocol):
    def complete(self, messages: list[dict], tools: list[dict]) -> dict: ...


class ScriptedLLM:
    """Replays a fixed list of responses and records what it was shown."""

    def __init__(self, responses: list[dict]):
        self.responses = list(responses)
        self.calls: list[dict] = []

    def complete(self, messages: list[dict], tools: list[dict]) -> dict:
        self.calls.append({"messages": copy.deepcopy(messages), "tools": copy.deepcopy(tools)})
        if not self.responses:
            raise RuntimeError("ScriptedLLM ran out of responses")
        return self.responses.pop(0)
