from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"

DRIVE_SOURCE_PREFIX = "gdrive://"
DRY_RUN_ACTIONS = ("new", "changed", "unchanged", "skipped")


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
        "source_url": item.get("webViewLink") or f"{DRIVE_SOURCE_PREFIX}{item.get('id')}",
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

    args = parser.parse_args(argv)
    if not args.dry_run:
        parser.error("v0.3 only supports --dry-run")

    result = plan_sync(args.manifest, args.db_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
