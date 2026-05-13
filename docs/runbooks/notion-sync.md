# Notion Handoff Sync Runbook

`docs/handoff/CURRENT_HANDOFF.md`가 원본이다.

Notion은 source of truth가 아니다. Notion handoff page는 agent가 빠르게 찾기 위한 mirror/index로만 사용한다.

## 환경변수

apply를 실행하려면 다음 환경변수가 필요하다.

```text
NOTION_API_KEY
NOTION_HANDOFF_PAGE_ID
```

token이나 `.env` 파일은 커밋하지 않는다.

## Dry-run

기본 사용은 dry-run이다. Notion API를 호출하지 않고 반영할 내용을 출력한다.

```bash
python scripts/sync_notion_handoff.py --dry-run
```

옵션 없이 실행해도 dry-run으로 동작한다.

```bash
python scripts/sync_notion_handoff.py
```

## Apply

Notion mirror에 실제 반영할 때만 apply를 사용한다.

```bash
python scripts/sync_notion_handoff.py --apply
```

`--apply`는 `NOTION_API_KEY`와 `NOTION_HANDOFF_PAGE_ID`가 없으면 exit code 1로 종료한다.

현재 apply는 복잡한 Markdown to Notion block 변환을 하지 않는다. `CURRENT_HANDOFF.md`의 plain text 요약을 Notion page children에 paragraph block으로 append하는 최소 구조다.

## 주의

- Notion token을 코드에 하드코딩하지 않는다.
- `.env`를 만들거나 커밋하지 않는다.
- Notion 내용이 오래되었으면 `docs/handoff/CURRENT_HANDOFF.md`를 기준으로 다시 sync한다.
