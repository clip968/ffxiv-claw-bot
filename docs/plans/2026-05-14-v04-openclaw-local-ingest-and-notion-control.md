# v0.4 OpenClaw Local Ingest and Notion Control

Spec:
- `docs/adrs/0006-local-storage-and-notion-control.md`
- `docs/runbooks/local-storage.md`
- `docs/runbooks/openclaw-notion.md`
- Legacy reference: `docs/specs/0003-google-drive-sync.md`

## Status

v0.4의 기본 운영 경로는 Google Drive write/publish가 아니다.

기본 source of truth는 사용자가 관리하는 로컬 원본 파일 저장소 `/mnt/d/ffixiv-bot-storage`다. Notion은 OpenClaw가 직접 읽고 쓰는 작업 관리, 상태판, 문서 인덱스 계층이며 파일 저장소가 아니다. repo `docs/`는 구현 계약, ADR, plan, runbook, handoff의 문서 source of truth다.

Google Drive 기반 `sync_drive.py`, `publish_drive.py`, 관련 테스트와 runbook은 삭제하지 않는다. 이들은 v0.3/v0.4-01에서 구현된 Legacy / Deferred / Optional Integration으로 유지한다.

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

역할:

- `incoming/`: 아직 분류하지 않은 임시 파일
- `sources/`: 사용자가 관리하는 원본 파일
- `exports/`: xlsx, pdf, docx 등에서 추출한 md/txt/html 변환본
- `manifests/`: 테스트와 dry-run용 manifest JSON
- `archive/`: 더 이상 활성 사용하지 않지만 보존할 자료

## Default Pipeline

```text
Discord/OpenClaw 저장 요청 또는 Notion 상태판 처리 대상
-> validate_request
-> /mnt/d/ffixiv-bot-storage/sources/<category>/ 원본 저장 또는 기존 local path 확인
-> raw/local_storage/<category>/ 처리용 snapshot 생성
-> db/ffxiv.sqlite sources upsert
-> compile_wiki.py 로 LLM Wiki markdown 생성 또는 갱신
-> wiki_fts 색인 갱신
-> build_graph.py 로 graph nodes/edges 생성
-> Notion 상태판에 처리 결과, 실패 사유, 다음 액션 기록
-> Discord/OpenClaw 결과 메시지
```

`raw/local_storage`, `wiki`, `graph`, `db/ffxiv.sqlite`는 파생 계층이다. 원본 파일을 repo 내부에 대량 저장하지 않는다.

## Standard Result Actions

기본 Local Storage ingest result는 다음 action 이름을 표준으로 사용한다.

- `validate_request`
- `write_local_source`
- `snapshot_raw`
- `upsert_source`
- `compile_wiki`
- `index_fts`
- `build_graph`
- `update_notion_status`

Drive 전용 action은 legacy plan에서만 사용한다.

- `upload_drive_file`
- `sync_drive`
- `drive_auth`
- `drive_download`
- `drive_export`

## Standard Error Codes

기본 오류 코드:

- `invalid_input`
- `unsupported_attachment`
- `local_storage_root_missing`
- `local_write_failed`
- `source_upsert_failed`
- `rebuild_failed`
- `notion_update_failed`

Drive legacy 오류 코드:

- `drive_auth_missing`
- `drive_write_failed`

## Feature Plans

| # | Plan | Status |
|---|---|---|
| 00 | `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` | [x] Local Storage result contract로 정리 완료 |
| 01 | `docs/plans/v04/2026-05-14-v04-01-local-storage-foundation.md` | [x] **Implemented** — sync_storage.py, path traversal 보안, manifest apply |
| 02 | `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md` | [x] **Implemented** — build_notion_update(), CLI→Notion status mapping |
| 03 | `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md` | [x] **Implemented** — ingest_local.py, dry-run/apply CLI facade |
| 04 | `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md` | [x] **Implemented** — local_rebuild.py, rebuild_after_ingest(), compile/graph pipeline |
| 05 | `docs/plans/v04/2026-05-14-v04-05-status-notification.md` | [ ] Notion status + Discord 결과 알림 |
| legacy | `docs/plans/v04/2026-05-14-v04-legacy-drive-integration.md` | [ ] Optional Drive integration 기록 |

