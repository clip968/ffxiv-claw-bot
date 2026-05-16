# v0.6-13: Derived Wiki Hook after Source Processing

## Spec

- Master plan: `docs/plans/v06/README.md`
- Implementation source plan: `docs/plans/2026-05-16-v06-implementation-plan.md` (Task v06-13)
- Pipeline spec: `docs/specs/0005- v06-Multi-format-Source-Processing.md`

## Status

Pending

## Goal

source processing 성공 후 derived wiki generation을 선택적으로 실행할 수 있도록 hook을 연결한다.

기본값은 안전하게 **skip**이며, `process_source.py` 단독 실행에서는 derived wiki를 생성하지 않는다. `process_pending_sources.py`에 `--build-derived-wiki` 옵션을 제공한다.

## Scope

- `tools/process_source.py`에 다음 옵션 중 하나 추가
  - `--build-derived-wiki`
  - `--skip-derived-wiki` (default)
- `tools/process_pending_sources.py`에 `--build-derived-wiki` 옵션 추가
- hook 호출: `tools/generate_derived_wiki.py --kind jobs` (또는 v06-10/v06-11 함수 직접 호출)
- 상태 기록
  - 성공: `derived_wiki_built`
  - 실패: `error_stage=derived_wiki_generate`, `error_message=...`
- source processing 자체 성공 / derived wiki 실패 분리
- 기존 process_source/pending loop 동작 회귀 보호

권장 정책:

| Entrypoint | 기본 동작 | 옵션으로 변경 |
|---|---|---|
| `process_source.py` 단독 | skip | `--build-derived-wiki`로 옵트인 |
| `process_pending_sources.py` | skip | `--build-derived-wiki`로 옵트인 |

Out of scope:

- LLM 요약
- raids/items/systems generator (v0.7+)
- scheduler/daemon

## Red Test

- File: `tests/test_v06_pending_sources.py` (또는 v06-13 전용 test)
- Implementation target: `tools/process_source.py`, `tools/process_pending_sources.py`
- Expected red reason: derived wiki hook이 없거나, 실패 stage가 source processing 실패와 구분되지 않는다.

Contracts fixed by the tests:

- 기본값에서는 derived wiki가 생성되지 않는다.
- `--build-derived-wiki` 옵션이 있으면 derived wiki generator가 호출된다.
- derived wiki 생성 성공 시 source 상태에 `derived_wiki_built`가 기록된다.
- derived wiki 생성 실패 시 `error_stage=derived_wiki_generate`로 분리되어 기록된다.
- derived wiki 실패가 source processing 자체의 성공/실패 판정을 바꾸지 않는다.

## Checklist

- [ ] `tools/process_source.py`에 `--build-derived-wiki` / `--skip-derived-wiki` 옵션 추가
- [ ] `tools/process_pending_sources.py`에 `--build-derived-wiki` 옵션 추가
- [ ] hook 호출 wiring (v06-10/v06-11 함수 import)
- [ ] derived wiki 결과를 result JSON에 분리해서 기록
  - [ ] `derived_wiki` block: `status`, `targets`, `error_stage`, `error_message`
- [ ] DB status 갱신
  - [ ] 성공: `derived_wiki_built`
  - [ ] 실패: `error_stage=derived_wiki_generate`, `error_message`
- [ ] source processing 성공/실패와 derived wiki 성공/실패 분리
- [ ] 기존 회귀 보호
  - [ ] derived wiki 옵션 없으면 기존 process_source.py / pending loop 동작과 동일
- [ ] `tests/test_v06_pending_sources.py`에 다음 테스트 추가
  - [ ] `test_process_pending_sources_can_build_derived_wiki_when_enabled`
  - [ ] `test_process_pending_sources_skips_derived_wiki_by_default`
  - [ ] `test_derived_wiki_failure_records_derived_wiki_stage`
  - [ ] `test_derived_wiki_failure_does_not_mark_source_as_failed`
- [ ] red 상태 확인
- [ ] 최소 구현으로 green 전환

## Verification

```bash
python -m unittest tests.test_v06_pending_sources -v
python -m unittest tests.test_v05_process_source -v
python -m unittest discover -s tests -p "test_*.py"
```

smoke (선택):

```bash
python tools/process_pending_sources.py --dry-run --limit 3
python tools/process_pending_sources.py --build-derived-wiki --limit 3 --dry-run
```

## Key Decisions

- v0.6 기본값은 derived wiki 생성을 **skip**한다. derived wiki 생성은 비교적 비싸고 실험적이므로 명시적 opt-in을 요구한다.
- derived wiki 실패는 source processing 실패와 다른 stage로 보고한다. Notion status mapping에서도 별도 stage로 노출한다.
- hook은 v06-11 통합 CLI 함수 (`generate_derived_wiki` main)에 의존한다. subprocess 호출 대신 함수 직접 import를 권장한다.
- derived wiki hook이 동작해도 한 source 처리당 한 번만 호출되도록 한다. 여러 source 처리 후 batch로 한 번 부르고 싶으면 별도 task로 분리한다 (본 task에서는 per-source hook).

## Implementation Notes

- v06-07 pending loop와 v06-11 통합 CLI가 완료된 뒤 진행해야 한다.
- 본 task가 v0.6 마지막 functional task다. v06-14는 문서 전용.
- Notion update payload schema 변경이 필요한 경우 v0.5 boundary(`process_source.py`는 payload-only)를 깨지 않도록 주의한다.

## Verification Results

- Pending.
