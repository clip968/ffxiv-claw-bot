# 구현 로드맵

> 원본: Notion "ffxiv bot" §11-13
> 동기화: 2026-05-14

---

## Phase 1. 프로젝트 골격 생성

작업:

```
1. /mnt/d/programming/ffxiv-claw-bot 생성
2. 디렉터리 구조 생성
3. agent.md 생성
4. config/aliases.yaml 생성
5. README.md 작성
```

성공 기준: 프로젝트 루트가 준비되고 agent.md가 존재한다.

✅ 완료

---

## Phase 2. SQLite DB와 raw archive

작업:

```
1. tools/init_db.py 구현
2. raw/ 저장 규칙 구현
3. sources metadata 저장
4. hash 기반 중복 방지 구현
```

성공 기준:

```
python tools/init_db.py
python tools/ingest_url.py "URL"
```

실행 후 `raw/urls/`와 `db/ffxiv.sqlite`에 기록이 남는다.

✅ 완료

---

## Phase 3. URL 저장 파이프라인

작업:

```
1. ingest_url.py 구현
2. HTML title/body 추출
3. metadata 생성
4. ingest_log 기록
```

성공 기준: URL 하나를 넣으면 raw 저장 + DB metadata 저장이 된다.

✅ 완료

---

## Phase 4. LLM Wiki compiler

작업:

```
1. prompts/wiki_compiler.md 작성
2. compile_wiki.py 구현
3. 문서 타입 분류
4. wiki markdown 생성
5. wiki_pages 테이블 갱신
```

성공 기준: raw 문서 하나에서 wiki 문서가 1개 이상 생성된다.

✅ 완료 (초기 버전: HTML → 단순 markdown 변환)

---

## Phase 5. FTS 검색

작업:

```
1. index_fts.py 구현 (compile_wiki.py에 통합됨, 별도 구현 보류)
2. search_kb.py 구현
3. alias 기반 query parsing
4. patch/job/raid metadata filter 구현
```

성공 기준:

```
python tools/search_kb.py "흑마 7.5 변경점"
```

관련 wiki 문서와 score가 반환된다.

✅ search_kb.py 완료 (1-2), 3-4는 v0.2에서 alias 설정 후 진행

---

## Phase 6. Graph layer (v0.2)

작업:

```
1. prompts/entity_extractor.md 작성
2. prompts/graph_extractor.md 작성
3. build_graph.py 구현
4. nodes.json / edges.json 생성
5. graph_path.py 구현
```

성공 기준:

```
patch:7.5 -> AFFECTS -> job:black_mage
raid:savage_3 -> HAS_MACRO -> macro:savage_3
```

같은 관계가 생성된다.

🔜 다음 단계

---

## Phase 7. answer pipeline

작업:

```
1. answer.py 구현
2. search_kb 결과를 context pack으로 변환
3. answer_policy.md 적용
4. 출처와 확실도 포함 답변 생성
```

성공 기준:

```
python tools/answer.py "7.5에서 흑마 뭐 바뀜?"
```

근거 포함 답변이 반환된다.

✅ answer.py + answer_policy.md 완료

---

## Phase 8. OpenClaw / Discord 연결 (v0.3)

작업:

```
1. ffxiv agent 추가
2. workspace를 /mnt/d/programming/ffxiv-claw-bot으로 지정
3. ffxiv mention pattern 추가
4. ffxiv-kb tool 연결
5. Discord 호출 테스트
```

성공 기준:

```
@claw_bot ffxiv 안녕
→ ffxiv agent가 응답

@claw_bot ffxiv 7.5 흑마 변경점 알려줘
→ search_kb / answer pipeline 사용
```

📋 예정

---

## Phase 9. Google Drive 동기화

작업:

```
1. FFXIV_KB 폴더 생성
2. rclone 또는 Drive API 설정
3. sync_drive.py 구현
4. modifiedTime/hash 기반 변경 감지
5. 변경된 문서만 재컴파일
```

성공 기준:

```
Google Docs 수정 → sync_drive 실행 → raw/drive 갱신 → wiki 갱신 → graph 갱신
```

📋 예정

---

## Phase 10. 패치노트 자동 수집

작업:

```
1. 공식 패치노트 URL 목록 관리
2. crawl_patchnotes.py 구현
3. 새 문서 감지
4. raw 저장
5. wiki/graph 자동 갱신
6. Discord 요약 게시 옵션 추가
```

성공 기준:

```
새 패치노트 감지 → raw 저장 → wiki 생성 → graph 생성 → 요약 가능
```

📋 예정

---

# MVP 범위

## v0.1 (현재)

```
필수 기능:
- 프로젝트 골격 생성 ✅
- SQLite DB 생성 ✅
- URL raw 저장 ✅
- wiki markdown 생성 ✅ (초기 단순 버전)
- FTS 검색 ✅
- answer.py로 근거 기반 답변 ✅
```

## v0.2 (다음)

```
기능:
- node/edge 추출
- graph.json 생성
- graph_path 질의
- "A와 B가 어떻게 연결돼?" 질문 지원
```

## v0.3

```
기능:
- Google Drive FFXIV_KB 동기화
- Docs/Sheets/Excel 파싱
- 변경된 문서만 재컴파일
```

## v0.4+

```
- OpenClaw/Discord 저장 요청 수집
- Google Drive FFXIV_KB 업로드/생성
- Drive publish 후 local KB 재빌드
- Discord 저장 결과/부분 실패 알림
- 패치노트 자동 수집
- Discord 자동 요약 게시
- 필요 시 BGE-M3 또는 다른 embedding 모델 추가
```

v0.4 OpenClaw Drive ingest 작업 분해는 `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`와 `docs/plans/v04/`에서 추적한다.