기존 `docs/plans/v04/legacy/2026-05-14-v04-01-drive-write-foundation.md`는 Completed but Deferred legacy plan으로 보존한다.

## Responsibility Boundaries

중복을 피하기 위해 active plan의 소유 범위를 다음처럼 고정한다.

| Plan | Owns | Does not own |
|---|---|---|
| v04-00 ingest contract | request/result JSON, 표준 action/error 이름 | CLI 구현, Notion schema 확정, rebuild 구현 |
| v04-01 local storage foundation | storage layout, category/path/filename/source_id 규칙, manifest sync foundation | OpenClaw/Discord request normalization, rebuild, Notion update |
| v04-02 Notion control contract | Notion schema 후보, status enum, read/update mapping | Discord 문구, local file write, graph rebuild |
| v04-03 ingest local note CLI | OpenClaw/Discord request -> local ingest CLI facade | storage 규칙 재정의, rebuild 실행, Notion 직접 갱신 |
| v04-04 local publish then rebuild | successful local source -> compile_wiki/index_fts/build_graph | local source write 재구현, Discord 문구, Notion schema 설계 |
| v04-05 status notification | final result JSON -> Notion status update + Discord/OpenClaw summary | storage/rebuild 실행, Notion schema 설계 |
| legacy Drive integration | Drive sync/write 보존 | 기본 v0.4 path |

## Graphify + LLM Wiki 유지 조건

Google Drive를 기본 경로에서 빼더라도 다음 구조는 유지한다.

```text
원본 파일 감지
-> raw/local_storage snapshot 생성
-> sources DB upsert
-> compile_wiki.py 로 LLM Wiki 문서 생성
-> wiki_fts 색인
-> build_graph.py 로 graph nodes/edges 생성
-> search_kb.py 와 answer.py 에서 FTS + graph traversal 기반 답변
```

원본을 단순 저장하지 않고 FFXIV 개념 단위 wiki로 재구성한다. wiki 문서에서 entity와 relation을 뽑아 graph를 만든다. 검색은 metadata + SQLite FTS + graph traversal 중심으로 한다.

embedding/vector DB는 아직 도입하지 않는다.

## Notion Direct Control

OpenClaw는 Notion을 다음 목적으로 직접 다룬다.

- Notion에서 작업 상태를 읽는다.
- Notion에서 저장 요청 또는 처리 대상을 찾는다.
- Notion에 처리 결과, 실패 사유, 다음 액션을 기록한다.
- Notion에는 파일 자체를 올리지 않는다.
- Notion에는 로컬 원본 파일 경로와 처리 상태만 기록한다.
- 실제 파일은 `/mnt/d/ffixiv-bot-storage`에서 읽는다.

권장 상태 필드:

| Field | Meaning |
|---|---|
| `Title` | 사람이 읽는 문서 제목 |
| `Category` | Local Storage category |
| `Local Source Path` | `/mnt/d/ffixiv-bot-storage/sources/<category>/...` |
| `Status` | `New`, `Queued`, `Snapshot`, `Indexed`, `Graph Built`, `Partial`, `Error`, `Archived` |
| `Source ID` | `local_*` source id |
| `Wiki Path` | 생성된 wiki markdown path |
| `Graph Status` | graph build 상태 |
| `Last Processed` | 마지막 처리 시각 |
| `Last Error` | 실패 사유 또는 null |

## Non-goals

- Google Drive를 기본 source of truth로 되돌리기
- Drive 파일 삭제 또는 Drive 테스트 삭제
- embedding/vector DB 도입
- Discord/OpenClaw 실제 연결 구현
- Notion에 파일 업로드 구현
- 원본 파일을 repo 내부에 대량 저장

## How to Update

feature plan 하나가 완료되면:

1. 개별 plan 파일의 `## Status`를 갱신한다.
2. 이 master plan에서 해당 feature의 상태를 갱신한다.
3. 관련 runbook/spec/ADR이 바뀌었는지 확인한다.
4. `docs/handoff/CURRENT_HANDOFF.md`에 완료 상태와 검증 결과를 반영한다.
