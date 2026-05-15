"""Rebuild KB pipeline after successful local ingest.

Pipeline: compile_wiki -> index_fts -> build_graph
Consumes a successful local ingest result (v04-03 output).

Usage:
    python -c "from tools.local_rebuild import rebuild_after_ingest; ..."

Partial Failure Policy (per v04-04 plan):
  - upstream local ingest failed        -> skipped (no rebuild)
  - compile/wiki/FTS failed             -> status=partial
  - graph failed                        -> status=partial
  - Notion update failure               -> handled by v04-05
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"

REBUILD_ACTIONS = ["compile_wiki", "index_fts", "build_graph"]


def rebuild_after_ingest(
    ingest_result: dict[str, Any],
    root_path: Path | None = None,
    db_path: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Run the rebuild pipeline after a successful local ingest.

    Parameters
    ----------
    ingest_result : dict
        The result JSON from a local ingest operation.
        Must contain at least ``status``, ``source_id``, ``source_type``.
    root_path : Path or None
        Root of the repository (used to resolve relative raw paths).
        Defaults to ``tools.local_rebuild.ROOT``.
    db_path : Path or None
        Path to the SQLite database.
        Defaults to ``tools.local_rebuild.DB_PATH``.
    dry_run : bool
        If True, return planned actions without executing them.

    Returns
    -------
    dict
        Result with keys: ``status``, ``dry_run``, ``source_id``,
        ``actions`` (list), ``summary``.
    """
    resolved_root = root_path or ROOT
    resolved_db = db_path or DB_PATH

    source_id = ingest_result.get("source_id", "")
    source_type = ingest_result.get("source_type", "")
    result_status = ingest_result.get("status", "")

    # Upstream local ingest failure: do not run rebuild
    if result_status != "ok":
        return {
            "status": "skipped",
            "dry_run": dry_run,
            "source_id": source_id,
            "source_type": source_type,
            "reason": f"upstream ingest status is '{result_status}', not 'ok'",
            "actions": [],
            "summary": {"total": 0, "ok": 0, "partial": 0, "errors": 0, "skipped": 0},
        }

    if dry_run:
        return _plan_dry_run(source_id, source_type)

    return _execute_apply(source_id, source_type, resolved_root, resolved_db)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _plan_dry_run(source_id: str, source_type: str) -> dict[str, Any]:
    actions = [
        {
            "action": action_name,
            "source_id": source_id,
            "status": "planned",
            "message": f"Dry-run: would run {action_name} for {source_id}",
        }
        for action_name in REBUILD_ACTIONS
    ]
    return {
        "status": "ok",
        "dry_run": True,
        "source_id": source_id,
        "source_type": source_type,
        "actions": actions,
        "summary": {"total": 3, "ok": 3, "partial": 0, "errors": 0, "skipped": 0},
    }


def _execute_apply(
    source_id: str,
    source_type: str,
    root_path: Path,
    db_path: Path,
) -> dict[str, Any]:
    from tools.build_graph import build_graph
    from tools.compile_wiki import compile_for_source

    actions: list[dict[str, Any]] = []
    wiki_path: str | None = None

    # --- compile_wiki (also handles FTS internally) ---
    compile_result = compile_for_source(
        source_id,
        db_path=db_path,
        root_path=root_path,
        summary_dir=root_path / "wiki" / "source_summaries",
    )

    if compile_result.get("status") == "ok":
        wiki_path = compile_result.get("summary_path", "")
        char_count = compile_result.get("char_count", 0)
        actions.append({
            "action": "compile_wiki",
            "source_id": source_id,
            "status": "ok",
            "wiki_path": wiki_path,
            "char_count": char_count,
            "message": f"Wiki compiled for {source_id}: {char_count} chars",
        })
        actions.append({
            "action": "index_fts",
            "source_id": source_id,
            "status": "ok",
            "message": f"FTS indexed for {source_id}",
        })
    else:
        error_msg = compile_result.get("message", "unknown compile error")
        actions.append({
            "action": "compile_wiki",
            "source_id": source_id,
            "status": "failed",
            "error_type": "compile_failed",
            "message": error_msg,
        })
        actions.append({
            "action": "index_fts",
            "source_id": source_id,
            "status": "skipped",
            "message": f"Skipped due to compile_wiki failure: {error_msg}",
        })

    # --- build_graph (attempt even if compile failed per partial-failure policy) ---
    graph_dir = root_path / "graph"
    graph_result = build_graph(
        source_id,
        db_path=db_path,
        graph_dir=graph_dir,
    )

    if graph_result.get("status") == "ok":
        actions.append({
            "action": "build_graph",
            "source_id": source_id,
            "status": "ok",
            "nodes": graph_result.get("nodes", 0),
            "edges": graph_result.get("edges", 0),
            "message": (
                f"Graph built for {source_id}: "
                f"{graph_result.get('nodes', 0)} nodes, "
                f"{graph_result.get('edges', 0)} edges"
            ),
        })
    else:
        error_msg = graph_result.get("message", "unknown graph error")
        actions.append({
            "action": "build_graph",
            "source_id": source_id,
            "status": "failed",
            "error_type": "graph_failed",
            "message": error_msg,
        })

    # --- summary ---
    ok_count = sum(1 for a in actions if a.get("status") == "ok")
    failed_count = sum(1 for a in actions if a.get("status") == "failed")
    skipped_count = sum(1 for a in actions if a.get("status") == "skipped")

    final_status = "partial" if failed_count > 0 else "ok"

    return {
        "status": final_status,
        "dry_run": False,
        "source_id": source_id,
        "source_type": source_type,
        "wiki_path": wiki_path,
        "actions": actions,
        "summary": {
            "total": len(actions),
            "ok": ok_count,
            "partial": 0,
            "errors": failed_count,
            "skipped": skipped_count,
        },
    }
