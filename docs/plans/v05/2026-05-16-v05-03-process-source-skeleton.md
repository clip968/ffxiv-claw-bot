# v05-03: process_source.py Skeleton

## Goal

`tools/process_source.py`의 기본 CLI skeleton, request validation, dry-run, JSON output 구조를 구현한다.

## Spec Reference

- [Sec 9] Repo Execution Layer
- [Sec 10] Pipeline Steps (Step 1-3)
- [Sec 11] Output Contract
- [Sec 13] Dry Run Semantics
- [Sec 14.1] Validation Error
- [Sec 20.1] Test Plan (validation tests)

## Tasks

### 1. Create `tools/process_source.py`

- [ ] `argparse` 기반 CLI argument parsing
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
- [ ] Request validation 함수
  - source_type validation (지원된 값인지)
  - category validation (지원된 값인지)
  - 필수 인자 존재 여부 (source_type별 conditional required)
  - `--apply`와 `--dry-run` 동시 지정 방지
  - 파일 입력 시 파일 존재 여부 확인
  - URL 형식 기본 검증

### 2. Action log 구조

- [ ] `ProcessResult` 또는 dict 기반 action log 구조 정의
  - 각 action: name, status(ok/skipped/error), optional reason/error
  - 전체 status 계산: ok/partial/error/skipped
- [ ] dry-run mode: 모든 action을 `status=skipped, reason=dry_run`으로 설정

### 3. JSON output

- [ ] 성공/실패 통일된 JSON 포맷으로 stdout 출력
- [ ] Output contract: status, source_id, source_type, category, title, local_source_path, raw_path, wiki_path, graph_status, actions, notion_update, summary

### 4. Tests (`tests/test_v05_process_source.py`)

- [ ] `test_process_missing_body_returns_error` — text_note without body
- [ ] `test_process_missing_url_returns_error` — url without URL
- [ ] `test_process_missing_local_path_returns_error` — file without path
- [ ] `test_process_dry_run_returns_skipped_status`
- [ ] `test_process_apply_and_dry_run_mutual_exclusion`

## Red Test

`tests/test_v05_process_source.py`

## Completion

- `tools/process_source.py` exists with CLI parsing
- `--dry-run` returns valid skipped JSON
- Validation errors return error JSON
- Test file exists with 5+ validation tests
