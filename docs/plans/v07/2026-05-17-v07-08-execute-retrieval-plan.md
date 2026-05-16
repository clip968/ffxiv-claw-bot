# v0.7-08: Execute Retrieval Plan

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-08)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

retrieval plan의 primary target들을 먼저 실행하고, primary가 빈 결과일 때만 fallback을 실행하는 `execute_retrieval_plan()` 함수를 구현한다.

## Scope

- `src/retrieval/context_builder.py` 또는 `src/retrieval/planner.py`에 함수 추가
- primary targets를 priority 순서로 검색
- primary에 결과가 있으면 fallback 실행하지 않음
- primary가 전부 빈 결과일 때만 fallback 실행
- page_id 기준 중복 제거
- plan.limit 준수

Out of scope:

- context document 생성 (v07-09)
- answer composition (v07-11)

## Red Test

- File: `tests/test_v07_retrieval.py`
- Implementation target: `src/retrieval/context_builder.py` 또는 `src/retrieval/planner.py`
- Expected red reason: `execute_retrieval_plan` 함수 미존재.

Contracts fixed by the tests:

- primary에 결과가 있으면 그것만 반환 (fallback 미실행)
- primary가 빈 결과면 fallback 실행
- 동일 page_id 중복 제거
- 결과 수가 plan.limit 이하

## Checklist

- [ ] `execute_retrieval_plan()` 함수 구현
  - [ ] primary targets priority 순 실행
  - [ ] primary 결과 확인
  - [ ] 조건부 fallback 실행
  - [ ] page_id 기준 deduplication
  - [ ] limit 적용
- [ ] `tests/test_v07_retrieval.py` 갱신
  - [ ] `test_execute_retrieval_plan_uses_primary_first`
  - [ ] `test_execute_retrieval_plan_uses_fallback_when_primary_empty`
  - [ ] `test_execute_retrieval_plan_deduplicates_page_ids`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_retrieval -v
```

## Key Decisions

- primary targets는 priority 숫자 오름차순으로 실행한다.
- 하나의 primary target이라도 결과를 반환하면 전체 primary를 성공으로 간주하고 fallback은 건너뛴다.
- deduplication은 page_id 기준이며, 먼저 나온 것을 유지한다.

## Implementation Notes

- v07-06의 `RetrievalPlan`과 v07-07의 `search_wiki()` + `SearchResult`에 의존한다.
- test에서는 mock 또는 temporary DB를 사용한다.
- 이 함수는 `tools/ask.py`에서 핵심 실행 경로로 사용된다.

## Agent Prompt

```text
Implement v07-08 only.

Add retrieval plan execution.

Files:
- src/retrieval/context_builder.py or src/retrieval/planner.py
- tests/test_v07_retrieval.py

Rules:
- Execute primary targets first.
- Run fallback only if primary produces no results.
- Deduplicate by page_id.
- Respect plan.limit.
- Do not build answer text yet.
- Run:
  python -m unittest tests.test_v07_retrieval -v
```
