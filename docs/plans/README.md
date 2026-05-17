# Plans

plan은 구현 전 작업 분해 문서다.

plan은 spec이나 ADR을 대체하지 않는다. spec은 현재 시스템 동작 계약이고, ADR은 기술적 결정 이유다. plan은 그 기준을 실제 작업 단위로 쪼개는 문서다.

## 규칙

- plan은 작고 검증 가능한 작업 단위로 작성한다.
- 각 작업에는 변경 대상 파일과 검증 명령을 포함한다.
- 오픈소스 모델이나 낮은 신뢰도의 agent에게 넘길 plan은 단일 task 범위로 제한한다.
- plan에는 Allowed Files, Docs Required, Red Test, Verification을 명시한다.
- 코드 변경 task는 handoff 외에도 관련 spec/runbook/ADR 중 하나 이상을 갱신해야 한다.
- 완료된 plan은 필요하면 `docs/archive/`로 옮길 수 있다.
- plan에 없는 큰 구현 변경이 필요해지면 먼저 plan을 갱신한다.
- documentation-only change는 구현 계획 대신 문서 변경 범위와 검증 기준을 명확히 적는다.

## Planner / Executor 방식

권장 흐름:

```text
상위 모델 또는 maintainer가 spec/ADR/runbook을 읽고 task plan 작성
-> executor agent가 plan의 단일 task 수행
-> focused test, full unittest, docs freshness, finish_task.py 실행
-> reviewer/CI가 diff와 command output으로 완료 판정
```

plan은 source of truth가 아니다. 실행 중 contract가 바뀌면 spec/runbook/ADR을 갱신해야 한다.

## Phase Plan Folders

- `docs/plans/v03/`: Google Drive sync feature plans (Legacy / Deferred optional integration)
- `docs/plans/v04/`: OpenClaw Local Ingest and Notion Control feature plans
- `docs/plans/v09/`: guide.ff14.co.kr official DB crawler and item pilot feature plans
