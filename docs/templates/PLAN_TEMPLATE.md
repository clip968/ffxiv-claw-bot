# Plan: Title

## Status

Proposed | In Progress | Completed YYYY-MM-DD

## Related contract

- Spec: `docs/specs/...`
- ADR: `docs/adrs/...`
- Master plan: `docs/plans/...` (더 큰 단위의 tracking plan이 있을 경우)

## Goal

이번 plan에서 끝낼 작은 목표를 적는다. spec의 한 기능 단위에 대응해야 한다.

## Non-goals

- 이번 plan에서 하지 않는 것

## Tasks

각 task는 완료 시 `[x]`로 변경한다.

- [ ] task 1
- [ ] task 2
- [ ] task 3

## Verification

```bash
python -m unittest discover -s tests -p "test_*.py"
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
