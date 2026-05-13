# Memory Log — FFXIV Claw Bot

이 파일은 개발 세션 이후 항상 갱신해야 합니다.
작업 완료 → commit → push → 이 파일에 기록 순으로 진행합니다.

---

## 기록 양식

```
### YYYY-MM-DD

#### 변경한 파일
- `path/to/file` — 추가/수정/삭제
- `path/to/file` — 추가/수정/삭제

#### 변경 이유
- 무엇을 했고, 왜 했는지 간략히 설명

#### 변경 내용
- 어떻게 변경했는지 구체적으로 설명 (함수/클래스/스키마 등)

#### 결과물
- 최종 상태 요약 (실행 결과, 테이블 구조, 출력 예시 등)
```

---

## 개발 Agent 작업 규칙

1. **작업 전** — `memory.md`의 최신 기록을 확인하고 이어서 작업할 부분을 파악한다.
2. **작업 중** — 코드 변경 전에 의도를 간략히 설명하고 구현한다.
3. **작업 완료 후**
   - `git add . && git commit -m "설명"`
   - `git push`
   - `memory.md`에 위 양식으로 요약을 작성한다.
4. **요약 작성 기준**
   - **변경한 파일**: 추가/수정/삭제된 모든 파일을 나열
   - **변경 이유**: 왜 이 변경이 필요했는지
   - **변경 내용**: 구체적으로 어떻게 변경했는지 (SQL 스키마, 함수 로직, 파일 구조 등)
   - **결과물**: 실행 결과, 확인 명령어 출력, 동작 방식 등
5. **commit 메시지 규칙**
   - 한국어로 작성
   - 접두어: `feat:`, `fix:`, `refactor:`, `docs:`, `chore:`
   - 예: `feat: ingest_url.py 추가 — URL 입력 → HTML 저장 → DB 기록`

---

## 세션 기록

### 2026-05-14

#### 변경한 파일
- `agent.md` — 추가 (FFXIV Knowledge Agent 역할 정의)
- `memory.md` — 추가 (개발 세션 기록 및 작업 규칙)
- `tools/init_db.py` — 추가 (DB 스키마 초기화: sources, wiki_pages, wiki_fts, graph_nodes, graph_edges, ingest_log)
- `tools/ingest_url.py` — 추가 (URL 입력 → HTML 다운로드 → raw 저장 → hash 계산 → sources 테이블 기록)
- `config/aliases.yaml` — 추가
- `config/sources.yaml` — 추가
- `config/tool_config.yaml` — 추가
- `wiki/index.md` — 추가
- `db/ffxiv.sqlite` — 추가 (SQLite DB with 6 tables + FTS5)
- `raw/urls/*.html` — 추가 (Lodestone 테스트 수집 결과)

#### 변경 이유
- 프로젝트의 기반이 되는 DB 초기화 및 URL 수집 기능을 먼저 구현
- DB가 있어야 ingest_url, compile_wiki, search_kb 등 후속 기능을 붙일 수 있음

#### 변경 내용
- DB 스키마: sources(URL 메타데이터), wiki_pages(컴파일된 위키), wiki_fts(FTS5 전문검색), graph_nodes/edges(지식 그래프), ingest_log(수집 로그)
- ingest_url: requests로 HTML 다운로드 → SHA256 중복 검사 → BeautifulSoup title 추출 → raw/urls/에 저장 → sources 테이블 INSERT
- 중복 방지: content_hash 기준으로 동일 내용 URL 재수집 방지

#### 결과물
- `python tools/ingest_url.py <URL>` 실행 시 JSON 결과 출력
- DB `sources` 테이블에 메타데이터 저장
- `raw/urls/`에 원본 HTML 파일 저장
- 동일 URL 중복 실행 시 `deduplicated: true` 반환
