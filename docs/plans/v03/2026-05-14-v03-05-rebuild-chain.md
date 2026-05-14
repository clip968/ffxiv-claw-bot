# v0.3-05: Drive 변경 감지 후 Wiki/FTS/Graph 재빌드

## Spec

`docs/specs/0003-google-drive-sync.md`
- "아직 완료되지 않은 범위: wiki/FTS/graph rebuild 연결"
- v0.3 manifest sync 범위 밖: Drive 변경 감지 후 wiki/FTS/graph 자동 재빌드

## Status

**Completed** (2026-05-14)

## Context

이 plan은 `sync_drive.py --apply` 이후 wiki/FTS/graph 재빌드 자동화를 구현한다.

## Key Decisions (해결됨)

1. **Drive markdown/text -> compile_wiki 처리 방식**: 옵션 A 선택.
   - `compile_wiki.py`가 `source_type`을 읽어 `drive_document`이면 raw content를 HTML 파싱 없이 그대로 사용한다.
   - HTML source는 기존처럼 BeautifulSoup으로 extract_text() 처리.

2. **FTS 갱신 단위**: source 단위. 기존 `upsert_wiki_fts()`가 DELETE + INSERT로 source 단위 갱신을 이미 지원함.

3. **graph rebuild 범위**: source 단위. 기존 `build_graph.py --source-id`를 그대로 재사용.

4. **자동 재빌드 vs 수동 `--rebuild` 플래그**: 수동 `--rebuild` 플래그 선택.
   - `sync_drive.py --apply --manifest X --rebuild`로 명시적 실행.
   - `--from-drive --download --apply --rebuild`도 지원.
   - 자동 연결은 다음 v0.4에서 필요 시 논의.

## 구현 요약

### compile_wiki.py 변경
- `get_source()`에 `source_type` 필드 추가
- `read_raw_html()` → `read_raw_content()`로 일반화 (이름만 변경, 동일 시그니처)
- `compile_for_source()`가 `source_type == "drive_document"` 감지 시 raw content를 HTML 파싱 없이 body_text로 사용

### sync_drive.py 변경
- `--rebuild` CLI 플래그 추가 (`--apply`와 함께 사용 필수)
- `build_plan_item()`에 실제 DB source_id 반영 (기존 source는 DB id, 새 source는 `drive_source_id()` 생성)
- `rebuild_for_items()` 함수: source ID 목록을 받아 compile_wiki + build_graph 실행
  - compile 실패 시에도 나머지 source 처리 계속 (부분 실패 허용)
  - graph 실패 시 error 수집 (compile 성공한 source만 graph 대상)
- `--from-drive` 경로와 manifest 경로 양쪽에서 `--rebuild` 지원

### 테스트
- `test_compile_wiki.py`: drive_document source가 Markdown content를 HTML 파싱 없이 그대로 FTS에 저장하는지 검증
- `test_sync_drive.py`: `rebuild_for_items()` end-to-end 테스트 (apply → compile → FTS → graph)
- `test_sync_drive.py`: `--rebuild` without `--apply` CLI validation

## Checklist

- [x] changed/new Drive source만 compile 대상으로 수집
- [x] Drive raw (Markdown/text) -> compile_wiki 입력 처리 결정 (옵션 A)
- [x] compile_wiki를 Markdown/text 입력도 처리 가능하게 확장 (옵션 A)
- [x] `wiki_fts` 갱신 범위를 변경된 source 단위로 제한 (기존 설계로 충족)
- [x] compile_wiki.py `upsert_wiki_fts()` 재사용
- [x] `build_graph.py --source-id` 연결 확인
- [x] graph_nodes/edges를 특정 source만 rebuild 지원 (기존 설계로 충족)
- [x] End-to-end 파이프라인: Drive sync -> compile -> FTS -> graph
- [x] 실패 시 롤백 또는 부분 재시도 정책 (source별 개별 처리, error 수집, 계속 진행)
- [x] unittest: compile_wiki가 Markdown 입력 처리 확인
- [x] unittest: FTS 증분 갱신 확인
- [x] unittest: graph incremental rebuild 확인

## Verification

```bash
# 1. manifest 기반 apply + rebuild
python tools/sync_drive.py --apply --manifest tests/fixtures/drive_manifest.json --rebuild --db-path /tmp/ffxiv-test.sqlite --root-path /tmp/ffxiv-test

# 2. rebuild 결과에서 compile + graph 확인
python tools/search_kb.py "Black Mage" --db-path /tmp/ffxiv-test.sqlite 2>/dev/null
# 또는 json output 확인

# 3. unittest 전체 통과 확인
python -m unittest discover -s tests -p "test_*.py"
```
