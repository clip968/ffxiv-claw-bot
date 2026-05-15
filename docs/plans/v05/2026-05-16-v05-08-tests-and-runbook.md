# v0.5-08 Plan: Tests and Runbook

## Goal

v0.5 Source Processing Pipeline의 테스트, runbook, handoff 문서를 정리하고, 사용자가 실제로 process_source.py를 운영할 수 있게 한다.

이번 task는 v0.5의 마무리 작업이다.

## Background

v0.5는 다음을 통합한다.

- OpenClaw Skill Layer
- process_source.py
- text_note ingest
- markdown_file ingest
- plain_text_file ingest
- URL fetch + ingest
- wiki rebuild
- FTS rebuild
- graph build
- Notion update payload 생성

v0.5-08에서는 전체 흐름이 문서와 테스트로 닫히는지 확인한다.

## Scope

이번 task에서 수행할 것:

1. v0.5 전체 unit/integration test 정리
2. docs/runbooks/process-source.md 작성 또는 갱신
3. docs/handoff/CURRENT_HANDOFF.md 갱신
4. docs/WORKFLOW.md 갱신
5. agent.md 또는 CLAUDE.md 갱신
6. 수동 smoke test 절차 작성
7. 완료 보고 형식 고정

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- 새 기능 추가
- Notion polling
- crawler
- scheduler
- Discord runtime
- vector DB
- embedding

이번 task는 검증과 운영 문서화 단계다.

## Files to Add

docs/runbooks/process-source.md

필요한 경우:

docs/skills/ffxiv-source-processing.md

## Files to Update

tests/test_v05_process_source.py
tests/test_v05_fetch_url.py
tests/test_v04_status_notification.py
docs/handoff/CURRENT_HANDOFF.md
docs/WORKFLOW.md
agent.md
CLAUDE.md

## Test Inventory

v0.5 완료 시 다음 테스트가 존재해야 한다.

### process_source.py Skeleton Tests

- test_process_dry_run_text_note_returns_skipped
- test_process_dry_run_url_returns_skipped
- test_process_missing_body_returns_error
- test_process_missing_url_returns_error
- test_process_missing_local_path_returns_error
- test_process_file_not_found_returns_error
- test_process_invalid_source_type_returns_error
- test_process_invalid_category_returns_error
- test_process_apply_and_dry_run_mutually_exclusive

### Local Source Integration Tests

- test_process_text_note_apply_creates_source
- test_process_markdown_file_apply_creates_source
- test_process_plain_text_file_apply_creates_source
- test_process_ingest_error_skips_rebuild
- test_process_duplicate_source_returns_skipped_or_reuse
- test_process_apply_uses_storage_root
- test_process_apply_uses_db_path

### URL Integration Tests

- test_fetch_url_html_ok
- test_fetch_url_plain_text_ok
- test_fetch_url_http_error
- test_fetch_url_timeout
- test_fetch_url_unsupported_content_type
- test_fetch_url_extracts_title
- test_fetch_url_rejects_empty_body
- test_process_url_apply_creates_source
- test_process_url_fetch_error_skips_ingest
- test_process_url_uses_cli_title_when_provided
- test_process_url_uses_fetched_title_when_title_missing
- test_process_url_notion_payload_excludes_full_body

### Rebuild Integration Tests

- test_process_text_note_e2e_creates_wiki_fts_graph
- test_process_markdown_file_e2e_creates_wiki_fts_graph
- test_process_url_e2e_creates_wiki_fts_graph
- test_process_rebuild_wiki_error_returns_partial
- test_process_rebuild_fts_error_returns_partial
- test_process_graph_error_returns_partial
- test_process_dry_run_skips_rebuild
- test_process_success_result_contains_wiki_path
- test_process_success_result_sets_graph_status_built

### Notion Payload Tests

- test_process_success_includes_notion_update
- test_process_graph_built_maps_to_notion_graph_built
- test_process_graph_failed_maps_to_notion_failed_or_partial
- test_process_validation_error_maps_to_notion_error
- test_process_dry_run_maps_to_notion_skipped
- test_process_notion_payload_excludes_body
- test_process_notion_payload_excludes_raw_html
- test_process_notion_payload_excludes_attachment_data

## Test Strategy

테스트는 운영 데이터와 분리되어야 한다.

원칙:

1. 실제 /mnt/d/ffixiv-bot-storage를 오염시키지 않는다.
2. tempfile.TemporaryDirectory를 storage root로 사용한다.
3. 임시 sqlite db를 사용한다.
4. URL 테스트는 실제 인터넷에 의존하지 않는다.
5. 네트워크 호출은 mock한다.
6. graph 파일이 운영 graph를 오염시키지 않게 한다.
7. stdout JSON은 항상 parse 가능한지 확인한다.

## Runbook Content

docs/runbooks/process-source.md에는 다음 항목을 포함한다.

### 1. Overview

process_source.py는 source 하나를 Local Storage, wiki, FTS, graph, Notion payload까지 처리하는 v0.5 공식 entrypoint다.

### 2. Supported Source Types

