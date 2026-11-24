"""Runbook search over hisn/data/runbooks. You write this file."""
from __future__ import annotations


def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Search Hisn's SOC runbooks.

    Returns up to `k` results, each `{"id", "title", "snippet", "score"}`, best first, ties
    broken by ID ascending. `k` is clamped to 1-10. A blank (empty or whitespace-only) query
    returns `[]`. Any method is fine (TF-IDF, BM25, …); it must run offline and return the
    right runbook for clear queries. See README.md for the ten runbook IDs and topics.
    """
    raise NotImplementedError
