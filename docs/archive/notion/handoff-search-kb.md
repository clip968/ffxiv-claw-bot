# 다음 세션 핸드오프 - search_kb.py 구현 (Archive)

> Notion `다음 세션 핸드오프 - search_kb.py 구현`에서 2026-05-14 가져옴.
> 현재 search_kb.py는 graph_paths 필드까지 포함하여 완료된 기능이다.
> 과거 핸드오프 참고용으로 보관한다.

## 원본 출처

Notion URL: https://www.notion.so/35f4bf16ed1f81b495e7d2df444d9751

## 요약

Notion에 작성되었던 search_kb.py 구현 세션의 핸드오프.
핵심 SQL: `wiki_fts MATCH ?` + `bm25(wiki_fts)` score + `snippet()`.
이미 완료된 구현이며 현재 search_kb.py와 answer.py에 반영됨.
