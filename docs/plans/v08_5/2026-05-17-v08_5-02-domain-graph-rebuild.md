# v0.8.5-02: Actual Domain Graph Rebuild

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 2)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Completed 2026-05-17

## Goal

테스트 fixture가 아니라 실제 `wiki/source_summaries/`를 기준으로 domain graph를 채운다.

## Scope

- dry-run 실행 및 결과 확인
- 실제 reset rebuild 실행
- DB node/edge type count 확인
- graph export 파일 생성 확인
- idempotency 확인
- 실패 시 원인 진단 및 최소 코드 수정

Out of scope:

- source summary 수정 (v08_5-01 책임)
- graph report 생성 (v08_5-03 책임)
- derived wiki 생성 (v08_5-04 책임)
- 새 namespace 추가 (v08.5 non-goal)

## Red Test

- File: `tests/test_v08_5_real_graph_population.py`
- Implementation target: 실제 source summary 기반 graph population
- Expected red reason: v08.5 acceptance criteria에 맞는 assertion이 아직 없음.

Contracts fixed by the tests:

- `rebuild_domain_graph()` 실행 후 `graph_nodes`에 `Job`, `Patch`, `Skill`, `Fact`가 생긴다.
- `graph_edges`에 `MENTIONS`, `SUPPORTS`, `VALID_IN_PATCH`가 생긴다.
- `graph/domain_graph.json`과 `graph/entity_index.json`이 생긴다.
- 같은 rebuild를 두 번 실행해도 count가 증가하지 않는다.

Fixture source summary:

```text
# Fixture Patch Note

> Source: `local_v08_5_graph_population`

Patch 7.5 includes Gunbreaker adjustments. No Mercy duration was changed.
```

Expected entities:

- `job:gunbreaker`
- `patch:7_5`
- `skill:no_mercy`
- `fact:*`

## Checklist

- [x] red test 작성: `tests/test_v08_5_real_graph_population.py`
  - [x] `test_rebuild_creates_job_patch_skill_fact_nodes`
  - [x] `test_rebuild_creates_required_edge_types`
  - [x] `test_rebuild_creates_graph_export_files`
  - [x] `test_rebuild_idempotent`
- [x] red 상태 확인
- [x] dry-run 실행
  - [x] `python tools/rebuild_domain_graph.py --dry-run --verbose`
- [x] 실제 rebuild 실행
  - [x] `python tools/rebuild_domain_graph.py --reset-domain-graph --verbose`
- [x] DB 확인
  - [x] node type count 확인 (Job, Patch, Skill, Fact)
  - [x] edge type count 확인 (MENTIONS, SUPPORTS, VALID_IN_PATCH)
  - [x] AFFECTS_JOB, AFFECTS_SKILL이 0이면 사유 문서화
- [x] graph export 파일 확인
  - [x] `graph/nodes.json`
  - [x] `graph/edges.json`
  - [x] `graph/domain_graph.json`
  - [x] `graph/entity_index.json`
- [x] idempotency 확인: 반복 실행 후 count 비교
- [x] 실패 시 원인 진단
  - [x] source summary parser가 실제 포맷을 못 읽는가?
  - [x] `> Source: ...` 포맷이 문서마다 다른가?
  - [x] registry alias가 부족한가?
  - [x] relation trigger가 너무 보수적인가?
  - [x] graph reset이 provenance node까지 잘못 지우는가?
- [x] 최소 코드 수정으로 green 전환
- [x] handoff/README feature map status 갱신

결과:

- Red 확인: `tests.test_v08_5_real_graph_population` import error.
- 추가 regression: legacy `SOURCE_OF` confidence `EXTRACTED`가 export를 막지 않도록 고정.
- 실제 rebuild: `sources=26`, `facts=14`, DB nodes `78`, DB edges `339`.
- Required node types: `Job=5`, `Patch=3`, `Skill=4`, `Fact=14`.
- Required edge types: `MENTIONS=198`, `SUPPORTS=14`, `VALID_IN_PATCH=14`, `AFFECTS_JOB=59`, `AFFECTS_SKILL=4`.
- Idempotency: reset rebuild 반복 후 nodes `78`, edges `339` 유지.
- Generated graph JSON files are verified local outputs and remain ignored by Git because they are derived from local source summaries.

## Verification

```bash
python -m unittest tests.test_v08_5_real_graph_population -v
python tools/rebuild_domain_graph.py --dry-run --verbose
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
```

DB 확인:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('db/ffxiv.sqlite')
print('node types')
for row in conn.execute('SELECT type, COUNT(*) FROM graph_nodes GROUP BY type ORDER BY type'):
    print(row)
print('edge types')
for row in conn.execute('SELECT type, COUNT(*) FROM graph_edges GROUP BY type ORDER BY type'):
    print(row)
conn.close()
PY
```

Export 파일 확인:

```bash
ls -l graph/nodes.json graph/edges.json graph/domain_graph.json graph/entity_index.json
```

## Key Decisions

- 이 task에서 코드 수정은 최소화한다.
- 기존 `tools/rebuild_domain_graph.py`로 실제 데이터가 채워지지 않는 경우에만 진단 및 수정한다.
- 테스트는 fixture 기반으로 작성한다 (실제 repo 데이터에 의존하지 않음).

## Implementation Notes

- v08-05에서 이미 구현된 `tools/rebuild_domain_graph.py`를 그대로 사용한다.
- 실제 source summary에서 entity가 추출되지 않으면 registry alias 또는 relation trigger를 점검한다.
- `tempfile.TemporaryDirectory()` 기반 fixture를 사용하여 테스트를 격리한다.

## Agent Prompt

```text
v08.5 Task 2를 수행한다.
먼저 tests/test_v08_5_real_graph_population.py에 red test를 작성한다.
그 다음 tools/rebuild_domain_graph.py를 실제 source summaries에 대해 실행한다.
dry-run → reset rebuild → node/edge count 확인 → idempotency 확인 순서로 진행한다.
기존 코드 수정은 최소화한다.
```
