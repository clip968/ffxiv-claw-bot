from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.domain_graph.entity_extractor import extract_entities
from src.domain_graph.entity_registry import Entity, load_entity_registry
from src.domain_graph.relation_extractor import ExtractedFact, ExtractedRelation, extract_relations
from src.domain_graph.storage import (
    ensure_graph_schema,
    make_edge_id,
    reset_domain_graph as reset_domain_graph_storage,
    upsert_edge,
    upsert_fact,
    upsert_node,
)
from src.guide_ff14.storage import ensure_guide_ff14_schema
from src.source_processing.job_guide import (
    clean_official_job_guide_text,
    detect_official_job_slug,
)


DB_PATH = ROOT / "db" / "ffxiv.sqlite"
WIKI_ROOT = ROOT / "wiki"
ENTITIES_DIR = ROOT / "data" / "ffxiv_entities"
GRAPH_DIR = ROOT / "graph"


@dataclass(frozen=True)
class SourceSummary:
    source_id: str
    page_id: str
    title: str
    path: Path
    relative_path: str
    body: str
    job: str | None = None
    source_kind: str | None = None


@dataclass(frozen=True)
class GuideItemGraphRecord:
    id: str
    name: str
    url: str
    category: str | None
    subcategory: str | None
    item_level: int | None
    equip_level: int | None
    jobs: tuple[str, ...]
    source: dict[str, Any]
    raw_path: str


