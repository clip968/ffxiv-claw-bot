# Sync Drive Runbook

## 원칙

Google Drive `FFXIV_KB`는 사람이 관리하는 canonical source다.

`raw/drive`, `wiki`, `db/ffxiv.sqlite`, FTS, graph는 로컬 파생 캐시다.

기본 unittest와 manifest fixture 흐름은 실제 Google API를 호출하지 않는다. manifest fixture를 읽어 dry-run 계획을 출력하거나 fixture content를 local raw cache에 적용한다.

`--from-drive`는 Google Drive API에서 metadata를 조회하므로 local OAuth token과 Google client dependency가 필요하다.

`--from-drive --download`는 metadata 조회 뒤 Drive content까지 가져오므로 네트워크와 Drive API export/download 권한이 필요하다.

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
조회는 root folder에서 시작해 하위 category folder까지 재귀적으로 진행한다.

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

## Drive export/download

Drive에서 content까지 가져와 manifest JSON으로 확인한다.

```bash
python tools/sync_drive.py --from-drive \
  --download \
  --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

쓰기 없이 실제 downloaded content hash 기준으로 dry-run을 확인한다.

```bash
python tools/sync_drive.py --from-drive \
  --download \
  --dry-run \
  --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

Drive content를 `raw/drive`에 저장하고 `sources` DB를 갱신한다.

```bash
python tools/sync_drive.py --from-drive \
  --download \
  --apply \
  --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

실험에서 실제 repo `raw/`와 `db/ffxiv.sqlite`를 건드리고 싶지 않으면 임시 경로를 지정한다.

```bash
python tools/sync_drive.py --from-drive \
  --download \
  --apply \
  --drive-folder-id <FFXIV_KB_FOLDER_ID> \
  --db-path /tmp/ffxiv-drive-download.sqlite \
  --root-path /tmp/ffxiv-claw-bot-drive-download
```

동작:

- Google Docs는 `text/markdown`으로 export하고 `.md`로 저장한다.
- Google Sheets는 v0.3-04에서 `skipped`로 처리한다.
- PDF, 이미지, text/plain, text/markdown 같은 일반 파일은 binary content를 download한다.
- `content_hash`는 downloaded bytes의 SHA256 hex digest다.
- `--from-drive --apply`만 단독으로 실행하면 parser error가 난다. 실제 raw content 저장에는 `--download`가 필요하다.

## Rebuild (wiki/FTS/graph)

`--apply`와 `--rebuild`를 함께 사용하면 apply 직후 compile_wiki와 build_graph를 실행한다.

manifest 기반:

```bash
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --rebuild
```

Drive API 기반:

```bash
python tools/sync_drive.py --from-drive --download --apply --drive-folder-id <FFXIV_KB_FOLDER_ID> --rebuild
```

동작:

- `new`/`changed` Drive source만 compile 대상으로 수집한다.
- compile_wiki가 source_type `drive_document`의 Markdown/text/HTML 계열 raw를 처리한다.
- PDF/이미지 같은 binary raw는 raw cache와 DB에는 저장할 수 있지만 rebuild 대상에서는 제외한다.
- compile_wiki가 `wiki_fts`를 source 단위로 갱신한다.
- `build_graph --source-id`로 graph_nodes/edges를 source 단위로 갱신한다.
- compile 실패 시에도 나머지 source 처리 계속 진행한다.
- `--rebuild`는 `--apply` 없이 단독 실행할 수 없다.

## 현재 한계

- Google Sheets CSV 변환 없음
