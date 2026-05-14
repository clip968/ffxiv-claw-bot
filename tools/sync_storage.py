from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"
DEFAULT_STORAGE_ROOT = Path("/mnt/d/ffixiv-bot-storage")

LOCAL_SOURCE_PREFIX = "local://"
DRY_RUN_ACTIONS = ("new", "changed", "unchanged", "skipped")
VALID_CATEGORIES = {
    "patch_notes",
    "job_guides",
    "raid_guides",
    "static_docs",
    "macros",
    "bis_sheets",
    "personal_notes",
}
LOCAL_SOURCE_TYPES = {"local_file", "local_document"}
CONTENT_TYPE_EXTENSIONS = {
    "text/markdown": "md",
    "text/plain": "txt",
    "text/html": "html",
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
}


def safe_path_part(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9가-힣._-]+", "_", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    normalized = normalized.strip("._")
    return normalized or "untitled"


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def canonical_path_for_item(item: dict[str, Any]) -> str:
    return str(item.get("canonical_path") or item.get("canonicalPath") or "")


def local_source_url(canonical_path: str) -> str:
    normalized = canonical_path.replace("\\", "/").lstrip("/")
    return f"{LOCAL_SOURCE_PREFIX}{normalized}"


def local_source_id(canonical_path: str) -> str:
    digest = hashlib.sha256(canonical_path.encode("utf-8")).hexdigest()[:12]
    return f"local_{digest}"


def source_id_for_item(item: dict[str, Any]) -> str | None:
    source_id = item.get("source_id") or item.get("sourceId")
    if source_id:
        return str(source_id)

    canonical_path = canonical_path_for_item(item)
    if canonical_path:
        return local_source_id(canonical_path)

    return None


def extension_for_item(item: dict[str, Any]) -> str:
    canonical_path = canonical_path_for_item(item)
    suffix = Path(canonical_path).suffix.lower().lstrip(".")
    if suffix:
        return suffix

    content_type = item.get("content_type") or item.get("contentType")
    return CONTENT_TYPE_EXTENSIONS.get(str(content_type), "bin")


def planned_raw_path(item: dict[str, Any]) -> str:
    source_id = source_id_for_item(item)
    if not source_id:
        raise ValueError("source_id or canonical_path is required")

    title = str(item["title"])
    category = str(item["category"])
    extension = extension_for_item(item)

    filename = f"{safe_path_part(title)}__{safe_path_part(source_id)}.{extension}"
    return f"raw/local_storage/{safe_path_part(category)}/{filename}"


def load_existing_local_sources(db_path: Path) -> dict[str, dict[str, Any]]:
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
                 WHERE source_type IN (?, ?)
                   AND source_url LIKE ?
                """,
                ("local_file", "local_document", f"{LOCAL_SOURCE_PREFIX}%"),
            ).fetchall()
        except sqlite3.OperationalError:
            return {}
    finally:
        conn.close()

    existing: dict[str, dict[str, Any]] = {}
    for row in rows:
        canonical_path = row["source_url"].removeprefix(LOCAL_SOURCE_PREFIX)
        existing[canonical_path] = dict(row)

    return existing


def missing_required_reason(item: dict[str, Any]) -> str | None:
    required_fields = (
        "title",
        "category",
        "source_type",
        "content_type",
        "canonical_path",
        "content_hash",
    )
    for field in required_fields:
        if not (item.get(field) or item.get(_camel_case(field))):
            return f"missing required metadata: {field}"

    category = str(item.get("category"))
    if category not in VALID_CATEGORIES:
        return f"invalid category: {category}"

    return None


def _camel_case(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


def classify_item(item: dict[str, Any], existing_sources: dict[str, dict[str, Any]]) -> str:
    if missing_required_reason(item):
        return "skipped"

    canonical_path = canonical_path_for_item(item)
    existing = existing_sources.get(canonical_path)
    if not existing:
        return "new"

    content_hash = item.get("content_hash") or item.get("contentHash")
    if existing["content_hash"] == content_hash:
        return "unchanged"

    return "changed"


def build_plan_item(
    item: dict[str, Any],
    existing_sources: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    action = classify_item(item, existing_sources)
    canonical_path = canonical_path_for_item(item)
    source_id = source_id_for_item(item)
    planned_path = planned_raw_path(item) if action != "skipped" else None

    result = {
        "source_id": source_id,
        "title": item.get("title"),
        "category": item.get("category"),
        "source_type": item.get("source_type") or item.get("sourceType"),
        "content_type": item.get("content_type") or item.get("contentType"),
        "canonical_path": canonical_path or None,
        "source_url": local_source_url(canonical_path) if canonical_path else None,
        "action": action,
        "planned_raw_path": planned_path,
    }

    if action == "skipped":
        result["reason"] = missing_required_reason(item) or "missing required dry-run metadata"

    return result


def plan_sync(
    manifest_path: Path,
    db_path: Path = DB_PATH,
    *,
    root_path: Path = ROOT,
) -> dict[str, Any]:
    del root_path
    manifest = load_manifest(manifest_path)
    existing_sources = load_existing_local_sources(db_path)
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
        "storage_root": manifest.get("storage_root") or str(DEFAULT_STORAGE_ROOT),
        "summary": summary,
        "items": items,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run Local Storage manifest sync planning."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writes")
    parser.add_argument("--manifest", required=True, help="Local Storage manifest JSON path")
    parser.add_argument("--db-path", default=str(DB_PATH), help="SQLite DB path")
    args = parser.parse_args(argv)

    if not args.dry_run:
        parser.error("--dry-run is required; apply writes are not implemented yet")

    result = plan_sync(Path(args.manifest), Path(args.db_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
