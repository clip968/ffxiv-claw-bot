# CURRENT_HANDOFF

## Repo

- GitHub: https://github.com/clip968/ffxiv-claw-bot
- Local path: `/mnt/d/programming/ffxiv-claw-bot`
- Current branch: `main`

## Current Phase

v0.3 Google Drive sync와 v0.4-01 Drive write foundation은 구현 완료 상태로 보존한다.

2026-05-14 현재 기본 운영 경로는 Google Drive 중심이 아니라 `/mnt/d/ffixiv-bot-storage` 기반 Local Storage + OpenClaw Notion direct control 구조다.

Google Drive 기반 sync/write 구조는 Legacy / Deferred / Optional Integration이다. 삭제하지 않는다.

## 이번 세션 완료

### v0.4-02 `--apply` 모드 구현

1. `tools/sync_storage.py --apply` 모드 구현
   - `write_local_source`: manifest body를 `/mnt/d/ffixiv-bot-storage/sources/<category>/...`에 쓰기
   - `snapshot_raw`: `raw/local_storage/<category>/...`에 처리용 snapshot 생성
   - `upsert_source`: `db/ffxiv.sqlite` sources 테이블에 `local://<canonical_path>` upsert
   - `unchanged`/`skipped` 항목은 apply에서 건너뜀
   - `write_local_source`는 body가 없고 대상 파일도 없으면 failed 처리
2. `tests/test_sync_storage.py`에 6개 apply 테스트 추가
   - `test_apply_writes_local_source_to_storage_root`
   - `test_apply_creates_raw_snapshot`
   - `test_apply_upserts_source_db`
   - `test_apply_rejects_missing_body_for_new_items`
   - `test_apply_cli_outputs_json_result`
   - `test_apply_skipped_for_missing_storage_root_source`
3. 관련 문서 갱신
   - `docs/plans/v04/2026-05-14-v04-02-ingest-discord-note-cli.md`: 체크리스트 업데이트, verification 명령 추가
   - `docs/runbooks/local-storage.md`: Manifest Sync Apply 섹션 추가, 보류 범위에서 write_local_source/snapshot_raw/upsert_source 제거
   - `docs/handoff/CURRENT_HANDOFF.md`: 현재 세션

### Phase A-1: `compile_wiki.py` `local_file`/`local_document` 연결

1. `compile_wiki.py` 조건 확장: `drive_document` → `drive_document`, `local_file`, `local_document` 모두 HTML 파싱 없이 raw content 그대로 사용
2. `tests/test_compile_wiki.py`에 `local_file` source_type 테스트 추가 (HTML entity 보존 검증)
3. 관련 문서 갱신
   - `docs/specs/0001-local-kb-pipeline.md`: source_type별 처리 규칙 갱신
   - `docs/runbooks/rebuild-kb.md`: "예정" → "완료" 상태 반영
   - `docs/handoff/CURRENT_HANDOFF.md`: 현재 세션

### Docs-first workflow 템플릿화 개선

1. `docs/WORKFLOW.md`에 Planner / Executor 분리 원칙을 추가했다.
2. `docs/templates/PLAN_TEMPLATE.md`에 Allowed Files, Docs Required, Red Test, Verification 섹션을 추가했다.
3. `docs/plans/README.md`에 상위 모델 task 분해 -> executor 단일 task 수행 -> reviewer/CI 판정 흐름을 명시했다.
4. `docs/runbooks/finish-task.md`에 executor agent 실패 처리와 plan/handoff-only 문서 갱신 금지 원칙을 추가했다.
5. `docs/templates/HANDOFF_TEMPLATE.md`와 `.github/pull_request_template.md`에 plan/executor scope와 docs freshness evidence 항목을 추가했다.
6. `docs-first-workflow/` 템플릿에도 같은 개선을 반영했다.

## 기본 Source of Truth

- 원본 파일 저장소: `/mnt/d/ffixiv-bot-storage`
- 문서 source of truth: repo `docs/`
- 처리용 snapshot: `raw/local_storage`
- 파생 산출물: `wiki`, `graph`, `db/ffxiv.sqlite`
- Notion: OpenClaw가 직접 읽고 쓰는 작업 관리, 상태판, 문서 인덱스 계층

Notion에는 원본 파일 자체를 올리지 않는다. Notion에는 local path, category, source_id, processing status, wiki path, graph status, last error만 기록한다.

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

## sync_storage.py 현재 범위

현재 구현은 dry-run과 --apply를 모두 지원한다.

```bash
# planning (dry-run)
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json

# execution (apply)
python tools/sync_storage.py --apply --manifest tests/fixtures/storage_manifest.json
```

### dry-run 지원

