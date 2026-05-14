# ffxiv-claw-bot Docs

`docs/`는 `ffxiv-claw-bot`의 구현 계약과 작업 흐름을 Git으로 관리하는 source of truth다.

Notion은 source of truth가 아니다. Notion에는 handoff 요약, 링크, decision index와 OpenClaw가 직접 갱신하는 작업 상태만 기록한다.

## Directory Roles

- `specs/`: 구현 계약. 기능이 지켜야 하는 입력, 출력, 저장, 에러, acceptance criteria를 정의한다.
- `adrs/`: 기술 결정 이유. 되돌리기 어렵거나 장기 영향을 주는 선택의 배경을 기록한다.
- `plans/`: 이번 작업의 작은 구현 계획. 실행 순서와 red test를 적지만 장기 owner로 쓰지 않는다.
- `runbooks/`: 반복 가능한 명령. 현재 레포에서 실제 실행 가능한 테스트, 동기화, 재빌드 절차를 기록한다.
- `handoff/`: 다음 agent/session의 첫 문서. 현재 상태, 남은 TODO, 검증 결과를 요약한다.
- `templates/`: spec, ADR, plan, handoff 작성 템플릿이다.
- `archive/`: 현재 기준 실행 대상이 아닌 문서. DOC_OWNERS owner로 쓰지 않는다.

## Principles

- 기능 구현은 spec 계약을 기준으로 한다.
- 큰 변경은 `spec -> ADR(if needed) -> plan -> failing tests -> implementation -> docs update -> handoff update -> finish_task` 순서로 진행한다.
- 행동이 바뀌는 코드 변경은 먼저 실패하는 테스트를 작성한다.
- `docs/handoff/CURRENT_HANDOFF.md`는 모든 코드 변경의 전역 상태 문서다.
- `docs/DOC_OWNERS.yml`은 코드 경로가 어떤 spec/runbook/ADR 계약 아래 있는지 추적하는 정책 파일이다.
- `docs/plans/`와 `docs/archive/`는 DOC_OWNERS owner로 인정하지 않는다.
- Notion 문서나 외부 링크는 DOC_OWNERS owner가 아니다.
- 원본 파일 저장소는 repo 외부 `/mnt/d/ffixiv-bot-storage`이며, Notion에는 파일 자체를 올리지 않는다.

## Start Here

새 session은 다음 순서로 읽는다.

1. `docs/WORKFLOW.md`
2. `docs/handoff/CURRENT_HANDOFF.md`
3. 변경 대상과 관련된 `docs/specs/`, `docs/runbooks/`, `docs/adrs/`

작업 종료 전에는 handoff를 갱신한 뒤 다음을 실행한다.

```bash
python scripts/finish_task.py
```
