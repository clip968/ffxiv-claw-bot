# ffxiv-openclaw-router

## Purpose

Use this skill first when an OpenClaw request could map to more than one FFXIV
KB workflow. It chooses the specific skill and prevents ad hoc tool selection.

## Routing Table

| Use case | Trigger examples | Skill | Entrypoint |
|---|---|---|---|
| save / ingest / index source | "저장해줘", "KB에 반영", "이 URL/파일/메모 ingest" | `ffxiv-source-processing` | `python tools/process_source.py` |
| ask / search / answer | "물어봐줘", "검색해줘", "무슨 변경?", "source 보여줘" | `ffxiv-ask-kb` | `python tools/ask.py --format json` |
| refresh / rebuild / regenerate | "KB 최신화", "graph 다시 빌드", "wiki 재생성", "FTS 재색인" | `ffxiv-kb-refresh` | v08.5 refresh sequence |
| Notion status | "Notion 상태 갱신", "처리 결과 기록", "Graph Status 반영" | `ffxiv-notion-status` | `notion_update` payload |
| latest info | "최신 정보 찾아줘" without a supplied source | unsupported-latest-info | ask for a source |

## Priority

1. If the user provides a source and asks to save/ingest/index it, use
   `ffxiv-source-processing`.
2. If the user asks a KB question, use `ffxiv-ask-kb`.
3. If the user explicitly asks to rebuild or refresh the KB, use
   `ffxiv-kb-refresh`.
4. If the user asks to update Notion status from a completed result, use
   `ffxiv-notion-status`.
5. If the user asks for latest info without a source, ask for a source or
   explicit browsing scope. Do not crawl silently.

## Global Boundaries

- Do not call crawler, scheduler, Discord slash command, LLM API, vector DB, or
  external graph DB workflows from this router.
- Do not upload source body, raw HTML, attachments, SQLite dumps, or graph JSON
  to Notion.
- Prefer one specific skill per user request. If a request needs mutation then
  reporting, finish the mutation first, parse JSON, then report.
