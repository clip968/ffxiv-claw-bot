# v0.7-12: tools/ask.py CLI Skeleton and JSON Contract

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-12)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

v07 ask pipeline의 공식 CLI인 `tools/ask.py`를 추가하고 안정적인 JSON 출력 계약을 정의한다.

## Scope

- `tools/ask.py` CLI 생성
- CLI options: `question`, `--format json|text`, `--debug`, `--limit`, `--db-path`, `--root-path`
- 파이프라인 연결: parse_query → build_retrieval_plan → execute_retrieval_plan → build_context_pack → compose_answer
- JSON output contract 정의
- 빈 question에 대한 status=error 반환
- debug mode에서 parsed_query와 retrieval_plan 포함

Out of scope:

- text output formatting (v07-13)
- E2E tests (v07-14, v07-15)
- Discord integration

## Red Test

- File: `tests/test_v07_ask_cli.py`
- Implementation target: `tools/ask.py`
- Expected red reason: `tools/ask.py` 미존재 또는 import 실패.

Contracts fixed by the tests:

- `tools/ask.py` 실행 시 valid JSON 반환
- 빈 question은 `status=error` 반환
- debug mode에서 `parsed_query`와 `retrieval_plan` 포함

## JSON Contract

```json
{
  "status": "ok",
  "question": "...",
  "parsed_query": {},
  "retrieval_plan": {},
  "contexts": [],
  "answer": {
    "format": "text",
    "body": "...",
    "confidence": "...",
    "sources": []
  },
  "actions": []
}
```

## Checklist

- [ ] `tools/ask.py` 생성
  - [ ] argparse 설정 (question, --format, --debug, --limit, --db-path, --root-path)
  - [ ] 파이프라인 연결
  - [ ] JSON output 구현
  - [ ] 빈 question 검증
  - [ ] debug mode
- [ ] `tests/test_v07_ask_cli.py` 생성
  - [ ] `test_ask_cli_json_contract_no_context`
  - [ ] `test_ask_cli_rejects_empty_question`
  - [ ] `test_ask_cli_debug_includes_parsed_query_and_retrieval_plan`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_ask_cli -v
python -m py_compile tools/ask.py
```

## Key Decisions

- JSON contract의 top-level key는 안정적이다. 향후 추가만 가능하고 삭제/변경 불가.
- `--format` 기본값은 `json`.
- `--debug` 없으면 `parsed_query`와 `retrieval_plan`을 출력에서 제외.
- `actions` 필드는 향후 Discord adapter에서 사용할 예약 필드. 현재는 빈 list.

## Implementation Notes

- v07-01~11의 모든 구현에 의존한다. Batch D의 첫 task이다.
- 기존 `tools/answer.py`를 수정하지 않는다. `tools/ask.py`는 별도 entrypoint이다.
- test에서는 subprocess로 `tools/ask.py`를 실행하거나, 내부 함수를 직접 호출한다.

## Agent Prompt

```text
Implement v07-12 only.

Add tools/ask.py with JSON output contract.

Files:
- tools/ask.py
- tests/test_v07_ask_cli.py

Rules:
- Wire together parse_query, build_retrieval_plan, retrieval execution, context builder, and composer.
- Support --format json|text, --debug, --limit, --db-path, --root-path.
- Empty question must return status=error.
- Do not implement Discord.
- Do not implement crawling.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
  python -m py_compile tools/ask.py
```
