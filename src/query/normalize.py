from __future__ import annotations

import re


def normalize_query(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def extract_terms(value: str) -> tuple[str, ...]:
    normalized = normalize_query(value)
    terms = re.findall(r"[a-z0-9_.]+|[가-힣]+", normalized)
    return tuple(term for term in terms if term)
