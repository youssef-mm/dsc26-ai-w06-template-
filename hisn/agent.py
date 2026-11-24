"""The triage loop. You write this file. See README.md for the exact eight rules."""
from __future__ import annotations

from hisn.llm import LLM
from hisn.types import TriageResult

# A fixed string. Never contains alert data, host names, IPs or log lines.
SYSTEM_PROMPT: str = ""


def run_triage(alert: dict, llm: LLM, max_steps: int = 6) -> TriageResult:
    """Triage one alert with `llm`, calling tools at most `max_steps` times.

    See README.md "What to build -> hisn/agent.py" for the message sequence, the escaping
    rule for the <alert> block, how tool errors and invalid final answers are handled, how
    citations are checked against runbooks actually retrieved in this run, and the exact
    `trace` and `TriageResult` shape.
    """
    raise NotImplementedError
