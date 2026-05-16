from __future__ import annotations

import argparse
import contextlib
import io
import json
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import process_source
from tools.sync_storage import DB_PATH, DEFAULT_STORAGE_ROOT


QUEUE_SCHEMA = """
CREATE TABLE IF NOT EXISTS source_processing_queue (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  category TEXT NOT NULL,
  title TEXT,
  body TEXT,
  local_path TEXT,
  url TEXT,
  status TEXT NOT NULL DEFAULT 'pending',
  error_stage TEXT,
  error_message TEXT,
  retry_count INTEGER NOT NULL DEFAULT 0,
  processed_source_id TEXT,
  graph_status TEXT,
  result_json TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  last_attempt_at TEXT,
  last_success_at TEXT
)
"""

FILE_SOURCE_TYPES = {"markdown_file", "plain_text_file", "binary_attachment"}
LOCAL_FILE_FILTER_TYPES = tuple(sorted(FILE_SOURCE_TYPES))
PROCESSED_STATUSES = {"processed", "derived_wiki_built"}


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    db_path = Path(args.db_path)
    result = process_pending_sources(args, db_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process pending source queue rows through tools/process_source.py."
    )
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--source-type", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--retry-errors", action="store_true")
    parser.add_argument("--max-retry", type=int, default=3)
    parser.add_argument("--build-derived-wiki", action="store_true")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--storage-root", default=str(DEFAULT_STORAGE_ROOT))
    return parser.parse_args(argv)


def process_pending_sources(args: argparse.Namespace, db_path: Path) -> dict[str, Any]:
    if args.dry_run and not db_path.exists():
        return _dry_run_result(args, db_path, [])

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        if args.dry_run:
            if not _queue_table_exists(conn):
                return _dry_run_result(args, db_path, [])
        else:
            _ensure_queue_schema(conn)
        targets = _select_targets(conn, args)
        if args.dry_run:
            return _dry_run_result(args, db_path, targets)
        return _process_targets(conn, args, db_path, targets)
    finally:
        conn.close()


def _ensure_queue_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(QUEUE_SCHEMA)
    conn.commit()


def _queue_table_exists(conn: sqlite3.Connection) -> bool:
    row = conn.execute(
        """
        SELECT 1
          FROM sqlite_master
         WHERE type = 'table'
           AND name = 'source_processing_queue'
        """
    ).fetchone()
    return row is not None


