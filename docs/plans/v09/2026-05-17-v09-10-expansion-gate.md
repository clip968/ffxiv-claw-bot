# v09-10: Expansion-Gate Documentation Only

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 10)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Pending

## Goal

quest/recipe/gathering expansion이 item pilot quality gates 이전에 구현되지 않도록 future expansion gate를 문서화한다.

## Scope

- spec/runbook future-work section
- explicit gate statement
- intended future entities/edges outline

Out of scope:

- `guide_quests`, `guide_recipes`, `guide_gathering_entries`
- quest/recipe/gathering crawler modes
- quest/recipe/gathering wiki generators
- quest/recipe/gathering graph/retrieval behavior

## Red Test

No red test required. Documentation-only task.

## Checklist

- [ ] expansion gate docs 확인/보강
- [ ] future entities/edges outline 유지
- [ ] no new quest/recipe/gathering code 확인
- [ ] docs freshness 실행
- [ ] handoff 갱신

## Verification

```bash
git diff -- docs
python scripts/check_docs_freshness.py --all
```

## Agent Prompt

```text
v09 Task 10을 수행한다. quest/recipe/gathering expansion gate만 문서화하고 어떤 expansion code도 구현하지 않는다.
```
