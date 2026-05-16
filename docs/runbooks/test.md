# Test Runbook

## 기본 테스트

현재 레포에서 실제 가능한 기본 테스트 명령은 `unittest`다.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

검증 결과는 작업 종료 시 `docs/handoff/CURRENT_HANDOFF.md`에 기록한다.

## 특정 테스트

Local Storage sync dry-run 테스트:

```bash
python -m unittest tests.test_sync_storage
```

Drive sync dry-run 테스트:

```bash
python -m unittest tests.test_sync_drive
```

## v0.4 Red Tests

The active v0.4 plan files name their red tests. These tests are expected to fail until the matching implementation slice is written.

```bash
python -m unittest tests.test_v04_openclaw_notion_control
python -m unittest tests.test_v04_ingest_local_cli
python -m unittest tests.test_v04_local_rebuild
python -m unittest tests.test_v04_status_notification
```

Current status:

- `tests/test_v04_openclaw_notion_control.py` -> `tools/openclaw_notion_control.py` (**Green** 2026-05-15)
- `tests/test_v04_ingest_local_cli.py` -> `tools/ingest_local.py` (**Green** 2026-05-15, 3 tests including content_hash regression)
- `tests/test_v04_local_rebuild.py` -> `tools/local_rebuild.py` (**Green** 2026-05-15)
- `tests/test_v04_status_notification.py` -> `tools/status_notification.py` (**Green** 2026-05-16, 4 tests including Graph Built promotion)

Full suite: **98 tests, 0 reds** (2026-05-16, +3 Graph Built promotion regression tests).

### Graph Built Status Promotion Tests

New in `tests/test_v04_status_notification.py`:

- `test_ok_with_graph_built_promotes_status_and_excludes_body_attachments_drive` — verifies `status=ok` + `graph_status=built` → Notion Status = `Graph Built`; confirms `body`, `attachments`, `drive_url` are excluded from payload.
- `test_ok_without_graph_built_stays_indexed` — verifies `status=ok` + `graph_status=pending` → Notion Status = `Indexed`, Graph Status = `Pending`.
- `test_ok_missing_graph_status_defaults_indexed` — verifies `status=ok` with no `graph_status` → Notion Status = `Indexed`, no Graph Status key.

These tests prevent the `Status=Indexed` + `Graph Status=Built` contradiction from recurring.

### FTS5 Query Sanitization Tests

New in `tests/test_search_kb.py`:

- **SanitizeFtsQueryTests** (13 tests): Each FTS5-special character (`@`, `/`, `"`, `(`, `)`, `-`, `+`, `*`, `^`, `:`) is removed by `sanitize_fts_query()`. Korean text, underscores, and whitespace are preserved.
- **FormatQueryTests** (2 tests): Empty query is rejected, input is sanitized before FTS5 MATCH.
- **AnswerBuildContextsNoCrashTests** (7 tests): Real paths (`tools/ingest_local.py`, `foo/bar baz`), special chars (`@`, `"`), OpenClaw/Discord input, `discord_agent_smoke_test` — all return results or `"찾을 수 없습니다"` without crashing.

These tests prevent the `sqlite3.OperationalError: FTS5 syntax error near "@[/]"` bug from recurring (see answer.py E2E smoke test findings).

**한국어 검색 한계**: FTS5 `unicode61` tokenizer는 CJK unigram 분할을 지원하지 않으므로, 한국어 검색어가 의도대로 매칭되지 않을 수 있습니다. 이는 tokenizer의 근본적인 한계이며 버그가 아닙니다.

### content_hash Regression Tests

New in `tests/test_v04_ingest_local_cli.py`:

- `test_text_note_apply_stores_content_hash_on_insert` — runs `--apply`, verifies `sources.content_hash` is not NULL and matches SHA-256 of the body.
- `test_text_note_apply_stores_content_hash_on_update` — runs `--apply` twice with different bodies, verifies `content_hash` matches SHA-256 of the second body.

