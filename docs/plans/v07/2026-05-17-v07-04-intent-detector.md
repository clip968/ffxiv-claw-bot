# v0.7-04: Intent Detector

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-04)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Completed 2026-05-17

## Goal

사용자 질문을 단순 결정론적 규칙으로 intent로 분류하는 `detect_intent()` 함수를 구현한다. LLM 호출 없이 keyword 매칭만 사용한다.

## Scope

- `src/query/intent_detector.py` 추가
- intent: `job_change_history` (직업 + 변경 관련 키워드)
- intent: `generic_search` (기본값)
- keyword list 정의 (변경 이력, 변경점, 뭐 바뀜, 바뀐, change history, changes 등)

Out of scope:

- LLM 기반 intent 분류
- 추가 intent 확장 (raid_guide, item_search 등은 향후 버전)
- topic 결정 (v07-05 parser에서 담당)

## Red Test

- File: `tests/test_v07_query_parser.py`
- Implementation target: `src/query/intent_detector.py`
- Expected red reason: `src.query.intent_detector` module 미존재.

Contracts fixed by the tests:

- `detect_intent("건브레이커 변경 이력", job="gunbreaker")` → `"job_change_history"`
- `detect_intent("흑마 뭐 바뀜?", job="black_mage")` → `"job_change_history"`
- `detect_intent("M4S 공략 찾아줘", job=None)` → `"generic_search"`

## Checklist

- [x] `src/query/intent_detector.py` 생성
  - [x] `JOB_CHANGE_KEYWORDS` 상수 정의
  - [x] `detect_intent(query: str, *, job: str | None = None) -> str` 구현
- [x] `src/query/__init__.py` 갱신 (re-export)
- [x] `tests/test_v07_query_parser.py` 갱신
  - [x] `test_detect_job_change_history_intent_with_change_history`
  - [x] `test_detect_job_change_history_intent_with_what_changed`
  - [x] `test_detect_generic_search_without_job`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_query_parser -v
python -m py_compile src/query/intent_detector.py
```

## Key Decisions

- job이 있고 변경 관련 키워드가 있으면 `job_change_history`, 그 외 모든 경우는 `generic_search`.
- LLM을 호출하지 않는다. 순수 규칙 기반이다.
- 향후 intent 추가 시 이 함수에 elif를 추가하면 된다.

## Implementation Notes

- v07-01의 `src/query/` 패키지에 의존한다.
- v07-02 job detector와 독립적으로 테스트 가능하다 (job 파라미터를 직접 전달).
- `tools/search_kb.py`나 `tools/answer.py`를 수정하지 않는다.
- Red verification: `python -m unittest tests.test_v07_query_parser.V07IntentDetectorTests -v` failed because `detect_intent` was not importable from `src.query`.
- Green verification: `python -m unittest tests.test_v07_query_parser -v` passed 17 tests.
- Compile verification: `python -m py_compile src/query/intent_detector.py src/query/__init__.py` passed.

## Agent Prompt

```text
Implement v07-04 only.

Add deterministic intent detection for the v07 ask pipeline.

Files:
- src/query/intent_detector.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- Required intents: job_change_history and generic_search.
- Use simple rule-based detection.
- Do not call any LLM.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/intent_detector.py
```
