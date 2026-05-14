# Spec 0003: Google Drive Sync

## Status

Accepted

## Scope

이 spec은 v0.3 Google Drive sync의 manifest 기반 dry-run, fixture 기반 local apply, Drive metadata listing, Drive export/download 계약을 정의한다.

> Notion `SPEC - v0.3 Google Drive Sync - ffxiv-claw-bot`에서 2026-05-14 repo docs로 이관 완료.

현재 구현 파일:

- `tools/sync_drive.py`
- `tests/test_sync_drive.py`
- `tests/fixtures/drive_manifest.json`

## Source of truth

Google Drive `FFXIV_KB`는 사람이 관리하는 canonical source다.

로컬 산출물은 파생 캐시다.

- `raw/drive`: Drive 문서의 로컬 캐시
- `wiki`: 검색과 답변용 markdown
- `db/ffxiv.sqlite`: source metadata, FTS, graph 저장소
- `graph`: graph export cache

Drive 문서는 로컬에서 직접 편집하는 것이 아니라 Drive 원본에서 동기화된다.

## source_type

Drive 문서는 `sources.source_type = drive_document`로 기록한다.

dry-run은 DB write를 하지 않는다. 기존 DB record를 읽어 `source_url = gdrive://<drive_file_id>` 형식의 row와 비교한다.

manifest 기반 `--apply`는 fixture content를 `raw/drive`에 저장하고 `sources.source_type = drive_document` row를 upsert한다.

## Manifest 기반 dry-run

CLI는 manifest 기반 dry-run을 지원한다.

```bash
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
```

옵션:

- `--dry-run`: 파일이나 DB를 쓰지 않고 동기화 계획만 출력한다.
- `--manifest <path>`: Drive API 응답을 단순화한 local JSON manifest 경로다. 필수다.
- `--db-path <path>`: 비교에 사용할 SQLite DB 경로다. 기본값은 `db/ffxiv.sqlite`다.

`--dry-run`과 `--apply` 중 정확히 하나를 지정하지 않으면 parser error가 발생한다.

## Manifest 형식

현재 fixture:

```text
tests/fixtures/drive_manifest.json
```

file item에서 dry-run 분류에 필요한 필드:

- `id`: Drive file id
- `name`: Drive file name
- `category`: Drive category folder
- `exportExt`: planned local extension
- `contentHash`: metadata 기반 hash 또는 export/download 결과 SHA256 hash
- `contentFixture`: `--apply`에서 raw file로 저장할 repo-root relative fixture file path

출력에 포함되는 추가 metadata:

- `mimeType`
- `modifiedTime`
- `webViewLink`

## Local raw path 규칙

planned raw path는 다음 형식이다.

```text
raw/drive/<category>/<safe_title>__<drive_file_id>.<ext>
```

`safe_title`, `category`, `drive_file_id`는 lowercase safe path part로 변환된다.

예시:

```text
raw/drive/job_guides/black_mage_7.5_guide__drive_file_001.md
```

## Drive 폴더 구조

초기 Drive 폴더는 다음 구조로 고정한다.

```text
Google Drive/FFXIV_KB/
  patch_notes/
  job_guides/
  raid_guides/
  static_docs/
  macros/
  bis_sheets/
  personal_notes/
```

각 하위 폴더는 `source_type = drive_document` 안에서 category metadata로 해석한다. DB schema 변경을 최소화하기 위해 category 전용 컬럼은 추가하지 않고, manifest와 raw path 규칙으로 category를 보존한다.

## 변경 감지 기준

역할을 분리한다.

- `drive_file_id`: 동일 Drive 문서 식별 기준이다.
- `modifiedTime`: Drive metadata이며 현재 출력에 포함된다. 현재 dry-run 분류의 최종 기준은 아니다.
- `content_hash`: 기존 `sources.content_hash`와 manifest `contentHash`를 비교하는 최종 변경 판단 기준이다.

현재 분류:

- `new`: DB에 같은 `gdrive://<id>` source가 없다.
- `unchanged`: DB에 같은 `gdrive://<id>` source가 있고 hash가 같다.
- `changed`: DB에 같은 `gdrive://<id>` source가 있고 hash가 다르다.
- `skipped`: `id`, `name`, `category`, `exportExt`, `contentHash` 중 필요한 값이 없다.

## JSON 출력 계약

