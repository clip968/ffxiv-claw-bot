# v0.4-00: OpenClaw Ingest Contract

## Spec

- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- `docs/adrs/0002-drive-is-canonical-source.md`

## Status

**Completed 2026-05-14**

## Context

OpenClaw/Discord 저장 요청은 URL, 짧은 메모, markdown/text 파일, 첨부 파일처럼 입력 형태가 섞인다.
구현 전에 저장 요청과 결과 JSON 계약을 먼저 고정해야 Drive write, CLI ingest, OpenClaw adapter가 같은 인터페이스를 공유할 수 있다.

이 contract는 `docs/specs/01-architecture.md`의 metadata 형식, `docs/specs/0003-google-drive-sync.md`의 dry-run/apply JSON 출력 패턴, Drive 폴더 구조를 기준으로 정의한다.

---

## 1. 입력 타입

| 타입 | 설명 | 예시 |
|---|---|---|
| `url` | 웹 페이지 URL 저장 요청 | `https://jp.finalfantasyxiv.com/lodestone/...` |
| `text_note` | 짧은 텍스트 메모 | "오늘 공대 3층 3세트 기록" |
| `markdown_file` | 포맷된 markdown 파일 | 공대 매크로, BIS 시트 |
| `plain_text_file` | 일반 텍스트 파일 | 로그 덤프, 설정 파일 |
| `binary_attachment` | 바이너리 첨부 파일 (v0.4-00에서는 저장만, compile 제외) | PDF, 이미지, Excel 등 |

---

## 2. Ingest Request JSON

