from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ENTITY_FILES = ("jobs.json", "skills.json", "patches.json")
TYPE_PREFIX = {
    "Job": "job",
    "Patch": "patch",
    "Skill": "skill",
    "Item": "item",
    "Encounter": "encounter",
    "GearSet": "gearset",
}


@dataclass(frozen=True)
class Entity:
    type: str
    canonical: str
    slug: str
    aliases: tuple[str, ...]
    properties: dict[str, Any]

    @property
    def node_id(self) -> str:
        prefix = TYPE_PREFIX.get(self.type, self.type.casefold())
        return f"{prefix}:{self.slug}"

    @property
    def normalized_aliases(self) -> tuple[str, ...]:
        return tuple(normalize_alias(alias) for alias in self.aliases)


@dataclass(frozen=True)
class AliasEntry:
    alias: str
    normalized_alias: str
    entity: Entity


class EntityRegistry:
    def __init__(
        self,
        entities: list[Entity],
        duplicate_alias_warnings: list[str] | None = None,
    ) -> None:
        self.entities = tuple(sorted(entities, key=lambda item: item.node_id))
        self.entities_by_node_id = {entity.node_id: entity for entity in self.entities}
        self.duplicate_alias_warnings = tuple(duplicate_alias_warnings or [])

        alias_entries: list[AliasEntry] = []
        alias_map: dict[str, Entity] = {}
        for entity in self.entities:
            for alias in entity.aliases:
                normalized = normalize_alias(alias)
                alias_entries.append(AliasEntry(alias, normalized, entity))
                alias_map.setdefault(normalized, entity)

        self.alias_entries = tuple(
            sorted(
                alias_entries,
                key=lambda item: (-len(item.normalized_alias), item.normalized_alias, item.entity.node_id),
            )
        )
        self._alias_map = alias_map

    def resolve_alias(self, alias: str) -> Entity:
        normalized = normalize_alias(alias)
        try:
            return self._alias_map[normalized]
        except KeyError as exc:
            raise KeyError(f"unknown entity alias: {alias}") from exc

    def get(self, node_id: str) -> Entity | None:
        return self.entities_by_node_id.get(node_id)

    def require(self, node_id: str) -> Entity:
        entity = self.get(node_id)
        if entity is None:
            raise KeyError(f"unknown entity node id: {node_id}")
        return entity

    def aliases_for_index(self) -> dict[str, str]:
        return {
            entry.normalized_alias: entry.entity.node_id
            for entry in self.alias_entries
            if entry.normalized_alias
        }

    def skill_job_pairs(self) -> tuple[tuple[Entity, Entity], ...]:
        jobs_by_canonical = {
            entity.canonical.casefold(): entity for entity in self.entities if entity.type == "Job"
        }
        pairs: list[tuple[Entity, Entity]] = []
        for skill in self.entities:
            if skill.type != "Skill":
                continue
            job_name = str(skill.properties.get("job", "")).casefold()
            job = jobs_by_canonical.get(job_name)
            if job is not None:
                pairs.append((job, skill))
        return tuple(sorted(pairs, key=lambda pair: (pair[0].node_id, pair[1].node_id)))


def normalize_alias(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def load_entity_registry(entities_dir: Path | str) -> EntityRegistry:
    root = Path(entities_dir)
    entities: list[Entity] = []
    seen_aliases: dict[str, tuple[str, str]] = {}
    duplicate_warnings: list[str] = []

    for filename in ENTITY_FILES:
        path = root / filename
        if not path.exists():
            continue
        records = json.loads(path.read_text(encoding="utf-8"))
        for record in records:
            entity = _entity_from_record(record)
            entities.append(entity)
            for alias in entity.aliases:
                normalized = normalize_alias(alias)
                previous = seen_aliases.get(normalized)
                if previous is not None and previous[0] != entity.node_id:
                    duplicate_warnings.append(
                        f"duplicate alias '{alias}' maps to {previous[0]} and {entity.node_id}"
                    )
                    continue
                seen_aliases[normalized] = (entity.node_id, alias)

    return EntityRegistry(entities, duplicate_warnings)


def _entity_from_record(record: dict[str, Any]) -> Entity:
    entity_type = str(record["type"])
    canonical = str(record["canonical"])
    slug = str(record["slug"])
    aliases = tuple(str(alias) for alias in record.get("aliases", []))
    if canonical not in aliases:
        aliases = (canonical, *aliases)
    properties = {
        key: value
        for key, value in record.items()
        if key not in {"type", "canonical", "slug", "aliases"}
    }
    return Entity(
        type=entity_type,
        canonical=canonical,
        slug=slug,
        aliases=tuple(dict.fromkeys(aliases)),
        properties=properties,
    )
