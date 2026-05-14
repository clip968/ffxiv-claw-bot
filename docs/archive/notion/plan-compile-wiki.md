# 다음 작업 - compile_wiki.py 최소 버전 (Archive)

> Notion `다음 작업 - compile_wiki.py 최소 버전`에서 2026-05-14 가져옴.
> 현재 compile_wiki.py는 완료된 기능이다. 과거 계획 참고용으로 보관한다.

## 원본 출처

Notion URL: https://www.notion.so/35f4bf16ed1f81fc87cfd5ce4f42142e

## 요약

초기 구현 계획: sources 테이블의 source_id로 raw HTML을 읽어 wiki markdown으로 변환.
LLM 기반 생성은 보류하고 BeautifulSoup 기반 텍스트 추출 우선.

## 당시 성공 기준

1. source_id 하나를 입력하면 `wiki/source_summaries/<source_id>.md` 파일 생성
2. 생성된 md 파일에 title, source_url, raw_path, body excerpt 포함
3. wiki_pages 테이블에 해당 wiki page metadata 저장
4. 같은 source_id로 다시 실행해도 중복 insert가 아니라 update/upsert 동작

## 이후 방향

- compile_wiki.py 완료 후 다음은 search_kb.py로 이동
- index_fts.py 분리는 compile_wiki.py가 FTS를 포함했으므로 보류됨
