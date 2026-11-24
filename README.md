# W6 task · Hisn: a triage loop that cites its runbook and never closes an alert

DSC Summer Internship 2026 · AI & Deep Tech track · Week 6 · expected time 3–4 hours

## Scenario

Karim wants the core of his night-shift copilot, but he will not let a model near production
until he has seen how the loop behaves when the model misbehaves. You will build the tools
(asset lookup, runbook search, related-alert count), expose them through an MCP server, and
write the triage loop. The grader drives your loop with a scripted model that makes every
mistake a real model makes, including following instructions planted in a log line. There is no
real model anywhere in this task: `ScriptedLLM` plays that part, deterministically.

## Set up

1. Open this starter (`dsc26-ai-w06-starter`), **Use this template → Create a new repository**,
   owner your own account, name exactly **`dsc26-ai-w06`**.
2. Clone, `uv sync`, `uv run pytest` (the public tests fail until you write the code).

Versions: Python 3.12, numpy 2.5.3, pandas 3.0.6, scikit-learn 1.9.1, scipy 1.18.1, pydantic
2.13.5, mcp 2.2.0 (the official MCP Python SDK, **v2 line**; it brings `anyio` and
`mcp-types`), pytest 9.1.1. Nothing else: the grader has nothing else installed. If an AI
assistant writes `from mcp.server.fastmcp import FastMCP`, that is v1 code and will not import
under mcp 2.2.0 — use `from mcp.server import MCPServer` instead, and log the mistake in
`AI_USAGE.md`.

## Layout

```
dsc26-ai-w06/
├── pyproject.toml          # provided, do not change the dependencies
├── hisn/
│   ├── __init__.py
│   ├── llm.py               # provided: LLM protocol, ScriptedLLM (do not edit)
│   ├── types.py              # provided: TriageNote, TriageResult (do not edit)
│   ├── data/                 # provided: runbooks/RB-01.md … RB-10.md, assets.json, alerts.jsonl
│   ├── retrieval.py          # you write
│   ├── tools.py               # you write
│   ├── server.py              # you write
│   └── agent.py                # you write
├── tests/test_public.py
└── AI_USAGE.md
```

The grader restores `hisn/llm.py`, `hisn/types.py` and `hisn/data/` from DSC's own copies before
running, so edits there have no effect on your score.

## Provided data

**Runbooks** (`hisn/data/runbooks/RB-01.md` … `RB-10.md`), each Markdown with front matter
(`id`, `title`) and a body: SSH brute force, malware detected by antivirus, web application
attack, privilege escalation on Linux, suspicious PowerShell, file integrity change, port scan,
data exfiltration suspicion, account lockout, ransomware indicators.

**`assets.json`**: four hosts for two Hisn clients — `web-01` and `dev-07` (Nile Retail),
`db-02` and `hr-laptop-12` (Delta Hospital) — each with `owner`, `criticality`, `env`.

**`alerts.jsonl`**: Wazuh-style alerts (`id`, ISO `timestamp` ending in `Z`, `rule.id`,
`rule.level`, `rule.description`, `agent.name`, `data`, `full_log`). It includes a burst of
twelve SSH-brute-force alerts on `web-01` five minutes apart (`A000`–`A011`), a file-integrity
alert `A100` on `db-02` whose `full_log` contains a planted prompt injection (closing
`</alert>` early and a fake `SYSTEM:` instruction, as text — not executable), and a PowerShell
alert `A101` on `hr-laptop-12`.

## What to build

### `hisn/retrieval.py`

```python
def search_runbooks(query: str, k: int = 3) -> list[dict]: ...
```

Each result is `{"id", "title", "snippet", "score"}`, best first, ties by ID ascending. `k` is
clamped to 1–10. A blank query returns `[]`. Any method is fine (TF-IDF, BM25 from W4, or
anything else); it must run offline and return the right runbook for clear queries such as "ssh
brute force failed logins" → `RB-01`.

