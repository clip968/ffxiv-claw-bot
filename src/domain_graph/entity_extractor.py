from __future__ import annotations

import re
from dataclasses import dataclass

from src.domain_graph.entity_registry import AliasEntry, EntityRegistry


TYPE_PRIORITY = {
    "Patch": 0,
    "Job": 1,
    "Skill": 2,
    "Item": 3,
    "Encounter": 4,
    "GearSet": 5,
}


@dataclass(frozen=True)
class ExtractedEntity:
    node_id: str
    type: str
    canonical: str
    matched_alias: str
    span: tuple[int, int]
    confidence: float


def extract_entities(text: str, registry: EntityRegistry) -> tuple[ExtractedEntity, ...]:
    matches: list[ExtractedEntity] = []
    occupied_spans: list[tuple[int, int]] = []

    for entry in registry.alias_entries:
        for start, end, matched_alias in _find_alias_matches(text, entry):
            if _overlaps((start, end), occupied_spans):
                continue
            occupied_spans.append((start, end))
            matches.append(
                ExtractedEntity(
                    node_id=entry.entity.node_id,
                    type=entry.entity.type,
                    canonical=entry.entity.canonical,
                    matched_alias=matched_alias,
                    span=(start, end),
                    confidence=_confidence_for_alias(entry.alias),
                )
            )

    deduped = _dedupe_entities(matches)
    return tuple(
        sorted(
            deduped,
            key=lambda item: (
                TYPE_PRIORITY.get(item.type, 99),
                item.canonical.casefold(),
                item.span,
            ),
        )
    )


def _find_alias_matches(text: str, entry: AliasEntry) -> list[tuple[int, int, str]]:
    alias = entry.alias
    if not alias:
        return []

    if _is_ascii_alias(alias):
        flags = 0 if _is_short_uppercase_alias(alias) else re.IGNORECASE
        pattern = _ascii_alias_pattern(alias)
        return [
            (match.start(), match.end(), text[match.start() : match.end()])
            for match in re.finditer(pattern, text, flags)
        ]

    results: list[tuple[int, int, str]] = []
    start = 0
    while True:
        index = text.find(alias, start)
        if index < 0:
            break
        end = index + len(alias)
        results.append((index, end, text[index:end]))
        start = index + 1
    return results


def _ascii_alias_pattern(alias: str) -> str:
    escaped = re.escape(alias)
    boundary_chars = r"A-Za-z0-9_." if any(char.isdigit() or char == "." for char in alias) else r"A-Za-z0-9_"
    return rf"(?<![{boundary_chars}]){escaped}(?![{boundary_chars}])"


def _is_ascii_alias(alias: str) -> bool:
    return all(ord(char) < 128 for char in alias)


def _is_short_uppercase_alias(alias: str) -> bool:
    compact = alias.replace(" ", "")
    return 2 <= len(compact) <= 4 and compact.isupper()


def _confidence_for_alias(alias: str) -> float:
    return 0.85 if _is_short_uppercase_alias(alias) else 0.9


def _overlaps(span: tuple[int, int], occupied_spans: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < occupied_end and end > occupied_start for occupied_start, occupied_end in occupied_spans)


def _dedupe_entities(matches: list[ExtractedEntity]) -> list[ExtractedEntity]:
    by_node_id: dict[str, ExtractedEntity] = {}
    for match in matches:
        existing = by_node_id.get(match.node_id)
        if existing is None or _is_better_match(match, existing):
            by_node_id[match.node_id] = match
    return list(by_node_id.values())


def _is_better_match(candidate: ExtractedEntity, existing: ExtractedEntity) -> bool:
    if len(candidate.matched_alias) != len(existing.matched_alias):
        return len(candidate.matched_alias) > len(existing.matched_alias)
    return candidate.span < existing.span
