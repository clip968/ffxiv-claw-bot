# v0.8-03: Relation / Fact Extractor

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 3)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Pending

## Goal

추출된 entity와 source summary text를 기반으로 relation과 fact를 생성한다. Fact는 patch + job/skill + change trigger가 있을 때만 보수적으로 생성한다.

## Scope

필수 relation:

- `SourceDocument -> MENTIONS -> Entity`
- `WikiPage -> MENTIONS -> Entity`
- `Job -> HAS_SKILL -> Skill` (registry 기반)
- `SourceDocument -> SUPPORTS -> Fact`
- `Fact -> VALID_IN_PATCH -> Patch`
- `Fact -> AFFECTS_JOB -> Job`
- `Fact -> AFFECTS_SKILL -> Skill`

선택:

- `Entity -> RELATED_TO -> Entity` (co-occurrence, 낮은 confidence)

Out of scope:

- graph DB 저장 (v08-04 책임)
- BUFFED_IN / NERFED_IN 판단 (v08 non-goal)
- LLM-assisted extraction (v08 non-goal)

## Red Test

- File: `tests/test_relation_extractor.py`
- Implementation target: relation/fact extractor module
- Expected red reason: relation extractor 모듈이 존재하지 않아 `ImportError` 발생.

Contracts fixed by the tests:

- Job entity가 있으면 `SourceDocument -> MENTIONS -> Job` edge가 생성된다.
- Skill entity가 있으면 `SourceDocument -> MENTIONS -> Skill` edge가 생성된다.
- Patch entity가 있으면 `SourceDocument -> MENTIONS -> Patch` edge가 생성된다.
- registry에 skill.job이 있으면 `Job -> HAS_SKILL -> Skill` edge가 생성된다.
- patch + skill + trigger가 있으면 Fact node가 생성된다.
- trigger가 없으면 Fact node가 생성되지 않는다.
- Fact는 `SUPPORTS`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL` edge를 가진다.

## Checklist

- [ ] relation extractor 모듈 생성
  - [ ] `MENTIONS` relation 생성
  - [ ] `HAS_SKILL` relation 생성 (registry 기반)
  - [ ] change trigger 감지 (영어 + 한국어)
  - [ ] Fact node 생성 (patch + job/skill + trigger 조건)
  - [ ] `SUPPORTS` edge 생성
  - [ ] `VALID_IN_PATCH` edge 생성
  - [ ] `AFFECTS_JOB` edge 생성
  - [ ] `AFFECTS_SKILL` edge 생성
  - [ ] Fact id deterministic hash 생성
  - [ ] confidence 설정
- [ ] `tests/test_relation_extractor.py` 생성
  - [ ] `test_mentions_edge_for_job`
  - [ ] `test_mentions_edge_for_skill`
  - [ ] `test_mentions_edge_for_patch`
  - [ ] `test_has_skill_from_registry`
  - [ ] `test_fact_created_with_trigger`
  - [ ] `test_no_fact_without_trigger`
  - [ ] `test_fact_edges_complete`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_relation_extractor -v
```

## Key Decisions

- Fact 생성 조건: Patch entity + Job 또는 Skill entity + change trigger. 세 조건을 모두 만족해야 한다.
- 영어 trigger: changed, adjusted, potency, recast, duration, effect, added, removed, increased, decreased, now, no longer.
- 한국어 trigger: 변경, 조정, 위력, 재사용, 지속시간, 효과, 추가, 삭제, 증가, 감소, 이제, 더 이상.
- Fact id = hash(source_id + subject_node_id + relation + object_node_id + normalized_fact_text).
- Edge id = hash(source_node_id + relation_type + target_node_id + source_id).
- confidence: registry-derived = 1.0, exact alias mention = 0.9, rule-based fact = 0.75~0.9, co-occurrence = 0.4~0.6.

## Implementation Notes

- v08-01 entity registry와 v08-02 entity extractor에 의존한다.
- relation extractor는 entity extractor 결과를 입력으로 받는다.
- 출력은 relation list와 fact list로 분리한다.
- v08-04 graph storage helper가 이 출력을 DB에 저장한다.

## Agent Prompt

```text
v08 Task 3을 수행한다.
extracted entities를 기반으로 MENTIONS, HAS_SKILL, SUPPORTS, VALID_IN_PATCH, AFFECTS_JOB, AFFECTS_SKILL relation과 Fact node를 생성하는 extractor를 구현한다.
Fact는 patch + job/skill + change trigger가 있을 때만 생성한다.
먼저 tests/test_relation_extractor.py에 red tests를 작성한 뒤 구현한다.
```
