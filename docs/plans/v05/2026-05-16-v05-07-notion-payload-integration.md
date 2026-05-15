# v0.5-07 Plan: Notion Payload Integration

## Goal

process_source.py가 처리 결과를 기반으로 Notion update payload를 안정적으로 생성하도록 구현한다.

이번 task의 핵심은 process_source.py가 Notion API를 직접 호출하는 것이 아니라, OpenClaw가 사용할 수 있는 안전한 notion_update JSON을 생성하는 것이다.

## Background

현재 Notion은 원본 파일 저장소가 아니라 control/status/index layer다.

Notion에는 다음 metadata만 저장해야 한다.

- source title
- category
- status
- source ID
- local source path
- wiki path
- graph status
- last processed
- last error
- next action

Notion에는 원문 body 전체, binary attachment, raw HTML 전체가 들어가면 안 된다.

v0.4에는 status_notification.py가 있고, status와 graph_status를 Notion property update로 변환하는 기능이 있다.

v0.5에서는 process_source.py가 이 로직을 재사용한다.

## Scope

이번 task에서 구현할 것:

1. process_source.py 결과에서 notion_update 생성
2. status_notification.py 기존 로직 재사용
3. ok/partial/error/skipped 상태 mapping 고정
4. body/attachment/raw HTML exclusion 보장
5. notion_update payload test 작성
6. OpenClaw가 notion_update를 사용할 수 있도록 runbook 갱신

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- Notion API 직접 호출
- Notion DB polling
- Notion queue
- crawler
- scheduler
- Notion database schema migration 자동화

## Files to Update

tools/process_source.py
tools/status_notification.py
tests/test_v05_process_source.py
tests/test_v04_status_notification.py
docs/runbooks/process-source.md
docs/runbooks/openclaw-notion.md
docs/handoff/CURRENT_HANDOFF.md

## Notion Payload Contract

process_source.py의 최종 JSON에는 notion_update가 포함되어야 한다.

예시:

{
  "notion_update": {
    "Status": "Graph Built",
    "Graph Status": "Built",
    "Source ID": "local_abc123",
    "Local Source Path": "sources/personal_notes/p12s_note.md",
    "Wiki Path": "wiki/source_summaries/local_abc123.md",
    "Last Processed": "2026-05-16T00:00:00+09:00",
    "Next Action": "Ready for search and answer."
  }
}

에러 예시:

{
  "notion_update": {
    "Status": "Error",
    "Graph Status": "Skipped",
    "Last Error": "Missing required argument: --url",
    "Next Action": "Provide a valid URL."
  }
}

## Allowed Fields

notion_update에 허용되는 필드:

- Status
- Graph Status
- Source ID
- Category
- Local Source Path
- Wiki Path
- Last Processed
- Last Error
- Next Action
- Source URL
- Content Hash

필요한 경우 추가 가능하지만, 원문 전체를 넣지 않는다.

## Forbidden Fields

notion_update에 들어가면 안 되는 필드:

- body
- full_body
- raw_body
- raw_html
- content
- attachment_bytes
- binary_data
- file_blob
- large_text
- fetched_html
- original_document_text

테스트에서 body/attachment exclusion을 반드시 검증한다.

## Status Mapping

내부 결과에서 Notion status로 변환한다.

### Full Success

조건:

status=ok
graph_status=built

Notion:

Status=Graph Built
Graph Status=Built
Next Action=Ready for search and answer.

### Indexed But Graph Pending

조건:

status=ok 또는 partial
graph_status=pending

Notion:

Status=Indexed
Graph Status=Pending
Next Action=Run graph build.

### Graph Failure

조건:

status=partial
graph_status=failed

Notion:

Status=Indexed 또는 Partial
Graph Status=Failed
Last Error=...
Next Action=Retry graph build.

정책 선택:
기존 status_notification.py가 Graph Status Failed를 따로 지원한다면 그 값을 따른다.
기존 정책이 Indexed를 유지한다면 기존 정책을 우선한다.