These tests prevent the `NOT NULL constraint failed: sources.content_hash` bug from recurring (see v04 E2E smoke test findings).

When these red tests are present and not yet implemented, full unittest discover is expected to fail on those planned v0.4 slices.

## v0.5 Source Processing Tests

## v0.6 Multi-format Source Processing Tests

Focused v0.6 extractor tests:

```bash
python -m unittest tests.test_v06_extractors -v
```

Current status:

- `V06ExtractorModelTests` -> `src/source_processing/models.py`, `src/source_processing/errors.py` (**Green** 2026-05-16, 5 tests)
- `V06ExtractorRegistryTests` -> `src/source_processing/extractor_registry.py`, `src/source_processing/extractors/__init__.py` (**Green** 2026-05-16, 8 tests)
- `V06TextMarkdownHtmlExtractorTests` -> `src/source_processing/extractors/text.py`, `markdown.py`, `html.py` (**Green** 2026-05-16, 8 tests)
- `V06CsvExtractorTests` -> `src/source_processing/extractors/csv.py` (**Green** 2026-05-16, 5 tests)
- `V06XlsxExtractorTests` -> `src/source_processing/extractors/xlsx.py` (**Green** 2026-05-16, 6 tests)

Red/green notes:

- v06-01 red check: `python -m unittest tests.test_v06_extractors -v` failed with 5 expected `ModuleNotFoundError: No module named 'src'` errors.
- v06-01 green check: `python -m unittest tests.test_v06_extractors -v` passed 5 tests after adding the shared model and error layer.
- v06-02 red check: `python -m unittest tests.test_v06_extractors.V06ExtractorRegistryTests -v` failed with 8 expected registry module import errors.
- v06-02 green check: `python -m unittest tests.test_v06_extractors -v` passed 13 tests after adding registry and stub extractor mapping.
- v06-03 red check: `python -m unittest tests.test_v06_extractors.V06TextMarkdownHtmlExtractorTests -v` failed with expected missing concrete modules and registry stub content failure.
- v06-03 green check: `python -m unittest tests.test_v06_extractors -v` passed 21 tests after implementing text, markdown, and generic HTML extractors.
- v06-03 Lodestone regression: `python -m unittest tests.test_v05_1_lodestone_extractor -v` passed 5 tests.
- v06-04 red check: `python -m unittest tests.test_v06_extractors.V06CsvExtractorTests -v` failed with expected missing CSV module and registry stub content failure.
- v06-04 green check: `python -m unittest tests.test_v06_extractors -v` passed 26 tests after implementing CSV extraction.
- v06-05 red check: `python -m unittest tests.test_v06_extractors.V06XlsxExtractorTests -v` failed with expected missing XLSX module and registry stub content failure.
- v06-05 green check: `python -m unittest tests.test_v06_extractors -v` passed 32 tests after implementing standard-library XLSX extraction.

v0.5 source processing tests:

```bash
python -m unittest tests.test_v05_fetch_url -v
python -m unittest tests.test_v05_process_source -v
```

Current status:

- `V05OpenClawSkillDocTests` -> `docs/skills/ffxiv-source-processing.md` (**Green** 2026-05-16)
- `V05ProcessSourceSkeletonTests` -> `tools/process_source.py` (**Green** 2026-05-16)
- `V05ProcessSourceLocalIntegrationTests` -> `tools/process_source.py`, `tools/ingest_local.py` (**Green** 2026-05-16)
- `V05FetchUrlTests` -> `tools/fetch_url.py` (**Green** 2026-05-16)
- `V05ProcessSourceUrlIntegrationTests` -> `tools/process_source.py`, `tools/fetch_url.py`, `tools/ingest_local.py` (**Green** 2026-05-16)
- `V05ProcessSourceRebuildIntegrationTests` -> `tools/process_source.py`, `tools/local_rebuild.py` (**Green** 2026-05-16)
- `V05ProcessSourceNotionPayloadIntegrationTests` -> `tools/process_source.py`, `tools/status_notification.py` (**Green** 2026-05-16)
- `V05ProcessSourceRunbookTests` -> `docs/runbooks/process-source.md` (**Green** 2026-05-16)

