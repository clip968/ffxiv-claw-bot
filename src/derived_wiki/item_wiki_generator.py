from __future__ import annotations

import json
import hashlib
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ITEM_INDEX_LINK = "- [Items](items/index.md)"
CATEGORY_SLUGS = {
    "건블레이드": "geombeulreideu",
}


@dataclass(frozen=True)
class ItemRecord:
    id: str
    name: str
    url: str
    category: str | None
    subcategory: str | None
    item_level: int | None
    equip_level: int | None
    jobs: tuple[str, ...]
    stats: dict[str, Any]
    source: dict[str, Any]
    description: str | None
    raw_path: str


def generate_item_wiki(
    conn: sqlite3.Connection,
    wiki_root: Path,
    *,
    dry_run: bool = False,
    verbose: bool = False,
) -> dict[str, Any]:
    items = _load_items(conn)
    planned_paths = _planned_paths(wiki_root, items)
    if not dry_run:
        _write_pages(conn, wiki_root, items)

    result = {
        "status": "ok",
        "dry_run": dry_run,
        "planned_paths": [_display_path(path, wiki_root) for path in planned_paths],
        "written": [] if dry_run else [_display_path(path, wiki_root) for path in planned_paths],
        "summary": {
            "items": len(items),
            "categories": len(_category_names(items)),
        },
    }
    if verbose:
        result["wiki_root"] = str(wiki_root)
    return result


def _load_items(conn: sqlite3.Connection) -> list[ItemRecord]:
    rows = conn.execute(
        """
        SELECT id, name, url, category, subcategory, item_level, equip_level,
               jobs_json, stats_json, source_json, description, raw_path
          FROM guide_items
         ORDER BY category, subcategory, name, id
        """
    ).fetchall()
    return [
        ItemRecord(
            id=row[0],
            name=row[1],
            url=row[2],
            category=row[3],
            subcategory=row[4],
            item_level=row[5],
            equip_level=row[6],
            jobs=tuple(_json_loads(row[7], [])),
            stats=dict(_json_loads(row[8], {})),
            source=dict(_json_loads(row[9], {})),
            description=row[10],
            raw_path=row[11],
        )
        for row in rows
    ]


def _planned_paths(wiki_root: Path, items: list[ItemRecord]) -> list[Path]:
    paths = [wiki_root / "items" / "index.md"]
    paths.extend(
        wiki_root / "items" / "categories" / f"{_slug(category)}.md"
        for category in _category_names(items)
    )
    paths.extend(wiki_root / "items" / f"{item.id}.md" for item in items)
    return paths


def _write_pages(conn: sqlite3.Connection, wiki_root: Path, items: list[ItemRecord]) -> None:
    _write_item_index(conn, wiki_root, items)
    for category in _category_names(items):
        category_items = [item for item in items if _category_name(item) == category]
        _write_category_page(conn, wiki_root, category, category_items)
    for item in items:
        _write_item_page(conn, wiki_root, item)
    _update_root_index(wiki_root)
    conn.commit()


def _write_item_index(conn: sqlite3.Connection, wiki_root: Path, items: list[ItemRecord]) -> None:
    lines = ["# Items", "", "## Categories"]
    for category in _category_names(items):
        lines.append(f"- [{category}](categories/{_slug(category)}.md)")
    lines.extend(["", "## Item List"])
    for item in items:
        lines.append(f"- [{item.name}]({item.id}.md)")
    path = wiki_root / "items" / "index.md"
    _write_text(path, "\n".join(lines).rstrip() + "\n")


def _write_category_page(
    conn: sqlite3.Connection,
    wiki_root: Path,
    category: str,
    items: list[ItemRecord],
) -> None:
    lines = [f"# {category}", "", "## Items"]
    for item in items:
        level = f" IL {item.item_level}" if item.item_level is not None else ""
        lines.append(f"- [{item.name}](../{item.id}.md){level}")
    path = wiki_root / "items" / "categories" / f"{_slug(category)}.md"
    _write_text(path, "\n".join(lines).rstrip() + "\n")


