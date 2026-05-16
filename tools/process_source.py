from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import ingest_local
from tools import generate_derived_wiki
from tools import local_rebuild
from tools import status_notification
from tools.fetch_url import fetch_single_url
from tools.sync_storage import DB_PATH, DEFAULT_STORAGE_ROOT
from src.source_processing import (
    SourceDecodingError,
    SourceParseError,
    UnsupportedSourceExtensionError,
    extract_source_text,
)


SUPPORTED_SOURCE_TYPES = {
    "text_note",
    "markdown_file",
    "plain_text_file",
    "url",
    "binary_attachment",
}
SUPPORTED_CATEGORIES = {
    "urls",
    "documents",
    "sheets",
    "patch_notes",
    "raid_guides",
    "job_guides",
    "static_docs",
    "macros",
    "bis_sheets",
    "personal_notes",
}
FILE_SOURCE_TYPES = {"markdown_file", "plain_text_file", "binary_attachment"}


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)
    error = _validation_error(args)
    if error:
        _print_json(_error_result(args, error["message"], error["next_action"]))
        return

    if args.dry_run:
        _print_json(_dry_run_result(args))
        return

    if args.source_type in {"text_note", *FILE_SOURCE_TYPES}:
        _print_json(_apply_local_source(args))
        return

    if args.source_type == "url":
        _print_json(_apply_url_source(args))
        return

    _print_json(
        _error_result(
            args,
            f"Apply pipeline is not implemented for source_type={args.source_type}.",
            "Implement the matching v0.5 follow-up goal before running apply mode.",
            actions=[
                {"name": "validate_request", "status": "ok"},
                {
                    "name": "ingest",
                    "status": "error",
                    "error": f"Apply pipeline is not implemented for source_type={args.source_type}.",
                },
            ],
        )
    )


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Process one FFXIV KB source through the v0.5 source pipeline."
    )
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--source-type")
    parser.add_argument("--category")
    parser.add_argument("--title")
    parser.add_argument("--body")
    parser.add_argument("--local-path")
    parser.add_argument("--url")
    parser.add_argument("--storage-root", default=str(DEFAULT_STORAGE_ROOT))
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--notion-page-id")
    parser.add_argument("--build-derived-wiki", action="store_true")
    parser.add_argument("--skip-derived-wiki", action="store_true")
    return parser.parse_args(argv)


def _validation_error(args: argparse.Namespace) -> dict[str, str] | None:
    if args.apply and args.dry_run:
        return {
            "message": "--apply and --dry-run cannot be used together.",
            "next_action": "Choose exactly one mode: --apply or --dry-run.",
        }
    if args.build_derived_wiki and args.skip_derived_wiki:
        return {
            "message": "--build-derived-wiki and --skip-derived-wiki cannot be used together.",
            "next_action": "Choose at most one derived wiki option.",
        }
    if not args.apply and not args.dry_run:
        return {
            "message": "Missing required mode: --apply or --dry-run.",
            "next_action": "Choose exactly one mode: --apply or --dry-run.",
        }
    if not args.source_type:
        return {
            "message": "Missing required argument: --source-type",
            "next_action": "Provide a supported source type.",
        }
    if args.source_type not in SUPPORTED_SOURCE_TYPES:
        return {
            "message": f"Unsupported source type: {args.source_type}",
            "next_action": "Use text_note, markdown_file, plain_text_file, url, or binary_attachment.",
        }
    if not args.category:
        return {
            "message": "Missing required argument: --category",
            "next_action": "Provide a supported category.",
        }
    if args.category not in SUPPORTED_CATEGORIES:
        return {
            "message": f"Unsupported category: {args.category}",
            "next_action": "Provide one of the v0.5 supported categories.",
        }
    if args.source_type == "text_note" and not args.body:
        return {
            "message": "Missing required argument: --body",
            "next_action": "Provide the text note body.",
        }
    if args.source_type == "url":
        if not args.url:
            return {
                "message": "Missing required argument: --url",
                "next_action": "Provide a valid URL.",
            }
        if not _is_valid_http_url(args.url):
            return {
                "message": f"Invalid URL: {args.url}",
                "next_action": "Provide an absolute http or https URL.",
            }
    if args.source_type in FILE_SOURCE_TYPES:
        if not args.local_path:
            return {
                "message": "Missing required argument: --local-path",
                "next_action": "Provide an existing local file path.",
            }
        if not Path(args.local_path).is_file():
            return {
                "message": f"Local path does not exist or is not a file: {args.local_path}",
                "next_action": "Provide an existing local file path.",
            }
    return None


