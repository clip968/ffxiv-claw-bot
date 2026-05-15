# v0.5-03: process_source.py Skeleton

## Spec

- Master plan: `docs/plans/v05/README.md`
- Pipeline spec: `docs/specs/0004-v05-source-processing-pipeline.md`
- Sections: [Sec 9] Repo Execution Layer, [Sec 10] Pipeline Steps (Step 1-3), [Sec 11] Output Contract, [Sec 13] Dry Run Semantics, [Sec 14.1] Validation Error

## Status

**Pending**

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
- Current red reason: module/function does not exist yet.
- Contract fixed by the test:
  - `text_note` without body returns error JSON.
  - `url` source type without `--url` returns error JSON.
  - File source types without `--local-path` returns error JSON.
  - Dry-run returns status=`skipped` with all actions skipped.
  - `--apply` and `--dry-run` simultaneous usage returns error.

## Checklist

- [ ] `argparse` CLI argument parsing 구현
- [ ] source_type validation (지원된 값인지)
- [ ] category validation (지원된 값인지)
- [ ] source_type별 conditional required 인자 검증
- [ ] `--apply`와 `--dry-run` 동시 지정 방지
- [ ] 파일 입력 시 파일 존재 여부 확인
- [ ] URL 형식 기본 검증
- [ ] `ProcessResult` / dict 기반 action log 구조 정의
  - [ ] 각 action: name, status(ok/skipped/error), optional reason/error
  - [ ] 전체 status 계산: ok/partial/error/skipped
- [ ] dry-run mode: 모든 action을 `status=skipped, reason=dry_run`으로 설정
- [ ] 통일된 JSON output 포맷으로 stdout 출력
  - [ ] Output contract: status, source_id, source_type, category, title, local_source_path, raw_path, wiki_path, graph_status, actions, notion_update, summary
- [ ] `tests/test_v05_process_source.py` 테스트 5개 작성:
  - [ ] `test_process_missing_body_returns_error` — text_note without body
  - [ ] `test_process_missing_url_returns_error` — url without URL
  - [ ] `test_process_missing_local_path_returns_error` — file without path
  - [ ] `test_process_dry_run_returns_skipped_status`
  - [ ] `test_process_apply_and_dry_run_mutual_exclusion`

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
