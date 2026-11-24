"""Offline BM25 search over the bundled runbooks."""

import math
import re
from collections import Counter
from functools import cache
from pathlib import Path

RUNBOOKS = Path(__file__).parent / "data" / "runbooks"


def _tokens(text: str) -> list[str]:
    return re.findall(r"[^\W_]+", text.casefold())


@cache
def _index():
    documents = []
    document_frequency = Counter()
    for path in sorted(RUNBOOKS.glob("RB-*.md")):
        _, front, body = path.read_text(encoding="utf-8").split("---\n", 2)
        metadata = dict(line.split(": ", 1) for line in front.strip().splitlines())
        snippet = " ".join(line.strip() for line in body.splitlines() if line and not line.startswith("#"))
        terms = Counter(_tokens(f"{metadata['title']} {body}"))
        documents.append((metadata, snippet, terms, terms.total()))
        document_frequency.update(terms.keys())
    count = len(documents)
    idf = {term: math.log1p((count - freq + 0.5) / (freq + 0.5))
           for term, freq in document_frequency.items()}
    return documents, idf, sum(doc[3] for doc in documents) / count


def search_runbooks(query: str, k: int = 3) -> list[dict]:
    """Rank runbooks by lexical relevance and return an excerpt from each."""
    if not query.strip():
        return []
    documents, idf, average_length = _index()
    query_terms = _tokens(query)
    results = []
    for metadata, snippet, terms, length in documents:
        normalization = 1.2 * (0.25 + 0.75 * length / average_length)
        score = sum(idf[term] * terms[term] * 2.2 / (terms[term] + normalization)
                    for term in query_terms if term in terms)
        results.append({**metadata, "snippet": snippet, "score": float(score)})
    results.sort(key=lambda result: (-result["score"], result["id"]))
    return results[:max(1, min(10, k))]
