# v0.7-17: Full Regression Verification

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-17)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

v07 전체 테스트 + 기존 v06 regression + full test suite를 실행하여 v07이 기존 기능을 깨뜨리지 않았음을 확인한다.

## Scope

- v07 전체 테스트 실행
- v06 regression 테스트 실행
- full test suite 실행
- docs freshness check
- `tools/ask.py` smoke test

Out of scope:

- 새로운 기능 구현
- 새로운 테스트 추가 (버그 발견 시 최소 패치만)

## Required Commands

```bash
python -m unittest tests.test_v07_query_parser -v
python -m unittest tests.test_v07_retrieval -v
python -m unittest tests.test_v07_context_builder -v
python -m unittest tests.test_v07_answer_composer -v
python -m unittest tests.test_v07_ask_cli -v

python -m unittest tests.test_v06_extractors -v
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v06_job_wiki_generator -v
python -m unittest tests.test_v06_fts_indexing -v

python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

## Smoke Test

```bash
python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json
```

## Checklist

- [ ] v07 tests 전체 통과
- [ ] v06 tests 전체 통과
- [ ] full test suite 통과
- [ ] docs freshness check 통과
- [ ] smoke test valid JSON 반환
- [ ] 버그 발견 시 최소 패치 적용 후 재실행

## Acceptance Criteria

- All v07 tests pass.
- Existing v06 tests pass.
- Full test suite passes.
- Docs freshness check passes.
- `python tools/ask.py "7.x 건브레이커 변경 이력 알려줘" --format json` returns valid JSON.

## Key Decisions

- 코드를 수정하지 않는 것이 원칙이다. 진짜 버그만 최소 패치.
- 실패 시 원인을 보고하고, 관련 task로 되돌려 수정한다.

## Implementation Notes

- verification-only task이므로 새 코드 작성 불필요.
- v07-01~16 전체 완료 후 실행한다.
- 이 task 통과 시 v07 완료.

## Agent Prompt

```text
Implement v07-17 verification only.

Run all v07 tests, all v06 tests, full unittest discovery, and docs freshness check.

Do not modify code unless a test failure reveals a real bug.
If fixing is required:
- explain the failing test
- patch only the minimal affected files
- rerun the relevant tests
- then rerun the full verification commands

Report:
- commands run
- pass/fail result
- files changed
- remaining known limitations
```
