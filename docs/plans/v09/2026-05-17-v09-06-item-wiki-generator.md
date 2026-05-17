# v09-06: Item Wiki Generator and FTS Integration

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 06)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Completed 2026-05-17

## Goal

`guide_items` records에서 `wiki/items` derived pages를 생성하고 existing `wiki_pages`/`wiki_fts` indexing convention에 연결한다.

## Scope

- `src/derived_wiki/item_wiki_generator.py`
- `tools/generate_item_wiki.py`
- `tests/test_guide_ff14_item_wiki.py`
- 필요 시 `src/wiki_indexing/wiki_document_scanner.py`

Out of scope:

- quest/recipe/gathering wiki generation
- unified `generate_derived_wiki.py --kind items` hook unless trivial after independent generator passes
- committing generated `wiki/items/**`

## Red Test

- File: `tests/test_guide_ff14_item_wiki.py`
- Expected red reason: item wiki generator module/tool missing.

Contracts to fix:

- dry-run lists planned paths and writes nothing
- apply writes `wiki/items/index.md`, category page, item page
- item page includes official URL and item/equip level
- missing acquisition data emits explicit absence note
- apply indexes `wiki_pages.type = item`
- apply indexes `wiki_fts`
- rerun is idempotent
- `wiki/index.md` gains or preserves item index link

## Checklist

- [x] temp DB/wiki red tests 작성
- [x] red 상태 확인
- [x] item wiki generator 구현
- [x] CLI 구현
- [x] scanner/indexing integration 구현
- [x] docs/handoff 갱신
- [x] focused and regression tests 실행

## Verification

```bash
python -m unittest tests.test_guide_ff14_item_wiki -v
python -m unittest tests.test_compile_wiki tests.test_guide_ff14_item_wiki -v
git diff --check
python scripts/check_docs_freshness.py --all
```

## Implementation Notes

- Use generated output paths under `wiki/items/`.
- Do not commit generated item wiki pages.
- `index_wiki_documents()` now includes item wiki pages in its scanner summary.

## Agent Prompt

```text
v09 Task 06을 수행한다. temp DB/wiki red tests를 먼저 작성하고 item wiki generator와 FTS integration만 구현한다.
```
