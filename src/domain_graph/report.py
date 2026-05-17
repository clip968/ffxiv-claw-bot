from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

from src.domain_graph.storage import ensure_graph_schema


NODE_TYPES = (
    "SourceDocument",
    "WikiPage",
    "Job",
    "Patch",
    "Skill",
    "Item",
    "ItemCategory",
    "EquipmentJob",
    "ItemSource",
    "Fact",
)
EDGE_TYPES = (
    "SOURCE_OF",
    "MENTIONS",
    "HAS_SKILL",
    "ITEM_IN_CATEGORY",
    "EQUIPPABLE_BY_JOB",
    "HAS_ITEM_LEVEL",
    "HAS_EQUIP_LEVEL",
    "OBTAINED_FROM",
    "SUPPORTS",
    "VALID_IN_PATCH",
    "AFFECTS_JOB",
    "AFFECTS_SKILL",
    "DERIVED_FROM",
)


def generate_graph_report(conn: sqlite3.Connection, graph_dir: Path) -> dict[str, Any]:
    ensure_graph_schema(conn)
    graph_dir.mkdir(parents=True, exist_ok=True)
    text = build_graph_report(conn)
    output_path = graph_dir / "GRAPH_REPORT.md"
    output_path.write_text(text, encoding="utf-8")
    return {
        "status": "ok",
        "path": output_path.as_posix(),
        "warnings": len(_quality_warnings(conn)),
    }


def build_graph_report(conn: sqlite3.Connection) -> str:
    node_counts = _counts_by(conn, "graph_nodes", "type")
    edge_counts = _counts_by(conn, "graph_edges", "type")
    total_nodes = sum(node_counts.values())
    total_edges = sum(edge_counts.values())
    lines = [
        "# FFXIV Graph Report",
        "",
        "## Summary",
        f"- sources: {node_counts.get('SourceDocument', 0)}",
        f"- wiki_pages: {node_counts.get('WikiPage', 0)}",
        f"- graph_nodes: {total_nodes}",
        f"- graph_edges: {total_edges}",
        f"- facts: {node_counts.get('Fact', 0)}",
        "",
        "## Node Counts",
        *_format_counts(node_counts, NODE_TYPES),
        "",
        "## Edge Counts",
        *_format_counts(edge_counts, EDGE_TYPES),
        "",
        "## Top Mentioned Jobs",
        *_format_top_mentions(conn, "Job"),
        "",
        "## Top Mentioned Patches",
        *_format_top_mentions(conn, "Patch"),
        "",
        "## Top Mentioned Skills",
        *_format_top_mentions(conn, "Skill"),
        "",
        "## Quality Warnings",
        *_quality_warnings(conn),
        "",
    ]
    return "\n".join(lines)


def _counts_by(conn: sqlite3.Connection, table: str, column: str) -> dict[str, int]:
    return {
        row[0]: row[1]
        for row in conn.execute(
            f"SELECT {column}, COUNT(*) FROM {table} GROUP BY {column} ORDER BY {column}"
        ).fetchall()
    }


def _format_counts(counts: dict[str, int], keys: tuple[str, ...]) -> list[str]:
    return [f"- {key}: {counts.get(key, 0)}" for key in keys]


def _format_top_mentions(conn: sqlite3.Connection, node_type: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT graph_nodes.name, COUNT(*) AS mention_count
          FROM graph_edges
          JOIN graph_nodes ON graph_edges.target_id = graph_nodes.id
         WHERE graph_edges.type = 'MENTIONS'
           AND graph_nodes.type = ?
         GROUP BY graph_nodes.id, graph_nodes.name
         ORDER BY mention_count DESC, graph_nodes.name
         LIMIT 10
        """,
        (node_type,),
    ).fetchall()
    if not rows:
        return ["- None"]
    return [f"- {name}: {count}" for name, count in rows]


def _quality_warnings(conn: sqlite3.Connection) -> list[str]:
    warnings: list[str] = []
    fact_without_support = conn.execute(
        """
        SELECT COUNT(*)
          FROM graph_nodes
         WHERE type = 'Fact'
           AND id NOT IN (SELECT target_id FROM graph_edges WHERE type = 'SUPPORTS')
        """
    ).fetchone()[0]
    if fact_without_support:
        warnings.append(f"- facts without supporting sources: {fact_without_support}")

    fact_without_patch = conn.execute(
        """
        SELECT COUNT(*)
          FROM graph_nodes
         WHERE type = 'Fact'
           AND id NOT IN (SELECT source_id FROM graph_edges WHERE type = 'VALID_IN_PATCH')
        """
    ).fetchone()[0]
    if fact_without_patch:
        warnings.append(f"- facts without patch: {fact_without_patch}")

    entities_without_mentions = conn.execute(
        """
        SELECT COUNT(*)
          FROM graph_nodes
         WHERE type IN ('Job', 'Patch', 'Skill')
           AND id NOT IN (SELECT target_id FROM graph_edges WHERE type = 'MENTIONS')
        """
    ).fetchone()[0]
    if entities_without_mentions:
        warnings.append(f"- entities without mentions: {entities_without_mentions}")

    if not warnings:
        return ["- None"]
    return warnings
