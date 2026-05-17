# v08.5 Implementation Plan — Managed Wiki Knowledge Base Activation

## 0. 목적

이 문서는 `v08.5 Spec — Managed Wiki Knowledge Base Activation`을 실제 구현 작업으로 분해한 implementation plan이다.

v08.5는 새 기능 확장이 아니다. v08에서 구현된 domain graph, graph-derived wiki, hybrid retrieval 엔진을 실제 `wiki/source_summaries/` 데이터에 적용하고, RAG Wiki로서 사용할 수 있는 답변 품질과 운영 절차를 확보하는 단계다.

목표 상태는 다음과 같다.

    wiki/source_summaries/
      -> source audit
      -> rebuild_domain_graph.py --reset-domain-graph
      -> db/ffxiv.sqlite graph_nodes / graph_edges population
      -> graph/nodes.json, graph/edges.json, graph/domain_graph.json, graph/entity_index.json
      -> graph/GRAPH_REPORT.md validation
      -> generate_derived_wiki.py
      -> wiki/jobs, wiki/patches, wiki/skills
      -> compile_wiki / SQLite FTS re-index
      -> ask.py topic-based grounded answer

완료 후 대표 질문은 다음처럼 동작해야 한다.

    python tools/ask.py "건브 7.5 변경점 알려줘" --format json
    python tools/ask.py "No Mercy 관련 변경 있어?" --format json
    python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
    python tools/ask.py "건브 관련 source 보여줘" --format json

답변은 source body dump가 아니라 다음 구조를 가져야 한다.

    요약:
    - 질문에 대한 핵심 답변

    관련 항목:
    - Job / Patch / Skill

    확인된 내용:
    - source에 근거가 있는 fact

    근거:
    - source summary 또는 derived wiki 경로

    주의:
    - source 부족, 범위 제한, 전체 패치노트로 단정 불가 등의 불확실성

---

## 1. 구현 원칙

### 1.1 새 namespace 확장 금지

v08.5에서는 BIS, raid, item, gearset, encounter namespace를 확장하지 않는다. 현재 엔진이 실제 지식체로 정상 작동하는지 먼저 검증한다.

금지 범위:

- 공식 패치노트 crawler
- polling / scheduler
- Discord slash command 개편
- vector DB
- graph DB
- LLM API 기반 extractor
- GraphRAG community detection
- BIS / raid / item namespace 확장
- ask pipeline 전체 재작성

### 1.2 v08 엔진은 유지하고 활성화한다

v08에서 이미 구현된 다음 파일과 흐름을 우선 사용한다.

- `tools/rebuild_domain_graph.py`
- `tools/generate_graph_report.py`
- `tools/generate_derived_wiki.py`
- `tools/ask.py`
- `src/domain_graph/*`
- `src/retrieval/hybrid.py`
- `src/answering.py`
- `tools/compile_wiki.py`

필요한 경우 수정하되, 기존 v06/v07/v08 테스트가 깨지면 안 된다.

### 1.3 red test 우선

행동 변경이 있는 작업은 먼저 실패하는 테스트를 추가한다.

red test가 필요한 작업:

- 실제 source summary fixture 기반 graph population 검증
- graph-derived wiki 실제 생성 검증
- generated wiki의 FTS visibility 검증
- ask answer quality 개선
- domain graph refresh runbook/documentation freshness 검증이 이미 존재하면 유지

### 1.4 산출물은 재현 가능해야 한다

`db/ffxiv.sqlite`, `graph/*.json`, `graph/GRAPH_REPORT.md`, `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md`는 재생성 가능해야 한다.

반복 실행 시 다음이 유지되어야 한다.

- node 중복 없음
- edge 중복 없음
- fact 중복 없음
- derived wiki 파일 내용 불필요한 흔들림 없음
- FTS 재색인 후 중복 증가 없음

### 1.5 문서 drift를 반드시 해소한다

현재 README와 specs README가 v0.6 중심으로 남아 있으면 다음 agent가 현재 상태를 오해한다. v08.5 완료 시점에는 아래 문서가 현재 pipeline을 반영해야 한다.

- `README.md`
- `docs/specs/README.md`
- `docs/runbooks/ask.md`
- `docs/runbooks/generate-derived-wiki.md`
- `docs/runbooks/domain-graph-refresh.md`
- `docs/handoff/CURRENT_HANDOFF.md`

---

## 2. 권장 작업 순서

반드시 아래 순서로 진행한다.

    0. Baseline verification
    1. Source summary audit
    2. Real domain graph rebuild
    3. GRAPH_REPORT.md validation
    4. Graph-derived wiki generation
    5. SQLite FTS re-indexing
    6. ask.py answer quality improvement
    7. v08.5 tests
    8. Documentation / runbook update
    9. Final regression and handoff update

