# v0.4-01: Drive Write Foundation

## Legacy / Deferred Notice

This plan is completed and preserved, but it is no longer part of the default v0.4 operating path.

Current default v0.4 planning uses `/mnt/d/ffixiv-bot-storage` as the canonical local source store and OpenClaw Notion direct control as the status/task/index layer. See `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`.

`tools/publish_drive.py`, `tools/sync_drive.py`, and related tests remain available as Legacy / Deferred / Optional Integration for future cloud sync needs.

## Spec

- `docs/specs/0003-google-drive-sync.md`
- `docs/specs/01-architecture.md`
- `docs/adrs/0002-drive-is-canonical-source.md`
- `docs/adrs/0005-drive-write-scope-and-upload.md`
- Master plan: `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`
- Ingest contract: `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md`

## Status

**Completed 2026-05-14** — code review fixes applied

## Context

현재 Drive 연동은 read-only sync/export/download 중심이다.
OpenClaw가 받은 저장 요청을 Drive canonical source에 반영하려면 Drive file create/upload 기능과 write 가능한 OAuth scope가 필요하다.

이 plan은 v04-00 ingest contract의 request/result JSON 계약을 기준으로 Drive write 기반을 구현한다.

## 설계 결정 (ADR 0005)

| 항목 | 결정 | 근거 |
|---|---|---|
| OAuth scope | `drive` (full) | 기존 폴더 읽기 + 파일 생성 + 추후 수정/삭제 가능 |
| Upload 방식 | 원본 파일 upload (Google Docs convert 안 함) | 원본 형식 보존, raw/drive와 포맷 일관성 |
| 중복 정책 | Timestamp append (`__YYYY-MM-DD`) | 데이터 손실 방지 |
| Folder ID 관리 | `config/drive_folders.yaml` config file | 사용성, 재사용성 |
| CLI 구조 | `tools/publish_drive.py` (별도 신설) | sync_drive.py read-only 책임 유지 |

## Checklist

### CLI 구조
- [x] `tools/publish_drive.py` 신설 (별도 CLI)
- [x] dry-run/apply 패턴 유지 (spec0003과 일관성)
- [x] v04-00 계약의 result JSON 출력 형식 사용

### OAuth / Token
- [x] scope: `drive` (full) — 기존 `drive.readonly` token과 별도 관리
- [x] `--auth` 플래그로 Drive full scope OAuth flow 실행
- [x] credential path: `config/google_drive_client_secret.json` (기존과 동일)
- [x] token path: `config/google_drive_token_write.json` (기존 read-only와 분리)
- [x] token 없을 때 actionable error 출력

### Category folder ID
- [x] config file 방식: `config/drive_folders.yaml`
- [x] config file 파싱 및 검증
- [x] config file 없거나 category 누락 시 actionable error
- [x] fixture 추가: `tests/fixtures/drive_folders.yaml`

### Dry-run 동작
- [x] dry-run: Drive API 호출 없음, 계획만 출력
- [x] 출력: ingest 계약 result JSON (dry_run: true)
- [x] `action`: `drive_upload` (신규)
- [x] `drive_file_id`: 예상 ID (placeholder)
- [x] `raw_path`: 예상 raw 경로
- [x] `rebuild_status`: `pending`

### Apply 동작
- [x] apply: Drive API `files.create` 호출
- [x] Markdown 파일 upload (text_note source_type)
- [x] Plain text 파일 upload (`--source-type plain_text_file` 지원)
- [x] content_type/MIME 자동 결정
- [x] raw/drive에 동일 내용 저장
- [x] sources DB upsert
- [x] 중복 시 timestamp append
- [x] apply 결과에 `rebuild_status=completed` 기록 (실제 `--rebuild` 연결은 v04-04에서 구현)

### Error 처리
- [x] v04-00 ingest contract 오류 계약 준수
- [x] `drive_auth_missing`: 전체 실패 (structured JSON 반환)
- [x] `drive_write_failed`: 부분 실패 (API 호출 실패 시)
- [x] `invalid_input`: source_type/title/body 검증

### Testing
- [x] fake Drive service로 create 요청 검증
- [x] dry-run: Drive API 호출 없음 검증
- [x] apply: raw/drive 저장 + DB upsert 검증
- [x] 중복 정책 timestamp append 검증
- [x] config file 누락/오류 검증
- [x] token 누락 시 actionable error 검증 (structured JSON)
- [x] PyYAML 없는 환경에서 folders config fallback 검증
- [x] 실제 Drive write smoke test는 기본 unittest에서 제외

## Verification

```bash
python -m unittest tests.test_publish_drive
python -m unittest discover -s tests -p "test_*.py"
python tools/publish_drive.py --dry-run --category personal_notes --title "Test note" --body "hello"
```

실제 Drive write smoke는 maintainer가 승인한 token/folder id로만 실행한다.

## Key Decisions

- Drive write는 `sync_drive.py`에 섞지 않고 별도 CLI로 시작하는 것을 우선한다.
- `sync_drive.py`는 Drive -> local sync 책임을 유지한다.
- `publish_drive.py`는 local/OpenClaw -> Drive publish 책임을 가진다.
- dry-run/apply 이분법은 spec0003 Google Drive sync의 패턴을 재사용한다.
- Binary attachment는 v0.4-00에서 unsupported 처리, 이 feature에서도 미지원.
