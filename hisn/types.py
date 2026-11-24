"""Output types. Provided by DSC. Do not edit."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class TriageNote(BaseModel):
    model_config = ConfigDict(extra="forbid")
    severity: Literal["low", "medium", "high", "critical"]
    summary: str = Field(min_length=1, max_length=600)
    action: Literal["escalate", "investigate", "monitor"]   # there is no "close"
    next_step: str = Field(min_length=1, max_length=400)
    citations: list[str] = Field(default_factory=list)       # runbook ids, e.g. "RB-04"


class TriageResult(BaseModel):
    status: Literal["ok", "needs_human"]
    note: TriageNote | None = None
    reason: str | None = None        # None when ok; "no_valid_citations" | "invalid_output" | "step_limit"
    dropped_citations: list[str] = Field(default_factory=list)
    steps: int = 0                   # number of LLM calls made
    trace: list[dict] = Field(default_factory=list)