이 순서를 바꾸면 안 되는 이유는 다음과 같다.

- graph가 비어 있으면 derived wiki 생성도 의미가 없다.
- derived wiki가 생성되지 않으면 FTS 재색인 검증도 의미가 없다.
- retrieval context가 부실하면 answer quality만 손봐도 답변 품질이 좋아지지 않는다.
- 문서 갱신은 실제 명령 결과를 본 뒤 해야 한다.

---

## 3. Phase 0 — Baseline verification

### 목표

v08.5 작업 시작 전, 현재 레포가 v08 완료 상태에서 깨끗하게 테스트를 통과하는지 확인한다.

### 실행 명령

    git status --short
    python -m unittest tests.test_v08_e2e -v
    python -m unittest tests.test_hybrid_retrieval -v
    python -m unittest tests.test_derived_wiki -v
    python -m unittest tests.test_graph_report -v
    python -m unittest tests.test_domain_graph_rebuild -v

가능하면 전체 regression도 먼저 실행한다.

    python -m unittest discover -s tests -p "test_*.py"

### 확인할 것

- 작업 전 uncommitted user change가 있는지 확인한다.
- 기존 v08 테스트가 실패하면 v08.5를 시작하지 말고 원인부터 기록한다.
- 실패가 환경 문제인지 코드 문제인지 구분한다.

### 산출물

- 필요 시 `docs/reports/2026-05-17-v08_5-baseline.md`
- 또는 `CURRENT_HANDOFF.md`의 작업 시작 메모

### Acceptance criteria

- 기존 v08 핵심 테스트가 통과한다.
- 실패가 있으면 v08.5 작업 범위에 포함할지 명시한다.

---

## 4. Task 1 — Source summary audit

### 목표

`wiki/source_summaries/`가 실제 domain graph rebuild 입력으로 사용 가능한 상태인지 확인한다.

### 생성 파일

    docs/reports/2026-05-17-v08_5-source-audit.md

### 구현 방식

우선 수동/스크립트 기반 audit를 수행한다. 필요하면 간단한 helper script를 추가할 수 있다.

권장 helper script:

    tools/audit_source_summaries.py

단, helper script 추가가 과하면 문서와 임시 Python one-liner로도 충분하다.

### 점검 항목

각 source summary에 대해 다음을 확인한다.

- 파일명
- source id 존재 여부
- title 존재 여부
- body length
- FFXIV 관련성
- 비-FFXIV 오염 데이터 여부
- 빈 summary 여부
- 중복 source 가능성
- Job/Patch/Skill alias가 포함될 가능성

### 권장 명령

    find wiki/source_summaries -maxdepth 1 -type f -name "*.md" | sort | wc -l
    find wiki/source_summaries -maxdepth 1 -type f -name "*.md" | sort | head -20

SQLite 상태도 같이 확인한다.

    python - <<'PY'
    import sqlite3
    from pathlib import Path
    db = Path('db/ffxiv.sqlite')
    if not db.exists():
        print('db_missing')
        raise SystemExit(0)
    conn = sqlite3.connect(db)
    for table in ['sources', 'wiki_pages', 'graph_nodes', 'graph_edges']:
        try:
            n = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            print(table, n)
        except sqlite3.Error as exc:
            print(table, 'error', exc)
    conn.close()
    PY

### 문서 템플릿

`docs/reports/2026-05-17-v08_5-source-audit.md`는 다음 구조로 작성한다.

    # v08.5 Source Summary Audit

    ## Summary
    - Audit date:
    - Total source summaries:
    - Usable FFXIV summaries:
    - Empty or too-short summaries:
    - Suspected non-FFXIV summaries:
    - Duplicate candidates:
    - Graph rebuild readiness: yes/no

    ## Method
    - Commands used
    - Criteria

    ## Findings
    | File | Source ID | Title | Body Length | Status | Notes |
    |---|---|---:|---:|---|---|

    ## Exclusions or Fixes Needed
    - ...

    ## Decision
    - Proceed with graph rebuild: yes/no
    - Reason:

### Acceptance criteria

- source summary 총 개수가 기록된다.
- FFXIV source로 사용 가능한 파일 수가 기록된다.
- 제외/수정 후보가 있으면 기록된다.
- graph rebuild 진행 가능 여부가 명시된다.

---

## 5. Task 2 — Actual domain graph rebuild

### 목표

테스트 fixture가 아니라 실제 `wiki/source_summaries/`를 기준으로 domain graph를 채운다.

### 실행 순서

