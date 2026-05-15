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
- `tests/test_v04_status_notification.py` -> `tools/status_notification.py` (**Green** 2026-05-15)

Full suite: **95 tests, 0 reds** (2026-05-15, +22 FTS5 syntax regression tests).

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

## pytest

현재 레포에는 pytest 설정이나 requirements가 없다. 따라서 pytest를 기본 테스트 명령으로 쓰지 않는다.

pytest가 필요해지면 dependency와 실행 방식을 별도 plan/spec에서 먼저 정한다.
