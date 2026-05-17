# v0.8.5-08: Documentation and Runbook Update

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 8)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Completed 2026-05-17

## Goal

v08.5 graph/wiki refresh workflow를 다음 세션이나 다른 agent가 재현할 수 있게 문서화한다.

## Scope

- `docs/runbooks/domain-graph-refresh.md` 추가
- `README.md` 갱신 (현재 pipeline 반영)
- `docs/specs/README.md` 갱신 (v08/v08.5 spec 반영)
- `docs/runbooks/ask.md` 갱신
- `docs/runbooks/generate-derived-wiki.md` 갱신
- `docs/handoff/CURRENT_HANDOFF.md` 갱신
- `docs/plans/v08_5/README.md` 갱신

Out of scope:

- 코드 수정
- 새 기능 추가

## Red Test

이 task는 문서 전용이므로 별도 red test가 필요하지 않다. `scripts/check_docs_freshness.py --all`로 freshness를 검증한다.

## Checklist

- [x] `docs/runbooks/domain-graph-refresh.md` 추가
  - [x] Purpose
  - [x] Preconditions
  - [x] Step 1. Source summary audit
  - [x] Step 2. Dry-run rebuild
  - [x] Step 3. Reset rebuild
  - [x] Step 4. Graph report
  - [x] Step 5. Derived wiki generation
  - [x] Step 6. FTS re-index
  - [x] Step 7. Ask smoke tests
  - [x] Step 8. Regression
  - [x] Troubleshooting
  - [x] Completion checklist
- [x] `README.md` 갱신
  - [x] Current Pipeline을 v08.5 기준으로 갱신
  - [x] v0.6 중심 설명을 history/legacy로 이동
  - [x] Common Commands에 v08.5 명령 추가
- [x] `docs/specs/README.md` 갱신
  - [x] v08 spec 반영
  - [x] v08.5 spec 반영
- [x] `docs/runbooks/ask.md` 갱신
  - [x] graph-aware retrieval 설명
  - [x] `graph/entity_index.json` 없으면 FTS fallback
  - [x] 대표 smoke query 추가
  - [x] JSON output 확인 방법 설명
- [x] `docs/runbooks/generate-derived-wiki.md` 갱신
  - [x] legacy `--kind jobs`와 v08 graph-derived wiki mode 분리
  - [x] `--dry-run --verbose` 선행 권장
  - [x] generation 후 FTS re-index 필요성 명시
- [x] `docs/handoff/CURRENT_HANDOFF.md` 갱신
  - [x] Current phase는 final verification 전까지 in progress로 유지
  - [x] Last completed task
  - [x] Next task
  - [x] 검증 명령과 결과
  - [x] 아직 하지 말 것
- [x] docs freshness 확인
  - [x] `python scripts/check_docs_freshness.py --all`
- [x] handoff/README feature map status 갱신

## Results

- `docs/runbooks/domain-graph-refresh.md`를 추가해 v08.5 refresh 절차를 source audit부터 regression까지 한 문서로 정리했다.
- `README.md` Current Pipeline을 v08.5 기준으로 갱신하고 v0.6 source processing은 legacy pipeline로 분리했다.
- `docs/specs/README.md`에 v05/v05.1/v06/v07/v08/v08.5 spec을 현재 spec 목록으로 반영했다.
- `docs/runbooks/ask.md`에 graph-aware fallback, v08.5 smoke query, JSON 확인 기준을 추가했다.
- `docs/runbooks/generate-derived-wiki.md`에 v08 graph-derived mode와 legacy `--kind jobs` mode를 분리하고 FTS re-index 필요성을 명시했다.
- `docs/runbooks/README.md`에 새 runbook과 ask runbook을 등록했다.
- `CURRENT_HANDOFF.md`는 v08.5-08 완료 및 v08.5-09 final verification 대기 상태로 갱신했다.

## Verification

```bash
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- README가 v0.6 중심으로만 보이지 않도록 현재 pipeline을 갱신한다.
- specs README에 v08/v08.5가 현재 spec으로 반영된다.
- domain graph refresh 절차가 한 runbook에서 재현 가능해야 한다.
- handoff가 다음 agent의 첫 진입점 역할을 한다.

## Implementation Notes

- 실제 명령 결과를 본 뒤 문서를 작성한다.
- 문서 구조는 implementation plan의 Task 8 참조.
- freshness check가 실패하면 해당 문서를 갱신한다.

## Agent Prompt

```text
v08.5 Task 8을 수행한다.
docs/runbooks/domain-graph-refresh.md를 추가한다.
README.md, docs/specs/README.md, docs/runbooks/ask.md, docs/runbooks/generate-derived-wiki.md를 갱신한다.
docs/handoff/CURRENT_HANDOFF.md를 v08.5 완료 상태로 갱신한다.
docs freshness check를 통과시킨다.
```