먼저 dry-run을 실행한다.

    python tools/rebuild_domain_graph.py --dry-run --verbose

정상이면 실제 reset rebuild를 실행한다.

    python tools/rebuild_domain_graph.py --reset-domain-graph --verbose

### 확인 SQL

rebuild 후 node type count를 확인한다.

    python - <<'PY'
    import sqlite3
    conn = sqlite3.connect('db/ffxiv.sqlite')
    print('node types')
    for row in conn.execute('SELECT type, COUNT(*) FROM graph_nodes GROUP BY type ORDER BY type'):
        print(row)
    print('edge types')
    for row in conn.execute('SELECT type, COUNT(*) FROM graph_edges GROUP BY type ORDER BY type'):
        print(row)
    conn.close()
    PY

export 파일을 확인한다.

    ls -l graph/nodes.json graph/edges.json graph/domain_graph.json graph/entity_index.json

idempotency를 확인한다.

    python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
    python - <<'PY'
    import sqlite3
    conn = sqlite3.connect('db/ffxiv.sqlite')
    print('nodes', conn.execute('SELECT COUNT(*) FROM graph_nodes').fetchone()[0])
    print('edges', conn.execute('SELECT COUNT(*) FROM graph_edges').fetchone()[0])
    conn.close()
    PY

### red test

추가 후보:

    tests/test_v08_5_real_graph_population.py

fixture 기반으로 작성한다. 실제 repo 데이터에 의존하면 테스트가 흔들릴 수 있으므로, 임시 디렉터리에 source summary와 registry fixture를 만든다.

필수 테스트:

- `rebuild_domain_graph()` 실행 후 `graph_nodes`에 `Job`, `Patch`, `Skill`, `Fact`가 생긴다.
- `graph_edges`에 `MENTIONS`, `SUPPORTS`, `VALID_IN_PATCH`가 생긴다.
- `graph/domain_graph.json`과 `graph/entity_index.json`이 생긴다.
- 같은 rebuild를 두 번 실행해도 count가 증가하지 않는다.

테스트 fixture 예시 입력:

    # Fixture Patch Note

    > Source: `local_v08_5_graph_population`

    Patch 7.5 includes Gunbreaker adjustments. No Mercy duration was changed.

기대 entity:

- `job:gunbreaker`
- `patch:7_5`
- `skill:no_mercy`
- `fact:*`

### 구현 메모

이 task에서 코드 수정은 최소화한다. 기존 `tools/rebuild_domain_graph.py`로 실제 데이터가 채워지지 않는 경우에만 다음을 점검한다.

- source summary parser가 실제 파일 포맷을 못 읽는가?
- `> Source: ...` 포맷이 문서마다 다른가?
- registry alias가 부족한가?
- relation trigger가 너무 보수적인가?
- graph reset이 provenance node까지 잘못 지우는가?

### Acceptance criteria

- 실제 rebuild가 `status=ok`를 반환한다.
- `Job`, `Patch`, `Skill`, `Fact` count가 0이 아니다.
- `MENTIONS`, `SUPPORTS`, `VALID_IN_PATCH` count가 0이 아니다.
- `AFFECTS_JOB`, `AFFECTS_SKILL`이 0이면 source 부족 또는 extractor trigger 부족 사유를 문서화한다.
- graph export 파일이 생성된다.
- 반복 rebuild에서 count가 비정상 증가하지 않는다.

---

## 6. Task 3 — GRAPH_REPORT.md validation

### 목표

생성된 graph가 의미 있는지 `GRAPH_REPORT.md`로 검증한다.

### 실행 명령

    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph

### 확인 항목

`graph/GRAPH_REPORT.md`에서 다음을 확인한다.

- Summary
- total nodes
- total edges
- node type counts
- edge type counts
- top mentioned jobs 또는 top mentioned entities
- quality warnings

### 필요 시 생성 문서

    docs/reports/2026-05-17-v08_5-graph-report-review.md

문서 템플릿:

    # v08.5 Graph Report Review

    ## Summary
    - Report generated:
    - Total nodes:
    - Total edges:
    - Job count:
    - Patch count:
    - Skill count:
    - Fact count:

    ## Edge Coverage
    | Edge Type | Count | Status |
    |---|---:|---|

    ## Top Entities
    - ...

    ## Quality Warnings
    | Warning | Cause | Action |
    |---|---|---|

    ## Decision
    - Proceed to derived wiki generation: yes/no

### red test

기존 `tests/test_graph_report.py`가 충분하면 새 테스트는 생략 가능하다. 다만 실제 v08.5 기준을 고정하려면 아래 테스트를 추가한다.

    tests/test_v08_5_graph_report_quality.py

