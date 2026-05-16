# v0.7-05: Query Parser Integration

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-05)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

normalization, job detection, patch range parsing, intent detection을 하나의 `parse_query()` 함수로 통합하여 완전한 `ParsedQuery`를 반환한다.

## Scope

- `src/query/parser.py` 추가
- `parse_query(query: str) -> ParsedQuery` 함수 구현
- 내부적으로 `normalize_query`, `extract_terms`, `detect_job`, `parse_patch_range`, `detect_intent` 호출
- topic 결정 로직 (job이 있으면 `"job"`, 없으면 `None`)

Out of scope:

- retrieval planning (v07-06)
- FTS search (v07-07)
- context building (v07-09)

## Red Test

- File: `tests/test_v07_query_parser.py`
- Implementation target: `src/query/parser.py`
- Expected red reason: `src.query.parser` module 미존재.

Contracts fixed by the tests:

- `parse_query("7.x 건브레이커 변경 이력 알려줘")` → intent=job_change_history, job=gunbreaker, patch_range=7.0..7.99, topic=job
- `parse_query("M4S 공략 찾아줘")` → intent=generic_search, job=None

## Checklist

- [ ] `src/query/parser.py` 생성
  - [ ] `parse_query(query: str) -> ParsedQuery` 구현
  - [ ] 내부 호출: normalize_query, extract_terms, detect_job, parse_patch_range, detect_intent
  - [ ] topic 결정 로직
- [ ] `src/query/__init__.py` 갱신 (re-export `parse_query`)
- [ ] `tests/test_v07_query_parser.py` 갱신
  - [ ] `test_parse_query_job_change_history`
  - [ ] `test_parse_query_generic_search`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_query_parser -v
python -m py_compile src/query/parser.py
```

## Key Decisions

- `parse_query()`는 단순 조합 함수다. 각 하위 컴포넌트는 별도로 테스트 가능해야 한다.
- topic은 현재 `"job"` 또는 `None`만 지원한다. 향후 `"raid"`, `"item"` 등 추가 가능.

## Implementation Notes

- v07-01~04 모두에 의존한다. Batch A의 마지막 task이다.
- 이 함수가 완성되면 Batch B의 retrieval planner가 `ParsedQuery`를 입력으로 받을 수 있다.
- `tools/search_kb.py`나 `tools/answer.py`를 수정하지 않는다.

## Agent Prompt

```text
Implement v07-05 only.

Integrate the query parser.

Files:
- src/query/parser.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- parse_query() must return ParsedQuery.
- Reuse normalize_query, extract_terms, detect_job, parse_patch_range, detect_intent.
- Do not implement retrieval yet.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/parser.py
```
