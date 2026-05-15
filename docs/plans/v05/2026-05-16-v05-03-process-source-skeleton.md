# v0.5-03: process_source.py Skeleton

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 9] Repo Execution Layer, [Sec 10] Pipeline Steps (Step 1-3), [Sec 11] Output Contract, [Sec 13] Dry Run Semantics, [Sec 14.1] Validation Error

## Status

**Completed 2026-05-16**

## Goal

`tools/process_source.py`의 기본 CLI skeleton, request validation, dry-run, JSON output 구조를 구현한다.

## Scope

- `argparse` 기반 CLI argument parsing
- Request validation 함수
- Action log 구조 (`ProcessResult` / dict)
- dry-run mode: 모든 action을 `status=skipped, reason=dry_run`으로 설정
- 통일된 JSON output 포맷
- `tests/test_v05_process_source.py` 테스트 5개

CLI arguments:
- `--apply` / `--dry-run` (mutual exclusive)
- `--source-type` (required)
- `--category` (required)
- `--title` (optional)
- `--body` (required if source_type=text_note)
- `--local-path` (required if source_type=markdown_file or plain_text_file)
- `--url` (required if source_type=url)
- `--storage-root` (default `/mnt/d/ffixiv-bot-storage`)
- `--db-path` (default `db/ffxiv.sqlite`)
- `--notion-page-id` (optional)

Out of scope:

- 실제 ingest 로직 연결
- URL fetch 구현
- rebuild 연결
- Notion payload 생성

## Red Test

- File: `tests/test_v05_process_source.py`
- Implementation target: `tools/process_source.py`
- Verified red reason: module/function did not exist yet.
- Contract fixed by the test:
  - `text_note` without body returns error JSON.
  - `url` source type without `--url` returns error JSON.
  - File source types without `--local-path` returns error JSON.
  - Dry-run returns status=`skipped` with all actions skipped.
  - `--apply` and `--dry-run` simultaneous usage returns error.

## Checklist

- [x] `argparse` CLI argument parsing 구현
- [x] source_type validation (지원된 값인지)
- [x] category validation (지원된 값인지)
- [x] source_type별 conditional required 인자 검증
- [x] `--apply`와 `--dry-run` 동시 지정 방지
- [x] 파일 입력 시 파일 존재 여부 확인
- [x] URL 형식 기본 검증
- [x] `ProcessResult` / dict 기반 action log 구조 정의
  - [x] 각 action: name, status(ok/skipped/error), optional reason/error
  - [x] 전체 status 계산: ok/error/skipped
- [x] dry-run mode: side-effect action을 `status=skipped, reason=dry_run`으로 설정
- [x] 통일된 JSON output 포맷으로 stdout 출력
  - [x] Output contract: status, source_id, source_type, category, title, local_source_path, raw_path, wiki_path, graph_status, actions, notion_update, summary
- [x] `tests/test_v05_process_source.py` 테스트 작성:
  - [x] `test_process_missing_body_returns_error` — text_note without body
  - [x] `test_process_missing_url_returns_error` — url without URL
  - [x] `test_process_missing_local_path_returns_error` — file without path
  - [x] `test_process_file_not_found_returns_error`
  - [x] `test_process_dry_run_returns_skipped_status_and_contract_fields`
  - [x] `test_process_dry_run_cli_script_execution_prints_json`
  - [x] `test_process_apply_and_dry_run_mutual_exclusion`

## Verification

```bash
python -m unittest tests.test_v05_process_source -v
python tools/process_source.py --dry-run --source-type text_note --category personal_notes --title "Test" --body "hello"
python tools/process_source.py --dry-run --source-type url --category patch_notes --url "https://example.com"
```

## Key Decisions

- `tools/process_source.py`는 v0.5의 단일 entrypoint다.
- dry-run은 절대 파일/DB를 변경하지 않는다.
- validation error는 JSON error response로 반환하고 종료한다.
- v0.5-03에서는 `--apply`의 실제 ingest/rebuild를 구현하지 않는다. 유효한 apply 요청은 JSON error로 막고 v0.5-04 이후 구현 범위로 남긴다.

## Implementation Notes

- Created `tools/process_source.py`.
- Public entrypoint: `main(argv)`.
- Supported source types: `text_note`, `markdown_file`, `plain_text_file`, `url`, `binary_attachment`.
- Supported categories follow the v0.5 spec: `urls`, `documents`, `sheets`, `patch_notes`, `raid_guides`, `job_guides`, `static_docs`, `macros`, `bis_sheets`, `personal_notes`.
- Validation errors and dry-run results are always printed as stdout JSON.
- Dry-run returns `status=skipped`, `graph_status=skipped`, `notion_update={}`, and does not create files, DB rows, wiki files, graph files, or Notion updates.

## Verification Results

```bash
python -m unittest tests.test_v05_process_source -v
# 8 tests, OK
```
