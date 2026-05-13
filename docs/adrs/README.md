# ADRs

ADR은 Architecture Decision Record다. 기술적 결정을 왜 했는지 기록하는 문서다.

ADR은 spec이나 plan을 대체하지 않는다. spec은 현재 시스템 동작 계약이고, ADR은 그 계약 뒤에 있는 결정 이유를 보존한다.

## 형식

```markdown
# ADR NNNN: Title

## Status

Accepted | Proposed | Superseded

## Context

상황과 문제

## Decision

결정한 내용

## Consequences

좋은 영향, 나쁜 영향, 트레이드오프
```

## 규칙

- 한 ADR에는 하나의 기술적 결정을 기록한다.
- 결정이 바뀌면 기존 ADR을 삭제하지 말고 `Superseded`로 표시하고 새 ADR을 작성한다.
- 구현 세부 단계는 `docs/plans/`에 둔다.