Test maintenance note:

- `tests/test_v05_process_source.py` uses `ProcessSourceTempCase` for integration-style cases that need a temp directory, storage root, repo root, initialized SQLite DB, and `process_source.py` root override. The dry-run side-effect test keeps its own temp paths because it verifies that dry-run does not create those paths.

Covered contract:

- OpenClaw Source Processing Skill document exists and names the required command/source-type/Notion payload rules.
- Validation errors print JSON to stdout for missing `--body`, missing `--url`, missing `--local-path`, missing local files, and simultaneous `--apply` + `--dry-run`.
- Dry-run prints the v0.5 JSON contract, returns `status=skipped`, skips side-effect actions, and does not create storage directories or SQLite DB files.
- Direct script execution via `python tools/process_source.py ...` works and prints JSON.
- `text_note` apply writes a Local Storage source, raw snapshot, source DB row, rebuilds wiki/FTS/graph, and returns `source_id`, `canonical_path`, `local_source_path`, `raw_path`, `content_hash`, `wiki_path`, and `graph_status=built`.
- Duplicate `text_note` apply for the same canonical source reuses the existing `source_id`, updates the Local Storage file, raw snapshot, and `sources` row, and does not return `status=skipped`.
- `markdown_file` apply reads `--local-path`, writes the content to Local Storage, and creates a raw snapshot.
- `plain_text_file` apply reads `--local-path`, writes the content to a canonical `.md` Local Storage path, and creates a `.md` raw snapshot.
- `url` apply fetches exactly one mocked URL, writes fetched text to Local Storage, creates a raw snapshot, and rebuilds wiki/FTS/graph.
- URL fetch supports mocked `text/html`, `text/plain`, `application/json`, `+json`, HTTP failure, and unsupported content-type behavior.
- CLI `--title` overrides fetched URL title.
- URL fetch failure does not write Local Storage files or DB rows.
- ingest failure returns `status=error`, `graph_status=skipped`, and skips rebuild.
- rebuild failure returns `status=partial`, keeps saved source metadata, and records failed rebuild actions.
- graph failure sets `graph_status=failed` without discarding wiki/FTS output.
- successful apply includes a safe `notion_update` payload with `Status`, `Graph Status`, `Source ID`, `Local Source Path`, `Wiki Path`, and `Last Processed`.
- `notion_update` excludes original body text, raw HTML, attachments, and binary data.

Out of scope for these tests:

- Notion API calls
- Notion polling
- crawler/scheduler behavior

v05-05 regression tests added:

- `tests/test_v05_fetch_url.py`
  - `test_fetch_html_extracts_title_and_visible_text`
  - `test_fetch_plain_text_uses_url_fallback_title`
  - `test_fetch_unsupported_content_type_raises_url_fetch_error`
  - `test_fetch_http_error_raises_url_fetch_error`
- `tests/test_v05_process_source.py`
  - `test_process_url_ok_fetches_single_url_and_ingests_local_storage`
  - `test_process_url_prefers_cli_title_over_fetched_title`
  - `test_process_url_fetch_fails_returns_error_without_ingest`

v05-04 regression tests added:

- `test_process_text_note_ok`
- `test_process_markdown_file_ok`
- `test_process_plain_text_file_ok`
- `test_process_ingest_error_skips_rebuild`

Full suite before v05-06: **117 tests, 0 reds** (2026-05-16, +7 v05-05 URL integration tests).

v05-06/v05-07/v05-08 regression tests added:

- `test_process_rebuild_error_returns_partial`
- `test_process_graph_failure_sets_graph_status_failed`
- `test_process_notion_payload_excludes_body`
- `test_process_notion_payload_ok_graph_pending`
- `test_process_source_runbook_documents_completed_v05_workflow`

Full suite target after v05-08: **122 tests, 0 reds**.

