# v0.7-15: Source Summary Fallback E2E

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-15)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

job wiki가 없을 때 source summary가 fallback으로 사용됨을 E2E 테스트로 증명한다.

## Scope

- E2E test 추가: job wiki 없이 source summary만 있는 상태 → fallback 동작 검증
- `wiki/source_summaries/patch_7_0.md` fixture만 존재 (wiki/jobs/gunbreaker.md 없음)
- answer에 source summary path와 source_id 포함 확인

Out of scope:

- job wiki first 테스트 (v07-14)
- 새로운 기능 구현

## Red Test

- File: `tests/test_v07_ask_cli.py`
- Expected red reason: fallback이 동작하지 않거나 source summary가 context에 포함되지 않음.

Contracts fixed by the tests:

- 첫 context의 wiki_type이 `source_summary`
- answer에 source summary path 포함
- answer에 source_id 포함

## Checklist

- [ ] `tests/test_v07_ask_cli.py` 갱신
  - [ ] temporary root + SQLite DB setup (job wiki 없음)
  - [ ] `wiki/source_summaries/patch_7_0.md` fixture 생성
  - [ ] `test_ask_cli_source_summary_fallback_when_no_job_wiki` 테스트
- [ ] 필요 시 구현 보정
- [ ] green 확인

## Verification

```bash
python -m unittest tests.test_v07_ask_cli -v
```

## Key Decisions

- job wiki가 없는 상태에서 건브레이커 변경 이력 질문을 하면, primary(job wiki) 검색 결과가 0이므로 fallback(source_summary) 실행.
- 이 테스트는 v07-08의 fallback 로직이 정상 동작함을 증명한다.

## Implementation Notes

- v07-14와 동일한 test infrastructure를 사용하되, job wiki fixture를 제외한다.
- 기존 `tools/search_kb.py`는 수정하지 않는다.

## Agent Prompt

```text
Implement v07-15 only.

Add E2E fallback test for tools/ask.py.

Files:
- tests/test_v07_ask_cli.py
- update implementation if needed

Rules:
- If job wiki is missing, source_summary fallback must run.
- Answer must include source summary path or source_id.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
```
