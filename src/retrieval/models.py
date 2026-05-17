from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RetrievalTarget:
    wiki_type: str | None
    topic: str | None
    query: str
    priority: int


@dataclass(frozen=True)
class RetrievalPlan:
    primary: tuple[RetrievalTarget, ...]
    fallback: tuple[RetrievalTarget, ...]
    limit: int
