from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from src.domain_graph.storage import ensure_graph_schema, make_edge_id, upsert_edge, upsert_node


DERIVED_INDEX_START = "<!-- BEGIN DERIVED WIKI -->"
DERIVED_INDEX_END = "<!-- END DERIVED WIKI -->"
DEFAULT_TYPES = ("jobs", "patches", "skills")


def generate_derived_wiki(
    conn: sqlite3.Connection,
    wiki_root: Path,
    graph_dir: Path | None = None,
    *,
    types: tuple[str, ...] = DEFAULT_TYPES,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    ensure_graph_schema(conn)
    graph = _load_graph(conn)
    written: list[str] = []
    selected = set(types)

    if "jobs" in selected:
        written.extend(_write_job_pages(conn, graph, wiki_root, dry_run=dry_run))
    if "patches" in selected:
        written.extend(_write_patch_pages(conn, graph, wiki_root, dry_run=dry_run))
    if "skills" in selected:
        written.extend(_write_skill_pages(conn, graph, wiki_root, dry_run=dry_run))

    if not dry_run:
        _update_index(wiki_root, graph)

    result = {
        "status": "ok",
        "dry_run": dry_run,
        "written": sorted(written),
        "types": sorted(selected),
    }
    if verbose:
        result["wiki_root"] = str(wiki_root)
        result["graph_dir"] = str(graph_dir) if graph_dir else None
    return result


def _write_job_pages(
    conn: sqlite3.Connection,
    graph: dict[str, Any],
    wiki_root: Path,
    *,
    dry_run: bool,
) -> list[str]:
    written: list[str] = []
    for job in _nodes_by_type(graph, "Job"):
        slug = _slug(job["id"])
        path = wiki_root / "jobs" / f"{slug}.md"
        skills = _related_nodes(graph, job["id"], "HAS_SKILL", direction="out")
        facts = _related_nodes(graph, job["id"], "AFFECTS_JOB", direction="in")
        patches = _patches_for_facts(graph, facts)
        sources = _sources_for_facts(graph, facts)
        links = _graph_links(graph, job["id"])
        content = _render_document(
            job["name"],
            [
                ("Summary", [f"Current KB-level summary for {job['name']}."]),
                ("Related Patches", _node_bullets(patches)),
                ("Skills", _node_bullets(skills)),
                ("Recent Facts", _fact_bullets(facts)),
                ("Related Sources", _source_bullets(sources)),
                ("Graph Links", links),
            ],
        )
        _write_page(conn, path, content, wiki_root, f"page:jobs/{slug}", job["name"], sources, dry_run)
        written.append(_relative_path(path, wiki_root))
    return written


def _write_patch_pages(
    conn: sqlite3.Connection,
    graph: dict[str, Any],
    wiki_root: Path,
    *,
    dry_run: bool,
) -> list[str]:
    written: list[str] = []
    for patch in _nodes_by_type(graph, "Patch"):
        slug = _slug(patch["id"])
        path = wiki_root / "patches" / f"{slug}.md"
        facts = _related_nodes(graph, patch["id"], "VALID_IN_PATCH", direction="in")
        jobs = _targets_from_facts(graph, facts, "AFFECTS_JOB")
        skills = _targets_from_facts(graph, facts, "AFFECTS_SKILL")
        sources = _sources_for_facts(graph, facts)
        content = _render_document(
            patch["name"],
            [
                ("Summary", [f"Current KB-level summary for {patch['name']}."]),
                ("Affected Jobs", _node_bullets(jobs)),
                ("Affected Skills", _node_bullets(skills)),
                ("Facts", _fact_bullets(facts)),
                ("Related Sources", _source_bullets(sources)),
            ],
        )
        _write_page(conn, path, content, wiki_root, f"page:patches/{slug}", patch["name"], sources, dry_run)
        written.append(_relative_path(path, wiki_root))
    return written


def _write_skill_pages(
    conn: sqlite3.Connection,
    graph: dict[str, Any],
    wiki_root: Path,
    *,
    dry_run: bool,
) -> list[str]:
    written: list[str] = []
    for skill in _nodes_by_type(graph, "Skill"):
        slug = _slug(skill["id"])
        path = wiki_root / "skills" / f"{slug}.md"
        jobs = _related_nodes(graph, skill["id"], "HAS_SKILL", direction="in")
        facts = _related_nodes(graph, skill["id"], "AFFECTS_SKILL", direction="in")
        patches = _patches_for_facts(graph, facts)
        sources = _sources_for_facts(graph, facts)
        content = _render_document(
            skill["name"],
            [
                ("Summary", [f"Current KB-level summary for {skill['name']}."]),
                ("Job", _node_bullets(jobs)),
                ("Related Patches", _node_bullets(patches)),
                ("Facts", _fact_bullets(facts)),
                ("Related Sources", _source_bullets(sources)),
            ],
        )
        _write_page(conn, path, content, wiki_root, f"page:skills/{slug}", skill["name"], sources, dry_run)
        written.append(_relative_path(path, wiki_root))
    return written


def _write_page(
    conn: sqlite3.Connection,
    path: Path,
    content: str,
    wiki_root: Path,
    page_node_id: str,
    title: str,
    sources: list[dict[str, Any]],
    dry_run: bool,
) -> None:
    if dry_run:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    upsert_node(
        conn,
        {
            "id": page_node_id,
            "type": "WikiPage",
            "name": title,
            "canonical_name": title,
            "properties": {"path": _relative_path(path, wiki_root)},
        },
    )
    for source in sources:
        upsert_edge(
            conn,
            {
                "id": make_edge_id(page_node_id, "DERIVED_FROM", source["id"], source["source_id"]),
                "source_node_id": page_node_id,
                "relation_type": "DERIVED_FROM",
                "target_node_id": source["id"],
                "source_id": source["source_id"],
                "confidence": 1.0,
            },
        )


def _update_index(wiki_root: Path, graph: dict[str, Any]) -> None:
    index_path = wiki_root / "index.md"
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else ""
    section = "\n".join(
        [
            DERIVED_INDEX_START,
            "## Derived Wiki",
            "",
            "### Jobs",
            *_index_links(_nodes_by_type(graph, "Job"), "jobs"),
            "",
            "### Patches",
            *_index_links(_nodes_by_type(graph, "Patch"), "patches"),
            "",
            "### Skills",
            *_index_links(_nodes_by_type(graph, "Skill"), "skills"),
            DERIVED_INDEX_END,
            "",
        ]
    )
    if DERIVED_INDEX_START in existing and DERIVED_INDEX_END in existing:
        before = existing.split(DERIVED_INDEX_START, 1)[0].rstrip()
        after = existing.split(DERIVED_INDEX_END, 1)[1].lstrip()
        content = f"{before}\n\n{section}{after}" if before else f"{section}{after}"
    else:
        content = f"{existing.rstrip()}\n\n{section}" if existing.strip() else section
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(content, encoding="utf-8")


def _load_graph(conn: sqlite3.Connection) -> dict[str, Any]:
    nodes = {
        row[0]: {
            "id": row[0],
            "type": row[1],
            "name": row[2],
            "properties": _json_loads(row[3], _json_loads(row[4], {})),
        }
        for row in conn.execute(
            "SELECT id, type, name, properties_json, properties FROM graph_nodes ORDER BY id"
        ).fetchall()
    }
    edges = [
        {"source": row[0], "relation": row[1], "target": row[2], "source_ids": _json_loads(row[3], [])}
        for row in conn.execute(
            "SELECT source_id, type, target_id, source_ids FROM graph_edges ORDER BY id"
        ).fetchall()
    ]
    return {"nodes": nodes, "edges": edges}


def _nodes_by_type(graph: dict[str, Any], node_type: str) -> list[dict[str, Any]]:
    return sorted(
        [node for node in graph["nodes"].values() if node["type"] == node_type],
        key=lambda node: node["name"],
    )


def _related_nodes(
    graph: dict[str, Any],
    node_id: str,
    relation: str,
    *,
    direction: str,
) -> list[dict[str, Any]]:
    related: list[dict[str, Any]] = []
    for edge in graph["edges"]:
        if edge["relation"] != relation:
            continue
        candidate_id = None
        if direction == "out" and edge["source"] == node_id:
            candidate_id = edge["target"]
        elif direction == "in" and edge["target"] == node_id:
            candidate_id = edge["source"]
        if candidate_id and candidate_id in graph["nodes"]:
            related.append(graph["nodes"][candidate_id])
    return _dedupe_nodes(related)


def _patches_for_facts(graph: dict[str, Any], facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    fact_ids = {fact["id"] for fact in facts}
    for edge in graph["edges"]:
        if edge["relation"] == "VALID_IN_PATCH" and edge["source"] in fact_ids and edge["target"] in graph["nodes"]:
            patches.append(graph["nodes"][edge["target"]])
    return _dedupe_nodes(patches)


def _targets_from_facts(
    graph: dict[str, Any],
    facts: list[dict[str, Any]],
    relation: str,
) -> list[dict[str, Any]]:
    targets: list[dict[str, Any]] = []
    fact_ids = {fact["id"] for fact in facts}
    for edge in graph["edges"]:
        if edge["relation"] == relation and edge["source"] in fact_ids and edge["target"] in graph["nodes"]:
            targets.append(graph["nodes"][edge["target"]])
    return _dedupe_nodes(targets)


def _sources_for_facts(graph: dict[str, Any], facts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    fact_ids = {fact["id"] for fact in facts}
    for edge in graph["edges"]:
        if edge["relation"] == "SUPPORTS" and edge["target"] in fact_ids and edge["source"] in graph["nodes"]:
            source = graph["nodes"][edge["source"]]
            sources.append(
                {
                    "id": source["id"],
                    "source_id": source["id"].removeprefix("src:"),
                    "name": source["name"],
                    "properties": source.get("properties", {}),
                }
            )
    return sorted({source["id"]: source for source in sources}.values(), key=lambda item: item["id"])


def _graph_links(graph: dict[str, Any], node_id: str) -> list[str]:
    links = []
    for edge in graph["edges"]:
        if edge["source"] == node_id or edge["target"] == node_id:
            links.append(f"- {edge['source']} -> {edge['relation']} -> {edge['target']}")
    return sorted(links) or ["- None"]


def _render_document(title: str, sections: list[tuple[str, list[str]]]) -> str:
    lines = [f"# {title}", ""]
    for heading, body in sections:
        lines.extend([f"## {heading}", "", *(body or ["- None"]), ""])
    return "\n".join(lines).rstrip() + "\n"


def _node_bullets(nodes: list[dict[str, Any]]) -> list[str]:
    return [f"- {node['name']}" for node in _dedupe_nodes(nodes)] or ["- None"]


def _fact_bullets(facts: list[dict[str, Any]]) -> list[str]:
    return [f"- {fact['properties'].get('text') or fact['name']}" for fact in _dedupe_nodes(facts)] or ["- None"]


def _source_bullets(sources: list[dict[str, Any]]) -> list[str]:
    if not sources:
        return ["- None"]
    lines = []
    for source in sources:
        parts = [f"- source_id: {source['source_id']}"]
        title = source["properties"].get("title")
        path = source["properties"].get("path")
        if title:
            parts.append(f"  - title: {title}")
        if path:
            parts.append(f"  - path: {path}")
        lines.append("\n".join(parts))
    return lines


def _index_links(nodes: list[dict[str, Any]], directory: str) -> list[str]:
    return [f"- [{node['name']}]({directory}/{_slug(node['id'])}.md)" for node in nodes] or ["- None"]


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted({node["id"]: node for node in nodes}.values(), key=lambda node: node["name"])


def _slug(node_id: str) -> str:
    return node_id.split(":", 1)[1]


def _relative_path(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return default
