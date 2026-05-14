# ADR 0006: Local Storage and Notion Control

## Status

Accepted

## Context

v0.3과 v0.4-01에서 Google Drive 기반 sync/write 구조를 구현했다. 이 구조는 동작 계약과 테스트가 있으므로 삭제하지 않는다.

하지만 현재 기본 운영 경로를 Drive 중심으로 두면 OAuth, folder ID, 네트워크, 외부 cloud 상태가 저장 요청의 필수 의존성이 된다. OpenClaw가 처리할 원본 파일은 사용자가 로컬에서 직접 관리할 수 있어야 하고, repo docs는 계속 Git으로 관리되는 문서 source of truth여야 한다.

Notion은 원본 파일 저장소가 아니다. Notion은 OpenClaw가 직접 읽고 쓰는 작업 관리, 상태판, 문서 인덱스 계층으로 사용한다.

## Decision

1. 기본 원본 파일 저장소는 `/mnt/d/ffixiv-bot-storage`로 둔다.
2. repo `docs/`는 구현 계약, ADR, plan, runbook, handoff의 source of truth로 유지한다.
3. Notion은 OpenClaw가 직접 조작하는 작업 관리, 상태판, 문서 인덱스 계층으로 사용한다.
4. Notion에는 원본 파일 자체를 업로드하지 않는다.
5. Notion에는 `local path`, `category`, `source_id`, `processing status`, `wiki path`, `graph status`, `last error` 같은 상태 metadata만 기록한다.
6. 처리 결과는 repo 내부 `raw/local_storage`, `wiki`, `graph`, `db/ffxiv.sqlite`에 반영한다. 이들은 봇 실행용 캐시 또는 파생 산출물이다.
7. Google Drive 기반 `sync_drive.py`, `publish_drive.py`, 관련 테스트와 문서는 삭제하지 않고 optional legacy integration으로 유지한다.

기본 로컬 저장소 구조는 다음으로 고정한다.

```text
/mnt/d/ffixiv-bot-storage/
  incoming/
  sources/
    urls/
    documents/
    sheets/
    patch_notes/
    raid_guides/
    job_guides/
    static_docs/
    macros/
    bis_sheets/
    personal_notes/
  exports/
    markdown/
    text/
    html/
  manifests/
  archive/
```

각 디렉터리 역할:

- `incoming/`: 아직 분류하지 않은 임시 파일
- `sources/`: 사용자가 관리하는 원본 파일
- `exports/`: xlsx, pdf, docx 같은 파일에서 추출한 md/txt/html 변환본
- `manifests/`: 동기화 테스트용 manifest JSON
- `archive/`: 더 이상 활성 사용하지 않지만 보존할 자료

## Consequences

좋은 영향:

- 기본 ingest/sync 경로가 OAuth와 외부 cloud 상태에 의존하지 않는다.
- 원본 파일 저장 책임과 repo docs 책임이 분리된다.
- OpenClaw는 Notion 상태판에서 처리 대상과 결과를 직접 추적할 수 있다.
- Graphify + LLM Wiki 파이프라인은 유지된다.
- Drive 구현은 삭제하지 않으므로 향후 cloud sync가 필요하면 optional integration으로 재사용할 수 있다.

트레이드오프:

- 여러 장치 간 파일 동기화는 기본 기능이 아니다.
- 로컬 저장소 백업은 별도 운영 책임이다.
- 기존 Drive 중심 문서와 계획은 legacy/deferred 상태로 해석해야 한다.

## Legacy / Deferred

Google Drive 기반 sync/write 구조는 v0.4-01까지 구현되어 있으나, 현재 기본 운영 경로에서는 사용하지 않는다. 향후 외부 클라우드 동기화가 필요할 때 optional integration으로 재검토한다.
