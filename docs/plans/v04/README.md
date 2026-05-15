# v0.4 Feature Plans

v0.4 OpenClaw Local Ingest and Notion Control의 feature별 plan을 보관한다.

기본 운영 경로는 `/mnt/d/ffixiv-bot-storage`와 OpenClaw Notion direct control이다. Google Drive 기반 v0.3 sync와 v0.4-01 Drive write foundation은 completed legacy optional integration으로 보존한다.

## Master Plan

`docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`에서 전체 진행 상태를 추적한다.

`docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`는 historical legacy reference다.

## Active Feature Map

| # | Plan |
|---|---|
| 00 | `2026-05-14-v04-00-openclaw-ingest-contract.md` |
| 01 | `2026-05-14-v04-01-local-storage-foundation.md` |
| 02 | `2026-05-14-v04-02-openclaw-notion-control-contract.md` |
| 03 | `2026-05-14-v04-03-ingest-local-note-cli.md` |
| 04 | `2026-05-14-v04-04-local-publish-then-rebuild.md` |
| 05 | `2026-05-14-v04-05-status-notification.md` |
| legacy | `2026-05-14-v04-legacy-drive-integration.md` |

## Legacy Folder

`docs/plans/v04/legacy/`에는 현재 active feature map에서 제외된 과거 plan을 보관한다.

루트의 `v04-01`~`v04-05` 파일은 active plan만 둔다. 같은 번호의 과거 plan은 `legacy/` 아래 파일을 참고한다.

## 작성 규칙

- 각 plan은 spec의 한 기능 단위에 대응한다.
- Tasks는 체크리스트(`[ ]`/`[x]`)로 작성한다.
- 완료 시 `## Status`를 **Completed YYYY-MM-DD**로 변경하고 master plan의 체크리스트도 함께 갱신한다.
- v0.4 구현은 v0.3-05 rebuild chain 완료 후 시작한다.