필수 테스트:

- report에 `Job`, `Patch`, `Skill`, `Fact` count가 표시된다.
- report에 `Quality Warnings` 섹션이 있다.
- report 생성 결과가 deterministic하다.

### Acceptance criteria

- `GRAPH_REPORT.md`가 생성된다.
- Job/Patch/Skill/Fact count가 모두 0이 아니다.
- warning이 있으면 원인과 처리 여부가 문서화된다.
- graph가 비어 있으면 다음 task로 넘어가지 않는다.

---

## 7. Task 4 — Generate graph-derived wiki

### 목표

domain graph에서 파생된 관리형 wiki 문서를 실제 생성한다.

### 실행 순서

먼저 dry-run을 실행한다.

    python tools/generate_derived_wiki.py --dry-run --verbose

정상이면 실제 생성한다.

    python tools/generate_derived_wiki.py --verbose

### 확인 명령

    find wiki/jobs -maxdepth 1 -type f -name "*.md" | sort | head -20
    find wiki/patches -maxdepth 1 -type f -name "*.md" | sort | head -20
    find wiki/skills -maxdepth 1 -type f -name "*.md" | sort | head -20
    sed -n '1,200p' wiki/index.md

### generated page 확인 항목

각 generated wiki는 가능한 한 다음 정보를 포함해야 한다.

- canonical entity name
- entity type
- related facts
- related jobs / patches / skills
- related sources
- source summary path 또는 source id
- generated marker 또는 provenance

### red test

추가 후보:

    tests/test_v08_5_real_derived_wiki.py

필수 테스트:

- graph fixture 기반으로 `generate_derived_wiki()` 실행 시 `wiki/jobs/gunbreaker.md`가 생성된다.
- `wiki/patches/7_5.md`가 생성된다.
- `wiki/skills/no_mercy.md`가 생성된다.
- generated page에 source id 또는 source path가 포함된다.
- `wiki/index.md`가 jobs/patches/skills 문서를 링크한다.
- 재실행해도 파일 내용이 변하지 않는다.

### 구현 메모

이 task에서 새 namespace를 추가하지 않는다. `types=jobs,patches,skills`만 다룬다.

실제 데이터에서 파일이 생성되지 않으면 원인은 보통 다음 중 하나다.

- graph에 Job/Patch/Skill node가 없다.
- graph relation이 source와 entity를 연결하지 못했다.
- derived wiki generator가 특정 edge type만 기대한다.
- `wiki_root` 또는 `graph_dir` 경로가 잘못되었다.

### Acceptance criteria

- `wiki/jobs/*.md`가 최소 1개 이상 존재한다.
- `wiki/patches/*.md`가 최소 1개 이상 존재한다.
- `wiki/skills/*.md`가 최소 1개 이상 존재한다.
- generated page에 related source가 포함된다.
- `wiki/index.md`가 generated pages를 링크한다.
- derived wiki 생성이 idempotent하다.

---

## 8. Task 5 — Re-index wiki into SQLite FTS

### 목표

새로 생성된 graph-derived wiki가 ask 검색 대상에 포함되도록 SQLite FTS를 재색인한다.

### 실행 명령

    python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"

### 확인 SQL

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

### ask smoke

    python tools/ask.py "건브 7.5 변경점 알려줘" --format json
    python tools/ask.py "No Mercy 관련 변경 있어?" --format json

확인할 것:

- `status`가 `ok`다.
- `contexts`가 비어 있지 않다.
- contexts에 `job`, `patch`, `skill`, `source_summary` 중 관련 context가 포함된다.
- source summary fallback이 유지된다.

### red test

추가 후보:

    tests/test_v08_5_fts_visibility.py

필수 테스트:

- graph-derived job wiki 생성 후 `index_wiki_documents()`를 실행하면 `wiki_pages`에 job page가 들어간다.
- patch page가 들어간다.
- skill page가 들어간다.
- `search_wiki()` 또는 ask retrieval에서 generated wiki가 검색된다.
- source summary도 계속 검색된다.

### Acceptance criteria

- generated job/patch/skill wiki가 `wiki_pages`에 들어간다.
- generated wiki가 FTS 검색 대상이 된다.
- source summary fallback이 깨지지 않는다.

---

## 9. Task 6 — Improve ask answer quality

### 목표

`ask.py` 결과가 raw source dump처럼 보이지 않고, 주제별 grounded summary로 보이도록 개선한다.

### 현재 문제 정의

retrieval은 graph-aware로 보강되었지만, answer composer가 context body를 거의 그대로 이어붙이면 사용자는 “wiki RAG”가 아니라 “source dump”로 느낀다.

