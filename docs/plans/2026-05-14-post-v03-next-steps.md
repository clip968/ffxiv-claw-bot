# Post-v0.3 Next Steps

## Status

Proposed

## Context

현재 완료 상태:

- v0.1 local KB pipeline
- v0.2 graph layer
- v0.3 manifest 기반 Google Drive sync dry-run

이번 문서는 v0.3 이후 후보를 작은 구현 단위로 나눈다. 아래 기능들은 이번 문서 작업에서 구현하지 않는다.

## 후보 1: 실제 Google Drive API 인증/조회 설계

작은 단위:

1. OAuth credential 위치와 token 저장 위치를 결정한다.
2. 필요한 Google API scope를 문서화한다.
3. `FFXIV_KB` folder id 조회 방식을 정한다.
4. 실제 다운로드 없이 파일 목록 조회 CLI만 설계한다.

검증 후보:

- TODO: Google Drive API dependency와 인증 방식 확정 후 작성

## 후보 2: Google Docs export/download 구현

작은 단위:

1. Google Docs export format을 결정한다.
2. Google Docs가 아닌 파일의 download 규칙을 정한다.
3. export/download 결과로 `content_hash`를 계산한다.
4. `raw/drive/<category>/...`에 저장한다.

검증 후보:

- manifest fixture 기반 local content write test
- 실제 Drive API test는 기본 unittest에서 제외

## 후보 3: Drive 변경 감지 후 wiki/FTS/graph 재빌드 연결

작은 단위:

1. changed/new Drive source만 compile 대상으로 수집한다.
2. Drive raw file을 `compile_wiki.py`가 처리할 수 있는지 확인한다.
3. `wiki_fts` 갱신 범위를 source 단위로 제한한다.
4. `build_graph.py --source-id` 연결을 검토한다.

주의:

- 현재 `compile_wiki.py`는 HTML text extraction 중심이다. Drive markdown/text 처리 지원 여부는 TODO다.

## 후보 4: Discord/OpenClaw 연결

작은 단위:

1. CLI pipeline 안정화 상태를 확인한다.
2. Discord command surface를 문서화한다.
3. OpenClaw agent 설정 schema를 확인한다.
4. read-only query command부터 연결한다.

주의:

- Discord/OpenClaw 연결은 v0.3 범위가 아니다.

## 후보 5: 패치노트 자동 수집

작은 단위:

1. 공식 patch note URL source를 정의한다.
2. 수동 URL ingest와 자동 crawl의 중복 기준을 정한다.
3. dry-run crawl plan을 먼저 만든다.

주의:

- 자동 패치노트 크롤링은 명시 요청 전까지 구현하지 않는다.

## 후보 6: 검색 품질 평가

작은 단위:

1. 대표 질문 fixture를 만든다.
2. 기대 source/page id를 정의한다.
3. FTS + graph path 결과를 평가한다.
4. 실패 query를 spec/alias 개선 후보로 기록한다.

## 후보 7: embedding/vector DB 검토

상태:

보류

조건:

- keyword/metadata 검색으로 의미 기반 질의를 처리하기 어렵다는 증거가 생긴다.
- 유사 문서가 많아 ranking 품질이 떨어진다.
- 자연어 질문 표현 다양성이 커진다.

그 전까지는 SQLite FTS5 + metadata + graph traversal을 유지한다.
