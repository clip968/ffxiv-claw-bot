# v0.4-00: OpenClaw Ingest Contract

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- ADR: `docs/adrs/0006-local-storage-and-notion-control.md`
- Local runbook: `docs/runbooks/local-storage.md`
- Notion runbook: `docs/runbooks/openclaw-notion.md`

Legacy reference:

- `docs/specs/0003-google-drive-sync.md`
- `docs/plans/v04/legacy/2026-05-14-v04-01-drive-write-foundation.md`

## Status

**Reframed for Local Storage 2026-05-15**

This plan is the request/result contract for v0.4 Local Storage ingest and OpenClaw Notion direct control. The original Drive write contract is preserved below as Legacy / Deferred reference.

## Context

OpenClaw/Discord 저장 요청은 URL, 짧은 메모, markdown/text 파일, 첨부 파일처럼 입력 형태가 섞인다.

v0.4의 기본 저장소는 Google Drive가 아니라 `/mnt/d/ffixiv-bot-storage`다. Notion은 원본 파일 저장소가 아니라 OpenClaw가 직접 읽고 쓰는 작업 관리, 상태판, 문서 인덱스 계층이다.

이 contract는 Local Storage 저장, 처리용 snapshot, DB upsert, LLM Wiki/FTS/graph rebuild, Notion status update가 같은 result JSON을 공유하도록 고정한다.

## 1. Input Types

| Type | Meaning | Default handling |
|---|---|---|
| `url` | 웹 페이지 URL 저장 요청 | local source metadata와 URL 기록 |
| `text_note` | 짧은 텍스트 메모 | markdown 또는 plain text source로 저장 |
| `markdown_file` | markdown 파일 | 원본 파일 저장 후 raw snapshot |
| `plain_text_file` | 일반 텍스트 파일 | 원본 파일 저장 후 raw snapshot |
| `binary_attachment` | PDF, 이미지, Excel 등 | metadata-only 또는 `unsupported_attachment` |

## 2. Ingest Request JSON

```json
{
  "source_type": "url | text_note | markdown_file | plain_text_file | binary_attachment",
  "content_type": "text/markdown | text/plain | application/pdf | image/png | ...",
  "title": "문서 제목",
  "body": "텍스트 내용",
  "url": "https://...",
  "attachments": [
    {
      "filename": "macro.txt",
      "content_type": "text/plain",
      "data": "<base64 encoded bytes or adapter-managed reference>"
    }
  ],
  "category": "patch_notes | job_guides | raid_guides | static_docs | macros | bis_sheets | personal_notes",
  "author": "Discord 사용자명 또는 ID",
  "channel": "Discord 채널 ID 또는 mention",
  "created_at": "2026-05-14T12:00:00Z"
}
```

필드 규칙:

- `source_type`: 필수. 허용 값만 입력 가능.
- `title`: 필수. local source filename과 raw snapshot path에 사용한다.
- `body`: `text_note`, `markdown_file`, `plain_text_file`에서 필수다.
- `url`: `source_type=url`에서 필수다.
- `attachments`: `binary_attachment`에서 사용한다. 기본 v0.4 path에서는 파일 본문 저장을 보류할 수 있다.
- `category`: 필수. 허용 category 중 하나여야 한다.
- `author`, `channel`, `created_at`: 선택 metadata다.

## 3. Category And Path Mapping

Local Storage root:

```text
/mnt/d/ffixiv-bot-storage/
```

원본 source path:

```text
/mnt/d/ffixiv-bot-storage/sources/<category>/<safe_title>.<ext>
```

처리 snapshot path:

```text
raw/local_storage/<category>/<safe_title>__<source_id>.<ext>
```

DB 식별:

```text
source_url = local://sources/<category>/<safe_title>.<ext>
source_type = local_file | local_document
```

Category:

| Category | Local source directory | Snapshot directory |
|---|---|---|
| `patch_notes` | `sources/patch_notes/` | `raw/local_storage/patch_notes/` |
| `job_guides` | `sources/job_guides/` | `raw/local_storage/job_guides/` |
| `raid_guides` | `sources/raid_guides/` | `raw/local_storage/raid_guides/` |
| `static_docs` | `sources/static_docs/` | `raw/local_storage/static_docs/` |
| `macros` | `sources/macros/` | `raw/local_storage/macros/` |
| `bis_sheets` | `sources/bis_sheets/` | `raw/local_storage/bis_sheets/` |
| `personal_notes` | `sources/personal_notes/` | `raw/local_storage/personal_notes/` |

## 4. Ingest Result JSON

```json
{
  "status": "ok | partial | error",
  "dry_run": true,
  "source_id": "local_001",
  "canonical_path": "sources/job_guides/black_mage_7_5.md",
  "raw_path": "raw/local_storage/job_guides/black_mage_7_5__local_001.md",
  "wiki_path": "wiki/source_summaries/local_001.md",
  "graph_status": "pending | built | skipped | failed",
  "actions": [
    {
      "action": "write_local_source",
      "target": "/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md",
      "status": "planned | written | skipped | failed",
      "message": "Dry-run: would write local source"
    }
  ],
  "summary": {
    "total": 1,
    "ok": 1,
    "partial": 0,
    "errors": 0,
    "skipped": 0
  }
}
```

최상위 `status`:

- `ok`: 모든 필수 action 성공
- `partial`: 원본 저장은 되었지만 rebuild/graph/Notion update 중 일부 실패
- `error`: 원본 저장 또는 필수 DB upsert 실패

## 5. Standard Actions