- manifest load
- DB의 `local://<canonical_path>` source와 비교
- `new`, `changed`, `unchanged`, `skipped` 분류
- planned `raw/local_storage/<category>/<safe_title>__<source_id>.<ext>` 생성
- JSON result 출력
- dry-run에서 raw 파일 또는 DB를 쓰지 않음

### --apply 지원

- `write_local_source`: manifest body를 저장소 `/mnt/d/ffixiv-bot-storage/sources/<category>/...`에 쓰기
- `snapshot_raw`: `raw/local_storage/<category>/...`에 처리용 snapshot 생성
- `upsert_source`: `db/ffxiv.sqlite` sources 테이블에 `local://<canonical_path>` upsert
- `unchanged`/`skipped` 항목은 apply 시 건너뜀
- `write_local_source`는 body가 없고 대상 파일도 없으면 failed 처리

보류:

- `compile_wiki.py`와 `build_graph.py` 자동 연결 (향후 작업)
- Notion 상태판 실제 update (v0.4-02 범위 아님. OpenClaw adapter 단계에서 sync_storage.py JSON 결과를 읽어 처리)

## Graphify + LLM Wiki 유지 조건

Google Drive를 기본 경로에서 제외해도 다음 구조는 유지한다.

```text
원본 파일 감지
-> raw/local_storage snapshot 생성
-> sources DB upsert
-> compile_wiki.py 로 LLM Wiki 문서 생성
-> wiki_fts 색인
-> build_graph.py 로 graph nodes/edges 생성
-> search_kb.py 와 answer.py 에서 FTS + graph traversal 기반 답변
```

embedding/vector DB는 아직 도입하지 않는다.

## Legacy / Deferred

다음 파일은 삭제하지 않는다.

- `tools/sync_drive.py`
- `tools/publish_drive.py`
- `tests/test_sync_drive.py`
- `tests/test_publish_drive.py`
- `docs/specs/0003-google-drive-sync.md`
- `docs/runbooks/sync-drive.md`
- `docs/runbooks/publish-drive.md`
- `docs/adrs/0002-drive-is-canonical-source.md`
- `docs/adrs/0005-drive-write-scope-and-upload.md`

Drive 기반 sync/write 구조는 v0.4-01까지 구현되어 있으나 현재 기본 운영 경로에서는 사용하지 않는다. 향후 외부 클라우드 동기화가 필요할 때 optional integration으로 재검토한다.

## 검증

이번 세션에서 확인한 명령:

```bash
python -m unittest tests.test_sync_storage
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
cd docs-first-workflow && python -m unittest discover -s tests -p "test_*.py"
cd docs-first-workflow && python scripts/check_docs_freshness.py --all
```

결과:

- `tests.test_sync_storage`: 10 tests OK
- `sync_storage.py --dry-run`: JSON 출력 확인
- `sync_storage.py --apply`: JSON 결과 확인 (write_local_source, snapshot_raw, upsert_source)
- full unittest discover: 58 tests OK
- docs freshness: ok
- `docs-first-workflow` focused unittest/docs freshness/finish_task: OK

작업 종료 전 마지막 게이트:

```bash
python scripts/finish_task.py
```

## 다음 작업

v04-02 `--apply` 구현이 완료되어, 현재 기준 권장 진행 순서는 다음과 같다.

**Phase A: 즉시 구현 가능 (plan 재정의 불필요)**

1. ✅ `local_file`/`local_document` source_type을 `compile_wiki.py` Markdown/text 처리 경로에 연결 — **완료**
   - sync_storage.py --apply가 raw/local_storage/ snapshot을 생성할 수 있게 되었고,
   - compile_wiki.py가 이 snapshot을 받아 wiki 문서를 생성해야 rebuild chain이 성립한다.
2. `compile_wiki.py` → `build_graph.py` 자동 rebuild 연결

**Phase B: Local Storage/Notion 기준 plan 재정의 후 진행**

2. v04-03, v04-04, v04-05 plan을 Drive 중심 → Local Storage/Notion 기준으로 재정의
   - 현재 v04-03/04/05 plan은 `sync_drive.py`, `--publish-drive`, `drive_file_id`, `Drive link` 등 Drive 기준 설계가 남아 있어
     그대로 구현하면 Local Storage/Notion 전환 방향과 충돌한다.
   - plan 재정의 후 구현 순서는 재정의된 plan에서 결정한다.
3. 재정의된 v04-03 plan에 따라 OpenClaw Notion 상태판 adapter 설계 및 구현
4. rebuild chain: compile_wiki.py → build_graph.py 자동 연결

## 건드리지 말아야 할 것

명시 요청 없이는 다음을 건드리지 않는다.

- 기존 Drive 구현 삭제 또는 리셋
- `db/ffxiv.sqlite` 실제 데이터
- 원본 파일 저장소 `/mnt/d/ffixiv-bot-storage`의 실제 파일
- embedding/vector DB 도입
- 사용자 변경 되돌리기
