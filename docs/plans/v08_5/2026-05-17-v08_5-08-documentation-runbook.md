# v0.8.5-08: Documentation and Runbook Update

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 8)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

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

- [ ] `docs/runbooks/domain-graph-refresh.md` 추가
  - [ ] Purpose
  - [ ] Preconditions
  - [ ] Step 1. Source summary audit
  - [ ] Step 2. Dry-run rebuild
  - [ ] Step 3. Reset rebuild
  - [ ] Step 4. Graph report
  - [ ] Step 5. Derived wiki generation
  - [ ] Step 6. FTS re-index
  - [ ] Step 7. Ask smoke tests
  - [ ] Step 8. Regression
  - [ ] Troubleshooting
  - [ ] Completion checklist
- [ ] `README.md` 갱신
  - [ ] Current Pipeline을 v08.5 기준으로 갱신
  - [ ] v0.6 중심 설명을 history/legacy로 이동
  - [ ] Common Commands에 v08.5 명령 추가
- [ ] `docs/specs/README.md` 갱신
  - [ ] v08 spec 반영
  - [ ] v08.5 spec 반영
- [ ] `docs/runbooks/ask.md` 갱신
  - [ ] graph-aware retrieval 설명
  - [ ] `graph/entity_index.json` 없으면 FTS fallback
  - [ ] 대표 smoke query 추가
  - [ ] JSON output 확인 방법 설명
- [ ] `docs/runbooks/generate-derived-wiki.md` 갱신
  - [ ] legacy `--kind jobs`와 v08 graph-derived wiki mode 분리
  - [ ] `--dry-run --verbose` 선행 권장
  - [ ] generation 후 FTS re-index 필요성 명시
- [ ] `docs/handoff/CURRENT_HANDOFF.md` 갱신
  - [ ] Current phase: v08.5 completed
  - [ ] Last completed task
  - [ ] Next task
  - [ ] 검증 명령과 결과
  - [ ] 아직 하지 말 것
- [ ] docs freshness 확인
  - [ ] `python scripts/check_docs_freshness.py --all`
- [ ] handoff/README feature map status 갱신

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
