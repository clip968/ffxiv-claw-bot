from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections import deque
from datetime import datetime, timezone
from typing import Any


DOMAIN_NODE_TYPES = (
    "Job",
    "Patch",
    "Skill",
    "Item",
    "ItemCategory",
    "EquipmentJob",
    "ItemSource",
    "Encounter",
    "GearSet",
    "Fact",
)
DOMAIN_EDGE_TYPES = (
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
    "RELATED_TO",
    "DERIVED_FROM",
)


def ensure_graph_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS graph_nodes (
          id TEXT PRIMARY KEY,
          type TEXT NOT NULL,
          name TEXT NOT NULL,
          aliases TEXT,
          properties TEXT
        );

        CREATE TABLE IF NOT EXISTS graph_edges (
          id TEXT PRIMARY KEY,
          source_id TEXT NOT NULL,
          target_id TEXT NOT NULL,
          type TEXT NOT NULL,
          confidence TEXT NOT NULL,
          score REAL,
          source_page_id TEXT,
          source_ids TEXT,
          properties TEXT
        );
        """
    )
    _add_column(conn, "graph_nodes", "canonical_name", "TEXT")
    _add_column(conn, "graph_nodes", "aliases_json", "TEXT")
    _add_column(conn, "graph_nodes", "properties_json", "TEXT")
    _add_column(conn, "graph_nodes", "created_at", "TEXT")
    _add_column(conn, "graph_nodes", "updated_at", "TEXT")
    _add_column(conn, "graph_edges", "source_node_id", "TEXT")
    _add_column(conn, "graph_edges", "target_node_id", "TEXT")
    _add_column(conn, "graph_edges", "relation_type", "TEXT")
    _add_column(conn, "graph_edges", "properties_json", "TEXT")
    _add_column(conn, "graph_edges", "created_at", "TEXT")
    _add_column(conn, "graph_edges", "updated_at", "TEXT")
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(type);
        CREATE INDEX IF NOT EXISTS idx_graph_nodes_canonical_name ON graph_nodes(canonical_name);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_source_id ON graph_edges(source_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_target_id ON graph_edges(target_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_type ON graph_edges(type);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_source_node_id ON graph_edges(source_node_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_target_node_id ON graph_edges(target_node_id);
        CREATE INDEX IF NOT EXISTS idx_graph_edges_relation_type ON graph_edges(relation_type);
        """
    )
    conn.commit()


def upsert_node(conn: sqlite3.Connection, node: dict[str, Any]) -> None:
    ensure_graph_schema(conn)
    timestamp = _now_iso()
    aliases = list(node.get("aliases") or [])
    properties = dict(node.get("properties") or {})
    conn.execute(
        """
        INSERT INTO graph_nodes (
            id, type, name, aliases, properties, canonical_name,
            aliases_json, properties_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          type = excluded.type,
          name = excluded.name,
          aliases = excluded.aliases,
          properties = excluded.properties,
          canonical_name = excluded.canonical_name,
          aliases_json = excluded.aliases_json,
          properties_json = excluded.properties_json,
          updated_at = excluded.updated_at
        """,
        (
            node["id"],
            node["type"],
            node["name"],
            _json_dumps(aliases) if aliases else None,
            _json_dumps(properties) if properties else None,
            node.get("canonical_name") or node.get("name"),
            _json_dumps(aliases),
            _json_dumps(properties),
            timestamp,
            timestamp,
        ),
    )
    conn.commit()


def upsert_edge(conn: sqlite3.Connection, edge: dict[str, Any]) -> None:
    ensure_graph_schema(conn)
    timestamp = _now_iso()
    source_node_id = edge["source_node_id"]
    target_node_id = edge["target_node_id"]
    relation_type = edge["relation_type"]
    edge_id = edge.get("id") or make_edge_id(
        source_node_id,
        relation_type,
        target_node_id,
        edge.get("source_id"),
    )
    source_ids = [edge["source_id"]] if edge.get("source_id") else []
    properties = dict(edge.get("properties") or {})
    confidence = edge.get("confidence", 1.0)
    conn.execute(
        """
        INSERT INTO graph_edges (
            id, source_id, target_id, type, confidence, score, source_page_id,
            source_ids, properties, source_node_id, target_node_id, relation_type,
            properties_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
          source_id = excluded.source_id,
          target_id = excluded.target_id,
          type = excluded.type,
          confidence = excluded.confidence,
          score = excluded.score,
          source_page_id = excluded.source_page_id,
          source_ids = excluded.source_ids,
          properties = excluded.properties,
          source_node_id = excluded.source_node_id,
          target_node_id = excluded.target_node_id,
          relation_type = excluded.relation_type,
          properties_json = excluded.properties_json,
          updated_at = excluded.updated_at
        """,
        (
            edge_id,
            source_node_id,
            target_node_id,
            relation_type,
            str(confidence),
            edge.get("score"),
            edge.get("source_page_id"),
            _json_dumps(source_ids),
            _json_dumps(properties) if properties else None,
            source_node_id,
            target_node_id,
            relation_type,
            _json_dumps(properties),
            timestamp,
            timestamp,
        ),
    )
    conn.commit()


