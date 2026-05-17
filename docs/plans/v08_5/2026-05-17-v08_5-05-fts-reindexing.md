# v0.8.5-05: Re-index Wiki into SQLite FTS

## Spec

- Master plan: `docs/plans/v08_5/README.md`
- Implementation source plan: `docs/plans/2026-05-17-v08_5_implementation.md` (Task 5)
- Activation spec: `docs/specs/0009-v08_5_managed_wiki_kb_activation_spec.md`

## Status

Pending

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

- [ ] red test 작성: `tests/test_v08_5_fts_visibility.py`
  - [ ] `test_generated_job_wiki_in_wiki_pages`
  - [ ] `test_generated_patch_wiki_in_wiki_pages`
  - [ ] `test_generated_skill_wiki_in_wiki_pages`
  - [ ] `test_generated_wiki_searchable`
  - [ ] `test_source_summary_fallback_preserved`
- [ ] red 상태 확인
- [ ] FTS 재색인 실행
- [ ] DB 확인
  - [ ] `wiki_pages` wiki_type 분포 확인
  - [ ] generated wiki (job, patch, skill) page 포함 확인
  - [ ] source_summary page 유지 확인
- [ ] ask smoke 확인
  - [ ] `python tools/ask.py "건브 7.5 변경점 알려줘" --format json`
  - [ ] `python tools/ask.py "No Mercy 관련 변경 있어?" --format json`
  - [ ] `status`가 `ok`인지 확인
  - [ ] `contexts`가 비어 있지 않은지 확인
  - [ ] contexts에 job/patch/skill/source_summary 중 관련 context 포함 확인
- [ ] 최소 코드 수정으로 green 전환
- [ ] handoff/README feature map status 갱신

## Verification

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
python -m unittest tests.test_v08_5_fts_visibility -v
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
