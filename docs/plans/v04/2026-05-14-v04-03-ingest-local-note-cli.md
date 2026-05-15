# v0.4-03: Ingest Local Note CLI

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- Contract: `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
- Runbook: `docs/runbooks/local-storage.md`

## Status

**Proposed**

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

## Checklist

- [ ] CLI 이름 결정: `tools/ingest_local.py` 또는 기존 `tools/sync_storage.py` 확장
- [ ] `--dry-run`, `--apply`, `--manifest`, `--storage-root`, `--db-path` 옵션 정리
- [ ] text/markdown/plain text body를 local source로 저장
- [ ] url 입력은 source metadata와 canonical path를 분리해 기록
- [ ] binary attachment는 metadata-only 또는 unsupported로 처리
- [ ] result JSON을 v04-00 contract와 맞춘다
- [ ] Notion update는 이 CLI의 필수 side effect로 만들지 않는다
- [ ] compile/index/graph rebuild는 이 CLI에서 직접 구현하지 않고 v04-04 플래그 또는 wrapper로 넘긴다

## Verification

```bash
python -m unittest tests.test_sync_storage
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json
python tools/sync_storage.py --apply --manifest tests/fixtures/storage_manifest.json --storage-root /tmp/test-storage --db-path /tmp/test-ffxiv.sqlite
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- OpenClaw adapter는 repo CLI의 JSON 입출력에만 의존한다.
- 파일 쓰기와 DB upsert는 CLI `--apply`에서만 일어난다.
- Notion에는 CLI 결과를 받은 adapter가 상태만 기록한다.