def upsert_fact(conn: sqlite3.Connection, fact: dict[str, Any]) -> None:
    properties = dict(fact.get("properties") or {})
    properties.update(
        {
            "text": fact["text"],
            "subject": fact["subject_node_id"],
            "relation": fact["relation"],
            "object": fact["object_node_id"],
            "source_id": fact["source_id"],
            "confidence": fact.get("confidence", 0.85),
        }
    )
    upsert_node(
        conn,
        {
            "id": fact["node_id"],
            "type": "Fact",
            "name": fact["text"],
            "canonical_name": fact["text"],
            "aliases": [],
            "properties": properties,
        },
    )


def get_neighbors(
    conn: sqlite3.Connection,
    node_id: str,
    depth: int = 1,
) -> dict[str, list[dict[str, Any]]]:
    ensure_graph_schema(conn)
    seen_nodes = {node_id}
    seen_edges: dict[str, dict[str, Any]] = {}
    queue: deque[tuple[str, int]] = deque([(node_id, 0)])

    while queue:
        current, current_depth = queue.popleft()
        if current_depth >= depth:
            continue
        rows = conn.execute(
            """
            SELECT id, source_id, target_id, type, confidence, source_ids, properties
              FROM graph_edges
             WHERE source_id = ? OR target_id = ?
             ORDER BY id
            """,
            (current, current),
        ).fetchall()
        for row in rows:
            edge = _edge_row_to_dict(row)
            seen_edges[edge["id"]] = edge
            for neighbor in (edge["source"], edge["target"]):
                if neighbor in seen_nodes:
                    continue
                seen_nodes.add(neighbor)
                queue.append((neighbor, current_depth + 1))

    nodes = [
        _node_row_to_dict(row)
        for row in conn.execute(
            "SELECT id, type, name, aliases, properties, canonical_name FROM graph_nodes ORDER BY id"
        ).fetchall()
        if row[0] in seen_nodes
    ]
    return {"nodes": nodes, "edges": list(seen_edges.values())}


def get_nodes_by_type(conn: sqlite3.Connection, node_type: str) -> list[dict[str, Any]]:
    ensure_graph_schema(conn)
    return [
        _node_row_to_dict(row)
        for row in conn.execute(
            "SELECT id, type, name, aliases, properties, canonical_name FROM graph_nodes WHERE type = ? ORDER BY id",
            (node_type,),
        ).fetchall()
    ]


def get_edges_by_relation(conn: sqlite3.Connection, relation_type: str) -> list[dict[str, Any]]:
    ensure_graph_schema(conn)
    return [
        _edge_row_to_dict(row)
        for row in conn.execute(
            "SELECT id, source_id, target_id, type, confidence, source_ids, properties FROM graph_edges WHERE type = ? ORDER BY id",
            (relation_type,),
        ).fetchall()
    ]


def reset_domain_graph(conn: sqlite3.Connection) -> None:
    ensure_graph_schema(conn)
    conn.execute(
        f"DELETE FROM graph_edges WHERE type IN ({','.join('?' for _ in DOMAIN_EDGE_TYPES)})",
        DOMAIN_EDGE_TYPES,
    )
    conn.execute(
        f"DELETE FROM graph_nodes WHERE type IN ({','.join('?' for _ in DOMAIN_NODE_TYPES)})",
        DOMAIN_NODE_TYPES,
    )
    conn.commit()


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
        re.sub(r"\s+", " ", fact_text.strip()),
    )


def _add_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> None:
    existing = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _node_row_to_dict(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    aliases = _json_loads(row[3], default=[])
    properties = _json_loads(row[4], default={})
    return {
        "id": row[0],
        "type": row[1],
        "name": row[2],
        "canonical_name": row[5] or row[2],
        "aliases": aliases,
        "properties": properties,
    }


def _edge_row_to_dict(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "id": row[0],
        "source": row[1],
        "target": row[2],
        "relation": row[3],
        "confidence": _optional_float(row[4]),
        "source_ids": _json_loads(row[5], default=[]),
        "properties": _json_loads(row[6], default={}),
    }


def _json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_loads(raw: str | None, *, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hash_parts(*parts: str) -> str:
    return hashlib.sha1("\x1f".join(parts).encode("utf-8")).hexdigest()[:12]


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
