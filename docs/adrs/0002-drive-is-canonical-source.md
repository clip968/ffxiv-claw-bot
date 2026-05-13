# ADR 0002: Drive Is Canonical Source

## Status

Accepted

## Context

FFXIV 공대 문서, 가이드, 매크로, 개인 노트는 사람이 계속 수정한다. 사람이 편하게 관리하는 위치와 봇이 검색하기 좋은 위치는 다르다.

로컬 파일, wiki, DB, graph를 모두 수동 편집 대상으로 보면 어떤 값이 최신인지 불명확해진다.

## Decision

Google Drive `FFXIV_KB`를 사람이 관리하는 원본 지식 저장소로 둔다.

로컬 `raw/drive`, `wiki`, `db/ffxiv.sqlite`, FTS, graph는 재생성 가능한 파생 캐시로 본다.

## Consequences

좋은 영향:

- 사람이 직접 지식을 수정할 때는 Drive 문서를 수정하면 된다.
- 로컬 캐시는 sync/rebuild로 갱신한다.
- 봇은 로컬 캐시를 사용해 빠르게 검색할 수 있다.
- 원본과 파생 산출물의 책임이 분리된다.

트레이드오프:

- sync/rebuild 절차가 필요하다.
- 로컬 산출물을 직접 수정하면 다음 동기화에서 덮어쓰기될 수 있다.
- 실제 Google Drive API/OAuth 연동은 별도 구현 단계가 필요하다.
