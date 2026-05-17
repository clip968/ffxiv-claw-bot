# v09-01: SQLite Schema and Storage Layer

## Spec

- Master plan: `docs/plans/v09/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v09-implementation-guide-ff14-crawler.md` (Task 01)
- Crawler spec: `docs/specs/0011-v09-guide-ff14-official-db-crawler.md`

## Status

Completed 2026-05-17

## Goal

v09 crawl state와 structured item records를 저장할 idempotent SQLite schema/storage layer를 추가한다.

## Scope

- `src/guide_ff14/__init__.py`
- `src/guide_ff14/models.py`
- `src/guide_ff14/storage.py`
- `tools/init_db.py` schema hook
- `docs/DOC_OWNERS.yml` v09 rule
- storage tests

Out of scope:

- network fetch
- category parsing
- crawler CLI
- item wiki/graph/retrieval

## Red Test

- File: `tests/test_guide_ff14_storage.py`
- Expected red reason: `src.guide_ff14` module missing.

Contracts fixed by the tests:

- schema creation is idempotent
- crawl page upsert dedupes by URL
- category upsert dedupes by URL/id
- item upsert dedupes by detail id/URL
- JSON fields remain valid
- `created_at` is preserved and `updated_at` changes

## Checklist

- [x] storage tests 작성
- [x] red 상태 확인
- [x] dataclass models 추가
- [x] guide schema helper 추가
- [x] idempotent upsert helpers 추가
- [x] `tools/init_db.py` schema hook 추가
- [x] DOC_OWNERS v09 rule 추가
- [x] docs/handoff 갱신

## Verification

```bash
python -m unittest tests.test_guide_ff14_storage -v
python -m unittest tests.test_compile_wiki tests.test_guide_ff14_storage -v
python tools/init_db.py
git diff --check
python scripts/check_docs_freshness.py --all
```

## Implementation Notes

- Commit: `e5207f4 feat: add v09 guide storage schema`

## Agent Prompt

```text
v09 Task 01을 수행한다. 먼저 temp SQLite DB red tests를 작성하고, schema/storage를 최소 구현한다.
```
