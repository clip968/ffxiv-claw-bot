# v09-05: Item Pilot Crawler and CLI

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 05)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Completed 2026-05-17

## Goal

bounded item pilot crawl flow와 `tools/crawl_guide_ff14.py` JSON CLI를 구현한다.

## Scope

- category fixture for item list
- `src/guide_ff14/crawler.py`
- `tools/crawl_guide_ff14.py`
- `tests/test_guide_ff14_crawler.py`

Out of scope:

- quest/recipe/gathering crawl
- live network unit tests
- item wiki generation

## Red Test

- File: `tests/test_guide_ff14_crawler.py`
- Expected red reason: `src.guide_ff14.crawler` and `tools.crawl_guide_ff14` missing.

Contracts fixed by the tests:

- dry-run returns planned URLs and does not mutate DB/raw dir
- apply `--limit 1` stores one item
- apply rerun is idempotent
- category failure aborts detail fetches
- detail failure records partial error and continues
- detail URLs are absolute and limited
- JSON output contains required keys
- CLI prints structured JSON with fake fetcher

## Checklist

- [x] item category fixture 추가
- [x] crawler/CLI red tests 작성
- [x] red 상태 확인
- [x] detail discovery 구현
- [x] item-pilot dry-run/apply 구현
- [x] raw snapshot writing 구현
- [x] `tools/crawl_guide_ff14.py` 구현
- [x] docs/handoff 갱신

## Verification

```bash
python -m unittest tests.test_guide_ff14_crawler tests.test_guide_ff14_item_extractor tests.test_guide_ff14_fetcher tests.test_guide_ff14_category_map tests.test_guide_ff14_storage -v
python -m py_compile src/guide_ff14/crawler.py tools/crawl_guide_ff14.py src/guide_ff14/__init__.py
git diff --check
python scripts/check_docs_freshness.py --all
```

## Implementation Notes

- Commit: `c2a8bb2 feat: add guide item pilot crawler`

## Agent Prompt

```text
v09 Task 05를 수행한다. fake fetcher/storage tests를 먼저 작성하고 bounded item-pilot crawler와 CLI만 구현한다.
```