### `hisn/tools.py`

```python
def lookup_asset(host: str) -> dict: ...
def related_alerts(rule_id: str, agent: str, around: str, window_minutes: int = 60) -> dict: ...
TOOLS: dict
TOOL_SCHEMAS: list
```

- `lookup_asset`: match ignoring case and surrounding spaces. Known host: the asset's fields
  from `assets.json` plus `"known": True`. Unknown host: `{"host": host, "known": False}`.
- `related_alerts`: alerts in `alerts.jsonl` with the same `rule.id` (compared as strings) and
  `agent.name` (ignoring case), with `around - window_minutes <= timestamp <= around`, **both
  ends inclusive**. Returns `{"count": int, "alert_ids": [...]}` in file order (the order the
  alerts appear in `alerts.jsonl`, not sorted). `ValueError` unless
  `1 <= window_minutes <= 1440`.
- `TOOLS`: `{"lookup_asset": ..., "search_runbooks": ..., "related_alerts": ...}` — plain
  Python functions, so the agent loop can call `TOOLS[name](**arguments)`.
- `TOOL_SCHEMAS`: a list of exactly three dicts `{"name", "description", "input_schema"}`.
  `input_schema` is `{"type": "object", "properties": {...}, "required": [...],
  "additionalProperties": False}`. Parameter types are only `"string"` or `"integer"`
  (`window_minutes` and `k` are integers; everything else is a string).

### `hisn/server.py`

A module-level `server = MCPServer("hisn-triage")` exposing exactly these three tools — same
names, same parameters, a non-empty docstring each (the SDK turns it into the tool's
description) — registered with `@server.tool()`, built on top of `hisn.tools` and
`hisn.retrieval.search_runbooks`. `server.run()` under `if __name__ == "__main__":`.

### `hisn/agent.py`

```python
SYSTEM_PROMPT: str
def run_triage(alert: dict, llm: LLM, max_steps: int = 6) -> TriageResult: ...
```

1. The first message is `{"role": "system", "content": SYSTEM_PROMPT}`. `SYSTEM_PROMPT` is a
   fixed constant string and **never** contains alert data, host names, IPs or log text.
2. The second message is a user message built as: the literal text `<alert>`, a newline, the
   alert as `json.dumps(alert, sort_keys=True, ensure_ascii=False)` with every literal `<`
   character replaced by the six-character escape \u003c and every literal `>` replaced by
   \u003e, a newline, and the literal text `</alert>`. Because the alert's own `<` and `>`
   characters are escaped this way, the resulting string contains **exactly one** `<alert>` and
   **exactly one** `</alert>`, whatever the alert's fields say — including an alert whose
   `full_log` contains the literal text `</alert>` or `<script>`. Decoding is the inverse: take
   the text between the opening and closing tags and `json.loads` it; because \u003c/\u003e
   are standard JSON escapes for `<`/`>`, this reconstructs the original alert dict exactly.
   (The curriculum states this rule as "replace `<` and `>`"; this is the one reading under
   which the invariant — exactly one opening and one closing tag, and lossless decoding — can
   hold for every possible alert. See "Deviations from the curriculum" in the task's `README.md`
   in the private package if you want the exact wording DSC Ops uses.)
3. Call `llm.complete(messages, TOOL_SCHEMAS)` at most `max_steps` times. Each call is one step.
4. On a tool call: append the assistant `tool_call` message, then exactly one `tool` message
   with the same `tool_call_id`.
   - Unknown tool name: content starts with `"unknown tool"`, `is_error` true.
   - Arguments that are not a JSON object, miss a required key, contain a key the schema does
     not list, or have the wrong type (a bool is **not** an integer): content starts with
     `"invalid arguments"`, `is_error` true.
   - The tool itself raises: content starts with `"tool error"`, `is_error` true, and never
     contains a traceback.
   - Otherwise: content is the tool's return value as JSON, `is_error` false. Remember every
     runbook ID returned by `search_runbooks` during this run (across all steps).
