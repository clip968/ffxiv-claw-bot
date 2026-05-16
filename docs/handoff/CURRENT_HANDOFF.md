# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.4 implementation is complete. All five v04 feature plans are Implemented.

v0.5 planning is complete. The v05 Source Processing Pipeline spec and all 8 task plans are documented.
v05.1 Source Processing Hardening is complete. v05.1-02 through v05.1-08 are implemented.
v0.6 Multi-format Source Processing and Derived Wiki Generation is complete. v06-01 through v06-14 are implemented and documented. v06.1 derived wiki FTS hardening is complete in the current session.

v0.5-02 through v0.5-08 are implemented:

- `docs/skills/ffxiv-source-processing.md` documents the OpenClaw Source Processing Skill contract.
- `tools/process_source.py` exists with CLI parsing, validation, dry-run behavior, and JSON stdout contract.
- `process_source.py --apply` now ingests `text_note`, `markdown_file`, and `plain_text_file` through Local Storage via `tools.ingest_local.ingest_source()`.
- `process_source.py --apply --source-type url` now fetches exactly one user-provided URL via `tools.fetch_url.fetch_single_url()` and ingests the fetched body through Local Storage.
- Rebuild execution and Notion success payload generation are implemented. `process_source.py --apply` now runs ingest -> wiki/FTS/graph rebuild -> safe `notion_update` payload generation.

v0.4 planning has been reframed from Google Drive write/publish to Local Storage + OpenClaw Notion direct control.

The v05 phase transitions from multi-tool manual wiring to a unified `process_source.py` entrypoint that takes a single source through ingest -> rebuild -> status payload in one call. The current implementation supports validation, dry-run, apply-mode Local Storage ingest for local text source types, single URL fetch into Local Storage, wiki/FTS/graph rebuild, and metadata-only Notion payload generation.

v05.1 adds a deterministic Lodestone article extractor for `.news__detail__wrapper`, routes Lodestone HTML URLs through that extractor in `fetch_url.py`, records extractor metadata in the `process_source.py` `fetch_url` action, and locks the official `process_source.py` entrypoint/helper/Notion payload boundaries through runbook regression tests.

Default source of truth for user-managed source files:

```text
/mnt/d/ffixiv-bot-storage
```

Documentation source of truth:

```text
repo docs/
```

Notion is not file storage. Notion is the OpenClaw control/status/index layer and should store local path, category, source_id, processing status, wiki path, graph status, last error, and next action only.

Google Drive sync/write remains implemented but is Legacy / Deferred / Optional Integration.

## Read First Next Session

1. `docs/WORKFLOW.md`
2. `docs/handoff/CURRENT_HANDOFF.md`
3. `docs/PROJECT_PROFILE.md`
4. `docs/FILE_INVENTORY.md`
5. `docs/specs/0004-v05-source-processing-pipeline.md` (v05 spec — read first before any v05 work)
6. `docs/plans/v05/README.md` (v05 feature map)
7. `docs/specs/0004a-v05.1-source-processing-hardening.md`
8. `docs/plans/v05.1/README.md`
9. `docs/adrs/0006-local-storage-and-notion-control.md`
10. `docs/specs/0005- v06-Multi-format-Source-Processing.md`
11. `docs/plans/v06/README.md`
12. `docs/plans/v06/2026-05-16-v06-13-derived-wiki-hook.md`
13. `docs/runbooks/process-source.md`
14. `docs/runbooks/process-pending-sources.md`
15. `docs/runbooks/generate-derived-wiki.md`
16. `docs/plans/v06.1/2026-05-16-v06.1-derived-wiki-fts-hardening.md`
17. `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
18. `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
19. `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md`
20. `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md`
21. `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`
22. `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md`
23. `docs/plans/v04/2026-05-14-v04-05-status-notification.md`
24. `docs/runbooks/rebuild-kb.md`
25. `docs/runbooks/local-storage.md`
26. `docs/runbooks/openclaw-notion.md`
- `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`
- `docs/specs/0003-google-drive-sync.md`
- `docs/runbooks/sync-drive.md`
- `docs/runbooks/publish-drive.md`

## This Session

### Current session update: v07-04 intent detector implemented -- 2026-05-17

1. **Scope**
   - Implemented v07-04 only.
   - Added `src/query/intent_detector.py` with deterministic keyword-based `detect_intent()`.
   - Implemented only `job_change_history` and `generic_search`; no LLM call or extra intent expansion.

2. **Red tests first**
   - Added `V07IntentDetectorTests` in `tests/test_v07_query_parser.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v07_query_parser.V07IntentDetectorTests -v` failed because `detect_intent` was not importable from `src.query`.

3. **Verification**
   - `python -m unittest tests.test_v07_query_parser -v`: OK, 17 tests.
   - `python -m py_compile src/query/intent_detector.py src/query/__init__.py`: OK.

4. **Next tasks**
   - v07-05: integrate normalization, job detection, patch parsing, and intent detection in `parse_query()`.

### Current session update: v07-03 patch range parser implemented -- 2026-05-17

1. **Scope**
   - Implemented v07-03 only.
   - Added `src/query/patch_parser.py` with numeric patch parsing for single patches, `N.x` ranges, explicit `~`/`-`/`–` ranges, and Korean `부터...까지` ranges.
   - Did not implement expansion-name mapping or semantic patch range interpretation.

2. **Red tests first**
   - Added `V07PatchRangeParserTests` in `tests/test_v07_query_parser.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v07_query_parser.V07PatchRangeParserTests -v` failed because `parse_patch_range` was not importable from `src.query`.

3. **Verification**
   - `python -m unittest tests.test_v07_query_parser -v`: OK, 14 tests.
   - `python -m py_compile src/query/patch_parser.py src/query/__init__.py`: OK.

4. **Next tasks**
   - v07-04: add deterministic intent detection.

### Current session update: v07-02 job detector implemented -- 2026-05-17

1. **Scope**
   - Implemented v07-02 only.
   - Added `src/query/job_detector.py` with `detect_job()` using the existing v06 `JOB_CATALOG`.
   - Added Korean full alias, Korean short alias, English abbreviation, English display name, and no-match tests.
   - Did not implement patch parsing, intent detection, parser integration, retrieval, or answer composition.

2. **Red tests first**
   - Added `V07JobDetectorTests` in `tests/test_v07_query_parser.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v07_query_parser.V07JobDetectorTests -v` failed because `detect_job` was not importable from `src.query`.

3. **Verification**
   - `python -m unittest tests.test_v07_query_parser -v`: OK, 8 tests.
   - `python -m py_compile src/query/job_detector.py src/query/__init__.py`: OK.

4. **Next tasks**
   - v07-03: add numeric patch range parsing.

### Current session update: v07-01 query model and normalization implemented -- 2026-05-17

1. **Scope**
   - Implemented v07-01 only.
   - Added `src/query` package foundation with `ParsedQuery`, `normalize_query()`, and `extract_terms()`.
   - Did not implement job detection, patch parsing, intent detection, parser integration, retrieval, or answer composition.

2. **Red tests first**
   - Added `V07QueryModelTests` in `tests/test_v07_query_parser.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v07_query_parser -v` failed with `ModuleNotFoundError: No module named 'src.query'`.

3. **Verification**
   - `python -m unittest tests.test_v07_query_parser -v`: OK, 3 tests.
   - `python -m py_compile src/query/models.py src/query/normalize.py src/query/__init__.py`: OK.

4. **Next tasks**
   - v07-02: add job detection by reusing the v06 job catalog.

### Current session update: v06-01 extractor model and errors implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-01 only.
   - Added the `src.source_processing` package foundation with `ExtractedSource`, `SourceExtractionError`, `UnsupportedSourceExtensionError`, `SourceDecodingError`, and `SourceParseError`.
   - Did not implement extractor registry, actual extractors, pending loop, derived wiki generation, or FTS expansion.

2. **Red tests first**
   - Added `V06ExtractorModelTests` in `tests/test_v06_extractors.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_extractors -v` failed with 5 `ModuleNotFoundError: No module named 'src'` errors.

3. **Verification**
   - `python -m unittest tests.test_v06_extractors -v`: OK, 5 tests.
   - `python -m py_compile src/source_processing/models.py src/source_processing/errors.py src/source_processing/__init__.py src/__init__.py`: OK.

4. **Next tasks**
   - v06-02: extractor registry and stub mapping.

### Current session update: v06-02 extractor registry implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-02 only.
   - Added `src/source_processing/extractor_registry.py` with `EXTRACTORS`, `get_extractor_for_path()`, and `extract_source_text()`.
   - Added temporary stub extractor functions for `.txt`, `.md`, `.html`, `.htm`, `.csv`, and `.xlsx`; concrete extraction remains v06-03 through v06-05.

2. **Red tests first**
   - Added `V06ExtractorRegistryTests` in `tests/test_v06_extractors.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_extractors.V06ExtractorRegistryTests -v` failed with 8 registry module import errors.

