# v0.8-02: Entity Extractor

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 2)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Completed 2026-05-17

## Goal

source summary 또는 wiki page text에서 FFXIV entity를 추출하는 rule-based entity extractor를 구현한다. 긴 alias 우선, 중복 제거, 영어 word boundary, 한국어 substring match를 처리한다.

## Scope

- rule-based entity extractor 구현
- 영어 alias: case-insensitive + word boundary match
- 한국어 alias: substring match + overlap 제거
- 긴 alias 우선 매칭
- 같은 canonical entity 중복 extraction 제거
- matched_alias, span, confidence 보존
- deterministic 정렬 (type priority → canonical name)

Out of scope:

- relation/fact extraction (v08-03 책임)
- LLM-assisted extraction (v08 non-goal)
- graph DB 저장 (v08-04 책임)

## Red Test

- File: `tests/test_entity_extractor.py`
- Implementation target: entity extractor module
- Expected red reason: entity extractor 함수가 존재하지 않아 `ImportError` 발생.

Contracts fixed by the tests:

- `"건브 7.5 변경점"`에서 `job:gunbreaker`, `patch:7_5`가 추출된다.
- `"GNB No Mercy"`에서 `job:gunbreaker`, `skill:no_mercy`가 추출된다.
- `"Gunbreaker Gunbreaker GNB"`에서 `job:gunbreaker`가 한 번만 나온다.
- `"No Mercy duration changed in Patch 7.5"`에서 skill과 patch가 추출된다.
- 짧은 alias가 다른 단어 내부에서 오탐되지 않는다.

## Checklist

- [x] entity extractor 모듈 생성
  - [x] registry alias를 긴 순서대로 검사
  - [x] 영어 alias: case-insensitive + word boundary
  - [x] 한국어 alias: substring match + overlap 제거
  - [x] 같은 canonical entity 중복 제거
  - [x] matched_alias, span, confidence 보존
  - [x] deterministic 정렬 (type priority: Patch, Job, Skill, Item, Encounter → canonical name)
- [ ] CLI wrapper 추가 (optional)
  - [ ] `--text` 옵션
  - [ ] `--source-id` 옵션
- [x] `tests/test_entity_extractor.py` 갱신
  - [x] `test_extract_korean_alias_and_patch`
  - [x] `test_extract_english_alias`
  - [x] `test_dedup_same_entity`
  - [x] `test_extract_skill_and_patch`
  - [x] `test_short_alias_no_false_positive`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환
- [x] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_entity_extractor -v
```

## Key Decisions

- 영어 약어(GNB, DRK 등)는 case-sensitive + word boundary로 처리한다.
- 한국어 alias는 word boundary가 없으므로 substring match를 사용하되 긴 alias 우선으로 overlap을 제거한다.
- 반환 결과의 정렬 순서: Patch → Job → Skill → Item → Encounter, 같은 type이면 canonical name 기준.
- confidence: exact alias match = 0.9, 약어 match = 0.85.

## Implementation Notes

- v08-01의 entity registry loader에 의존한다.
- extractor는 pure function으로 구현하여 테스트 가능해야 한다.
- 이 task는 `tools/ask.py`, `tools/search_kb.py`를 수정하지 않는다.
- v08-03 relation extractor가 이 extractor의 출력을 입력으로 사용한다.

## Agent Prompt

```text
v08 Task 2를 수행한다.
source summary text에서 FFXIV entity를 추출하는 rule-based entity extractor를 구현한다.
긴 alias 우선, 중복 제거, 영어 word boundary, 한국어 substring match를 처리한다.
먼저 red tests를 작성하고, 그 후 구현한다.
결과에는 node_id, type, canonical, matched_alias, confidence를 포함한다.
```
