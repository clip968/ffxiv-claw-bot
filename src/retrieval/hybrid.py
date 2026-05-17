from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

from src.retrieval.models import SearchResult


SOURCE_ID_PATTERN = re.compile(r"source_id:\s*([A-Za-z0-9_.:-]+)")


@dataclass(frozen=True)
class GraphRetrievalResult:
    page_id: str
    title: str
    wiki_type: str
    path: str
    snippet: str
    source_id: str | None
    node_id: str
    score: float
    topic: str | None = None

    def to_search_result(self) -> SearchResult:
        return SearchResult(
            page_id=self.page_id,
            title=self.title,
            wiki_type=self.wiki_type,
            path=self.path,
            score=self.score,
            snippet=self.snippet,
            topic=self.topic,
        )


def load_entity_index(graph_dir: Path) -> dict[str, str]:
    path = graph_dir / "entity_index.json"
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(alias): str(node_id) for alias, node_id in payload.items()}


def match_query_entities(question: str, entity_index: dict[str, str]) -> tuple[str, ...]:
    matches: list[tuple[tuple[int, int], str]] = []
    occupied: list[tuple[int, int]] = []
    for alias, node_id in sorted(entity_index.items(), key=lambda item: (-len(item[0]), item[0])):
        span = _find_alias_span(question, alias)
        if span is None or _overlaps(span, occupied):
            continue
        occupied.append(span)
        if node_id not in [item[1] for item in matches]:
            matches.append((span, node_id))
    return tuple(node_id for _, node_id in sorted(matches, key=lambda item: item[0]))


def retrieve_graph_neighborhood(
    conn: sqlite3.Connection,
    entity_ids: Sequence[str],
    *,
    depth: int = 2,
) -> tuple[GraphRetrievalResult, ...]:
    del depth
    nodes = _load_nodes(conn)
    results: dict[tuple[str, str], GraphRetrievalResult] = {}
    for entity_id in entity_ids:
        fact_ids = _fact_ids_for_entity(conn, entity_id)
        for fact_id in fact_ids:
            fact = nodes.get(fact_id, {"name": fact_id, "properties": {}})
            for source_id in _supporting_source_ids(conn, fact_id):
                source = nodes.get(source_id, {"name": source_id, "properties": {}})
                result = _graph_result_for_source(
                    source_id,
                    source,
                    fact_id,
                    fact,
                    score=1.4,
                )
                results[(result.page_id, result.node_id)] = result
        for source_id in _mention_source_ids(conn, entity_id):
            source = nodes.get(source_id, {"name": source_id, "properties": {}})
            result = _graph_result_for_source(
                source_id,
                source,
                entity_id,
                nodes.get(entity_id, {"name": entity_id, "properties": {}}),
                score=1.0,
            )
            results[(result.page_id, result.node_id)] = result
    return tuple(sorted(results.values(), key=lambda item: (-item.score, item.page_id, item.node_id)))


def merge_retrieval_results(
    fts_results: Sequence[SearchResult],
    graph_results: Sequence[GraphRetrievalResult],
    *,
    limit: int = 8,
) -> tuple[SearchResult, ...]:
    merged: list[SearchResult] = []
    seen_pages: set[str] = set()
    seen_sources: set[str] = set()

    for result in fts_results:
        source_id = _source_id_from_search_result(result)
        if _seen(result.page_id, source_id, seen_pages, seen_sources):
            continue
        merged.append(result)
        _mark_seen(result.page_id, source_id, seen_pages, seen_sources)

    for result in sorted(graph_results, key=lambda item: (-item.score, item.page_id)):
        if _seen(result.page_id, result.source_id, seen_pages, seen_sources):
            continue
        merged.append(result.to_search_result())
        _mark_seen(result.page_id, result.source_id, seen_pages, seen_sources)
        if len(merged) >= limit:
            break

    return tuple(merged[:limit])


def build_answer_context(results: Sequence[GraphRetrievalResult]) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "page_id": result.page_id,
            "title": result.title,
            "path": result.path,
            "source_id": result.source_id,
            "node_id": result.node_id,
            "snippet": result.snippet,
            "score": result.score,
        }
        for result in results
    )


def execute_graph_aware_retrieval(
    question: str,
    fts_results: Sequence[SearchResult],
    *,
    db_path: Path,
    graph_dir: Path,
    limit: int = 8,
) -> tuple[SearchResult, ...]:
    entity_index = load_entity_index(graph_dir)
    if not entity_index:
        return tuple(fts_results)
    entity_ids = match_query_entities(question, entity_index)
    if not entity_ids:
        return tuple(fts_results)
    entity_page_results: tuple[SearchResult, ...] = ()
    try:
        conn = sqlite3.connect(db_path)
        try:
            entity_page_results = retrieve_entity_page_results(conn, entity_ids)
            graph_results = retrieve_graph_neighborhood(conn, entity_ids)
        finally:
            conn.close()
    except sqlite3.Error:
        return _dedupe_search_results((*fts_results, *entity_page_results))[:limit]
    fts_and_entity_results = _dedupe_search_results((*fts_results, *entity_page_results))
    return merge_retrieval_results(fts_and_entity_results, graph_results, limit=limit)


