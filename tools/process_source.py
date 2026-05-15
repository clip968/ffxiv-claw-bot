from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import ingest_local
from tools.fetch_url import fetch_single_url
from tools.sync_storage import DB_PATH, DEFAULT_STORAGE_ROOT


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

    if args.source_type in {"text_note", "markdown_file", "plain_text_file"}:
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
    return parser.parse_args(argv)


def _validation_error(args: argparse.Namespace) -> dict[str, str] | None:
    if args.apply and args.dry_run:
        return {
            "message": "--apply and --dry-run cannot be used together.",
            "next_action": "Choose exactly one mode: --apply or --dry-run.",
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
    body = _local_source_body(args)
    ingest_result = ingest_local.ingest_source(
        source_type=args.source_type,
        category=args.category,
        title=args.title or "untitled",
        body=body,
        storage_root=Path(args.storage_root),
        db_path=Path(args.db_path),
        root_path=ROOT,
        dry_run=False,
    )

    if ingest_result.get("status") != "ok":
        return _local_ingest_error_result(args, ingest_result)

    result = _base_result(args)
    canonical_path = ingest_result.get("canonical_path")
    result.update(
        {
            "status": "ok",
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
                    "status": "ok",
                    "source_id": ingest_result.get("source_id"),
                },
                {
                    "name": "rebuild",
                    "status": "skipped",
                    "reason": "v05-06_not_implemented",
                },
            ],
            "summary": {
                "message": "Local source ingested. Rebuild is intentionally skipped in v0.5-04.",
                "next_action": "Run the v0.5-06 rebuild integration goal.",
            },
        }
    )
    return result


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

    result = _base_result(args)
    canonical_path = ingest_result.get("canonical_path")
    result.update(
        {
            "status": "ok",
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
                },
                {
                    "name": "ingest_local",
                    "status": "ok",
                    "source_id": ingest_result.get("source_id"),
                },
                {
                    "name": "rebuild",
                    "status": "skipped",
                    "reason": "v05-06_not_implemented",
                },
            ],
            "summary": {
                "message": "URL source fetched and ingested. Rebuild is intentionally skipped in v0.5-05.",
                "next_action": "Run the v0.5-06 rebuild integration goal.",
            },
        }
    )
    return result


def _local_source_body(args: argparse.Namespace) -> str:
    if args.source_type == "text_note":
        return args.body or ""
    return Path(args.local_path).read_text(encoding="utf-8")


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


def _print_json(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
