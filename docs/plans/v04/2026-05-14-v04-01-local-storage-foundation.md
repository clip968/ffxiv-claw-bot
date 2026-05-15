# v0.4-01: Local Storage Foundation

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- ADR: `docs/adrs/0006-local-storage-and-notion-control.md`
- Runbook: `docs/runbooks/local-storage.md`

## Status

**Implemented**

All checklist items complete. 11/11 tests pass (`tests/test_sync_storage.py`).

## Goal

원본 파일을 `/mnt/d/ffixiv-bot-storage`에 저장하고, repo 내부에는 처리용 snapshot과 파생 산출물만 두는 Local Storage 기반을 만든다.

## Scope

- Local storage root 구조 정의
- category 검증
- safe filename 생성
- 중복 title 처리 정책
- manifest 기반 dry-run
- `raw/local_storage` snapshot path 생성
- `sources` DB upsert 계약

Out of scope:

- OpenClaw/Discord request normalization
- `compile_wiki.py` 또는 `build_graph.py` 실행
- Notion 상태판 갱신
- Discord/OpenClaw 사용자 메시지 생성

## Local Storage Contract

기본 root:

```text
/mnt/d/ffixiv-bot-storage/
```

원본 저장 위치:

```text
/mnt/d/ffixiv-bot-storage/sources/<category>/<safe_title>.<ext>
```

처리 snapshot 위치:

```text
raw/local_storage/<category>/<safe_title>__<source_id>.<ext>
```

DB 식별:

```text
source_url = local://sources/<category>/<filename>
source_type = local_file | local_document
```

## Checklist

- [x] `VALID_CATEGORIES`와 local storage category 목록 일치 확인
- [x] safe filename 규칙을 문서화하고 테스트한다
- [x] 같은 title + category가 있을 때 timestamp append 또는 deterministic suffix 정책 결정
- [x] manifest dry-run 결과가 `new`, `changed`, `unchanged`, `skipped`를 반환하는지 확인
- [x] apply 결과가 `write_local_source`, `snapshot_raw`, `upsert_source` action을 반환하는지 확인
- [x] `docs/runbooks/local-storage.md`와 결과 JSON 예시를 맞춘다
- [x] v04-03 CLI가 이 storage foundation을 재사용하고 규칙을 중복 정의하지 않도록 interface를 명확히 한다

## Verification

```bash
python -m unittest tests.test_sync_storage
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- Local Storage가 기본 원본 파일 저장소다.
- Notion에는 파일 자체를 올리지 않는다.
- Drive publish는 이 plan의 범위가 아니며 legacy integration으로만 유지한다.
