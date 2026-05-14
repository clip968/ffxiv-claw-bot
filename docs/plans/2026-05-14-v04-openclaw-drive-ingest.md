# v0.4 Master Plan: OpenClaw Drive Ingest

Spec:
- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- `docs/adrs/0002-drive-is-canonical-source.md`

## Status

v0.4는 OpenClaw/Discord에서 들어온 저장 요청을 Google Drive canonical source에 반영하고, 로컬 KB를 재빌드한 뒤 사용자에게 결과를 돌려주는 단계다.

## Prerequisite

- v0.3-05 `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md` 완료

## Feature Plans

| # | Plan | Status |
|---|---|---|
| 00 | `docs/plans/v04/2026-05-14-v04-00-openclaw-ingest-contract.md` | [x] Completed 2026-05-14 |
| 01 | `docs/plans/v04/2026-05-14-v04-01-drive-write-foundation.md` | [ ] 미구현 |
| 02 | `docs/plans/v04/2026-05-14-v04-02-ingest-discord-note-cli.md` | [ ] 미구현 |
| 03 | `docs/plans/v04/2026-05-14-v04-03-openclaw-tool-adapter.md` | [ ] 미구현 |
| 04 | `docs/plans/v04/2026-05-14-v04-04-publish-then-rebuild.md` | [ ] 미구현 |
| 05 | `docs/plans/v04/2026-05-14-v04-05-discord-summary-notification.md` | [ ] 미구현 |

## v0.4 Goal

OpenClaw/Discord에서 다음 흐름을 지원한다.

```text
Discord/OpenClaw 저장 요청
-> ingest request 정규화
-> Google Drive FFXIV_KB 업로드/생성
-> Drive sync/download/apply
-> wiki/FTS/graph rebuild
-> Discord/OpenClaw 결과 메시지
```

## v0.4 Non-goals

- embedding/vector DB 도입
- 자동 패치노트 크롤링
- 다중 사용자 권한 모델
- Google Sheets CSV 변환
- Discord bot hosting/deployment 자동화

## How to Update

feature plan 하나가 완료되면:

1. 개별 plan 파일의 `## Status`를 **Completed YYYY-MM-DD**로 변경
2. 이 master plan에서 해당 feature의 `[ ]`를 `[x]`로 변경
3. `docs/handoff/CURRENT_HANDOFF.md`에 완료 상태 반영

