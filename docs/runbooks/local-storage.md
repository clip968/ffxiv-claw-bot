# Local Storage Runbook

## 원칙

기본 원본 파일 저장소는 `/mnt/d/ffixiv-bot-storage`다.

repo 내부 `raw/local_storage`, `wiki`, `graph`, `db/ffxiv.sqlite`는 봇 실행용 캐시 또는 파생 산출물이다. 원본 파일을 repo 내부에 대량 저장하지 않는다.

Google Drive 기반 `sync_drive.py`와 `publish_drive.py`는 Legacy / Deferred optional integration으로 유지한다.

## Directory Layout

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

역할:

- `incoming/`: 아직 분류하지 않은 임시 파일
- `sources/`: 사용자가 관리하는 원본 파일
- `exports/`: xlsx, pdf, docx 같은 파일에서 추출한 md/txt/html 변환본
- `manifests/`: 동기화 테스트용 manifest JSON
- `archive/`: 더 이상 활성 사용하지 않지만 보존할 자료

## Manifest Sync Apply

`--dry-run`과 같은 manifest 구조를 사용하며, 실제로 파일을 쓰고 DB를 갱신한다.

```bash
python tools/sync_storage.py --apply --manifest tests/fixtures/storage_manifest.json
```

### Apply 과정 (item별)

1. **`write_local_source`**: `/mnt/d/ffixiv-bot-storage/sources/<category>/...`에 원본 쓰기 (manifest의 `body` 필드 사용)
   - body가 없고 대상 파일이 이미 있으면 skipped
   - body가 없고 대상 파일도 없으면 failed
2. **`snapshot_raw`**: `raw/local_storage/<category>/...`에 처리용 snapshot 생성
3. **`upsert_source`**: `db/ffxiv.sqlite` sources 테이블에 `local://<canonical_path>` upsert

### 결과 JSON

```json
{
  "status": "ok | partial | error",
  "dry_run": false,
  "storage_root": "/mnt/d/ffixiv-bot-storage",
  "summary": {
    "write_local_source": 1,
    "snapshot_raw": 1,
    "upsert_source": 1,
    "unchanged": 1,
    "failed": 0,
    "skipped": 0
  },
  "actions": [
    {
      "action": "write_local_source",
      "source_id": "local_001",
      "target": "/mnt/d/ffixiv-bot-storage/sources/job_guides/black_mage_7_5.md",
      "status": "written",
      "message": "Written 45 bytes to ..."
    }
  ]
}
```

`status` 값:

- `"ok"`: 모든 new/changed 항목이 성공적으로 처리됨
- `"partial"`: 일부 항목이 실패함 (body 누락 등 데이터 문제)
- `"error"`: `canonical_path` path traversal 같은 보안/입력 오류가 포함됨

path traversal 거부 시 action 예시:

```json
{
  "action": "write_local_source",
  "source_id": "local_escape",
  "target": "...",
  "status": "failed",
  "error_type": "invalid_input",
  "message": "canonical_path '../outside.md' resolves outside storage_root '...'"
}
```

## Source Type and Storage Root Rules

- Request-level `source_type` values such as `text_note`, `markdown_file`, `plain_text_file`, `binary_attachment`, and `url` describe how OpenClaw or Discord received the input.
- DB-level `sources.source_type` for Local Storage text/markdown sources is normalized to `local_document` unless the manifest already uses `local_file` or `local_document`.
- `compile_wiki.py` uses DB `source_type` to decide whether raw content should be read as local text/markdown. This is why request source types must not be stored directly as DB source types.
- `--apply` requires the configured storage root to already exist and be a directory. Missing roots fail with `error_type = local_storage_root_missing`; the CLI does not create the canonical external source root automatically.
- `raw/local_storage/` is a derived processing snapshot directory and is ignored by Git.

## Manifest Dry-run

현재 구현된 첫 범위는 manifest 기반 dry-run이다.

```bash
python tools/sync_storage.py --dry-run --manifest tests/fixtures/storage_manifest.json
```

예상 manifest item:

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

분류:

- `new`: DB에 같은 `local://<canonical_path>` source가 없다.
- `changed`: DB에 같은 source가 있고 `content_hash`가 다르다.
- `unchanged`: DB에 같은 source가 있고 `content_hash`가 같다.
- `skipped`: 필수 metadata가 부족하거나 category가 허용 목록에 없다.

Planned snapshot path:

```text
raw/local_storage/<category>/<safe_title>__<source_id>.<ext>
```

## Ingest Local CLI (`tools/ingest_local.py`)

v04-03 CLI facade for OpenClaw/Discord request to Local Storage ingestion.

```bash
# Dry-run: plan only, no writes
python tools/ingest_local.py --dry-run --source-type text_note --category personal_notes --title "Raid note" --body "Use Reprisal"

# Apply: write source, snapshot, upsert DB
python tools/ingest_local.py --apply --source-type text_note --category personal_notes --title "Raid note" --body "Use Reprisal" --storage-root /mnt/d/ffixiv-bot-storage --db-path db/ffxiv.sqlite
```

Supports `--source-type`: `text_note`, `markdown_file`, `plain_text_file`, `url`, `binary_attachment`.

Dry-run outputs these actions in order: `validate_request` → `write_local_source` → `snapshot_raw` → `upsert_source`.

Result JSON follows v04-00 contract format with `actions`, `summary`, `status`, `dry_run`.

`--apply` mode computes `content_hash = SHA-256(body)` and stores it in the `sources.content_hash` column (NOT NULL). Both INSERT and UPDATE paths include `content_hash`. Regression tests in `tests/test_v04_ingest_local_cli.py` verify this behavior.

### Reusable Ingest Function

`tools/ingest_local.py` also exposes `ingest_source(...)` for `tools/process_source.py`.

`process_source.py` uses this function in v05-04 for:

- `text_note`: pass `--body` directly as ingest body.
- `markdown_file`: read `--local-path` as UTF-8 text and ingest the content.
- `plain_text_file`: read `--local-path` as UTF-8 text and ingest the content.

For v05 local source processing, all three local text source types are stored under:

```text
{storage_root}/sources/{category}/{title_slug}.md
```

That means `plain_text_file` input is copied into a canonical `.md` Local Storage path and a `.md` raw snapshot. The body is not otherwise transformed in v05-04.

`ingest_source()` accepts a `root_path` argument so tests can create raw snapshots under a temporary repo root instead of writing to the checkout's real `raw/local_storage/` directory.

## Full Pipeline Target

최종 목표 pipeline:

```text
원본 파일 감지
-> raw/local_storage snapshot 생성
-> sources DB upsert
-> compile_wiki.py 로 LLM Wiki 문서 생성
-> wiki_fts 색인
-> build_graph.py 로 graph nodes/edges 생성
-> search_kb.py 와 answer.py 에서 FTS + graph traversal 기반 답변
```

## 보류 범위 (향후 작업)

다음 동작은 아직 구현되지 않았다.

- Notion 상태판 status mapping은 `tools/openclaw_notion_control.py`의 `build_notion_update(result)`로 구현됨 (v04-02). 실제 Notion API 호출은 OpenClaw adapter 단계에서 처리한다.
- `compile_wiki.py` + `build_graph.py` 자동 호출은 `tools/local_rebuild.py`로 구현됨 (v04-04). `rebuild_after_ingest()` 참고.

## Legacy / Deferred

Drive 기반 명령은 삭제하지 않는다.

```bash
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
python tools/publish_drive.py --dry-run --category personal_notes --title "Test" --body "hello"
```

이 명령은 cloud sync가 필요할 때 optional integration으로 재검토한다.
