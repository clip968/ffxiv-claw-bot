# v09 Task 09 Quality Gate Report

Date: 2026-05-17

## Scope

- Added `docs/runbooks/guide-ff14-crawler.md`.
- Updated runbook index and v09 plan/handoff docs.
- No product code changes.
- Live guide.ff14.co.kr smoke was not executed because maintainer-approved live
  crawl scope was not provided in this task.

## Automated Verification

```bash
python -m unittest tests.test_guide_ff14_storage tests.test_guide_ff14_category_map tests.test_guide_ff14_fetcher tests.test_guide_ff14_item_extractor tests.test_guide_ff14_crawler tests.test_guide_ff14_item_wiki tests.test_guide_ff14_item_graph tests.test_guide_ff14_item_retrieval -v
```

Result: 50 tests OK.

```bash
git diff --check
```

Result: OK.

```bash
python scripts/check_docs_freshness.py --all
```

Result: OK.

```bash
python scripts/finish_task.py
```

Result: 417 tests OK, docs freshness OK, Notion handoff dry-run OK.

## Manual Smoke Status

Skipped. The runbook documents the manual/network-approved commands for robots
check, category-map dry run, item-pilot dry run/apply, item wiki generation,
FTS re-index, graph report, and ask smoke. These should only be run against the
live official guide after explicit maintainer approval of crawl scope.

## Remaining Risk

- Live guide.ff14.co.kr structure can drift. Fixture/unit coverage protects the
  current parser and extractor contract, but live smoke is still required before
  increasing crawl limits.
- Generated raw HTML, DB, wiki item pages, and graph outputs remain local state
  and must not be committed.
