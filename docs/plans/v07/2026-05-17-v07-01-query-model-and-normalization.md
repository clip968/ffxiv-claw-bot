# v0.7-01: Query Model and Normalization

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-01)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

모든 query parser 컴포넌트가 공통으로 사용할 `ParsedQuery` 모델과 기본 normalization helpers(`normalize_query`, `extract_terms`)를 추가한다.

이 task는 v0.7 ask pipeline의 토대를 만드는 단계이며, 실제 job detection, patch parsing, intent detection은 후속 task에서 다룬다.

## Scope

- `src/query/` 패키지 추가
- `ParsedQuery` frozen dataclass 정의 (raw_query, normalized_query, intent, job, patch_range, topic, terms)
- `normalize_query()` 함수: casefold + whitespace 정규화
- `extract_terms()` 함수: 영문/숫자/한국어 토큰 추출

Out of scope:

- job detection (v07-02 책임)
- patch range parsing (v07-03 책임)
- intent detection (v07-04 책임)
- query parser 통합 (v07-05 책임)
- retrieval (v07-06 이후 책임)

## Red Test

- File: `tests/test_v07_query_parser.py`
- Implementation target: `src/query/models.py`, `src/query/normalize.py`, `src/query/__init__.py`
- Expected red reason: `src.query` 패키지가 아직 존재하지 않아 `ModuleNotFoundError` 발생.

Contracts fixed by the tests:

- `ParsedQuery`는 `raw_query`, `normalized_query`, `intent`, `job`, `patch_range`, `topic`, `terms` 필드를 가진다.
- `normalize_query()`는 casefold + whitespace 정규화를 수행한다.
- 한국어 텍스트는 보존된다.
- `extract_terms()`는 영문/숫자/한국어 토큰을 튜플로 반환한다.
- 빈 입력 또는 whitespace만 있는 입력이 crash하지 않는다.

## Checklist

- [ ] `src/query/__init__.py` 생성
- [ ] `src/query/models.py` 생성 (`ParsedQuery` frozen dataclass)
- [ ] `src/query/normalize.py` 생성
  - [ ] `normalize_query()` 구현
  - [ ] `extract_terms()` 구현
- [ ] `tests/test_v07_query_parser.py` 생성
  - [ ] `test_parsed_query_preserves_raw_and_normalized_query`
  - [ ] `test_normalize_query_casefolds_english_but_preserves_korean`
  - [ ] `test_tokenize_query_extracts_terms`
- [ ] red 상태 확인 (`python -m unittest tests.test_v07_query_parser -v`)
- [ ] 최소 구현으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_v07_query_parser -v
python -m py_compile src/query/models.py src/query/normalize.py src/query/__init__.py
```

## Key Decisions

- `ParsedQuery`는 `@dataclass(frozen=True)`로 정의한다. 외부 의존성 추가 금지.
- `normalize_query()`는 casefold를 사용한다. 한국어는 casefold에 영향받지 않으므로 자연스럽게 보존된다.
- `extract_terms()`는 regex `[a-z0-9_.]+|[가-힣]+`로 토큰을 추출한다.

## Implementation Notes

- import path는 `from src.query import ParsedQuery` 형태가 되도록 `__init__.py`에 re-export 한다.
- 이 task는 행동 변경이 없으므로 기존 `tools/search_kb.py`, `tools/answer.py`에 영향을 주지 않는다.
- 후속 v07-02~05에서 이 모델과 함수를 그대로 사용한다.

## Agent Prompt

```text
Implement v07-01 only.

Add the query package foundation for v07 Grounded Ask Pipeline.

Files:
- src/query/__init__.py
- src/query/models.py
- src/query/normalize.py
- tests/test_v07_query_parser.py

Rules:
- Write red tests first.
- Add ParsedQuery as a frozen dataclass.
- Add normalize_query() and extract_terms().
- Do not implement job detection yet.
- Do not modify search_kb.py or answer.py.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/models.py src/query/normalize.py src/query/__init__.py
```
