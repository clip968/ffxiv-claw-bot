# SPEC 0010 - OpenClaw Use-Case Skill Routing

## Status

Active

## Purpose

OpenClaw must route common user requests to predictable repo entrypoints. This
spec fixes the skill set and the routing contract so natural-language requests
do not drift into ad hoc tool calls.

## Scope

In scope:

- Source ingest/index requests
- KB ask/search requests
- KB graph/wiki/FTS refresh requests
- Notion status payload/update requests
- Unsupported latest-info requests without a provided source

Out of scope:

- Scheduler/daemon behavior
- Crawling or sitemap traversal
- Discord slash command runtime
- LLM API generation
- Vector DB or external graph DB
- BIS/raid/item namespace expansion

## Source of Truth

OpenClaw skill contracts live in `docs/skills/`.

Machine-readable routing lives in:

- `docs/skills/openclaw-usecase-routing.json`

The JSON manifest is an index for routing. The Markdown skill documents remain
the detailed contract.

## Skill Set

### ffxiv-openclaw-router

Routes a request to one of the specific skills. If a request maps to more than
one skill, route to the first destructive or state-mutating action and then run
read-only follow-up skills after the mutation succeeds.

### ffxiv-source-processing

Handles save/ingest/index requests for provided sources. It must call:

```bash
python tools/process_source.py
```

It must not call `tools/ingest_local.py` directly for normal OpenClaw requests.

### ffxiv-ask-kb

Handles KB question/search/explanation requests. It must call:

```bash
python tools/ask.py "<question>" --format json
```

It must not answer from memory when the KB is the requested source.

### ffxiv-kb-refresh

Handles explicit KB refresh/rebuild/regenerate requests. It follows the v08.5
refresh sequence:

```text
rebuild_domain_graph dry-run
-> rebuild_domain_graph reset rebuild
-> generate_graph_report
-> generate_derived_wiki dry-run
-> generate_derived_wiki apply
-> FTS re-index
-> ask smoke
-> regression gate
```

Generated graph/wiki outputs remain local derived state and must not be
committed unless a later spec changes that policy.

### ffxiv-notion-status

Handles Notion status updates from result JSON or `notion_update` payloads.
It must not upload source body, raw HTML, attachments, binary data, SQLite
records, or graph JSON to Notion.

## Routing Requirements

- REQ-0010-001: Source save/ingest/index requests route to `ffxiv-source-processing`.
- REQ-0010-002: KB question/search/explain requests route to `ffxiv-ask-kb`.
- REQ-0010-003: KB refresh/rebuild/regenerate requests route to `ffxiv-kb-refresh`.
- REQ-0010-004: Notion status update requests route to `ffxiv-notion-status`.
- REQ-0010-005: Requests for latest information without a supplied source must ask for a source or explicit browsing scope. They must not silently crawl.
- REQ-0010-006: Skills must name their allowed entrypoint and forbidden tool calls.
- REQ-0010-007: Skills must define how to parse output and report result shape.
- REQ-0010-008: Notion skills must forbid `body`, `attachments`, `raw_html`, and equivalent raw source fields.

## Acceptance Criteria

- AC-0010-001: `docs/skills/ffxiv-openclaw-router.md` maps the supported use cases to named skills.
- AC-0010-002: `docs/skills/ffxiv-ask-kb.md` requires `tools/ask.py --format json`.
- AC-0010-003: `docs/skills/ffxiv-kb-refresh.md` defines the full v08.5 refresh sequence.
- AC-0010-004: `docs/skills/ffxiv-notion-status.md` defines safe Notion payload handling.
- AC-0010-005: `docs/skills/ffxiv-source-processing.md` preserves `process_source.py` as the normal entrypoint.
- AC-0010-006: `docs/skills/openclaw-usecase-routing.json` indexes all supported routes.
- AC-0010-007: `tests/test_openclaw_skills.py` validates the skill set and routing manifest.

## Verification

```bash
python -m unittest tests.test_openclaw_skills -v
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```
