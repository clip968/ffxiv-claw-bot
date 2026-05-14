# Sync Drive Runbook

## 원칙

Google Drive `FFXIV_KB`는 사람이 관리하는 canonical source다.

`raw/drive`, `wiki`, `db/ffxiv.sqlite`, FTS, graph는 로컬 파생 캐시다.

기본 unittest와 manifest fixture 흐름은 실제 Google API를 호출하지 않는다. manifest fixture를 읽어 dry-run 계획을 출력하거나 fixture content를 local raw cache에 적용한다.

`--from-drive`는 Google Drive API에서 metadata를 조회하므로 local OAuth token과 Google client dependency가 필요하다.

## Manifest fixture

현재 fixture:

```text
tests/fixtures/drive_manifest.json
```

`--apply`는 manifest의 `contentFixture`가 가리키는 repo-root relative file을 raw cache에 저장한다.

## Dry-run 실행

```bash
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
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

fixture 기반 local apply:

```bash
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json
```

동작:

- `new`, `changed`: `contentFixture` 내용을 `raw/drive/<category>/...`에 쓰고 `sources`를 upsert한다.
- `unchanged`: raw file과 DB를 새로 쓰지 않는다.
- `skipped`: raw file과 DB를 쓰지 않는다.
- `new` 또는 `changed`에 `contentFixture`가 없으면 `skipped`로 처리한다.
- 같은 manifest를 재실행해도 같은 Drive file id에 대해 중복 DB row를 만들지 않는다.

테스트나 실험에서 실제 repo `raw/`와 `db/ffxiv.sqlite`를 건드리고 싶지 않으면 임시 경로를 지정한다.

```bash
python tools/sync_drive.py --apply \
  --manifest tests/fixtures/drive_manifest.json \
  --db-path /tmp/ffxiv.sqlite \
  --root-path /tmp/ffxiv-claw-bot-apply
```

`tools/sync_drive.py`는 `--dry-run`과 `--apply` 중 정확히 하나를 지정하지 않으면 parser error를 반환한다.

## Drive API 인증

OAuth client secret은 Google Cloud Console에서 Desktop application으로 만든다.

기본 local secret path:

```text
config/google_drive_client_secret.json
config/google_drive_token.json
```

인증:

```bash
python tools/sync_drive.py --auth
```

다른 경로를 쓰려면:

```bash
python tools/sync_drive.py --auth \
  --credentials-path /path/to/client_secret.json \
  --token-path /path/to/token.json
```

`--from-drive`에서 token이 없으면 먼저 `--auth`를 실행해야 한다.

## Drive 파일 목록 조회

FFXIV_KB folder id를 명시해서 조회한다.

```bash
python tools/sync_drive.py --from-drive \
  --dry-run \
  --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

조회 결과를 manifest로 저장:

```bash
python tools/sync_drive.py --from-drive \
  --drive-folder-id <FFXIV_KB_FOLDER_ID> \
  --output-manifest /tmp/drive-manifest.json
```

저장된 manifest는 기존 dry-run/apply 흐름에서 재사용한다.

```bash
python tools/sync_drive.py --dry-run --manifest /tmp/drive-manifest.json
```

`--from-drive --apply`는 아직 지원하지 않는다. Drive metadata만으로는 raw content를 저장할 수 없으므로 v0.3-04 export/download 이후 연결한다.

## 현재 한계

- Google Docs export/download 없음
- wiki/FTS/graph rebuild 연결 없음
