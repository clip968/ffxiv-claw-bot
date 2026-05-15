# v0.4-02: Local Storage Ingest CLI

## Historical Notice

This file records the first Local Storage ingest CLI implementation slice. Under the refreshed v0.4 feature map, the active implementation plan is `docs/plans/v04/2026-05-14-v04-03-ingest-local-note-cli.md`.

The refreshed v04-02 slot is now `docs/plans/v04/2026-05-14-v04-02-openclaw-notion-control-contract.md`.

## Spec

- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- `docs/adrs/0006-local-storage-and-notion-control.md`
- Master plan: `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

Legacy reference:
- `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
- `docs/plans/v04/legacy/2026-05-14-v04-01-drive-write-foundation.md`

## Status

**Proposed**

First implementation slice added `tools/sync_storage.py` dry-run skeleton only. Actual file write/apply is deferred.

## Context

OpenClaw adapter가 직접 DB, graph, wiki, 파일 시스템을 모두 만지면 테스트와 재사용이 어렵다.
Discord/OpenClaw 입력과 Notion 상태판 처리 대상은 먼저 repo-local CLI 또는 sync utility로 정규화한다.

기본 운영 경로는 Drive publish가 아니라 Local Storage다. 원본 파일은 `/mnt/d/ffixiv-bot-storage`에 두고, repo 내부에는 처리용 snapshot과 파생 산출물만 둔다.

## Local Storage Layout

```text
/mnt/d/ffixiv-bot-storage/
  incoming/
  sources/
    urls/
    documents/
    sheets/
    patch_notes/
    raid_guides/
    job_guides/
    static_docs/
    macros/
    bis_sheets/
    personal_notes/
  exports/
    markdown/
    text/
    html/
  manifests/
  archive/
```

## Ingest Request JSON

```json
{
  "source_type": "text_note | markdown_file | plain_text_file | binary_attachment | url",
  "content_type": "text/markdown | text/plain | application/pdf | ...",
  "title": "문서 제목",
  "body": "텍스트 내용",
  "url": "https://...",
  "attachments": [],
  "category": "patch_notes | job_guides | raid_guides | static_docs | macros | bis_sheets | personal_notes",
  "author": "Discord 사용자명 또는 ID",
  "channel": "Discord 채널 ID 또는 mention",
  "created_at": "2026-05-14T12:00:00Z"
}
```

## Ingest Result JSON

```json
{
  "status": "ok | partial | error",
  "dry_run": true,
  "actions": [
    {
      "action": "write_local_source",
      "target": "/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md",
      "status": "planned",
      "message": "Dry-run: would write local source"
    },
    {
      "action": "snapshot_raw",
      "target": "raw/local_storage/job_guides/black_mage_7_5__local_001.md",
      "status": "planned",
      "message": "Dry-run: would create processing snapshot"
    }
  ]
}
```

Action 의미:

| Action | Meaning |
|---|---|
| `write_local_source` | `/mnt/d/ffixiv-bot-storage/sources/<category>/...`에 원본 저장 |
| `snapshot_raw` | `raw/local_storage/<category>/...`에 처리용 snapshot 생성 |
| `upsert_source` | `db/ffxiv.sqlite` sources 테이블 갱신 |
| `compile_wiki` | LLM Wiki markdown 생성 또는 갱신 |
| `build_graph` | graph nodes/edges 갱신 |
| `update_notion_status` | Notion 상태판에 처리 결과 기록 |

## Manifest Sync Skeleton

`tools/sync_storage.py --dry-run --manifest <manifest>`는 첫 구현 범위로 허용한다.

Manifest item 개념:

```json
{
  "source_id": "local_001",
  "title": "Black Mage 7.5 Guide",
  "category": "job_guides",
  "source_type": "markdown_file",
  "content_type": "text/markdown",
  "canonical_path": "sources/job_guides/black_mage_7_5.md",
  "content_hash": "sha256..."
}
```

Dry-run 분류:

- `new`: DB에 같은 `local://<canonical_path>` source가 없다.
- `changed`: DB에 같은 source가 있고 `content_hash`가 다르다.
- `unchanged`: DB에 같은 source가 있고 `content_hash`가 같다.
- `skipped`: 필수 metadata가 부족하거나 category가 허용 목록에 없다.

Planned raw path:

```text
raw/local_storage/<category>/<safe_title>__<source_id>.<ext>
```

## Checklist

- [x] `tools/sync_storage.py` dry-run skeleton 신설
- [x] `tests/fixtures/storage_manifest.json` 신설
- [x] `tests/test_sync_storage.py` 신설
- [x] manifest 기반 `new`, `changed`, `unchanged`, `skipped` 분류
- [x] planned `raw/local_storage` path 생성
- [x] JSON result 출력
- [x] `--apply` 모드: `write_local_source`, `snapshot_raw`, `upsert_source` 구현
- [ ] Notion update는 local CLI result를 받은 OpenClaw adapter 단계에서 처리
  - (v0.4-02 범위 아님. OpenClaw adapter 단계에서 sync_storage.py JSON 결과를 읽어 Notion 상태판 기록)

## Verification

```bash
python -m unittest tests.test_sync_storage
python -m unittest discover -s tests -p "test_*.py"
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json
python tools/sync_storage.py --apply --manifest tests/fixtures/storage_manifest.json --storage-root /tmp/test-storage --db-path /tmp/test-ffxiv.sqlite
```

## Key Decisions

- Discord/OpenClaw adapter는 repo CLI의 JSON 입출력만 의존한다.
- Notion에는 파일 자체가 아니라 local path와 처리 상태만 기록한다.
- Local-only 저장 모드가 기본이다.
- Drive publish는 기본 경로에서 제외하고 optional legacy integration으로 유지한다.
