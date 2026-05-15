# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.4 implementation is complete. All five v04 feature plans are Implemented.

v0.5 planning is complete. The v05 Source Processing Pipeline spec and all 8 task plans are documented.

v0.5-02 and v0.5-03 are implemented:

- `docs/skills/ffxiv-source-processing.md` documents the OpenClaw Source Processing Skill contract.
- `tools/process_source.py` exists with CLI parsing, validation, dry-run behavior, and JSON stdout contract.
- Actual apply-mode ingest, URL fetch, rebuild, and Notion payload generation remain v0.5-04+ work and are intentionally not implemented yet.

v0.4 planning has been reframed from Google Drive write/publish to Local Storage + OpenClaw Notion direct control.

The v05 phase transitions from multi-tool manual wiring to a unified `process_source.py` entrypoint that takes a single source through ingest → rebuild → status payload in one call. The current implementation is only the v0.5-03 skeleton: validation and dry-run are usable, while apply-mode processing is still blocked until v0.5-04+.

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
7. `docs/adrs/0006-local-storage-and-notion-control.md`
8. `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
9. `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
10. `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md`
11. `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md`
12. `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`
13. `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md`
14. `docs/plans/v04/2026-05-14-v04-05-status-notification.md`
15. `docs/runbooks/rebuild-kb.md`
16. `docs/runbooks/local-storage.md`
17. `docs/runbooks/openclaw-notion.md`
- `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`
- `docs/specs/0003-google-drive-sync.md`
- `docs/runbooks/sync-drive.md`
- `docs/runbooks/publish-drive.md`

## This Session

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