개선 대상은 retrieval이 아니라 answer composition이다.

수정 후보:

- `src/answering.py`
- `src/retrieval/context_builder.py`
- `tools/ask.py`

우선순위는 `src/answering.py`다. JSON 출력 schema는 유지한다.

### 목표 출력 형식

한국어 질문에 대해 기본적으로 한국어 구조화 답변을 반환한다.

    요약:
    - ...

    관련 항목:
    - Job: ...
    - Patch: ...
    - Skill: ...

    확인된 내용:
    - ...

    근거:
    - ...

    주의:
    - ...

영어 질문은 기존 정책을 유지해도 되지만, 이 프로젝트의 primary use는 한국어 질문이므로 한국어 출력 최적화를 우선한다.

### red test

추가 후보:

    tests/test_v08_5_answer_quality.py

필수 red tests:

1. 답변이 source body 전체를 그대로 덤프하지 않는다.
2. 답변에 `요약` 섹션이 있다.
3. 답변에 `관련 항목` 또는 entity list가 있다.
4. 답변에 `근거` 섹션이 있다.
5. source가 부족하면 `주의` 또는 불확실성 문구가 있다.
6. `--format text`는 answer body만 출력한다.
7. 기존 `tests.test_v07_ask_cli`와 `tests.test_v08_e2e`가 깨지지 않는다.

### 구체 구현안

#### Step 1 — Context classification

context를 wiki_type별로 분류한다.

- `job`
- `patch`
- `skill`
- `source_summary`
- 기타

가능하면 context title/path/snippet/body에서 entity를 추출하지 말고, 이미 검색 결과나 page metadata에 있는 정보를 사용한다.

#### Step 2 — Evidence extraction

context body에서 너무 긴 본문을 그대로 사용하지 않고, 짧은 evidence line을 추출한다.

보수적인 규칙:

- 질문 term 또는 matched entity alias가 포함된 문장 우선
- `changed`, `adjusted`, `duration`, `potency`, `cooldown`, `변경`, `조정`, `상향`, `하향` 등 trigger 포함 문장 우선
- source summary는 근거로 우선 표시
- derived wiki는 정리된 context로 표시

#### Step 3 — Answer sections

답변을 section 단위로 조립한다.

- 요약: evidence가 있으면 1~3문장
- 관련 항목: context title과 graph-derived wiki type 기반
- 확인된 내용: evidence bullet
- 근거: source path/source id bullet
- 주의: context 부족, source 수 제한, 전체 패치노트 단정 불가

#### Step 4 — No source dump guard

answer body가 특정 context body와 지나치게 동일하면 안 된다.

간단한 guard:

- context body 전체를 그대로 append하지 않는다.
- evidence 문장은 최대 N개, 각 문장 최대 M자 제한을 둔다.
- source 경로는 `근거` 섹션에만 표시한다.

#### Step 5 — Confidence 유지

기존 `Answer.confidence` 구조가 있다면 유지한다.

- context 0개: low
- source summary 1개 이상: medium
- derived wiki + source summary 둘 다 있음: medium/high
- 단, 자동으로 high 남발 금지

### Acceptance criteria

- ask JSON schema가 유지된다.
- answer body가 구조화된다.
- source path/source id가 보인다.
- source body 전체 덤프가 없다.
- context 부족 시 부족하다고 말한다.
- 기존 v07/v08 ask tests가 깨지지 않는다.

---

## 10. Task 7 — Add v08.5 tests

### 목표

v08.5에서 확보한 graph population, derived wiki activation, FTS visibility, answer quality를 regression으로 고정한다.

### 생성 테스트 파일

권장:

    tests/test_v08_5_real_graph_population.py
    tests/test_v08_5_real_derived_wiki.py
    tests/test_v08_5_fts_visibility.py
    tests/test_v08_5_answer_quality.py

테스트 수가 과하면 다음처럼 묶어도 된다.

    tests/test_v08_5_activation.py
    tests/test_v08_5_answer_quality.py

### 테스트 설계 원칙

- 실제 repo의 현재 source summary 개수에 의존하지 않는다.
- `tempfile.TemporaryDirectory()`를 사용한다.
- fixture registry와 fixture source summary를 직접 작성한다.
- DB도 temp path를 사용한다.
- v08 E2E test와 중복되더라도 v08.5 acceptance criteria를 명시적으로 검증한다.

### 공통 fixture

registry:

    jobs.json:
      Gunbreaker / GNB / 건브 / 건브레이커
    skills.json:
      No Mercy / 노머시 / job=Gunbreaker
    patches.json:
      Patch 7.5 / 7.5 / 패치 7.5