- text_note
- markdown_file
- plain_text_file
- url

### 3. Basic Commands

text_note dry-run:

python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "Dry Run" --body "Hello"

text_note apply:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "Apply" --body "Hello"

markdown_file apply:

python tools/process_source.py --apply --source-type markdown_file --category raid_guides --local-path "/mnt/d/ffixiv-bot-storage/incoming/guide.md"

plain_text_file apply:

python tools/process_source.py --apply --source-type plain_text_file --category personal_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/note.txt"

url apply:

python tools/process_source.py --apply --source-type url --category patch_notes --url "https://example.com"

### 4. Output JSON 읽는 법

중요 필드:

- status
- source_id
- graph_status
- local_source_path
- raw_path
- wiki_path
- actions
- notion_update
- summary.next_action

### 5. Status Meaning

status=ok:
모든 처리 성공

status=partial:
source는 저장됐지만 rebuild/graph/notion payload 일부 실패

status=error:
처리 실패

status=skipped:
dry-run 또는 duplicate

### 6. Notion Update

process_source.py는 Notion API를 직접 호출하지 않는다.

OpenClaw는 notion_update payload를 읽어 Notion DB를 갱신한다.

### 7. Search Verification

처리 후 검색:

python tools/search_kb.py "keyword"

답변 확인:

python tools/answer.py "question" --format text

### 8. Troubleshooting

Missing body:
--body를 제공한다.

Missing URL:
--url을 제공한다.

Graph failed:
graph build를 재시도한다.

Fetch failed:
URL 접근 가능 여부와 content type을 확인한다.

No search result:
FTS rebuild 여부와 검색어를 확인한다.

Korean search weak:
영문 고유명사 또는 FFXIV 용어를 함께 사용한다.

## Handoff Update

docs/handoff/CURRENT_HANDOFF.md에는 다음을 포함한다.

- v0.5 완료 여부
- process_source.py 사용법
- 지원 source_type
- 현재 제한 사항
- v0.6 다음 목표

v0.6로 넘길 내용:

- Notion queue schema
- Notion New 항목 처리 loop
- source_registry.yml
- allowlist crawler
- scheduler/cron runbook

## WORKFLOW Update

docs/WORKFLOW.md에는 v0.5 이후 기본 workflow를 반영한다.

이전:

OpenClaw가 ingest_local.py, local_rebuild.py, status_notification.py를 순서대로 직접 호출

이후:

OpenClaw가 process_source.py를 우선 호출
결과 JSON의 notion_update를 사용해 Notion 갱신

## Agent Instruction Update

agent.md 또는 CLAUDE.md에는 다음 원칙을 추가한다.

- source 처리 요청은 process_source.py를 우선 사용한다.
- 개별 tool 호출은 진단 또는 fallback에만 사용한다.
- URL/file/text source가 명확하면 추가 질문 없이 처리한다.
- category가 불명확하면 질문한다.
- 최신 정보를 알아서 찾는 요청은 v0.6 범위이며, v0.5에서는 사용자가 URL을 제공해야 한다.
- Google Drive를 기본 경로로 사용하지 않는다.
- Notion을 원본 저장소로 사용하지 않는다.

## Final Verification Commands

전체 테스트:

python -m unittest discover -s tests -p "test_*.py"

문서 검사:

python scripts/check_docs_freshness.py --all

완료 스크립트:

python scripts/finish_task.py --skip-notion-dry-run

수동 dry-run:

python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "v05 final dry run" --body "This should not be written."

수동 apply:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "v05 final apply" --body "This should be searchable."

검색 확인:

python tools/search_kb.py "v05 final apply"

답변 확인:

python tools/answer.py "v05 final apply" --format text

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- v0.5 관련 테스트가 정리되어 있다.
- 전체 테스트가 통과한다.
- docs/runbooks/process-source.md가 존재한다.
- handoff 문서가 갱신되어 있다.
- WORKFLOW 문서가 갱신되어 있다.
- agent.md 또는 CLAUDE.md가 process_source.py 우선 사용을 설명한다.
- 사용자가 process_source.py를 직접 실행할 수 있는 예시가 있다.
- OpenClaw가 process_source.py 결과 JSON을 어떻게 해석할지 문서화되어 있다.
- v0.6로 넘어갈 남은 작업이 명확하다.

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일

2. 새 CLI 사용 예시

3. 통과한 테스트

4. 남은 제한 사항

예시:

1. 추가/수정한 파일
- tools/process_source.py
- tools/fetch_url.py
- tests/test_v05_process_source.py
- tests/test_v05_fetch_url.py
- docs/runbooks/process-source.md
- docs/handoff/CURRENT_HANDOFF.md

2. 새 CLI 사용 예시
python tools/process_source.py --apply --source-type text_note --category personal_notes --title "Example" --body "Hello"

3. 통과한 테스트
python -m unittest discover -s tests -p "test_*.py"
Result: OK

4. 남은 제한 사항
- Notion polling은 아직 없음
- allowlist crawler는 아직 없음
- scheduler는 아직 없음
- 사용자가 source를 직접 제공해야 함