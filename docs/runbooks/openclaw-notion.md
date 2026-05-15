# OpenClaw Notion Direct Control Runbook

## 원칙

Notion은 원본 파일 저장소가 아니다.

Notion은 OpenClaw가 직접 읽고 쓰는 작업 관리, 상태판, 문서 인덱스 계층이다. repo `docs/`는 문서 source of truth이며, 실제 원본 파일은 `/mnt/d/ffixiv-bot-storage`에서 읽는다.

## OpenClaw가 Notion에서 하는 일

- 작업 상태를 읽는다.
- 저장 요청 또는 처리 대상을 찾는다.
- 처리 결과를 기록한다.
- 실패 사유와 다음 액션을 기록한다.
- wiki path와 graph status를 기록한다.

## Notion에 기록하지 않는 것

- 원본 파일 본문
- PDF, XLSX, DOCX, 이미지 같은 attachment 자체
- repo docs의 원문 전체
- `db/ffxiv.sqlite` 전체 record
- `graph/nodes.json`, `graph/edges.json` 전체 내용

## Status Item Shape

| Field | Example |
|---|---|
| Title | 흑마 7.5 가이드 |
| Category | job_guides |
| Local Source Path | `/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md` |
| Status | Indexed |
| Source ID | local_001 |
| Wiki Path | `wiki/jobs/black_mage/7_5.md` |
| Graph Status | Built |
| Last Processed | `2026-05-14T00:00:00Z` |
| Last Error | null |

## Status Values

권장 상태:

- `New`: Notion에 등록되었지만 아직 처리하지 않음
- `Queued`: OpenClaw가 처리 대상으로 잡음
- `Snapshot`: `raw/local_storage` snapshot 생성 완료
- `Indexed`: DB와 wiki/FTS 갱신 완료
- `Graph Built`: graph 갱신 완료
- `Partial`: 일부 action 실패
- `Error`: 처리 실패
- `Archived`: 현재 활성 사용하지 않음

## Processing Flow

```text
Notion status item 읽기
-> Local Source Path 확인
-> /mnt/d/ffixiv-bot-storage 원본 읽기
-> raw/local_storage snapshot 생성
-> db/ffxiv.sqlite sources upsert
-> compile_wiki.py 실행
-> build_graph.py 실행
-> Notion status item 갱신
```

## Error 기록

오류 발생 시 Notion에는 다음만 기록한다.

- `Status`: `Partial` 또는 `Error`
- `Last Error`: 짧은 실패 사유
- `Next Action`: 사용자가 해야 할 일 또는 다음 agent가 이어갈 일
- `Last Processed`: 실패 시각

원본 파일을 Notion에 첨부해서 해결하지 않는다. 원본 파일은 Local Source Path에서 수정한다.

## Legacy / Deferred

Drive URL이나 Drive file ID는 legacy optional integration metadata로만 기록한다. 현재 기본 운영 경로에서는 `Local Source Path`와 `Source ID`가 우선이다.

## CLI Result → Notion Payload Mapping

`tools/openclaw_notion_control.py`의 `build_notion_update(result)` 함수를 사용한다.

### Status 매핑 규칙

| CLI `status` | CLI `graph_status` | Notion `Status` |
|---|---|---|
| `ok` | `built` | `Graph Built` |
| `ok` | 기타/없음 | `Indexed` |
| `partial` | 어떤 값이든 | `Partial` |
| `error` | 어떤 값이든 | `Error` |

### 필드 매핑

| CLI result key | Notion property |
|---|---|
| `status` (+ `graph_status`) | `Status` |
| `title` | `Title` |
| `category` | `Category` |
| `source_id` | `Source ID` |
| `local_source_path` | `Local Source Path` |
| `wiki_path` | `Wiki Path` |
| `graph_status` | `Graph Status` |
| `last_processed` | `Last Processed` |
| `last_error` | `Last Error` |
| `next_action` | `Next Action` |

### 절대 포함하지 않는 필드

- `body`
- `attachments`

## Status Notification Functions

`tools/status_notification.py` provides two functions that consume a final pipeline result JSON:

### `format_discord_summary(result)`

사용자-facing Discord/OpenClaw 메시지를 생성한다.

| Result status | message format |
|---|---|
| `ok` | `[category] title — 처리 완료` + 경로 정보 |
| `partial` | `[category] title — 일부 실패` + 경로 + 오류 + next action |
| `error` | `[category] title — 처리 실패` + 오류 + next action |
| `skipped` | `[category] title — 건너뜀 (처리 생략)` |

Drive URL은 기본 응답에 포함되지 않는다.

### `build_notion_status_update(result)`

같은 result JSON을 Notion property update payload로 변환한다.

| CLI key | Notion property |
|---|---|
| `status` | `Status` (ok→Indexed, partial→Partial, error→Error 등) |
| `graph_status` | `Graph Status` (built→Built, pending→Pending, failed→Failed, skipped→Skipped) |
| `title`, `category`, `source_id` | 대응 Notion property |
| `local_source_path`, `wiki_path` | 대응 Notion property |
| `last_error` | `Last Error` |
| `next_action` | `Next Action` |
