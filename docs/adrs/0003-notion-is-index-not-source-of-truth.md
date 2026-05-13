# ADR 0003: Notion Is Index, Not Source of Truth

## Status

Accepted

## Context

초기 작업에서는 Notion이 handoff와 decision summary 역할을 했다. 하지만 구현 기준이 Notion에만 있으면 코드 변경과 spec 변경이 같은 Git 히스토리에 남지 않는다.

Notion에 전체 작업 트리나 산출물을 복제하면 금방 stale해지고, AI agent가 따라야 할 기준이 분산된다.

## Decision

Notion은 프로젝트 인덱스와 handoff 요약으로만 사용한다.

구현 기준은 레포의 `docs/specs/*.md`다.

## Consequences

좋은 영향:

- spec과 코드 변경을 같은 Git 커밋으로 관리할 수 있다.
- AI agent가 따라야 할 기준이 레포 내부에 있다.
- Notion에는 요약과 링크만 두므로 stale surface가 줄어든다.

트레이드오프:

- Notion handoff를 갱신할 때 레포 docs 링크와 요약을 함께 관리해야 한다.
- 긴 설명은 Notion이 아니라 docs에 있어야 하므로 문서 위치 규칙을 지켜야 한다.

실제 spec, ADR, plan, runbook, handoff는 `docs/`에 둔다.
