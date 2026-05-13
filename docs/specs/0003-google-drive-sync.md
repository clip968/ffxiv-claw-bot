# Spec 0003: Google Drive Sync

## Status

Accepted

## Scope

이 spec은 v0.3 Google Drive sync의 현재 구현 계약을 정의한다.

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

현재 v0.3 구현은 DB write를 하지 않는다. 기존 DB record를 읽어 `source_url = gdrive://<drive_file_id>` 형식의 row와 비교한다.

## Manifest 기반 dry-run

현재 구현된 CLI는 manifest 기반 dry-run만 지원한다.

```bash
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
```

옵션:

- `--dry-run`: 파일이나 DB를 쓰지 않고 동기화 계획만 출력한다.
- `--manifest <path>`: Drive API 응답을 단순화한 local JSON manifest 경로다. 필수다.
- `--db-path <path>`: 비교에 사용할 SQLite DB 경로다. 기본값은 `db/ffxiv.sqlite`다.

`--dry-run` 없이 실행하면 parser error가 발생한다.

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
- `contentHash`: export/download 결과의 hash 역할

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

manifest 기반 `--apply`는 현재 구현되어 있지 않다.

현재 v0.3은 dry-run으로 동기화 계획을 검증하는 단계다. 파일 write, `sources` upsert, wiki/FTS/graph rebuild 연결은 이후 작업이다.

## Idempotent 재실행 원칙

반복 실행은 같은 manifest와 같은 DB 상태에서 같은 action summary를 반환해야 한다.

향후 apply 구현은 같은 Drive file id와 같은 content hash에 대해 중복 raw 저장과 중복 DB row 생성을 하지 않아야 한다.

## v0.3 범위 밖

- 실제 OAuth
- 실제 Google Drive API 호출
- Google Docs export/download
- Discord/OpenClaw 연결
- embedding/vector DB
- Drive 변경 감지 후 wiki/FTS/graph 자동 재빌드

## 성공 기준

- `sync_drive.py --dry-run --manifest ...`가 JSON을 출력한다.
- Drive item이 `new`, `changed`, `unchanged`, `skipped`로 분류된다.
- planned raw path가 `raw/drive/<category>/...` 규칙을 따른다.
- 기존 DB record는 `source_url = gdrive://<drive_file_id>`로 식별된다.
- 실제 Google Drive나 네트워크에 의존하지 않는다.

## 테스트와 확인 명령

```bash
python -m unittest tests.test_sync_drive
python -m unittest discover -s tests -p "test_*.py"
python tools/sync_drive.py --dry-run --manifest tests/fixtures/drive_manifest.json
```
