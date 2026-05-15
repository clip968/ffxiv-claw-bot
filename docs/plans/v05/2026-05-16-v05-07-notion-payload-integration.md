# v05-07: Notion Payload Integration

## Goal

`process_source.py`의 rebuild 이후 단계에 Notion status update payload 생성을 연결한다. 기존 `status_notification.py`의 `build_notion_status_update()`를 재사용한다.

## Spec Reference

- [Sec 10.5] Notion Status Payload
- [Sec 14.5] Notion Payload Error
- [Sec 17] Notion Integration Contract
- [Sec 11] Output Contract (notion_update field)

## Tasks

### 1. Reuse `status_notification.build_notion_status_update()`

- [ ] `tools/status_notification.py`의 `build_notion_status_update()` 함수 확인
- [ ] process_source.py의 pipeline step 10에서 호출
- [ ] rebuild 결과(graph_status) 반영한 payload 생성

### 2. Payload contract enforcement

- [ ] notion_update payload에 body/attachment/raw HTML/binary가 포함되지 않는지 검증
- [ ] payload 필드: Status, Graph Status, Source ID, Local Source Path, Wiki Path, Last Processed, Last Error, Next Action
- [ ] v0.4 status semantics 매핑 유지 (ok+graph_built → Graph Built, ok+graph_pending → Indexed)

### 3. Payload 생성 실패 처리

- [ ] payload 생성 실패는 source 처리 status와 분리
- [ ] ingest/rebuild가 성공했으면 source status=ok 또는 partial 유지
- [ ] payload 생성 실패를 action log에 error로 기록

### 4. Tests

- [ ] `test_process_notion_payload_excludes_body` — body 전문이 payload에 없는지 검증
- [ ] `test_process_notion_payload_ok_graph_built` — ok+graph_built → Graph Built
- [ ] `test_process_notion_payload_ok_graph_pending` — ok+graph_pending → Indexed

## Red Test

`tests/test_v05_process_source.py`

## Completion

- notion_update payload가 JSON output에 포함됨
- body/attachment가 payload에 포함되지 않음
- v0.4 status semantics 유지
- payload 생성 실패가 source 처리와 분리됨
