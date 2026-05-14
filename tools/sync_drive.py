from __future__ import annotations

import argparse
import json
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"

DRIVE_SOURCE_PREFIX = "gdrive://"
DRY_RUN_ACTIONS = ("new", "changed", "unchanged", "skipped")

SOURCES_SCHEMA = """
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  title TEXT,
  source_url TEXT,
  raw_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  language TEXT,
  patch TEXT,
  job TEXT,
  raid TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
)
"""


def safe_path_part(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9가-힣._-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("._")
    return normalized or "untitled"


def planned_raw_path(item: dict[str, Any]) -> str:
    file_id = str(item["id"])
    title = str(item["name"])
    category = str(item["category"])
    extension = str(item["exportExt"]).lstrip(".")

    filename = f"{safe_path_part(title)}__{safe_path_part(file_id)}.{extension}"
    return f"raw/drive/{safe_path_part(category)}/{filename}"


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def drive_source_url(drive_file_id: str) -> str:
    return f"{DRIVE_SOURCE_PREFIX}{drive_file_id}"


def drive_source_id(drive_file_id: str) -> str:
    return f"drive_{safe_path_part(drive_file_id)}"


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def ensure_sources_table(conn: sqlite3.Connection) -> None:
    conn.execute(SOURCES_SCHEMA)


def load_existing_drive_sources(db_path: Path) -> dict[str, dict[str, Any]]:
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(db_path)
    try:
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                """
                SELECT id, title, source_url, raw_path, content_hash
                  FROM sources
                 WHERE source_type = ?
                   AND source_url LIKE ?
                """,
                ("drive_document", f"{DRIVE_SOURCE_PREFIX}%"),
            ).fetchall()
        except sqlite3.OperationalError:
            return {}
    finally:
        conn.close()

    existing: dict[str, dict[str, Any]] = {}
    for row in rows:
        source_url = row["source_url"]
        drive_file_id = source_url.removeprefix(DRIVE_SOURCE_PREFIX)
        existing[drive_file_id] = dict(row)

    return existing


def classify_item(item: dict[str, Any], existing_sources: dict[str, dict[str, Any]]) -> str:
    required_fields = ("id", "name", "category", "exportExt", "contentHash")
    if any(not item.get(field) for field in required_fields):
        return "skipped"

    existing = existing_sources.get(str(item["id"]))
    if not existing:
        return "new"

    if existing["content_hash"] == item["contentHash"]:
        return "unchanged"

    return "changed"


def build_plan_item(
    item: dict[str, Any],
    existing_sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    action = classify_item(item, existing_sources)
    planned_path = planned_raw_path(item) if action != "skipped" else None

    result = {
        "drive_file_id": item.get("id"),
        "title": item.get("name"),
        "category": item.get("category"),
        "mime_type": item.get("mimeType"),
        "modified_time": item.get("modifiedTime"),
        "source_url": item.get("webViewLink") or drive_source_url(str(item.get("id"))),
        "action": action,
        "planned_raw_path": planned_path,
    }

    if action == "skipped":
        result["reason"] = "missing required dry-run metadata"

    return result


def plan_sync(manifest_path: Path, db_path: Path = DB_PATH) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    existing_sources = load_existing_drive_sources(db_path)
    items = [
        build_plan_item(item, existing_sources)
        for item in manifest.get("files", [])
    ]

    summary = {action: 0 for action in DRY_RUN_ACTIONS}
    for item in items:
        summary[item["action"]] += 1

    return {
        "status": "ok",
        "dry_run": True,
        "root_folder": manifest.get("root_folder"),
        "summary": summary,
        "items": items,
    }


def resolve_content_fixture(manifest_path: Path, item: dict[str, Any]) -> Path | None:
    fixture = item.get("contentFixture")
    if not fixture:
        return None

    fixture_path = Path(str(fixture))
    if fixture_path.is_absolute():
        return fixture_path

    repo_relative = ROOT / fixture_path
    if repo_relative.exists():
        return repo_relative

    return manifest_path.parent / fixture_path


def write_raw_file(root_path: Path, relative_raw_path: str, content: str) -> None:
    raw_path = root_path / relative_raw_path
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(content, encoding="utf-8")


def upsert_drive_source(
    db_path: Path,
    item: dict[str, Any],
    relative_raw_path: str,
    existing_source: dict[str, Any] | None,
) -> None:
    now = utc_now()
    source_url = drive_source_url(str(item["id"]))

    with sqlite3.connect(db_path) as conn:
        ensure_sources_table(conn)
        if existing_source:
            conn.execute(
                """
                UPDATE sources
                   SET title = ?,
                       source_url = ?,
                       raw_path = ?,
                       content_hash = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    item["name"],
                    source_url,
                    relative_raw_path,
                    item["contentHash"],
                    now,
                    existing_source["id"],
                ),
            )
        else:
            conn.execute(
                """
                INSERT INTO sources (
                  id,
                  source_type,
                  title,
                  source_url,
                  raw_path,
                  content_hash,
                  created_at,
                  updated_at
                )
                VALUES (?, 'drive_document', ?, ?, ?, ?, ?, ?)
                """,
                (
                    drive_source_id(str(item["id"])),
                    item["name"],
                    source_url,
                    relative_raw_path,
                    item["contentHash"],
                    now,
                    now,
                ),
            )
        conn.commit()


def apply_sync(
    manifest_path: Path,
    db_path: Path = DB_PATH,
    root_path: Path = ROOT,
) -> dict[str, Any]:
    manifest = load_manifest(manifest_path)
    existing_sources = load_existing_drive_sources(db_path)
    items: list[dict[str, Any]] = []

    for item in manifest.get("files", []):
        plan_item = build_plan_item(item, existing_sources)
        action = plan_item["action"]

        if action in ("new", "changed"):
            content_fixture = resolve_content_fixture(manifest_path, item)
            if content_fixture is None or not content_fixture.exists():
                plan_item["action"] = "skipped"
                plan_item["planned_raw_path"] = None
                plan_item["reason"] = "missing content fixture"
            else:
                relative_raw_path = str(plan_item["planned_raw_path"])
                content = content_fixture.read_text(encoding="utf-8")
                write_raw_file(root_path, relative_raw_path, content)
                upsert_drive_source(
                    db_path,
                    item,
                    relative_raw_path,
                    existing_sources.get(str(item["id"])),
                )

        items.append(plan_item)

    summary = {action: 0 for action in DRY_RUN_ACTIONS}
    for item in items:
        summary[item["action"]] += 1

    return {
        "status": "ok",
        "dry_run": False,
        "root_folder": manifest.get("root_folder"),
        "summary": summary,
        "items": items,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Plan Google Drive sync for FFXIV knowledge base."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan changes without writing files or updating the database.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write manifest fixture content and upsert Drive source records.",
    )
    parser.add_argument(
        "--manifest",
        required=True,
        type=Path,
        help="Path to a local Drive manifest JSON file.",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DB_PATH,
        help="Path to the SQLite database.",
    )
    parser.add_argument(
        "--root-path",
        type=Path,
        default=ROOT,
        help="Repository root used for raw/drive writes.",
    )

    args = parser.parse_args(argv)
    if args.dry_run == args.apply:
        parser.error("choose exactly one of --dry-run or --apply")

    if args.dry_run:
        result = plan_sync(args.manifest, args.db_path)
    else:
        result = apply_sync(args.manifest, args.db_path, args.root_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
