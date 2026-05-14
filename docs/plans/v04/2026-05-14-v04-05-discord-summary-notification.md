# v0.4-05: Discord Summary and Notification

## Spec

- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- `agent.md`
- Master plan: `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

## Status

**Proposed**

## Context

OpenClaw/Discord 사용자는 저장 요청 후 내부 JSON을 볼 필요가 없다.
사용자에게는 저장 위치, 처리 결과, 검색 가능 여부, 실패 시 다음 행동만 짧게 알려야 한다.

## Checklist

- [ ] 저장 성공 메시지 형식 결정: title, category, Drive link, rebuild status
- [ ] dry-run 메시지 형식 결정: planned category/path, no write
- [ ] partial failure 메시지 형식 결정: Drive saved but rebuild failed
- [ ] auth failure 메시지 형식 결정: maintainer action required
- [ ] unsupported input 메시지 형식 결정
- [ ] summary length 제한 결정
- [ ] `tools/format_discord_result.py` 신설 여부 결정
- [ ] unittest: success JSON -> Korean user message 변환 검증
- [ ] unittest: partial failure JSON -> Korean user message 변환 검증
- [ ] unittest: auth failure JSON -> Korean user message 변환 검증
- [ ] `agent.md`에 저장/요약 응답 정책 반영

## Verification

```bash
python -m unittest tests.test_format_discord_result
python -m unittest discover -s tests -p "test_*.py"
```

실제 Discord posting은 OpenClaw adapter smoke 이후 수동으로 확인한다.

## Key Decisions

- Discord 사용자 메시지는 짧게 유지한다.
- 자세한 진단은 JSON/log에 남기고 Discord에는 다음 행동만 노출한다.
- 자동 요약 게시와 패치노트 자동 수집은 이 plan에서 구현하지 않는다.

