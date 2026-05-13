from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"


def get_node(conn: sqlite3.Connection, node_id: str) -> dict | None:
    row = conn.execute(
        "SELECT id, type, name, aliases, properties FROM graph_nodes WHERE id = ?",
        (node_id,),
    ).fetchone()
    return dict(row) if row else None


def query_source(conn: sqlite3.Connection, source_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT source_id, target_id, type, confidence, score, source_page_id
        FROM graph_edges WHERE source_id = ?
        ORDER BY type
        """,
        (source_id,),
    ).fetchall()
    return [dict(r) for r in rows]


def query_direct(conn: sqlite3.Connection, source_id: str, target_id: str) -> list[dict]:
    rows = conn.execute(
        """
        SELECT source_id, target_id, type, confidence, score, source_page_id
        FROM graph_edges WHERE source_id = ? AND target_id = ?
        """,
        (source_id, target_id),
    ).fetchall()
    return [dict(r) for r in rows]


def query_bfs(conn: sqlite3.Connection, start_id: str, depth: int) -> dict:
    """BFS traversal from start_id up to given depth."""
    visited_nodes: set[str] = {start_id}
    visited_edge_ids: set[str] = set()
    current: set[str] = {start_id}
    all_edges: list[dict] = []

    for _ in range(depth):
        if not current:
            break

        placeholders = ",".join("?" for _ in current)
        rows = conn.execute(
            f"""
            SELECT id, source_id, target_id, type, confidence, score, source_page_id
            FROM graph_edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})
            """,
            list(current) + list(current),
        ).fetchall()

        next_nodes: set[str] = set()
        for r in rows:
            edge_id = r["id"]
            if edge_id in visited_edge_ids:
                continue
            visited_edge_ids.add(edge_id)
            all_edges.append({
                "source_id": r["source_id"],
                "target_id": r["target_id"],
                "type": r["type"],
                "confidence": r["confidence"],
                "score": r["score"],
                "source_page_id": r["source_page_id"],
            })
            if r["source_id"] not in visited_nodes:
                visited_nodes.add(r["source_id"])
                next_nodes.add(r["source_id"])
            if r["target_id"] not in visited_nodes:
                visited_nodes.add(r["target_id"])
                next_nodes.add(r["target_id"])

        current = next_nodes

    nodes_info: list[dict] = []
    for nid in sorted(visited_nodes):
        node = get_node(conn, nid)
        if node:
            nodes_info.append(node)

    return {"nodes": nodes_info, "edges": all_edges}


def main() -> None:
    parser = argparse.ArgumentParser(description="Query knowledge graph.")
    parser.add_argument("--source", help="Source node ID")
    parser.add_argument("--target", help="Target node ID (for direct query)")
    parser.add_argument("--node", help="Start node for BFS traversal")
    parser.add_argument("--depth", type=int, default=2, help="BFS depth (default: 2)")
    args = parser.parse_args()

    if not args.source and not args.node:
        result = {
            "status": "error",
            "message": "Provide --source, --source --target, or --node --depth",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row

        mode: str
        output: dict

        if args.source and args.target:
            mode = "direct"
            edges = query_direct(conn, args.source, args.target)
            output = {
                "status": "ok",
                "mode": mode,
                "params": {"source": args.source, "target": args.target},
                "edges": edges,
            }
        elif args.source:
            mode = "source"
            edges = query_source(conn, args.source)
            output = {
                "status": "ok",
                "mode": mode,
                "params": {"source": args.source},
                "edges": edges,
            }
        else:
            mode = "bfs"
            bfs_result = query_bfs(conn, args.node, args.depth)
            output = {
                "status": "ok",
                "mode": mode,
                "params": {"node": args.node, "depth": args.depth},
                "nodes": bfs_result["nodes"],
                "edges": bfs_result["edges"],
            }

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
