from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Any, Sequence

from src.domain_graph.entity_extractor import ExtractedEntity
from src.domain_graph.entity_registry import EntityRegistry, normalize_alias


CHANGE_TRIGGERS = (
    "changed",
    "adjusted",
    "potency",
    "recast",
    "duration",
    "effect",
    "added",
    "removed",
    "increased",
    "decreased",
    "now",
    "no longer",
    "변경",
    "조정",
    "위력",
    "재사용",
    "지속시간",
    "효과",
    "추가",
    "삭제",
    "증가",
    "감소",
    "이제",
    "더 이상",
)


@dataclass(frozen=True)
class ExtractedRelation:
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation_type: str
    source_id: str | None
    confidence: float
    properties: dict[str, Any]


@dataclass(frozen=True)
class ExtractedFact:
    node_id: str
    text: str
    subject_node_id: str
    relation: str
    object_node_id: str
    source_id: str
    confidence: float
    properties: dict[str, Any]


@dataclass(frozen=True)
class RelationExtraction:
    edges: tuple[ExtractedRelation, ...]
    facts: tuple[ExtractedFact, ...]


def extract_relations(
    text: str,
    entities: Sequence[ExtractedEntity],
    registry: EntityRegistry,
    *,
    source_id: str,
    wiki_page_id: str | None = None,
) -> RelationExtraction:
    source_node_id = f"src:{source_id}"
    edges: list[ExtractedRelation] = []

    for entity in entities:
        edges.append(
            _edge(
                source_node_id,
                "MENTIONS",
                entity.node_id,
                source_id=source_id,
                confidence=entity.confidence,
                properties={"matched_alias": entity.matched_alias, "span": list(entity.span)},
            )
        )
        if wiki_page_id:
            edges.append(
                _edge(
                    f"page:{wiki_page_id}",
                    "MENTIONS",
                    entity.node_id,
                    source_id=source_id,
                    confidence=entity.confidence,
                    properties={"matched_alias": entity.matched_alias, "span": list(entity.span)},
                )
            )

    for job, skill in registry.skill_job_pairs():
        edges.append(
            _edge(
                job.node_id,
                "HAS_SKILL",
                skill.node_id,
                source_id=None,
                confidence=1.0,
                properties={"source": "registry"},
            )
        )

    facts = _extract_facts(text, entities, registry, source_id=source_id)
    for fact in facts:
        edges.extend(_fact_edges(source_node_id, fact, entities, registry))

    return RelationExtraction(
        edges=tuple(_dedupe_edges(edges)),
        facts=tuple(facts),
    )


def make_edge_id(
    source_node_id: str,
    relation_type: str,
    target_node_id: str,
    source_id: str | None = None,
) -> str:
    return "edge:" + _hash_parts(source_node_id, relation_type, target_node_id, source_id or "")


def make_fact_id(
    source_id: str,
    subject_node_id: str,
    relation: str,
    object_node_id: str,
    fact_text: str,
) -> str:
    return "fact:" + _hash_parts(
        source_id,
        subject_node_id,
        relation,
        object_node_id,
        _normalize_fact_text(fact_text),
    )


def _extract_facts(
    text: str,
    entities: Sequence[ExtractedEntity],
    registry: EntityRegistry,
    *,
    source_id: str,
) -> list[ExtractedFact]:
    if not _has_change_trigger(text):
        return []

    patches = [entity for entity in entities if entity.type == "Patch"]
    subjects = [entity for entity in entities if entity.type == "Skill"]
    if not subjects:
        subjects = [entity for entity in entities if entity.type == "Job"]
    if not patches or not subjects:
        return []

    patch = sorted(patches, key=lambda item: item.canonical)[0]
    subject = sorted(subjects, key=lambda item: (item.type != "Skill", item.canonical))[0]
    fact_text = _first_trigger_sentence(text)
    fact_id = make_fact_id(
        source_id,
        subject.node_id,
        "CHANGED_IN",
        patch.node_id,
        fact_text,
    )
    return [
        ExtractedFact(
            node_id=fact_id,
            text=fact_text,
            subject_node_id=subject.node_id,
            relation="CHANGED_IN",
            object_node_id=patch.node_id,
            source_id=source_id,
            confidence=0.85,
            properties={
                "extraction_method": "rule_based_v1",
                "entity_node_ids": [entity.node_id for entity in entities],
                "inferred_job_node_ids": _job_node_ids_for_entities(entities, registry),
            },
        )
    ]


def _fact_edges(
    source_node_id: str,
    fact: ExtractedFact,
    entities: Sequence[ExtractedEntity],
    registry: EntityRegistry,
) -> list[ExtractedRelation]:
    edges = [
        _edge(source_node_id, "SUPPORTS", fact.node_id, source_id=fact.source_id, confidence=0.85),
        _edge(fact.node_id, "VALID_IN_PATCH", fact.object_node_id, source_id=fact.source_id, confidence=0.85),
    ]
    job_node_ids = _job_node_ids_for_entities(entities, registry)
    skill_node_ids = sorted(entity.node_id for entity in entities if entity.type == "Skill")
    for node_id in job_node_ids:
        edges.append(_edge(fact.node_id, "AFFECTS_JOB", node_id, source_id=fact.source_id, confidence=0.85))
    for node_id in skill_node_ids:
        edges.append(_edge(fact.node_id, "AFFECTS_SKILL", node_id, source_id=fact.source_id, confidence=0.85))
    return edges


def _job_node_ids_for_entities(
    entities: Sequence[ExtractedEntity],
    registry: EntityRegistry,
) -> list[str]:
    job_node_ids = {entity.node_id for entity in entities if entity.type == "Job"}
    jobs_by_canonical = {
        entity.canonical.casefold(): entity.node_id
        for entity in registry.entities
        if entity.type == "Job"
    }
    for entity in entities:
        if entity.type != "Skill":
            continue
        skill = registry.get(entity.node_id)
        if skill is None:
            continue
        job_name = str(skill.properties.get("job", "")).casefold()
        job_node_id = jobs_by_canonical.get(job_name)
        if job_node_id:
            job_node_ids.add(job_node_id)
    return sorted(job_node_ids)


def _edge(
    source_node_id: str,
    relation_type: str,
    target_node_id: str,
    *,
    source_id: str | None,
    confidence: float,
    properties: dict[str, Any] | None = None,
) -> ExtractedRelation:
    return ExtractedRelation(
        edge_id=make_edge_id(source_node_id, relation_type, target_node_id, source_id),
        source_node_id=source_node_id,
        target_node_id=target_node_id,
        relation_type=relation_type,
        source_id=source_id,
        confidence=confidence,
        properties=properties or {},
    )


def _has_change_trigger(text: str) -> bool:
    normalized = normalize_alias(text)
    return any(trigger in normalized for trigger in CHANGE_TRIGGERS)


def _first_trigger_sentence(text: str) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text.strip()) if part.strip()]
    for sentence in sentences:
        if _has_change_trigger(sentence):
            return sentence
    return _normalize_fact_text(text)[:240]


def _normalize_fact_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def _dedupe_edges(edges: list[ExtractedRelation]) -> list[ExtractedRelation]:
    by_id: dict[str, ExtractedRelation] = {}
    for edge in edges:
        by_id[edge.edge_id] = edge
    return [by_id[edge_id] for edge_id in sorted(by_id)]


def _hash_parts(*parts: str) -> str:
    payload = "\x1f".join(parts)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
