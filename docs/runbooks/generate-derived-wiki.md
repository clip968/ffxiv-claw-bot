# Generate Derived Wiki Runbook

v0.6 derived wiki generation turns source summaries into topic-level Markdown pages. In v0.6, only FFXIV job pages are implemented.

Inputs:

```text
wiki/source_summaries/*.md
```

Outputs:

```text
wiki/jobs/<job>.md
```

The generator is deterministic and evidence-preserving. It does not call an LLM and does not invent summaries beyond matching source summary text.

## Job Wiki CLI

Generate one job page:

```bash
python tools/generate_job_wiki.py --job gunbreaker
```

Dry-run one job:

```bash
python tools/generate_job_wiki.py --job gunbreaker --dry-run
```

Generate every non-limited combat job page:

```bash
python tools/generate_job_wiki.py --all
```

Include limited jobs such as Blue Mage:

```bash
python tools/generate_job_wiki.py --all --include-limited
```

Filter by patch range:

```bash
python tools/generate_job_wiki.py --job gunbreaker --patch-range 7.0..7.5
```

Use custom roots:

```bash
python tools/generate_job_wiki.py --job gunbreaker --summary-root wiki/source_summaries --target-root wiki/jobs
```

## Unified CLI

`tools/generate_derived_wiki.py` is the v0.6 wrapper for derived wiki kinds.

Supported in v0.6:

```bash
python tools/generate_derived_wiki.py --kind jobs
python tools/generate_derived_wiki.py --kind jobs --job gunbreaker --dry-run
python tools/generate_derived_wiki.py --kind jobs --patch-range 7.0..7.5
```

Reserved for later specs:

- `--kind raids`
- `--kind items`
- `--kind systems`

Those kinds currently fail with an unsupported-kind error.

## FTS Indexing

`tools.compile_wiki.index_wiki_documents()` indexes both source summaries and generated job pages into `wiki_pages` and `wiki_fts`.

Indexed document types:

- `wiki/source_summaries/*.md` -> `wiki_type=source_summary`
- `wiki/jobs/*.md` -> `wiki_type=job`, `topic=<job-slug>`

Run the indexing helper from Python:

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

## Source Processing Hook

Derived wiki generation can run after source processing only when explicitly requested:

```bash
python tools/process_source.py --apply --source-type text_note --category patch_notes --title "Patch note" --body "..." --build-derived-wiki
python tools/process_pending_sources.py --build-derived-wiki --limit 10
```

Default source processing skips derived wiki generation.

Failure policy:

- source result not `status=ok`: derived wiki hook is skipped
- derived wiki generator failure: source remains successful, and `derived_wiki.error_stage=derived_wiki_generate`

## Troubleshooting

No job page generated:

- Confirm the source summaries mention the job by English name, abbreviation, or supported Korean alias.
- Run with `--dry-run` and inspect `summary.generated`.
- Confirm `--include-limited` when generating Blue Mage.

Unsupported kind:

```text
Derived wiki kind 'raids' is not supported in v0.6.
```

Stale search results:

- Generate the wiki page again.
- Re-run `index_wiki_documents()`.

## Verification

```bash
python -m unittest tests.test_v06_job_wiki_generator -v
python -m unittest tests.test_v06_fts_indexing -v
python scripts/check_docs_freshness.py --all
```
