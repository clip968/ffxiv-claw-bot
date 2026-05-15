# v0.4-05: Status Notification

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- Notion runbook: `docs/runbooks/openclaw-notion.md`

## Status

**Implemented**

## Goal

처리 결과를 Discord 응답과 Notion 상태판에 반영한다.

이 plan은 최종 result JSON을 사람이 읽는 메시지와 Notion status update로 변환한다. storage write와 rebuild 실행은 수행하지 않는다.

## Scope

- `ok`, `partial`, `error` 응답 문구
- 저장 위치 출력
- wiki path 출력
- graph status 출력
- 실패 사유 출력
- v04-02 schema를 사용한 Notion status 반영

Out of scope:

- Notion schema 설계
- local source write
- compile_wiki/build_graph 실행

## Message Fields

사용자-facing Discord/OpenClaw 응답에는 다음만 짧게 포함한다.

- title
- category
- local source path 또는 relative canonical path
- wiki path
- graph status
- 실패 시 next action

Drive URL은 legacy optional integration 결과에서만 표시한다.

## Red Test

- File: `tests/test_v04_status_notification.py`
- Implementation target: `tools/status_notification.py`
- Expected callables:
  - `format_discord_summary(result)`
  - `build_notion_status_update(result)`
- Current red reason: module/functions do not exist yet.
- Contract fixed by the test:
  - Partial local ingest/rebuild result formats a Discord/OpenClaw-facing summary with title, category, local source path, wiki path, graph status, failure reason, and next action.
  - Default user-facing summary must not include a Drive URL.
  - The same result maps to Notion fields such as `Status`, `Graph Status`, `Last Error`, and `Next Action`.

## Checklist

- [x] `ok` result JSON -> Korean user message 변환 규칙 작성
- [x] `partial` result JSON -> 저장은 되었지만 rebuild/graph/Notion 일부 실패 메시지 작성
- [x] `error` result JSON -> 저장 실패 사유와 next action 작성
- [x] v04-02의 Notion status value mapping을 사용한다
- [x] `tools/status_notification.py` 신설 (format_discord_summary + build_notion_status_update)
- [x] Discord message는 짧게, 자세한 진단은 JSON/log에 남긴다

## Verification

```bash
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- Notion status와 Discord summary는 같은 result JSON에서 파생한다.
- Notion에는 파일을 업로드하지 않는다.
- Drive link는 기본 응답 필드가 아니다.

## Implementation Notes

- Created `tools/status_notification.py` with two public functions:
  - `format_discord_summary(result)` — produces a short Korean plain-text summary.
    - `ok` → `[category] title — 처리 완료`
    - `partial` → `[category] title — 일부 실패` with paths, error, next action
    - `error` → `[category] title — 처리 실패` with error and next action
    - Never includes Drive URL (per contract).
  - `build_notion_status_update(result)` — flat dict of Notion property name→value pairs.
    - Maps `status` → `Status` using v04-02 conventions (ok→Indexed, partial→Partial, error→Error)
    - Maps `graph_status` → `Graph Status` (built→Built, pending→Pending, failed→Failed, skipped→Skipped)
    - Copies title, category, source_id, local_source_path, wiki_path, last_error, next_action verbatim.
- Used `tools/openclaw_notion_control.py` status mapping conventions but kept independent mapping constants (v04-05 uses "Failed" not "Error" for graph status).
- `format_discord_result.py` naming was rejected; the functions live in `tools/status_notification.py` alongside the Notion mapping.

## Verification Results

```bash
python -m unittest tests.test_v04_status_notification -v
python -m unittest discover -s tests -p "test_*.py"
```

- v04-05 test: **Green** (1/1 pass)
- full suite: **72 tests, 0 reds** — all v04 tests now green
