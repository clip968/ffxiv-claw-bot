from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"


def lookup_graph_paths(conn: sqlite3.Connection, page_id: str) -> list[str]:
    """Find graph edges involving this page and return readable path strings."""
    graph_node_id = f"page:{page_id}"
    rows = conn.execute(
        """
        SELECT source_id, target_id, type
        FROM graph_edges
        WHERE source_id = ? OR target_id = ?
        ORDER BY type
        """,
        (graph_node_id, graph_node_id),
    ).fetchall()
    return [f"{r[0]} --{r[2]}--> {r[1]}" for r in rows]


def search_fts(query: str) -> list[dict]:
    results: list[dict] = []

    with sqlite3.connect(DB_PATH) as conn:
        rows = conn.execute(
            """
            SELECT wiki_fts.page_id,
                   wiki_fts.title,
                   wiki_pages.type,
                   wiki_pages.path,
                   wiki_fts.rank AS score,
                   snippet(wiki_fts, -1, '', '', '...', 48) AS snippet
            FROM wiki_fts
            JOIN wiki_pages ON wiki_fts.page_id = wiki_pages.id
            WHERE wiki_fts MATCH ?
            ORDER BY rank
            """,
            (query,),
        ).fetchall()

        for row in rows:
            page_id = row[0]
            graph_paths = lookup_graph_paths(conn, page_id)
            results.append({
                "page_id": page_id,
                "title": row[1],
                "type": row[2],
                "path": row[3],
                "score": row[4],
                "snippet": row[5],
                "graph_paths": graph_paths,
            })

    return results


def format_query(raw: str) -> str:
    raw = raw.strip()
    if not raw:
        raise ValueError("query must not be empty")
    return raw


def main() -> None:
    parser = argparse.ArgumentParser(description="Search FFXIV knowledge base.")
    parser.add_argument("query", help="FTS5 search query")
    args = parser.parse_args()

    try:
        query = format_query(args.query)
    except ValueError as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        return

    try:
        results = search_fts(query)
    except sqlite3.OperationalError as e:
        print(
            json.dumps({"status": "error", "message": f"FTS5 error: {e}"}, ensure_ascii=False)
        )
        return

    print(
        json.dumps(
            {"status": "ok", "query": query, "results": results},
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
