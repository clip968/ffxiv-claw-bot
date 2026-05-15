# v0.5-06 Plan: Rebuild Integration

## Goal

process_source.py가 ingest 성공 후 wiki summary, FTS, graph build까지 이어서 실행하도록 구현한다.

이번 task가 완료되면 source 하나를 process_source.py로 추가했을 때 검색과 answer context에 반영되어야 한다.

## Background

v0.4에는 이미 다음 도구가 있다.

- compile_wiki.py
- local_rebuild.py
- build_graph.py
- search_kb.py
- answer.py

v0.5에서는 process_source.py가 이들을 직접 재구현하지 않고 기존 rebuild 로직을 재사용해야 한다.

## Scope

이번 task에서 구현할 것:

1. process_source.py에서 ingest 성공 후 rebuild 호출
2. wiki summary 생성 확인
3. FTS 갱신 확인
4. graph build 실행
5. rebuild result를 JSON에 반영
6. partial failure handling
7. search_kb.py와 answer.py로 후속 확인 가능하게 함
8. 관련 tests 작성

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- 새로운 graph 알고리즘
- embedding/vector DB
- LLM 기반 요약 품질 개선
- Notion polling
- crawler
- scheduler
- Discord runtime

## Files to Update

tools/process_source.py
tests/test_v05_process_source.py
docs/runbooks/process-source.md
docs/handoff/CURRENT_HANDOFF.md

필요한 경우:

tools/local_rebuild.py
tools/compile_wiki.py
tools/build_graph.py

단, 기존 CLI 사용법이 깨지지 않아야 한다.

## Rebuild Flow

ingest 성공 후 process_source.py는 다음 흐름을 실행한다.

1. rebuild_wiki
2. rebuild_fts
3. build_graph
4. collect paths/status
5. update graph_status
6. update notion_update base fields
7. update summary

권장 구현:

process_source.py는 local_rebuild.py의 public function을 우선 사용한다.

만약 local_rebuild.py가 source_id 기반 rebuild를 이미 통합하고 있다면:

rebuild_after_ingest(source_id, db_path, storage_root) -> dict

같은 함수로 호출한다.

없다면 local_rebuild.py에 reusable function을 추가한다.

## Expected Rebuild Result

rebuild 결과 dict는 최소 다음 필드를 포함해야 한다.

- status
- source_id
- wiki_path
- fts_status
- graph_status
- graph_nodes_count
- graph_edges_count
- errors
- actions

예시:

{
  "status": "ok",
  "source_id": "local_abc123",
  "wiki_path": "wiki/source_summaries/local_abc123.md",
  "fts_status": "built",
  "graph_status": "built",
  "graph_nodes_count": 12,
  "graph_edges_count": 18,
  "errors": []
}

## Status Rules

### Full Success

조건:

- ingest 성공
- wiki summary 생성 성공
- FTS 갱신 성공
- graph build 성공
- notion payload 생성 가능

결과:

status=ok
graph_status=built

### Wiki/FTS Success, Graph Failure

조건:

- ingest 성공
- wiki summary 성공
- FTS 성공
- graph 실패

결과:

status=partial
graph_status=failed
Notion Status=Indexed 또는 Partial
Next Action=Retry graph build.

### Wiki Failure

조건:

- ingest 성공
- wiki summary 실패

결과:

status=partial
graph_status=pending 또는 failed
Next Action=Retry wiki rebuild.

### FTS Failure

조건:

- ingest 성공
- wiki success
- FTS failure

결과:

status=partial
graph_status=pending 또는 failed
Next Action=Retry FTS rebuild.

## Output JSON Update

성공 결과에는 다음 필드가 채워져야 한다.

- source_id
- local_source_path
- raw_path
- wiki_path
- graph_status=built
- actions에 rebuild_wiki ok
- actions에 rebuild_fts ok
- actions에 build_graph ok
- summary.message=Source processed successfully.
- summary.next_action=Ready for search and answer.

부분 실패 결과에는 실패 단계가 명확해야 한다.

actions 예시:

{
  "name": "build_graph",
  "status": "error",
  "error": "Graph build failed."
}

## Dry Run

dry-run에서는 rebuild를 실행하지 않는다.

actions:

- rebuild_wiki skipped dry_run
- rebuild_fts skipped dry_run
- build_graph skipped dry_run

## Tests

tests/test_v05_process_source.py에 다음을 추가한다.

test_process_text_note_e2e_creates_wiki_fts_graph
test_process_markdown_file_e2e_creates_wiki_fts_graph
test_process_url_e2e_creates_wiki_fts_graph
test_process_rebuild_wiki_error_returns_partial
test_process_rebuild_fts_error_returns_partial
test_process_graph_error_returns_partial
test_process_dry_run_skips_rebuild
test_process_success_result_contains_wiki_path
test_process_success_result_sets_graph_status_built

테스트 전략:

- 가능한 경우 temp db와 temp storage root 사용
- 실제 graph 파일이 운영 graph를 오염시키지 않도록 테스트 경로 분리
- 외부 네트워크는 mock
- graph failure는 build function mock으로 유도

## Search Verification

수동 smoke test 이후 다음을 확인한다.

python tools/search_kb.py "v05 local ingest smoke"

python tools/answer.py "v05 local ingest smoke" --format text

검색 결과에 새 source가 반영되어야 한다.

## Runbook Update

docs/runbooks/process-source.md에 end-to-end 사용법을 추가한다.

1. text_note apply
2. search_kb.py 확인
3. answer.py 확인
4. graph status 확인
5. 실패 시 next_action 확인

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- process_source.py apply 후 wiki_path가 생성된다.
- FTS 검색 결과에 새 source가 반영된다.
- graph build가 실행된다.
- graph_status=built가 JSON에 반영된다.
- graph 실패 시 status=partial이 반환된다.
- rebuild 실패 시 실패 단계가 actions에 기록된다.
- dry-run은 rebuild를 실행하지 않는다.
- 기존 compile_wiki.py, build_graph.py 직접 사용법이 깨지지 않는다.

## Verification

전체 테스트:

python -m unittest discover -s tests -p "test_*.py"

수동 apply:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "v05 rebuild smoke" --body "This source should be searchable after rebuild."

검색 확인:

python tools/search_kb.py "v05 rebuild smoke"

답변 확인:

python tools/answer.py "v05 rebuild smoke" --format text

가능하면 다음도 실행:

python scripts/finish_task.py --skip-notion-dry-run

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일
2. rebuild 연결 방식
3. 새 CLI 사용 예시
4. 통과한 테스트
5. 남은 제한 사항