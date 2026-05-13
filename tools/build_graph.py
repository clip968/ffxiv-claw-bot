from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
GRAPH_DIR = ROOT / "graph"


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def upsert_node(conn: sqlite3.Connection, node_id: str, node_type: str, name: str) -> None:
    conn.execute(
        """
        INSERT INTO graph_nodes (id, type, name, aliases, properties)
        VALUES (?, ?, ?, NULL, NULL)
        ON CONFLICT(id) DO UPDATE SET
          type = excluded.type,
          name = excluded.name
        """,
        (node_id, node_type, name),
    )


def upsert_edge(
    conn: sqlite3.Connection,
    source_id: str,
    target_id: str,
    edge_type: str,
    confidence: str,
    source_page: str | None = None,
    score: float | None = None,
) -> None:
    edge_id = f"{source_id}--{edge_type}--{target_id}"
    conn.execute(
        """
        INSERT INTO graph_edges (id, source_id, target_id, type, confidence, score, source_page_id, source_ids, properties)
        VALUES (?, ?, ?, ?, ?, ?, ?, NULL, NULL)
        ON CONFLICT(id) DO UPDATE SET
          type = excluded.type,
          confidence = excluded.confidence,
          score = excluded.score,
          source_page_id = excluded.source_page_id
        """,
        (edge_id, source_id, target_id, edge_type, confidence, score, source_page),
    )


def build_graph(source_id: str | None = None) -> dict:
    """Build deterministic graph from wiki_pages data."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")

        if source_id:
            rows = conn.execute(
                "SELECT id, type, title, path, source_ids FROM wiki_pages WHERE id = ?",
                (f"wiki_{source_id.removeprefix('src_')}",),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, type, title, path, source_ids FROM wiki_pages"
            ).fetchall()

        node_count = 0
        edge_count = 0
        processed = 0

        for row in rows:
            page_id: str = row[0]
            page_type: str = row[1]
            page_title: str = row[2]
            page_path: str = row[3]
            source_ids_raw: str = row[4]

            # Create WikiPage node
            wiki_node_id = f"page:{page_id}"
            upsert_node(conn, wiki_node_id, "WikiPage", page_title)
            node_count += 1

            # Parse source_ids JSON
            try:
                source_ids = json.loads(source_ids_raw)
            except (json.JSONDecodeError, TypeError):
                source_ids = []

            for sid in source_ids:
                # Create SourceDocument node
                src_node_id = f"src:{sid}"
                upsert_node(conn, src_node_id, "SourceDocument", sid)
                node_count += 1

                # Create SOURCE_OF edge: source document → wiki page
                upsert_edge(
                    conn,
                    source_id=src_node_id,
                    target_id=wiki_node_id,
                    edge_type="SOURCE_OF",
                    confidence="EXTRACTED",
                    source_page=page_path,
                )
                edge_count += 1

            processed += 1

        conn.commit()

        # Export to JSON
        db_nodes = [
            dict(r)
            for r in conn.execute(
                "SELECT id, type, name, aliases, properties FROM graph_nodes ORDER BY id"
            )
        ]
        db_edges = [
            dict(r)
            for r in conn.execute(
                "SELECT id, source_id, target_id, type, confidence, score, source_page_id, source_ids, properties FROM graph_edges ORDER BY id"
            )
        ]

    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    (GRAPH_DIR / "nodes.json").write_text(
        json.dumps(db_nodes, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (GRAPH_DIR / "edges.json").write_text(
        json.dumps(db_edges, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    return {
        "status": "ok",
        "processed": processed,
        "nodes": node_count,
        "edges": edge_count,
        "db_nodes": len(db_nodes),
        "db_edges": len(db_edges),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build deterministic graph from wiki pages.")
    parser.add_argument("--source-id", help="Only process a specific source ID")
    parser.add_argument(
        "--llm-enhanced",
        action="store_true",
        help="Enable LLM-based extraction (placeholder, not yet implemented)",
    )
    args = parser.parse_args()

    result = build_graph(args.source_id)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