source summary:

    # Fixture Patch 7.5

    > Source: `local_v08_5_patch_75`

    Patch 7.5 includes adjustments to Gunbreaker. No Mercy duration was changed.

### 필수 assertion

Graph population:

- `job:gunbreaker` node exists
- `patch:7_5` node exists
- `skill:no_mercy` node exists
- `fact:*` node exists
- required edge types exist

Derived wiki:

- `wiki/jobs/gunbreaker.md` exists
- `wiki/patches/7_5.md` exists
- `wiki/skills/no_mercy.md` exists
- related source text exists
- `wiki/index.md` links generated pages

FTS visibility:

- `wiki_pages` has generated wiki pages
- ask/retrieval can include derived wiki context
- source summary fallback still works

Answer quality:

- answer includes `요약`
- answer includes `근거`
- answer includes relevant entity text
- answer does not equal raw source body
- answer includes uncertainty when contexts are sparse

### 실행 명령

    python -m unittest tests.test_v08_5_activation -v
    python -m unittest tests.test_v08_5_answer_quality -v

또는 파일별로:

    python -m unittest tests.test_v08_5_real_graph_population -v
    python -m unittest tests.test_v08_5_real_derived_wiki -v
    python -m unittest tests.test_v08_5_fts_visibility -v
    python -m unittest tests.test_v08_5_answer_quality -v

### Acceptance criteria

- 새 테스트가 red 상태로 시작한다.
- 구현 후 새 테스트가 모두 통과한다.
- 기존 v06/v07/v08 테스트가 모두 통과한다.

---

## 11. Task 8 — Documentation and runbook update

### 목표

v08.5 graph/wiki refresh workflow를 다음 세션이나 다른 agent가 재현할 수 있게 문서화한다.

### 추가 문서

    docs/runbooks/domain-graph-refresh.md

### 갱신 문서

    README.md
    docs/specs/README.md
    docs/runbooks/ask.md
    docs/runbooks/generate-derived-wiki.md
    docs/handoff/CURRENT_HANDOFF.md
    docs/plans/v08_5/README.md

`docs/plans/v08_5/README.md`가 없다면 새로 만든다.

### README.md 갱신 방향

README의 Current Pipeline을 v08.5 기준으로 갱신한다.

기존 v0.6 중심 설명은 history 또는 legacy section으로 내리고, 현재 pipeline은 다음처럼 표시한다.

    Current pipeline:
      source files / URL / queued source
      -> process_source / source summary
      -> rebuild_domain_graph
      -> graph export/report
      -> graph-derived wiki generation
      -> FTS indexing
      -> ask.py graph-aware retrieval

Common Commands에 다음을 추가한다.

    python tools/rebuild_domain_graph.py --dry-run --verbose
    python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
    python tools/generate_derived_wiki.py --dry-run --verbose
    python tools/generate_derived_wiki.py --verbose
    python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
    python tools/ask.py "건브 7.5 변경점 알려줘" --format json

### docs/specs/README.md 갱신 방향

현재 spec 목록에 다음을 포함한다.

- `0007` 또는 v07 ask/retrieval spec이 있으면 포함
- `0008-v08-ffxiv-domain-graphify-layer-spec.md`
- `0008_5-v08_5-managed-wiki-kb-activation-spec.md` 또는 실제 spec 파일명

만약 v08.5 spec 파일을 repo에 추가한다면 권장 경로는 다음이다.

    docs/specs/0008_5-v08_5-managed-wiki-kb-activation-spec.md

### docs/runbooks/domain-graph-refresh.md 구조

    # Domain Graph Refresh Runbook

    ## Purpose
    ## Preconditions
    ## Step 1. Source summary audit
    ## Step 2. Dry-run rebuild
    ## Step 3. Reset rebuild
    ## Step 4. Graph report
    ## Step 5. Derived wiki generation
    ## Step 6. FTS re-index
    ## Step 7. Ask smoke tests
    ## Step 8. Regression
    ## Troubleshooting
    ## Completion checklist

### docs/runbooks/ask.md 갱신 방향

- graph-aware retrieval이 언제 사용되는지 설명
- `graph/entity_index.json`이 없으면 FTS fallback 된다는 점 설명
- 대표 smoke query 추가
- JSON output에서 contexts, answer, sources 확인 방법 설명

### docs/runbooks/generate-derived-wiki.md 갱신 방향

- legacy `--kind jobs`와 v08 graph-derived wiki mode를 분리해서 설명
- `--dry-run --verbose` 선행 권장
- generation 후 FTS re-index 필요성 명시

### CURRENT_HANDOFF.md 갱신 방향

