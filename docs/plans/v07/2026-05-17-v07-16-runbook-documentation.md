# v0.7-16: Runbook Documentation

## Spec

- Master plan: `docs/plans/v07/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v07-implementation-plan.md` (Task v07-16)
- Pipeline spec: `docs/specs/0007-v07-grounded-ask-pipeline.md`

## Status

Pending

## Goal

v07 ask pipeline의 사용법과 운영 절차를 문서화한다.

## Scope

- `docs/runbooks/ask.md` 생성
- `docs/plans/v07/README.md` 최종 갱신
- `docs/handoff/CURRENT_HANDOFF.md` v07 반영

Out of scope:

- 코드 변경
- 새로운 테스트 추가

## Content Requirements

`docs/runbooks/ask.md` 필수 내용:

- Purpose (v07 ask pipeline 목적)
- CLI examples (JSON, text, debug)
- JSON output example
- Text output example
- Debug mode 설명
- Job wiki first policy
- Source summary fallback policy
- No-context behavior
- Known limitations

## Checklist

- [ ] `docs/runbooks/ask.md` 생성
  - [ ] Purpose
  - [ ] CLI examples
  - [ ] JSON output example
  - [ ] Text output example
  - [ ] Debug mode
  - [ ] Job wiki first policy
  - [ ] Source summary fallback policy
  - [ ] No-context behavior
  - [ ] Known limitations
- [ ] `docs/plans/v07/README.md` feature map status 갱신
- [ ] `docs/handoff/CURRENT_HANDOFF.md` v07 반영

## Verification

```bash
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- crawling은 v07에 포함되지 않음을 명시한다.
- Discord integration은 명시적으로 future work로 표기한다.
- runbook은 다음 agent가 ask pipeline을 이해하고 사용할 수 있을 정도로 충분해야 한다.

## Implementation Notes

- documentation-only task이므로 red test 불필요.
- v07-01~15 완료 후 작성한다.

## Agent Prompt

```text
Implement v07-16 only.

Document the v07 Grounded Ask Pipeline.

Files:
- docs/runbooks/ask.md
- docs/plans/v07/README.md
- docs/handoff/CURRENT_HANDOFF.md

Rules:
- Do not mention crawling as part of v07.
- State that Discord integration is future work.
- Include examples for --format json, --format text, and --debug.
- Run:
  python scripts/check_docs_freshness.py --all
```
