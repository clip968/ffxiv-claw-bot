# v0.6-10: Job Wiki Generator

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-10)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

source summaries에서 직업 관련 내용을 deterministic하게 수집해 `wiki/jobs/<job>.md`를 생성한다.

v0.6은 LLM 요약을 사용하지 않는다. 직업 alias가 포함된 line/section을 patch_version 시간순으로 정리하고 source_id를 보존한다.

## Scope

- `src/derived_wiki/job_wiki_generator.py` 구현
- `tools/generate_job_wiki.py` CLI 구현
- 직업별 entry 수집: alias가 포함된 line 또는 section
- patch_version 기준 시간순 정렬
- 중복 entry 제거
- source_id와 patch_version 보존
- 근거 없는 내용은 생성하지 않음
- `wiki/jobs/<job>.md` 생성 (v06-08 writer 사용)

CLI 계약:

```bash
python tools/generate_job_wiki.py --all
python tools/generate_job_wiki.py --job gunbreaker
python tools/generate_job_wiki.py --job gunbreaker --patch-range 7.0..7.5
python tools/generate_job_wiki.py --dry-run
```

권장 출력 형식 (`wiki/jobs/gunbreaker.md`):

```markdown
# Gunbreaker 변경 이력

## 개요

이 문서는 source summaries를 기반으로 Gunbreaker 관련 변경 사항을 시간순으로 정리한다.

## 7.0

### 변경 사항
- 변경 사항 본문

### 출처
- source_id: patch_7_0

## 7.1

### 변경 사항
- 변경 사항 본문

### 출처
- source_id: patch_7_1

## 누적 요약

- v06에서는 근거 기반 bullet만 나열한다.
- 해석형 요약은 후속 버전에서 LLM summarizer로 확장한다.
```

Out of scope:

- generate_derived_wiki 통합 CLI (v06-11)
- FTS 통합 (v06-12)
- LLM 요약
- action-level 정밀 추출 (action catalog 필요, v0.7+)
- raids/items/systems generator

## Red Test

- File: `tests/test_v06_job_wiki_generator.py`
- Implementation target: `src/derived_wiki/job_wiki_generator.py`, `tools/generate_job_wiki.py`
- Expected red reason: generator module과 CLI가 아직 없거나, alias matching/정렬/중복 제거가 비어 있다.

Contracts fixed by the tests:

- 단일 직업 wiki 파일이 생성된다 (`wiki/jobs/gunbreaker.md`).
- 결과에 직업 display title이 들어간다.
- 결과에 해당 직업 alias가 포함된 patch summary entry만 들어간다.
- 결과에 patch_version과 source_id가 모두 포함된다.
- entry는 patch_version 오름차순으로 정렬된다.
- 중복 entry는 한 번만 나타난다.
- `--dry-run`은 파일을 쓰지 않는다.

## Checklist

- [x] `src/derived_wiki/job_wiki_generator.py` 구현
  - [x] `collect_job_entries(job: JobEntry, summaries: list[SourceSummary])`
  - [x] alias 기반 line/section matching
  - [x] patch_version 정렬
  - [x] 중복 제거 (정규화된 텍스트 hash)
  - [x] `render_job_wiki(job, entries) -> str`
  - [x] `generate_job_wiki(job, summaries, target_root, dry_run=False)`
- [x] `tools/generate_job_wiki.py` CLI 구현
  - [x] `--all`
  - [x] `--job <slug>`
  - [x] `--patch-range A..B`
  - [x] `--dry-run`
  - [x] `--summary-root` (default `wiki/source_summaries`)
  - [x] `--target-root` (default `wiki/jobs`)
- [x] 의존성: v06-08 summary_loader/writer, v06-09 job_catalog
- [x] `tests/test_v06_job_wiki_generator.py`에 다음 테스트 추가
  - [x] `test_generate_single_job_wiki_creates_file`
  - [x] `test_generate_job_wiki_includes_job_title`
  - [x] `test_generate_job_wiki_includes_matching_patch_entries`
  - [x] `test_generate_job_wiki_preserves_source_id`
  - [x] `test_generate_job_wiki_sorts_entries_by_patch_version`
  - [x] `test_generate_job_wiki_deduplicates_duplicate_entries`
  - [x] `test_generate_job_wiki_dry_run_does_not_write_file`
  - [x] `test_generate_job_wiki_patch_range_filter`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_job_wiki_generator -v
python tools/generate_job_wiki.py --dry-run --job gunbreaker
```

## Key Decisions

- v0.6 1차 구현은 LLM 없이 deterministic line/section 수집만 한다.
- 매칭 단위는 line 우선, 필요 시 surrounding section heading까지 함께 포함한다.
- alias matching은 word boundary 기준으로 false positive를 최소화한다 (예: `BLM` 토큰이 단어 단위로 나타날 때만 매칭).
- patch_range filter는 단순 string comparison으로 시작하며, 정확한 semantic version 비교는 후속에서 보강한다.
- 생성된 wiki에는 항상 출처(`source_id`)를 보존해 reproducibility를 유지한다.

## Implementation Notes

- v06-08 summary_loader, v06-09 job_catalog, v06-02 registry와 함께 본 task가 derived wiki layer의 핵심이다.
- 매칭되는 entry가 없으면 빈 wiki를 쓰지 않고 stdout warning만 출력한다 (정책: 빈 결과는 파일 생성하지 않음).
- `--all` 실행 시 limited job 포함 여부는 v06-09의 `list_jobs(include_limited=...)`를 따른다. CLI 옵션으로 `--include-limited`를 추가할지 본 task에서 결정한다.

## Verification Results

- Red: `python -m unittest tests.test_v06_job_wiki_generator.V06JobWikiGeneratorTests -v` failed with 9 expected missing module errors for `src.derived_wiki.job_wiki_generator` and `tools.generate_job_wiki`.
- Green: `python -m unittest tests.test_v06_job_wiki_generator.V06JobWikiGeneratorTests -v` passed 9 tests after adding deterministic section/line matching, rendering, writing, dry-run, patch-range filtering, and the job CLI.
- Regression: `python -m unittest tests.test_v06_job_wiki_generator -v` passed 23 tests.
- CLI smoke: `python tools/generate_job_wiki.py --dry-run --job gunbreaker --summary-root tests/fixtures/source_summaries --target-root /tmp/ffxiv-claw-bot-v06-jobs` returned `status=ok`, `generated=1`, `written=false`.
- Regression: `python -m py_compile src/derived_wiki/job_wiki_generator.py tools/generate_job_wiki.py src/derived_wiki/__init__.py` passed.
- Docs: `python scripts/check_docs_freshness.py --all` passed.
- Full suite: `python -m unittest discover -s tests -p "test_*.py"` passed 201 tests.
