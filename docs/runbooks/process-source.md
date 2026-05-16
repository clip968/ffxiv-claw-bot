# Process Source Runbook

`tools/process_source.py` is the v0.5 official source processing entrypoint for normal OpenClaw source processing.

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
- v05.1-04: Lodestone HTML URLs route through the Lodestone article extractor before generic HTML extraction.
- v05.1-05: URL fetch actions include extractor metadata when `fetch_single_url()` returns it.
- v06-06: local file sources route through the v0.6 extractor registry before Local Storage ingest.
- v06-07: `tools/process_pending_sources.py` processes queued pending sources through `process_source.py`.

Out of scope:

- No crawler, sitemap traversal, recursive URL discovery, or search-engine lookup.
- No scheduler, daemon, queue polling, or Notion polling.
- No direct Notion API call. OpenClaw consumes `notion_update` and performs any Notion write separately.
- No raw body, raw HTML, attachment bytes, or binary data in `notion_update`.

## Entrypoint Boundary

Normal user/OpenClaw source processing must start with `tools/process_source.py`.

Allowed normal commands:

```bash
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "..." --body "..."
python tools/process_source.py --apply --source-type markdown_file --category patch_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/patch-7-5.md"
python tools/process_source.py --apply --source-type plain_text_file --category personal_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/note.txt"
python tools/process_source.py --apply --source-type binary_attachment --category bis_sheets --local-path "/mnt/d/ffixiv-bot-storage/incoming/bis.xlsx"
python tools/process_source.py --apply --source-type url --category patch_notes --url "https://na.finalfantasyxiv.com/lodestone/..."
```

`markdown_file`, `plain_text_file`, and `binary_attachment` processing must use `process_source.py --local-path`. Do not read the file path into a helper command by hand.

Bad normal-workflow example:

```bash
python tools/ingest_local.py \
  --apply \
  --source-type markdown_file \
  --category patch_notes \
  --title "Patch 7.5 Notes" \
  --body "/mnt/d/ffixiv-bot-storage/incoming/patch-7-5.md"
```

This stores the path string itself, not the file contents. `ingest_local.py --body` expects already-read body text.

Helper boundaries:

- `tools/ingest_local.py` is a low-level helper and not the OpenClaw-facing source processing interface.
- `tools/local_rebuild.py` is library-only for normal workflow. Do not run `python tools/local_rebuild.py` expecting source rebuild execution; normal rebuild is performed through `tools/process_source.py`, which calls `local_rebuild.rebuild_after_ingest()` internally.
- `tools/status_notification.py` is payload-builder-only for normal workflow. It builds metadata payloads through `status_notification.build_notion_status_update()` and is not a Notion write CLI.

Notion boundary:

- `process_source.py` returns `result["notion_update"]` as a payload only.
- `process_source.py itself does not call the Notion API`.
- If `result["notion_update"]` is present, OpenClaw may apply it to the Notion control/status database.
- A generated `notion_update` payload is not already applied to Notion DB state.

## Pending Source Loop

`tools/process_pending_sources.py` is the v0.6 orchestration layer for queued source rows. It repeatedly calls `tools/process_source.py` for one source at a time; it does not duplicate extractor, ingest, rebuild, or Notion payload logic.

Queue table:

```text
source_processing_queue
```

Required queue fields:

- `id`
- `source_type`
- `category`
- `title`
- one input field: `body`, `local_path`, or `url`
- `status`
- `retry_count`

Normal commands:

```bash
python tools/process_pending_sources.py --dry-run --limit 3
python tools/process_pending_sources.py --limit 10
python tools/process_pending_sources.py --source-type local_file --limit 10
python tools/process_pending_sources.py --retry-errors --max-retry 3 --limit 10
```

Status behavior:

- `--dry-run` returns planned targets and does not create or mutate queue rows.
- Normal processing selects `status=pending` rows.
- `--retry-errors` also selects `status=error` rows with `retry_count < max_retry`.
- Each selected row is marked `in_progress` before calling `process_source.py`.
- `process_source.py` `status=ok` marks the queue row `processed`.
- Any non-ok result marks the queue row `error`, stores `error_stage` and `error_message`, and increments `retry_count`.
- `--source-type local_file` filters to `markdown_file`, `plain_text_file`, and `binary_attachment`.

The queue loop is not a scheduler, daemon, watcher, crawler, or Notion polling tool.

## Job Wiki Generation

`tools/generate_job_wiki.py` is the v0.6 deterministic job wiki generator. It reads `wiki/source_summaries/*.md`, finds job-related lines/sections through the v0.6 job catalog aliases, sorts entries by patch version, deduplicates identical entry text, and writes `wiki/jobs/<job>.md`.

Commands:

```bash
python tools/generate_job_wiki.py --job gunbreaker --dry-run
python tools/generate_job_wiki.py --job gunbreaker
python tools/generate_job_wiki.py --job gunbreaker --patch-range 7.0..7.5
python tools/generate_job_wiki.py --all
python tools/generate_derived_wiki.py --kind jobs --job gunbreaker --dry-run
python tools/generate_derived_wiki.py --kind jobs --patch-range 7.0..7.5
```

Options:

- `--summary-root`: source summary input root, default `wiki/source_summaries`
- `--target-root`: generated job wiki root, default `wiki/jobs`
- `--include-limited`: include limited jobs such as Blue Mage when using `--all`
- `--dry-run`: return JSON actions and generated paths without writing files

The generator is evidence-preserving: generated job wiki entries include patch version sections and `source_id` lines. It does not call an LLM and does not invent summaries beyond matched source summary text.

`tools/generate_derived_wiki.py` is the v0.6 unified derived wiki entrypoint. In v0.6, only `--kind jobs` is supported. `raids`, `items`, and `systems` return an unsupported-kind error until a later spec implements them.

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

Binary/table file:

```bash
python tools/process_source.py \
  --apply \
  --source-type binary_attachment \
  --category bis_sheets \
  --title "BiS Sheet" \
  --local-path /mnt/d/ffixiv-bot-storage/incoming/bis.xlsx \
  --storage-root /mnt/d/ffixiv-bot-storage \
  --db-path db/ffxiv.sqlite
```

`--storage-root` must already exist. Missing storage roots fail with `status=error` and `graph_status=skipped`.

Local file extraction behavior:

- `text_note` still passes `--body` directly to Local Storage and does not run an extractor.
- `markdown_file`, `plain_text_file`, and `binary_attachment` call `src.source_processing.extract_source_text(path)` before ingest.
- Supported extensions are `.txt`, `.md`, `.html`, `.htm`, `.csv`, and `.xlsx`.
- The extracted normalized text is passed to `tools.ingest_local.ingest_source()`.
- `extract_metadata` is preserved in the result JSON for diagnostics and downstream pending-source handling.
- Extractor metadata is not copied into `notion_update`.
- `binary_attachment` output is stored as normalized `.md` text in Local Storage and raw snapshots.

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
- `text/html` Lodestone URLs are extracted with `tools.extractors.lodestone.extract_lodestone_article()` and return `extractor=lodestone`.
- `text/html` non-Lodestone URLs use generic visible text extraction and return `extractor=generic_html`.
- `text/plain`, `application/json`, and `+json` content are stored as text.
- `text/plain` returns `extractor=text`; `application/json` and `+json` return `extractor=json`.
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
  "source_type": "url",
  "category": "patch_notes",
  "title": "Patch 7.5 Notes",
  "canonical_path": "sources/patch_notes/patch_7.5_notes.md",
  "local_source_path": "sources/patch_notes/patch_7.5_notes.md",
  "raw_path": "raw/local_storage/patch_notes/patch_7.5_notes__local_....md",
  "content_hash": "sha256...",
  "wiki_path": "wiki/source_summaries/local_....md",
  "graph_status": "built",
  "actions": [
    {"name": "validate_request", "status": "ok"},
    {
      "name": "fetch_url",
      "status": "ok",
      "url": "https://na.finalfantasyxiv.com/lodestone/...",
      "content_type": "text/html; charset=utf-8",
      "extractor": "lodestone"
    },
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
    "Local Source Path": "sources/patch_notes/patch_7.5_notes.md",
    "Wiki Path": "wiki/source_summaries/local_....md",
    "Last Processed": "2026-05-16T00:00:00+00:00",
    "Last Error": "",
    "Next Action": ""
  }
}
```

Partial rebuild failure returns `status=partial`, keeps the saved source metadata, records the failed rebuild action, and still builds a metadata-only `notion_update` payload. If graph build fails, `graph_status=failed`; if graph is not attempted, `graph_status=pending`.

Fetch or ingest failure returns `status=error`, `graph_status=skipped`, and skips downstream rebuild.

Local extractor failure returns `status=error`, `error_stage=extract`, `graph_status=skipped`, and skips Local Storage ingest plus rebuild. Examples:

```json
{
  "status": "error",
  "error_stage": "extract",
  "graph_status": "skipped",
  "last_error": "Unsupported source extension: .png",
  "actions": [
    {"name": "validate_request", "status": "ok"},
    {"name": "extract", "status": "error", "error_stage": "extract"},
    {"name": "ingest_local", "status": "skipped", "reason": "upstream_extract_error"},
    {"name": "rebuild", "status": "skipped", "reason": "upstream_extract_error"}
  ]
}
```

Successful local file extraction adds an `extract` action before `ingest_local`:

```json
{
  "extract_metadata": {
    "extractor_name": "xlsx",
    "sheet_count": 3
  },
  "actions": [
    {"name": "validate_request", "status": "ok"},
    {"name": "extract", "status": "ok", "extractor": "xlsx"},
    {"name": "ingest_local", "status": "ok"}
  ]
}
```

## Duplicate Policy

`process_source.py` uses the Local Storage canonical source policy from `ingest_local.py`.

For local source types, the canonical path is derived from `category`, normalized `title`, and stored source extension. That canonical path determines the `local_source_id`. Running the same source again with new body content reuses the same `source_id`, updates the Local Storage file, overwrites the raw snapshot, updates the `sources` row, and then rebuilds wiki/FTS/graph from the latest content.

In v06-06, file-source input extensions do not necessarily become stored extensions. `binary_attachment` inputs such as `.xlsx` and `.csv` are extracted to normalized text and stored as `.md`.

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
python -m unittest tests.test_v05_1_lodestone_extractor -v
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
