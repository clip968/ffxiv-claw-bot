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


@dataclass(frozen=True)
class SearchResult:
    page_id: str
    title: str
    wiki_type: str
    path: str
    score: float | None
    snippet: str
    topic: str | None
