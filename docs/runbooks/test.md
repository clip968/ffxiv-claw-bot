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

Covered contract:

- OpenClaw Source Processing Skill document exists and names the required command/source-type/Notion payload rules.
- Validation errors print JSON to stdout for missing `--body`, missing `--url`, missing `--local-path`, missing local files, and simultaneous `--apply` + `--dry-run`.
- Dry-run prints the v0.5 JSON contract, returns `status=skipped`, skips side-effect actions, and does not create storage directories or SQLite DB files.
- Direct script execution via `python tools/process_source.py ...` works and prints JSON.
- `text_note` apply writes a Local Storage source, raw snapshot, source DB row, and returns `source_id`, `canonical_path`, `local_source_path`, `raw_path`, and `content_hash`.
- `markdown_file` apply reads `--local-path`, writes the content to Local Storage, and creates a raw snapshot.
- `plain_text_file` apply reads `--local-path`, writes the content to a canonical `.md` Local Storage path, and creates a `.md` raw snapshot.
- `url` apply fetches exactly one mocked URL, writes fetched text to Local Storage, creates a raw snapshot, and skips rebuild until v05-06.
- URL fetch supports mocked `text/html`, `text/plain`, `application/json`, `+json`, HTTP failure, and unsupported content-type behavior.
- CLI `--title` overrides fetched URL title.
- URL fetch failure does not write Local Storage files or DB rows.
- ingest failure returns `status=error`, `graph_status=skipped`, and a skipped rebuild action.

Out of scope for these tests:

- wiki/FTS/graph rebuild
- Notion payload generation beyond dry-run/error skeleton fields

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

Full suite: **117 tests, 0 reds** (2026-05-16, +7 v05-05 URL integration tests).

## pytest

현재 레포에는 pytest 설정이나 requirements가 없다. 따라서 pytest를 기본 테스트 명령으로 쓰지 않는다.

pytest가 필요해지면 dependency와 실행 방식을 별도 plan/spec에서 먼저 정한다.