5. On a final answer: append it as an assistant message, then validate it with
   `TriageNote.model_validate_json`. If it does not validate, append a user message that starts
   with `"Your last answer was not valid"` and asks for JSON only, and continue the loop. After
   the **third** invalid final answer in a run, stop and return `needs_human` with reason
   `invalid_output`.
6. On a valid note: keep only the citations that were returned by `search_runbooks` at some
   point in this run, in their original order; put the rest in `dropped_citations`. If none of
   the note's citations remain, return `needs_human` with reason `no_valid_citations` and the
   (filtered) note attached. Otherwise return `ok` with the filtered note.
7. If `max_steps` calls are used up without a final answer being accepted, return `needs_human`
   with reason `step_limit`.
8. `trace` has one entry per step: `{"step": n, "type": "tool_call" | "final", "ok": bool}`,
   plus `"name"` (the tool's name) for tool-call steps. `steps` is the number of `llm.complete`
   calls actually made.

## `AI_USAGE.md`

Tools and what for; whether your assistant produced MCP v1 code (`FastMCP`) and how you
noticed; one hostile model move you thought of that the spec does not mention, and what your
loop does with it. Read by your Track Mentor, not graded by tests.

## How grading works

Push, then **Submit for grading** on DSC Hex. The grader clones that commit, restores
`hisn/llm.py`, `hisn/types.py` and `hisn/data/`, and runs the hidden tests on Python 3.12 with
the versions above, network off, 60 seconds per test, 5 minutes in all. Score 0–100 with
feedback per test name; each test is all or nothing; up to five runs per task per day; the best
attempt counts.

| Test name | What it checks | Points |
|---|---|---|
| `lookup_asset_rules` | Case, spaces, unknown host shape | 5 |
| `runbook_search_relevance` | Top-3 contains the expected runbook for 12 hidden queries (at least 10 of 12) | 8 |
| `runbook_search_limits` | `k` clamped to 1–10, blank query, result fields and order | 4 |
| `related_alerts_window` | Inclusive window edges, other agents and rules excluded, bad window raises | 6 |
| `mcp_lists_three_tools_with_schemas` | Names, non-empty descriptions, required parameters in each input schema | 8 |
| `mcp_call_matches_direct_call` | `call_tool` through the in-memory MCP `Client` returns the same data as the Python function; unknown tool gives `is_error` | 6 |
| `happy_path_variants` | Three scripted runs with different tool orders end `ok` with the right steps and citations | 8 |
| `untrusted_alert_stays_in_its_block` | Constant system prompt; alert with `</alert>`, `<script>` and "ignore previous instructions" text yields exactly one opening and one closing tag; JSON inside decodes back to the original alert | 10 |
| `unknown_tool_and_bad_arguments` | `close_alert`, missing argument, extra argument, wrong type, bool for integer; each answered with one tool error and the loop continues | 9 |
| `tool_exception_is_contained` | A tool that raises returns `tool error` content with no traceback; loop continues | 5 |
| `repair_then_success` | Invalid JSON, then a valid note: one repair message, status `ok` | 7 |
| `close_is_never_accepted` | `"action": "close"` three times ends `needs_human` / `invalid_output` | 5 |
| `citations_must_be_retrieved` | Mixed valid and invented IDs: order kept, invented ones dropped; all invented gives `no_valid_citations` | 8 |
| `step_limit` | A model that only calls tools: LLM called exactly `max_steps` times, `step_limit` | 6 |
| `trace_and_message_shapes` | One trace entry per step with the right fields; every tool call answered by exactly one tool message with the matching ID | 5 |

Late policy: ×1.0 within 72 hours of the session starting, ×0.6 in the following 7 days, ×0.5
after that until the W8 deadline. During W5 (consolidation week) you can resubmit at ×1.0.

If you are stuck for more than an hour, ask in the AI track channel on Discord or ask Hexa
rather than spending grader runs.
