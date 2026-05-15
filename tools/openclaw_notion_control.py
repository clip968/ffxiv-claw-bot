"""tools/openclaw_notion_control.py

v04-02: OpenClaw Notion Control Contract.

Owns: Notion schema / status mapping only.
Does NOT own: local file write, rebuild execution, Discord message formatting.

Notion is a control plane, NOT a file store.
File body and attachments must never be sent to Notion.
"""
from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Status mapping: CLI result "status" + optional "graph_status" -> Notion Status
# ---------------------------------------------------------------------------

# CLI result status -> Notion Status (when graph_status is absent or not "built")
_CLI_STATUS_TO_NOTION: dict[str, str] = {
    "ok": "Indexed",
    "partial": "Partial",
    "error": "Error",
    "queued": "Queued",
    "snapshot": "Snapshot",
    "archived": "Archived",
}

# graph_status value -> Notion "Graph Status" property
_GRAPH_STATUS_TO_NOTION: dict[str, str] = {
    "built": "Built",
    "pending": "Pending",
    "failed": "Error",
    "skipped": "Skipped",
    "": "",
}

# When graph_status == "built", the overall Notion Status is promoted to "Graph Built"
_GRAPH_BUILT_STATUS = "Graph Built"

# Fields from CLI result that must never appear in the Notion update payload
_BLOCKED_FIELDS: frozenset[str] = frozenset({"body", "attachments"})

# Allowed optional fields copied verbatim (snake_case key -> Notion property name)
_OPTIONAL_FIELD_MAP: dict[str, str] = {
    "last_processed": "Last Processed",
    "last_error": "Last Error",
    "next_action": "Next Action",
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_notion_update(result: dict[str, Any]) -> dict[str, Any]:
    """Convert a CLI result JSON into a Notion property update payload.

    Contract (v04-02):
    - Maps ``status`` (and ``graph_status``) to Notion ``Status``.
    - Copies title, category, source_id, local_source_path, wiki_path,
      graph_status verbatim (with property-name capitalisation).
    - MUST NOT include ``body`` or ``attachments`` in the output.
    - Returns a flat dict of Notion property names to values.
    """
    payload: dict[str, Any] = {}

    # --- Status ---
    cli_status = str(result.get("status") or "").lower()
    graph_status_raw = str(result.get("graph_status") or "").lower()

    if graph_status_raw == "built":
        notion_status = _GRAPH_BUILT_STATUS
    else:
        notion_status = _CLI_STATUS_TO_NOTION.get(cli_status, "Error")

    payload["Status"] = notion_status

    # --- Required fields ---
    if "title" in result:
        payload["Title"] = result["title"]
    if "category" in result:
        payload["Category"] = result["category"]
    if "source_id" in result:
        payload["Source ID"] = result["source_id"]
    if "local_source_path" in result:
        payload["Local Source Path"] = result["local_source_path"]
    if "wiki_path" in result:
        payload["Wiki Path"] = result["wiki_path"]

    # --- Graph Status (capitalized) ---
    if graph_status_raw:
        payload["Graph Status"] = _GRAPH_STATUS_TO_NOTION.get(graph_status_raw, graph_status_raw.capitalize())

    # --- Optional metadata fields ---
    for key, notion_name in _OPTIONAL_FIELD_MAP.items():
        if key in result and result[key] is not None:
            payload[notion_name] = result[key]

    # Safety check: blocked fields must not appear in output
    for blocked in _BLOCKED_FIELDS:
        payload.pop(blocked, None)

    return payload
