# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.4 implementation is complete. All five v04 feature plans are Implemented.

v0.4 planning has been reframed from Google Drive write/publish to Local Storage + OpenClaw Notion direct control.

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
5. `docs/adrs/0006-local-storage-and-notion-control.md`
6. `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
7. `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
8. `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md`
9. `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md`
10. `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`
11. `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md`
12. `docs/plans/v04/2026-05-14-v04-05-status-notification.md`
13. `docs/runbooks/rebuild-kb.md`
14. `docs/runbooks/local-storage.md`
15. `docs/runbooks/openclaw-notion.md`
- `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`
- `docs/specs/0003-google-drive-sync.md`
- `docs/runbooks/sync-drive.md`
- `docs/runbooks/publish-drive.md`

## This Session

### Current session: v04-05 Status Notification -- Implemented

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
python -m unittest tests.test_v04_status_notification -v
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

Results:

- v04-05 test: **green** (1/1 pass)
- full suite: **72 tests, 0 reds** — all v04 tests now green
- docs freshness: pending (will run finish_task.py as final gate)
- `tools/status_notification.py` is the new v04-05 implementation module.
- No Drive files were modified.
- `raw/local_storage/` remains untracked, generated content only.

## Next Work

All five v04 feature plans are now **Implemented**. v0.4 core pipeline is complete:

```text
Discord/OpenClaw 저장 요청
-> validate_request
-> local source write
-> raw snapshot
-> DB upsert
-> compile_wiki / index_fts / build_graph
-> Notion status update + Discord summary
```

Recommended next direction:

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
