# v0.6-08: Derived Wiki Foundation

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-8)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

`wiki/source_summaries/*.md`를 읽어 derived wiki 생성에 사용할 입력 모델로 변환하는 foundation layer를 추가한다.

이 task는 derived wiki 생성을 위한 데이터 로딩과 파일 출력 helper만 책임지며, 직업별/주제별 추출은 후속 task에서 다룬다.

## Scope

- `src/derived_wiki/__init__.py` 추가
- `src/derived_wiki/summary_loader.py` 추가
  - `wiki/source_summaries/` 디렉터리 scan
  - source summary 파일에서 `source_id`, `patch_version`, `title`, `text` 추출
  - patch version 추출 우선순위: filename → heading → metadata
- `src/derived_wiki/writer.py` 추가
  - target path에 Markdown 파일 작성
  - parent directory 자동 생성
- `src/derived_wiki/templates.py` 추가 (기본 heading/section template)
- fixture source summaries 추가 (`patch_7_0.md`, `patch_7_1.md`)
- 데이터 모델: `SourceSummary(source_id, patch_version, title, text, path)` 또는 dict

Out of scope:

- job catalog (v06-09)
- job wiki generator (v06-10)
- generate_derived_wiki CLI (v06-11)
- FTS 통합 (v06-12)
- LLM 요약

## Red Test

- File: `tests/test_v06_job_wiki_generator.py`
- Fixtures:
  - `tests/fixtures/source_summaries/patch_7_0.md`
  - `tests/fixtures/source_summaries/patch_7_1.md`
- Implementation target:
  - `src/derived_wiki/summary_loader.py`
  - `src/derived_wiki/writer.py`
  - `src/derived_wiki/templates.py`
- Expected red reason: `src.derived_wiki` 패키지가 아직 없거나 loader/writer가 비어 있다.

Contracts fixed by the tests:

- summary_loader는 fixture 디렉터리에서 모든 `*.md`를 읽는다.
- 각 summary는 `source_id`, `patch_version`, `title`, `text`를 가진다.
- `patch_7_0.md` → `patch_version=7.0`, `patch_7_1.md` → `7.1`
- writer는 target path의 parent directory가 없으면 생성한다.
- writer는 UTF-8로 파일을 쓴다.

## Checklist

- [x] `src/derived_wiki/__init__.py` 생성
- [x] `src/derived_wiki/summary_loader.py` 구현
  - [x] `load_summaries(root: Path) -> list[SourceSummary]`
  - [x] source_id 추출 (filename stem 또는 metadata)
  - [x] patch_version 추출 (filename → heading → metadata)
  - [x] title 추출 (첫 heading 또는 metadata)
  - [x] text 본문 로딩
- [x] `src/derived_wiki/writer.py` 구현
  - [x] `write_derived_wiki(path: Path, content: str)`
  - [x] parent directory 생성
  - [x] UTF-8 write
- [x] `src/derived_wiki/templates.py` 구현
  - [x] 기본 heading/section template helper
- [x] fixture 추가
  - [x] `tests/fixtures/source_summaries/patch_7_0.md`
  - [x] `tests/fixtures/source_summaries/patch_7_1.md`
- [x] `tests/test_v06_job_wiki_generator.py`에 다음 테스트 추가
  - [x] `test_summary_loader_reads_source_summary_files`
  - [x] `test_summary_loader_extracts_source_id`
  - [x] `test_summary_loader_extracts_patch_version_from_filename`
  - [x] `test_summary_loader_extracts_patch_version_from_heading`
  - [x] `test_summary_writer_writes_to_target_path`
  - [x] `test_summary_writer_creates_missing_parent_directory`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_job_wiki_generator -v
python -m py_compile \
  src/derived_wiki/summary_loader.py \
  src/derived_wiki/writer.py \
  src/derived_wiki/templates.py
```

## Key Decisions

- summary_loader는 파일 시스템 기반 scanning으로 시작한다. DB 기반은 Open Question 5 해결 후 검토.
- patch_version은 string으로 보존한다 (`"7.0"`, `"7.1"`). semantic version object 도입은 v0.6 범위 외.
- summary 모델은 `@dataclass`로 시작한다.
- LLM 호출/요약 가공은 일절 하지 않는다. source summary 텍스트를 그대로 보존하여 reproducibility를 유지한다.

## Implementation Notes

- 향후 raids/items/systems generator도 같은 loader를 재사용하므로 인터페이스를 generator-agnostic하게 유지한다.
- fixture는 한국어/영어 patch note 양쪽 패턴을 포함한다.
- summary 파일이 frontmatter를 가질 수 있으므로 metadata block (YAML 또는 ad-hoc key:value) 파싱은 best-effort 수준으로 지원한다.

## Verification Results

- Red: `python -m unittest tests.test_v06_job_wiki_generator -v` failed with 7 expected `ModuleNotFoundError: No module named 'src.derived_wiki'` errors.
- Green: `python -m unittest tests.test_v06_job_wiki_generator -v` passed 7 tests after adding loader, writer, template helpers, and source summary fixtures.
- Regression: `python -m unittest tests.test_v06_pending_sources tests.test_v05_process_source tests.test_v06_extractors -v` passed 69 tests.
- Regression: `python -m py_compile src/derived_wiki/summary_loader.py src/derived_wiki/writer.py src/derived_wiki/templates.py src/derived_wiki/__init__.py` passed.
- Docs: `python scripts/check_docs_freshness.py --all` passed.
- Full suite: `python -m unittest discover -s tests -p "test_*.py"` passed 185 tests.
