# v09-00: Baseline Repo Inspection and Guardrails

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 00)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Completed 2026-05-17

## Goal

v09 구현 전 repo의 DB, wiki, graph, ask, test, finish workflow 패턴을 확인하고 generated crawler artifacts가 커밋되지 않도록 guardrail을 둔다.

## Scope

- existing workflow/docs/spec inspection
- DB init/migration style 확인
- wiki indexing style 확인
- graph report and ask retrieval style 확인
- test fixture/temp DB style 확인
- generated artifact ignore rule 확인/보강

Out of scope:

- crawler product code
- live network access
- DB schema changes

## Red Test

No red test required. Inspection/documentation-only task.

## Checklist

- [x] `CLAUDE.md`, `docs/WORKFLOW.md`, handoff 확인
- [x] v09 spec/master plan 확인
- [x] `tools/init_db.py`, `tools/compile_wiki.py`, graph/ask tools 확인
- [x] tests/fixtures/temp DB convention 확인
- [x] `.gitignore` generated artifact coverage 확인
- [x] `data/raw/guide_ff14/`, `wiki/items/` ignore 추가
- [x] baseline report 작성
- [x] handoff/status 갱신

## Verification

```bash
git diff --check
python scripts/check_docs_freshness.py --all
```

## Implementation Notes

- Baseline report: `docs/reports/2026-05-17-v09-task-00-baseline.md`
- Commit: `be7fdee docs: add v09 crawler baseline`

## Agent Prompt

```text
v09 Task 00을 수행한다. repo baseline을 inspection-only로 확인하고 generated artifact guardrail만 보강한다.
```
