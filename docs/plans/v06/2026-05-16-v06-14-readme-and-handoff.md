# v0.6-14: README and Handoff Documentation

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-14)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Completed 2026-05-16

## Goal

v0.6 사용법을 문서화하고 다음 작업자가 같은 방식으로 진행할 수 있도록 README/handoff/runbook을 업데이트한다.

이 task는 runtime 코드 변경이 없는 문서 전용 task다.

## Scope

- `README.md` 또는 `docs/README.md` 갱신
- `docs/handoff/CURRENT_HANDOFF.md` 갱신
- v0.6 관련 runbook 추가/갱신
  - `docs/runbooks/process-source.md` (file source / 미지원 확장자 동작)
  - `docs/runbooks/process-pending-sources.md` (신규)
  - `docs/runbooks/generate-derived-wiki.md` (신규)
- v0.5/v05.1 문서와 충돌하지 않도록 확인

문서에 포함할 내용:

1. v0.6 목표
2. 지원 확장자 (`.txt`, `.md`, `.html`, `.htm`, `.csv`, `.xlsx`)
3. extractor 구조 (`src/source_processing/`, registry, extractors)
4. pending loop 실행법 (`tools/process_pending_sources.py`)
5. derived wiki generation 실행법 (`tools/generate_job_wiki.py`, `tools/generate_derived_wiki.py`)
6. FTS indexing 대상 (source_summaries + jobs)
7. known limitations (OCR/PDF/DOCX/LLM 미지원)
8. troubleshooting (미지원 확장자 error, derived wiki 실패 stage)

문서 예시 명령어:

```bash
python tools/process_pending_sources.py --limit 10 --dry-run
python tools/process_pending_sources.py --limit 10
python tools/generate_job_wiki.py --job gunbreaker
python tools/generate_derived_wiki.py --kind jobs
python tools/process_pending_sources.py --build-derived-wiki --limit 10
```

Out of scope:

- runtime 코드 변경
- 새 기능 추가
- spec 추가 (이미 SPEC 0006 존재)

## Red Test

No red test required. This is a documentation-only task.

규칙: `docs/plans/v06/README.md` Writing Rules에 따라 문서 변경 task는 red test 대신 변경 범위와 검증 기준을 명확히 적는다.

## Checklist

- [x] `README.md` 또는 `docs/README.md`에 v0.6 섹션 추가/갱신
  - [x] 지원 확장자
  - [x] extractor 구조
  - [x] CLI 사용법
  - [x] derived wiki 사용법
  - [x] known limitations
- [x] `docs/handoff/CURRENT_HANDOFF.md` 갱신
  - [x] v0.5/v05.1 완료 상태 유지
  - [x] v0.6 진행/완료 상태 반영
  - [x] 다음 작업자가 읽을 문서 목록
- [x] `docs/runbooks/process-source.md` 갱신
  - [x] file source extractor 동작 추가
  - [x] 미지원 확장자 처리
- [x] `docs/runbooks/process-pending-sources.md` 신규 작성
  - [x] CLI 옵션
  - [x] 상태 전이
  - [x] retry policy
  - [x] dry-run
- [x] `docs/runbooks/generate-derived-wiki.md` 신규 작성
  - [x] `generate_job_wiki.py` 사용법
  - [x] `generate_derived_wiki.py` 통합 CLI
  - [x] 출력 위치 (`wiki/jobs/*.md`)
- [x] `docs/plans/v06/README.md` feature map status를 모두 Completed로 갱신
- [x] 다음 명령으로 docs freshness 검증
  - [x] `python scripts/check_docs_freshness.py --all`
- [x] whitespace 검증
  - [x] v06-14 변경 파일 대상 `git diff --check`

## Verification

```bash
python scripts/check_docs_freshness.py --all
git diff --check
python -m unittest discover -s tests -p "test_*.py"
python scripts/finish_task.py
```

## Key Decisions

- README는 새 개발자가 README만 보고 v0.6 pipeline 전체를 실행할 수 있게 작성한다.
- runbook은 단계별 명령어와 expected output을 포함한다.
- v0.6에서 지원하지 않는 범위(OCR, PDF, DOCX, LLM 요약, scheduler/daemon)는 명시적으로 적어 사용자가 잘못된 기대를 갖지 않도록 한다.
- Notion spec과 repo 문서의 범위가 충돌하지 않는지 마지막으로 확인한다.

## Implementation Notes

- v06-01 ~ v06-13이 모두 완료된 뒤 마지막에 실행한다.
- 본 task에서는 runtime 코드를 수정하지 않는다. 만약 문서 작성 중 실제 동작과 어긋난 부분이 발견되면, 별도 follow-up task로 분리한다.
- handoff 문서에는 다음 마일스톤(v0.6.1 또는 v0.7)에서 다룰 PDF/OCR/DOCX/LLM 요약 등을 future work로 기재한다.

## Verification Results

- `python scripts/check_docs_freshness.py --all`: ok.
- v06-14 changed files path-scoped `git diff --check`: OK.
- `python scripts/finish_task.py`: finish_task ok.
  - Includes `python -m unittest discover -s tests -p "test_*.py"`: OK, 218 tests.
  - Includes docs freshness check: ok.
  - Includes Notion handoff dry-run: ok.

Note: the worktree still has pre-existing unstaged `.gitignore` and `AGENTS.md` edits outside v06-14 scope, so whitespace checking was scoped to v06-14 files.
