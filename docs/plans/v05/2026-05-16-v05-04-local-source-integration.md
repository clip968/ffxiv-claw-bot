# v0.5-04 Plan: Local Source Integration

## Goal

process_source.py가 text_note, markdown_file, plain_text_file 입력을 실제 Local Storage ingest로 연결하도록 구현한다.

이번 task가 끝나면 사용자가 제공한 텍스트나 로컬 파일을 process_source.py 하나로 sources DB에 등록하고 raw/local_storage snapshot까지 만들 수 있어야 한다.

## Background

v0.4에는 이미 tools/ingest_local.py가 존재한다.

v0.5에서는 process_source.py가 새로운 저장 규칙을 만들면 안 된다. 기존 ingest_local.py의 정책을 재사용해야 한다.

즉, process_source.py는 orchestrator이고, ingest_local.py가 source 저장의 권위 있는 구현이다.

## Scope

이번 task에서 구현할 것:

1. process_source.py에서 ingest_local.py 로직 호출
2. text_note 실제 apply 처리
3. markdown_file 실제 apply 처리
4. plain_text_file 실제 apply 처리
5. ingest 결과를 output JSON에 반영
6. ingest 실패 handling
7. local source 관련 unit/integration test 추가

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- URL fetch
- wiki rebuild
- FTS rebuild
- graph build
- Notion API 호출
- crawler
- scheduler

이번 task는 ingest까지만 확실히 한다.

## Files to Update

tools/process_source.py
tests/test_v05_process_source.py
docs/runbooks/process-source.md
docs/handoff/CURRENT_HANDOFF.md

필요한 경우:

tools/ingest_local.py

단, ingest_local.py는 기존 동작을 깨지 않는 범위에서만 수정한다.

## Input Types

이번 task에서 실제 apply를 지원할 source_type:

- text_note
- markdown_file
- plain_text_file

## Required Behavior

### text_note

입력:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "P12S note" --body "Use Reprisal."

기대 결과:

- /mnt/d/ffixiv-bot-storage/sources/personal_notes 아래 canonical source가 생성된다.
- repo raw/local_storage 아래 snapshot이 생성된다.
- db/ffxiv.sqlite sources 테이블에 row가 등록된다.
- source_id가 result JSON에 포함된다.
- status는 후속 rebuild가 아직 없으면 ok 또는 partial이 아니라 ingest-only 상태 정책에 맞춰 반환한다.

권장:
- 이번 task에서 rebuild가 아직 연결되지 않았다면 status=partial, graph_status=pending으로 반환한다.
- 다음 task v0.5-06에서 rebuild까지 연결되면 status=ok로 승격한다.

### markdown_file

입력:

python tools/process_source.py --apply --source-type markdown_file --category raid_guides --local-path "/mnt/d/ffixiv-bot-storage/incoming/p12s.md"

기대 결과:

- local_path 파일을 읽는다.
- ingest_local.py의 markdown_file 처리 경로를 사용한다.
- canonical source와 raw snapshot을 생성한다.
- source_id를 반환한다.

### plain_text_file

입력:

python tools/process_source.py --apply --source-type plain_text_file --category personal_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/note.txt"

기대 결과:

- local_path 파일을 읽는다.
- plain text로 ingest한다.
- source_id를 반환한다.

## Integration Approach

가능하면 ingest_local.py 내부 함수를 import해서 사용한다.

만약 ingest_local.py가 CLI 중심으로만 작성되어 있다면 두 선택지가 있다.

Option A:
ingest_local.py에서 reusable function을 추출한다.

예시 함수:
ingest_local_source(request) -> dict

Option B:
process_source.py에서 subprocess로 ingest_local.py를 호출한다.

권장:
Option A를 우선한다.

이유:
- 테스트가 쉽다.
- JSON 파싱 실패 가능성이 줄어든다.
- Python 내부 예외 처리가 명확하다.

단, 기존 구조가 크게 깨질 경우 Option B로 시작해도 된다.

## Expected Ingest Result Fields

ingest 결과에서 process_source.py가 수집해야 할 필드:

- status
- source_id
- source_type
- category
- title
- canonical_path
- raw_path
- content_hash
- dedupe_status 또는 duplicate 여부
- error

이 필드가 ingest_local.py에 없다면 backward-compatible하게 추가한다.

## Output JSON Update

ingest 성공 후 process_source.py output은 최소 다음 필드를 포함해야 한다.

- status
- source_id
- source_type
- category
- title
- local_source_path
- raw_path
- graph_status
- actions
- notion_update
- summary

rebuild가 아직 연결되지 않은 경우:

graph_status=pending

summary.next_action:
Run rebuild step.

## Error Handling

### Ingest Error

ingest_local.py가 실패하면:

status=error
source_id=null 또는 ingest가 반환한 값
graph_status=skipped

actions에는 다음이 있어야 한다.

- validate_request ok
- ingest_local error
- rebuild skipped

### Duplicate

ingest_local.py가 duplicate를 반환하면:

기본 정책:

status=skipped
reason=duplicate
existing_source_id=...

단, 기존 ingest_local.py 정책이 reuse라면 그 정책을 우선한다.

## Tests

tests/test_v05_process_source.py에 다음을 추가한다.

test_process_text_note_apply_creates_source
test_process_markdown_file_apply_creates_source
test_process_plain_text_file_apply_creates_source
test_process_ingest_error_skips_rebuild
test_process_duplicate_source_returns_skipped_or_reuse
test_process_apply_uses_storage_root
test_process_apply_uses_db_path

테스트 전략:

- tempfile.TemporaryDirectory를 storage_root로 사용한다.
- 임시 sqlite db path를 사용한다.
- 테스트가 실제 /mnt/d/ffixiv-bot-storage를 오염시키지 않게 한다.
- markdown_file/plain_text_file 테스트는 임시 파일을 생성해서 수행한다.

## Runbook Update

docs/runbooks/process-source.md에 다음 예시를 추가한다.

text_note apply:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "Test note" --body "Hello"

markdown_file apply:

python tools/process_source.py --apply --source-type markdown_file --category raid_guides --local-path "/mnt/d/ffixiv-bot-storage/incoming/guide.md"

plain_text_file apply:

python tools/process_source.py --apply --source-type plain_text_file --category personal_notes --local-path "/mnt/d/ffixiv-bot-storage/incoming/note.txt"

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- process_source.py --apply --source-type text_note가 실제 source를 생성한다.
- process_source.py --apply --source-type markdown_file이 실제 source를 생성한다.
- process_source.py --apply --source-type plain_text_file이 실제 source를 생성한다.
- ingest 결과 source_id가 JSON에 포함된다.
- raw_path와 local_source_path가 JSON에 포함된다.
- ingest 실패 시 rebuild를 시도하지 않는다.
- 테스트가 실제 운영 storage root를 오염시키지 않는다.
- 기존 ingest_local.py 직접 사용법이 깨지지 않는다.

## Verification

다음 테스트를 실행한다.

python -m unittest discover -s tests -p "test_*.py"

수동 smoke test:

python tools/process_source.py --apply --source-type text_note --category personal_notes --title "v05 local ingest smoke" --body "This is a v0.5 local ingest smoke test."

결과 확인:

- JSON에 source_id가 있는지
- local_source_path가 있는지
- raw_path가 있는지
- db/ffxiv.sqlite에 row가 있는지

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일
2. 지원되는 local source type
3. 새 CLI 사용 예시
4. 통과한 테스트
5. 남은 제한 사항