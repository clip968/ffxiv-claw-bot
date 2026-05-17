# v09-08: Item-Aware Retrieval and Ask Smoke Behavior

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 08)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Pending

## Goal

item wiki pages가 존재할 때 item/title/category queries가 broad source summaries나 unrelated job guides보다 item context를 우선하도록 retrieval/ask behavior를 조정한다.

## Scope

- existing retrieval/ranking logic
- `tests/test_guide_ff14_item_retrieval.py`

Out of scope:

- vector DB
- LLM extraction
- hard-coded single item answer path

## Red Test

- File: `tests/test_guide_ff14_item_retrieval.py`
- Expected red reason: item-specific ranking/provenance behavior missing.

Contracts to fix:

- item/weapon/gunblade queries rank `wiki_pages.type = item` first
- `건브 무기` does not rank unrelated job guide first when item pages exist
- answer includes official URL/provenance
- missing acquisition data gets explicit absence wording
- non-item job queries continue to work
- JSON output remains backward-compatible

## Checklist

- [ ] temp wiki/FTS red tests 작성
- [ ] red 상태 확인
- [ ] ranking/policy 최소 조정
- [ ] existing ask/retrieval regressions 실행
- [ ] docs/handoff 갱신

## Verification

```bash
python -m unittest tests.test_guide_ff14_item_retrieval -v
python -m unittest tests.test_v07_retrieval tests.test_v07_context_builder tests.test_v07_answer_composer tests.test_v07_ask_cli tests.test_v08_5_precision_regression -v
git diff --check
python scripts/check_docs_freshness.py --all
```

## Agent Prompt

```text
v09 Task 08을 수행한다. temp wiki/FTS red tests를 먼저 작성하고 item-aware retrieval behavior만 최소 조정한다.
```
