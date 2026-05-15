# v0.4-04: Publish Then Rebuild

## Superseded Notice

This Drive publish-era plan is superseded for the default v0.4 path.

Use `docs/plans/v04/2026-05-14-v04-04-local-publish-then-rebuild.md` for Local Storage publish/snapshot/rebuild. Drive publish and `sync_drive.py --from-drive` references in this file are historical optional integration context only.

## Spec

- `docs/specs/0003-google-drive-sync.md`
- `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md`
- Master plan: `docs/plans/v04/legacy/2026-05-14-v04-openclaw-drive-ingest.md`

## Status

**Proposed**

## Context

Drive에 저장만 하고 로컬 KB를 재빌드하지 않으면 사용자는 방금 저장한 내용을 바로 검색할 수 없다.
이 plan은 Drive publish 성공 후 sync/download/apply와 wiki/FTS/graph rebuild를 연결한다.

## Checklist

- [ ] v0.3-05 rebuild chain 완료 여부 확인
- [ ] publish result의 `drive_file_id`를 sync/rebuild 대상으로 넘기는 방식 결정
- [ ] `ingest_discord_note.py --apply --publish-drive --rebuild` 플래그 설계
- [ ] Drive publish 성공 후 `sync_drive.py --from-drive --download --apply` 호출 범위 결정
- [ ] 변경된 source만 compile 대상으로 수집하는 방식 재사용
- [ ] rebuild 실패 시 output JSON 정책 결정: Drive saved, local rebuild failed
- [ ] unittest: publish success -> sync/rebuild 호출 순서 검증
- [ ] unittest: publish success + rebuild failure는 partial failure JSON 반환 검증
- [ ] unittest: publish failure면 rebuild 호출 없음 검증
- [ ] end-to-end fixture: 저장한 note가 `search_kb.py`에서 검색되는지 검증
- [ ] handoff/runbook 업데이트

## Verification

```bash
python -m unittest tests.test_ingest_discord_note
python -m unittest discover -s tests -p "test_*.py"
python tools/ingest_discord_note.py --dry-run --publish-drive --rebuild --category personal_notes --title "Rebuild smoke" --body "hello"
```

실제 Drive publish + rebuild smoke는 maintainer가 승인한 folder id/token으로만 실행한다.

## Key Decisions

- Drive publish 성공은 원본 저장 성공으로 본다.
- rebuild 실패는 저장 실패가 아니라 partial failure로 반환한다.
- 사용자는 partial failure일 때 나중에 수동 rebuild를 재시도할 수 있어야 한다.
