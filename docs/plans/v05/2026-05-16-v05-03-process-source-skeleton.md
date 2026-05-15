# v0.5-03 Plan: process_source.py Skeleton

## Goal

tools/process_source.py의 기본 골격을 구현한다.

이번 task의 목표는 아직 실제 ingest/rebuild를 완성하는 것이 아니라, CLI argument parsing, request validation, dry-run, JSON output contract, action log 구조를 먼저 고정하는 것이다.

## Background

v0.5에서 process_source.py는 source 하나를 처리하는 공식 entrypoint다.

OpenClaw는 여러 도구를 직접 조합하는 대신 process_source.py를 우선 호출한다.

따라서 process_source.py는 항상 machine-readable JSON을 stdout으로 출력해야 한다.

## Scope

이번 task에서 구현할 것:

1. tools/process_source.py 파일 생성
2. argparse 기반 CLI 추가
3. 지원 source_type 정의
4. 지원 category 정의
5. request validation 추가
6. action log 구조 추가
7. dry-run support 추가
8. output JSON contract skeleton 구현
9. 기본 unit test 작성

## Non-Goals

이번 task에서는 다음을 구현하지 않는다.

- 실제 Local Storage ingest
- 실제 URL fetch
- 실제 wiki rebuild
- 실제 FTS rebuild
- 실제 graph build
- 실제 Notion API 호출
- 실제 Notion payload 완성
- dedupe 처리

이번 task는 skeleton 단계다.

## Files to Add

tools/process_source.py
tests/test_v05_process_source.py

## Files to Update

docs/handoff/CURRENT_HANDOFF.md

필요한 경우:

docs/runbooks/process-source.md

## CLI Contract

지원해야 하는 기본 CLI:

python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "Test" --body "Hello"

python tools/process_source.py --dry-run --source-type markdown_file --category raid_guides --local-path "/path/to/file.md"

python tools/process_source.py --dry-run --source-type plain_text_file --category personal_notes --local-path "/path/to/file.txt"

python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com"

## Required Arguments

공통 필수:

- --apply 또는 --dry-run 중 하나
- --source-type
- --category

source_type별 필수:

text_note:
- --body

markdown_file:
- --local-path

plain_text_file:
- --local-path

url:
- --url

선택 인자:

- --title
- --storage-root
- --db-path
- --notion-page-id

기본값:

--storage-root /mnt/d/ffixiv-bot-storage
--db-path db/ffxiv.sqlite

## Validation Rules

검증 실패 시:

- 파일을 쓰지 않는다.
- DB를 수정하지 않는다.
- stdout에 JSON을 출력한다.
- exit code는 1 또는 정책상 0 중 하나로 고정한다.

권장:
- 자동화 도구가 JSON을 항상 읽을 수 있게 stdout JSON은 항상 출력한다.
- validation error는 top-level status=error로 반환한다.
- exit code는 error에서 1을 반환한다.

검증 항목:

1. --apply와 --dry-run이 동시에 지정되지 않았는지
2. --apply와 --dry-run 중 하나는 반드시 있는지
3. source_type이 허용 목록에 있는지
4. category가 허용 목록에 있는지
5. source_type=text_note이면 body가 있는지
6. source_type=url이면 url이 있는지
7. source_type=markdown_file이면 local_path가 있는지
8. source_type=plain_text_file이면 local_path가 있는지
9. local_path 입력이면 파일이 존재하는지
10. url 입력이면 http 또는 https scheme인지

## Internal Data Structure

process_source.py 내부에서는 request dict를 만든다.

필드:

- apply
- dry_run
- source_type
- category
- title
- body
- url
- local_path
- storage_root
- db_path
- notion_page_id

action log entry 형식:

- name
- status
- reason
- error
- details

예시:

{
  "name": "validate_request",
  "status": "ok"
}

{
  "name": "ingest_local",
  "status": "skipped",
  "reason": "dry_run"
}

## Output Contract

dry-run 성공 예시:

{
  "status": "skipped",
  "dry_run": true,
  "source_id": null,
  "source_type": "text_note",
  "category": "personal_notes",
  "title": "Test",
  "graph_status": "skipped",
  "actions": [
    {
      "name": "validate_request",
      "status": "ok"
    },
    {
      "name": "ingest_local",
      "status": "skipped",
      "reason": "dry_run"
    },
    {
      "name": "rebuild",
      "status": "skipped",
      "reason": "dry_run"
    }
  ],
  "notion_update": {
    "Status": "Skipped",
    "Graph Status": "Skipped",
    "Next Action": "Run with --apply to persist the source."
  },
  "summary": {
    "message": "Dry run completed. No files or database rows were written.",
    "next_action": "Run with --apply to persist the source."
  }
}

validation error 예시:

{
  "status": "error",
  "dry_run": false,
  "source_id": null,
  "source_type": "url",
  "category": "patch_notes",
  "title": null,
  "graph_status": "skipped",
  "actions": [
    {
      "name": "validate_request",
      "status": "error",
      "error": "Missing required argument: --url"
    }
  ],
  "notion_update": {
    "Status": "Error",
    "Graph Status": "Skipped",
    "Last Error": "Missing required argument: --url",
    "Next Action": "Provide a valid URL."
  },
  "summary": {
    "message": "Request validation failed.",
    "next_action": "Provide a valid URL."
  }
}

## Implementation Steps

### Step 1. Create tools/process_source.py

구조:

- parse_args()
- build_request(args)
- validate_request(request)
- build_error_result(request, error)
- build_dry_run_result(request)
- main()

### Step 2. Add Constants

정의:

SUPPORTED_SOURCE_TYPES
SUPPORTED_CATEGORIES
DEFAULT_STORAGE_ROOT
DEFAULT_DB_PATH

### Step 3. Implement Argument Parsing

argparse를 사용한다.

mutually exclusive group:

- --apply
- --dry-run

source input args:

- --body
- --url
- --local-path

metadata args:

- --title
- --category
- --source-type
- --storage-root
- --db-path
- --notion-page-id

### Step 4. Implement Validation

validate_request(request)는 성공 시 None 또는 빈 list를 반환한다.

실패 시 error message를 반환한다.

검증은 실제 작업 전 가장 먼저 수행한다.

### Step 5. Implement Dry Run

dry-run에서는 ingest/rebuild를 호출하지 않는다.

다만 action log에는 다음이 포함되어야 한다.

- validate_request ok
- ingest_local skipped dry_run
- rebuild skipped dry_run
- build_notion_update skipped 또는 ok

### Step 6. Implement JSON Printing

모든 결과는 json.dumps(..., ensure_ascii=False, indent=2)로 출력한다.

stdout에는 JSON 외 다른 로그를 출력하지 않는다.

필요한 debug log는 stderr로 보낸다.

## Tests

tests/test_v05_process_source.py에 다음 테스트를 추가한다.

test_process_dry_run_text_note_returns_skipped
test_process_dry_run_url_returns_skipped
test_process_missing_body_returns_error
test_process_missing_url_returns_error
test_process_missing_local_path_returns_error
test_process_file_not_found_returns_error
test_process_invalid_source_type_returns_error
test_process_invalid_category_returns_error
test_process_apply_and_dry_run_mutually_exclusive

테스트는 subprocess로 CLI를 호출하거나, 내부 main helper를 직접 호출하는 방식 중 하나를 선택한다.

권장:
- 핵심 로직은 함수로 분리해 unit test
- CLI 동작은 최소 smoke test만 subprocess로 확인

## Acceptance Criteria

이 task는 다음 조건을 만족하면 완료다.

- tools/process_source.py가 존재한다.
- --dry-run text_note 요청이 JSON을 반환한다.
- --dry-run url 요청이 JSON을 반환한다.
- 필수 인자가 없으면 status=error JSON을 반환한다.
- file path가 없으면 status=error JSON을 반환한다.
- stdout에 JSON 외 텍스트가 섞이지 않는다.
- dry-run은 파일과 DB를 변경하지 않는다.
- 기본 unit test가 통과한다.

## Verification

다음 명령을 실행한다.

python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "Smoke" --body "Hello"

python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com"

python -m unittest discover -s tests -p "test_*.py"

가능하면 다음도 실행한다.

python scripts/finish_task.py --skip-notion-dry-run

## Completion Report Format

완료 보고에는 다음만 포함한다.

1. 추가/수정한 파일
2. 지원하는 CLI 인자
3. 통과한 테스트
4. 남은 제한 사항