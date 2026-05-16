# Handoff 문서 운영 규칙

`docs/handoff/`는 다음 agent/session이 이어받기 위한 인계 문서 영역이다.

핵심 원칙:

- `CURRENT_HANDOFF.md`는 현재 상태 대시보드다.
- 과거 상세 로그는 `history/` 아래 날짜별 파일로 보관한다.
- 긴 구현 설명은 handoff가 아니라 spec, plan, runbook에 남긴다.

## 파일 역할

```text
docs/handoff/
  CURRENT_HANDOFF.md
  README.md
  history/
    YYYY-MM-DD-current-handoff.md
```

### `CURRENT_HANDOFF.md`

다음 agent가 바로 작업을 시작할 수 있게 현재 상태만 짧게 적는다.

포함할 내용:

- 현재 phase
- 마지막 완료 task
- 다음 task
- 먼저 읽을 문서
- 최근 검증 스냅샷
- 현재 작업트리 주의사항
- 명시적 금지 범위

포함하지 않을 내용:

- 오래된 task별 상세 로그
- 이미 완료된 phase의 긴 구현 기록
- spec/runbook에 있어야 할 반복 실행 절차 전문
- plan에 있어야 할 세부 체크리스트 전문

권장 길이:

- 평소 100줄 안팎
- 특별한 전환기에도 150줄을 넘기지 않는다.

### `history/`

`CURRENT_HANDOFF.md`가 길어졌을 때 과거 내용을 날짜별로 보존하는 곳이다.

파일명 규칙:

```text
YYYY-MM-DD-current-handoff.md
YYYY-MM-DD-brief-topic.md
```

예시:

```text
docs/handoff/history/2026-05-17-current-handoff.md
```

history 파일은 감사 추적용이다. 다음 agent는 기본적으로 읽지 않고, 필요한 근거가 있을 때만 연다.

## 작성 방식

작업 종료 시:

1. `CURRENT_HANDOFF.md`를 append-only 로그로 만들지 않는다.
2. 현재 상태, 마지막 완료 task, 다음 task, 검증 스냅샷만 갱신한다.
3. 상세 red/green 결과는 해당 task plan에 남긴다.
4. phase가 끝나거나 handoff가 150줄을 넘으면 과거 내용을 `history/`로 옮긴다.
5. `python scripts/finish_task.py`를 실행하기 전에 current handoff가 최신인지 확인한다.

## 문서 위치 기준

- 구현 계약: `docs/specs/`
- 작업 체크리스트와 red/green 증거: `docs/plans/`
- 반복 가능한 명령과 운영 절차: `docs/runbooks/`
- 다음 세션 현재 상태: `docs/handoff/CURRENT_HANDOFF.md`
- 과거 handoff 전문: `docs/handoff/history/`

## Notion 경계

Notion은 source of truth가 아니다. Notion에는 handoff 요약, 링크, 상태 인덱스만 둔다. 원본 인계 문서는 항상 repo `docs/handoff/`에 둔다.