def _write_item_page(conn: sqlite3.Connection, wiki_root: Path, item: ItemRecord) -> None:
    path = wiki_root / "items" / f"{item.id}.md"
    content = _render_item_page(item)
    _write_text(path, content)
    _upsert_wiki_page(
        conn,
        page_id=f"item_{item.id}",
        title=item.name,
        path=_display_path(path, wiki_root),
        body=content,
    )


def _render_item_page(item: ItemRecord) -> str:
    lines = [
        f"# {item.name}",
        "",
        "## Official Source",
        "",
        f"- URL: {item.url}",
        f"- Raw path: `{item.raw_path}`",
        "",
        "## Item Facts",
        "",
        f"- Category: {item.category or 'Unknown'}",
        f"- Subcategory: {item.subcategory or 'Unknown'}",
        f"- Item level: {_value_or_unknown(item.item_level)}",
        f"- Equip level: {_value_or_unknown(item.equip_level)}",
    ]
    if item.jobs:
        lines.append(f"- Allowed jobs: {', '.join(item.jobs)}")
    else:
        lines.append("- Allowed jobs: current KB has no job restriction data.")

    lines.extend(["", "## Stats", ""])
    if item.stats:
        for key, value in sorted(item.stats.items()):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- Current KB has no stat data for this item.")

    lines.extend(["", "## Acquisition", ""])
    source_text = str(item.source.get("text") or "").strip()
    if source_text:
        lines.append(f"- {source_text}")
    else:
        lines.append("- Current KB has no acquisition data for this item.")

    lines.extend(["", "## Description", ""])
    lines.append(item.description or "Current KB has no description data for this item.")
    lines.extend(["", "## Confidence", "", "- Source-grounded official DB item pilot page; verify with live official guide if freshness matters.", ""])
    return "\n".join(lines)


def _upsert_wiki_page(
    conn: sqlite3.Connection,
    *,
    page_id: str,
    title: str,
    path: str,
    body: str,
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    existing = conn.execute("SELECT id FROM wiki_pages WHERE id = ?", (page_id,)).fetchone()
    if existing:
        conn.execute(
            """
            UPDATE wiki_pages
               SET type = ?, title = ?, path = ?, confidence = ?, updated_at = ?
             WHERE id = ?
            """,
            ("item", title, path, "high", timestamp, page_id),
        )
    else:
        conn.execute(
            """
            INSERT INTO wiki_pages (
                id, type, title, path, source_ids, confidence, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (page_id, "item", title, path, json.dumps([], ensure_ascii=False), "high", timestamp, timestamp),
        )
    conn.execute("DELETE FROM wiki_fts WHERE page_id = ?", (page_id,))
    conn.execute(
        "INSERT INTO wiki_fts (page_id, title, body) VALUES (?, ?, ?)",
        (page_id, title, body),
    )


def _update_root_index(wiki_root: Path) -> None:
    index_path = wiki_root / "index.md"
    existing = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Wiki\n"
    if ITEM_INDEX_LINK in existing:
        return
    content = existing.rstrip() + "\n\n## Item Wiki\n\n" + ITEM_INDEX_LINK + "\n"
    _write_text(index_path, content)


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _category_names(items: list[ItemRecord]) -> list[str]:
    return sorted({_category_name(item) for item in items})


def _category_name(item: ItemRecord) -> str:
    return item.subcategory or item.category or "unknown"


def _slug(value: str) -> str:
    if value in CATEGORY_SLUGS:
        return CATEGORY_SLUGS[value]
    ascii_slug = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if ascii_slug:
        return ascii_slug
    return f"category_{hashlib.sha1(value.encode('utf-8')).hexdigest()[:12]}"


def _display_path(path: Path, wiki_root: Path) -> str:
    try:
        return path.relative_to(wiki_root.parent).as_posix()
    except ValueError:
        return path.as_posix()


def _value_or_unknown(value: int | None) -> str:
    return str(value) if value is not None else "Unknown"


def _json_loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default