3. **Verification**
   - `python -m unittest tests.test_v06_extractors -v`: OK, 13 tests.
   - `python -m py_compile src/source_processing/extractor_registry.py src/source_processing/extractors/__init__.py src/source_processing/__init__.py`: OK.

4. **Next tasks**
   - v06-03: replace `.txt`, `.md`, `.html`, and `.htm` stubs with concrete extractors.

### Current session update: v06-03 text/markdown/html extractors implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-03 only.
   - Added concrete `.txt`, `.md`, `.html`, and `.htm` extraction through `src/source_processing/extractors/text.py`, `markdown.py`, and `html.py`.
   - CSV and XLSX remain temporary stubs for v06-04 and v06-05.

2. **Red tests first**
   - Added source file fixtures under `tests/fixtures/source_files/`.
   - Added `V06TextMarkdownHtmlExtractorTests` in `tests/test_v06_extractors.py`.
   - Confirmed expected red failure: concrete extractor modules were missing and registry still returned empty stub text.

3. **Verification**
   - `python -m unittest tests.test_v06_extractors -v`: OK, 21 tests.
   - `python -m py_compile src/source_processing/extractors/text.py src/source_processing/extractors/markdown.py src/source_processing/extractors/html.py src/source_processing/extractors/__init__.py`: OK.
   - `python -m unittest tests.test_v05_1_lodestone_extractor -v`: OK, 5 tests.

4. **Next tasks**
   - v06-04: replace `.csv` stub with the concrete CSV extractor.

### Current session update: v06-04 CSV extractor implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-04 only.
   - Added `src/source_processing/extractors/csv.py`.
   - Replaced the `.csv` registry stub with the concrete extractor.
   - XLSX remains a temporary stub for v06-05.

2. **Red tests first**
   - Added `tests/fixtures/source_files/sample.csv`.
   - Added `V06CsvExtractorTests` in `tests/test_v06_extractors.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_extractors.V06CsvExtractorTests -v` failed with missing CSV module errors and registry stub content failure.

3. **Verification**
   - `python -m unittest tests.test_v06_extractors -v`: OK, 26 tests.
   - `python -m py_compile src/source_processing/extractors/csv.py src/source_processing/extractors/__init__.py`: OK.

4. **Next tasks**
   - v06-05: replace `.xlsx` stub with the concrete XLSX extractor.

### Current session update: v06-05 XLSX extractor implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-05 only.
   - Added `src/source_processing/extractors/xlsx.py`.
   - Replaced the `.xlsx` registry stub with the concrete extractor.
   - Did not add `openpyxl`; the current environment lacks it, so XLSX support uses Python standard library zip/XML parsing.

2. **Red tests first**
   - Added `V06XlsxExtractorTests` in `tests/test_v06_extractors.py`.
   - Tests generate a minimal temporary `.xlsx` workbook at runtime instead of committing a binary fixture.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_extractors.V06XlsxExtractorTests -v` failed with missing XLSX module errors and registry stub content failure.

3. **Verification**
   - `python -m unittest tests.test_v06_extractors -v`: OK, 32 tests.
   - `python -m py_compile src/source_processing/extractors/xlsx.py src/source_processing/extractors/__init__.py`: OK.

4. **Next tasks**
   - v06-06: integrate extractor registry into `tools/process_source.py` for local file sources.

### Current session update: v06-06 process_source extractor integration implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-06 only.
   - `tools/process_source.py` now routes `markdown_file`, `plain_text_file`, and `binary_attachment` local file sources through `src.source_processing.extract_source_text()`.
   - `text_note` still uses the direct `--body` path, and `url` still uses the existing v05.1 fetch/Lodestone route.
   - `binary_attachment` normalized output is stored as `.md` through `tools.ingest_local.ingest_source()`.

2. **Red tests first**
   - Added `V06ProcessSourceExtractorIntegrationTests` in `tests/test_v05_process_source.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v05_process_source.V06ProcessSourceExtractorIntegrationTests -v` failed because local file `extract` actions, `extract_metadata`, extract-stage errors, and `binary_attachment` apply support were missing.

3. **Verification**
   - `python -m unittest tests.test_v05_process_source.V06ProcessSourceExtractorIntegrationTests -v`: OK, 4 tests.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 31 tests.
   - `python -m unittest tests.test_v06_extractors -v`: OK, 32 tests.
   - `python -m unittest tests.test_v05_1_lodestone_extractor -v`: OK, 5 tests.
   - `python -m py_compile tools/process_source.py tools/ingest_local.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 172 tests.

4. **Next tasks**
   - v06-07: implement `tools/process_pending_sources.py` pending source loop.

### Current session update: v06-07 pending source loop implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-07 only.
   - Added `source_processing_queue` to `tools/init_db.py`.
   - Added `tools/process_pending_sources.py` with `--limit`, `--source-type`, `--dry-run`, `--retry-errors`, `--max-retry`, `--db-path`, and `--storage-root`.
   - The pending loop calls `tools.process_source.main()` for each selected queue row and does not duplicate extractor, ingest, rebuild, or Notion payload logic.

2. **Red tests first**
   - Added `V06PendingSourceLoopTests` in `tests/test_v06_pending_sources.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_pending_sources -v` failed with 6 missing-module failures because `tools.process_pending_sources` did not exist.

3. **Verification**
   - `python -m unittest tests.test_v06_pending_sources -v`: OK, 6 tests.
   - `python tools/process_pending_sources.py --dry-run --limit 3`: returned `status=skipped`, `targeted=0`.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 31 tests.
   - `python -m unittest tests.test_v06_extractors -v`: OK, 32 tests.
   - `python -m py_compile tools/process_pending_sources.py tools/init_db.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 178 tests.

4. **Next tasks**
   - v06-08: implement derived wiki foundation (`summary_loader`, `writer`, `templates`).

### Current session update: v06-08 derived wiki foundation implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-08 only.
   - Added `src/derived_wiki/summary_loader.py` with `SourceSummary` and filesystem-based `load_summaries()`.
   - Added `src/derived_wiki/writer.py` and `src/derived_wiki/templates.py`.
   - Added source summary fixtures for patch 7.0 and patch 7.1.
   - Did not implement job catalog, job wiki generation, CLI, FTS integration, or derived wiki hook.

2. **Red tests first**
   - Added `V06DerivedWikiFoundationTests` in `tests/test_v06_job_wiki_generator.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_job_wiki_generator -v` failed with 7 missing `src.derived_wiki` module errors.

3. **Verification**
   - `python -m unittest tests.test_v06_job_wiki_generator -v`: OK, 7 tests.
   - `python -m unittest tests.test_v06_pending_sources tests.test_v05_process_source tests.test_v06_extractors -v`: OK, 69 tests.
   - `python -m py_compile src/derived_wiki/summary_loader.py src/derived_wiki/writer.py src/derived_wiki/templates.py src/derived_wiki/__init__.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 185 tests.

4. **Next tasks**
   - v06-09: implement job catalog and aliases.

### Current session update: v06-09 job catalog and aliases implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-09 only.
   - Added `src/derived_wiki/job_catalog.py` with `JobEntry`, `JOB_CATALOG`, `resolve_job()`, and `list_jobs()`.
   - Added English, abbreviation, and Korean aliases for the v06 combat job list.
   - Marked Blue Mage as limited and excluded it from `list_jobs()` unless `include_limited=True`.
   - Did not implement job wiki generation or CLI behavior.

2. **Red tests first**
   - Added `V06JobCatalogTests` in `tests/test_v06_job_wiki_generator.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_job_wiki_generator.V06JobCatalogTests -v` failed with 7 missing `src.derived_wiki.job_catalog` module errors.

3. **Verification**
   - `python -m unittest tests.test_v06_job_wiki_generator.V06JobCatalogTests -v`: OK, 7 tests.
   - `python -m unittest tests.test_v06_job_wiki_generator -v`: OK, 14 tests.
   - `python -m unittest tests.test_v06_pending_sources tests.test_v05_process_source tests.test_v06_extractors -v`: OK, 69 tests.
   - `python -m py_compile src/derived_wiki/job_catalog.py src/derived_wiki/__init__.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 192 tests.

4. **Next tasks**
   - v06-10: implement deterministic job wiki generator.

### Current session update: v06-10 job wiki generator implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-10 only.
   - Added `src/derived_wiki/job_wiki_generator.py` for deterministic job entry collection, rendering, and writing.
   - Added `tools/generate_job_wiki.py` with `--all`, `--job`, `--patch-range`, `--dry-run`, `--summary-root`, `--target-root`, and `--include-limited`.
   - Matching is alias-based and evidence-preserving; generated content includes patch sections and `source_id`.
   - Did not implement generic `generate_derived_wiki.py`, FTS integration, or source-processing derived hook.

2. **Red tests first**
   - Added `V06JobWikiGeneratorTests` in `tests/test_v06_job_wiki_generator.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_job_wiki_generator.V06JobWikiGeneratorTests -v` failed with 9 missing module errors for `job_wiki_generator` and `generate_job_wiki`.

3. **Verification**
   - `python -m unittest tests.test_v06_job_wiki_generator.V06JobWikiGeneratorTests -v`: OK, 9 tests.
   - `python -m unittest tests.test_v06_job_wiki_generator -v`: OK, 23 tests.
   - `python tools/generate_job_wiki.py --dry-run --job gunbreaker --summary-root tests/fixtures/source_summaries --target-root /tmp/ffxiv-claw-bot-v06-jobs`: returned `status=ok`, `generated=1`, `written=false`.
   - `python -m py_compile src/derived_wiki/job_wiki_generator.py tools/generate_job_wiki.py src/derived_wiki/__init__.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 201 tests.

