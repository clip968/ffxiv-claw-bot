from __future__ import annotations

from dataclasses import dataclass

from src.answering.citations import collect_sources
from src.answering.confidence import confidence_for_context_count
from src.retrieval.models import AskContextPack, ContextDocument


@dataclass(frozen=True)
class Answer:
    body: str
    confidence: str
    sources: tuple[str, ...]


def compose_answer(context_pack: AskContextPack) -> Answer:
    sources = collect_sources(context_pack.contexts)
    confidence = confidence_for_context_count(len(context_pack.contexts))
    if not context_pack.contexts:
        return Answer(
            body=(
                "현재 KB에서 관련 KB 문서를 찾지 못했습니다.\n"
                "context에 없는 내용은 추정하지 않았습니다.\n\n"
                "확실도:\n"
                "N/A"
            ),
            confidence=confidence,
            sources=(),
        )

    body = "\n\n".join(
        [
            "핵심 답변",
            _format_contexts(context_pack.contexts),
            "근거 문서\n" + _format_sources(sources),
            "확실도\n" + confidence,
            "주의\ncontext에 없는 내용은 추정하지 않았습니다.",
        ]
    )
    return Answer(body=body, confidence=confidence, sources=sources)


def _format_contexts(contexts: tuple[ContextDocument, ...]) -> str:
    chunks: list[str] = []
    for context in contexts:
        content = context.content_excerpt or context.snippet
        chunks.append(f"{context.title}\n{content}")
    return "\n\n".join(chunks)


def _format_sources(sources: tuple[str, ...]) -> str:
    if not sources:
        return "- N/A"
    return "\n".join(f"- {source}" for source in sources)
