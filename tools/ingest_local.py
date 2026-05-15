from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from tools.sync_storage import (
    DB_PATH,
    DEFAULT_STORAGE_ROOT,
    LOCAL_REQUEST_SOURCE_TYPES,
    ROOT,
    VALID_CATEGORIES,
    local_source_id,
    safe_path_part,
)

SOURCE_TYPE_EXTENSIONS: dict[str, str] = {
    "text_note": "md",
    "markdown_file": "md",
    "plain_text_file": "md",
    "url": "md",
    "binary_attachment": "bin",
}


def _determine_extension(source_type: str) -> str:
    return SOURCE_TYPE_EXTENSIONS.get(source_type, "md")


def _canonical_path(category: str, title: str, source_type: str) -> str:
    safe_title = safe_path_part(title)
    ext = _determine_extension(source_type)
    return f"sources/{safe_path_part(category)}/{safe_title}.{ext}"


def _raw_path(category: str, title: str, source_type: str, source_id: str) -> str:
    safe_title = safe_path_part(title)
    ext = _determine_extension(source_type)
    return (
        f"raw/local_storage/{safe_path_part(category)}"
        f"/{safe_title}__{safe_path_part(source_id)}.{ext}"
    )


def _validate(args: argparse.Namespace) -> dict[str, Any] | None:
    if args.source_type not in LOCAL_REQUEST_SOURCE_TYPES:
        return {
            "action": "validate_request",
            "target": None,
            "status": "failed",
            "message": f"invalid source_type: {args.source_type}",
            "error_type": "invalid_input",
        }
    if args.category not in VALID_CATEGORIES:
        return {
            "action": "validate_request",
            "target": None,
            "status": "failed",
            "message": f"invalid category: {args.category}",
            "error_type": "invalid_input",
        }
    if not args.title:
        return {
            "action": "validate_request",
            "target": None,
            "status": "failed",
            "message": "title is required",
            "error_type": "invalid_input",
        }
    if args.source_type in ("text_note", "markdown_file", "plain_text_file") and not args.body:
        return {
            "action": "validate_request",
            "target": None,
            "status": "failed",
            "message": f"body is required for source_type={args.source_type}",
            "error_type": "invalid_input",
        }
    return None


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a note/text/file/URL into Local Storage."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Plan without writes",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Execute ingest: write source, snapshot, upsert DB",
    )
    parser.add_argument(
        "--source-type",
        required=True,
        help="Input type: text_note, markdown_file, plain_text_file, url, binary_attachment",
    )
    parser.add_argument("--category", required=True, help="Content category")
    parser.add_argument("--title", required=True, help="Document title")
    parser.add_argument("--body", default=None, help="Text body content")
    parser.add_argument("--url", default=None, help="URL for source_type=url")
    parser.add_argument(
        "--storage-root", default=str(DEFAULT_STORAGE_ROOT), help="Storage root path"
    )
    parser.add_argument("--db-path", default=str(DB_PATH), help="SQLite DB path")
    args = parser.parse_args(argv)

    result = ingest_source(
        source_type=args.source_type,
        category=args.category,
        title=args.title,
        body=args.body,
        storage_root=Path(args.storage_root),
        db_path=Path(args.db_path),
        root_path=ROOT,
        dry_run=bool(args.dry_run),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


def ingest_source(
    *,
    source_type: str,
    category: str,
    title: str,
    body: str | None,
    storage_root: Path,
    db_path: Path,
    root_path: Path = ROOT,
    dry_run: bool = False,
) -> dict[str, Any]:
    args = argparse.Namespace(
        source_type=source_type,
        category=category,
        title=title,
        body=body,
        storage_root=str(storage_root),
        db_path=str(db_path),
    )
    is_dry_run = bool(dry_run)

    # 1. Validate request
    validation_error = _validate(args)
    if validation_error:
        actions: list[dict[str, Any]] = [validation_error]
        return {
            "status": "error",
            "dry_run": is_dry_run,
            "actions": actions,
            "summary": {"total": 1, "ok": 0, "partial": 0, "errors": 1, "skipped": 0},
        }

    # Build metadata
    canonical = _canonical_path(args.category, args.title, args.source_type)
    source_id = local_source_id(canonical)
    target_path = str(storage_root / canonical)
    raw_rel = _raw_path(args.category, args.title, args.source_type, source_id)
    content_hash = hashlib.sha256((args.body or "").encode("utf-8")).hexdigest()

    actions: list[dict[str, Any]] = []

    # validate_request action
    actions.append({
        "action": "validate_request",
        "target": None,
        "status": "ok",
        "message": "Request validated",
    })

    if is_dry_run:
        # write_local_source (planned only)
        actions.append({
            "action": "write_local_source",
            "source_id": source_id,
            "target": target_path,
            "status": "planned",
            "message": f"Dry-run: would write local source to {target_path}",
        })
        # snapshot_raw (planned only)
        actions.append({
            "action": "snapshot_raw",
            "source_id": source_id,
            "target": raw_rel,
            "status": "planned",
            "message": f"Dry-run: would create raw snapshot at {raw_rel}",
        })
        # upsert_source (planned only)
        actions.append({
            "action": "upsert_source",
            "source_id": source_id,
            "target": source_id,
            "status": "planned",
            "message": f"Dry-run: would upsert source {source_id} in DB",
        })
    else:
        # --apply mode: actually write files and upsert DB
        _do_write_local_source(actions, args, storage_root, canonical, source_id, target_path)
        if actions[-1].get("status") == "failed":
            return _finalize_result(
                is_dry_run=False,
                actions=actions,
                status_override="error",
                source_id=source_id,
                canonical=canonical,
                raw_rel=raw_rel,
                storage_root=storage_root,
                content_hash=content_hash,
            )

        _do_snapshot_raw(actions, args, source_id, raw_rel, root_path)
        _do_upsert_source(actions, args, source_id)

    summary = {
        "total": len(actions),
        "ok": sum(
            1
            for a in actions
            if a.get("status")
            in ("ok", "planned", "written", "inserted", "updated")
        ),
        "partial": 0,
        "errors": sum(1 for a in actions if a.get("status") == "failed"),
        "skipped": sum(1 for a in actions if a.get("status") == "skipped"),
    }
    final_status = "error" if summary["errors"] > 0 else "ok"

    return {
        "status": final_status,
        "dry_run": is_dry_run,
        "source_id": source_id,
        "source_type": args.source_type,
        "category": args.category,
        "title": args.title,
        "canonical_path": canonical,
        "raw_path": raw_rel,
        "content_hash": content_hash,
        "storage_root": str(storage_root),
        "actions": actions,
        "summary": summary,
    }


def _do_write_local_source(
    actions: list[dict[str, Any]],
    args: argparse.Namespace,
    storage_root: Path,
    canonical: str,
    source_id: str,
    target_path: str,
) -> None:
    if not storage_root.exists() or not storage_root.is_dir():
        actions.append({
            "action": "write_local_source",
            "source_id": source_id,
            "target": target_path,
            "status": "failed",
            "error_type": "local_storage_root_missing",
            "message": f"Storage root does not exist or is not a directory: {storage_root}",
        })
        return

    target_path_obj = (storage_root / canonical).resolve()
    try:
        target_path_obj.relative_to(storage_root.resolve())
    except ValueError:
        actions.append({
            "action": "write_local_source",
            "source_id": source_id,
            "target": target_path,
            "status": "failed",
            "error_type": "invalid_input",
            "message": (
                f"canonical_path '{canonical}'"
                f" resolves outside storage_root '{storage_root}'"
            ),
        })
        return

    target_path_obj.parent.mkdir(parents=True, exist_ok=True)
    body = args.body or ""
    target_path_obj.write_text(body, encoding="utf-8")
    actions.append({
        "action": "write_local_source",
        "source_id": source_id,
        "target": target_path,
        "status": "written",
        "message": f"Written {len(body)} bytes to {target_path}",
    })


def _do_snapshot_raw(
    actions: list[dict[str, Any]],
    args: argparse.Namespace,
    source_id: str,
    raw_rel: str,
    root_path: Path = ROOT,
) -> None:
    raw_path = root_path / raw_rel
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    body = args.body or ""
    raw_path.write_text(body, encoding="utf-8")
    actions.append({
        "action": "snapshot_raw",
        "source_id": source_id,
        "target": raw_rel,
        "status": "written",
        "message": f"Snapshot {len(body)} bytes to {raw_rel}",
    })


def _do_upsert_source(
    actions: list[dict[str, Any]],
    args: argparse.Namespace,
    source_id: str,
) -> None:
    db_path = Path(args.db_path)
    if not db_path.exists():
        actions.append({
            "action": "upsert_source",
            "source_id": source_id,
            "target": source_id,
            "status": "failed",
            "message": f"Database not found: {db_path}",
        })
        return

    from datetime import datetime, timezone

    timestamp = datetime.now(timezone.utc).isoformat()
    canonical = _canonical_path(args.category, args.title, args.source_type)
    source_url = f"local://{canonical}"
    raw_rel = _raw_path(args.category, args.title, args.source_type, source_id)
    body_hash = hashlib.sha256((args.body or "").encode("utf-8")).hexdigest()

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
                (args.title, source_url, raw_rel, body_hash, timestamp, source_id),
            )
            status = "updated"
        else:
            conn.execute(
                """
                INSERT INTO sources (id, source_type, title, source_url,
                                     raw_path, content_hash, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_id,
                    "local_document",
                    args.title,
                    source_url,
                    raw_rel,
                    body_hash,
                    timestamp,
                    timestamp,
                ),
            )
            status = "inserted"
        conn.commit()
    finally:
        conn.close()

    actions.append({
        "action": "upsert_source",
        "source_id": source_id,
        "target": source_id,
        "status": status,
        "message": f"{status.capitalize()} source {source_id}",
    })


def _finalize_result(
    *,
    is_dry_run: bool,
    actions: list[dict[str, Any]],
    status_override: str,
    source_id: str,
    canonical: str,
    raw_rel: str,
    storage_root: Path,
    content_hash: str,
) -> dict[str, Any]:
    summary = {
        "total": len(actions),
        "ok": sum(
            1
            for a in actions
            if a.get("status")
            in ("ok", "planned", "written", "inserted", "updated")
        ),
        "partial": 0,
        "errors": sum(1 for a in actions if a.get("status") == "failed"),
        "skipped": sum(1 for a in actions if a.get("status") == "skipped"),
    }
    return {
        "status": status_override,
        "dry_run": is_dry_run,
        "source_id": source_id,
        "canonical_path": canonical,
        "raw_path": raw_rel,
        "content_hash": content_hash,
        "storage_root": str(storage_root),
        "actions": actions,
        "summary": summary,
    }


if __name__ == "__main__":
    main()
