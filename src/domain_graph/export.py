from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.domain_graph.storage import ensure_graph_schema


SCHEMA_VERSION = "v08"
STABLE_GENERATED_AT = "1970-01-01T00:00:00+00:00"


def export_graph(conn: sqlite3.Connection, graph_dir: Path) -> dict[str, Any]:
    ensure_graph_schema(conn)
    graph_dir.mkdir(parents=True, exist_ok=True)
    nodes = export_nodes(conn, graph_dir / "nodes.json")
    edges = export_edges(conn, graph_dir / "edges.json")
    export_domain_graph(nodes, edges, graph_dir / "domain_graph.json")
    entity_index = export_entity_index(nodes, graph_dir / "entity_index.json")
    return {
        "status": "ok",
        "nodes": len(nodes),
        "edges": len(edges),
        "entity_index_aliases": len(entity_index),
    }


def export_nodes(conn: sqlite3.Connection, output_path: Path) -> list[dict[str, Any]]:
    ensure_graph_schema(conn)
    rows = conn.execute(
        """
        SELECT id, type, name, canonical_name, aliases_json, aliases, properties_json, properties
          FROM graph_nodes
         ORDER BY id
        """
    ).fetchall()
    nodes = [
        {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "canonical_name": row[3] or row[2],
            "aliases": _json_loads(row[4], _json_loads(row[5], [])),
            "properties": _json_loads(row[6], _json_loads(row[7], {})),
        }
        for row in rows
    ]
    _write_json(output_path, nodes)
    return nodes


def export_edges(conn: sqlite3.Connection, output_path: Path) -> list[dict[str, Any]]:
    ensure_graph_schema(conn)
    rows = conn.execute(
        """
        SELECT id, source_id, target_id, type, confidence, source_ids, properties_json, properties
          FROM graph_edges
         ORDER BY id
        """
    ).fetchall()
    edges = [
        {
            "id": row[0],
            "source": row[1],
            "target": row[2],
            "relation": row[3],
            "source_id": _first_or_none(_json_loads(row[5], [])),
            "confidence": float(row[4]) if row[4] is not None else None,
            "properties": _json_loads(row[6], _json_loads(row[7], {})),
        }
        for row in rows
    ]
    _write_json(output_path, edges)
    return edges


def export_domain_graph(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, Any]:
    payload = {
        "metadata": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": STABLE_GENERATED_AT,
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
        "nodes": nodes,
        "edges": edges,
    }
    _write_json(output_path, payload)
    return payload


def export_entity_index(
    nodes: list[dict[str, Any]],
    output_path: Path,
) -> dict[str, str]:
    index: dict[str, str] = {}
    for node in nodes:
        if node["type"] not in {"Job", "Patch", "Skill", "Item", "Encounter", "GearSet"}:
            continue
        aliases = [node["canonical_name"], node["name"], *node.get("aliases", [])]
        for alias in aliases:
            normalized = _normalize_alias(str(alias))
            if normalized:
                index.setdefault(normalized, node["id"])
    _write_json(output_path, dict(sorted(index.items())))
    return dict(sorted(index.items()))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _normalize_alias(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _first_or_none(values: list[Any]) -> Any | None:
    return values[0] if values else None
