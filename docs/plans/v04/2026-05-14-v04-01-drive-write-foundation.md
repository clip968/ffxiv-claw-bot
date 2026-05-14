# v0.4-01: Drive Write Foundation

## Spec

- `docs/specs/0003-google-drive-sync.md`
- `docs/specs/01-architecture.md`
- `docs/adrs/0002-drive-is-canonical-source.md`
- Master plan: `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

## Status

**Proposed**

## Context

현재 Drive 연동은 read-only sync/export/download 중심이다.
OpenClaw가 받은 저장 요청을 Drive canonical source에 반영하려면 Drive file create/update/upload 기능과 write 가능한 OAuth scope가 필요하다.

## Checklist

- [ ] 최소 Drive write scope 결정 (`drive.file` 우선 검토, 기존 folder/file 업데이트 요구 시 broader scope 필요 여부 기록)
- [ ] credential/token migration 정책 결정: 기존 read-only token 재인증 필요 문서화
- [ ] `tools/publish_drive.py` CLI 신설 여부 확정
- [ ] Drive category folder id 입력 방식 결정: config file vs CLI flag
- [ ] dry-run 출력 JSON 설계: 생성될 Drive path, MIME, category, duplicate policy
- [ ] apply 동작 설계: Google Docs 생성, text/markdown upload, binary upload
- [ ] Google Docs 생성 방식 결정: markdown/plain text를 Drive file로 업로드할지 Google Docs로 convert할지
- [ ] 중복 정책 결정: same title append timestamp, overwrite, create new revision 중 하나 선택
- [ ] unittest: fake Drive service로 create request 검증
- [ ] unittest: unsupported category는 parser/value error 검증
- [ ] unittest: apply 없이 dry-run은 Drive write 호출 없음 검증
- [ ] runbook 업데이트: Drive write auth와 smoke test 절차

## Verification

```bash
python -m unittest tests.test_publish_drive
python -m unittest discover -s tests -p "test_*.py"
python tools/publish_drive.py --dry-run --category personal_notes --title "Test note" --body "hello"
```

실제 Drive write smoke는 기본 unittest에서 제외하고 maintainer가 승인한 token/folder id로만 실행한다.

## Key Decisions

- Drive write는 `sync_drive.py`에 섞지 않고 별도 CLI로 시작하는 것을 우선한다.
- `sync_drive.py`는 Drive -> local sync 책임을 유지한다.
- `publish_drive.py`는 local/OpenClaw -> Drive publish 책임을 가진다.