| Action | Meaning |
|---|---|
| `validate_request` | source_type, category, title, body/url/attachment metadata 검증 |
| `write_local_source` | `/mnt/d/ffixiv-bot-storage/sources/<category>/...`에 원본 저장 |
| `snapshot_raw` | `raw/local_storage/<category>/...`에 처리용 snapshot 생성 |
| `upsert_source` | `db/ffxiv.sqlite` `sources` 테이블 갱신 |
| `compile_wiki` | LLM Wiki markdown 생성 또는 갱신 |
| `index_fts` | `wiki_fts` 색인 갱신 |
| `build_graph` | graph nodes/edges 생성 또는 갱신 |
| `update_notion_status` | Notion 상태판에 처리 결과 기록 |

각 action은 최소한 `action`, `target`, `status`, `message`를 가진다.

## 6. Dry-run And Apply

| Item | dry_run: true | dry_run: false |
|---|---|---|
| Local source write | 하지 않음, target만 표시 | 실제 파일 쓰기 |
| raw snapshot | 하지 않음, planned path만 표시 | 실제 snapshot 생성 |
| DB upsert | 하지 않음 | `sources` upsert |
| rebuild | 하지 않음 | 요청한 경우 compile/wiki/FTS/graph 실행 |
| Notion update | 하지 않음 | adapter 옵션 또는 후속 단계에서 상태 갱신 |

`dry_run`은 파일, DB, Notion을 쓰지 않는다.

## 7. Error Contract

```json
{
  "status": "error",
  "dry_run": false,
  "actions": [
    {
      "action": "validate_request",
      "target": null,
      "status": "failed",
      "message": "category is required",
      "error_type": "invalid_input"
    }
  ],
  "summary": {
    "total": 1,
    "ok": 0,
    "partial": 0,
    "errors": 1,
    "skipped": 0
  }
}
```

기본 error type:

| error_type | 발생 조건 | 처리 |
|---|---|---|
| `invalid_input` | source_type/category/title/body/url 누락 또는 잘못됨 | 해당 request 실패 |
| `unsupported_attachment` | 기본 path에서 처리하지 않는 binary attachment | metadata-only 또는 skipped |
| `local_storage_root_missing` | `/mnt/d/ffixiv-bot-storage` 없음 | 전체 실패 |
| `local_write_failed` | local source 또는 raw snapshot 쓰기 실패 | 해당 request 실패 |
| `source_upsert_failed` | `sources` DB upsert 실패 | 해당 request 실패 |
| `rebuild_failed` | compile_wiki/index_fts/build_graph 실패 | `partial` |
| `notion_update_failed` | Notion 상태판 갱신 실패 | `partial` |

## 8. OpenClaw/Discord Response Rules

OpenClaw tool adapter와 Discord summary는 이 contract의 result JSON을 사람이 읽는 메시지로 변환한다.

| result 상태 | 응답 방향 |
|---|---|
| `ok` | 저장 위치, category, wiki path, graph status를 짧게 알림 |
| `partial` | 저장은 되었지만 실패한 후속 action과 다음 행동을 알림 |
| `error` | 저장 실패 사유와 사용자가 수정할 입력을 알림 |
| dry-run | 예상 저장 위치와 실행 시 일어날 action만 알림 |

Drive URL은 기본 응답 필드가 아니다. Drive URL은 legacy integration 결과에서만 표시한다.

## 9. Feature Ownership

이 contract는 다음 plan의 기준이다.

- `v04-01-local-storage-foundation`: Local Storage root/path/category/result 기반
- `v04-02-openclaw-notion-control-contract`: Notion status field와 update action 기반
- `v04-03-ingest-local-note-cli`: request/result JSON CLI 입출력 기반
- `v04-04-local-publish-then-rebuild`: compile/wiki/FTS/graph action 기반
- `v04-05-status-notification`: Discord/Notion status summary 기반

## Legacy / Deferred Drive Contract

기존 v04-00은 Drive write가 기본 source of truth였을 때 다음 항목을 사용했다.

- action: `drive_upload`, `drive_update`, `upload_drive_file`, `sync_drive`
- fields: `drive_file_id`, `drive_url`
- raw path: `raw/drive/<category>/<safe_title>__<drive_file_id>.<ext>`
- source URL: `gdrive://<drive_file_id>`
- errors: `drive_auth_missing`, `drive_write_failed`

이 계약은 삭제하지 않고 `docs/plans/v04/2026-05-14-v04-legacy-drive-integration.md`, `docs/specs/0003-google-drive-sync.md`, `docs/adrs/0005-drive-write-scope-and-upload.md`에서 optional legacy integration으로 보존한다.

## Checklist

- [x] 입력 타입 결정: URL, text note, markdown file, plain text file, binary attachment
- [x] Local Storage request JSON 필드 결정
- [x] Local category와 path mapping 결정
- [x] Local result JSON 필드 결정
- [x] dry-run/apply 차이 결정
- [x] Local error contract 결정
- [x] OpenClaw/Discord 응답 문구 기준 결정
- [x] Drive contract를 legacy/deferred로 분리

## Verification

문서 계약 plan이므로 red test는 작성하지 않는다.

구현 단계에서는 이 plan의 request/result JSON 예시를 기준으로 unittest를 먼저 작성한다.

```bash
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- Local Storage를 기본 canonical source로 사용한다.
- Notion은 파일 저장소가 아니라 OpenClaw control/status/index layer다.
- repo `docs/`는 문서 source of truth다.
- Drive write/publish는 optional legacy integration이다.
- dry-run/apply 이분법은 유지하되 저장 대상은 Local Storage다.
