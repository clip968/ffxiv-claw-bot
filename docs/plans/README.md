# Plans

plan은 구현 전 작업 분해 문서다.

plan은 spec이나 ADR을 대체하지 않는다. spec은 현재 시스템 동작 계약이고, ADR은 기술적 결정 이유다. plan은 그 기준을 실제 작업 단위로 쪼개는 문서다.

## 규칙

- plan은 작고 검증 가능한 작업 단위로 작성한다.
- 각 작업에는 변경 대상 파일과 검증 명령을 포함한다.
- 완료된 plan은 필요하면 `docs/archive/`로 옮길 수 있다.
- plan에 없는 큰 구현 변경이 필요해지면 먼저 plan을 갱신한다.
- documentation-only change는 구현 계획 대신 문서 변경 범위와 검증 기준을 명확히 적는다.

## Phase Plan Folders

- `docs/plans/v03/`: Google Drive sync feature plans
- `docs/plans/v04/`: OpenClaw Drive ingest feature plans
