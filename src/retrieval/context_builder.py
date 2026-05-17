from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from src.retrieval.fts_search import search_wiki
from src.retrieval.models import RetrievalPlan, RetrievalTarget, SearchResult

SearchFn = Callable[..., Sequence[SearchResult]]


def execute_retrieval_plan(
    plan: RetrievalPlan,
    *,
    db_path: Path | None = None,
    search_fn: SearchFn = search_wiki,
) -> tuple[SearchResult, ...]:
    primary_results = _run_targets(
        plan.primary,
        limit=plan.limit,
        db_path=db_path,
        search_fn=search_fn,
    )
    if primary_results:
        return primary_results

    return _run_targets(
        plan.fallback,
        limit=plan.limit,
        db_path=db_path,
        search_fn=search_fn,
    )


def _run_targets(
    targets: tuple[RetrievalTarget, ...],
    *,
    limit: int,
    db_path: Path | None,
    search_fn: SearchFn,
) -> tuple[SearchResult, ...]:
    for target in sorted(targets, key=lambda item: item.priority):
        results = search_fn(
            target.query,
            wiki_type=target.wiki_type,
            topic=target.topic,
            limit=limit,
            db_path=db_path,
        )
        deduped = _dedupe_results(results)
        if deduped:
            return deduped[:limit]
    return ()


def _dedupe_results(results: Sequence[SearchResult]) -> tuple[SearchResult, ...]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        if result.page_id in seen:
            continue
        seen.add(result.page_id)
        deduped.append(result)
    return tuple(deduped)
