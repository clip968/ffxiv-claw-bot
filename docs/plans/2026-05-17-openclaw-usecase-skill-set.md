# OpenClaw Use-Case Skill Set Plan

## Status

Completed 2026-05-17

## Goal

다양한 OpenClaw 요청을 정형화된 skill routing으로 처리하도록 skill set과 테스트를 추가한다.

## Contract

- Spec: `docs/specs/0010-openclaw-usecase-skill-routing.md`
- Existing source-processing skill: `docs/skills/ffxiv-source-processing.md`
- Runbooks:
  - `docs/runbooks/process-source.md`
  - `docs/runbooks/ask.md`
  - `docs/runbooks/domain-graph-refresh.md`
  - `docs/runbooks/openclaw-notion.md`

## Scope

- `ffxiv-openclaw-router`
- `ffxiv-ask-kb`
- `ffxiv-kb-refresh`
- `ffxiv-notion-status`
- `openclaw-usecase-routing.json`
- 기존 `ffxiv-source-processing` 경계 보강
- doc-test 추가

Out of scope:

- 실제 Notion API write 구현
- OpenClaw runtime adapter 구현
- crawler/scheduler/LLM/vector DB

## Red Test

- File: `tests/test_openclaw_skills.py`
- Expected red:
  - missing router/ask/refresh/notion skill docs
  - missing routing manifest
  - existing source-processing skill missing some boundary text

## Checklist

- [x] red test 작성
- [x] red 상태 확인
- [x] OpenClaw use-case routing spec 추가
- [x] router skill 추가
- [x] ask skill 추가
- [x] refresh skill 추가
- [x] Notion status skill 추가
- [x] routing manifest 추가
- [x] source-processing skill 보강
- [x] focused test green 확인
- [x] docs freshness / finish gate 확인

## Verification Results

```bash
python -m unittest tests.test_openclaw_skills -v
# 6 tests OK
```

```bash
python -m unittest tests.test_v05_process_source tests.test_v04_openclaw_notion_control tests.test_v04_status_notification -v
# 39 tests OK
```

```bash
git diff --check
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
# finish_task: 361 tests OK, docs freshness OK, Notion handoff dry-run OK
```
