# Docs-First Agent Workflow

이 프로젝트의 문서 source of truth는 레포 내부 `docs/`다. Notion은 source of truth가 아니며 handoff 요약, 링크, 인덱스, OpenClaw 작업 상태를 남기는 control/status layer 역할만 한다.

## 기본 순서

큰 코드 변경은 다음 순서를 따른다.

```text
spec
-> ADR(if needed)
-> plan
-> failing tests
-> implementation
-> docs update
-> handoff update
-> python scripts/finish_task.py
-> optional Notion apply
```

작업 종료 흐름은 더 구체적으로 다음 순서다.

```text
implementation
-> tests
-> relevant docs/specs/runbooks update
-> docs/handoff/CURRENT_HANDOFF.md update
-> python scripts/finish_task.py
-> optional Notion apply
```

`finish_task.py`는 handoff 갱신 전에 실행하는 중간 점검이 아니라, handoff까지 포함한 작업 트리의 마지막 검증 게이트다.

## 작업 시작 체크

레포 루트에서 먼저 현재 상태를 확인한다.

```bash
git status --short
git branch --show-current
git log --oneline -5
git diff --stat
```

그 다음 최소한 다음 문서를 읽는다.

1. `docs/README.md`
2. `docs/WORKFLOW.md`
3. `docs/handoff/CURRENT_HANDOFF.md`
4. 변경 대상과 관련된 `docs/specs/`, `docs/runbooks/`, `docs/adrs/`

uncommitted 변경이 있으면 되돌리지 않는다. 현재 작업과 무관한 변경은 건드리지 않는다.

## Spec Contract

기능 구현은 spec 계약을 기준으로 한다. 관련 spec이 있으면 먼저 그 계약을 확인하고, 없으면 구현 전에 `docs/specs/`에 최소 계약을 만든다.

spec은 다음을 명확히 해야 한다.

- scope와 out of scope
- 입력, 출력, 저장 규칙
- 에러와 dry-run/apply 같은 모드별 동작
- requirement ID와 acceptance criteria
- 테스트 매핑

작은 documentation-only change는 새 spec 없이 진행할 수 있다. 행동이 바뀌는 코드 변경은 spec을 확인하거나 만든 뒤 진행한다.

## ADR 기준

ADR은 모든 변경에 필요하지 않다. 다음 중 하나에 해당하면 `docs/adrs/`에 작성한다.

- 되돌리기 어려운 기술 선택
- source of truth, 저장소, 외부 시스템 경계 변경
- 테스트/배포/운영 절차에 장기 영향을 주는 결정
- 여러 합리적 대안 중 하나를 선택한 이유를 남겨야 하는 경우

ADR은 spec을 대체하지 않는다. ADR은 왜 결정했는지를 기록하고, spec은 구현이 지켜야 할 계약을 기록한다.

## Plan 기준

비자명한 작업은 구현 전에 `docs/plans/`에 작은 실행 계획을 남긴다.

plan에는 관련 contract, 변경 파일, red test, implementation step, done when을 적는다. `docs/plans/`는 임시 작업 계획이며 장기 owner나 source of truth로 쓰지 않는다.

## TDD 규칙

행동이 바뀌는 코드 변경은 먼저 실패하는 테스트를 작성한다.

```text
failing tests -> implementation -> passing tests
```

테스트를 먼저 작성하지 못하는 경우 plan에 이유와 대체 검증 방법을 명시한다. 구현 후에 테스트를 붙이는 방식은 기본 workflow가 아니다.

현재 표준 테스트 명령은 unittest다.

```bash
python -m unittest discover -s tests -p "test_*.py"
```

pytest는 현재 표준이 아니다. 새로 도입하려면 별도 spec/plan에서 dependency와 실행 방식을 먼저 정한다.

## Docs Update 규칙

코드 변경 후에는 관련 문서 계약도 같은 작업 트리에 반영한다.

- behavior contract 변경: `docs/specs/`
- 반복 가능한 실행 절차 변경: `docs/runbooks/`
- 기술 결정 변경: `docs/adrs/`
- 다음 agent/session 상태 변경: `docs/handoff/CURRENT_HANDOFF.md`

`docs/archive/`는 현재 기준 실행 대상이 아니므로 owner 문서로 인정하지 않는다. Notion 문서나 외부 링크도 owner 문서가 아니다.

