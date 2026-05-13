# 다음 작업 - compile_wiki.py 최소 버전

> 원본: Notion "다음 작업 - compile_wiki.py 최소 버전"
> https://www.notion.so/35f4bf16ed1f81fc87cfd5ce4f42142e
> 동기화: 2026-05-14

**상태: ✅ 완료 (커밋 `b1ed453`)**

---

## 이전 완료 상태

```
완료:
- agent.md
- memory.md
- tools/init_db.py
- tools/ingest_url.py
- config/*.yaml
- wiki/index.md
- db/ffxiv.sqlite
- raw/urls/*.html 테스트 수집 결과
```

## 목표

`tools/compile_wiki.py` 구현. LLM 기반 위키 생성이 아닌, 최소 파이프라인:

```
sources 테이블의 source_id 입력 → sources.raw_path 조회 → raw HTML 읽기
→ BeautifulSoup으로 title/body 추출 → wiki/source_summaries/<source_id>.md 생성
→ wiki_pages 테이블에 metadata 저장
```

## 성공 기준

1. source_id 하나를 입력하면 wiki/source_summaries/<source_id>.md 파일 생성
2. 생성된 md 파일에 title, source_url, raw_path, body excerpt 포함
3. wiki_pages 테이블에 해당 wiki page metadata 저장
4. 같은 source_id로 다시 실행해도 중복 insert가 아니라 update/upsert 동작

## 이 단계에서 하지 않을 것

- LLM 요약 생성 ✗
- Graph 생성 ✗
- Discord/OpenClaw 연결 ✗
- Google Drive 동기화 ✗
