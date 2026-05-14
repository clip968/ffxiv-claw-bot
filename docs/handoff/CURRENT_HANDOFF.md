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

1. Google Drive 의존 지점을 조사했다.
   - 구현: `tools/sync_drive.py`, `tools/publish_drive.py`
   - 테스트: `tests/test_sync_drive.py`, `tests/test_publish_drive.py`, `tests/test_compile_wiki.py`
   - fixture/config: `tests/fixtures/drive_manifest.json`, `tests/fixtures/drive_folders.yaml`
   - docs: Drive canonical ADR/spec/runbook/v0.3 plans/v0.4 Drive ingest plans/handoff/profile/inventory
2. ADR 0006을 추가해 Local Storage + Notion direct control 결정을 기록했다.
3. ADR 0002와 ADR 0005를 기본 운영 경로 기준으로 superseded/legacy optional integration 상태로 정리했다.
4. `docs/specs/0003-google-drive-sync.md`를 Legacy / Deferred optional integration spec으로 표시했다.
5. v0.4 master plan과 v0.4-02 plan을 Local Storage 기본 경로로 갱신했다.
6. `docs/runbooks/local-storage.md`와 `docs/runbooks/openclaw-notion.md`를 추가했다.
7. `tools/sync_storage.py` dry-run skeleton을 추가했다.
8. `tests/fixtures/storage_manifest.json`과 `tests/test_sync_storage.py`를 추가했다.

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

현재 구현은 dry-run skeleton이다.

```bash
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json
```

지원:

- manifest load
- DB의 `local://<canonical_path>` source와 비교
- `new`, `changed`, `unchanged`, `skipped` 분류
- planned `raw/local_storage/<category>/<safe_title>__<source_id>.<ext>` 생성
- JSON result 출력
- dry-run에서 raw 파일 또는 DB를 쓰지 않음

보류:

- `/mnt/d/ffixiv-bot-storage/sources/<category>/...` 원본 쓰기
- `raw/local_storage` snapshot apply
- `sources` DB upsert
- `compile_wiki.py`와 `build_graph.py` 자동 연결
- Notion 상태판 실제 update

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
```

결과:

- `tests.test_sync_storage`: 4 tests OK
- `sync_storage.py --dry-run`: JSON 출력 확인
- full unittest discover: 58 tests OK
- docs freshness: ok

작업 종료 전 마지막 게이트:

```bash
python scripts/finish_task.py
```

## 다음 작업

1. `sync_storage.py --apply` 설계와 TDD 구현
2. `local_file` 또는 `local_document` source_type을 `compile_wiki.py` Markdown/text 처리 경로에 연결
3. `raw/local_storage` snapshot 쓰기와 `sources` DB upsert 구현
4. `compile_wiki.py` + `build_graph.py` 자동 rebuild 연결
5. OpenClaw가 Notion 상태판을 읽고 쓰는 adapter 설계
6. v04-03, v04-04, v04-05 plan을 Local Storage/Notion 기준으로 재정의

## 건드리지 말아야 할 것

명시 요청 없이는 다음을 건드리지 않는다.

- 기존 Drive 구현 삭제 또는 리셋
- `db/ffxiv.sqlite` 실제 데이터
- 원본 파일 저장소 `/mnt/d/ffixiv-bot-storage`의 실제 파일
- embedding/vector DB 도입
- 사용자 변경 되돌리기
