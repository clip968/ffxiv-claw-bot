# Process Source Runbook

`tools/process_source.py` is the v0.5 repo execution entrypoint for OpenClaw source processing.

Completed v0.5 workflow:

```text
request
-> process_source.py
-> local ingest
-> wiki/FTS/graph rebuild
-> Notion update payload generation
-> OpenClaw applies the Notion update outside this tool
```

Implemented slices:

- v05-03: validation, dry-run, and JSON stdout contract.
- v05-04: `text_note`, `markdown_file`, and `plain_text_file` Local Storage ingest.
- v05-05: exactly one user-provided URL fetch and ingest.
- v05-06: wiki/FTS/graph rebuild via `tools.local_rebuild.rebuild_after_ingest()`.
- v05-07: safe `notion_update` payload via `tools.status_notification.build_notion_status_update()`.

Out of scope:

- No crawler, sitemap traversal, recursive URL discovery, or search-engine lookup.
- No scheduler, daemon, queue polling, or Notion polling.
- No direct Notion API call. OpenClaw consumes `notion_update` and performs any Notion write separately.
- No raw body, raw HTML, attachment bytes, or binary data in `notion_update`.

## Local Source Apply

Text note:

```bash
python tools/process_source.py \
  --apply \
  --source-type text_note \
  --category personal_notes \
  --title "Raid mitigation note" \
  --body "Use Reprisal before the tank buster." \
  --storage-root /mnt/d/ffixiv-bot-storage \
  --db-path db/ffxiv.sqlite
```

Markdown file:

```bash
python tools/process_source.py \
  --apply \
  --source-type markdown_file \
  --category raid_guides \
  --title "Tower Guide" \
  --local-path /mnt/d/ffixiv-bot-storage/incoming/tower-guide.md \
  --storage-root /mnt/d/ffixiv-bot-storage \
  --db-path db/ffxiv.sqlite
```

Plain text file:

```bash
python tools/process_source.py \
  --apply \
  --source-type plain_text_file \
  --category macros \
  --title "Spread Stack Macro" \
  --local-path /mnt/d/ffixiv-bot-storage/incoming/spread-stack.txt \
  --storage-root /mnt/d/ffixiv-bot-storage \
  --db-path db/ffxiv.sqlite
```

`--storage-root` must already exist. Missing storage roots fail with `status=error` and `graph_status=skipped`.

## URL Source Apply

```bash
python tools/process_source.py \
  --apply \
  --source-type url \
  --category patch_notes \
  --url "https://example.com/ffxiv/patch-note" \
  --storage-root /mnt/d/ffixiv-bot-storage \
  --db-path db/ffxiv.sqlite
```

Optional title override:

```bash
python tools/process_source.py \
  --apply \
  --source-type url \
  --category patch_notes \
  --title "Maintainer Provided Patch Title" \
  --url "https://example.com/ffxiv/patch-note"
```

URL behavior:

- `tools.fetch_url.fetch_single_url()` fetches exactly the provided URL.
- `text/html` is converted to visible text and title.
- v05.1 adds `tools.extractors.lodestone.extract_lodestone_article()` for Lodestone article extraction; `fetch_url.py` routing to this extractor is the next hardening slice.
- `text/plain`, `application/json`, and `+json` content are stored as text.
- Unsupported content types fail before Local Storage ingest.
- The fetched body is passed to `tools.ingest_local.ingest_source(source_type="url", ...)`.

## Dry Run

```bash
python tools/process_source.py \
  --dry-run \
  --source-type text_note \
  --category personal_notes \
  --title "Dry run note" \
  --body "This should not be persisted."
```

Dry-run returns `status=skipped`, plans validation/ingest/rebuild actions, and does not write files or DB rows.

## Output Contract

Successful apply returns JSON like:

```json
{
  "status": "ok",
  "dry_run": false,
  "source_id": "local_...",
  "source_type": "text_note",
  "category": "personal_notes",
  "title": "Raid mitigation note",
  "canonical_path": "sources/personal_notes/raid_mitigation_note.md",
  "local_source_path": "sources/personal_notes/raid_mitigation_note.md",
  "raw_path": "raw/local_storage/personal_notes/raid_mitigation_note__local_....md",
  "content_hash": "sha256...",
  "wiki_path": "wiki/source_summaries/local_....md",
  "graph_status": "built",
  "actions": [
    {"name": "validate_request", "status": "ok"},
    {"name": "ingest_local", "status": "ok", "source_id": "local_..."},
    {"name": "compile_wiki", "status": "ok"},
    {"name": "index_fts", "status": "ok"},
    {"name": "build_graph", "status": "ok"},
    {"name": "build_notion_payload", "status": "ok"}
  ],
  "notion_update": {
    "Status": "Graph Built",
    "Graph Status": "Built",
    "Source ID": "local_...",
    "Local Source Path": "sources/personal_notes/raid_mitigation_note.md",
    "Wiki Path": "wiki/source_summaries/local_....md",
    "Last Processed": "2026-05-16T00:00:00+00:00",
    "Last Error": "",
    "Next Action": ""
  }
}
```

Partial rebuild failure returns `status=partial`, keeps the saved source metadata, records the failed rebuild action, and still builds a metadata-only `notion_update` payload. If graph build fails, `graph_status=failed`; if graph is not attempted, `graph_status=pending`.

Fetch or ingest failure returns `status=error`, `graph_status=skipped`, and skips downstream rebuild.

## Duplicate Policy

`process_source.py` uses the Local Storage canonical source policy from `ingest_local.py`.

For local source types, the canonical path is derived from `category`, normalized `title`, and source extension. That canonical path determines the `local_source_id`. Running the same source again with new body content reuses the same `source_id`, updates the Local Storage file, overwrites the raw snapshot, updates the `sources` row, and then rebuilds wiki/FTS/graph from the latest content.

Duplicate canonical sources are not returned as `status=skipped` in v0.5. A successful reprocess returns `status=ok` or `status=partial` with the existing `source_id`.

## OpenClaw Sequence

1. Resolve source type, category, title, body/path/URL using `docs/skills/ffxiv-source-processing.md`.
2. Run `python tools/process_source.py` with either `--dry-run` or `--apply`.
3. Parse stdout JSON.
4. If `notion_update` is present, apply that payload through OpenClaw's Notion control layer.
5. Do not upload source body, raw HTML, attachments, or binary data to Notion.

## Troubleshooting

- `status=error` with validation action: fix the missing or invalid CLI argument.
- `ingest_local=error`: check storage root existence and SQLite DB initialization.
- `compile_wiki=error` or `index_fts=skipped`: check `sources.raw_path`, wiki tables, and raw snapshot existence.
- `build_graph=error`: check graph tables and rerun after wiki/FTS succeeds.
- `build_notion_payload=error`: inspect `last_error`; source ingest/rebuild status remains authoritative.

## Validation

Focused tests:

```bash
python -m unittest tests.test_v05_fetch_url -v
python -m unittest tests.test_v05_process_source -v
python -m unittest tests.test_v04_status_notification -v
```

Full suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Docs freshness:

```bash
python scripts/check_docs_freshness.py --all
```

Finish gate:

```bash
python scripts/finish_task.py
```
