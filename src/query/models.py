from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedQuery:
    raw_query: str
    normalized_query: str
    intent: str | None
    job: str | None
    patch_range: str | None
    topic: str | None
    terms: tuple[str, ...]
