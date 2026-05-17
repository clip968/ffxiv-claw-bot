# ffxiv-notion-status

## Purpose

Use this skill when OpenClaw needs to update or report Notion status from a repo
pipeline result.

## Trigger

Examples:

- "처리 결과를 Notion에 반영해줘."
- "Graph Status를 Built로 기록해줘."
- "이 process_source 결과의 notion_update를 적용해줘."

Do not use this skill to store source content, rebuild the KB, or answer a KB
question.

## Payload Sources

Preferred source:

- Use `result["notion_update"]` returned by `tools/process_source.py`.

Fallback helpers:

- `tools.status_notification.build_notion_status_update(result)`
- `tools.openclaw_notion_control.build_notion_update(result)`

The helper names must remain visible in this skill: `build_notion_status_update`
and `build_notion_update`.

## Required Fields

Check for these when present:

- `Status`
- `Graph Status`
- `Source ID`
- `Local Source Path`
- `Wiki Path`
- `Last Processed`
- `Last Error`
- `Next Action`

## Forbidden Payload Content

Never upload source content to Notion.

The Notion payload must not include:

- `body`
- `attachments`
- `raw_html`
- `raw_body`
- binary bytes
- full SQLite records
- `graph/nodes.json` or `graph/edges.json` content

If any forbidden field is present, strip it before Notion write or stop and
report the unsafe payload.

## Status Rules

- `status=ok` + `graph_status=built` -> `Status=Graph Built`,
  `Graph Status=Built`
- `status=ok` without built graph -> `Status=Indexed`
- `status=partial` -> `Status=Partial`
- `status=error` -> `Status=Error`

Notion is a control/status layer, not the source of truth.
