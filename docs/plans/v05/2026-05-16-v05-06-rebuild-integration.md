# v05-06: Rebuild Integration

## Goal

`process_source.py`의 ingest 이후 단계에 wiki, FTS, graph rebuild를 연결한다. 기존 `local_rebuild.py`의 `rebuild_after_ingest()`를 재사용한다.

## Spec Reference

- [Sec 10.4] Rebuild
- [Sec 14.4] Rebuild Error
- [Sec 20.1] Test Plan (rebuild tests)

## Tasks

### 1. wiki rebuild integration

- [ ] ingest 성공 후 `compile_wiki.py` 호출 또는 `local_rebuild.rebuild_after_ingest()` 활용
- [ ] wiki summary 생성 확인
- [ ] wiki_path를 결과 JSON에 포함

### 2. FTS rebuild integration

- [ ] wiki rebuild 후 FTS indexing 확인
- [ ] `local_rebuild.rebuild_after_ingest()`가 FTS rebuild를 포함하는지 확인

### 3. graph build integration

- [ ] wiki/FTS rebuild 후 graph build 확인
- [ ] graph build 성공 시 `graph_status=built`
- [ ] graph build 실패 시 `graph_status=failed`, 전체 status=partial

### 4. Partial failure handling

- [ ] ingest 성공 + rebuild 실패 → `status=partial`
- [ ] 각 rebuild 하위 단계 실패를 action log에 개별 기록
- [ ] 실패 단계에서 chain 중단 (graph 실패 시에도 wiki/FTS 성공은 유지)

### 5. Tests

- [ ] `test_process_rebuild_error_returns_partial` — rebuild 실패 모의 → partial
- [ ] `test_process_graph_failure_sets_graph_status_failed` — graph 실패 → status partial + graph_status failed
- [ ] `test_process_text_note_e2e_creates_source_wiki_fts_graph` — e2e smoke

## Red Test

`tests/test_v05_process_source.py`

## Completion

- ingest → wiki → FTS → graph chain이 process_source.py 내에서 실행됨
- graph 성공 시 graph_status=built
- rebuild 실패 시 partial handling
- rebuild 결과가 action log에 기록됨
