# v0.4-04: Local Publish Then Rebuild

## Spec

- Master plan: `docs/plans/2026-05-14-v04-openclaw-local-ingest-and-notion-control.md`
- v0.3 rebuild reference: `docs/plans/v03/2026-05-14-v03-05-rebuild-chain.md`
- Runbook: `docs/runbooks/rebuild-kb.md`

## Status

**Proposed**

## Goal

Local Storage 저장 후 `compile_wiki.py`, `wiki_fts`, `build_graph.py`를 연결해 저장한 자료가 검색/답변 경로에 반영되게 한다.

이 plan은 성공한 local ingest 결과를 입력으로 받아 rebuild를 수행한다. local source write, raw snapshot, DB upsert 규칙은 v04-01/v04-03의 책임이다.

## Scope

- `compile_wiki.py` 실행
- `wiki_fts` 색인 갱신
- `build_graph.py` 실행
- 부분 실패 정책
- Notion/Discord가 사용할 rebuild result payload 생성

Input:

- `source_id`
- `raw_path`
- `source_type = local_file | local_document`
- successful `write_local_source`, `snapshot_raw`, `upsert_source` result

## Pipeline

```text
successful local ingest result
-> compile_wiki
-> index_fts
-> build_graph
-> rebuild result payload
```

## Partial Failure Policy

- upstream local ingest 실패: rebuild 실행 안 함
- compile/wiki/FTS 실패: `status=partial`
- graph 실패: `status=partial`
- Notion update 실패는 v04-05에서 처리

## Red Test

- File: `tests/test_v04_local_rebuild.py`
- Implementation target: `tools/local_rebuild.py`
- Expected callable: `rebuild_after_ingest(ingest_result, root_path, db_path, dry_run)`
- Current red reason: module/function does not exist yet.
- Contract fixed by the test:
  - Successful local ingest result plans rebuild actions in this order: `compile_wiki`, `index_fts`, `build_graph`.
  - Dry-run rebuild returns JSON without invoking Drive behavior.
  - Rebuild consumes `source_id`, `raw_path`, and `source_type = local_document` from the local ingest result.

## Checklist

- [ ] `local_file`/`local_document` source_type이 `compile_wiki.py` Markdown/text 경로를 타는지 확인
- [ ] `new`/`changed` local source만 rebuild 대상으로 수집
- [ ] `sync_storage.py --apply --rebuild` 또는 별도 rebuild wrapper 설계
- [ ] rebuild 실패가 storage 성공을 되돌리지 않는지 테스트
- [ ] end-to-end fixture로 저장한 note가 `search_kb.py`에서 검색되는지 검증
- [ ] v04-05가 사용할 `wiki_path`, `graph_status`, `last_error`를 result JSON에 포함

## Verification

```bash
python -m unittest tests.test_compile_wiki
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- rebuild 실패는 저장 실패와 분리한다.
- Local Storage source는 wiki/FTS/graph로 재구성되어야 검색 가능한 지식이 된다.
- Drive download/sync는 이 plan의 기본 경로가 아니다.
