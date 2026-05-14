# v0.4-03: OpenClaw Tool Adapter

## Spec

- `docs/specs/01-architecture.md`
- `agent.md`
- Master plan: `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

## Status

**Proposed**

## Context

OpenClaw integration은 repo CLI를 호출하는 얇은 adapter여야 한다.
저장/검색/답변의 실제 동작은 repo tool layer에 남기고, OpenClaw 설정은 routing과 입출력 변환만 담당한다.

## Checklist

- [ ] 현재 설치된 OpenClaw config/schema 위치 확인
- [ ] `ffxiv` agent workspace를 repo root로 지정하는 설정 초안 작성
- [ ] mention pattern 결정: `ffxiv`, `ff14`, `파판`, `파판봇`
- [ ] tool command 매핑: save note -> `tools/ingest_discord_note.py`
- [ ] tool command 매핑: search/answer -> `tools/search_kb.py`, `tools/answer.py`
- [ ] tool command 매핑: drive sync -> `tools/sync_drive.py`
- [ ] OpenClaw adapter가 JSON stdout/stderr를 어떻게 Discord message로 바꾸는지 규칙 작성
- [ ] 실패 메시지 규칙 작성: auth missing, invalid category, rebuild failed
- [ ] unittest 또는 fixture test로 command mapping 검증
- [ ] `agent.md`에 저장 요청 처리 규칙 반영
- [ ] runbook 작성: local OpenClaw smoke test

## Verification

```bash
python -m unittest discover -s tests -p "test_*.py"
python tools/ingest_discord_note.py --dry-run --category personal_notes --title "Adapter smoke" --body "hello"
python tools/answer.py "흑마 7.5 변경점 알려줘"
```

실제 Discord 호출은 local CLI 검증 후 maintainer 환경에서 수동 smoke로 확인한다.

## Key Decisions

- OpenClaw adapter는 repo 내부 파일을 직접 쓰지 않는다.
- 모든 side effect는 CLI tool의 `--apply` 경로에서만 발생한다.
- OpenClaw 설정 schema가 불명확하면 먼저 조사 plan을 갱신한다.