```json
{
  "source_type": "url | text_note | markdown_file | plain_text_file | binary_attachment",
  "content_type": "text/markdown | text/plain | application/pdf | image/png | ...",
  "title": "문서 제목",
  "body": "텍스트 내용 (url/attachment 타입에서는 비울 수 있음)",
  "url": "https://... (source_type=url 일 때 필수)",
  "attachments": [
    {
      "filename": "macro.txt",
      "content_type": "text/plain",
      "data": "<base64 encoded bytes>"
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
- `title`: 필수. Drive 파일명과 raw path에 사용.
- `body`: `text_note`, `markdown_file`, `plain_text_file`에서 필수. `url`에서는 비움.
- `url`: `source_type=url`에서 필수. 다른 타입에서는 무시.
- `attachments`: `binary_attachment`에서 사용. v0.4-00에서는 binary attachment 지원 안 함 (unsupported 처리).
- `category`: 필수. 7개 category 중 하나.
- `author`, `channel`, `created_at`: 선택. 기록용 metadata.

---

## 3. Category 매핑

7개 category는 Google Drive `FFXIV_KB` 폴더 구조와 일치한다.

| Category | Drive 폴더 | raw 경로 |
|---|---|---|
| `patch_notes` | `FFXIV_KB/patch_notes/` | `raw/drive/patch_notes/<title>__<id>.md` |
| `job_guides` | `FFXIV_KB/job_guides/` | `raw/drive/job_guides/<title>__<id>.md` |
| `raid_guides` | `FFXIV_KB/raid_guides/` | `raw/drive/raid_guides/<title>__<id>.md` |
| `static_docs` | `FFXIV_KB/static_docs/` | `raw/drive/static_docs/<title>__<id>.md` |
| `macros` | `FFXIV_KB/macros/` | `raw/drive/macros/<title>__<id>.md` |
| `bis_sheets` | `FFXIV_KB/bis_sheets/` | `raw/drive/bis_sheets/<title>__<id>.md` |
| `personal_notes` | `FFXIV_KB/personal_notes/` | `raw/drive/personal_notes/<title>__<id>.md` |

raw 경로 규칙은 `docs/specs/0003-google-drive-sync.md`의 local raw path 규칙을 따른다:

```
raw/drive/<category>/<safe_title>__<drive_file_id>.<ext>
```

---

## 4. Ingest Result JSON

```json
{
  "status": "success | partial | failed",
  "actions": [
    {
      "action": "drive_upload | drive_update | skip | error",
      "source_type": "url | text_note | ...",
      "title": "문서 제목",
      "category": "patch_notes",
      "drive_file_id": "abc123...",
      "drive_url": "https://drive.google.com/...",
      "source_id": "drive_abc123...",
      "raw_path": "raw/drive/patch_notes/...",
      "rebuild_status": "pending | running | completed | skipped | failed",
      "message": "성공 또는 실패 상세 메시지"
    }
  ],
  "summary": {
    "total": 3,
    "uploaded": 2,
    "updated": 0,
    "skipped": 0,
    "errors": 1
  },
  "dry_run": true
}
```

최상위 필드:

- `status`: 전체 결과. `success` = 모든 action 성공, `partial` = 일부 실패, `failed` = 전체 실패.
- `actions`: 각 입력 항목별 개별 결과 배열.
- `summary`: 집계. `total`, `uploaded`, `updated`, `skipped`, `errors`.
- `dry_run`: dry-run 모드 여부.

action별 필드 규칙:

| action | drive_file_id | drive_url | source_id | raw_path | rebuild_status |
|---|---|---|---|---|---|
| `drive_upload` | 실제 ID | 실제 URL | `drive_<id>` | 실제 경로 | `completed` or `failed` |
| `drive_update` | 기존 ID | 기존 URL | `drive_<id>` | 실제 경로 | `completed` or `failed` |
| `skip` | null (dry-run시 예상 ID) | null | null | 예상 경로 | `skipped` |
| `error` | null | null | null | null | `skipped` |

---

## 5. Dry-run 결과와 Apply 결과 차이

| 항목 | dry_run: true | dry_run: false |
|---|---|---|
| Drive API 호출 | 하지 않음 | 실제 upload/create 호출 |
| raw/drive 저장 | 하지 않음 | 실제 파일 저장 |
| DB upsert | 하지 않음 | sources 테이블 upsert |
| rebuild | 하지 않음 | apply 직후 --rebuild 실행 |
| `dry_run` 필드 | `true` | `false` |
| `action` 값 | `drive_upload` / `drive_update` / `skip` (계획) | `drive_upload` / `drive_update` / `error` (실행 결과) |
| `drive_file_id` | 예상 ID 또는 null | 실제 생성된 ID |
| `source_id` | 예상 source_id | 실제 source_id |
| `raw_path` | 예상 경로 | 실제 저장 경로 |
| `rebuild_status` | `pending` | `completed` / `skipped` / `failed` |

---

## 6. 오류 계약

```json
{
  "status": "failed",
  "actions": [
    {
      "action": "error",
      "source_type": "text_note",
      "title": "문서 제목",
      "category": null,
      "drive_file_id": null,
      "drive_url": null,
      "source_id": null,
      "raw_path": null,
      "rebuild_status": "skipped",
      "message": "상세 오류 메시지",
      "error_type": "invalid_input | unsupported_attachment | drive_auth_missing | drive_write_failed | rebuild_failed"
    }
  ],
  "summary": {
    "total": 1,
    "uploaded": 0,
    "updated": 0,
    "skipped": 0,
    "errors": 1
  },
  "dry_run": false
}
```

Error type 목록:

| error_type | 발생 조건 | 처리 |
|---|---|---|
| `invalid_input` | source_type 누락/잘못됨, body 누락 (text 계열), title 누락, URL 형식 오류 | 해당 action만 실패, 나머지 계속 |
| `unsupported_attachment` | binary_attachment 입력 (v0.4-00에서 미지원) | 해당 action skip, 나머지 계속 |
| `drive_auth_missing` | Drive token/credential 없음 | 전체 실패 |
| `drive_write_failed` | Drive API upload/create/http 오류 | 해당 action만 실패, 나머지 계속 |
| `rebuild_failed` | compile_wiki/build_graph 실패 | 비파탈 오류, status=partial로 처리 |

원칙:
- `drive_auth_missing`만 전체 실패. 나머지는 부분 실패로 처리.
- `rebuild_failed`는 storage 성공과 별개로 추적. raw 저장은 완료되었으나 rebuild가 실패한 경우.

---

## 7. OpenClaw/Discord 응답 문구 기준

OpenClaw tool adapter에서 이 contract의 result JSON을 기준으로 자연어 응답을 생성한다.

| result 상태 | 응답 방향 |
|---|---|
| `success` / 모든 action 성공 | "✅ 저장 완료. 카테고리: {category}, 파일명: {title}" |
| `partial` / 일부 action 실패 | "일부만 저장됨. {n}개 성공, {m}개 실패. 실패: {오류 메시지}" |
| `failed` / 전체 실패 | "저장 실패: {오류 메시지}. 입력을 확인하거나 관리자에게 문의하세요." |
| dry-run | "저장 예상 결과: {n}개 upload, {m}개 update, {k}개 skip" |

응답에 포함할 정보:
- 저장된 파일의 Drive URL (link)
- category 정보
- rebuild 결과 (성공/실패 여부)
- 오류 발생 시 구체적인 원인과 해결 방법

---

## 8. 관련 spec 업데이트

v04-00 contract는 v04-01~v04-05 feature들의 입력/출력 인터페이스 기준이다.
별도 spec 파일을 추가하지 않고, 이 plan 자체를 다음 feature들의 인터페이스 계약으로 사용한다.

영향 받는 feature:
- `v04-01-drive-write-foundation`: 이 contract의 request JSON을 Drive write 입력으로 사용
- `v04-02-ingest-discord-note-cli`: 이 contract의 request/result JSON을 CLI 출력 형식으로 사용
- `v04-03-openclaw-tool-adapter`: 이 contract의 result JSON을 OpenClaw 응답으로 변환
- `v04-04-publish-then-rebuild`: rebuild_status 필드를 rebuild chain 연결에 사용
- `v04-05-discord-summary-notification`: result JSON의 summary/actions를 Discord 메시지로 변환

## Checklist (completed)

- [x] 입력 타입 결정: URL, text note, markdown file, plain text file, binary attachment
- [x] ingest request JSON 필드 결정
- [x] category 매핑 결정
- [x] result JSON 필드 결정
- [x] dry-run result와 apply result 차이 결정
- [x] 오류 계약 결정
- [x] OpenClaw/Discord 응답 문구 기준 결정
- [x] 관련 spec 업데이트 필요 여부 확인 (불필요, plan이 contract 역할)

## Verification

문서 계약 plan이므로 red test는 작성하지 않는다.
구현 단계에서는 이 plan의 request/result JSON 예시를 기준으로 unittest를 먼저 작성한다.

```bash
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- Drive를 canonical source로 유지한다.
- OpenClaw adapter는 repo tool을 호출하는 thin wrapper로 둔다.
- MCP/skill은 호출 껍데기이며 저장 계약은 repo `tools/`와 `docs/`에 둔다.
- dry-run/apply 이분법은 spec0003 Google Drive sync의 패턴을 재사용한다.
- binary_attachment는 v0.4-00에서 unsupported 처리하고, Drive write 기반이 안정화된 후 추가 지원한다.
- 오류 계약은 `drive_auth_missing`만 전체 실패, 나머지는 부분 실패로 처리한다.
