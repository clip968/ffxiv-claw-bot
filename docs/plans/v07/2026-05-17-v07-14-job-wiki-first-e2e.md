# v0.7-14: Job Wiki First E2E

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-14)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Completed 2026-05-17

## Goal

job 변경 이력 질문이 `wiki/jobs/<job>.md`를 source summary보다 우선 사용함을 E2E 테스트로 증명한다.

## Scope

- E2E test 추가: 임시 DB + 임시 파일 → `tools/ask.py` 파이프라인 실행 → job wiki가 primary context인지 검증
- `wiki/jobs/gunbreaker.md` fixture
- `wiki/source_summaries/patch_7_0.md` fixture
- `index_wiki_documents()`로 FTS 인덱싱

Out of scope:

- fallback 테스트 (v07-15)
- 새로운 기능 구현 (이미 v07-01~12에서 완료된 상태)

## Red Test

- File: `tests/test_v07_ask_cli.py`
- Expected red reason: job wiki가 primary context로 선택되지 않음 (구현 미완성 시).

Contracts fixed by the tests:

- `contexts[0].page_id == "job_gunbreaker"`
- answer에 `wiki/jobs/gunbreaker.md` path 포함
- answer에 job wiki content 포함

## Checklist

- [x] `tests/test_v07_ask_cli.py` 갱신
  - [x] temporary root + SQLite DB setup
  - [x] `wiki/jobs/gunbreaker.md` fixture 생성
  - [x] `wiki/source_summaries/patch_7_0.md` fixture 생성
  - [x] `index_wiki_documents()` 호출로 FTS 인덱싱
  - [x] `test_ask_cli_job_change_history_uses_job_wiki_first` 테스트
- [x] 필요 시 구현 보정 (v07-07 또는 v07-08의 필터링 로직)
- [x] green 확인

## Verification

```bash
python -m unittest tests.test_v07_ask_cli -v
```

## Key Decisions

- test에서는 실제 `tools.compile_wiki.index_wiki_documents()`를 호출하여 FTS를 구축한다.
- fixture 파일은 테스트 내에서 임시 디렉토리에 생성한다.
- 이 테스트는 v07의 핵심 가치 증명이다: "job wiki가 source summary보다 우선한다."

## Implementation Notes

- v07-01~12 전체에 의존한다.
- 만약 이 E2E가 실패하면, v07-07이나 v07-08의 필터링 로직을 수정해야 할 수 있다.
- 기존 `tools/search_kb.py`는 수정하지 않는다.

## Agent Prompt

```text
Implement v07-14 only.

Add E2E test proving tools/ask.py uses job wiki first.

Files:
- tests/test_v07_ask_cli.py
- update implementation if needed

Rules:
- Use temporary root and SQLite DB.
- Create wiki/jobs/gunbreaker.md and wiki/source_summaries/*.md fixtures.
- Use tools.compile_wiki.index_wiki_documents() for indexing.
- Assert job_gunbreaker is first context.
- Run:
  python -m unittest tests.test_v07_ask_cli -v
```
