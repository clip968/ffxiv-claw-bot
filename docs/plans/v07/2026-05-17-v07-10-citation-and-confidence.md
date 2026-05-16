# v0.7-10: Citation and Confidence Helpers

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-10)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

source path 수집과 confidence label 결정을 위한 작은 helper 함수를 구현한다. answer composer의 building block이다.

## Scope

- `src/answering/` 패키지 추가
- `src/answering/citations.py`: `collect_sources()` 함수
- `src/answering/confidence.py`: `confidence_for_context_count()` 함수
- source 중복 제거 (순서 보존)

Out of scope:

- answer text composition (v07-11)
- LLM 호출
- CLI (v07-12)

## Red Test

- File: `tests/test_v07_answer_composer.py`
- Implementation target: `src/answering/citations.py`, `src/answering/confidence.py`, `src/answering/__init__.py`
- Expected red reason: `src.answering` 패키지 미존재.

Contracts fixed by the tests:

- `collect_sources()` 결과에 context path가 포함된다.
- `collect_sources()` 결과에 source_ids가 포함된다.
- 중복 source는 제거된다.
- `confidence_for_context_count(0)` → `"N/A"`
- `confidence_for_context_count(1)` → `"source_grounded"`

## Checklist

- [ ] `src/answering/__init__.py` 생성
- [ ] `src/answering/citations.py` 생성
  - [ ] `collect_sources(contexts: tuple[ContextDocument, ...]) -> tuple[str, ...]`
  - [ ] 중복 제거 (순서 보존)
  - [ ] path + source_ids 포함
- [ ] `src/answering/confidence.py` 생성
  - [ ] `confidence_for_context_count(count: int) -> str`
- [ ] `tests/test_v07_answer_composer.py` 생성
  - [ ] `test_collect_sources_includes_paths`
  - [ ] `test_collect_sources_includes_source_ids`
  - [ ] `test_confidence_no_context_returns_na`
  - [ ] `test_confidence_with_context_returns_source_grounded`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_answer_composer -v
python -m py_compile src/answering/citations.py src/answering/confidence.py
```

## Key Decisions

- `collect_sources()`는 context의 path와 source_ids를 모두 수집하여 하나의 tuple로 반환한다.
- 중복 제거는 `dict.fromkeys()` 패턴으로 순서를 보존한다.
- confidence는 현재 binary: 0개면 N/A, 1개 이상이면 source_grounded.

## Implementation Notes

- v07-09의 `ContextDocument`에 의존한다.
- 이 helper들은 v07-11의 answer composer에서 사용된다.
- 순수 함수이며 DB나 파일 I/O 없다.

## Agent Prompt

```text
Implement v07-10 only.

Add citation and confidence helpers.

Files:
- src/answering/__init__.py
- src/answering/citations.py
- src/answering/confidence.py
- tests/test_v07_answer_composer.py

Rules:
- Do not implement the full composer yet.
- Deduplicate sources while preserving order.
- Run:
  python -m unittest tests.test_v07_answer_composer -v
  python -m py_compile src/answering/citations.py src/answering/confidence.py
```
