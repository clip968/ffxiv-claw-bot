# v0.3 Master Plan: Google Drive Sync

Spec: `docs/specs/0003-google-drive-sync.md`

## Status

v0.3은 5개 feature plan으로 구성된다. 각 plan은 spec의 한 기능 단위에 대응한다.

## Feature Plans

| # | Plan | Status |
|---|---|---|
| 01 | `docs/plans/v03/2026-05-14-v03-01-manifest-dry-run.md` | [x] 완료 |
| 02 | `docs/plans/v03/2026-05-14-v03-02-fixture-apply.md` | [x] 완료 |
| 03 | `docs/plans/v03/2026-05-14-v03-03-drive-api-auth.md` | [x] 완료 |
| 04 | `docs/plans/v03/2026-05-14-v03-04-drive-export-download.md` | [ ] 미구현 (다음 1순위) |
| 05 | `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` | [ ] 미구현 |

## v0.3 Not In Scope

- Discord/OpenClaw 연결
- 패치노트 자동 수집
- 검색 품질 평가
- embedding/vector DB

위 항목은 `docs/plans/2026-05-14-post-v03-next-steps.md` (v0.4+ 후보) 참조.

## How to Update

feature plan 하나가 완료되면:
1. 개별 plan 파일의 `## Status`를 **Completed**로 변경
2. 이 master plan에서 해당 feature의 `[ ]`를 `[x]`로 변경
3. `docs/handoff/CURRENT_HANDOFF.md`에 완료 상태 반영