최종 완료 시 다음을 기록한다.

- Current phase: v08.5 Managed Wiki Knowledge Base Activation completed
- Last completed task: final regression / handoff update
- Next task: wait for maintainer scope; v09 is the official guide DB crawler/item pilot, and log/notebook namespace expansion is v10 future work
- 검증 명령과 결과
- 아직 하지 말 것

### Acceptance criteria

- README가 더 이상 v0.6만 현재 pipeline처럼 보이지 않는다.
- specs README에 v08/v08.5가 현재 spec으로 반영된다.
- domain graph refresh 절차가 runbook 하나로 재현 가능하다.
- handoff가 다음 agent의 첫 진입점 역할을 한다.

---

## 12. Task 9 — Final verification

### 목표

v08.5 완료 전 전체 regression과 smoke test를 수행한다.

### 필수 명령

    python tools/rebuild_domain_graph.py --dry-run --verbose
    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
    python tools/generate_derived_wiki.py --dry-run --verbose
    python tools/ask.py "건브 7.5 변경점 알려줘" --format json
    python tools/ask.py "No Mercy 관련 변경 있어?" --format json
    python -m unittest discover -s tests -p "test_*.py"
    python scripts/check_docs_freshness.py --all
    python scripts/finish_task.py

### 추가 권장 명령

실제 graph count 확인:

    python - <<'PY'
    import sqlite3
    conn = sqlite3.connect('db/ffxiv.sqlite')
    print('node types')
    for row in conn.execute('SELECT type, COUNT(*) FROM graph_nodes GROUP BY type ORDER BY type'):
        print(row)
    print('edge types')
    for row in conn.execute('SELECT type, COUNT(*) FROM graph_edges GROUP BY type ORDER BY type'):
        print(row)
    print('wiki types')
    for row in conn.execute('SELECT wiki_type, COUNT(*) FROM wiki_pages GROUP BY wiki_type ORDER BY wiki_type'):
        print(row)
    conn.close()
    PY

### 완료 조건

- full unittest 통과
- docs freshness 통과
- finish_task 통과
- graph report 생성 성공
- derived wiki dry-run 성공
- ask smoke query JSON 정상 반환
- answer가 source dump가 아니라 요약형 답변
- `CURRENT_HANDOFF.md`에 명령과 결과 기록

---

## 13. 권장 커밋 분해

작업이 크면 다음 단위로 커밋한다.

### Commit 1 — docs: add v08.5 spec and implementation plan

포함 파일:

- `docs/specs/0008_5-v08_5-managed-wiki-kb-activation-spec.md`
- `docs/plans/v08_5/README.md`
- `docs/plans/v08_5/implementation.md`

### Commit 2 — test: add v08.5 activation red tests

포함 파일:

- `tests/test_v08_5_activation.py`
- `tests/test_v08_5_answer_quality.py`

또는 분리:

- `tests/test_v08_5_real_graph_population.py`
- `tests/test_v08_5_real_derived_wiki.py`
- `tests/test_v08_5_fts_visibility.py`
- `tests/test_v08_5_answer_quality.py`

### Commit 3 — feat: activate managed wiki graph refresh workflow

포함 파일:

- 필요한 코드 수정
- `tools/audit_source_summaries.py`를 추가했다면 포함
- graph/derived wiki 관련 버그 수정

### Commit 4 — feat: improve ask summary answer quality

포함 파일:

- `src/answering.py`
- 필요 시 `src/retrieval/context_builder.py`
- 관련 테스트

### Commit 5 — docs: document v08.5 refresh workflow

포함 파일:

- `README.md`
- `docs/specs/README.md`
- `docs/runbooks/domain-graph-refresh.md`
- `docs/runbooks/ask.md`
- `docs/runbooks/generate-derived-wiki.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/reports/*.md`

### Commit 6 — chore: refresh generated graph and wiki artifacts

포함 파일:

- `graph/*.json`
- `graph/GRAPH_REPORT.md`
- `wiki/jobs/*.md`
- `wiki/patches/*.md`
- `wiki/skills/*.md`
- `wiki/index.md`
- `db/ffxiv.sqlite`는 repo 정책에 따라 포함 여부 결정

주의:

- `db/ffxiv.sqlite`가 repo에서 추적 중이면 갱신 포함 여부를 maintainer 정책에 맞춘다.
- generated artifact를 commit하지 않는 정책이면 runbook에 재생성 명령만 남긴다.

---

## 14. agent에게 줄 실행 프롬프트