def rebuild_domain_graph(
    *,
    db_path: Path = DB_PATH,
    wiki_root: Path = WIKI_ROOT,
    entities_dir: Path = ENTITIES_DIR,
    graph_dir: Path = GRAPH_DIR,
    dry_run: bool = False,
    source_id: str | None = None,
    reset_domain_graph: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    registry = load_entity_registry(entities_dir)
    summaries = _load_source_summaries(wiki_root, source_id=source_id)

    if dry_run:
        return {
            "status": "ok",
            "dry_run": True,
            "planned_sources": len(summaries),
            "planned_registry_nodes": len(registry.entities),
            "source_id": source_id,
            "actions": ["scan_source_summaries", "load_entity_registry"],
        }

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        ensure_graph_schema(conn)
        if reset_domain_graph:
            reset_domain_graph_storage(conn)

        _upsert_registry_nodes(conn, registry.entities)
        source_count = 0
        fact_count = 0
        edge_count = 0
        item_count = 0

        for summary in summaries:
            source_count += 1
            _upsert_source_summary_nodes(conn, summary)
            entities = extract_entities(summary.body, registry)
            extraction = extract_relations(
                summary.body,
                entities,
                registry,
                source_id=summary.source_id,
                wiki_page_id=summary.page_id,
            )
            for fact in extraction.facts:
                upsert_fact(conn, _fact_to_node(fact))
                fact_count += 1
            for edge in extraction.edges:
                upsert_edge(conn, _edge_to_dict(edge))
                edge_count += 1

        for item in _load_guide_items(conn):
            _upsert_guide_item_graph(conn, item)
            item_count += 1

        export_result = _maybe_export(conn, graph_dir)
        report_result = _maybe_report(conn, graph_dir)
    finally:
        conn.close()

    result = {
        "status": "ok",
        "dry_run": False,
        "sources": source_count,
        "facts": fact_count,
        "edges": edge_count,
        "items": item_count,
        "source_id": source_id,
        "export": export_result,
        "report": report_result,
    }
    if verbose:
        result["graph_dir"] = str(graph_dir)
        result["db_path"] = str(db_path)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Rebuild the v08 FFXIV domain graph.")
    parser.add_argument("--db-path", type=Path, default=DB_PATH)
    parser.add_argument("--wiki-root", type=Path, default=WIKI_ROOT)
    parser.add_argument("--entities-dir", type=Path, default=ENTITIES_DIR)
    parser.add_argument("--graph-dir", type=Path, default=GRAPH_DIR)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source-id")
    parser.add_argument("--reset-domain-graph", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    result = rebuild_domain_graph(
        db_path=args.db_path,
        wiki_root=args.wiki_root,
        entities_dir=args.entities_dir,
        graph_dir=args.graph_dir,
        dry_run=args.dry_run,
        source_id=args.source_id,
        reset_domain_graph=args.reset_domain_graph,
        verbose=args.verbose,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def _load_source_summaries(
    wiki_root: Path,
    *,
    source_id: str | None,
) -> list[SourceSummary]:
    summary_dir = wiki_root / "source_summaries"
    if not summary_dir.exists():
        return []

    summaries: list[SourceSummary] = []
    for path in sorted(summary_dir.glob("*.md")):
        text = path.read_text(encoding="utf-8")
        resolved_source_id = _parse_source_id(text) or path.stem
        if source_id is not None and resolved_source_id != source_id:
            continue
        title = _parse_title(text) or path.stem
        body = _strip_summary_header(text)
        official_job = detect_official_job_slug(title, body)
        if official_job:
            body = clean_official_job_guide_text(body, official_job)
        page_id = f"wiki_{resolved_source_id.removeprefix('src_')}"
        summaries.append(
            SourceSummary(
                source_id=resolved_source_id,
                page_id=page_id,
                title=title,
                path=path,
                relative_path=_relative_path(path, wiki_root.parent),
                body=body,
                job=official_job,
                source_kind="official_job_guide" if official_job else None,
            )
        )
    return summaries


def _upsert_registry_nodes(conn: sqlite3.Connection, entities: tuple[Entity, ...]) -> None:
    for entity in entities:
        upsert_node(
            conn,
            {
                "id": entity.node_id,
                "type": entity.type,
                "name": entity.canonical,
                "canonical_name": entity.canonical,
                "aliases": list(entity.aliases),
                "properties": entity.properties,
            },
        )


def _upsert_source_summary_nodes(conn: sqlite3.Connection, summary: SourceSummary) -> None:
    source_node_id = f"src:{summary.source_id}"
    page_node_id = f"page:{summary.page_id}"
    source_properties = {"path": summary.relative_path, "title": summary.title}
    page_properties = {"path": summary.relative_path, "source_id": summary.source_id}
    if summary.job:
        source_properties["job"] = summary.job
        page_properties["job"] = summary.job
    if summary.source_kind:
        source_properties["source_kind"] = summary.source_kind
        page_properties["source_kind"] = summary.source_kind
    upsert_node(
        conn,
        {
            "id": source_node_id,
            "type": "SourceDocument",
            "name": summary.source_id,
            "canonical_name": summary.source_id,
            "properties": source_properties,
        },
    )
    upsert_node(
        conn,
        {
            "id": page_node_id,
            "type": "WikiPage",
            "name": summary.title,
            "canonical_name": summary.title,
            "properties": page_properties,
        },
    )
    upsert_edge(
        conn,
        {
            "source_node_id": source_node_id,
            "target_node_id": page_node_id,
            "relation_type": "SOURCE_OF",
            "source_id": summary.source_id,
            "confidence": 1.0,
            "source_page_id": summary.relative_path,
        },
    )


def _load_guide_items(conn: sqlite3.Connection) -> list[GuideItemGraphRecord]:
    ensure_guide_ff14_schema(conn)
    rows = conn.execute(
        """
        SELECT id, name, url, category, subcategory, item_level, equip_level,
               jobs_json, source_json, raw_path
          FROM guide_items
         ORDER BY id
        """
    ).fetchall()
    return [
        GuideItemGraphRecord(
            id=row[0],
            name=row[1],
            url=row[2],
            category=row[3],
            subcategory=row[4],
            item_level=row[5],
            equip_level=row[6],
            jobs=tuple(_json_loads(row[7], [])),
            source=dict(_json_loads(row[8], {})),
            raw_path=row[9],
        )
        for row in rows
    ]


def _upsert_guide_item_graph(conn: sqlite3.Connection, item: GuideItemGraphRecord) -> None:
    item_node_id = f"item:{item.id}"
    source_node_id = f"src:guide_ff14:{item.id}"
    upsert_node(
        conn,
        {
            "id": item_node_id,
            "type": "Item",
            "name": item.name,
            "canonical_name": item.name,
            "properties": {
                "official_url": item.url,
                "category": item.category,
                "subcategory": item.subcategory,
                "item_level": item.item_level,
                "equip_level": item.equip_level,
                "raw_path": item.raw_path,
            },
        },
    )
    upsert_node(
        conn,
        {
            "id": source_node_id,
            "type": "SourceDocument",
            "name": item.url,
            "canonical_name": item.url,
            "properties": {
                "source_kind": "guide_ff14_item_detail",
                "url": item.url,
                "path": item.raw_path,
            },
        },
    )
    _upsert_item_edge(
        conn,
        item_node_id,
        "DERIVED_FROM",
        source_node_id,
        item.id,
        {"official_url": item.url},
    )
    category_name = item.subcategory or item.category
    if category_name:
        category_node_id = f"item_category:{_slug(category_name)}"
        upsert_node(
            conn,
            {
                "id": category_node_id,
                "type": "ItemCategory",
                "name": category_name,
                "canonical_name": category_name,
            },
        )
        _upsert_item_edge(conn, item_node_id, "ITEM_IN_CATEGORY", category_node_id, item.id)
    for job in item.jobs:
        job_node_id = f"equipment_job:{_slug(job)}"
        upsert_node(
            conn,
            {
                "id": job_node_id,
                "type": "EquipmentJob",
                "name": job,
                "canonical_name": job,
            },
        )
        _upsert_item_edge(conn, item_node_id, "EQUIPPABLE_BY_JOB", job_node_id, item.id)
    if item.item_level is not None:
        _upsert_item_edge(
            conn,
            item_node_id,
            "HAS_ITEM_LEVEL",
            item_node_id,
            item.id,
            {"value": item.item_level},
        )
    if item.equip_level is not None:
        _upsert_item_edge(
            conn,
            item_node_id,
            "HAS_EQUIP_LEVEL",
            item_node_id,
            item.id,
            {"value": item.equip_level},
        )
    source_text = str(item.source.get("text") or "").strip()
    if source_text:
        item_source_node_id = f"item_source:{item.id}:{_slug(source_text)[:24]}"
        upsert_node(
            conn,
            {
                "id": item_source_node_id,
                "type": "ItemSource",
                "name": source_text,
                "canonical_name": source_text,
                "properties": item.source,
            },
        )
        _upsert_item_edge(conn, item_node_id, "OBTAINED_FROM", item_source_node_id, item.id)


def _upsert_item_edge(
    conn: sqlite3.Connection,
    source_node_id: str,
    relation_type: str,
    target_node_id: str,
    source_id: str,
    properties: dict[str, Any] | None = None,
) -> None:
    upsert_edge(
        conn,
        {
            "id": make_edge_id(source_node_id, relation_type, target_node_id, source_id),
            "source_node_id": source_node_id,
            "relation_type": relation_type,
            "target_node_id": target_node_id,
            "source_id": source_id,
            "confidence": 1.0,
            "properties": properties or {},
        },
    )


def _edge_to_dict(edge: ExtractedRelation) -> dict[str, Any]:
    return {
        "id": edge.edge_id,
        "source_node_id": edge.source_node_id,
        "target_node_id": edge.target_node_id,
        "relation_type": edge.relation_type,
        "source_id": edge.source_id,
        "confidence": edge.confidence,
        "properties": edge.properties,
    }


def _fact_to_node(fact: ExtractedFact) -> dict[str, Any]:
    return {
        "node_id": fact.node_id,
        "text": fact.text,
        "subject_node_id": fact.subject_node_id,
        "relation": fact.relation,
        "object_node_id": fact.object_node_id,
        "source_id": fact.source_id,
        "confidence": fact.confidence,
        "properties": fact.properties,
    }


def _maybe_export(conn: sqlite3.Connection, graph_dir: Path) -> dict[str, Any]:
    try:
        from src.domain_graph.export import export_graph
    except ModuleNotFoundError:
        return {"status": "skipped", "reason": "v08-06_not_implemented"}
    return export_graph(conn, graph_dir)


def _maybe_report(conn: sqlite3.Connection, graph_dir: Path) -> dict[str, Any]:
    try:
        from src.domain_graph.report import generate_graph_report
    except ModuleNotFoundError:
        return {"status": "skipped", "reason": "v08-07_not_implemented"}
    return generate_graph_report(conn, graph_dir)


def _parse_source_id(text: str) -> str | None:
    match = re.search(r"(?:source_id:\s*|Source:\s*`)([A-Za-z0-9_.:-]+)`?", text)
    return match.group(1) if match else None


def _parse_title(text: str) -> str | None:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _strip_summary_header(text: str) -> str:
    return re.sub(r"^# .+?\n+", "", text, count=1).strip()


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def _slug(value: str) -> str:
    normalized = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value.strip()).strip("_")
    return normalized.casefold() if normalized else "unknown"


if __name__ == "__main__":
    main()
