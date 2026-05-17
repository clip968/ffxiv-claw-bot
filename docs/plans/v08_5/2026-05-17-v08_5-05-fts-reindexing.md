# v0.8.5-05: Re-index Wiki into SQLite FTS

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 5)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Completed 2026-05-17

## Goal

새로 생성된 graph-derived wiki가 ask 검색 대상에 포함되도록 SQLite FTS를 재색인한다.

## Scope

- `index_wiki_documents()` 실행
- `wiki_pages`에 generated wiki 색인 확인
- `wiki_fts`에 generated wiki text 색인 확인
- ask 결과 context에 derived wiki 등장 확인
- source summary fallback 유지 확인

Out of scope:

- derived wiki 생성 (v08_5-04 책임)
- answer quality 개선 (v08_5-06 책임)
- FTS 엔진 자체 수정

## Red Test

- File: `tests/test_v08_5_fts_visibility.py`
- Implementation target: generated wiki FTS visibility

Contracts fixed by the tests:

- graph-derived job wiki 생성 후 `index_wiki_documents()`를 실행하면 `wiki_pages`에 job page가 들어간다.
- patch page가 들어간다.
- skill page가 들어간다.
- `search_wiki()` 또는 ask retrieval에서 generated wiki가 검색된다.
- source summary도 계속 검색된다.

## Checklist

- [x] red test 작성: `tests/test_v08_5_fts_visibility.py`
  - [x] `test_generated_job_wiki_in_wiki_pages`
  - [x] `test_generated_patch_wiki_in_wiki_pages`
  - [x] `test_generated_skill_wiki_in_wiki_pages`
  - [x] `test_generated_wiki_searchable`
  - [x] `test_source_summary_fallback_preserved`
  - [x] `test_entity_match_falls_back_to_generated_skill_page`
- [x] red 상태 확인
- [x] FTS 재색인 실행
- [x] DB 확인
  - [x] `wiki_pages` wiki_type 분포 확인
  - [x] generated wiki (job, patch, skill) page 포함 확인
  - [x] source_summary page 유지 확인
- [x] ask smoke 확인
  - [x] `python tools/ask.py "건브 7.5 변경점 알려줘" --format json`
  - [x] `python tools/ask.py "No Mercy 관련 변경 있어?" --format json`
  - [x] `status`가 `ok`인지 확인
  - [x] `contexts`가 비어 있지 않은지 확인
  - [x] contexts에 job/patch/skill/source_summary 중 관련 context 포함 확인
- [x] 최소 코드 수정으로 green 전환
- [x] handoff/README feature map status 갱신

## Results

- 최초 red 상태: `tests/test_v08_5_fts_visibility.py`가 존재하지 않아 import 실패.
- 두 번째 red 상태: `scan_wiki_documents()`가 `wiki/jobs`만 색인하고 `wiki/patches`, `wiki/skills`를 누락.
- 세 번째 red 상태: `Patch 7.5` 검색어의 decimal separator가 FTS 토큰과 맞지 않아 patch page 검색 실패.
- 네 번째 red 상태: `No Mercy 관련 변경 있어?`가 FTS generic query에서 비어 있고 graph entity match만으로는 generated skill page를 context에 넣지 못함.
- 구현 결과: wiki scanner가 `job`, `patch`, `skill`, `source_summary`를 색인하고, `sanitize_fts_query()`가 `7.5`를 `7 5`로 토큰화하며, graph-aware retrieval이 matched entity의 generated wiki page를 fallback context로 반환한다.
- 실제 re-index summary: `indexed=38`, `source_summary=26`, `job=5`, `patch=3`, `skill=4`.
- 실제 DB sample: `job_gunbreaker`, `patch_7_5`, `skill_no_mercy`가 `wiki_pages`에 포함되고 source summaries 26개가 유지됨.
- ask smoke: `건브 7.5 변경점 알려줘`는 `job_gunbreaker`, `patch_7_5`, source summaries를 context로 반환했고, `No Mercy 관련 변경 있어?`는 `skill_no_mercy`를 context로 반환했다.
- 답변 본문은 아직 source dump에 가깝다. 구조화 요약 품질 개선은 v08.5-06 범위다.

## Verification

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
python -m unittest tests.test_v08_5_fts_visibility -v
python -m unittest tests.test_search_kb -v
python -m unittest tests.test_hybrid_retrieval -v
python -m unittest tests.test_v07_ask_cli -v
```

DB 확인:

```bash
python - <<'PY'
import sqlite3
conn = sqlite3.connect('db/ffxiv.sqlite')
print('wiki types')
for row in conn.execute('SELECT wiki_type, COUNT(*) FROM wiki_pages GROUP BY wiki_type ORDER BY wiki_type'):
    print(row)
print('sample pages')
for row in conn.execute("SELECT page_id, title, wiki_type, path FROM wiki_pages WHERE wiki_type IN ('job','patch','skill','source_summary') ORDER BY wiki_type, page_id LIMIT 20"):
    print(row)
conn.close()
PY
```

Ask smoke:

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
```

## Key Decisions

- FTS 재색인은 기존 `tools/compile_wiki.py`의 `index_wiki_documents()`를 사용한다.
- source summary fallback은 반드시 유지한다.
- graph-aware retrieval이 additive하게 동작해야 한다.
- generated entity page fallback은 graph neighborhood edge가 부족할 때만이 아니라 matched entity 자체가 generated wiki page로 존재할 때도 유효한 context로 취급한다.
- FTS5 decimal patch query는 `7.5`를 `7 5`로 변환해 generated `Patch 7.5` 문서와 매칭한다.

## Implementation Notes

- `index_wiki_documents()`가 `wiki/jobs`, `wiki/patches`, `wiki/skills` 하위 파일을 인식하지 못하면 wiki_type 매핑 로직을 점검한다.
- FTS 재색인 후 중복이 증가하지 않아야 한다.
- 테스트는 fixture 기반으로 격리한다.

## Agent Prompt

```text
v08.5 Task 5를 수행한다.
먼저 tests/test_v08_5_fts_visibility.py에 red test를 작성한다.
그 다음 index_wiki_documents()를 실행하여 generated wiki를 FTS에 색인한다.
wiki_pages에 job/patch/skill page가 들어가는지 확인한다.
ask smoke query로 context에 derived wiki가 등장하는지 확인한다.
source summary fallback이 유지되는지 확인한다.
```
