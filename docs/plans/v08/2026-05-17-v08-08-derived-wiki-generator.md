# v0.8-08: Derived Wiki Generator

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 8)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Completed 2026-05-17

## Goal

domain graph를 기반으로 derived wiki를 생성한다. `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md`를 생성하고, 각 문서에 related sources와 graph links를 포함한다. `wiki/index.md`에 derived wiki 링크 섹션을 추가 또는 갱신한다.

## Scope

- `tools/generate_derived_wiki.py` CLI 생성
- `wiki/jobs/*.md` 생성 (Summary, Related Patches, Skills, Recent Facts, Related Sources, Graph Links)
- `wiki/patches/*.md` 생성 (Summary, Affected Jobs, Affected Skills, Facts, Related Sources)
- `wiki/skills/*.md` 생성 (Summary, Job, Related Patches, Facts, Related Sources)
- `wiki/index.md` 갱신
- idempotent 생성
- deterministic 정렬

Out of scope:

- graph export/report (v08-06, v08-07 책임)
- hybrid retrieval (v08-09 책임)
- BIS/opener/rotation derived wiki (v08 non-goal)

## Red Test

- File: `tests/test_derived_wiki.py`
- Implementation target: `tools/generate_derived_wiki.py`, derived wiki generator module
- Expected red reason: generator 모듈이 존재하지 않아 `ImportError` 발생.

Contracts fixed by the tests:

- `wiki/jobs/gunbreaker.md`가 생성된다.
- job wiki에 related skills가 포함된다.
- job wiki에 related patches가 포함된다.
- job wiki에 related sources가 포함된다.
- `wiki/patches/7_5.md`가 생성된다.
- `wiki/skills/no_mercy.md`가 생성된다.
- `wiki/index.md`가 갱신된다.
- 같은 입력으로 두 번 실행해도 결과가 안정적이다.

## Checklist

- [x] `tools/generate_derived_wiki.py` 생성
  - [x] argparse CLI (--db-path, --wiki-root, --graph-dir, --types, --dry-run, --verbose)
- [x] derived wiki generator 모듈 생성
  - [x] Job wiki 생성 (Summary, Related Patches, Skills, Recent Facts, Related Sources, Graph Links)
  - [x] Patch wiki 생성 (Summary, Affected Jobs, Affected Skills, Facts, Related Sources)
  - [x] Skill wiki 생성 (Summary, Job, Related Patches, Facts, Related Sources)
  - [x] wiki/index.md 갱신 (Derived Wiki 섹션 추가/갱신)
  - [x] deterministic 정렬 (canonical name 기준)
  - [x] source linking 포함 (source_id, title, path 중 최소 하나)
- [x] `tests/test_derived_wiki.py` 생성
  - [x] `test_job_wiki_created`
  - [x] `test_job_wiki_has_skills`
  - [x] `test_job_wiki_has_patches`
  - [x] `test_job_wiki_has_sources`
  - [x] `test_patch_wiki_created`
  - [x] `test_skill_wiki_created`
  - [x] `test_index_md_updated`
  - [x] `test_idempotent_generation`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환
- [x] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_derived_wiki -v
python tools/generate_derived_wiki.py --dry-run --verbose
```

## Key Decisions

- Derived wiki는 source summary를 대체하지 않는다. source summary와 별도로 존재한다.
- 각 derived wiki에는 최소 related sources(source_id)를 포함해야 한다.
- Markdown 생성 시 정렬: Job = canonical name, Patch = version, Skill = canonical name, Source = source_id, Fact = fact text.
- wiki/index.md의 Derived Wiki 섹션은 기존 내용을 보존하면서 추가/갱신한다.

## Implementation Notes

- v08-04 graph storage helper와 v08-05 rebuild 결과에 의존한다.
- 테스트는 fixture graph data와 tmp wiki 디렉터리를 사용한다.
- 사용자가 직접 읽을 수 있는 품질의 Markdown을 생성한다.

## Agent Prompt

```text
v08 Task 8을 수행한다.
graph 기반 derived wiki generator를 구현한다.
`wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md`를 생성하고, 각 문서에 related sources와 graph links를 포함한다.
`wiki/index.md`에 derived wiki 링크 섹션을 추가 또는 갱신한다.
같은 입력으로 두 번 실행해도 결과가 안정적이어야 한다.
```
