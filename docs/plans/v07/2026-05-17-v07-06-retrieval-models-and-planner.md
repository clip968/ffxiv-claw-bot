# v0.7-06: Retrieval Models and Planner

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-06)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Completed 2026-05-17

## Goal

`ParsedQuery`로부터 retrieval plan을 생성하는 모델(`RetrievalTarget`, `RetrievalPlan`)과 planner(`build_retrieval_plan`)를 구현한다.

## Scope

- `src/retrieval/` 패키지 추가
- `RetrievalTarget` frozen dataclass (wiki_type, topic, query, priority)
- `RetrievalPlan` frozen dataclass (primary, fallback, limit)
- `build_retrieval_plan(parsed: ParsedQuery, *, limit: int = 5) -> RetrievalPlan` 함수
- job_change_history intent → job wiki primary + source_summary fallback + generic fallback
- generic_search intent → unfiltered primary

Out of scope:

- 실제 DB search (v07-07)
- retrieval plan 실행 (v07-08)
- context pack building (v07-09)

## Red Test

- File: `tests/test_v07_retrieval.py`
- Implementation target: `src/retrieval/models.py`, `src/retrieval/planner.py`, `src/retrieval/__init__.py`
- Expected red reason: `src.retrieval` 패키지 미존재.

Contracts fixed by the tests:

- job_change_history plan의 `primary[0].wiki_type == "job"` 및 `primary[0].topic == "gunbreaker"`
- generic_search plan은 topic filter 없음
- fallback에 source_summary target 포함

## Checklist

- [x] `src/retrieval/__init__.py` 생성
- [x] `src/retrieval/models.py` 생성
  - [x] `RetrievalTarget` frozen dataclass
  - [x] `RetrievalPlan` frozen dataclass
- [x] `src/retrieval/planner.py` 생성
  - [x] `build_retrieval_plan()` 구현
  - [x] `_job_query()` helper (job slug → alias-expanded query)
- [x] `tests/test_v07_retrieval.py` 생성
  - [x] `test_job_change_history_plan_prefers_job_wiki`
  - [x] `test_generic_search_plan_has_no_topic_filter`
  - [x] `test_job_change_history_plan_has_source_summary_fallback`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_retrieval -v
python -m py_compile src/retrieval/models.py src/retrieval/planner.py
```

## Key Decisions

- `_job_query()`는 `src.derived_wiki.job_catalog.resolve_job()`을 사용하여 모든 alias를 검색어로 확장한다.
- job_change_history의 fallback 순서: source_summary(topic 무관) → 전체 검색(무필터).
- planner는 deterministic이다. 동일 입력에 항상 동일 plan을 반환한다.

## Implementation Notes

- v07-05의 `ParsedQuery`에 의존한다.
- `src.derived_wiki.job_catalog`을 재사용한다 (v06에서 구현됨).
- 이 task에서는 DB를 열지 않는다. planner는 순수 함수이다.

## Agent Prompt

```text
Implement v07-06 only.

Add retrieval models and planner.

Files:
- src/retrieval/__init__.py
- src/retrieval/models.py
- src/retrieval/planner.py
- tests/test_v07_retrieval.py

Rules:
- Job change history queries must prefer wiki_type=job and topic=<job>.
- Source summary fallback must be included.
- Generic search must remain unfiltered.
- Do not implement database search yet.
- Run:
  python -m unittest tests.test_v07_retrieval -v
  python -m py_compile src/retrieval/models.py src/retrieval/planner.py
```
