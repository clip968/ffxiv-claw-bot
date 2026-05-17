from __future__ import annotations

from dataclasses import dataclass

from src.query.models import ParsedQuery


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


@dataclass(frozen=True)
class ContextDocument:
    page_id: str
    wiki_type: str
    title: str
    path: str
    score: float | None
    snippet: str
    content_excerpt: str
    source_ids: tuple[str, ...]


@dataclass(frozen=True)
class AskContextPack:
    question: str
    parsed_query: ParsedQuery
    retrieval_plan: RetrievalPlan
    contexts: tuple[ContextDocument, ...]
    confidence: str
