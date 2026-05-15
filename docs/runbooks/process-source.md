# Process Source Runbook

`tools/process_source.py` is the v0.5 repo execution entrypoint for OpenClaw source processing.

Current implementation status:

- v05-03: validation, dry-run, and JSON stdout contract are implemented.
- v05-04: local text sources are connected to Local Storage ingest.
- v05-05 URL fetch is not implemented.
- v05-06 rebuild execution is not implemented in `process_source.py`.
- v05-07 Notion success payload generation is not implemented.

## Local Source Apply

Supported local source types in v05-04:

```text
text_note
markdown_file
plain_text_file
```

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

## Output Contract

Successful v05-04 local ingest returns JSON with:

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
  "wiki_path": null,
  "graph_status": "skipped",
  "actions": [
    {"name": "validate_request", "status": "ok"},
    {"name": "ingest_local", "status": "ok", "source_id": "local_..."},
    {"name": "rebuild", "status": "skipped", "reason": "v05-06_not_implemented"}
  ],
  "notion_update": {},
  "summary": {
    "message": "Local source ingested. Rebuild is intentionally skipped in v0.5-04.",
    "next_action": "Run the v0.5-06 rebuild integration goal."
  }
}
```

Ingest failure returns:

```json
{
  "status": "error",
  "graph_status": "skipped",
  "actions": [
    {"name": "validate_request", "status": "ok"},
    {"name": "ingest_local", "status": "error", "error": "..."},
    {"name": "rebuild", "status": "skipped", "reason": "upstream_ingest_error"}
  ]
}
```

## Storage Behavior

`process_source.py` delegates storage rules to `tools.ingest_local.ingest_source()`.

The v05-04 canonical Local Storage path for local text sources is:

```text
{storage_root}/sources/{category}/{title_slug}.md
```

`plain_text_file` input is stored in the same `.md` canonical path shape as `text_note` and `markdown_file`. The text body is not wrapped or reformatted in v05-04.

Raw snapshots are created under:

```text
raw/local_storage/{category}/{title_slug}__{source_id}.md
```

## Validation

Focused tests:

```bash
python -m unittest tests.test_v05_process_source -v
```

Full suite:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Finish gate:

```bash
python scripts/finish_task.py
```
