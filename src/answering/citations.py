from __future__ import annotations

from src.retrieval.models import ContextDocument


def collect_sources(contexts: tuple[ContextDocument, ...]) -> tuple[str, ...]:
    sources: list[str] = []
    for context in contexts:
        sources.append(context.path)
        sources.extend(context.source_ids)
    return tuple(dict.fromkeys(source for source in sources if source))
