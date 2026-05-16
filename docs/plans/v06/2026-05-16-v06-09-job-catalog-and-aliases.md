# v0.6-09: Job Catalog and Aliases

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-9)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Pending

## Goal

FFXIV 직업별 derived wiki 생성을 위한 canonical job slug list와 alias resolver를 정의한다.

이 task는 데이터/lookup만 책임지며, 실제 wiki 문서 생성은 v06-10이 담당한다.

## Scope

- `src/derived_wiki/job_catalog.py` 추가
- canonical job slug 목록 정의
- display name 정의
- 한국어/영어/약어 alias 정의
- `resolve_job(query: str) -> JobEntry | None` 구현
- `list_jobs(include_limited: bool = False) -> list[JobEntry]` 구현
- Blue Mage는 limited job이므로 `include_limited` 옵션으로 제어

권장 canonical slug:

```text
paladin, warrior, dark_knight, gunbreaker,
white_mage, scholar, astrologian, sage,
monk, dragoon, ninja, samurai, reaper, viper,
bard, machinist, dancer,
black_mage, summoner, red_mage, pictomancer,
blue_mage
```

권장 alias 예시:

```text
gunbreaker: Gunbreaker, GNB, 건브레이커
black_mage: Black Mage, BLM, 흑마도사, 흑마
paladin: Paladin, PLD, 나이트
```

Out of scope:

- job wiki generator (v06-10)
- generate_derived_wiki CLI (v06-11)
- action catalog (v0.7+)
- 직업 외 주제 catalog (raids/items/systems)

## Red Test

- File: `tests/test_v06_job_wiki_generator.py`
- Implementation target: `src/derived_wiki/job_catalog.py`
- Expected red reason: job_catalog module이 아직 없거나 alias resolver가 비어 있다.

Contracts fixed by the tests:

- 모든 전투 직업의 canonical slug가 catalog에 존재한다.
- 영어 alias(`Gunbreaker`, `GNB`)로 canonical job slug를 찾을 수 있다.
- 약어 alias(`BLM`, `PLD`)로 canonical job slug를 찾을 수 있다.
- 한국어 alias(`건브레이커`, `흑마도사`, `나이트`)로 canonical job slug를 찾을 수 있다.
- `include_limited=False`이면 `blue_mage`가 list 결과에서 제외된다.
- `include_limited=True`이면 `blue_mage`가 포함된다.

## Checklist

- [ ] `src/derived_wiki/job_catalog.py` 생성
  - [ ] `JobEntry(slug, display_name, aliases, is_limited)`
  - [ ] `JOB_CATALOG: list[JobEntry]`
  - [ ] `resolve_job(query: str) -> JobEntry | None`
  - [ ] `list_jobs(include_limited: bool = False) -> list[JobEntry]`
  - [ ] case-insensitive alias matching
- [ ] 모든 전투 직업 entry 작성 (canonical slug 목록 참고)
- [ ] alias 한국어/영어/약어 포함
- [ ] Blue Mage `is_limited=True`
- [ ] `tests/test_v06_job_wiki_generator.py`에 다음 테스트 추가
  - [ ] `test_job_catalog_contains_gunbreaker`
  - [ ] `test_job_catalog_contains_all_combat_jobs`
  - [ ] `test_job_catalog_resolves_english_alias`
  - [ ] `test_job_catalog_resolves_abbreviation_alias`
  - [ ] `test_job_catalog_resolves_korean_alias`
  - [ ] `test_job_catalog_can_exclude_limited_jobs`
  - [ ] `test_job_catalog_can_include_limited_jobs`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_job_wiki_generator -v
python -m py_compile src/derived_wiki/job_catalog.py
```

## Key Decisions

- alias matching은 `query.strip().lower()` 기준 set lookup으로 단순하게 구현한다.
- alias 충돌은 명시적 단위 테스트로 방지한다 (예: 동일 별칭이 두 직업에 매핑되면 catalog 정의 시점에 에러).
- Limited job은 Blue Mage만 우선 포함한다. 향후 Beastmaster 등은 spec/plan 갱신 후 추가한다.
- 한국어 alias는 일반적인 community 표기를 우선한다 (`흑마`, `백마`, `학사`, `점성`, `현자`, `용기사`, `사무라이` 등).

## Implementation Notes

- catalog는 Python 상수로 정의해 import 비용을 최소화한다.
- v06-10 job wiki generator가 이 catalog를 import하므로 인터페이스가 안정적이어야 한다.
- 디스플레이 이름은 한/영 모두 합리적인 한 가지를 선택한다. 기본 표기는 영어(`Gunbreaker`)로 두고 별도 `display_name_ko`를 추가할지는 v06-10 진행 시 판단한다.

## Verification Results

- Pending.
