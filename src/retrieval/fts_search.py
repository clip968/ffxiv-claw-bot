from __future__ import annotations

import sqlite3
from pathlib import Path

from src.retrieval.models import SearchResult
from tools.search_kb import DB_PATH, sanitize_fts_query


def search_wiki(
    query: str,
    *,
    wiki_type: str | None = None,
    topic: str | None = None,
    limit: int = 5,
    db_path: Path | None = None,
) -> list[SearchResult]:
    fts_query = sanitize_fts_query(query)
    if not fts_query:
        return []

    where = ["wiki_fts MATCH ?"]
    params: list[object] = [fts_query]
    if wiki_type is not None:
        where.append("wiki_pages.type = ?")
        params.append(wiki_type)
    if topic is not None:
        where.append("wiki_pages.job = ?")
        params.append(topic)
    params.append(limit)

    sql = f"""
        SELECT wiki_fts.page_id,
               wiki_fts.title,
               wiki_pages.type,
               wiki_pages.path,
               wiki_fts.rank AS score,
               snippet(wiki_fts, -1, '', '', '...', 48) AS snippet,
               wiki_pages.job
          FROM wiki_fts
          JOIN wiki_pages ON wiki_fts.page_id = wiki_pages.id
         WHERE {" AND ".join(where)}
         ORDER BY rank
         LIMIT ?
    """

    conn = sqlite3.connect(db_path or DB_PATH)
    try:
        rows = conn.execute(sql, params).fetchall()
    except sqlite3.OperationalError:
        return []
    finally:
        conn.close()

    return [
        SearchResult(
            page_id=row[0],
            title=row[1],
            wiki_type=row[2],
            path=row[3],
            score=row[4],
            snippet=row[5],
            topic=row[6],
        )
        for row in rows
    ]
