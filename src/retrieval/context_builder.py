from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Sequence

from src.retrieval.fts_search import search_wiki
from src.query.models import ParsedQuery
from src.retrieval.models import (
    AskContextPack,
    ContextDocument,
    RetrievalPlan,
    RetrievalTarget,
    SearchResult,
)

SearchFn = Callable[..., Sequence[SearchResult]]
ROOT = Path(__file__).resolve().parents[2]
SOURCE_ID_PATTERN = re.compile(r"(?:source_id:\s*|Source:\s*`)([A-Za-z0-9_.:-]+)`?")


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


def build_context_pack(
    question: str,
    parsed_query: ParsedQuery,
    retrieval_plan: RetrievalPlan,
    results: Sequence[SearchResult],
    *,
    root_path: Path | None = None,
    max_chars: int = 2000,
) -> AskContextPack:
    root = root_path or ROOT
    contexts = tuple(
        _context_from_result(result, root_path=root, max_chars=max_chars)
        for result in results
    )
    return AskContextPack(
        question=question,
        parsed_query=parsed_query,
        retrieval_plan=retrieval_plan,
        contexts=contexts,
        confidence="source_grounded" if contexts else "N/A",
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


def _context_from_result(
    result: SearchResult,
    *,
    root_path: Path,
    max_chars: int,
) -> ContextDocument:
    content = _read_content(result.path, root_path)
    return ContextDocument(
        page_id=result.page_id,
        wiki_type=result.wiki_type,
        title=result.title,
        path=result.path,
        score=result.score,
        snippet=result.snippet,
        content_excerpt=content[:max_chars],
        source_ids=_extract_source_ids(content),
    )


def _read_content(path_value: str, root_path: Path) -> str:
    path = Path(path_value)
    if not path.is_absolute():
        path = root_path / path
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_source_ids(content: str) -> tuple[str, ...]:
    return tuple(dict.fromkeys(SOURCE_ID_PATTERN.findall(content)))


def _dedupe_results(results: Sequence[SearchResult]) -> tuple[SearchResult, ...]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        if result.page_id in seen:
            continue
        seen.add(result.page_id)
        deduped.append(result)
    return tuple(deduped)
