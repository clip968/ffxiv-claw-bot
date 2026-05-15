# v0.4-03: Ingest Local Note CLI

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- Contract: `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
- Runbook: `docs/runbooks/local-storage.md`

## Status

**Implemented 2026-05-15**

## Goal

OpenClaw/Discord 저장 요청을 Local Storage에 저장하는 CLI를 만든다.

이 plan은 adapter-facing CLI facade를 소유한다. storage path/category/source_id 규칙은 v04-01을 재사용하고, rebuild는 v04-04, Notion/Discord 결과 반영은 v04-05로 넘긴다.

## Scope

지원 입력:

- `text_note`
- `markdown_file`
- `plain_text_file`
- `url`

보류 또는 metadata-only:

- `binary_attachment`

기본 CLI는 dry-run/apply를 분리하고 JSON result를 출력한다. Notion update는 옵션 또는 adapter 단계로 분리한다.

## Expected Actions

CLI result에는 다음 storage actions가 포함될 수 있지만, 규칙은 v04-01 Local Storage Foundation을 따른다.

- `validate_request`
- `write_local_source`
- `snapshot_raw`
- `upsert_source`

`compile_wiki`, `index_fts`, `build_graph`, `update_notion_status`는 v04-04/v04-05 연결 단계에서 다룬다.

## Red Test

- File: `tests/test_v04_ingest_local_cli.py`
- Implementation target: `tools/ingest_local.py`
- Expected callable: `main(argv)`
- Current red reason: module/function does not exist yet.
- Contract fixed by the test:
  - `text_note` dry-run accepts `--source-type`, `--category`, `--title`, `--body`, `--storage-root`, and `--db-path`.
  - Dry-run outputs JSON actions in this order: `validate_request`, `write_local_source`, `snapshot_raw`, `upsert_source`.
  - Dry-run does not write the local source file and does not perform `update_notion_status`.

## Checklist

- [x] CLI 이름 결정: `tools/ingest_local.py` — 별도 CLI facade로 구현
- [x] `--dry-run`, `--apply`, `--storage-root`, `--db-path` 옵션 구현
- [x] text/markdown/plain text body를 local source로 저장 (`--apply`에서만)
- [x] url 입력은 source metadata와 canonical path를 분리해 기록 (source_type=url 지원, body/source_id는 동일 체계)
- [x] binary attachment는 metadata-only 또는 unsupported로 처리 (source_type 허용하지만 body가 필수는 아님)
- [x] result JSON을 v04-00 contract와 맞춘다 (actions, summary, status, dry_run)
- [x] Notion update는 이 CLI의 필수 side effect로 만들지 않는다 (`update_notion_status`가 dry-run action 목록에 없음)
- [x] compile/index/graph rebuild는 이 CLI에서 직접 구현하지 않고 v04-04/v04-05로 넘긴다

## Verification

```bash
python -m unittest tests.test_v04_ingest_local_cli
python tools/ingest_local.py --dry-run --source-type text_note --category personal_notes --title "Test" --body "hello"
python tools/ingest_local.py --apply --source-type text_note --category personal_notes --title "Test" --body "hello" --storage-root /tmp/test-storage --db-path /tmp/test-ffxiv.sqlite
python scripts/check_docs_freshness.py --all
```

## Implementation Notes

- Red test: `tests/test_v04_ingest_local_cli.py` test_text_note_dry_run_outputs_local_ingest_actions_without_writing_files → **Green**
- Module: `tools/ingest_local.py` exposes `main(argv)` callable.
- Reuses `tools.sync_storage` helpers: `safe_path_part`, `local_source_id`, `VALID_CATEGORIES`, `LOCAL_REQUEST_SOURCE_TYPES`.
- Dry-run outputs: `validate_request` (ok), `write_local_source` (planned), `snapshot_raw` (planned), `upsert_source` (planned).
- Apply mode performs actual file writes and DB upsert with the same security checks as `sync_storage.py` (path traversal rejection, storage root existence).

## Key Decisions

- OpenClaw adapter는 repo CLI의 JSON 입출력에만 의존한다.
- 파일 쓰기와 DB upsert는 CLI `--apply`에서만 일어난다.
- Notion에는 CLI 결과를 받은 adapter가 상태만 기록한다.