dry-run은 JSON을 출력한다.

최상위 필드:

- `status`
- `dry_run`
- `root_folder`
- `summary`
- `items`

`summary`에는 다음 key가 항상 포함된다.

- `new`
- `changed`
- `unchanged`
- `skipped`

item 주요 필드:

- `drive_file_id`
- `title`
- `category`
- `mime_type`
- `modified_time`
- `source_url`
- `action`
- `planned_raw_path`
- `reason` (`skipped`인 경우)

## Manifest 기반 apply

manifest 기반 `--apply`는 실제 Google Drive API 호출 없이 manifest의 `contentFixture` 파일을 로컬 raw cache로 저장한다.

```bash
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json
```

옵션:

- `--apply`: fixture content를 저장하고 DB를 갱신한다.
- `--manifest <path>`: Drive API 응답을 단순화한 local JSON manifest 경로다. 필수다.
- `--db-path <path>`: 갱신할 SQLite DB 경로다. 기본값은 `db/ffxiv.sqlite`다.
- `--root-path <path>`: `raw/drive`를 쓸 repo root 경로다. 기본값은 repo root다.

apply 동작:

- `new`와 `changed` item은 `contentFixture` 파일 내용을 `raw/drive/<category>/...`에 쓴다.
- `new` item은 deterministic source id `drive_<safe_drive_file_id>`로 insert한다.
- `changed` item은 기존 `gdrive://<drive_file_id>` row를 update한다.
- `unchanged` item은 raw file이나 DB row를 새로 쓰지 않는다.
- `skipped` item은 raw file이나 DB row를 쓰지 않는다.
- `new` 또는 `changed` item에 `contentFixture`가 없으면 apply에서 `skipped`로 처리한다.
- apply도 dry-run과 같은 JSON shape를 출력하되 `dry_run`은 `false`다.

rebuild 연결은 v0.3-05에서 완료되었다. `--apply --rebuild`는 `new`/`changed` 중 text/Markdown/HTML 계열 raw만 compile 대상으로 넘긴다. PDF/이미지 같은 binary raw는 raw cache와 DB에는 저장할 수 있지만 wiki/FTS/graph rebuild 대상에서는 제외한다.

## Drive API 인증과 파일 목록 조회

Drive API 인증/조회는 파일 metadata를 가져와 기존 manifest 형식으로 변환한다. `--download`를 함께 쓰면 metadata 조회 뒤 content export/download까지 수행한다.

```bash
python tools/sync_drive.py --auth
python tools/sync_drive.py --from-drive --dry-run --drive-folder-id <FFXIV_KB_FOLDER_ID>
python tools/sync_drive.py --from-drive --output-manifest /tmp/drive-manifest.json --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

옵션:

- `--auth`: OAuth browser flow를 실행하고 token file을 저장한다.
- `--from-drive`: Google Drive API에서 root folder와 하위 category folder의 file metadata를 재귀적으로 조회한다.
- `--download`: `--from-drive`와 함께 Drive content를 export/download하고 SHA256 `contentHash`를 계산한다.
- `--drive-folder-id <id>`: 조회할 Drive folder id다. v0.3-03에서는 folder search를 하지 않고 명시 입력을 요구한다.
- `--credentials-path <path>`: OAuth client secret JSON path다. 기본값은 `config/google_drive_client_secret.json`이다.
- `--token-path <path>`: OAuth token JSON path다. 기본값은 `config/google_drive_token.json`이다.
- `--output-manifest <path>`: 조회 결과를 manifest JSON으로 저장한다.

`--from-drive --apply`는 raw content가 필요하므로 `--download`와 함께 사용할 때만 지원한다.

Credential/token 규칙:

- `config/google_drive_client_secret.json`과 `config/google_drive_token.json`은 local secret으로 취급한다.
- Git에는 credential/token file을 커밋하지 않는다.
- Drive read scope는 `https://www.googleapis.com/auth/drive.readonly`만 사용한다.
- token이 없으면 `--from-drive`는 actionable error를 출력한다.

Drive API metadata는 기존 manifest item으로 변환된다.

