from __future__ import annotations

import re
from dataclasses import dataclass

from src.answering.citations import collect_sources
from src.answering.confidence import confidence_for_context_count
from src.retrieval.models import AskContextPack, ContextDocument


@dataclass(frozen=True)
class Answer:
    body: str
    confidence: str
    sources: tuple[str, ...]


TRIGGER_KEYWORDS = (
    "changed",
    "change",
    "adjusted",
    "adjustment",
    "adjustments",
    "duration",
    "potency",
    "cooldown",
    "recast",
    "변경",
    "조정",
    "상향",
    "하향",
)
NOISE_PHRASES = (
    "current kb-level summary",
    "contains content that can only be accessed",
    "these additions and adjustments require",
    "these additions and adjustments contain elements",
    "final fantasy xiv patch",
    "for further details on changes to actions and traits",
    "playable content",
    "solution nine",
    "the manderville gold saucer",
    "the name of the client for the",
)
NOISE_PREFIXES = (
    "fact:",
    "path:",
    "source_id:",
    "title:",
)
NOISE_LINES = {
    "action name",
    "actions & traits",
    "acquired",
    "cast",
    "effect",
    "graph links",
    "job actions",
    "mp cost",
    "radius",
    "range",
    "recast",
    "related sources",
    "type",
}
ENTITY_LABELS = {
    "item": "Item",
    "job": "Job",
    "patch": "Patch",
    "skill": "Skill",
}
MAX_EVIDENCE = 6
MAX_EVIDENCE_CHARS = 220


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

    related_entities = _related_entities(context_pack.contexts)
    evidence = _extract_evidence(context_pack)
    notes = _build_notes(context_pack.contexts, evidence)
    body = "\n\n".join(
        [
            "핵심 답변",
            "요약\n" + _format_summary(context_pack, related_entities, evidence),
            "관련 항목\n" + _format_related_entities(related_entities),
            "확인된 내용\n" + _format_bullets(evidence),
            "근거 문서\n" + _format_sources(sources),
            "확실도\n" + confidence,
            "주의\n" + _format_bullets(notes),
        ]
    )
    return Answer(body=body, confidence=confidence, sources=sources)


def _format_summary(
    context_pack: AskContextPack,
    related_entities: tuple[tuple[str, str], ...],
    evidence: tuple[str, ...],
) -> str:
    question = context_pack.question.strip()
    entity_summary = ", ".join(title for _, title in related_entities[:3])
    bullets: list[str] = []
    if entity_summary:
        bullets.append(f"{question} 관련 KB context에서 {entity_summary} 항목을 확인했습니다.")
    else:
        bullets.append(f"{question} 관련 KB context를 확인했습니다.")
    if evidence:
        bullets.append("아래 확인된 내용은 검색된 KB context 문장만 압축한 것입니다.")
    else:
        bullets.append("검색된 context 안에서 질문에 직접 답하는 확인 문장은 제한적입니다.")
    return _format_bullets(tuple(bullets))


def _related_entities(contexts: tuple[ContextDocument, ...]) -> tuple[tuple[str, str], ...]:
    entities: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for context in contexts:
        label = ENTITY_LABELS.get(context.wiki_type)
        if label is None:
            continue
        item = (label, context.title)
        if item in seen:
            continue
        seen.add(item)
        entities.append(item)
    return tuple(entities)


def _format_related_entities(entities: tuple[tuple[str, str], ...]) -> str:
    if not entities:
        return "- N/A"
    return "\n".join(f"- {label}: {title}" for label, title in entities)


def _extract_evidence(context_pack: AskContextPack) -> tuple[str, ...]:
    query_terms = _query_terms(context_pack)
    scored: list[tuple[int, int, str]] = []
    sequence = 0
    for context in context_pack.contexts:
        content = context.content_excerpt or context.snippet
        for line in _candidate_lines(content):
            score = _score_line(line, query_terms)
            if context.wiki_type == "item":
                score += _item_evidence_bonus(line)
            if score > 0 and context.wiki_type != "source_summary":
                score += 1
            if score <= 0:
                continue
            scored.append((score, sequence, _truncate(line, MAX_EVIDENCE_CHARS)))
            sequence += 1

    seen: set[str] = set()
    evidence: list[str] = []
    for _, _, line in sorted(scored, key=lambda item: (-item[0], item[1])):
        if line in seen:
            continue
        seen.add(line)
        evidence.append(line)
        if len(evidence) >= MAX_EVIDENCE:
            break
    return tuple(evidence)


def _query_terms(context_pack: AskContextPack) -> tuple[str, ...]:
    parsed = context_pack.parsed_query
    terms = [
        parsed.raw_query,
        parsed.normalized_query,
        parsed.job or "",
        parsed.patch_range or "",
        parsed.topic or "",
        *parsed.terms,
    ]
    return tuple(
        dict.fromkeys(term.lower() for term in terms if term and len(term.strip()) >= 2)
    )


def _candidate_lines(content: str) -> tuple[str, ...]:
    lines: list[str] = []
    for raw_line in re.split(r"[\r\n]+", content):
        line = raw_line.strip()
        if not line:
            continue
        if (
            line.startswith("#")
            or line.startswith("> Source:")
            or line in {"---", "None", "- None"}
        ):
            continue
        line = line.removeprefix("- ").strip()
        if not line:
            continue
        lines.append(line)
    return tuple(lines)


def _score_line(line: str, query_terms: tuple[str, ...]) -> int:
    lower = line.lower()
    if _is_noise_line(lower):
        return 0
    score = 0
    if any(keyword in lower for keyword in TRIGGER_KEYWORDS):
        score += 3
    if any(term in lower for term in query_terms):
        score += 2
    return score


def _item_evidence_bonus(line: str) -> int:
    lower = line.lower()
    if lower.startswith("url: ") and "guide.ff14.co.kr" in lower:
        return 5
    if "no acquisition data" in lower:
        return 5
    return 0


def _is_noise_line(lower_line: str) -> bool:
    stripped = lower_line.strip()
    if stripped in NOISE_LINES:
        return True
    if any(stripped.startswith(prefix) for prefix in NOISE_PREFIXES):
        return True
    if any(phrase in stripped for phrase in NOISE_PHRASES):
        return True
    if "leve" in stripped and "changed" in stripped:
        return True
    return False


def _truncate(value: str, max_chars: int) -> str:
    if len(value) <= max_chars:
        return value
    return value[: max_chars - 1].rstrip() + "..."


def _build_notes(
    contexts: tuple[ContextDocument, ...],
    evidence: tuple[str, ...],
) -> tuple[str, ...]:
    notes = ["context에 없는 내용은 추정하지 않았습니다."]
    has_source_summary = any(context.wiki_type == "source_summary" for context in contexts)
    has_source_ids = any(context.source_ids for context in contexts)
    if not evidence or not (has_source_summary or has_source_ids):
        notes.append("근거가 제한적입니다. 추가 source summary가 들어오면 답변이 달라질 수 있습니다.")
    if any(context.wiki_type in ENTITY_LABELS for context in contexts):
        notes.append("일부 항목은 graph-derived wiki context 기반입니다.")
    return tuple(notes)


def _format_bullets(items: tuple[str, ...]) -> str:
    if not items:
        return "- N/A"
    return "\n".join(f"- {item}" for item in items)


def _format_sources(sources: tuple[str, ...]) -> str:
    if not sources:
        return "- N/A"
    return "\n".join(f"- {source}" for source in sources)
