# Docs 기반 작업 워크플로우

이 프로젝트의 작업 기준은 레포 내부 `docs/` 문서다. Notion은 source of truth가 아니며, 요약과 링크를 남기는 인덱스 역할만 한다.

## 기본 흐름

1. 문제 또는 기능 요구를 확인한다.
2. 관련 spec을 `docs/specs/`에서 확인한다.
3. spec이 없으면 `docs/specs/`에 작성한다.
4. 기술적 결정이 필요하면 `docs/adrs/`에 ADR을 작성한다.
5. 구현 전 `docs/plans/`에 작은 구현 계획을 작성한다.
6. 구현한다.
7. `unittest`를 실행한다.
8. 결과를 `docs/handoff/CURRENT_HANDOFF.md`에 반영한다.
9. Notion에는 요약과 링크만 반영한다.

## 문서 역할

- spec은 구현이 따라야 하는 계약이다.
- ADR은 이미 결정한 이유를 보존하는 문서다.
- plan은 구현 전 작업 계획이다.
- runbook은 반복 가능한 명령 모음이다.
- handoff는 다음 agent가 읽는 첫 문서다.
- archive는 현재 기준 실행 대상이 아닌 문서를 보관한다.

## 작업 규칙

- Notion은 source of truth가 아니다.
- 코드 변경과 spec 변경이 함께 필요하면 같은 작업 단위에서 관리한다.
- 큰 변경은 `spec -> ADR -> plan -> implementation -> tests -> handoff` 순서로 진행한다.
- 구현 코드와 무관한 문서 정리는 `documentation-only change`로 취급한다.
- runbook에는 추측한 명령을 쓰지 않는다. 확실하지 않으면 `TODO`로 남긴다.
- 오래된 handoff나 폐기된 계획은 삭제하지 말고 `docs/archive/`로 옮긴다.

## 작업 시작 체크

1. `git status --short`
2. `git branch --show-current`
3. `git log --oneline -5`
4. `git diff --stat`
5. `docs/handoff/CURRENT_HANDOFF.md` 확인

uncommitted 변경이 있으면 되돌리지 않는다. 현재 작업과 무관한 변경은 건드리지 않는다.