다음 프롬프트를 그대로 사용할 수 있다.

    Goal: Implement v08.5 — Managed Wiki Knowledge Base Activation for ffxiv-claw-bot.

    Context:
    v08 engine is already implemented. Do not add new BIS, raid, item, crawler, polling, Discord slash command, vector DB, graph DB, or LLM API features. This task is to activate and validate the existing v08 domain graph/wiki/RAG engine against real wiki/source_summaries data and improve answer quality.

    Required order:
    0. Run baseline v08 tests.
    1. Audit wiki/source_summaries and write docs/reports/2026-05-17-v08_5-source-audit.md.
    2. Add red tests for v08.5 graph population, derived wiki generation, FTS visibility, and answer quality.
    3. Run tools/rebuild_domain_graph.py --dry-run --verbose.
    4. Run tools/rebuild_domain_graph.py --reset-domain-graph --verbose.
    5. Verify graph_nodes and graph_edges contain real Job, Patch, Skill, Fact, SourceDocument, WikiPage nodes and required edge types.
    6. Generate graph/GRAPH_REPORT.md and validate node counts, edge counts, top entities, and quality warnings.
    7. Run tools/generate_derived_wiki.py --dry-run --verbose and then tools/generate_derived_wiki.py --verbose.
    8. Re-index wiki documents into SQLite FTS.
    9. Improve ask.py answer quality through answer composer/context handling so answers are structured topic summaries with related entities, confirmed facts, sources, and uncertainty notes, not raw source dumps.
    10. Update README.md, docs/specs/README.md, docs/runbooks/ask.md, docs/runbooks/generate-derived-wiki.md, add docs/runbooks/domain-graph-refresh.md, and update docs/handoff/CURRENT_HANDOFF.md.
    11. Run full regression:
        python -m unittest discover -s tests -p "test_*.py"
        python scripts/check_docs_freshness.py --all
        python scripts/finish_task.py

    Hard constraints:
    - Preserve existing v06/v07/v08 behavior.
    - Do not rewrite the whole retrieval pipeline.
    - Do not add new namespaces yet.
    - Do not call external LLM APIs.
    - Do not introduce vector DB or graph DB.
    - Keep graph retrieval additive; FTS-only fallback must continue to work.
    - Record exact verification commands and results in CURRENT_HANDOFF.md.

    Acceptance criteria:
    - graph/GRAPH_REPORT.md shows nonzero Job, Patch, Skill, and Fact counts.
    - graph/domain_graph.json and graph/entity_index.json exist and reflect real source summaries.
    - wiki/jobs/*.md, wiki/patches/*.md, and wiki/skills/*.md contain at least one generated page each.
    - wiki/index.md links generated derived wiki pages.
    - generated derived wiki pages are indexed into SQLite FTS.
    - ask.py returns structured topic summaries with sources for representative questions:
      python tools/ask.py "건브 7.5 변경점 알려줘" --format json
      python tools/ask.py "No Mercy 관련 변경 있어?" --format json
    - Existing v06/v07/v08 tests continue to pass.
    - CURRENT_HANDOFF.md records v08.5 completion status and exact verification commands/results.

---

## 15. 완료 후 다음 단계

v08.5가 완료된 뒤에야 다음 scope를 검토한다.

우선순위 후보:

1. BIS namespace
2. raid/encounter namespace
3. item/gearset namespace
4. official patch note source workflow
5. stronger relation extraction
6. answer evaluation harness
7. vector search integration
8. graph community summary

단, 위 항목은 v08.5에서 구현하지 않는다.

---

## 16. 최종 체크리스트

완료 전 아래를 모두 체크한다.

- [ ] source summary audit 문서 작성 완료
- [ ] domain graph dry-run 성공
- [ ] domain graph reset rebuild 성공
- [ ] Job node count > 0
- [ ] Patch node count > 0
- [ ] Skill node count > 0
- [ ] Fact node count > 0
- [ ] required edge type count 확인
- [ ] graph export 파일 생성 확인
- [ ] GRAPH_REPORT.md 생성 및 검토 완료
- [ ] graph-derived jobs wiki 생성
- [ ] graph-derived patches wiki 생성
- [ ] graph-derived skills wiki 생성
- [ ] wiki/index.md 갱신 확인
- [ ] FTS 재색인 완료
- [ ] ask smoke query 성공
- [ ] ask answer가 source dump가 아님
- [ ] v08.5 tests 추가 및 통과
- [ ] full unittest 통과
- [ ] docs freshness 통과
- [ ] finish_task 통과
- [ ] README 갱신
- [ ] specs README 갱신
- [ ] domain-graph-refresh runbook 추가
- [ ] ask runbook 갱신
- [ ] generate-derived-wiki runbook 갱신
- [ ] CURRENT_HANDOFF.md 최종 상태 기록