### Validation Error

조건:

status=error
source_id=null
graph_status=skipped

Notion:

Status=Error
Graph Status=Skipped
Last Error=...
Next Action=...

### Dry Run

조건:

status=skipped
dry_run=true

Notion:

Status=Skipped
Graph Status=Skipped
Next Action=Run with --apply to persist the source.

## Implementation Approach

1. process_source.py가 내부 result dict를 만든다.
2. result dict를 status_notification.py의 함수에 전달한다.
3. status_notification.py가 notion_update dict를 반환한다.
4. process_source.py가 최종 JSON에 notion_update를 포함한다.

가능하면 status_notification.py에 다음 형태의 함수가 있어야 한다.

build_notion_status_update(result: dict) -> dict

기존 함수 signature가 다르면 wrapper를 만든다.

## OpenClaw Responsibility

v0.5에서 process_source.py는 Notion API를 직접 호출하지 않는다.

OpenClaw는 다음을 수행한다.

1. process_source.py stdout JSON 파싱
2. notion_page_id가 있거나 사용자가 Notion update를 요청했는지 확인
3. notion_update payload를 Notion DB property update로 변환
4. Notion API 호출
5. 사용자에게 결과 보고

## Tests

tests/test_v05_process_source.py:

test_process_success_includes_notion_update
test_process_graph_built_maps_to_notion_graph_built
test_process_graph_failed_maps_to_notion_failed_or_partial
test_process_validation_error_maps_to_notion_error
test_process_dry_run_maps_to_notion_skipped
test_process_notion_payload_excludes_body
test_process_notion_payload_excludes_raw_html
test_process_notion_payload_excludes_attachment_data

tests/test_v04_status_notification.py에 기존 regression이 있다면 유지한다.

추가 regression:

test_ok_with_graph_built_promotes_status
test_ok_without_graph_built_stays_indexed
test_missing_graph_status_defaults_indexed_or_pending
test_payload_excludes_body_attachments_drive_url_if_policy_requires

## Runbook Update

docs/runbooks/process-source.md에 다음을 추가한다.

- process_source.py 결과에서 notion_update 확인하는 법
- OpenClaw가 Notion에 반영해야 하는 필드
- Notion에 넣으면 안 되는 필드
- partial/error일 때 사용자가 확인해야 할 next_action

docs/runbooks/openclaw-notion.md에 다음을 추가한다.

- v0.5에서는 process_source.py가 notion_update payload만 생성한다.
- 실제 Notion write는 OpenClaw가 수행한다.
- Notion은 control/status/index layer이며 원본 저장소가 아니다.

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- process_source.py 결과에 notion_update가 포함된다.
- ok + graph built가 Graph Built/Built로 mapping된다.
- validation error가 Error/Skipped로 mapping된다.
- dry-run이 Skipped/Skipped로 mapping된다.
- graph failure가 partial 또는 failed 상태로 명확히 mapping된다.
- notion_update에 body 전문이 들어가지 않는다.
- notion_update에 raw_html이 들어가지 않는다.
- notion_update에 attachment data가 들어가지 않는다.
- Notion API 직접 호출은 v0.5에 포함되지 않는다.
- 기존 status_notification regression test가 통과한다.

## Verification

전체 테스트:

python -m unittest discover -s tests -p "test_*.py"

수동 확인:

python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "notion payload smoke" --body "This body must not appear in notion_update."

확인할 것:

- notion_update가 존재하는지
- body가 notion_update 안에 없는지
- Status가 Skipped인지
- Graph Status가 Skipped인지

apply 확인:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "notion payload apply smoke" --body "This body must not appear in notion_update."

확인할 것:

- source_id 존재
- wiki_path 존재
- notion_update.Status가 Graph Built 또는 Indexed
- notion_update에 body 없음

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일
2. Notion payload mapping 요약
3. 통과한 테스트
4. 남은 제한 사항