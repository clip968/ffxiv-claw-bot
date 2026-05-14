# ADR 0005: Drive Write Scope, Upload, and Duplicate Policy

## Status

Accepted for optional legacy integration. Superseded for the default operating path by `docs/adrs/0006-local-storage-and-notion-control.md`.

## Context

v0.3까지의 Google Drive 연동은 read-only sync/export/download 중심이었다. v0.4에서는 OpenClaw/Discord 저장 요청을 Drive canonical source에 직접 반영해야 한다.

2026-05-14 이후 기본 운영 경로는 `/mnt/d/ffixiv-bot-storage`와 OpenClaw의 Notion direct control로 전환한다. 이 ADR은 Drive write 기능을 삭제하지 않고 optional legacy integration으로 유지하기 위한 결정 기록이다.

이를 위해 다음 결정이 필요했다:
1. OAuth scope: 어떤 쓰기 권한으로 Drive API를 호출할지
2. Upload 방식: Markdown/텍스트를 Google Docs 문서로 convert할지, 원본 형식 그대로 upload할지
3. 중복 정책: 같은 title 파일이 이미 Drive에 있을 때 처리 방식
4. Category folder ID 관리: CLI 매번 입력 vs config file에 등록
5. CLI 구조: `sync_drive.py`에 write를 추가할지, 별도 CLI로 분리할지

관련 문서:
- `docs/plans/v04/2026-05-14-v04-01-drive-write-foundation.md`
- `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`
- `docs/specs/0003-google-drive-sync.md`
- `docs/adrs/0002-drive-is-canonical-source.md`

## Decision

1. **Scope: `drive` (full)**
   - 기존 `drive.readonly`(sync/export/download)와 별도로 `drive` scope token 관리
   - 기존 `FFXIV_KB` 폴더를 읽고, 폴더 안에 새 파일을 생성하고, 필요 시 기존 파일을 수정/삭제할 수 있는 권한
   - `drive.file`(앱 전용 파일만 접근)은 기존 폴더 구조를 읽을 수 없어서 부적합
   - `drive.readonly + drive.file` 조합은 기존 폴더 읽기 + 새 파일 생성은 가능하지만, 추후 기존 파일 수정/삭제가 필요할 때 재인증 필요
   - 처음부터 `drive`(full)로 가는 것이 향후 변경 가능성(파일 수정, 삭제)을 고려할 때 재인증 비용을 줄일 수 있음

2. **Upload 방식: 원본 파일 upload (Google Docs convert 안 함)**
   - `.md`/`.txt` 파일을 Drive API `files.create`로 직접 upload
   - Google Docs 문서로 convert하지 않음 (원본 형식 보존)
   - 추후 필요 시 Google Docs convert 옵션을 추가할 수 있도록 확장 가능하게 설계

3. **중복 정책: Timestamp append**
   - 같은 title + 같은 category 파일이 이미 Drive에 있을 때, 파일명에 `__YYYY-MM-DD` timestamp를 추가
   - 예: `My Note__2026-05-14.md`
   - Overwrite는 의도치 않은 데이터 손실 위험이 있음
   - New revision은 Google Docs 형식에서만 의미 있음 (file upload에서는 무의미)

4. **Category folder ID: Config file (`config/drive_folders.yaml`)**
   - category별 folder ID를 YAML config file에 등록
   - CLI flag로 --folder-id를 매번 입력하는 것은 사용성 저하
   - config file로 한 번 설정하면 --category만으로 선택 가능
   - fixture에도 포함하여 테스트 가능

5. **CLI 구조: 별도 `tools/publish_drive.py`로 분리**
   - `sync_drive.py`는 Drive → local read-only sync 책임 유지
   - `publish_drive.py`는 local/OpenClaw → Drive write 책임
   - 책임 분리로 각 CLI의 복잡도와 테스트 범위를 명확히 구분
   - dry-run/apply 패턴은 `sync_drive.py`와 동일하게 유지

## Consequences

Good:
- Drive full scope로 추후 파일 수정/삭제가 필요해도 재인증 불필요
- 원본 파일 upload로 형식이 변하지 않음 (raw/drive와 동일한 포맷 유지)
- Timestamp append로 데이터 손실 없음
- Config file로 사용성 향상
- 별도 CLI로 각 도구의 책임이 명확함

Tradeoff:
- `drive` (full) scope는 read-only보다 위험 부담이 크며, OAuth 재인증 필요
- Config file을 최초에 설정해야 하는 초기 비용 있음
- Timestamp append로 동일 내용의 중복 파일이 쌓일 가능성 있음 (별도 정리 필요 시 추후)
