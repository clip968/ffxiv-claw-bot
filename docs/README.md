# ffxiv-claw-bot Docs

이 디렉터리는 `ffxiv-claw-bot`의 구현 기준과 작업 흐름을 Git으로 관리하기 위한 문서 공간이다.

구현 기준은 Notion이 아니라 레포 내부 Markdown 문서다. Notion은 프로젝트 인덱스, handoff 요약, decision summary 용도로만 사용한다.

## 구조

- `specs/`: 구현 계약. 현재 시스템이 어떻게 동작해야 하는지 정의한다.
- `adrs/`: 기술적 결정 이유. 왜 그런 선택을 했는지 기록한다.
- `plans/`: 다음 작업 계획. 구현 전 작은 단위로 작업을 분해한다.
- `runbooks/`: 반복 실행 절차. 테스트, 동기화, 재빌드 명령을 기록한다.
- `handoff/`: 다음 agent/session이 가장 먼저 읽는 현재 상태 문서다.
- `templates/`: spec, ADR, plan, handoff 작성 템플릿이다.
- `archive/`: 오래되었거나 현재 기준 실행 대상이 아닌 문서를 보관한다.

## 원칙

- spec과 코드 변경은 가능하면 같은 Git 작업 단위로 관리한다.
- ADR은 이미 결정한 이유를 보존한다.
- plan은 구현 전 작업 분해 문서이며 spec이나 ADR을 대체하지 않는다.
- runbook에는 현재 레포에서 실제 가능한 명령만 적는다.
- handoff에는 긴 설명을 넣지 말고 관련 spec, ADR, plan, runbook으로 연결한다.
