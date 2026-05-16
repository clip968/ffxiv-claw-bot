# v0.6-12: FTS Indexing Extension for Derived Wiki

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-12)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

FTS 인덱싱이 `wiki/source_summaries/*.md`뿐 아니라 derived wiki 문서(`wiki/jobs/*.md` 등)도 포함하도록 확장한다.

기존 source summary 인덱싱 동작은 회귀 없이 보존한다.

## Scope

- `src/wiki_indexing/__init__.py`
- `src/wiki_indexing/wiki_document_scanner.py` 추가 또는 기존 scanner 확장
- 다음 경로를 인덱싱 대상으로 포함
  - `wiki/source_summaries/*.md`
  - `wiki/jobs/*.md`
- `wiki_type` metadata 추가
  - `source_summary`
  - `job`
- `topic` metadata 추가 (예: `wiki/jobs/gunbreaker.md` → `topic=gunbreaker`)
- 기존 FTS schema에 backward-compatible하게 column/metadata 확장
- 기존 source_summaries 인덱싱 회귀 보호

Out of scope:

- derived wiki hook (v06-13)
- `tools/search_kb.py` UX 변경 (필요 최소만 처리)
- vector DB
- 새 검색 알고리즘

## Red Test

- File: `tests/test_v06_fts_indexing.py`
- Implementation target: `src/wiki_indexing/wiki_document_scanner.py`, 기존 FTS module
- Expected red reason: scanner가 `wiki/jobs/*.md`를 인덱싱 대상에 포함하지 않거나, `wiki_type`/`topic` metadata를 채우지 않는다.

Contracts fixed by the tests:

- scanner는 source_summaries를 인덱싱 대상에 포함한다 (기존 동작 회귀 보호).
- scanner는 `wiki/jobs/*.md`를 인덱싱 대상에 포함한다.
- job wiki entry의 `wiki_type`은 `job`이다.
- source summary entry의 `wiki_type`은 `source_summary`이다.
- job wiki entry의 `topic`은 filename stem과 일치한다 (`gunbreaker.md` → `gunbreaker`).
- 기존 FTS search 결과 형식은 깨지지 않는다.

## Checklist

- [x] `src/wiki_indexing/__init__.py` 생성
- [x] `src/wiki_indexing/wiki_document_scanner.py` 구현
  - [x] `scan_wiki_documents(root_path: Path) -> list[WikiDocument]`
  - [x] entry shape: `path`, `wiki_type`, `topic`, `title`, `text`
- [x] 기존 FTS module과 연결 (insert/update path)
- [x] FTS schema 확장: `wiki_fts`는 기존 `page_id/title/body`를 유지하고, `wiki_type/topic`은 `wiki_pages.type/job`에 저장
- [x] 기존 source_summaries 인덱싱 회귀 테스트
- [x] `tests/test_v06_fts_indexing.py`에 다음 테스트 추가
  - [x] `test_fts_scanner_includes_source_summaries`
  - [x] `test_fts_scanner_includes_job_wiki_pages`
  - [x] `test_fts_scanner_sets_wiki_type_for_source_summaries`
  - [x] `test_fts_scanner_sets_wiki_type_for_job_pages`
  - [x] `test_fts_scanner_sets_topic_from_job_filename`
  - [x] `test_existing_source_summary_indexing_still_works`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_fts_indexing -v
python -m unittest discover -s tests -p "test_*.py"
```

수동 검색 smoke (선택):

```bash
python tools/search_kb.py "건브레이커"
python tools/search_kb.py "gunbreaker"
```

## Key Decisions

- FTS schema 변경은 backward-compatible해야 한다. 새 column 추가는 NULL 허용 또는 기본값 처리로 해결한다.
- 인덱싱 대상은 파일 시스템 기반으로 시작한다. DB 기반은 Open Question 4 해결 후 검토.
- `wiki_type` enum은 v0.6 기준 `source_summary`, `job` 두 가지만 정의한다. 향후 `raid`, `item`, `system` 추가는 v0.7+에서 한다.
- scanner는 idempotent해야 한다. 동일 파일을 두 번 스캔해도 중복 entry가 생기지 않는다.

## Implementation Notes

- v06-10에서 wiki/jobs/*.md가 실제 생성되어 있어야 통합 테스트가 의미를 가진다.
- 기존 FTS module의 함수 이름/시그니처를 확인 후, 호환 가능한 확장 방식을 선택한다 (Open Question 4).
- 한국어 alias 검색이 잘 동작하도록 tokenizer 설정을 점검한다. 필요한 경우 별도 task로 분리.

## Verification Results

- Red: `python -m unittest tests.test_v06_fts_indexing -v` failed with expected missing `src.wiki_indexing` scanner errors and missing `tools.compile_wiki.index_wiki_documents`.
- Green: `python -m unittest tests.test_v06_fts_indexing -v` passed 7 tests after adding the wiki document scanner and derived wiki indexing path.
- Regression: `python -m unittest tests.test_compile_wiki -v` passed 3 tests.
- Regression: `python -m py_compile src/wiki_indexing/wiki_document_scanner.py src/wiki_indexing/__init__.py tools/compile_wiki.py` passed.
- Docs: `python scripts/check_docs_freshness.py --all` passed.
- Full suite: `python -m unittest discover -s tests -p "test_*.py"` passed 213 tests.