## v05.1 Source Processing Hardening Tests

v05.1 Lodestone extractor tests:

```bash
python -m unittest tests.test_v05_1_lodestone_extractor -v
```

Current status:

- `V051LodestoneExtractorTests` -> `tools/extractors/lodestone.py` (**Green** 2026-05-16, 5 tests)
- `V05FetchUrlTests` v05.1 routing coverage -> `tools/fetch_url.py` (**Green** 2026-05-16, 6 tests)
- `V05ProcessSourceUrlIntegrationTests.test_process_lodestone_url_records_lodestone_extractor_action` -> `tools/process_source.py` (**Green** 2026-05-16)
- `V05ProcessSourceRunbookTests` v05.1 boundary coverage -> `docs/runbooks/process-source.md` (**Green** 2026-05-16, 6 tests)

Covered contract:

- Official Lodestone regional URLs under `/lodestone/` are detected.
- `.news__detail__wrapper` is the extraction boundary.
- Patch title and body are extracted from a local Lodestone-like 7.5 fixture.
- Navigation, footer, script/style, share UI, and raw HTML tags are excluded.
- Missing or empty article body raises `LodestoneExtractionError`.

v05.1-02 red result:

- `python -m unittest tests.test_v05_1_lodestone_extractor -v`: expected red confirmed before implementation, 5 failures because `tools.extractors.lodestone` did not exist.

v05.1-04 and v05.1-05 remain pending:

- Completed 2026-05-16.
- `fetch_url.py` routes Lodestone HTML URLs through the Lodestone extractor before generic HTML extraction.
- `fetch_single_url()` now returns `extractor=lodestone`, `generic_html`, `text`, or `json`.
- `process_source.py` records the returned extractor metadata in the `fetch_url` action.
- `process-source.md` names `tools/process_source.py` as the official source processing entrypoint.
- `process-source.md` warns that `ingest_local.py --body "/path/file.md"` stores the path string itself, not the file contents.
- `process-source.md` documents `tools/local_rebuild.py` as library-only for normal workflow.
- `process-source.md` documents `tools/status_notification.py` as payload-builder-only and not a Notion write CLI.
- `process-source.md` states `result["notion_update"]` is not already applied and `process_source.py` itself does not call the Notion API.

v05.1-04 red result:

- `python -m unittest tests.test_v05_fetch_url -v`: expected red confirmed before implementation; failures were missing `extractor` metadata and Lodestone HTML still using the generic title path.

v05.1-05 red result:

- `python -m unittest tests.test_v05_process_source.V05ProcessSourceUrlIntegrationTests.test_process_lodestone_url_records_lodestone_extractor_action -v`: expected red confirmed before implementation; failure was missing `fetch_url.extractor`.

v05.1-07 red result:

- `python -m unittest tests.test_v05_process_source.V05ProcessSourceRunbookTests -v`: expected red confirmed before runbook update; 5 boundary tests failed because official entrypoint, helper misuse, library-only, payload-builder-only, and Notion auto-apply wording was missing.

Full suite after v05.1-03: **128 tests, 0 reds**.

Focused green results after v05.1-04/v05.1-05:

- `python -m unittest tests.test_v05_fetch_url -v`: **6 tests, OK**.
- `python -m unittest tests.test_v05_process_source -v`: **22 tests, OK**.
- `python -m unittest tests.test_v05_1_lodestone_extractor -v`: **5 tests, OK**.
- `python -m unittest tests.test_v05_process_source.V05ProcessSourceRunbookTests -v`: **6 tests, OK**.

Full suite after v05.1-04/v05.1-05: **131 tests, 0 reds**.

Full suite after v05.1-06/v05.1-07/v05.1-08: **136 tests, 0 reds**.

## pytest

현재 레포에는 pytest 설정이나 requirements가 없다. 따라서 pytest를 기본 테스트 명령으로 쓰지 않는다.

pytest가 필요해지면 dependency와 실행 방식을 별도 plan/spec에서 먼저 정한다.
