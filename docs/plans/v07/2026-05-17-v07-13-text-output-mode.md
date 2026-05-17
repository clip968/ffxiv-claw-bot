# v0.7-13: Text Output Mode

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-13)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Completed 2026-05-17

## Goal

`tools/ask.py --format text`가 사람이 읽기 좋은 plain text를 출력하도록 한다.

## Scope

- `tools/ask.py`의 `--format text` 경로 구현
- answer body만 출력 (JSON braces 없음)
- 기존 `--format json` 동작 유지

Out of scope:

- E2E tests (v07-14, v07-15)
- Discord formatting
- rich terminal output (color, table 등)

## Red Test

- File: `tests/test_v07_ask_cli.py`
- Implementation target: `tools/ask.py`
- Expected red reason: text output 시 JSON 형태가 출력되거나 body만 출력되지 않음.

Contracts fixed by the tests:

- `--format text` 출력에 answer body가 포함된다.
- `--format text` 출력에 `{`, `}` JSON braces가 없다.
- `--format json` 동작은 변경되지 않는다.

## Checklist

- [x] `tools/ask.py` 갱신
  - [x] `--format text` 분기 추가
  - [x] answer body만 stdout 출력
- [x] `tests/test_v07_ask_cli.py` 갱신
  - [x] `test_ask_cli_text_output_contains_answer_body`
  - [x] `test_ask_cli_text_output_no_json_braces`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_ask_cli -v
```

## Key Decisions

- text mode는 answer.body를 그대로 출력한다. 추가 formatting 없음.
- sources나 confidence를 text mode에도 포함할지는 향후 결정. 현재는 body만.

## Implementation Notes

- v07-12에 의존한다.
- 간단한 분기 추가이므로 최소 변경.

## Agent Prompt

```text
Implement v07-13 only.

Add text output mode to tools/ask.py.

Files:
- tools/ask.py
- tests/test_v07_ask_cli.py

Rules:
- --format text prints the answer body only.
- --format json remains unchanged.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
```
