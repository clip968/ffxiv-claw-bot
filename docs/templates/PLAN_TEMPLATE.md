# Plan: Title

## Status

Proposed | In Progress | Completed YYYY-MM-DD

## Related contract

- Spec: `docs/specs/...`
- ADR: `docs/adrs/...`
- Runbook: `docs/runbooks/...`
- Master plan: `docs/plans/...` (더 큰 단위의 tracking plan이 있을 경우)

## Goal

이번 plan에서 끝낼 작은 목표를 적는다. spec의 한 기능 단위에 대응해야 한다.

## Non-goals

- 이번 plan에서 하지 않는 것

## Execution Model

- Planner: 목표를 이 plan의 작은 task로 분해한 사람 또는 상위 모델
- Executor: 이 plan의 단일 task만 수행할 agent
- Reviewer/CI: diff, test output, docs freshness, finish gate로 완료 여부를 판단

Executor 규칙:

- plan 밖 구현 변경을 하지 않는다.
- 필요한 범위 확대가 보이면 먼저 plan과 관련 contract docs를 갱신한다.
- 완료 주장은 `python scripts/finish_task.py` 통과 후에만 한다.

## Allowed Files

- 수정 가능:
  - `path/to/file`
- 수정 금지:
  - `path/to/protected-file`

## Docs Required

코드 변경이 있으면 handoff 외에 관련 contract/procedure doc도 함께 갱신한다.

- Contract docs:
  - `docs/specs/...` 또는 `docs/adrs/...`
- Procedure docs:
  - `docs/runbooks/...`
- Global handoff:
  - `docs/handoff/CURRENT_HANDOFF.md`

`docs/plans/`와 handoff만 변경해서 docs freshness를 만족했다고 판단하지 않는다.

## Red Test

- 먼저 추가할 실패 테스트:
  - `tests/...`
- 테스트를 먼저 쓸 수 없는 경우 이유와 대체 검증:
  - 이유:
  - 대체 검증:

## Tasks

각 task는 완료 시 `[x]`로 변경한다.

- [ ] Task 1: 한 번에 검증 가능한 작은 변경
- [ ] Task 2: 필요 시 다음 작은 변경
- [ ] Task 3: docs/handoff/final verification 반영

## Verification

```bash
python -m unittest tests.<focused_test_module>
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

## Handoff Updates

- `docs/handoff/CURRENT_HANDOFF.md`에 반영할 내용

---

## Plan 작성 규칙

1. **Spec을 기능 단위로 쪼갠다.** 하나의 plan = spec의 한 기능(또는 한 구현 단계)에 대응한다.
2. **plan 파일명은 master plan에서 참조하기 쉽게 번호를 붙인다.** 예: `docs/plans/v03/2026-05-14-v03-03-drive-api-auth.md`
3. **Tasks는 체크리스트(`[ ]`/`[x]`)로 작성한다.** plan만 봐도 무엇이 완료되고 안 됐는지 한눈에 알 수 있어야 한다.
4. **feature plan은 `docs/plans/<phase>/` 아래에 둔다.** 예: `docs/plans/v03/`, `docs/plans/v04/`
5. **하나의 spec에서 여러 plan이 나오면 master plan을 만든다.** master plan은 `docs/plans/YYYY-MM-DD-<phase>-master.md`에 두고, 각 feature plan의 완료 상태를 체크리스트로 추적한다.
6. **plan의 Status는 Proposed / In Progress / Completed 중 하나다.** Completed에는 완료 날짜를 함께 적는다.
7. **오픈소스 모델에게 넘길 plan은 Allowed Files, Docs Required, Red Test, Verification을 반드시 채운다.**
8. **완료 판정은 agent 보고가 아니라 테스트 로그, docs freshness, finish gate, diff review로 한다.**
