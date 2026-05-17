# v0.8.5-04: Graph-Derived Wiki Generation

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 4)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

## Goal

domain graph에서 파생된 관리형 wiki 문서를 실제 생성한다.

## Scope

- dry-run 실행 및 결과 확인
- 실제 derived wiki 생성
- `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md` 확인
- generated page 내용 품질 확인
- `wiki/index.md` 갱신 확인
- idempotency 확인

Out of scope:

- 새 namespace 추가 (`types=jobs,patches,skills`만 다룸)
- graph rebuild (v08_5-02 책임)
- FTS 재색인 (v08_5-05 책임)

## Red Test

- File: `tests/test_v08_5_real_derived_wiki.py`
- Implementation target: 실제 derived wiki 생성 검증

Contracts fixed by the tests:

- graph fixture 기반으로 `generate_derived_wiki()` 실행 시 `wiki/jobs/gunbreaker.md`가 생성된다.
- `wiki/patches/7_5.md`가 생성된다.
- `wiki/skills/no_mercy.md`가 생성된다.
- generated page에 source id 또는 source path가 포함된다.
- `wiki/index.md`가 jobs/patches/skills 문서를 링크한다.
- 재실행해도 파일 내용이 변하지 않는다.

## Checklist

- [ ] red test 작성: `tests/test_v08_5_real_derived_wiki.py`
  - [ ] `test_generates_job_wiki`
  - [ ] `test_generates_patch_wiki`
  - [ ] `test_generates_skill_wiki`
  - [ ] `test_generated_page_includes_source`
  - [ ] `test_index_links_generated_pages`
  - [ ] `test_idempotent_generation`
- [ ] red 상태 확인
- [ ] dry-run 실행
  - [ ] `python tools/generate_derived_wiki.py --dry-run --verbose`
- [ ] 실제 생성
  - [ ] `python tools/generate_derived_wiki.py --verbose`
- [ ] 생성 결과 확인
  - [ ] `wiki/jobs/*.md` 최소 1개
  - [ ] `wiki/patches/*.md` 최소 1개
  - [ ] `wiki/skills/*.md` 최소 1개
- [ ] generated page 내용 확인
  - [ ] canonical entity name
  - [ ] entity type
  - [ ] related facts
  - [ ] related jobs / patches / skills
  - [ ] related sources
  - [ ] source summary path 또는 source id
  - [ ] generated marker 또는 provenance
- [ ] `wiki/index.md` 갱신 확인
- [ ] idempotency 확인: 재실행 후 파일 내용 비교
- [ ] 실패 시 원인 진단
  - [ ] graph에 Job/Patch/Skill node가 없는가?
  - [ ] graph relation이 source와 entity를 연결하지 못했는가?
  - [ ] derived wiki generator가 특정 edge type만 기대하는가?
  - [ ] `wiki_root` 또는 `graph_dir` 경로가 잘못되었는가?
- [ ] 최소 코드 수정으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/generate_derived_wiki.py --verbose
python -m unittest tests.test_v08_5_real_derived_wiki -v
```

생성 결과 확인:

```bash
find wiki/jobs -maxdepth 1 -type f -name "*.md" | sort | head -20
find wiki/patches -maxdepth 1 -type f -name "*.md" | sort | head -20
find wiki/skills -maxdepth 1 -type f -name "*.md" | sort | head -20
```

## Key Decisions

- 이 task에서 새 namespace를 추가하지 않는다. `types=jobs,patches,skills`만 다룬다.
- 기존 `tools/generate_derived_wiki.py`를 그대로 사용한다.
- 코드 수정은 최소화한다.

## Implementation Notes

- v08-08에서 이미 구현된 `tools/generate_derived_wiki.py`를 사용한다.
- 실제 데이터에서 파일이 생성되지 않으면 graph node/edge 상태를 먼저 점검한다.
- 테스트는 fixture 기반으로 격리한다.

## Agent Prompt

```text
v08.5 Task 4를 수행한다.
먼저 tests/test_v08_5_real_derived_wiki.py에 red test를 작성한다.
그 다음 tools/generate_derived_wiki.py를 실행하여 wiki/jobs, wiki/patches, wiki/skills를 생성한다.
dry-run → 실제 생성 → 결과 확인 → idempotency 확인 순서로 진행한다.
```
