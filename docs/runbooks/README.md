# Runbooks

runbook은 반복 가능한 명령과 절차를 기록하는 문서다.

## 규칙

- 현재 레포에서 실제 가능한 명령만 기록한다.
- 추측한 명령은 적지 않는다.
- 확실하지 않은 절차는 `TODO`로 표시한다.
- 명령의 목적과 예상 결과를 함께 적는다.

## 현재 runbook

- `test.md`: 테스트 실행
- `local-storage.md`: Local Storage ingest/sync 절차
- `openclaw-notion.md`: OpenClaw Notion direct control 절차
- `sync-drive.md`: manifest 기반 Drive sync dry-run
- `publish-drive.md`: Drive write/publish 절차 (Legacy / Deferred optional integration)
- `rebuild-kb.md`: 로컬 KB 재빌드 절차
- `finish-task.md`: 작업 종료 검증 자동화
- `notion-sync.md`: Notion handoff mirror dry-run/apply 절차
- `domain-graph-refresh.md`: v08.5 domain graph/wiki/FTS/ask refresh 절차
- `ask.md`: v07/v08/v08.5 graph-aware ask 절차
- `process-source.md`: v0.5/v05.1/v0.6 source processing entrypoint 절차
- `process-pending-sources.md`: v0.6 pending source queue 처리 절차
- `generate-derived-wiki.md`: v0.6 job wiki와 v08 graph-derived wiki 생성 절차