def _is_valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _base_result(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "status": None,
        "dry_run": bool(args.dry_run),
        "source_id": None,
        "source_type": args.source_type,
        "category": args.category,
        "title": args.title,
        "canonical_path": None,
        "local_source_path": None,
        "raw_path": None,
        "content_hash": None,
        "wiki_path": None,
        "graph_status": "skipped",
        "error_stage": None,
        "last_error": None,
        "next_action": None,
        "extract_metadata": {},
        "derived_wiki": {"status": "skipped", "reason": "not_requested"},
        "actions": [],
        "notion_update": {},
        "summary": {},
    }


def _error_result(
    args: argparse.Namespace,
    error: str,
    next_action: str,
    actions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = _base_result(args)
    result["status"] = "error"
    result["actions"] = actions or [
        {"name": "validate_request", "status": "error", "error": error}
    ]
    result["notion_update"] = {
        "Status": "Error",
        "Graph Status": "Skipped",
        "Last Error": error,
        "Next Action": next_action,
    }
    result["summary"] = {
        "message": "Request validation failed.",
        "next_action": next_action,
    }
    return result


def _dry_run_result(args: argparse.Namespace) -> dict[str, Any]:
    result = _base_result(args)
    result["status"] = "skipped"
    result["actions"] = [
        {"name": "validate_request", "status": "ok"},
        {"name": "ingest_local", "status": "skipped", "reason": "dry_run"},
        {"name": "rebuild", "status": "skipped", "reason": "dry_run"},
    ]
    result["summary"] = {
        "message": "Dry run completed. No files or database rows were written.",
        "next_action": "Run with --apply after reviewing the request.",
    }
    return result


def _apply_local_source(args: argparse.Namespace) -> dict[str, Any]:
    extract_action: dict[str, Any] | None = None
    extract_metadata: dict[str, Any] = {}
    title = args.title or "untitled"

    if args.source_type == "text_note":
        body = args.body or ""
    else:
        try:
            extracted = extract_source_text(Path(args.local_path))
        except (UnsupportedSourceExtensionError, SourceDecodingError, SourceParseError) as exc:
            return _local_extract_error_result(args, exc)
        body = extracted.text
        title = args.title or extracted.title or "untitled"
        extract_metadata = extracted.metadata
        extract_action = {
            "name": "extract",
            "status": "ok",
            "source_path": extract_metadata.get("source_path") or args.local_path,
            "extension": extract_metadata.get("extension"),
            "extractor": extract_metadata.get("extractor_name"),
        }

    ingest_result = ingest_local.ingest_source(
        source_type=args.source_type,
        category=args.category,
        title=title,
        body=body,
        storage_root=Path(args.storage_root),
        db_path=Path(args.db_path),
        root_path=ROOT,
        dry_run=False,
    )

    if ingest_result.get("status") != "ok":
        return _local_ingest_error_result(args, ingest_result)

    return _successful_ingest_result(
        args,
        ingest_result,
        fetch_action=None,
        extract_action=extract_action,
        extract_metadata=extract_metadata,
        title=title,
    )


def _apply_url_source(args: argparse.Namespace) -> dict[str, Any]:
    try:
        fetch_result = fetch_single_url(args.url)
    except Exception as exc:
        return _url_fetch_error_result(args, str(exc))

    title = args.title or fetch_result.get("title") or "untitled"
    ingest_result = ingest_local.ingest_source(
        source_type="url",
        category=args.category,
        title=title,
        body=fetch_result.get("body", ""),
        storage_root=Path(args.storage_root),
        db_path=Path(args.db_path),
        root_path=ROOT,
        dry_run=False,
    )

    if ingest_result.get("status") != "ok":
        return _url_ingest_error_result(args, title, fetch_result, ingest_result)

    fetch_action = _fetch_action_from_result(args, fetch_result)
    return _successful_ingest_result(args, ingest_result, fetch_action=fetch_action, title=title)


def _local_ingest_error_result(
    args: argparse.Namespace,
    ingest_result: dict[str, Any],
) -> dict[str, Any]:
    error_message = _ingest_error_message(ingest_result)
    result = _base_result(args)
    canonical_path = ingest_result.get("canonical_path")
    result.update(
        {
            "status": "error",
            "source_id": ingest_result.get("source_id"),
            "canonical_path": canonical_path,
            "local_source_path": canonical_path,
            "raw_path": ingest_result.get("raw_path"),
            "content_hash": ingest_result.get("content_hash"),
            "graph_status": "skipped",
            "actions": [
                {"name": "validate_request", "status": "ok"},
                {
                    "name": "ingest_local",
                    "status": "error",
                    "error": error_message,
                },
                {
                    "name": "rebuild",
                    "status": "skipped",
                    "reason": "upstream_ingest_error",
                },
            ],
            "notion_update": {
                "Status": "Error",
                "Graph Status": "Skipped",
                "Last Error": error_message,
                "Next Action": "Fix the local ingest error, then rerun process_source.py.",
            },
            "summary": {
                "message": "Local ingest failed. Rebuild was skipped.",
                "next_action": "Fix the local ingest error, then rerun process_source.py.",
            },
        }
    )
    return result


def _local_extract_error_result(
    args: argparse.Namespace,
    error: UnsupportedSourceExtensionError | SourceDecodingError | SourceParseError,
) -> dict[str, Any]:
    error_message = _extract_error_message(error)
    result = _base_result(args)
    result.update(
        {
            "status": "error",
            "graph_status": "skipped",
            "error_stage": "extract",
            "last_error": error_message,
            "next_action": "Fix the source file or source type, then rerun process_source.py.",
            "actions": [
                {"name": "validate_request", "status": "ok"},
                {
                    "name": "extract",
                    "status": "error",
                    "source_path": args.local_path,
                    "error_stage": "extract",
                    "error": error_message,
                },
                {
                    "name": "ingest_local",
                    "status": "skipped",
                    "reason": "upstream_extract_error",
                },
                {
                    "name": "rebuild",
                    "status": "skipped",
                    "reason": "upstream_extract_error",
                },
            ],
            "notion_update": {
                "Status": "Error",
                "Graph Status": "Skipped",
                "Last Error": error_message,
                "Next Action": "Fix the source file or source type, then rerun process_source.py.",
            },
            "summary": {
                "message": "Source extraction failed. Local ingest and rebuild were skipped.",
                "next_action": "Fix the source file or source type, then rerun process_source.py.",
            },
        }
    )
    return result


def _extract_error_message(
    error: UnsupportedSourceExtensionError | SourceDecodingError | SourceParseError,
) -> str:
    if isinstance(error, UnsupportedSourceExtensionError):
        return str(error)
    if isinstance(error, SourceDecodingError):
        return f"Decoding failed: {error}"
    if isinstance(error, SourceParseError):
        return f"Parse failed: {error}"
    return str(error)


def _ingest_error_message(ingest_result: dict[str, Any]) -> str:
    for action in reversed(ingest_result.get("actions", [])):
        if action.get("status") in {"failed", "error"}:
            return str(action.get("message") or action.get("error") or "Local ingest failed.")
    return "Local ingest failed."


def _url_fetch_error_result(args: argparse.Namespace, error_message: str) -> dict[str, Any]:
    result = _base_result(args)
    result.update(
        {
            "status": "error",
            "graph_status": "skipped",
            "actions": [
                {"name": "validate_request", "status": "ok"},
                {
                    "name": "fetch_url",
                    "status": "error",
                    "url": args.url,
                    "error": error_message,
                },
                {
                    "name": "ingest_local",
                    "status": "skipped",
                    "reason": "upstream_fetch_error",
                },
                {
                    "name": "rebuild",
                    "status": "skipped",
                    "reason": "upstream_fetch_error",
                },
            ],
            "notion_update": {
                "Status": "Error",
                "Graph Status": "Skipped",
                "Last Error": error_message,
                "Next Action": "Fix the URL fetch error, then rerun process_source.py.",
            },
            "summary": {
                "message": "URL fetch failed. Local ingest was skipped.",
                "next_action": "Fix the URL fetch error, then rerun process_source.py.",
            },
        }
    )
    return result


def _url_ingest_error_result(
    args: argparse.Namespace,
    title: str,
    fetch_result: dict[str, Any],
    ingest_result: dict[str, Any],
) -> dict[str, Any]:
    error_message = _ingest_error_message(ingest_result)
    result = _base_result(args)
    canonical_path = ingest_result.get("canonical_path")
    result.update(
        {
            "status": "error",
            "source_id": ingest_result.get("source_id"),
            "title": title,
            "canonical_path": canonical_path,
            "local_source_path": canonical_path,
            "raw_path": ingest_result.get("raw_path"),
            "content_hash": ingest_result.get("content_hash"),
            "graph_status": "skipped",
            "actions": [
                {"name": "validate_request", "status": "ok"},
                {
                    "name": "fetch_url",
                    "status": "ok",
                    "url": fetch_result.get("url") or args.url,
                    "content_type": fetch_result.get("content_type"),
                    **_fetch_action_metadata(fetch_result),
                },
                {
                    "name": "ingest_local",
                    "status": "error",
                    "error": error_message,
                },
                {
                    "name": "rebuild",
                    "status": "skipped",
                    "reason": "upstream_ingest_error",
                },
            ],
            "notion_update": {
                "Status": "Error",
                "Graph Status": "Skipped",
                "Last Error": error_message,
                "Next Action": "Fix the local ingest error, then rerun process_source.py.",
            },
            "summary": {
                "message": "URL was fetched, but local ingest failed. Rebuild was skipped.",
                "next_action": "Fix the local ingest error, then rerun process_source.py.",
            },
        }
    )
    return result


def _fetch_action_from_result(
    args: argparse.Namespace,
    fetch_result: dict[str, Any],
) -> dict[str, Any]:
    return {
        "name": "fetch_url",
        "status": "ok",
        "url": fetch_result.get("url") or args.url,
        "content_type": fetch_result.get("content_type"),
        **_fetch_action_metadata(fetch_result),
    }


def _fetch_action_metadata(fetch_result: dict[str, Any]) -> dict[str, Any]:
    if "extractor" not in fetch_result:
        return {}
    return {"extractor": fetch_result.get("extractor")}


def _successful_ingest_result(
    args: argparse.Namespace,
    ingest_result: dict[str, Any],
    *,
    fetch_action: dict[str, Any] | None,
    extract_action: dict[str, Any] | None = None,
    extract_metadata: dict[str, Any] | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    result = _base_result(args)
    canonical_path = ingest_result.get("canonical_path")
    base_actions = [{"name": "validate_request", "status": "ok"}]
    if extract_action:
        base_actions.append(extract_action)
    if fetch_action:
        base_actions.append(fetch_action)
    base_actions.append(
        {
            "name": "ingest_local",
            "status": "ok",
            "source_id": ingest_result.get("source_id"),
        }
    )

    rebuild_result = _run_rebuild(args, ingest_result)
    rebuild_actions = _normalize_rebuild_actions(rebuild_result)
    last_error = _first_rebuild_error(rebuild_actions)
    next_action = (
        "Fix the rebuild error, then rerun process_source.py."
        if last_error
        else None
    )

    result.update(
        {
            "status": "partial" if rebuild_result.get("status") != "ok" else "ok",
            "source_id": ingest_result.get("source_id"),
            "title": title or ingest_result.get("title") or args.title,
            "canonical_path": canonical_path,
            "local_source_path": canonical_path,
            "raw_path": ingest_result.get("raw_path"),
            "content_hash": ingest_result.get("content_hash"),
            "wiki_path": rebuild_result.get("wiki_path"),
            "graph_status": _graph_status_from_rebuild(rebuild_actions),
            "last_error": last_error,
            "next_action": next_action,
            "extract_metadata": extract_metadata or {},
            "actions": base_actions + rebuild_actions,
            "summary": {
                "message": (
                    "Source ingested and rebuilt."
                    if not last_error
                    else "Source ingested, but one or more rebuild steps failed."
                ),
                "next_action": next_action or "Review the generated Notion payload.",
            },
        }
    )
    _attach_notion_update(result)
    _attach_derived_wiki(result, args)
    return result


def _attach_derived_wiki(result: dict[str, Any], args: argparse.Namespace) -> None:
    if not args.build_derived_wiki or args.skip_derived_wiki:
        return
    if result.get("status") != "ok":
        result["derived_wiki"] = {
            "status": "skipped",
            "reason": "upstream_source_not_ok",
        }
        result["actions"].append(
            {
                "name": "generate_derived_wiki",
                "status": "skipped",
                "reason": "upstream_source_not_ok",
            }
        )
        return
    derived_args = argparse.Namespace(
        kind="jobs",
        job=None,
        patch_range=None,
        dry_run=False,
        summary_root=str(ROOT / "wiki" / "source_summaries"),
        target_root=str(ROOT / "wiki" / "jobs"),
        include_limited=False,
    )
    try:
        derived_result = generate_derived_wiki.run(derived_args)
    except Exception as exc:
        error_message = str(exc)
        result["derived_wiki"] = {
            "status": "error",
            "error_stage": "derived_wiki_generate",
            "error_message": error_message,
        }
        result["actions"].append(
            {
                "name": "generate_derived_wiki",
                "status": "error",
                "error_stage": "derived_wiki_generate",
                "error": error_message,
            }
        )
        return

    status = "ok" if derived_result.get("status") == "ok" else "skipped"
    result["derived_wiki"] = {
        "status": status,
        "targets": [
            action.get("path")
            for action in derived_result.get("actions", [])
            if action.get("status") == "generated"
        ],
        "summary": derived_result.get("summary", {}),
    }
    result["actions"].append(
        {
            "name": "generate_derived_wiki",
            "status": status,
            "summary": derived_result.get("summary", {}),
        }
    )


def _run_rebuild(
    args: argparse.Namespace,
    ingest_result: dict[str, Any],
) -> dict[str, Any]:
    try:
        return local_rebuild.rebuild_after_ingest(
            ingest_result,
            root_path=ROOT,
            db_path=Path(args.db_path),
            dry_run=False,
        )
    except Exception as exc:
        return {
            "status": "partial",
            "source_id": ingest_result.get("source_id"),
            "wiki_path": None,
            "actions": [
                {
                    "action": "rebuild",
                    "status": "failed",
                    "message": str(exc),
                }
            ],
            "summary": {"total": 1, "ok": 0, "partial": 0, "errors": 1, "skipped": 0},
        }


def _normalize_rebuild_actions(rebuild_result: dict[str, Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for action in rebuild_result.get("actions", []):
        status = str(action.get("status") or "")
        name = str(action.get("name") or action.get("action") or "rebuild")
        normalized_action: dict[str, Any] = {
            "name": name,
            "status": "error" if status == "failed" else status,
        }
        for key in (
            "source_id",
            "wiki_path",
            "char_count",
            "nodes",
            "edges",
            "message",
            "error",
            "error_type",
            "reason",
        ):
            if key in action:
                normalized_action[key] = action[key]
        normalized.append(normalized_action)
    return normalized


def _first_rebuild_error(actions: list[dict[str, Any]]) -> str | None:
    for action in actions:
        if action.get("status") == "error":
            return str(
                action.get("error")
                or action.get("message")
                or f"{action.get('name', 'rebuild')} failed"
            )
    return None


def _graph_status_from_rebuild(actions: list[dict[str, Any]]) -> str:
    for action in actions:
        if action.get("name") == "build_graph":
            if action.get("status") == "ok":
                return "built"
            if action.get("status") == "error":
                return "failed"
            return str(action.get("status") or "pending")
    return "pending"


def _attach_notion_update(result: dict[str, Any]) -> None:
    try:
        payload = status_notification.build_notion_status_update(result)
        payload["Last Processed"] = _now_iso()
        payload.setdefault("Last Error", str(result.get("last_error") or ""))
        payload.setdefault("Next Action", str(result.get("next_action") or ""))
        result["notion_update"] = payload
        result["actions"].append({"name": "build_notion_payload", "status": "ok"})
    except Exception as exc:
        result["notion_update"] = {}
        result["last_error"] = str(exc)
        result["actions"].append(
            {
                "name": "build_notion_payload",
                "status": "error",
                "error": str(exc),
            }
        )


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _print_json(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
