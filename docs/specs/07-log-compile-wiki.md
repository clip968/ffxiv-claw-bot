# 작업 로그 - compile_wiki.py 완료 및 다음 단계

> 원본: Notion "작업 로그 - compile_wiki.py 완료 및 다음 단계"
> https://www.notion.so/35f4bf16ed1f81c68f00ca4d90c257ce
> 동기화: 2026-05-14

**상태: ✅ 완료**

---

## 결과 요약

커밋: `b1ed453`
작업명: `feat: compile_wiki.py 추가`

## 구현 기능

```
--source-id 인자 파싱 → sources 테이블 조회 → raw_path 기반 HTML 파일 로드
→ BeautifulSoup 기반 텍스트 추출 → wiki/source_summaries/<source_id>.md 생성
→ wiki_pages 테이블 INSERT or UPDATE → wiki_fts FTS5 테이블 갱신
```

## 주요 함수

- `extract_text()`: script/style/nav/footer 제거, 본문 텍스트 추출
- `write_summary()`: wiki/source_summaries/<source_id>.md 생성
- `upsert_wiki_page()`: wiki_pages에 INSERT or UPDATE (동일 source_id 재실행 시 update)
- `upsert_wiki_fts()`: wiki_fts에 전문검색 데이터 저장

## 검증 결과

```
1차 실행: wiki_pages 1건 INSERT (created_at = updated_at)
2차 실행: wiki_pages 1건 UPDATE (created_at 유지, updated_at 갱신)
에러 케이스: source_id가 없으면 status: error 반환
```

## 판단

원래 로드맵에서는 `compile_wiki.py` 다음에 `index_fts.py`를 구현할 예정이었으나,
`compile_wiki.py` 안에서 이미 `upsert_wiki_fts()`를 구현했으므로 별도 `index_fts.py`는 보류.
다음 작업은 `search_kb.py` 최소 버전 구현으로 이동.

## 수정된 로드맵

```
1. init_db.py ✅
2. ingest_url.py ✅
3. compile_wiki.py ✅
4. search_kb.py 구현 ← 다음 작업
5. answer.py 최소 버전 구현
6. index_fts.py 분리 여부 검토
7. LLM Wiki compiler 고도화
8. Graph layer 구현
9. OpenClaw / Discord 연결
```
