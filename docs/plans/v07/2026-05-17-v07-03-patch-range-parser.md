# v0.7-03: Patch Range Parser

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-03)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Completed 2026-05-17

## Goal

사용자 질문에서 숫자 패치 버전 표현을 파싱하여 정규화된 범위 문자열(`major.minor..major.minor`)을 반환하는 `parse_patch_range()` 함수를 구현한다.

## Scope

- `src/query/patch_parser.py` 추가
- 단일 패치: `7.2` → `"7.2..7.2"`
- X 범위: `7.x` → `"7.0..7.99"`
- 틸드/대시 범위: `7.0~7.5`, `7.0-7.5` → `"7.0..7.5"`
- 한국어 범위: `7.0부터 7.5까지` → `"7.0..7.5"`
- 패치 번호 없으면 `None` 반환

Out of scope:

- expansion name mapping (예: 황금의 레거시 → 7.x)
- 의미적 범위 해석

## Red Test

- File: `tests/test_v07_query_parser.py`
- Implementation target: `src/query/patch_parser.py`
- Expected red reason: `src.query.patch_parser` module 미존재.

Contracts fixed by the tests:

- `parse_patch_range("7.2 패치")` → `"7.2..7.2"`
- `parse_patch_range("7.x 변경점")` → `"7.0..7.99"`
- `parse_patch_range("7.0~7.5 변경 이력")` → `"7.0..7.5"`
- `parse_patch_range("7.0-7.5 변경 이력")` → `"7.0..7.5"`
- `parse_patch_range("7.0부터 7.5까지")` → `"7.0..7.5"`
- `parse_patch_range("건브레이커 변경 이력")` → `None`

## Checklist

- [x] `src/query/patch_parser.py` 생성
  - [x] `parse_patch_range(query: str) -> str | None` 구현
  - [x] 한국어 범위 패턴 (`부터...까지`)
  - [x] 명시적 범위 패턴 (`~`, `-`, `–`)
  - [x] X 범위 패턴 (`N.x`)
  - [x] 단일 패치 패턴 (`N.M`)
- [x] `src/query/__init__.py` 갱신 (re-export)
- [x] `tests/test_v07_query_parser.py` 갱신
  - [x] `test_parse_single_patch`
  - [x] `test_parse_x_patch_range`
  - [x] `test_parse_tilde_patch_range`
  - [x] `test_parse_dash_patch_range`
  - [x] `test_parse_korean_range`
  - [x] `test_parse_no_patch_returns_none`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_query_parser -v
python -m py_compile src/query/patch_parser.py
```

## Key Decisions

- 패턴 매칭 우선순위: 한국어 범위 → 명시적 범위 → X 범위 → 단일 패치.
- expansion name (예: "황금의 레거시") → patch 범위 매핑은 v0.7에서 구현하지 않는다.
- 정규화된 출력 형태는 항상 `"major.minor..major.minor"` 또는 `None`이다.

## Implementation Notes

- v07-01의 `src/query/` 패키지에 의존한다.
- regex 기반 순수 함수이며 외부 의존성 없다.
- `tools/search_kb.py`나 `tools/answer.py`를 수정하지 않는다.
- Red verification: `python -m unittest tests.test_v07_query_parser.V07PatchRangeParserTests -v` failed because `parse_patch_range` was not importable from `src.query`.
- Green verification: `python -m unittest tests.test_v07_query_parser -v` passed 14 tests.
- Compile verification: `python -m py_compile src/query/patch_parser.py src/query/__init__.py` passed.

## Agent Prompt

```text
Implement v07-03 only.

Add numeric patch range parsing for v07.

Files:
- src/query/patch_parser.py
- src/query/__init__.py
- tests/test_v07_query_parser.py

Rules:
- Support 7.2, 7.x, 7.0~7.5, 7.0-7.5, 7.0부터 7.5까지.
- Do not implement expansion name mapping.
- Return normalized string like 7.0..7.5 or None.
- Run:
  python -m unittest tests.test_v07_query_parser -v
  python -m py_compile src/query/patch_parser.py
```