4. **Next tasks**
   - v06-11: implement generic `tools/generate_derived_wiki.py` CLI.

### Current session update: v06-11 unified derived wiki CLI implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-11 only.
   - Added `tools/generate_derived_wiki.py` as a thin wrapper around v06-10 job wiki generation.
   - Supports `--kind jobs`, `--job`, `--patch-range`, `--dry-run`, `--summary-root`, `--target-root`, and `--include-limited`.
   - `raids`, `items`, and `systems` now fail clearly as unsupported in v0.6.

2. **Red tests first**
   - Added `V06GenerateDerivedWikiCliTests` in `tests/test_v06_job_wiki_generator.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_job_wiki_generator.V06GenerateDerivedWikiCliTests -v` failed because `tools.generate_derived_wiki` did not exist.

3. **Verification**
   - `python -m unittest tests.test_v06_job_wiki_generator.V06GenerateDerivedWikiCliTests -v`: OK, 5 tests.
   - `python -m unittest tests.test_v06_job_wiki_generator -v`: OK, 28 tests.
   - `python tools/generate_derived_wiki.py --help`: OK.
   - `python tools/generate_derived_wiki.py --kind jobs --dry-run --job gunbreaker --summary-root tests/fixtures/source_summaries --target-root /tmp/ffxiv-claw-bot-v06-derived-jobs`: returned `status=ok`, `kind=jobs`, `generated=1`, `written=false`.
   - `python -m py_compile tools/generate_derived_wiki.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 206 tests.

4. **Next tasks**
   - v06-12: extend FTS indexing to include derived wiki pages.

### Current session update: v06-12 FTS indexing extension implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-12 only.
   - Added `src/wiki_indexing/wiki_document_scanner.py` with `WikiDocument` and filesystem scanning for `wiki/source_summaries/*.md` and `wiki/jobs/*.md`.
   - Added `tools.compile_wiki.index_wiki_documents()` to upsert scanned wiki pages into `wiki_pages` and `wiki_fts`.
   - Kept `wiki_fts(page_id, title, body)` unchanged; v0.6 metadata is stored in `wiki_pages.type` and `wiki_pages.job`.
   - Did not wire this into source processing or pending loop yet.

2. **Red tests first**
   - Added `tests/test_v06_fts_indexing.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v06_fts_indexing -v` failed because `src.wiki_indexing` and `index_wiki_documents()` did not exist.

3. **Verification**
   - `python -m unittest tests.test_v06_fts_indexing -v`: OK, 7 tests.
   - `python -m unittest tests.test_compile_wiki -v`: OK, 3 tests.
   - `python -m py_compile src/wiki_indexing/wiki_document_scanner.py src/wiki_indexing/__init__.py tools/compile_wiki.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 213 tests.

4. **Next tasks**
   - v06-13: connect optional derived wiki generation after source processing.

### Current session update: v06-13 derived wiki hook implemented -- 2026-05-16

1. **Scope**
   - Implemented v06-13 only.
   - `tools/process_source.py` now accepts `--build-derived-wiki` and `--skip-derived-wiki`.
   - Default behavior remains skip; derived wiki generation is opt-in and calls the v06-11 `generate_derived_wiki.run()` path with `kind=jobs`.
   - `tools/process_pending_sources.py` passes `--build-derived-wiki` through to each source when requested.
   - Derived wiki success records queue status `derived_wiki_built`; derived wiki failure records `error_stage=derived_wiki_generate` without marking source processing itself as failed.
   - Derived wiki generation is skipped when source processing does not return `status=ok`, preventing stale derived output after partial rebuilds.

2. **Red tests first**
   - Added four hook tests to `V06PendingSourceLoopTests`.
   - Confirmed expected red failure before implementation: default skip passed, while opt-in/failure-path cases failed because `--build-derived-wiki` and `tools.process_source.generate_derived_wiki` hook wiring were missing.
   - Added a partial-rebuild guard test and confirmed expected red failure because the hook was still attempted after `status=partial`.

3. **Verification before full gate**
   - Focused v06-13 hook tests: OK, 4 tests.
   - `python -m unittest tests.test_v06_pending_sources -v`: OK, 10 tests.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 32 tests.
   - `python -m unittest tests.test_v06_job_wiki_generator -v`: OK, 28 tests.
   - `python -m py_compile tools/process_source.py tools/process_pending_sources.py tools/generate_derived_wiki.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 218 tests.

4. **Next tasks**
   - v06-14: README/handoff/final documentation gate and final verification for the v0.6 slice.

### Current session update: v06-14 README and handoff documentation completed -- 2026-05-16

1. **Scope**
   - Completed the v06-14 documentation-only final gate.
   - Updated root `README.md` with v0.6 pipeline, supported formats, common source-processing commands, pending queue commands, derived wiki commands, and final verification commands.
   - Added `docs/runbooks/process-pending-sources.md` for queue CLI options, status transitions, retry policy, derived wiki hook behavior, and troubleshooting.
   - Added `docs/runbooks/generate-derived-wiki.md` for job wiki generation, unified derived wiki CLI usage, FTS indexing, hook behavior, and troubleshooting.
   - Updated docs index/profile/inventory/owners/handoff/v06 feature map to mark v0.6 complete.

2. **Runtime changes**
   - None. This task is documentation-only.

3. **Verification**
   - `python scripts/check_docs_freshness.py --all`: ok.
   - v06-14 changed files path-scoped `git diff --check`: OK.
   - `python scripts/finish_task.py`: finish_task ok.
     - `python -m unittest discover -s tests -p "test_*.py"`: OK, 218 tests.
     - docs freshness check: ok.
     - Notion handoff dry-run: ok.

4. **Next tasks**
   - Future v0.6.1/v0.7 work should be separate specs: PDF/DOCX/OCR, scheduler/daemon, raids/items/systems derived wiki, and LLM-based summarization.

### Current session update: v06.1 derived wiki FTS hardening -- 2026-05-16

1. **Scope**
   - Closed the derived wiki pipeline gap found after v06.
   - `tools/process_source.py --build-derived-wiki` now calls `tools.compile_wiki.index_wiki_documents(root_path=ROOT, db_path=Path(args.db_path))` after successful job wiki generation.
   - The result action list now includes `index_wiki_documents`.
   - `result["derived_wiki"]["fts_index"]` records indexing status and summary.
   - If FTS indexing fails after derived wiki generation, source processing remains `status=ok` and `derived_wiki.status=partial` with `error_stage=derived_wiki_fts_index`.

2. **Red tests first**
   - Added direct `process_source.py --build-derived-wiki` regression for `wiki_fts.page_id='job_gunbreaker'`.
   - Added pending-loop `--build-derived-wiki` regression for the same FTS row.
   - Added FTS failure regression for `derived_wiki.status=partial`.
   - Confirmed expected red failures before implementation: missing `derived_wiki.fts_index` and missing `tools.process_source.index_wiki_documents` patch target.

3. **Verification before full gate**
   - `python -m unittest tests.test_v05_process_source.V05ProcessSourceRebuildIntegrationTests.test_process_build_derived_wiki_indexes_job_wiki_documents tests.test_v05_process_source.V05ProcessSourceRebuildIntegrationTests.test_process_build_derived_wiki_fts_failure_returns_partial_derived_wiki -v`: OK, 2 tests.
   - `python -m unittest tests.test_v06_pending_sources.V06PendingSourceLoopTests.test_process_pending_sources_build_derived_wiki_indexes_job_wiki_documents -v`: OK, 1 test.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 34 tests.
   - `python -m unittest tests.test_v06_pending_sources -v`: OK, 11 tests.
   - `python -m unittest tests.test_v06_fts_indexing -v`: OK, 7 tests.
   - `python -m py_compile tools/process_source.py`: OK.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 221 tests.

4. **Remaining follow-up candidates**
   - Add a dedicated `derived_wiki_status` queue column in a separate schema migration if queue filtering by derived state becomes necessary.
   - Improve XLSX extraction for dates, formulas, merged cells, hidden rows/columns, multi-line cells, and inferred headers in a separate extractor hardening task.
   - Decide whether to rename the v06 spec file from `0005- v06...` to a `0006-...` filename in a separate docs migration.

### Current session update: v05 process-source test fixture refactor -- 2026-05-16

1. **Scope**
   - Refactored only `tests/test_v05_process_source.py`.
   - Added `ProcessSourceTempCase` to centralize temp directory, storage root, repo root, SQLite DB path, schema initialization, and `process_source.py` invocation for integration-style tests.
   - Converted local source, URL source, rebuild, and Notion payload integration tests to use the shared fixture.
   - Left the dry-run side-effect test's local `TemporaryDirectory` in place because it intentionally asserts that dry-run does not create storage or DB paths.

2. **Verification**
   - `python -m unittest tests.test_v05_process_source -v`: OK, 27 tests.

3. **Notes**
   - No production behavior changed.
   - Keep `AGENTS.md` local change separate unless the maintainer explicitly wants it committed.

### Current session update: v05.1-06/v05.1-07/v05.1-08 boundary docs, regression tests, and final verification -- 2026-05-16

1. **Scope**
   - Implemented v05.1-06 entrypoint boundary documentation.
   - Implemented v05.1-07 runbook regression tests.
   - Completed v05.1-08 final verification and handoff cleanup.
   - Did not implement optional debug CLIs, crawler, scheduler, daemon, Notion API calls, Notion polling, or v0.6 automation behavior.

2. **Red tests first**
   - Added boundary regression tests under `V05ProcessSourceRunbookTests` in `tests/test_v05_process_source.py`.
   - Confirmed expected red failure: `python -m unittest tests.test_v05_process_source.V05ProcessSourceRunbookTests -v` failed 5 boundary tests because `docs/runbooks/process-source.md` did not yet include official entrypoint, helper misuse, library-only, payload-builder-only, and Notion auto-apply wording.

3. **Implementation**
   - `docs/runbooks/process-source.md` now names `tools/process_source.py` as the official source processing entrypoint for normal OpenClaw source processing.
   - The runbook documents the correct `markdown_file --local-path` path and the bad `ingest_local.py --body "/path/file.md"` pattern that stores the path string itself, not file contents.
   - The runbook documents `tools/ingest_local.py` as a low-level helper, `tools/local_rebuild.py` as library-only for normal workflow, and `tools/status_notification.py` as payload-builder-only and not a Notion write CLI.
   - The runbook states `result["notion_update"]` is a payload only, is not already applied, and `process_source.py` itself does not call the Notion API.

4. **Docs updated**
   - `docs/plans/v05.1/README.md`: v05.1-06 and v05.1-07 marked Completed; v05.1-08 final status recorded in this session.
   - `docs/plans/v05.1/2026-05-16-v05.1-06-entrypoint-boundary-docs.md`: checklist and verification updated.
   - `docs/plans/v05.1/2026-05-16-v05.1-07-runbook-regression-tests.md`: checklist, red result, and verification updated.
   - `docs/plans/v05.1/2026-05-16-v05.1-08-final-verification-and-handoff.md`: final verification checklist and results updated.
   - `docs/specs/0004a-v05.1-source-processing-hardening.md`: AC-0004A-010 through AC-0004A-020 marked implemented or re-verified.
   - `docs/runbooks/test.md`: v05.1 boundary regression tests and results documented.
   - `docs/handoff/CURRENT_HANDOFF.md`: this update.

5. **Verification before final gate**
   - `python -m unittest tests.test_v05_1_lodestone_extractor -v`: OK, 5 tests.
   - `python -m unittest tests.test_v05_fetch_url -v`: OK, 6 tests.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 27 tests.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 136 tests.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `git diff --check`: OK.
   - `python scripts/finish_task.py`: finish_task ok.

6. **Next tasks**
   - v05.1 is complete. Future work should stay outside this scope unless a new v0.6 plan/spec is created.
   - Keep `AGENTS.md` local change separate unless the maintainer explicitly wants it committed.

### Current session update: v05.1-04/v05.1-05 fetch routing and extractor metadata implemented -- 2026-05-16

1. **Scope**
   - Implemented only v05.1 B: tasks 04 and 05.
   - Added `fetch_single_url()` extractor metadata for Lodestone, generic HTML, text, and JSON responses.
   - Added `process_source.py` URL action metadata propagation.
   - Did not implement v05.1-06/v05.1-07 entrypoint boundary docs regression tasks, crawler, scheduler, daemon, Notion API calls, or Notion polling.

2. **Red tests first**
   - Updated `tests/test_v05_fetch_url.py`.
   - Added `test_fetch_url_uses_lodestone_extractor_for_lodestone_url`.
   - Added JSON extractor metadata coverage and extended existing generic HTML/text tests.
   - Confirmed expected red failure: `python -m unittest tests.test_v05_fetch_url -v` failed because `extractor` metadata was missing and Lodestone HTML still used the generic title path.
   - Added `test_process_lodestone_url_records_lodestone_extractor_action` in `tests/test_v05_process_source.py`.
   - Confirmed expected red failure: focused process-source test failed because `fetch_url.extractor` was missing.

3. **Implementation**
   - `tools/fetch_url.py`: imports the Lodestone extractor, routes `text/html` Lodestone URLs to `extract_lodestone_article()`, preserves generic HTML extraction for non-Lodestone pages, and returns stable extractor values: `lodestone`, `generic_html`, `text`, and `json`.
   - `tools/process_source.py`: adds shared fetch action construction and copies `fetch_result["extractor"]` into successful `fetch_url` actions when present.
   - `notion_update` remains metadata-only and does not include body, raw HTML, attachments, or binary fields.

4. **Docs updated**
   - `docs/plans/v05.1/README.md`: v05.1-04 and v05.1-05 marked Completed.
   - `docs/plans/v05.1/2026-05-16-v05.1-04-fetch-url-routing.md`: checklist and verification updated.
   - `docs/plans/v05.1/2026-05-16-v05.1-05-process-source-extractor-metadata.md`: checklist and verification updated.
   - `docs/specs/0004a-v05.1-source-processing-hardening.md`: AC-0004A-005 through AC-0004A-009 marked implemented; AC-0004A-021 re-verified.
   - `docs/runbooks/process-source.md`: URL extractor routing and `fetch_url` action metadata documented.
   - `docs/runbooks/test.md`: v05.1-04/v05.1-05 red and green results documented.
   - `docs/handoff/CURRENT_HANDOFF.md`: this update.

5. **Verification**
   - `python -m unittest tests.test_v05_fetch_url -v`: OK, 6 tests.
   - `python -m unittest tests.test_v05_process_source.V05ProcessSourceUrlIntegrationTests.test_process_lodestone_url_records_lodestone_extractor_action -v`: OK.
   - `python -m py_compile tools/fetch_url.py tools/process_source.py`: OK.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 22 tests.
   - `python -m unittest tests.test_v05_1_lodestone_extractor -v`: OK, 5 tests.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 131 tests.
   - `git diff --check`: OK.

6. **Next tasks**
   - v05.1-06: entrypoint boundary docs.
   - v05.1-07: runbook regression tests.
   - v05.1-08: final verification and handoff cleanup for the whole v05.1 slice.

### Current session update: v05.1-02/v05.1-03 Lodestone extractor implemented -- 2026-05-16

1. **Scope**
   - Implemented only v05.1 A: tasks 02 and 03.
   - Added a local Lodestone-like 7.5 fixture and red tests.
   - Added a domain-specific Lodestone extractor package.
   - Did not implement `fetch_url.py` routing, `process_source.py` extractor action metadata, crawler, scheduler, daemon, or Notion API calls.

2. **Red tests first**
   - Added `tests/test_v05_1_lodestone_extractor.py`.
   - Added `tests/fixtures/lodestone_patch_7_5.html`.
   - Confirmed expected red failure: `python -m unittest tests.test_v05_1_lodestone_extractor -v` failed with 5 failures because `tools.extractors.lodestone` did not exist.

3. **Implementation**
   - `tools/extractors/__init__.py`: exports the Lodestone extractor API.
   - `tools/extractors/lodestone.py`: adds `LodestoneExtractionError`, `is_lodestone_url()`, and `extract_lodestone_article()`.
   - The extractor recognizes official `na/eu/jp/de/fr.finalfantasyxiv.com/lodestone/` URLs.
   - The extractor prefers `.news__detail__wrapper`, removes script/style/nav/footer/header/aside/share UI noise, normalizes text, and returns `title`, `body`, and `extractor=lodestone`.

4. **Docs updated**
   - `docs/plans/v05.1/README.md`: v05.1-02 and v05.1-03 marked Completed.
   - `docs/plans/v05.1/2026-05-16-v05.1-02-lodestone-fixture-and-red-tests.md`: checklist and red verification updated.
   - `docs/plans/v05.1/2026-05-16-v05.1-03-lodestone-extractor.md`: checklist, implementation notes, and verification updated.
   - `docs/specs/0004a-v05.1-source-processing-hardening.md`: status Active and first Lodestone acceptance criteria marked implemented.
   - `docs/specs/0004-v05-source-processing-pipeline.md`: v05.1 Lodestone hardening note added.
   - `docs/runbooks/process-source.md`, `docs/runbooks/test.md`, `docs/PROJECT_PROFILE.md`, `docs/FILE_INVENTORY.md`, and `docs/DOC_OWNERS.yml` updated.

5. **Verification**
   - `python -m unittest tests.test_v05_fetch_url -v`: OK, 4 tests.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 21 tests.
   - `python -m unittest tests.test_v05_1_lodestone_extractor -v`: OK, 5 tests.
   - `python -m py_compile tools/extractors/__init__.py tools/extractors/lodestone.py`: OK.
   - Serena diagnostics for `tools/extractors/lodestone.py`: no warnings/errors.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 128 tests.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `git diff --check`: OK.
   - `python scripts/finish_task.py`: finish_task ok.

6. **Next tasks**
   - v05.1-04: route Lodestone URLs through the extractor in `tools/fetch_url.py`.
   - v05.1-05: include extractor metadata in the `process_source.py` `fetch_url` action.

### Current session update: v05 duplicate canonical source policy locked -- 2026-05-16

1. **Scope**
   - Accepted the existing Local Storage behavior as the official v05 duplicate policy.
   - Duplicate canonical sources are now documented as canonical `source_id` upsert/update, not `status=skipped`.

2. **Implementation**
   - Added `test_process_duplicate_source_upserts_existing_source_id` in `tests/test_v05_process_source.py`.
   - The test runs the same `text_note` canonical source twice, verifies the same `source_id` and canonical path are reused, and checks the Local Storage file, raw snapshot, and `sources` row contain the latest body/hash.

3. **Docs updated**
   - `docs/specs/0004-v05-source-processing-pipeline.md`: Dedupe Policy and Test Plan now name `canonical_source_upsert`.
   - `docs/runbooks/process-source.md`: Duplicate Policy section added.
   - `docs/runbooks/test.md`: duplicate canonical source contract added.
   - `docs/plans/v05/2026-05-16-v05-08-tests-and-runbook.md`: duplicate coverage added.

4. **Verification**
   - `python -m unittest tests.test_v05_process_source.V05ProcessSourceLocalIntegrationTests.test_process_duplicate_source_upserts_existing_source_id -v`: OK.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 21 tests.

### Current session: v05 spec and plan complete -- 2026-05-16

1. **v0.5 spec 작성 완료**
   - `docs/specs/0004-v05-source-processing-pipeline.md` (1330 lines) — Goal, Non-Goals, Design Principle, Source Types, Storage Model, OpenClaw Skill Layer, Repo Execution Layer, CLI contract, Pipeline Steps, Output Contract, Status Semantics, Dry Run Semantics, Error Handling, Dedupe, URL Policy, Notion Integration, Test Plan, Acceptance Criteria, Future Work.
   - 핵심 원칙: `OpenClaw = 판단`, `process_source.py = 실행`.

2. **v0.5 plan 구조 작성 완료 (v05-01 Completed)**
   - `docs/plans/v05/README.md` — feature map (01–08), red test map, scope/non-goals, status semantics, completion criteria.
   - `docs/plans/v05/2026-05-16-v05-01-spec-and-plan.md` — **Completed** (this session).
   - `docs/plans/v05/2026-05-16-v05-02-openclaw-skill-draft.md` — Pending.
   - `docs/plans/v05/2026-05-16-v05-03-process-source-skeleton.md` — Pending.
   - `docs/plans/v05/2026-05-16-v05-04-local-source-integration.md` — Pending.
   - `docs/plans/v05/2026-05-16-v05-05-url-integration.md` — Pending.
   - `docs/plans/v05/2026-05-16-v05-06-rebuild-integration.md` — Pending.
   - `docs/plans/v05/2026-05-16-v05-07-notion-payload-integration.md` — Pending.
   - `docs/plans/v05/2026-05-16-v05-08-tests-and-runbook.md` — Pending.

3. **문서 갱신**
   - `docs/handoff/CURRENT_HANDOFF.md`: current phase → v05, Read First → v05 spec/plans, new session entry.
   - `docs/PROJECT_PROFILE.md`: Current Phase → v05 planning complete, mention process_source.py.
   - `docs/FILE_INVENTORY.md`: add v05 spec and plans.
   - `docs/DOC_OWNERS.yml`: add `v05-source-pipeline` rule placeholder (spec only, no code yet).
   - `CLAUDE.md`: add v05 pipeline commands to Development Commands.

4. **검증**
   - `python -m unittest discover -s tests -p "test_*.py"`: **98 tests, 0 reds**.
   - `python scripts/check_docs_freshness.py --all`: **ok**.
   - `python scripts/finish_task.py --skip-notion-dry-run`: **finish_task ok**.

5. **Git push**: main 브랜치에 v05 spec + plans 커밋 및 push 완료.

6. **Google Drive**: not touched.
7. **다음 작업**: v05-02 OpenClaw Skill Draft 작성.

### Current session update: v05-02/v05-03 skeleton implemented -- 2026-05-16

1. **Red tests first**
   - Added `tests/test_v05_process_source.py`.
   - Initial focused run failed because `docs/skills/ffxiv-source-processing.md` and `tools/process_source.py` did not exist.

2. **v05-02 OpenClaw Skill Draft implemented**
   - Created `docs/skills/ffxiv-source-processing.md`.
   - Documents source type inference, category rules, ambiguity handling, `python tools/process_source.py` command construction, JSON parsing, and `notion_update` handling.

3. **v05-03 process_source skeleton implemented**
   - Created `tools/process_source.py`.
   - Supports CLI parsing for `--apply`, `--dry-run`, `--source-type`, `--category`, `--title`, `--body`, `--local-path`, `--url`, `--storage-root`, `--db-path`, and `--notion-page-id`.
   - Validation errors always print stdout JSON with `status=error` and `graph_status=skipped`.
   - Dry-run prints stdout JSON with `status=skipped`, skips side-effect actions, and does not create files or DB rows.
   - Direct script execution via `python tools/process_source.py ...` is covered by regression test.
   - Valid `--apply` is intentionally not implemented yet and returns JSON error; v05-04+ owns actual ingest/rebuild/payload wiring.

4. **Scope guard**
   - v05-04, v05-05, v05-06, v05-07, and v05-08 implementation tasks were not executed.

5. **Verification**
   - `python -m unittest tests.test_v05_process_source -v`: **8 tests, OK**.
   - `python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "Test" --body "hello"`: **OK**, JSON `status=skipped`.
   - `python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com"`: **OK**, JSON `status=skipped`.
   - `python tools/process_source.py --apply --source-type text_note --category personal_notes --title "Apply guard" --body "hello"`: **OK**, JSON `status=error` with v05-04 next action.
   - `python -m unittest discover -s tests -p "test_*.py"`: **106 tests, OK**.
   - `python scripts/check_docs_freshness.py --all`: **ok**.
   - `python scripts/finish_task.py --skip-notion-dry-run`: **finish_task ok**.

### Current session update: v05-04 local source integration implemented -- 2026-05-16

1. **Scope**
   - Implemented only v0.5-04.
   - Connected `text_note`, `markdown_file`, and `plain_text_file` apply mode in `tools/process_source.py` to Local Storage ingest.
   - Did not implement URL fetch, rebuild execution, or Notion success payload generation.

2. **Red tests first**
   - Added local integration tests to `tests/test_v05_process_source.py`.
   - Confirmed the new tests failed against the v05-03 skeleton because apply returned `status=error` and ingest failure did not include rebuild skip.

3. **Implementation**
   - `tools/ingest_local.py`
     - Added reusable `ingest_source(...)` function.
     - Preserved CLI JSON behavior.
     - Added `root_path` injection for raw snapshot tests.
     - Changed `plain_text_file` canonical extension to `.md` for v05 local source processing.
   - `tools/process_source.py`
     - Applies local source types through `ingest_local.ingest_source()`.
     - Returns `source_id`, `canonical_path`, `local_source_path`, `raw_path`, `content_hash`.
     - Leaves `graph_status=skipped` and emits rebuild skipped action until v05-06.
     - On ingest failure, returns `status=error`, `graph_status=skipped`, and rebuild skipped with `reason=upstream_ingest_error`.

4. **Docs updated after implementation**
   - `docs/plans/v05/2026-05-16-v05-04-local-source-integration.md`: Status Completed, checklist, implementation notes, verification results.
   - `docs/plans/v05/README.md`: v05-04 status Completed.
   - `docs/specs/0004-v05-source-processing-pipeline.md`: v05-04 local ingest behavior note.
   - `docs/runbooks/process-source.md`: new process_source runbook.
   - `docs/runbooks/local-storage.md`: reusable `ingest_source()` and v05 local text storage behavior.
   - `docs/runbooks/test.md`: v05-04 tests and full suite count.
   - `docs/handoff/CURRENT_HANDOFF.md`: this update.

5. **Verification before docs update**
   - `python -m unittest tests.test_v05_process_source -v`: **12 tests, OK**.
   - `python -m unittest tests.test_v04_ingest_local_cli tests.test_v04_local_rebuild -v`: **4 tests, OK**.
   - `python -m unittest discover -s tests -p "test_*.py"`: **110 tests, OK**.
   - `python -m py_compile tools/process_source.py tools/ingest_local.py`: **OK**.

6. **Final docs verification**
   - `python scripts/check_docs_freshness.py --all`: **ok**.
   - `python scripts/finish_task.py`: **finish_task ok** (110 tests OK, docs freshness OK, Notion handoff dry-run OK).

7. **Git**
   - Code/test commit pushed: `34092fd Implement v05 local source processing`.
   - Documentation update follows the code/test commit because `CLAUDE.md` requires docs/handoff freshness before finish gate.

### Current session update: v05-06/v05-07/v05-08 completed -- 2026-05-16

1. **Scope**
   - Implemented v05-06 rebuild integration, v05-07 Notion payload generation, and v05-08 tests/runbook/handoff cleanup.
   - Did not implement Notion API direct calls, Notion polling, crawler, or scheduler behavior.

2. **Red tests first**
   - Added rebuild red tests in `tests/test_v05_process_source.py`; confirmed failures because `process_source.py` did not call `local_rebuild.rebuild_after_ingest()`.
   - Added Notion payload red tests; confirmed failures because `notion_update` was empty.
   - Added runbook red test; confirmed failure because `docs/runbooks/process-source.md` still described v05-06/v05-07 as unimplemented.

3. **Implementation**
   - `tools/process_source.py`
     - Calls `tools.local_rebuild.rebuild_after_ingest()` after successful local or URL ingest.
     - Merges `compile_wiki`, `index_fts`, and `build_graph` actions into the final JSON.
     - Sets `graph_status=built`, `failed`, or `pending` from rebuild actions.
     - Returns `status=partial` when ingest succeeded but rebuild failed.
     - Builds metadata-only `notion_update` payload with `tools.status_notification.build_notion_status_update()`.
     - Adds `Last Processed` and `build_notion_payload` action.
   - `tools/local_rebuild.py`
     - Passes `summary_dir=root_path/wiki/source_summaries` into `compile_for_source()` so temp-root rebuild tests produce the expected relative wiki path.

4. **Docs updated**
   - `docs/runbooks/process-source.md`: completed workflow, examples, JSON output, OpenClaw sequence, troubleshooting, and validation.
   - `docs/runbooks/test.md`: v05-06/v05-07/v05-08 test coverage.
   - `docs/plans/v05/README.md`: v05-06/07/08 marked Completed.
   - `docs/plans/v05/2026-05-16-v05-06-rebuild-integration.md`: status and implementation notes.
   - `docs/plans/v05/2026-05-16-v05-07-notion-payload-integration.md`: status and implementation notes.
   - `docs/plans/v05/2026-05-16-v05-08-tests-and-runbook.md`: status and implementation notes.
   - `docs/specs/0004-v05-source-processing-pipeline.md`: v05-06/v05-07 implementation notes.
   - `docs/PROJECT_PROFILE.md`, `docs/FILE_INVENTORY.md`, and this handoff updated.

5. **Verification**
   - `python -m unittest tests.test_v05_process_source.V05ProcessSourceRebuildIntegrationTests -v`: OK.
   - `python -m unittest tests.test_v05_process_source.V05ProcessSourceNotionPayloadIntegrationTests -v`: OK.
   - `python -m unittest tests.test_v05_process_source.V05ProcessSourceRunbookTests -v`: OK.
   - `python -m unittest tests.test_v05_process_source -v`: OK, 20 tests.
   - `python -m unittest discover -s tests -p "test_*.py"`: OK, 122 tests.
   - `python scripts/check_docs_freshness.py --all`: ok.
   - `python scripts/finish_task.py`: finish_task ok.

6. **Git**
   - Commit and push requested by maintainer; pending after this handoff update is re-verified.

### Current session update: v05-05 URL integration implemented -- 2026-05-16

1. **Scope**
   - Implemented only v0.5-05.
   - Added single user-provided URL fetch and connected it to Local Storage ingest.
   - Did not implement crawler, scheduler, search engine usage, sitemap parsing, recursive crawling, rebuild execution, or Notion success payload generation.

2. **Red tests first**
   - Added `tests/test_v05_fetch_url.py`.
   - Added URL integration tests to `tests/test_v05_process_source.py`.
   - Confirmed red failures: `tools.fetch_url` missing and `process_source.py` URL apply path not connected.

3. **Implementation**
   - `tools/fetch_url.py`
     - Added `fetch_single_url()` and `UrlFetchError`.
     - Supports `text/html`, `text/plain`, `application/json`, and `+json`.
     - Extracts HTML title and visible text using existing `tools.html_utils`.
     - Uses `requests` when installed and stdlib `urllib` fallback otherwise.
   - `tools/process_source.py`
     - Connects `--apply --source-type url` to `fetch_single_url()`.
     - Sends fetched body into `tools.ingest_local.ingest_source(source_type="url", ...)`.
     - Emits `fetch_url`, `ingest_local`, and skipped `rebuild` actions.
     - Fetch failure returns `status=error`, `source_id=null`, `graph_status=skipped`, and does not ingest.

4. **Docs updated**
   - `docs/plans/v05/2026-05-16-v05-05-url-integration.md`: Status Completed, checklist, implementation notes, verification results.
   - `docs/plans/v05/README.md`: v05-05 status Completed.
   - `docs/specs/0004-v05-source-processing-pipeline.md`: v05-05 URL behavior note.
   - `docs/runbooks/process-source.md`: URL apply usage and output behavior.
   - `docs/runbooks/test.md`: v05-05 test coverage and full suite count.
   - `docs/PROJECT_PROFILE.md` and `docs/FILE_INVENTORY.md`: v05-05 current file/status updates.
   - `docs/handoff/CURRENT_HANDOFF.md`: this update.

5. **Verification**
   - `python -m unittest tests.test_v05_fetch_url -v`: **4 tests, OK**.
   - `python -m unittest tests.test_v05_process_source -v`: **15 tests, OK**.
   - `python -m py_compile tools/fetch_url.py tools/process_source.py`: **OK**.
   - `python -m unittest discover -s tests -p "test_*.py"`: **117 tests, OK**.

### Previous session: v04 final cleanup -- 2026-05-16

1. **Notion status semantics 정리**
   - `docs/runbooks/openclaw-notion.md`: Status Values 섹션을 progression diagram(`New → Queued → Snapshot → Indexed → Graph Built`) + table + 원칙 4개로 보강.
   - `tools/status_notification.py`: `build_notion_status_update()`에서 `status=ok` + `graph_status=built` → Notion Status = `Graph Built`로 승격.
   - runbook CLI‑to‑Notion status mapping table에 승격 규칙을 명시.

2. **Notion test record 정리**
   - `discord_agent_smoke_test` (page ID: `3614bf16-ed1f-8181-9e34-e9e2021bde9e`) 업데이트:
     - Status: `Indexed` → `Graph Built`
     - Graph Status: `Built` (변경 없음)
     - Local Source Path, Wiki Path 정규화 (markdown link 제거)

3. **env 이름 분리**
   - `~/.openclaw/.env`:
     - 기존: `NOTION_HANDOFF_PAGE_ID` (handoff mirror page 전용)
     - 추가: `NOTION_FFXIV_SOURCES_DB_ID=3614bf16-ed1f-81d3-a15f-e36edc92aa86` (FFXIV KB Sources database 전용)
   - 두 변수로 역할 분리 완료.

4. **Generated artifact 정책 확인**
   - `docs/FILE_INVENTORY.md`: `graph/nodes.json`, `graph/edges.json`이 "Derived cache"로 명시.
   - `docs/PROJECT_PROFILE.md`: `raw/local_storage`, `wiki`, `db`, FTS, graph는 재생성 가능한 파생 계층.
   - `.gitignore`에 이미 `graph/nodes.json`, `graph/edges.json` 포함 (`.gitignore:18-19`).
   - `git ls-files`로 tracked not → 확인. 정책과 실제 일치, 추가 조치 불필요.

5. **최종 검증**
   - `python -m unittest discover -s tests -p "test_*.py"`: **95 tests, 0 reds**
   - `python scripts/check_docs_freshness.py --all`: **ok** (DOCS_UPDATE_NOT_REQUIRED override for .gitignore; other rules satisfied)
   - `python scripts/finish_task.py --skip-notion-dry-run`: **finish_task ok**

6. **Regressions tests updated in this session**
   - `tests/test_v04_status_notification.py`: +3 tests (Graph Built promotion, body/attachments/Drive exclusion, `ok` without `graph_status` defaults Indexed). Total: 4 tests.
   - `docs/runbooks/test.md`: Graph Built Status Promotion Tests 섹션 추가. Suite count 95→98.
   - `docs/plans/v04/README.md`: v04-05 test count 4로 갱신.
   - `docs/handoff/CURRENT_HANDOFF.md`: 이 업데이트.
   - Full suite: **98 tests, 0 reds**.
   - `finish_task.py`: 통과.

7. **Google Drive**: not touched.

8. **후속 과제**: 한국어 검색 품질 개선, 실제 FFXIV 문서 대량 ingest.

### Previous session: FTS5 syntax error regression fix -- 2026-05-15

1. Answer.py E2E test exposed `sqlite3.OperationalError: FTS5 syntax error near "@[/]"`
   when user input contained FTS5-special characters (`@`, `/`, `"`, `(`, `)`, `-`, `+`, `*`, `^`, `:`).
2. Root cause: `format_query()` in `search_kb.py` passed raw user input directly to the FTS5 MATCH clause.
3. Fix added:
   - `tools/search_kb.py`: new `sanitize_fts_query()` function strips FTS5-special characters before MATCH.
   - `tools/answer.py`: `build_contexts()` wraps `search_fts()` in try/except for `sqlite3.OperationalError`
     as defense-in-depth, falling through to empty results.
   - `tools/search_kb.py`: `search_fts()` OperationalError also falls through to empty results instead of
     returning an error JSON to the CLI caller.
4. Added 22 regression tests in `tests/test_search_kb.py`:
   - 13 `SanitizeFtsQueryTests`: each special char (`@`, `/`, `"`, `(`, `)`, `-`, `+`, `*`, `^`, `:`) removed;
     Korean text, underscores, whitespace collapse preserved.
   - 2 `FormatQueryTests`: empty rejection, sanitization applied.
   - 7 `AnswerBuildContextsNoCrashTests`: real paths (`tools/ingest_local.py`, `foo/bar baz`),
     special chars (`@`, `"`), OpenClaw/Discord input, discord_agent_smoke_test,
     empty results `format_answer_text` produces "찾을 수 없습니다" without crash.
5. 한국어 검색 커버리지 한계: `unicode61` tokenizer는 CJK unigram 분할을 하지 않으므로
   한국어 query가 분할되지 않은 채로 MATCH되면 의도한 대로 매칭되지 않을 수 있다.
   이는 버그가 아닌 tokenizer 한계이며 FTS5 버전 업 또는 custom tokenizer 도입이 필요하다.
6. Updated docs:
   - `docs/runbooks/test.md`: FTS5 query sanitization tests section added, full suite count updated to 95.
   - `docs/runbooks/rebuild-kb.md`: FTS5 sanitization note added to Search/Answer smoke test section.
   - `docs/DOC_OWNERS.yml`: `tests/test_search_kb.py` added to `local-kb-pipeline` rule.
   - `docs/specs/0001-local-kb-pipeline.md`: FTS5 query sanitization note added.
   - `docs/handoff/CURRENT_HANDOFF.md`: 이 업데이트.
7. Full test suite: **95 tests, 0 reds** — +22 FTS5 regression tests.
8. Google Drive: not touched. No commit/push. Graph JSON and DB not included.

### Previous session: content_hash bugfix + regression test -- 2026-05-15

1. OpenClaw Discord E2E smoke test exposed `sqlite3.IntegrityError: NOT NULL constraint failed: sources.content_hash` during `--apply`.
   - Root cause: `_do_upsert_source()` INSERT and UPDATE SQL statements omitted `content_hash` column.
2. OpenClaw agent applied temporary fix (add `hashlib.sha256` content_hash computation) to unblock the E2E run.
3. Stabilized the fix in the repo:
   - `tools/ingest_local.py`: `_do_upsert_source()` now computes `body_hash = hashlib.sha256((args.body or "").encode("utf-8")).hexdigest()` and includes it in both INSERT and UPDATE SQL statements.
4. Added 2 regression tests in `tests/test_v04_ingest_local_cli.py`:
   - `test_text_note_apply_stores_content_hash_on_insert` — verifies `--apply` stores non-NULL `content_hash` matching body SHA-256 on INSERT.
   - `test_text_note_apply_stores_content_hash_on_update` — verifies `--apply` updates `content_hash` to match new body SHA-256 on UPDATE.
5. Updated docs:
   - `docs/runbooks/test.md`: content_hash regression tests documented, full suite count updated to 73.
   - `docs/runbooks/local-storage.md`: content_hash behavior documented in Ingest Local CLI section.
   - `docs/plans/v04/README.md`: note added about 3 tests in v04-03 test file.
   - `docs/handoff/CURRENT_HANDOFF.md`: 이 업데이트.
6. Full test suite: **73 tests, 0 reds** — +2 content_hash regression tests.

### Previous session: v04-05 Status Notification -- Implemented

1. Created `tools/status_notification.py`:
   - `format_discord_summary(result)` — produces short Korean plain-text Discord/OpenClaw-facing summary.
     - `ok` → `[category] title — 처리 완료` + paths
     - `partial` → `[category] title — 일부 실패` + paths + error + next action
     - `error` → `[category] title — 처리 실패` + error + next action
     - `skipped` → `[category] title — 건너뜀 (처리 생략)`
     - Never includes Drive URL (per v04-05 contract).
   - `build_notion_status_update(result)` — flat dict of Notion property name→value pairs.
     - Maps `status` → `Status` (ok→Indexed, partial→Partial, error→Error)
     - Maps `graph_status` → `Graph Status` (built→Built, pending→Pending, failed→Failed, skipped→Skipped)
     - Copies title, category, source_id, local_source_path, wiki_path, last_error, next_action verbatim.
   - Used `tools/openclaw_notion_control.py` status mapping conventions but kept independent mapping constants (v04-05 uses "Failed" not "Error" for graph status).
2. Red test → Green: `tests/test_v04_status_notification.py` 1/1 pass.
3. Updated docs:
   - `docs/plans/v04/2026-05-14-v04-05-status-notification.md`: Status → Implemented, checklist all [x], Implementation Notes + Verification Results added.
   - `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`: v04-05 status → Implemented.
   - `docs/runbooks/openclaw-notion.md`: Status Notification Functions 섹션 추가 (format_discord_summary, build_notion_status_update, message format tables, Notion property mapping table).
   - `docs/runbooks/test.md`: v04-05 green 상태 반영.
   - `docs/DOC_OWNERS.yml`: `status-notification` rule 추가 (`tools/status_notification.py` → `docs/runbooks/openclaw-notion.md`).
   - `docs/handoff/CURRENT_HANDOFF.md`: 이 업데이트.
4. Full test suite: **72 tests, 0 reds** — all v04 tests now green.

### Previous session: v04-04 Local Publish Then Rebuild -- Implemented

1. Created `tools/local_rebuild.py`:
   - `rebuild_after_ingest(ingest_result, root_path, db_path, dry_run)` — rebuild pipeline wrapper.
   - Dry-run returns 3 planned actions: `compile_wiki`, `index_fts`, `build_graph`.
   - Apply mode calls `compile_wiki.compile_for_source()` (includes FTS internally) then `build_graph.build_graph()`.
   - Partial failure policy: upstream failure → `skipped`; compile fail → `index_fts=skipped`, graph continues; graph fail → `status=partial`.
   - `source_type="local_document"` → existing compile_wiki reads Markdown/text directly (no HTML parsing).
   - Result JSON includes `wiki_path`, `source_id`, `actions[].status`, `summary` for v04-05 consumption.
2. Red test → Green: `tests/test_v04_local_rebuild.py` 1/1 pass.
3. Updated docs:
   - `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md`: Status → Implemented, checklist completed, Implementation Notes + Verification Results added.
   - `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`: v04-04 status → Implemented.
   - `docs/runbooks/rebuild-kb.md`: Local Rebuild After Ingest 섹션 추가 (usage, partial failure policy, dry-run format).
   - `docs/runbooks/local-storage.md`: 보류 범위에서 compile_wiki+graph 자동 호출 → 구현 완료로 갱신.
   - `docs/runbooks/test.md`: v04-04 green 상태 반영.
   - `docs/DOC_OWNERS.yml`: `local-rebuild` rule 추가 (`tools/local_rebuild.py` → `docs/runbooks/rebuild-kb.md`).
   - `docs/handoff/CURRENT_HANDOFF.md`: 이 업데이트.
4. Full test suite: 71 OK, 1 red (v04-05 미구현, 예정된 red 상태).

### Previous session: v04-03 Ingest Local Note CLI -- Implemented

1. Created `tools/ingest_local.py`:
   - CLI facade for OpenClaw/Discord request to Local Storage ingestion.
   - `--dry-run` and `--apply` modes, JSON result output.
   - Supports `--source-type`: `text_note`, `markdown_file`, `plain_text_file`, `url`, `binary_attachment`.
   - Reuses `tools.sync_storage` helpers: `safe_path_part`, `local_source_id`, `VALID_CATEGORIES`, `LOCAL_REQUEST_SOURCE_TYPES`.
   - Security: path traversal rejection, storage root existence check.
2. Red test → Green: `tests/test_v04_ingest_local_cli.py` 1/1 pass.
3. Updated docs:
   - `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`: Status → Implemented, checklist 전 항목 체크, Implementation Notes 추가.
   - `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`: v04-03 status → Implemented.
   - `docs/runbooks/local-storage.md`: Ingest Local CLI 섹션 추가 (사용법, 지원 타입, dry-run action 목록).
   - `docs/runbooks/test.md`: v04-03 green 상태 반영.
   - `docs/DOC_OWNERS.yml`: `ingest-local-cli` rule 추가 (`tools/ingest_local.py` → `docs/runbooks/local-storage.md`).
   - `docs/handoff/CURRENT_HANDOFF.md`: 이 업데이트.
4. Full test suite: 71 OK, 2 red (v04-04/05 미구현, 예정된 red 상태).

### Previous session: v04-02 OpenClaw Notion Control Contract -- Implemented
1. Added v04 red test files and documented them in active v04 plan files:
   - `tests/test_v04_openclaw_notion_control.py` -> `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md`
   - `tests/test_v04_ingest_local_cli.py` -> `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`
   - `tests/test_v04_local_rebuild.py` -> `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md`
   - `tests/test_v04_status_notification.py` -> `docs/plans/v04/2026-05-14-v04-05-status-notification.md`
2. Documented v04-01 tests in `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md`.
3. Tightened `tools/sync_storage.py` Local Storage behavior:
   - request `source_type` values such as `markdown_file` and `plain_text_file` normalize to DB `source_type = local_document`
   - missing storage root now fails with `local_storage_root_missing`
   - `canonical_path` path traversal remains rejected with `invalid_input`
4. Added `raw/local_storage/` to `.gitignore`.
5. Updated `docs/runbooks/local-storage.md` and `docs/runbooks/test.md` with the new safety rules and red test map.

### v0.4-01: Local Storage Foundation -- Implemented

1. Ran `tests/test_sync_storage.py` -> 10/11 pass, 1 fail.
   - Failing: `test_apply_rejects_canonical_path_outside_storage_root`
2. Fixed `tools/sync_storage.py`:
   - `write_local_source`: added path traversal security check (`.resolve()` + `.relative_to()`).
     Returns `status: "failed"`, `error_type: "invalid_input"` when `canonical_path` escapes `storage_root`.
   - `apply_sync`: new `had_invalid_input` flag; returns `status: "error"` (not `"partial"`) when any `invalid_input` failure occurs.
3. Updated docs:
   - `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md`: Status -> Implemented, all checklist items checked.
   - `docs/runbooks/local-storage.md`: result JSON status values documented (`ok | partial | error`), path traversal rejection example added.
   - `docs/handoff/CURRENT_HANDOFF.md`: this update.
4. All 11 tests pass.

### v0.4 plan restructuring (previous session)

1. Investigated Drive references across `docs`, `tools`, `tests`, and `config`.
2. Preserved Drive implementation and tests as legacy optional integration.
3. Added a new active v0.4 master plan:
   - `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
4. Marked old Drive-era master plan as historical:
   - `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`
5. Reframed v04-00 ingest contract for Local Storage result actions and local error codes.
6. Marked v04-01 Drive Write Foundation as Completed but Deferred.
7. Added new Local/Notion feature plans:
   - `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md`
   - `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md`
   - `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`
   - `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md`
   - `docs/plans/v04/2026-05-14-v04-05-status-notification.md`
   - `docs/plans/v04/2026-05-14-v04-legacy-drive-integration.md`
8. Added superseded/historical notices to old v04-02/03/04/05 Drive-era or pre-reframe plans.
9. Updated project profile, file inventory, v04 README, and ADR 0006 migration notes.
10. Cleaned up plan overlap:
   - moved old/superseded v04 plans into `docs/plans/v04/legacy/`
   - kept active v04 root files limited to the current feature map
   - added a responsibility boundary table to the active v0.4 master plan
   - narrowed v04-01/v04-03/v04-04/v04-05 scope so storage, CLI, rebuild, Notion status, and Discord summary are not all claiming the same work

## Drive Dependency Findings

Drive references now fall into two categories.

Legacy optional integration to keep:

- `tools/sync_drive.py`
- `tools/publish_drive.py`
- `tests/test_sync_drive.py`
- `tests/test_publish_drive.py`
- `tests/fixtures/drive_manifest.json`
- `tests/fixtures/drive_folders.yaml`
- `docs/specs/0003-google-drive-sync.md`
- `docs/runbooks/sync-drive.md`
- `docs/runbooks/publish-drive.md`
- `docs/adrs/0002-drive-is-canonical-source.md`
- `docs/adrs/0005-drive-write-scope-and-upload.md`
- v0.3 Drive plans

Drive-era v0.4 planning that was superseded:

- `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`
- `docs/plans/v04/legacy/2026-05-14-v04-02-ingest-discord-note-cli.md`
- `docs/plans/v04/legacy/2026-05-14-v04-03-openclaw-tool-adapter.md`
- `docs/plans/v04/legacy/2026-05-14-v04-04-publish-then-rebuild.md`
- `docs/plans/v04/legacy/2026-05-14-v04-05-discord-summary-notification.md`

## Active v0.4 Feature Map

| # | Plan | Status |
|---|---|---|
| 00 | `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` | Local contract reframed |
| 01 | `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md` | **Implemented** |
| 02 | `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md` | **Implemented** |
| 03 | `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md` | **Implemented** |
| 04 | `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md` | **Implemented** |
| 05 | `docs/plans/v04/2026-05-14-v04-05-status-notification.md` | **Implemented** |
| legacy | `docs/plans/v04/2026-05-14-v04-legacy-drive-integration.md` | Deferred |

## Active Plan Boundaries

| Plan | Owns | Does not own |
|---|---|---|
| v04-00 | request/result JSON, action/error names | implementation |
| v04-01 | storage layout/path/category/source_id foundation | OpenClaw request CLI, rebuild, Notion update |
| v04-02 | Notion schema/status/read-update contract | Discord message formatting, storage, rebuild |
| v04-03 | OpenClaw/Discord request -> local ingest CLI facade | storage rules, rebuild, Notion direct update |
| v04-04 | compile_wiki/index_fts/build_graph after successful ingest | local write/upsert, Discord text, Notion schema |
| v04-05 | final result -> Notion status update + Discord/OpenClaw summary | storage/rebuild execution |

## Local Storage Layout

```text
/mnt/d/ffixiv-bot-storage/
  incoming/
  sources/
    urls/
    documents/
    sheets/
    patch_notes/
    raid_guides/
    job_guides/
    static_docs/
    macros/
    bis_sheets/
    personal_notes/
  exports/
    markdown/
    text/
    html/
  manifests/
  archive/
```

## Standard Local Actions

- `validate_request`
- `write_local_source`
- `snapshot_raw`
- `upsert_source`
- `compile_wiki`
- `index_fts`
- `build_graph`
- `update_notion_status`

Legacy Drive actions:

- `upload_drive_file`
- `sync_drive`
- `drive_auth`
- `drive_download`
- `drive_export`

## Graphify + LLM Wiki Requirements

The default pipeline remains:

```text
원본 파일 감지
-> raw/local_storage snapshot 생성
-> sources DB upsert
-> compile_wiki.py 로 LLM Wiki 문서 생성
-> wiki_fts 색인
-> build_graph.py 로 graph nodes/edges 생성
-> search_kb.py 와 answer.py 에서 FTS + graph traversal 기반 답변
```

Do not introduce embedding/vector DB in the next task.

## Verification

Executed 2026-05-15:

```bash
python -m unittest tests.test_v04_ingest_local_cli -v
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

Results (current session: content_hash bugfix):

- Discord/OpenClaw E2E smoke test: **passed**
- ingest_local dry-run: **passed**
- ingest_local apply: **passed** (after content_hash fix)
- content_hash NOT NULL 누락 버그 발견 및 수정
- regression tests (x2) 추가: 1) INSERT content_hash 검증, 2) UPDATE content_hash 검증
- v04 ingest CLI tests: **3/3 green** (original dry-run + 2 content_hash regression tests)
- full suite: **73 tests, 0 reds** — +2 content_hash regression tests
- Google Drive: not touched

Previous verification (v04-05):

- v04-05 test: **green** (1/1 pass)
- full suite: **72 tests, 0 reds** — all v04 tests now green
- docs freshness: pending (will run finish_task.py as final gate)
- `tools/status_notification.py` is the new v04-05 implementation module.
- No Drive files were modified.
- `raw/local_storage/` remains untracked, generated content only.

## Next Work

1. **Integration / End-to-End testing** — Wire together all five tools into a single pipeline flow.
2. **OpenClaw agent integration** — Connect the tools to a real OpenClaw agent workflow.
3. **Operations** — Move beyond unittest into realistic dry-run → apply scenarios.
4. **v0.5 planning** — The next version should define features beyond the current pipeline (e.g., watchers, scheduling, multi-source GC).

## Do Not Touch Without Explicit Request

- Delete or reset Drive implementation files
- Delete Drive tests
- Modify `db/ffxiv.sqlite` manually
- Store original source files inside repo
- Upload original files to Notion
- Add embedding/vector DB
- Revert user changes