## Handoff 규칙

`docs/handoff/CURRENT_HANDOFF.md`는 모든 코드 변경의 전역 상태 문서다. 코드 변경이 있으면 handoff를 갱신한다.

handoff에는 다음 agent가 바로 판단할 수 있는 상태를 남긴다.

- 완료된 변경
- 관련 spec/runbook/ADR/plan
- 검증 명령과 결과
- 남은 TODO
- 건드리지 말아야 할 범위

단, handoff는 경로별 contract docs를 대체하지 못한다. handoff만 변경해서 code contract freshness를 만족시킬 수 없다.

## DOC_OWNERS 정책

`docs/DOC_OWNERS.yml`은 코드 변경이 어떤 문서 계약 아래 있는지 증명하는 정책 파일이다.

보장해야 하는 것:

1. Coverage: 변경된 코드 파일이 문서 계약 없이 존재하지 않는다.
2. Freshness: 코드 변경과 관련 문서 변경이 같은 작업 트리에 있다.
3. Traceability: 이 코드가 어떤 spec/runbook/ADR을 따르는지 추적 가능하다.

정책 요약:

- `code_paths`에 해당하고 `ignored_paths`가 아닌 코드 변경은 rule에 매칭되어야 한다.
- 매칭된 rule의 `contract_docs` 또는 `procedure_docs` 중 하나 이상이 변경되어야 한다.
- 코드 변경이 있으면 `global_required_on_code_change.changed`의 `docs/handoff/CURRENT_HANDOFF.md`도 변경되어야 한다.
- `docs/archive/**`, Notion 문서, 외부 링크는 owner로 인정하지 않는다.
- `docs/plans/**`는 장기 owner로 쓰지 않는다.
- `CURRENT_HANDOFF.md`만 바뀐 경우 contract freshness를 만족하지 않는다.
- `--allow-reviewed-docs`는 예외적 보조 옵션이며 기본 workflow와 `finish_task.py`는 이 옵션 없이 실행한다.

## 종료 검증

handoff를 갱신한 뒤 마지막에 실행한다.

```bash
python scripts/finish_task.py
```

`finish_task.py`는 다음을 실행한다.

1. `python -m unittest discover -s tests -p "test_*.py"`
2. `python scripts/check_docs_freshness.py --all`
3. `python scripts/sync_notion_handoff.py --dry-run`
4. `git status --short`
5. `git diff --stat`

Notion apply는 기본 종료 검증에 포함하지 않는다. 필요할 때만 maintainer가 명시적으로 요청하거나 승인한 뒤 실행한다.

## Git 규칙

AI agent는 maintainer가 명시적으로 요청하지 않는 한 commit 또는 push를 하지 않는다.

commit/push 요청이 있더라도 먼저 작업 트리 범위, 테스트 결과, 문서 갱신 상태를 확인한다. 사용자 변경이나 무관한 변경을 임의로 되돌리지 않는다.

## Notion 문서 이관 이후 운영 원칙

2026-05-14 기준으로 Notion에 있던 모든 프로젝트 문서를 repo `docs/`로 이관 완료했다.
앞으로 Notion은 더 이상 source of truth가 아니다.

새로운 문서는 다음 규칙을 따른다.

- **새 결정**: `docs/adrs/`에 ADR로 기록한다.
- **새 구현 계약**: `docs/specs/`에 spec으로 기록한다.
- **새 작업 계획**: `docs/plans/`에 plan으로 기록한다.
- **다음 세션 인계**: `docs/handoff/CURRENT_HANDOFF.md`에 기록한다.
- **반복 실행 절차**: `docs/runbooks/`에 runbook으로 기록한다.

Notion은 mirror/index와 OpenClaw 작업 상태판 역할만 한다. Notion에 문서를 작성해야 한다면 repo docs에 먼저 작성하고 Notion에 요약/링크를 추가한다.

OpenClaw가 Notion을 직접 갱신할 때도 원본 파일은 Notion에 업로드하지 않는다. Notion에는 `/mnt/d/ffixiv-bot-storage` local path, category, source_id, processing status, wiki path, graph status, last error만 기록한다.

Notion에만 있는 정보는 stale하다고 간주한다.
AI agent는 Notion 문서보다 repo `docs/`의 내용을 우선하여 따라야 한다.
