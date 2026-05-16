# v0.7-07: Filtered FTS Search

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-07)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

`wiki_fts`에 대해 `wiki_pages.type`과 topic/job 필터링을 적용하여 검색하는 함수를 구현한다.

## Scope

- `src/retrieval/fts_search.py` 추가
- `SearchResult` model 추가 (page_id, title, wiki_type, path, score, snippet, topic)
- `search_wiki()` 함수: SQLite wiki_fts + wiki_pages JOIN, optional filters
- FTS query sanitization (기존 `tools/search_kb.py` 로직 참고 또는 재사용)
- wiki_type filter (`job`, `source_summary`, `None`)
- topic/job filter

Out of scope:

- retrieval plan 실행 로직 (v07-08)
- context pack building (v07-09)
- vector search / embedding

## Red Test

- File: `tests/test_v07_retrieval.py`
- Implementation target: `src/retrieval/fts_search.py`
- Expected red reason: `src.retrieval.fts_search` module 미존재 또는 `SearchResult` 미정의.

Contracts fixed by the tests:

- wiki_type=job 필터 시 job page만 반환
- topic=gunbreaker 필터 시 해당 job page만 반환
- source_summary fallback 검색 가능
- unsafe FTS characters (예: `"`, `*`, `(`) 가 crash하지 않음

## Checklist

- [ ] `src/retrieval/fts_search.py` 생성
  - [ ] `search_wiki()` 함수 구현
  - [ ] FTS query sanitization
  - [ ] wiki_pages JOIN
  - [ ] wiki_type filter
  - [ ] topic/job filter
- [ ] `src/retrieval/models.py` 갱신
  - [ ] `SearchResult` frozen dataclass 추가
- [ ] `tests/test_v07_retrieval.py` 갱신
  - [ ] `test_search_wiki_filters_by_wiki_type_job`
  - [ ] `test_search_wiki_filters_by_topic`
  - [ ] `test_search_wiki_returns_source_summary_fallback`
  - [ ] `test_search_wiki_sanitizes_fts_query`
- [ ] temporary SQLite DB를 사용하는 test fixture 구성
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v07_retrieval -v
python -m py_compile src/retrieval/fts_search.py
```

기존 search_kb.py regression:

```bash
python -m unittest discover -s tests -p "test_*.py"
```

## Key Decisions

- `tools/search_kb.py`의 FTS query format 로직을 재사용하거나 동등한 sanitization을 구현한다.
- `tools/search_kb.py`의 외부 인터페이스는 수정하지 않는다.
- test에서는 temporary SQLite DB를 생성하여 wiki_pages + wiki_fts를 직접 구성한다.
- `snippet()` FTS 함수를 사용하여 검색 결과 미리보기를 반환한다.

## Implementation Notes

- v07-06의 retrieval models에 의존한다.
- v06에서 만든 `wiki_pages` 테이블의 `type`, `job` 컬럼을 활용한다.
- SQL JOIN: `wiki_fts JOIN wiki_pages ON wiki_fts.page_id = wiki_pages.id`.

## Agent Prompt

```text
Implement v07-07 only.

Add filtered FTS search for the ask pipeline.

Files:
- src/retrieval/fts_search.py
- src/retrieval/models.py
- tests/test_v07_retrieval.py

Rules:
- Search wiki_fts joined with wiki_pages.
- Support wiki_type filter.
- Support topic/job filter.
- Reuse or preserve existing FTS query sanitization.
- Do not modify the output contract of tools/search_kb.py.
- Use temporary SQLite DBs in tests.
- Run:
  python -m unittest tests.test_v07_retrieval -v
  python -m py_compile src/retrieval/fts_search.py
```
