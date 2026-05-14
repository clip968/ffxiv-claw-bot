# 작업 로그 - compile_wiki.py 완료 및 다음 단계 (Archive)

> Notion `작업 로그 - compile_wiki.py 완료 및 다음 단계`에서 2026-05-14 가져옴.
> 현재 완료된 기능이다. 과거 작업 로그 참고용으로 보관한다.

## 원본 출처

Notion URL: https://www.notion.so/35f4bf16ed1f81c68f00ca4d90c257ce

## 요약

커밋 `b1ed453`의 compile_wiki.py 구현 로그.
extract_text(), write_summary(), upsert_wiki_page(), upsert_wiki_fts() 구현.
index_fts.py 분리 판단: compile_wiki가 FTS를 포함하므로 보류.
다음 작업: search_kb.py 최소 버전.
