# v09 Task 00 Baseline Report

Date: 2026-05-17

Scope: baseline inspection and guardrails for `SPEC 0011 / v09 - guide.ff14.co.kr Official DB Crawler`.

## Files Inspected

- `README.md`
- `CLAUDE.md`
- `docs/README.md`
- `docs/WORKFLOW.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`
- `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md`
- `docs/DOC_OWNERS.yml`
- `.gitignore`
- `tools/init_db.py`
- `tools/compile_wiki.py`
- `tools/generate_derived_wiki.py`
- `tools/generate_graph_report.py`
- `tools/ask.py`
- `src/wiki_indexing/wiki_document_scanner.py`
- `src/domain_graph/storage.py`
- `src/domain_graph/report.py`
- existing `tests/test_*.py` modules and `tests/fixtures/`

## Current Patterns

- DB schema/init style: `tools/init_db.py` owns the canonical root schema with `CREATE TABLE IF NOT EXISTS`; domain-specific helpers such as `src/domain_graph/storage.py` also expose idempotent `ensure_*_schema(conn)` helpers.
- Storage/upsert style: SQLite with explicit SQL, deterministic JSON via `json.dumps(..., ensure_ascii=False, sort_keys=True)` where stable serialization matters, and no ORM dependency.
- Wiki indexing style: `tools/compile_wiki.py:index_wiki_documents()` scans generated wiki directories through `src/wiki_indexing`, upserts `wiki_pages`, then refreshes `wiki_fts`.
- Generated wiki policy: generated source summary/job/patch/skill pages are ignored. v09 item wiki output should follow that policy and remain uncommitted generated output.
- Graph/report style: `src/domain_graph/storage.py` upserts generic `graph_nodes` and `graph_edges`; `tools/generate_graph_report.py` emits JSON and writes `graph/GRAPH_REPORT.md`.
- Ask/retrieval style: `tools/ask.py` parses the query, runs graph-aware retrieval, applies result policy, builds context, composes a grounded answer, and emits JSON by default.
- Test style: standard `unittest`, temp SQLite DBs, local fixtures under `tests/fixtures/`, and no network dependency in unit tests.
- Finish workflow: final gates are `git diff --check`, focused unittest, `python scripts/check_docs_freshness.py --all`, and `python scripts/finish_task.py`.

## Guardrail Changes

- Added `.gitignore` entries for `data/raw/guide_ff14/` and `wiki/items/` because v09 raw snapshots and item derived wiki pages are generated artifacts.

## Deviations To Respect

- `docs/DOC_OWNERS.yml` currently has no v09-specific rule; Task 01 or the first code task must add one before new `src/guide_ff14/**`, `tools/crawl_guide_ff14.py`, item wiki, graph, or retrieval tests are committed.
- `tools/generate_derived_wiki.py` already treats `items` as a known future kind; v09 should implement independent `tools/generate_item_wiki.py` first and avoid adding a unified hook until item generation is stable.
- The live network smoke for guide.ff14.co.kr remains runbook-only and maintainer-approved. Task tests must use fakes or fixtures.