def _select_targets(
    conn: sqlite3.Connection,
    args: argparse.Namespace,
) -> list[sqlite3.Row]:
    clauses = ["status = 'pending'"]
    params: list[Any] = []
    if args.retry_errors:
        clauses = ["(status = 'pending' OR (status = 'error' AND retry_count < ?))"]
        params.append(args.max_retry)

    source_type_clause, source_type_params = _source_type_filter(args.source_type)
    if source_type_clause:
        clauses.append(source_type_clause)
        params.extend(source_type_params)

    limit = max(0, args.limit)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT *
          FROM source_processing_queue
         WHERE {' AND '.join(clauses)}
         ORDER BY created_at ASC, id ASC
         LIMIT ?
        """,
        params,
    ).fetchall()
    return list(rows)


def _source_type_filter(source_type: str | None) -> tuple[str | None, list[Any]]:
    if not source_type:
        return None, []
    if source_type == "local_file":
        placeholders = ", ".join("?" for _ in LOCAL_FILE_FILTER_TYPES)
        return f"source_type IN ({placeholders})", list(LOCAL_FILE_FILTER_TYPES)
    return "source_type = ?", [source_type]


def _dry_run_result(
    args: argparse.Namespace,
    db_path: Path,
    targets: list[sqlite3.Row],
) -> dict[str, Any]:
    actions = [
        {
            "source_id": row["id"],
            "source_type": row["source_type"],
            "status": "planned",
        }
        for row in targets
    ]
    return {
        "status": "skipped",
        "dry_run": True,
        "db_path": str(db_path),
        "limit": args.limit,
        "retry_errors": bool(args.retry_errors),
        "actions": actions,
        "summary": _summary(actions, targeted=len(targets)),
    }


def _process_targets(
    conn: sqlite3.Connection,
    args: argparse.Namespace,
    db_path: Path,
    targets: list[sqlite3.Row],
) -> dict[str, Any]:
    actions: list[dict[str, Any]] = []
    for row in targets:
        _mark_in_progress(conn, row["id"])
        try:
            source_result = _run_process_source(row, args)
        except Exception as exc:
            source_result = {
                "status": "error",
                "error_stage": "process_pending",
                "last_error": str(exc),
                "graph_status": "skipped",
            }

        if source_result.get("status") == "ok":
            action = _mark_processed(conn, row["id"], source_result)
        else:
            action = _mark_error(conn, row, source_result)
        actions.append(action)

    status = _overall_status(actions)
    return {
        "status": status,
        "dry_run": False,
        "db_path": str(db_path),
        "limit": args.limit,
        "retry_errors": bool(args.retry_errors),
        "actions": actions,
        "summary": _summary(actions, targeted=len(targets)),
    }


def _mark_in_progress(conn: sqlite3.Connection, source_id: str) -> None:
    timestamp = _now_iso()
    conn.execute(
        """
        UPDATE source_processing_queue
           SET status = 'in_progress',
               updated_at = ?,
               last_attempt_at = ?
         WHERE id = ?
        """,
        (timestamp, timestamp, source_id),
    )
    conn.commit()


def _mark_processed(
    conn: sqlite3.Connection,
    source_id: str,
    source_result: dict[str, Any],
) -> dict[str, Any]:
    timestamp = _now_iso()
    row_status = _processed_row_status(source_result)
    derived_error = _derived_wiki_error(source_result)
    conn.execute(
        """
        UPDATE source_processing_queue
           SET status = ?,
               error_stage = ?,
               error_message = ?,
               processed_source_id = ?,
               graph_status = ?,
               result_json = ?,
               updated_at = ?,
               last_success_at = ?
         WHERE id = ?
        """,
        (
            row_status,
            derived_error.get("error_stage"),
            derived_error.get("error_message"),
            source_result.get("source_id"),
            source_result.get("graph_status"),
            json.dumps(source_result, ensure_ascii=False, sort_keys=True),
            timestamp,
            timestamp,
            source_id,
        ),
    )
    conn.commit()
    action = {
        "source_id": source_id,
        "status": row_status,
        "result_status": source_result.get("status"),
        "processed_source_id": source_result.get("source_id"),
        "graph_status": source_result.get("graph_status"),
    }
    if derived_error:
        action["error_stage"] = derived_error["error_stage"]
        action["error_message"] = derived_error["error_message"]
    return action


def _mark_error(
    conn: sqlite3.Connection,
    row: sqlite3.Row,
    source_result: dict[str, Any],
) -> dict[str, Any]:
    timestamp = _now_iso()
    error_stage = _error_stage(source_result)
    error_message = _error_message(source_result)
    retry_count = int(row["retry_count"] or 0) + 1
    conn.execute(
        """
        UPDATE source_processing_queue
           SET status = 'error',
               error_stage = ?,
               error_message = ?,
               retry_count = ?,
               processed_source_id = ?,
               graph_status = ?,
               result_json = ?,
               updated_at = ?
         WHERE id = ?
        """,
        (
            error_stage,
            error_message,
            retry_count,
            source_result.get("source_id"),
            source_result.get("graph_status"),
            json.dumps(source_result, ensure_ascii=False, sort_keys=True),
            timestamp,
            row["id"],
        ),
    )
    conn.commit()
    return {
        "source_id": row["id"],
        "status": "error",
        "result_status": source_result.get("status"),
        "error_stage": error_stage,
        "error_message": error_message,
        "retry_count": retry_count,
    }


def _run_process_source(row: sqlite3.Row, args: argparse.Namespace) -> dict[str, Any]:
    process_argv = _process_source_argv(row, args)
    stdout = io.StringIO()
    with contextlib.redirect_stdout(stdout):
        process_source.main(process_argv)
    output = stdout.getvalue()
    try:
        return json.loads(output)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"process_source.py returned invalid JSON: {output}") from exc


def _process_source_argv(row: sqlite3.Row, args: argparse.Namespace) -> list[str]:
    source_type = row["source_type"]
    argv = [
        "--apply",
        "--source-type",
        source_type,
        "--category",
        row["category"],
        "--title",
        row["title"] or row["id"],
        "--storage-root",
        args.storage_root,
        "--db-path",
        args.db_path,
    ]
    if source_type == "text_note":
        body = row["body"]
        if not body:
            raise ValueError(f"Queue source {row['id']} is missing body.")
        return _with_derived_flag([*argv, "--body", body], args)
    if source_type == "url":
        url = row["url"]
        if not url:
            raise ValueError(f"Queue source {row['id']} is missing url.")
        return _with_derived_flag([*argv, "--url", url], args)
    if source_type in FILE_SOURCE_TYPES:
        local_path = row["local_path"]
        if not local_path:
            raise ValueError(f"Queue source {row['id']} is missing local_path.")
        return _with_derived_flag([*argv, "--local-path", local_path], args)
    raise ValueError(f"Unsupported queue source_type: {source_type}")


def _with_derived_flag(argv: list[str], args: argparse.Namespace) -> list[str]:
    if args.build_derived_wiki:
        return [*argv, "--build-derived-wiki"]
    return argv


def _error_stage(source_result: dict[str, Any]) -> str:
    if source_result.get("error_stage"):
        return str(source_result["error_stage"])
    for action in source_result.get("actions", []):
        if action.get("status") == "error":
            return str(action.get("name") or "process_source")
    return "process_source"


def _error_message(source_result: dict[str, Any]) -> str:
    if source_result.get("last_error"):
        return str(source_result["last_error"])
    for action in source_result.get("actions", []):
        if action.get("status") == "error":
            return str(
                action.get("error")
                or action.get("message")
                or f"{action.get('name', 'process_source')} failed"
            )
    summary = source_result.get("summary") or {}
    if summary.get("message"):
        return str(summary["message"])
    return "process_source.py failed."


def _overall_status(actions: list[dict[str, Any]]) -> str:
    if not actions:
        return "skipped"
    if any(action.get("status") == "error" for action in actions):
        return "partial"
    return "ok"


def _summary(actions: list[dict[str, Any]], *, targeted: int) -> dict[str, int]:
    return {
        "targeted": targeted,
        "processed": sum(1 for action in actions if action.get("status") in PROCESSED_STATUSES),
        "derived_wiki_built": sum(
            1 for action in actions if action.get("status") == "derived_wiki_built"
        ),
        "errors": sum(1 for action in actions if action.get("status") == "error"),
        "planned": sum(1 for action in actions if action.get("status") == "planned"),
    }


def _processed_row_status(source_result: dict[str, Any]) -> str:
    if (source_result.get("derived_wiki") or {}).get("status") == "ok":
        return "derived_wiki_built"
    return "processed"


def _derived_wiki_error(source_result: dict[str, Any]) -> dict[str, str]:
    derived = source_result.get("derived_wiki") or {}
    if derived.get("status") != "error":
        return {}
    return {
        "error_stage": str(derived.get("error_stage") or "derived_wiki_generate"),
        "error_message": str(derived.get("error_message") or "Derived wiki generation failed."),
    }


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    main()
