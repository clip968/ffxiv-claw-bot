# v0.4-02: OpenClaw Notion Control Contract

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- ADR: `docs/adrs/0006-local-storage-and-notion-control.md`
- Runbook: `docs/runbooks/openclaw-notion.md`

## Status

**Proposed**

## Goal

OpenClaw가 Notion 상태판을 직접 읽고 쓰는 계약을 정의한다.

이 plan은 Notion schema와 status mapping만 소유한다. local file write, rebuild 실행, Discord message formatting은 각각 v04-01/v04-04/v04-05에서 다룬다.

## Notion Role

Notion은 원본 파일 저장소가 아니다. Notion은 작업 관리, 상태판, 문서 인덱스 계층이다.

OpenClaw는 Notion에서 처리 대상을 찾고, 실제 파일은 `/mnt/d/ffixiv-bot-storage`에서 읽으며, 처리 결과를 다시 Notion에 기록한다.

## Candidate Fields

| Field | Required | Meaning |
|---|---|---|
| `Title` | yes | 사람이 읽는 문서 제목 |
| `Category` | yes | `patch_notes`, `job_guides`, `raid_guides`, `static_docs`, `macros`, `bis_sheets`, `personal_notes` |
| `Local Source Path` | yes | `/mnt/d/ffixiv-bot-storage/sources/<category>/...` |
| `Status` | yes | `New`, `Queued`, `Snapshot`, `Indexed`, `Graph Built`, `Partial`, `Error`, `Archived` |
| `Source ID` | no | `local_*` source id |
| `Wiki Path` | no | generated wiki markdown path |
| `Graph Status` | no | graph build status |
| `Last Processed` | no | ISO timestamp |
| `Last Error` | no | short failure reason |
| `Next Action` | no | maintainer or next-agent action |

## OpenClaw Read Flow

```text
Notion status item 조회
-> Status in New/Queued/Partial 필터
-> Local Source Path 존재 여부 확인
-> category와 source_id metadata 정규화
-> repo CLI에 request JSON 전달
```

## OpenClaw Update Flow

```text
repo CLI result JSON 수신
-> action별 status 해석
-> Status, Source ID, Wiki Path, Graph Status 갱신
-> 실패 시 Last Error와 Next Action 기록
```

## Failure Message Rules

- Local source path가 없으면 `Status=Error`, `Last Error=local source path missing`
- local storage root가 없으면 `Status=Error`, `Last Error=local storage root missing`
- rebuild가 실패하면 `Status=Partial`, `Last Error=rebuild failed`
- Notion update 자체가 실패하면 CLI result에는 `notion_update_failed`를 기록하고 파일 저장 결과는 유지한다

## Red Test

- File: `tests/test_v04_openclaw_notion_control.py`
- Implementation target: `tools/openclaw_notion_control.py`
- Expected callable: `build_notion_update(result)`
- Current red reason: module/function does not exist yet.
- Contract fixed by the test:
  - CLI result JSON maps to Notion properties such as `Status`, `Title`, `Category`, `Source ID`, `Local Source Path`, `Wiki Path`, and `Graph Status`.
  - File payload fields such as `body` and `attachments` must not be copied into the Notion update payload.

## Checklist

- [ ] 실제 Notion database/page schema 위치 확인
- [ ] 필드 이름과 enum 값을 확정한다
- [ ] OpenClaw read flow와 update flow를 runbook에 반영한다
- [ ] Notion에는 파일 본문이나 attachment를 올리지 않는 원칙을 재확인한다
- [ ] local CLI result JSON에서 Notion status로 변환하는 규칙을 테스트 가능하게 분리한다
- [ ] Discord/OpenClaw 사용자 문구는 v04-05로 넘기고 이 plan에서는 다루지 않는다

## Verification

```bash
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

## Key Decisions

- Notion은 control plane이다.
- repo `docs/`는 문서 source of truth다.
- 실제 파일은 `/mnt/d/ffixiv-bot-storage`에서 읽는다.
