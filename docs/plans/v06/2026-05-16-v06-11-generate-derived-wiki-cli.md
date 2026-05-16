# v0.6-11: generate_derived_wiki.py Unified CLI

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-11)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

derived wiki generation을 통합 CLI(`tools/generate_derived_wiki.py`)에서 실행할 수 있게 한다.

v0.6에서는 `--kind jobs`만 동작하고, 향후 `raids`/`items`/`systems` 확장을 위한 placeholder만 둔다.

## Scope

- `tools/generate_derived_wiki.py` 구현
- `--kind jobs` 지원
- `--job <slug>` 단일 직업 생성
- `--job` 없으면 전체 직업 생성
- `--patch-range A..B` 적용
- `--dry-run` 지원
- unknown `--kind` 값에 대해 명확한 에러
- 후속 kind를 위한 unsupported error 메시지

CLI 계약:

```bash
python tools/generate_derived_wiki.py --kind jobs
python tools/generate_derived_wiki.py --kind jobs --job gunbreaker
python tools/generate_derived_wiki.py --kind jobs --patch-range 7.0..7.5
python tools/generate_derived_wiki.py --kind jobs --dry-run
python tools/generate_derived_wiki.py --kind raids   # error: not supported in v0.6
```

Out of scope:

- raids/items/systems 실제 구현
- FTS 통합 (v06-12)
- derived wiki hook (v06-13)

## Red Test

- File: `tests/test_v06_job_wiki_generator.py`
- Implementation target: `tools/generate_derived_wiki.py`
- Expected red reason: 통합 CLI script가 아직 없거나 unknown kind 에러 처리가 비어 있다.

Contracts fixed by the tests:

- `--kind jobs` 호출 시 job wiki generator (v06-10)가 호출된다.
- `--job` 인자가 v06-10 generator로 전달된다.
- `--patch-range` 인자가 v06-10 generator로 전달된다.
- `--dry-run`이 v06-10 generator의 dry_run으로 전달된다.
- unknown `--kind`는 명확한 stderr/exit code로 실패한다.
- CLI help가 사용 가능한 kind 목록을 보여준다.

## Checklist

- [x] `tools/generate_derived_wiki.py` 생성
- [x] argparse 옵션
  - [x] `--kind jobs` (required)
  - [x] `--job <slug>` (optional)
  - [x] `--patch-range A..B` (optional)
  - [x] `--dry-run`
  - [x] `--summary-root`
  - [x] `--target-root`
  - [x] `--include-limited` (optional)
- [x] `--kind jobs` 핸들러에서 v06-10 generator 호출
- [x] unknown/unsupported kind 처리
- [x] `tests/test_v06_job_wiki_generator.py`에 다음 테스트 추가
  - [x] `test_generate_derived_wiki_jobs_invokes_job_generator`
  - [x] `test_generate_derived_wiki_jobs_passes_job_filter`
  - [x] `test_generate_derived_wiki_jobs_passes_patch_range`
  - [x] `test_generate_derived_wiki_jobs_dry_run`
  - [x] `test_generate_derived_wiki_rejects_unknown_kind`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_job_wiki_generator -v
python tools/generate_derived_wiki.py --help
python tools/generate_derived_wiki.py --kind jobs --dry-run
```

## Key Decisions

- 통합 CLI는 thin wrapper로 시작한다. v06-10 generator의 함수를 직접 호출한다.
- unsupported kind는 명확한 종료 코드(예: 2)와 stderr 메시지로 실패시켜 자동화 스크립트가 감지할 수 있게 한다.
- 향후 raids/items/systems 추가 시 `--kind` choices를 확장한다. 본 task에서는 `jobs`만 정상 처리한다.
- pending loop (v06-07)이 본 CLI를 호출하지는 않는다. derived wiki hook은 v06-13에서 별도로 wiring한다.

## Implementation Notes

- v06-10이 완료된 뒤 진행해야 한다.
- argparse choices에는 `jobs`만 두고, `raids`/`items`/`systems`를 사용자가 입력하면 코드 분기에서 명시적으로 unsupported error를 낸다. (또는 choices에 전부 두고 핸들러에서 unsupported 분기 — 본 task에서 선택)
- `--help` 출력은 README/handoff 예시에 그대로 인용 가능한 수준으로 정리한다.

## Verification Results

- Red: `python -m unittest tests.test_v06_job_wiki_generator.V06GenerateDerivedWikiCliTests -v` failed with 4 expected missing `tools.generate_derived_wiki` errors and one file-missing subprocess error.
- Green: `python -m unittest tests.test_v06_job_wiki_generator.V06GenerateDerivedWikiCliTests -v` passed 5 tests after adding the unified `--kind jobs` wrapper and v0.6 unsupported-kind exit.
- Regression: `python -m unittest tests.test_v06_job_wiki_generator -v` passed 28 tests.
- CLI help: `python tools/generate_derived_wiki.py --help` completed successfully.
- CLI smoke: `python tools/generate_derived_wiki.py --kind jobs --dry-run --job gunbreaker --summary-root tests/fixtures/source_summaries --target-root /tmp/ffxiv-claw-bot-v06-derived-jobs` returned `status=ok`, `kind=jobs`, `generated=1`, `written=false`.
- Regression: `python -m py_compile tools/generate_derived_wiki.py` passed.
- Docs: `python scripts/check_docs_freshness.py --all` passed.
- Full suite: `python -m unittest discover -s tests -p "test_*.py"` passed 206 tests.
