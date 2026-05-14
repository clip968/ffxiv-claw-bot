# v0.3-05: Drive 변경 감지 후 Wiki/FTS/Graph 재빌드

## Spec

`docs/specs/0003-google-drive-sync.md`
- "아직 완료되지 않은 범위: wiki/FTS/graph rebuild 연결"
- v0.3 manifest sync 범위 밖: Drive 변경 감지 후 wiki/FTS/graph 자동 재빌드

## Status

**Proposed**

## Context

## Checklist

- [ ] changed/new Drive source만 compile 대상으로 수집
- [ ] Drive raw (Markdown/text) -> compile_wiki 입력 처리 결정 (옵션 A or B)
- [ ] compile_wiki를 Markdown/text 입력도 처리 가능하게 확장 (옵션 A)
- [ ] `wiki_fts` 갱신 범위를 변경된 source 단위로 제한
- [ ] compile_wiki.py `upsert_wiki_fts()` 재사용
- [ ] `build_graph.py --source-id` 연결 확인
- [ ] graph_nodes/edges를 특정 source만 rebuild 지원
- [ ] End-to-end 파이프라인: Drive sync -> compile -> FTS -> graph
- [ ] 실패 시 롤백 또는 부분 재시도 정책
- [ ] unittest: compile_wiki가 Markdown 입력 처리 확인
- [ ] unittest: FTS 증분 갱신 확인
- [ ] unittest: graph incremental rebuild 확인

## Verification
```bash
# 1. Drive 문서 1개 수정 (manifest에서 hash 변경)
# 2. sync_drive --apply 실행 -> changed 1
# 3. wiki / FTS / graph 재빌드 확인
python tools/search_kb.py "수정된 문서 내용"
# -> 최신 내용 검색되는지 확인
```

## Key Decisions (미결정)

- Drive markdown/text -> compile_wiki 처리 방식
- FTS 갱신 단위 (source 단위 vs 전체 재색인)
- graph rebuild 범위 (전체 vs source 단위)
- 자동 재빌드 vs 수동 `--rebuild` 플래그
