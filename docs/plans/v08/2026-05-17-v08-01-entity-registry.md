# v0.8-01: Entity Registry

## Spec

- Master plan: `docs/plans/v08/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08-implementation.md` (Task 1)
- Graphify layer spec: `docs/specs/0008-v08-ffxiv-domain-graphify-layer-spec.md`

## Status

Completed 2026-05-17

## Goal

FFXIV 도메인 entity를 canonical node id로 정규화할 수 있는 registry를 추가한다. alias normalization을 통해 `Gunbreaker`, `GNB`, `건브`, `건브레이커`가 모두 `job:gunbreaker`로 매핑되어야 한다.

## Scope

- `data/ffxiv_entities/` 디렉터리 추가
- `jobs.json`, `skills.json`, `patches.json` 추가
- entity registry loader 구현
- alias → canonical node id 매핑
- 긴 alias 우선 정렬
- 중복 alias 감지 및 warning

Out of scope:

- entity extraction (v08-02 책임)
- relation/fact extraction (v08-03 책임)
- items.json, encounters.json (v08 optional, 필요 시 추가)
- LLM 기반 extraction (v08 non-goal)

## Red Test

- File: `tests/test_entity_extractor.py`
- Implementation target: `data/ffxiv_entities/*.json`, entity registry loader
- Expected red reason: entity registry loader 모듈이 존재하지 않아 `ModuleNotFoundError` 발생.

Contracts fixed by the tests:

- `Gunbreaker`가 `job:gunbreaker`로 정규화된다.
- `GNB`가 `job:gunbreaker`로 정규화된다.
- `건브`가 `job:gunbreaker`로 정규화된다.
- `건브레이커`가 `job:gunbreaker`로 정규화된다.
- `No Mercy`가 `skill:no_mercy`로 정규화된다.
- `7.5`, `Patch 7.5`, `패치 7.5`가 `patch:7_5`로 정규화된다.
- 같은 alias가 두 entity에 중복 등록되면 warning 또는 error를 낸다.

## Checklist

- [x] `data/ffxiv_entities/jobs.json` 생성
- [x] `data/ffxiv_entities/skills.json` 생성
- [x] `data/ffxiv_entities/patches.json` 생성
- [x] entity registry loader 구현
  - [x] 모든 registry JSON 로드
  - [x] alias → canonical entity 매핑
  - [x] canonical entity → node id 변환
  - [x] node id → entity metadata 조회
  - [x] 긴 alias 우선 정렬
  - [x] 중복 alias 감지
  - [x] ambiguity warning 생성
- [x] `tests/test_entity_extractor.py` 생성 (registry 관련 red tests)
  - [x] `test_job_alias_to_canonical_node_id`
  - [x] `test_skill_alias_to_canonical_node_id`
  - [x] `test_patch_alias_to_canonical_node_id`
  - [x] `test_duplicate_alias_warning`
- [x] red 상태 확인
- [x] 최소 구현으로 green 전환
- [x] handoff/README feature map status 갱신

## Verification

```bash
python -m unittest tests.test_entity_extractor -v
```

## Key Decisions

- Registry JSON은 `data/ffxiv_entities/` 하위에 type별 파일로 관리한다.
- Node id 규칙: `job:<slug>`, `patch:<slug>`, `skill:<slug>`.
- 예: `job:gunbreaker`, `patch:7_5`, `skill:no_mercy`.
- alias는 대소문자 무시로 매핑하되, 짧은 영어 약어는 case-sensitive option을 둔다.
- registry loader는 외부 의존성 없이 표준 라이브러리만 사용한다.

## Implementation Notes

- repo가 아직 패키지 구조를 갖추지 않았다면 `tools/` 하위에 loader를 둬도 된다.
- 패키지 구조가 있다면 `src/ffxiv_bot/graph/entity_registry.py` 권장.
- 이 task는 기존 `tools/ask.py`, `tools/search_kb.py`, `tools/answer.py`를 수정하지 않는다.
- v08-02 entity extractor가 이 registry를 입력으로 사용한다.

## Agent Prompt

```text
v08 Task 1을 수행한다.
`data/ffxiv_entities/`에 jobs.json, skills.json, patches.json을 추가하고 entity registry loader를 구현한다.
먼저 tests/test_entity_extractor.py에 alias normalization red tests를 작성한다.
Gunbreaker/GNB/건브/건브레이커, No Mercy, Patch 7.5 alias가 canonical node id로 정규화되어야 한다.
구현 후 해당 테스트를 통과시킨다.
기존 기능은 수정하지 않는다.
```
