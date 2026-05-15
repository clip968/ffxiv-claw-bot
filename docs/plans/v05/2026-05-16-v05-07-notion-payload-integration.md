# v0.5-07: Notion Payload Integration

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 10.5] Notion Status Payload, [Sec 14.5] Notion Payload Error, [Sec 17] Notion Integration Contract, [Sec 11] Output Contract (notion_update field)
- Runbook: `docs/runbooks/openclaw-notion.md`

## Status

**Completed** 2026-05-16

## Goal

`process_source.py`의 rebuild 이후 단계에 Notion status update payload 생성을 연결한다. 기존 `status_notification.py`의 `build_notion_status_update()`를 재사용한다.

## Scope

- `tools/status_notification.py`의 `build_notion_status_update()` 함수 확인 및 재사용
- process_source.py의 pipeline step 10에서 Notion payload 호출
- rebuild 결과(graph_status) 반영한 payload 생성
- notion_update payload에 body/attachment/raw HTML/binary가 포함되지 않는지 검증
- payload 필드: Status, Graph Status, Source ID, Local Source Path, Wiki Path, Last Processed, Last Error, Next Action
- v0.4 status semantics 매핑 유지 (ok+graph_built → Graph Built, ok+graph_pending → Indexed)
- payload 생성 실패는 source 처리 status와 분리 (ingest/rebuild 성공 시 status=ok 또는 partial 유지)

Out of scope:
- Notion API 실제 호출 (OpenClaw가 수행)
- Notion schema 설계
- Discord 메시지 포맷

## Red Test

- File: `tests/test_v05_process_source.py`
- Implementation target: `tools/process_source.py`, `tools/status_notification.py`
- Current red reason: Notion payload generation이 process_source.py에 연결되지 않음.
- Contract fixed by the test:
  - notion_update payload에 body 전문이 포함되지 않음.
  - ok+graph_built → Notion Status = Graph Built.
  - ok+graph_pending → Notion Status = Indexed.

## Checklist

- [x] `tools/status_notification.py`의 `build_notion_status_update()` 함수 확인
- [x] process_source.py의 pipeline step 10에서 호출
- [x] rebuild 결과(graph_status) 반영한 payload 생성
- [x] notion_update payload에 body/attachment/raw HTML/binary가 포함되지 않는지 검증
- [x] payload 필드 확인: Status, Graph Status, Source ID, Local Source Path, Wiki Path, Last Processed, Last Error, Next Action
- [x] v0.4 status semantics 매핑 유지 (ok+graph_built → Graph Built, ok+graph_pending → Indexed)
- [x] payload 생성 실패는 source 처리 status와 분리
- [x] ingest/rebuild가 성공했으면 source status=ok 또는 partial 유지
- [x] payload 생성 실패를 action log에 error로 기록
- [x] `test_process_notion_payload_excludes_body` — body 전문이 payload에 없는지 검증
- [x] `test_process_notion_payload_ok_graph_built` — ok+graph_built → Graph Built
- [x] `test_process_notion_payload_ok_graph_pending` — ok+graph_pending → Indexed

## Implementation Notes

- `tools/process_source.py` now reuses `tools.status_notification.build_notion_status_update()` after rebuild.
- The process result includes `notion_update` with `Status`, `Graph Status`, `Source ID`, `Local Source Path`, `Wiki Path`, `Last Processed`, `Last Error`, and `Next Action`.
- `ok + graph_status=built` maps to Notion `Status=Graph Built`.
- `ok + graph_status=pending` maps to Notion `Status=Indexed`.
- Payload generation does not call the Notion API and does not include body/raw HTML/attachments/binary data.
- Payload generation failure is isolated to a `build_notion_payload` action and does not overwrite the ingest/rebuild status.

## Verification Results

```bash
python -m unittest tests.test_v05_process_source.V05ProcessSourceNotionPayloadIntegrationTests -v
python -m unittest tests.test_v04_status_notification -v
```

The v05-07 red tests failed first on missing `notion_update` fields, then passed after integration.

## Verification

```bash
python -m unittest tests.test_v05_process_source -v
python -m unittest tests.test_v04_status_notification -v
python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "Notion Test" --body "Test" | python -c "import sys,json; d=json.load(sys.stdin); assert 'notion_update' in d; print('OK: notion_update in output')"
```

## Key Decisions

- Notion payload 생성은 실제 API 호출과 분리한다. process_source.py는 payload만 생성하고 OpenClaw가 실제 호출을 수행한다.
- payload 생성 실패가 ingest/rebuild 성공을 무효화하지 않는다.
- v0.4 status mapping을 그대로 유지한다.
