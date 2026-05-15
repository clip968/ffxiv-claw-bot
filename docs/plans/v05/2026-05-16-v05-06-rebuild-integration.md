# v0.5-06: Rebuild Integration

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 10.4] Rebuild, [Sec 14.4] Rebuild Error
- Runbook: `docs/runbooks/rebuild-kb.md`

## Status

**Pending**

## Goal

`process_source.py`의 ingest 이후 단계에 wiki, FTS, graph rebuild를 연결한다. 기존 `local_rebuild.py`의 `rebuild_after_ingest()`를 재사용한다.

## Scope

- ingest 성공 후 `compile_wiki.py` 호출 또는 `local_rebuild.rebuild_after_ingest()` 활용
- wiki summary 생성 및 `wiki_path`를 결과 JSON에 포함
- FTS indexing 확인 (`local_rebuild.rebuild_after_ingest()`가 포함하는지 확인)
- wiki/FTS rebuild 후 graph build
- graph build 성공 시 `graph_status=built`, 실패 시 `graph_status=failed`
- ingest 성공 + rebuild 실패 → `status=partial`
- 각 rebuild 하위 단계 실패를 action log에 개별 기록

Partial failure policy:
- ingest 성공 + rebuild 실패 → `status=partial`
- 각 rebuild 하위 단계 실패를 action log에 개별 기록
- graph 실패 시에도 wiki/FTS 성공은 유지

## Red Test

- File: `tests/test_v05_process_source.py`
- Implementation target: `tools/process_source.py`, `tools/local_rebuild.py`
- Current red reason: rebuild pipeline이 process_source.py에 연결되지 않음.
- Contract fixed by the test:
  - rebuild 실패 모의 시 `status=partial` 반환.
  - graph build 실패 시 `graph_status=failed`, 전체 `status=partial`.
  - text_note E2E로 source, wiki, FTS, graph 생성 확인.

## Checklist

- [ ] ingest 성공 후 `compile_wiki.py` 호출 또는 `local_rebuild.rebuild_after_ingest()` 활용
- [ ] wiki summary 생성 확인
- [ ] wiki_path를 결과 JSON에 포함
- [ ] wiki rebuild 후 FTS indexing 확인
- [ ] `local_rebuild.rebuild_after_ingest()`가 FTS rebuild를 포함하는지 확인
- [ ] wiki/FTS rebuild 후 graph build 확인
- [ ] graph build 성공 시 `graph_status=built`
- [ ] graph build 실패 시 `graph_status=failed`, 전체 status=partial
- [ ] ingest 성공 + rebuild 실패 → `status=partial`
- [ ] 각 rebuild 하위 단계 실패를 action log에 개별 기록
- [ ] graph 실패 시에도 wiki/FTS 성공은 유지
- [ ] `test_process_rebuild_error_returns_partial` — rebuild 실패 모의 → partial
- [ ] `test_process_graph_failure_sets_graph_status_failed` — graph 실패
- [ ] `test_process_text_note_e2e_creates_source_wiki_fts_graph` — e2e smoke

## Verification

```bash
python -m unittest tests.test_v05_process_source -v
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "Rebuild Test" --body "Test content"
python tools/search_kb.py "Rebuild Test"
```

## Key Decisions

- 기존 `local_rebuild.rebuild_after_ingest()`를 재사용한다. 중복 구현하지 않는다.
- rebuild 실패는 source 저장 성공을 되돌리지 않는다 (partial은 저장 성공).
- rebuild 실패도 action log에 기록되어 OpenClaw가 진단할 수 있어야 한다.
