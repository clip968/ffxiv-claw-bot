# Process Pending Sources Runbook

`tools/process_pending_sources.py` is the v0.6 queue runner for source rows stored in `source_processing_queue`.

It calls `tools/process_source.py` for each selected row. It does not duplicate extractor, ingest, rebuild, or Notion payload behavior.

## Queue Contract

Required table:

```text
source_processing_queue
```

Required fields for each row:

- `id`
- `source_type`
- `category`
- `title`
- one input field: `body`, `local_path`, or `url`
- `status`
- `retry_count`

Supported `source_type` values match `process_source.py`:

- `text_note`
- `markdown_file`
- `plain_text_file`
- `binary_attachment`
- `url`

## Commands

Preview selected rows without mutation:

```bash
python tools/process_pending_sources.py --dry-run --limit 10
```

Process pending rows:

```bash
python tools/process_pending_sources.py --limit 10
```

Retry failed rows below the retry limit:

```bash
python tools/process_pending_sources.py --retry-errors --max-retry 3 --limit 10
```

Process only local file rows:

```bash
python tools/process_pending_sources.py --source-type local_file --limit 10
```

Process rows and opt into derived job wiki generation after successful source processing:

```bash
python tools/process_pending_sources.py --build-derived-wiki --limit 10
```

Use explicit storage or DB paths:

```bash
python tools/process_pending_sources.py --limit 10 --storage-root /mnt/d/ffixiv-bot-storage --db-path db/ffxiv.sqlite
```

## Status Transitions

Normal success:

```text
pending -> in_progress -> processed
```

Derived wiki success when `--build-derived-wiki` is set:

```text
pending -> in_progress -> derived_wiki_built
```

Source processing failure:

```text
pending -> in_progress -> error
```

Retryable failure with `--retry-errors --max-retry N`:

```text
error retry_count < N -> in_progress -> processed/error
```

The queue runner stores `result_json` from `process_source.py`. For source failures, it increments `retry_count` and stores `error_stage` plus `error_message`.

## Derived Wiki Hook

`--build-derived-wiki` appends `--build-derived-wiki` to each `process_source.py` invocation.

Expected result cases:

- success: queue row `status=derived_wiki_built`; generated `wiki/jobs/*.md` pages are indexed into `wiki_fts`
- derived wiki failure: queue row remains `status=processed`, with `error_stage=derived_wiki_generate`
- derived wiki generated but FTS indexing failed: source processing remains successful, `result_json.derived_wiki.status=partial`, and `result_json.derived_wiki.fts_index.error_stage=derived_wiki_fts_index`
- source processing partial/error: derived wiki hook is skipped because the source result is not `status=ok`

The hook is opt-in. Without `--build-derived-wiki`, no `wiki/jobs/*.md` files are generated.

## Troubleshooting

Unsupported extension:

```text
status=error
error_stage=extract
error_message=Unsupported source extension: .png
```

Missing input field:

```text
status=error
error_stage=process_pending
```

Derived wiki generation failure:

```text
status=processed
error_stage=derived_wiki_generate
```

Derived wiki FTS indexing failure:

```text
result_json.derived_wiki.status=partial
result_json.derived_wiki.fts_index.error_stage=derived_wiki_fts_index
```

Queue rows do not have a dedicated `derived_wiki_status` column in v06.1. If operators need clearer queue filtering than `result_json`, add that schema change in a later hardening task.

If no rows are selected, the command returns `status=skipped`, `summary.targeted=0`.

## Verification

```bash
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v05_process_source -v
python scripts/check_docs_freshness.py --all
```
