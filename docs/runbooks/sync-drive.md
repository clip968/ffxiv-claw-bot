# Sync Drive Runbook

## 원칙

Google Drive `FFXIV_KB`는 사람이 관리하는 canonical source다.

`raw/drive`, `wiki`, `db/ffxiv.sqlite`, FTS, graph는 로컬 파생 캐시다.

현재 구현은 실제 Google API를 호출하지 않는다. manifest fixture를 읽어 dry-run 계획을 출력한다.

## Manifest fixture

현재 fixture:

```text
tests/fixtures/drive_manifest.json
```

## Dry-run 실행

```bash
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
```

다른 DB 파일과 비교하려면:

```bash
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json --db-path db/ffxiv.sqlite
```

## 출력 JSON 해석

최상위:

- `status`: 실행 상태
- `dry_run`: true
- `root_folder`: manifest root folder
- `summary`: action별 개수
- `items`: 파일별 계획

action:

- `new`: 기존 `sources`에 같은 `gdrive://<drive_file_id>`가 없다.
- `changed`: 기존 source는 있지만 `content_hash`가 다르다.
- `unchanged`: 기존 source가 있고 `content_hash`가 같다.
- `skipped`: dry-run에 필요한 metadata가 부족하다.

planned path:

```text
raw/drive/<category>/<safe_title>__<drive_file_id>.<ext>
```

## Apply

`--apply`는 현재 구현되어 있지 않다.

현재 `tools/sync_drive.py`는 `--dry-run` 없이 실행하면 parser error를 반환한다.

## 현재 한계

- 실제 OAuth 없음
- 실제 Google Drive API 호출 없음
- Google Docs export/download 없음
- raw file write 없음
- `sources` upsert 없음
- wiki/FTS/graph rebuild 연결 없음