- Google Docs document: `exportExt = md`
- text/plain: `exportExt = txt`
- text/markdown: `exportExt = md`
- folder item은 manifest file 목록에서 제외한다.
- category는 file parent id가 Drive 하위 folder id와 일치하면 해당 folder name을 사용한다.
- `contentHash`는 `--download`가 없으면 `md5Checksum`, `headRevisionId`, `modifiedTime` 순서로 사용한다.
- `--download`가 있으면 실제 export/download content bytes의 SHA256 hex digest를 `contentHash`로 사용한다.

## Drive export/download

`--from-drive --download`는 Drive metadata 조회 후 각 파일의 content를 가져온다.

```bash
python tools/sync_drive.py --from-drive --download --drive-folder-id <FFXIV_KB_FOLDER_ID>
python tools/sync_drive.py --from-drive --download --dry-run --drive-folder-id <FFXIV_KB_FOLDER_ID>
python tools/sync_drive.py --from-drive --download --apply --drive-folder-id <FFXIV_KB_FOLDER_ID>
```

동작:

- Google Docs document는 Drive API `files.export` 계열 호출로 `text/markdown`에 export하고 `.md`로 저장한다.
- Google Sheets는 v0.3-04에서 `skipped`로 처리한다. CSV 변환은 별도 plan에서 다룬다.
- PDF, 이미지, text/plain, text/markdown 같은 일반 Drive file은 file content를 download한다.
- 일반 file의 확장자는 파일명 suffix를 우선 사용하고, 없으면 MIME type mapping을 사용한다.
- export/download bytes의 SHA256 hex digest를 `contentHash`로 사용한다.
- `--apply`가 있으면 기존 apply 흐름과 같은 JSON shape로 출력하고 `raw/drive/<category>/...`와 `sources` DB를 갱신한다.
- `--apply`가 없으면 raw file과 DB를 쓰지 않는다.

## Idempotent 재실행 원칙

반복 실행은 같은 manifest와 같은 DB 상태에서 같은 action summary를 반환해야 한다.

apply는 같은 Drive file id와 같은 content hash에 대해 중복 raw 저장과 중복 DB row 생성을 하지 않는다.

## v0.3 manifest sync 범위 밖

- Discord/OpenClaw 연결
- embedding/vector DB

## v0.3-05: --rebuild (완료)

`sync_drive.py --apply --rebuild`는 apply 직후 compile_wiki와 build_graph를 실행한다.

- `--rebuild`는 `--apply`와 함께 사용해야 한다.
- manifest 기반과 `--from-drive` 양쪽 경로에서 지원한다.
- `new`/`changed` Drive source만 compile 대상으로 수집한다.
- compile_wiki가 `source_type = drive_document`의 Markdown/text raw를 처리한다. (v0.3-05)
- compile_wiki가 `wiki_fts`를 source 단위로 갱신한다.
- `build_graph --source-id`로 graph_nodes/edges를 source 단위로 갱신한다.
- compile 실패 시에도 나머지 source를 계속 처리한다.

```bash
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --rebuild
python tools/sync_drive.py --from-drive --download --apply --drive-folder-id <FFXIV_KB_FOLDER_ID> --rebuild
```

## v0.3 manifest sync 성공 기준

- `sync_drive.py --dry-run --manifest ...`가 JSON을 출력한다.
- `sync_drive.py --apply --manifest ...`가 fixture content를 저장하고 JSON을 출력한다.
- Drive item이 `new`, `changed`, `unchanged`, `skipped`로 분류된다.
- planned raw path가 `raw/drive/<category>/...` 규칙을 따른다.
- 기존 DB record는 `source_url = gdrive://<drive_file_id>`로 식별된다.
- apply는 `sources.source_type = drive_document` row를 idempotent하게 upsert한다.
- default unittest는 실제 Google Drive나 네트워크에 의존하지 않는다.
- Drive metadata response를 manifest JSON 형식으로 변환할 수 있다.
- `--from-drive --download --apply`는 Google Docs를 Markdown으로 export하고 일반 file을 download한 뒤 raw/drive와 DB를 갱신할 수 있다.
- token이 없을 때 `--from-drive`는 명확한 에러를 반환한다.

## 테스트와 확인 명령

```bash
python -m unittest tests.test_sync_drive
python -m unittest discover -s tests -p "test_*.py"
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json
python tools/sync_drive.py --from-drive --dry-run --drive-folder-id <FFXIV_KB_FOLDER_ID>
python tools/sync_drive.py --from-drive --download --apply --drive-folder-id <FFXIV_KB_FOLDER_ID>
```
