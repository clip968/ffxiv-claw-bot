# 다음 세션 핸드오프 - v0.2-1 build_graph.py 구현 (Archive)

> Notion `다음 세션 핸드오프 - v0.2-1 build_graph.py 구현`에서 2026-05-14 가져옴.
> 현재 v0.2 Graph layer는 4개 하위 단계 모두 완료된 상태다.
> 과거 핸드오프 참고용으로 보관한다.

## 원본 출처

Notion URL: https://www.notion.so/35f4bf16ed1f81569edcd0f0037a3c43

## 요약

- `build_graph.py`: wiki_pages 스캔 -> graph_nodes/edges 생성 (idempotent)
- `graph_path.py`: --source, --target, --node --depth 질의
- `search_kb.py` 수정: graph_paths 필드 추가
- `answer.py` 수정: 관계 그래프 경로 표시
- v0.2 4개 커밋 완료: `566d7a7`, `e1cd1cd`, `7d05c58`, `eb5685d`
