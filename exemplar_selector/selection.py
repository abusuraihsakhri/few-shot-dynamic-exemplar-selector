"""Deterministic, dependency-free TF-IDF and MMR few-shot exemplar selection.

This is lexical retrieval, not embedding-based semantic retrieval. Estimated token
counts are a planning heuristic, not model-tokenizer counts.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
import math
import re
from typing import Any

_WORDS = re.compile(r"[a-z0-9]+", re.IGNORECASE)
MAX_EXEMPLARS = 1000
MAX_TEXT_LENGTH = 10000


def _tokens(value: str) -> list[str]:
    return _WORDS.findall(value.lower())


def _token_cost(text: str) -> int:
    return max(1, math.ceil(len(text) / 4))


def _vector(tokens: list[str], idf: dict[str, float]) -> dict[str, float]:
    counts = Counter(tokens)
    weights = {term: count * idf[term] for term, count in counts.items()}
    norm = math.sqrt(sum(weight * weight for weight in weights.values()))
    return {term: weight / norm for term, weight in weights.items()} if norm else {}


def _cosine(a: dict[str, float], b: dict[str, float]) -> float:
    return sum(weight * b.get(term, 0.0) for term, weight in a.items())


def select_exemplars(
    query: str,
    exemplars: Sequence[Mapping[str, Any]],
    *,
    k: int = 3,
    diversity: float = 0.65,
    token_budget: int | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    """Return exemplars selected by maximal marginal relevance.

    MMR = diversity * relevance - (1 - diversity) * max(selected similarity).
    Larger diversity favors query relevance; smaller values penalize redundancy.
    """
    if not isinstance(query, str) or not query.strip() or len(query) > MAX_TEXT_LENGTH:
        raise ValueError("query must be nonempty text of at most 10000 characters")
    if type(k) is not int or not 1 <= k <= 50:
        raise ValueError("k must be an integer between 1 and 50")
    if isinstance(diversity, bool) or not isinstance(diversity, (int, float)) or not math.isfinite(diversity) or not 0 <= diversity <= 1:
        raise ValueError("diversity must be a finite number between 0 and 1")
    if token_budget is not None and (type(token_budget) is not int or not 1 <= token_budget <= 100000):
        raise ValueError("token_budget must be an integer between 1 and 100000")
    if domain is not None and (not isinstance(domain, str) or len(domain) > 100):
        raise ValueError("domain must be a string of at most 100 characters")
    if not isinstance(exemplars, Sequence) or isinstance(exemplars, (str, bytes)) or len(exemplars) > MAX_EXEMPLARS:
        raise ValueError("exemplars must be an array of at most 1000 items")

    validated: list[dict[str, Any]] = []
    ids: set[str] = set()
    for index, item in enumerate(exemplars):
        if not isinstance(item, Mapping):
            raise ValueError(f"exemplar {index} must be an object")
        entry = {}
        for key in ("id", "input", "output"):
            value = item.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > MAX_TEXT_LENGTH:
                raise ValueError(f"exemplar {index} field '{key}' must be nonempty text of at most 10000 characters")
            entry[key] = value
        category = item.get("domain", "")
        if not isinstance(category, str) or len(category) > 100:
            raise ValueError(f"exemplar {index} domain must be text of at most 100 characters")
        entry["domain"] = category
        if entry["id"] in ids:
            raise ValueError(f"duplicate exemplar id: {entry['id']}")
        ids.add(entry["id"])
        if domain is None or category.casefold() == domain.casefold():
            validated.append(entry)

    if not validated:
        return {"selected": [], "candidate_count": 0, "estimated_tokens": 0, "method": "tfidf-mmr"}

    documents = [_tokens(query)] + [_tokens(e["input"]) for e in validated]
    document_frequencies: Counter[str] = Counter()
    for tokens in documents:
        document_frequencies.update(set(tokens))
    count = len(documents)
    idf = {term: math.log((count + 1) / (freq + 1)) + 1 for term, freq in document_frequencies.items()}
    vectors = [_vector(tokens, idf) for tokens in documents]
    query_vec = vectors[0]
    candidate_vecs = vectors[1:]
    relevance = [_cosine(query_vec, vec) for vec in candidate_vecs]
    remaining = list(range(len(validated)))
    selected_indices: list[int] = []
    results: list[dict[str, Any]] = []
    consumed = 0

    while remaining and len(results) < k:
        eligible = [
            i for i in remaining
            if token_budget is None or consumed + _token_cost(validated[i]["input"] + "\n" + validated[i]["output"]) <= token_budget
        ]
        if not eligible:
            break

        def scores(i: int) -> tuple[float, float, int]:
            redundancy = max((_cosine(candidate_vecs[i], candidate_vecs[j]) for j in selected_indices), default=0.0)
            score = diversity * relevance[i] - (1 - diversity) * redundancy
            return score, relevance[i], -i

        winner = max(eligible, key=scores)
        score, _, _ = scores(winner)
        entry = validated[winner]
        cost = _token_cost(entry["input"] + "\n" + entry["output"])
        results.append({
            **entry,
            "rank": len(results) + 1,
            "relevance": round(relevance[winner], 6),
            "mmr_score": round(score, 6),
            "estimated_tokens": cost,
        })
        consumed += cost
        selected_indices.append(winner)
        remaining.remove(winner)

    return {
        "selected": results,
        "candidate_count": len(validated),
        "estimated_tokens": consumed,
        "method": "tfidf-mmr",
    }
