"""tools/status_notification.py

v04-05: Status Notification.

Converts a final result JSON from the ingest+rebuild pipeline into:
  - A Discord/OpenClaw-facing human-readable summary (``format_discord_summary``).
  - A Notion property update payload (``build_notion_status_update``).

Both functions derive from the same result JSON.

Contract (per v04-05 plan):
  - ``ok`` result       -> success message with paths.
  - ``partial`` result  -> paths plus failure reason and next action.
  - ``error`` result    -> failure reason and next action.
  - Default user-facing summary must NOT include a Drive URL.
  - Notion payload uses the v04-02 status/property conventions.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Notion status mapping (v04-05 scope)
# ---------------------------------------------------------------------------

# CLI result status -> Notion Status
_CLI_STATUS_TO_NOTION: dict[str, str] = {
    "ok": "Indexed",
    "partial": "Partial",
    "error": "Error",
    "queued": "Queued",
    "snapshot": "Snapshot",
    "archived": "Archived",
    "skipped": "Skipped",
}

# graph_status value -> Notion Graph Status (v04-05 uses "Failed" not "Error")
_GRAPH_STATUS_TO_NOTION: dict[str, str] = {
    "built": "Built",
    "pending": "Pending",
    "failed": "Failed",
    "skipped": "Skipped",
    "": "",
}

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def format_discord_summary(result: dict[str, Any]) -> str:
    """Format a pipeline result into a short Discord/OpenClaw-facing summary.

    Parameters
    ----------
    result : dict
        Pipeline result JSON with at least ``status``, ``title``,
        ``category``, and optionally ``local_source_path``, ``wiki_path``,
        ``graph_status``, ``last_error``, ``next_action``.

    Returns
    -------
    str
        Human-readable summary (Korean-friendly plain text).
    """
    parts: list[str] = []

    status = str(result.get("status") or "").lower()
    title = result.get("title") or ""
    category = result.get("category") or ""
    local_source_path = result.get("local_source_path")
    wiki_path = result.get("wiki_path")
    graph_status = result.get("graph_status")
    last_error = result.get("last_error")
    next_action = result.get("next_action")

    # Header with status icon and title
    if status == "ok":
        parts.append(f"[{category}] {title} — 처리 완료")
    elif status == "partial":
        parts.append(f"[{category}] {title} — 일부 실패")
    elif status == "error":
        parts.append(f"[{category}] {title} — 처리 실패")
    elif status == "skipped":
        parts.append(f"[{category}] {title} — 건너뜀 (처리 생략)")
    else:
        parts.append(f"[{category}] {title}")

    # Local source path
    if local_source_path:
        parts.append(f"로컬 경로: {local_source_path}")

    # Wiki path
    if wiki_path:
        parts.append(f"Wiki: {wiki_path}")

    # Graph status (only if non-empty and not "built")
    if graph_status and str(graph_status).lower() != "built":
        parts.append(f"Graph: {graph_status}")

    # Error detail
    if last_error:
        parts.append(f"오류: {last_error}")

    # Next action
    if next_action:
        parts.append(f"다음 액션: {next_action}")

    # NOTE: Drive URL is intentionally excluded per v04-05 contract.
    # Legacy Drive integration users can check the Drive runbook separately.

    return "\n".join(parts)


def build_notion_status_update(result: dict[str, Any]) -> dict[str, str]:
    """Convert a pipeline result into a Notion property update payload.

    Parameters
    ----------
    result : dict
        Pipeline result JSON (same shape as ``format_discord_summary``).

    Returns
    -------
    dict[str, str]
        Flat dict of Notion property names to string values.
    """
    payload: dict[str, str] = {}

    status = str(result.get("status") or "").lower()
    graph_status_raw = str(result.get("graph_status") or "").lower()
    title = result.get("title")
    category = result.get("category")
    source_id = result.get("source_id")
    local_source_path = result.get("local_source_path")
    wiki_path = result.get("wiki_path")
    last_error = result.get("last_error")
    next_action = result.get("next_action")

    # --- Status ---
    # If graph is built, promote "ok" -> "Graph Built"
    if status == "ok" and graph_status_raw == "built":
        payload["Status"] = "Graph Built"
    else:
        payload["Status"] = _CLI_STATUS_TO_NOTION.get(status, "Error")

    # --- Title ---
    if title:
        payload["Title"] = str(title)

    # --- Category ---
    if category:
        payload["Category"] = str(category)

    # --- Source ID ---
    if source_id:
        payload["Source ID"] = str(source_id)

    # --- Local Source Path ---
    if local_source_path:
        payload["Local Source Path"] = str(local_source_path)

    # --- Wiki Path ---
    if wiki_path:
        payload["Wiki Path"] = str(wiki_path)

    # --- Graph Status ---
    if graph_status_raw:
        payload["Graph Status"] = _GRAPH_STATUS_TO_NOTION.get(
            graph_status_raw, graph_status_raw.capitalize()
        )

    # --- Last Error ---
    if last_error:
        payload["Last Error"] = str(last_error)

    # --- Next Action ---
    if next_action:
        payload["Next Action"] = str(next_action)

    return payload
