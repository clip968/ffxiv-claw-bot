# v09-04: Item Detail Extractor

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 04)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Completed 2026-05-17

## Goal

official guide item detail HTML fixture에서 structured item record를 추출한다. 보이지 않는 게임 사실은 추론하지 않는다.

## Scope

- item detail fixture
- `src/guide_ff14/item_extractor.py`
- `tests/test_guide_ff14_item_extractor.py`

Out of scope:

- live network
- crawler CLI
- LLM extraction

## Red Test

- File: `tests/test_guide_ff14_item_extractor.py`
- Expected red reason: `src.guide_ff14.item_extractor` module missing.

Contracts fixed by the tests:

- official detail id from URL
- Korean item name preservation
- item/equip levels
- job restrictions list
- stats dict
- missing optional fields tolerated
- nav/footer/search/script noise removed
- content hash/raw path returned

## Checklist

- [x] item detail fixture 추가
- [x] red tests 작성
- [x] red 상태 확인
- [x] deterministic extractor 구현
- [x] missing optional-field coverage 추가
- [x] docs/handoff 갱신

## Verification

```bash
python -m unittest tests.test_guide_ff14_item_extractor tests.test_guide_ff14_fetcher tests.test_guide_ff14_category_map tests.test_guide_ff14_storage -v
python -m py_compile src/guide_ff14/item_extractor.py src/guide_ff14/__init__.py
git diff --check
python scripts/check_docs_freshness.py --all
```

## Implementation Notes

- Commit: `9b08501 feat: extract guide item details`

## Agent Prompt

```text
v09 Task 04를 수행한다. local HTML fixture와 red tests를 먼저 작성하고 item detail extractor만 구현한다.
```