def retrieve_entity_page_results(
    conn: sqlite3.Connection,
    entity_ids: Sequence[str],
) -> tuple[SearchResult, ...]:
    page_ids = [_entity_page_id(entity_id) for entity_id in entity_ids]
    page_ids = [page_id for page_id in page_ids if page_id]
    if not page_ids:
        return ()
    placeholders = ",".join("?" for _ in page_ids)
    rows = conn.execute(
        f"""
        SELECT id, title, type, path, job
          FROM wiki_pages
         WHERE id IN ({placeholders})
        """,
        page_ids,
    ).fetchall()
    by_page_id = {row[0]: row for row in rows}
    results: list[SearchResult] = []
    for page_id in page_ids:
        row = by_page_id.get(page_id)
        if row is None:
            continue
        results.append(
            SearchResult(
                page_id=row[0],
                title=row[1],
                wiki_type=row[2],
                path=row[3],
                score=-2.0,
                snippet=f"Matched entity page: {row[1]}",
                topic=row[4],
            )
        )
    return tuple(results)


def _load_nodes(conn: sqlite3.Connection) -> dict[str, dict[str, object]]:
    rows = conn.execute(
        "SELECT id, type, name, properties_json, properties FROM graph_nodes ORDER BY id"
    ).fetchall()
    return {
        row[0]: {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "properties": _json_loads(row[3], _json_loads(row[4], {})),
        }
        for row in rows
    }


def _fact_ids_for_entity(conn: sqlite3.Connection, entity_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT source_id
          FROM graph_edges
         WHERE target_id = ?
           AND type IN ('AFFECTS_JOB', 'AFFECTS_SKILL', 'VALID_IN_PATCH')
         ORDER BY source_id
        """,
        (entity_id,),
    ).fetchall()
    return [row[0] for row in rows]


def _supporting_source_ids(conn: sqlite3.Connection, fact_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT source_id
          FROM graph_edges
         WHERE target_id = ?
           AND type = 'SUPPORTS'
         ORDER BY source_id
        """,
        (fact_id,),
    ).fetchall()
    return [row[0] for row in rows]


def _mention_source_ids(conn: sqlite3.Connection, entity_id: str) -> list[str]:
    rows = conn.execute(
        """
        SELECT source_id
          FROM graph_edges
         WHERE target_id = ?
           AND type = 'MENTIONS'
           AND source_id LIKE 'src:%'
         ORDER BY source_id
        """,
        (entity_id,),
    ).fetchall()
    return [row[0] for row in rows]


def _graph_result_for_source(
    source_node_id: str,
    source: dict[str, object],
    node_id: str,
    node: dict[str, object],
    *,
    score: float,
) -> GraphRetrievalResult:
    source_id = source_node_id.removeprefix("src:")
    properties = source.get("properties", {})
    if not isinstance(properties, dict):
        properties = {}
    node_properties = node.get("properties", {})
    if not isinstance(node_properties, dict):
        node_properties = {}
    title = str(properties.get("title") or source.get("name") or source_id)
    path = str(properties.get("path") or f"wiki/source_summaries/{source_id}.md")
    snippet = str(node_properties.get("text") or node.get("name") or title)
    topic = str(properties.get("job") or "") or None
    return GraphRetrievalResult(
        page_id=f"wiki_{source_id.removeprefix('src_')}",
        title=title,
        wiki_type="source_summary",
        path=path,
        snippet=snippet,
        source_id=source_id,
        node_id=node_id,
        score=score,
        topic=topic,
    )


def _find_alias_span(question: str, alias: str) -> tuple[int, int] | None:
    if _is_ascii(alias):
        pattern = rf"(?<![A-Za-z0-9_.]){re.escape(alias)}(?![A-Za-z0-9_.])"
        match = re.search(pattern, question, re.IGNORECASE)
        return (match.start(), match.end()) if match else None
    index = question.find(alias)
    if index < 0:
        return None
    return (index, index + len(alias))


def _is_ascii(value: str) -> bool:
    return all(ord(char) < 128 for char in value)


def _overlaps(span: tuple[int, int], occupied: list[tuple[int, int]]) -> bool:
    start, end = span
    return any(start < occupied_end and end > occupied_start for occupied_start, occupied_end in occupied)


def _source_id_from_search_result(result: SearchResult) -> str | None:
    if result.wiki_type != "source_summary":
        return None
    match = SOURCE_ID_PATTERN.search(result.snippet or "")
    if match:
        return match.group(1)
    path = Path(result.path)
    if path.parent.as_posix().endswith("wiki/source_summaries"):
        return path.stem
    return None


def _entity_page_id(entity_id: str) -> str | None:
    if ":" not in entity_id:
        return None
    entity_type, slug = entity_id.split(":", 1)
    if entity_type not in {"job", "patch", "skill"}:
        return None
    return f"{entity_type}_{slug}"


def _dedupe_search_results(results: Sequence[SearchResult]) -> tuple[SearchResult, ...]:
    seen: set[str] = set()
    deduped: list[SearchResult] = []
    for result in results:
        if result.page_id in seen:
            continue
        seen.add(result.page_id)
        deduped.append(result)
    return tuple(deduped)


def _seen(
    page_id: str,
    source_id: str | None,
    seen_pages: set[str],
    seen_sources: set[str],
) -> bool:
    return page_id in seen_pages or (source_id is not None and source_id in seen_sources)


def _mark_seen(
    page_id: str,
    source_id: str | None,
    seen_pages: set[str],
    seen_sources: set[str],
) -> None:
    seen_pages.add(page_id)
    if source_id is not None:
        seen_sources.add(source_id)


def _json_loads(raw: str | None, default: object) -> object:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default
