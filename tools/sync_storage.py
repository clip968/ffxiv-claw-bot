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
APPLY_ACTIONS = ("write_local_source", "snapshot_raw", "upsert_source")
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


def now_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()


def write_local_source(
    item: dict[str, Any],
    storage_root: Path,
) -> dict[str, Any]:
    """Write the original source file under storage_root/sources/<category>/..."""
    canonical_path = canonical_path_for_item(item)
    source_id = source_id_for_item(item)
    target_path = storage_root / canonical_path
    action = {
        "action": "write_local_source",
        "source_id": source_id,
        "target": str(target_path),
    }

    body = item.get("body")
    if not body:
        # If item already exists at storage_root, nothing to do
        if target_path.exists():
            action["status"] = "skipped"
            action["message"] = "No body in manifest; file already exists at storage_root"
            return action
        action["status"] = "failed"
        action["message"] = "No body provided and source file does not exist at storage_root"
        return action

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(body, encoding="utf-8")
    action["status"] = "written"
    action["message"] = f"Written {len(body)} bytes to {target_path}"
    return action


def snapshot_raw(
    item: dict[str, Any],
    *,
    root_path: Path,
    storage_root: Path,
) -> dict[str, Any]:
    """Create a processing snapshot under root_path/raw/local_storage/<category>/..."""
    canonical_path = canonical_path_for_item(item)
    source_id = source_id_for_item(item)
    raw_relative = planned_raw_path(item)
    target_path = root_path / raw_relative
    action = {
        "action": "snapshot_raw",
        "source_id": source_id,
        "target": str(target_path),
    }

    source_path = storage_root / canonical_path
    if not source_path.exists():
        action["status"] = "failed"
        action["message"] = f"Source file does not exist at {source_path}"
        return action

    body = source_path.read_text(encoding="utf-8")
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(body, encoding="utf-8")
    action["status"] = "written"
    action["message"] = f"Snapshot {len(body)} bytes from {source_path} to {target_path}"
    return action


def upsert_source(
    item: dict[str, Any],
    db_path: Path,
    *,
    root_path: Path,
) -> dict[str, Any]:
    """Insert or update sources DB entry."""
    source_id = source_id_for_item(item) or ""
    canonical_path = canonical_path_for_item(item)
    raw_relative = planned_raw_path(item)
    title = str(item.get("title", ""))
    source_type = str(item.get("source_type") or item.get("sourceType") or "local_document")
    content_hash = str(item.get("content_hash") or item.get("contentHash") or "")
    source_url = local_source_url(canonical_path) if canonical_path else None
    timestamp = now_iso()
    action = {
        "action": "upsert_source",
        "source_id": source_id,
        "target": source_id,
    }

    if not db_path.exists():
        action["status"] = "failed"
        action["message"] = f"Database not found: {db_path}"
        return action

    conn = sqlite3.connect(db_path)
    try:
        existing = conn.execute(
            "SELECT id FROM sources WHERE id = ?", (source_id,)
        ).fetchone()

        if existing:
            conn.execute(
                """
                UPDATE sources
                   SET title = ?, source_url = ?, raw_path = ?,
                       content_hash = ?, updated_at = ?
                 WHERE id = ?
                """,
                (title, source_url, raw_relative, content_hash, timestamp, source_id),
            )
            action["status"] = "updated"
            action["message"] = f"Updated source {source_id}"
        else:
            conn.execute(
                """
                INSERT INTO sources (id, source_type, title, source_url,
                                     raw_path, content_hash,
                                     created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (source_id, source_type, title, source_url,
                 raw_relative, content_hash,
                 timestamp, timestamp),
            )
            action["status"] = "inserted"
            action["message"] = f"Inserted source {source_id}"
        conn.commit()
    finally:
        conn.close()

    return action


def apply_sync(
    manifest_path: Path,
    db_path: Path = DB_PATH,
    *,
    root_path: Path = ROOT,
    storage_root: Path = DEFAULT_STORAGE_ROOT,
) -> dict[str, Any]:
    """Execute the sync plan: write local sources, create raw snapshots, upsert DB."""
    manifest = load_manifest(manifest_path)
    # Explicit storage_root parameter takes priority over manifest value
    resolved_storage_root = storage_root
    existing_sources = load_existing_local_sources(db_path)

    actions: list[dict[str, Any]] = []
    summary: dict[str, int] = {
        "write_local_source": 0,
        "snapshot_raw": 0,
        "upsert_source": 0,
        "unchanged": 0,
        "failed": 0,
        "skipped": 0,
    }
    had_failure = False

    for item in manifest.get("files", []):
        classifier = classify_item(item, existing_sources)

        if classifier in ("skipped", "unchanged"):
            summary["skipped" if classifier == "skipped" else "unchanged"] += 1
            if classifier == "unchanged":
                actions.append({
                    "action": "write_local_source",
                    "source_id": source_id_for_item(item),
                    "target": str(resolved_storage_root / canonical_path_for_item(item)),
                    "status": "skipped",
                    "message": f"Unchanged item {source_id_for_item(item)}: no sync needed",
                })
            continue

        # 1. Write local source
        write_result = write_local_source(item, resolved_storage_root)
        actions.append(write_result)
        if write_result.get("status") == "failed":
            summary["failed"] += 1
            had_failure = True
            continue
        summary["write_local_source"] += 1

        # 2. Snapshot raw
        snap_result = snapshot_raw(
            item,
            root_path=root_path,
            storage_root=resolved_storage_root,
        )
        actions.append(snap_result)
        if snap_result.get("status") == "failed":
            summary["failed"] += 1
            had_failure = True
            continue
        summary["snapshot_raw"] += 1

        # 3. Upsert DB
        upsert_result = upsert_source(item, db_path, root_path=root_path)
        actions.append(upsert_result)
        if upsert_result.get("status") == "failed":
            summary["failed"] += 1
            had_failure = True
            continue
        summary["upsert_source"] += 1

    return {
        "status": "partial" if had_failure else "ok",
        "dry_run": False,
        "storage_root": str(resolved_storage_root),
        "summary": summary,
        "actions": actions,
    }


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Local Storage manifest sync planning and execution. "
                    "Use --dry-run for planning or --apply to execute."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writes")
    parser.add_argument("--apply", action="store_true", help="Execute sync: write sources, create snapshots, upsert DB")
    parser.add_argument("--manifest", required=True, help="Local Storage manifest JSON path")
    parser.add_argument("--db-path", default=str(DB_PATH), help="SQLite DB path")
    parser.add_argument("--storage-root", default=None, help="Override storage root path")
    args = parser.parse_args(argv)

    if args.apply:
        storage_root = Path(args.storage_root) if args.storage_root else DEFAULT_STORAGE_ROOT
        result = apply_sync(
            Path(args.manifest),
            Path(args.db_path),
            storage_root=storage_root,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.dry_run:
        parser.error("Use --dry-run for planning or --apply to execute the sync")

    result = plan_sync(Path(args.manifest), Path(args.db_path))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
