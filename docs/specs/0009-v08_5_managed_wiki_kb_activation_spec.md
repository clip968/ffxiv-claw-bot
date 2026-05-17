# v08.5 Spec — Managed Wiki Knowledge Base Activation

## 0. 문서 정보

- 문서명: v08.5 Spec — Managed Wiki Knowledge Base Activation
- 대상 프로젝트: ffxiv-claw-bot / FFXIV OpenClaw Bot
- 작성 목적: v08에서 구현된 Domain Graphify Layer, graph-derived wiki, hybrid retrieval 엔진을 실제 source summary 데이터로 채우고, RAG Wiki로서 사용 가능한 답변 품질까지 끌어올린다.
- 상태: Proposed
- 범위: v08 이후 안정화/활성화 단계
- 상위 전제:
  - v08 엔진은 구현되어 있다.
  - `wiki/source_summaries/`에는 정리된 FFXIV source summary가 존재한다.
  - Lost Ark 등 비-FFXIV 오염 데이터는 이미 제거되었다고 가정한다.
  - BIS, 레이드, 아이템 namespace 확장은 이 spec의 범위가 아니다.

---

## 1. 배경

v08까지의 구현으로 다음 엔진은 갖춰졌다.

- entity registry
- entity extractor
- relation/fact extractor
- domain graph storage
- domain graph rebuild CLI
- graph JSON export
- GRAPH_REPORT.md 생성
- graph-derived wiki 생성기
- graph-aware hybrid retrieval
- ask CLI integration
- v08 end-to-end smoke test

그러나 v08 완료만으로 곧바로 “관리되는 RAG Wiki”가 완성되는 것은 아니다.

현재 남은 핵심 과제는 다음이다.

1. 실제 `wiki/source_summaries/`를 기준으로 domain graph를 채운다.
2. `GRAPH_REPORT.md`를 통해 graph 품질을 확인한다.
3. graph-derived `wiki/jobs`, `wiki/patches`, `wiki/skills`를 실제 생성한다.
4. 새 derived wiki를 SQLite FTS에 재색인한다.
5. `ask.py`가 source dump가 아니라 주제별 요약 답변을 하도록 다듬는다.
6. 이 refresh 절차를 runbook으로 고정한다.

즉, v08.5는 새 기능 개발 단계가 아니라 기존 v08 엔진을 실제 지식체로 활성화하는 단계다.

---

## 2. 목표

v08.5의 목표는 다음이다.

```text
v08 graph/wiki/RAG engine
  -> real source summary audit
  -> real domain graph population
  -> graph quality report
  -> graph-derived wiki generation
  -> FTS re-indexing
  -> topic-based grounded answers
  -> documented refresh workflow
```

완료 후 대표 질문은 다음처럼 동작해야 한다.

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
```

기대 답변은 단순 source body 나열이 아니라 다음 구조를 가져야 한다.

```text
요약:
- 핵심 결론

관련 항목:
- Job / Patch / Skill

확인된 내용:
- source에 근거가 있는 fact

근거:
- source summary 또는 derived wiki 경로

주의:
- source가 부족하거나 전체 패치노트 수준으로 단정할 수 없는 경우 명시
```

---

## 3. Non-goals

v08.5에서 하지 않는다.

- 공식 FFXIV 패치노트 실시간 크롤러
- polling/scheduler
- Discord slash command 개편
- BIS namespace 확장
- raid/encounter namespace 확장
- item/gearset namespace 확장
- vector DB 도입
- graph DB 도입
- LLM API 기반 extractor 도입
- GraphRAG community detection
- complex graph visualization
- retrieval pipeline 전체 재작성
- 모든 FFXIV job/skill/item ontology 완성

v08.5는 “더 넓히는 단계”가 아니라 “현재 엔진을 실제 데이터로 채우고 답변 품질을 정리하는 단계”다.

---

## 4. 현재 상태

v08 이후 시스템은 다음 구조를 가진다.

```text
wiki/source_summaries/
  -> entity extraction
  -> relation/fact extraction
  -> db/ffxiv.sqlite graph_nodes / graph_edges
  -> graph/domain_graph.json
  -> graph/entity_index.json
  -> graph/GRAPH_REPORT.md
  -> wiki/jobs/
  -> wiki/patches/
  -> wiki/skills/
  -> SQLite FTS
  -> ask.py hybrid retrieval
```

다만 실제 운영 상태에서는 다음을 확인해야 한다.

- source summary가 충분히 존재하는가?
- source summary가 FFXIV 데이터만 포함하는가?
- actual graph rebuild 결과에서 Job/Patch/Skill/Fact가 0이 아닌가?
- derived wiki 파일이 실제로 생성되는가?
- derived wiki가 FTS 검색 대상에 들어가는가?
- ask 답변이 source dump가 아니라 요약형으로 나오는가?

---

## 5. 성공 기준

v08.5는 다음 조건을 만족하면 완료로 본다.

### 5.1 Source audit criteria

- `wiki/source_summaries/*.md` 개수가 기록된다.
- FFXIV source로 판단되는 파일 개수가 기록된다.
- 제외 또는 수정이 필요한 source summary가 있으면 목록화된다.
- graph rebuild 진행 가능 여부가 명시된다.

### 5.2 Domain graph criteria

- `tools/rebuild_domain_graph.py --reset-domain-graph --verbose`가 성공한다.
- `graph_nodes`에 다음 node type이 1개 이상 존재한다.
  - `SourceDocument`
  - `WikiPage`
  - `Job`
  - `Patch`
  - `Skill`
  - `Fact`
- `graph_edges`에 다음 edge type이 1개 이상 존재한다.
  - `MENTIONS`
  - `SUPPORTS`
  - `AFFECTS_JOB`
  - `AFFECTS_SKILL`
  - `VALID_IN_PATCH`
- 다음 export 파일이 생성된다.
  - `graph/nodes.json`
  - `graph/edges.json`
  - `graph/domain_graph.json`
  - `graph/entity_index.json`
- rebuild를 반복 실행해도 node/edge count가 비정상적으로 증가하지 않는다.

### 5.3 Graph report criteria

- `graph/GRAPH_REPORT.md`가 생성된다.
- report에 node type count가 포함된다.
- report에 edge type count가 포함된다.
- report에 top mentioned entities 또는 top mentioned jobs가 포함된다.
- report에 quality warnings 섹션이 포함된다.
- Job/Patch/Skill/Fact count가 모두 0이 아니다.

### 5.4 Derived wiki criteria

- `tools/generate_derived_wiki.py --verbose`가 성공한다.
- 다음 디렉터리에 최소 1개 이상의 파일이 생성된다.
  - `wiki/jobs/*.md`
  - `wiki/patches/*.md`
  - `wiki/skills/*.md`
- generated wiki 문서에는 related source가 포함된다.
- `wiki/index.md`가 생성된 derived wiki를 링크한다.
- derived wiki 생성은 idempotent하다.

### 5.5 FTS criteria

- generated derived wiki가 `wiki_pages`에 색인된다.
- generated derived wiki가 `wiki_fts`에 색인된다.
- ask 결과 contexts에 `job`, `patch`, `skill`, `source_summary` 중 관련 context가 포함된다.
- source summary fallback은 유지된다.

### 5.6 Answer quality criteria

- `ask.py` 답변은 source body 전체를 단순 덤프하지 않는다.
- 답변에는 요약이 있다.
- 답변에는 관련 엔티티가 있다.
- 답변에는 근거 source가 있다.
- context가 부족하면 부족하다고 말한다.
- graph-derived wiki context와 source summary context를 구분해 사용할 수 있다.
- 기존 v06/v07/v08 regression이 깨지지 않는다.

### 5.7 Documentation criteria

- `README.md`가 v08.5 이후 현재 pipeline을 설명한다.
- `docs/specs/README.md`가 v08/v08.5 spec을 현재 spec 목록에 반영한다.
- `docs/runbooks/domain-graph-refresh.md`가 추가된다.
- `docs/runbooks/ask.md`가 graph-aware ask 사용법을 반영한다.
- `docs/runbooks/generate-derived-wiki.md`가 v08.5 workflow를 반영한다.
- `docs/handoff/CURRENT_HANDOFF.md`에 최종 검증 명령과 결과가 기록된다.

---

## 6. 작업 분해

## Task 1 — Source summary audit

### 목적

graph를 채우기 전에 `wiki/source_summaries/`가 실제 FFXIV 지식체로 사용할 수 있는 상태인지 확인한다.

### 작업

1. `wiki/source_summaries/*.md` 파일 개수를 확인한다.
2. 각 파일에서 source id, title, category, body 존재 여부를 확인한다.
3. 비-FFXIV 데이터가 남아 있는지 확인한다.
4. 너무 짧거나 비어 있는 source summary를 찾는다.
5. 같은 source가 중복되어 있는지 확인한다.
6. audit 결과를 문서화한다.

### 산출물

- `docs/reports/2026-05-17-v08_5-source-audit.md`

### Acceptance criteria

- 총 source summary 개수 기록
- 정상 source summary 개수 기록
- 제외 후보 목록 기록
- 수정 필요 source 목록 기록
- graph rebuild 가능 여부 기록

---

## Task 2 — Actual domain graph rebuild

### 목적

테스트 fixture가 아니라 실제 source summary를 기준으로 domain graph를 채운다.

### 명령

먼저 dry-run을 실행한다.

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
```

dry-run이 정상이면 실제 rebuild를 실행한다.

```bash
python tools/rebuild_domain_graph.py --reset-domain-graph --verbose
```

### 작업

1. rebuild 결과 JSON을 확인한다.
2. DB에서 node type count를 확인한다.
3. DB에서 edge type count를 확인한다.
4. graph export 파일 생성 여부를 확인한다.
5. 같은 명령을 반복 실행했을 때 count가 비정상 증가하지 않는지 확인한다.

### 산출물

- 갱신된 `db/ffxiv.sqlite`
- 갱신된 `graph/nodes.json`
- 갱신된 `graph/edges.json`
- 갱신된 `graph/domain_graph.json`
- 갱신된 `graph/entity_index.json`

### Acceptance criteria

- `Job` count > 0
- `Patch` count > 0
- `Skill` count > 0
- `Fact` count > 0
- `MENTIONS` count > 0
- `SUPPORTS` count > 0
- `AFFECTS_JOB` count > 0 또는 실제 source 부족 사유 문서화
- `AFFECTS_SKILL` count > 0 또는 실제 source 부족 사유 문서화
- `VALID_IN_PATCH` count > 0 또는 실제 source 부족 사유 문서화
- Legacy `SOURCE_OF` edge confidence values such as `EXTRACTED` do not block graph export; they are treated as unknown confidence in exported JSON.

---

## Task 3 — Graph report validation

### 목적

graph가 단순히 생성된 상태인지, 실제로 의미 있는 graph인지 확인한다.

### 명령

```bash
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
```

### 작업

1. `graph/GRAPH_REPORT.md` 존재 여부를 확인한다.
2. node type count를 확인한다.
3. edge type count를 확인한다.
4. top mentioned entities를 확인한다.
5. quality warnings를 확인한다.
6. warning이 있으면 후속 조치 여부를 문서화한다.

### 산출물

- `graph/GRAPH_REPORT.md`
- 필요 시 `docs/reports/2026-05-17-v08_5-graph-report-review.md`

### Acceptance criteria

- `GRAPH_REPORT.md`가 빈 보고서가 아니다.
- Job/Patch/Skill/Fact count가 0이 아니다.
- quality warning이 있으면 무시하지 않고 원인과 처리 방침을 기록한다.

---

## Task 4 — Generate graph-derived wiki

### 목적

domain graph에서 파생된 관리형 wiki 문서를 실제 생성한다.

### 명령

먼저 dry-run을 실행한다.

```bash
python tools/generate_derived_wiki.py --dry-run --verbose
```

정상이면 실제 생성한다.

```bash
python tools/generate_derived_wiki.py --verbose
```

### 작업

1. `wiki/jobs/*.md` 생성 여부 확인
2. `wiki/patches/*.md` 생성 여부 확인
3. `wiki/skills/*.md` 생성 여부 확인
4. 각 문서에 related facts, related entities, related sources가 포함되는지 확인
5. `wiki/index.md`가 derived wiki를 링크하는지 확인
6. 재실행 시 파일 내용이 불필요하게 흔들리지 않는지 확인

### 산출물

- `wiki/jobs/*.md`
- `wiki/patches/*.md`
- `wiki/skills/*.md`
- 갱신된 `wiki/index.md`

### Acceptance criteria

- `wiki/jobs`에 최소 1개 이상 생성
- `wiki/patches`에 최소 1개 이상 생성
- `wiki/skills`에 최소 1개 이상 생성
- 각 generated page에 source link가 포함
- `wiki/index.md`가 generated pages를 링크
- Generated wiki pages under `wiki/jobs`, `wiki/patches`, and `wiki/skills` are local derived outputs and are not committed to Git.

---

## Task 5 — Re-index wiki into SQLite FTS

### 목적

graph-derived wiki가 ask 검색 대상에 포함되도록 SQLite FTS를 재색인한다.

### 명령

```bash
python -c "from tools.compile_wiki import index_wiki_documents; import json; print(json.dumps(index_wiki_documents(), ensure_ascii=False, indent=2))"
```

### 작업

1. `wiki_pages`에 generated wiki가 들어갔는지 확인한다.
2. `wiki_fts`에 generated wiki text가 들어갔는지 확인한다.
3. ask 결과 context에 derived wiki가 등장하는지 확인한다.
4. source summary fallback이 유지되는지 확인한다.

### Acceptance criteria

- generated job wiki가 FTS 대상에 포함된다.
- generated patch wiki가 FTS 대상에 포함된다.
- generated skill wiki가 FTS 대상에 포함된다.
- source summary 검색이 깨지지 않는다.

---

## Task 6 — Improve ask answer quality

### 목적

`ask.py`가 source dump가 아니라 주제별 grounded summary를 반환하도록 개선한다.

### 현재 문제

v08의 retrieval path는 graph-aware로 연결되었지만, 답변 품질이 낮으면 사용자는 RAG Wiki가 아니라 source dump처럼 느낄 수 있다.

### 목표 답변 구조

`compose_answer()` 또는 context builder 단계에서 답변을 다음 구조로 정리한다.

```text
요약:
- 질문에 대한 핵심 답변

관련 항목:
- Job: ...
- Patch: ...
- Skill: ...

확인된 내용:
- source에 근거가 있는 fact

근거:
- wiki/source_summaries/...
- wiki/jobs/...
- wiki/patches/...
- wiki/skills/...

주의:
- source가 부족한 경우
- 일부 정보가 derived wiki 기반인 경우
- 전체 패치노트 전체를 대표한다고 단정할 수 없는 경우
```

### 수정 대상 후보

- `src/answering.py`
- `src/retrieval/context_builder.py`
- `tools/ask.py`

### 작업

1. 현재 answer composer가 source body를 얼마나 직접 출력하는지 확인한다.
2. context type별로 요약에 활용할 정보를 분리한다.
3. source summary와 derived wiki를 구분해 표시한다.
4. related entity 정보를 답변에 반영한다.
5. context 부족 시 uncertainty note를 출력한다.
6. 기존 JSON 출력 구조는 유지한다.

### Acceptance criteria

- answer body가 raw source dump가 아니다.
- answer body에 `요약` 또는 이에 준하는 section이 포함된다.
- answer body에 related entity가 포함된다.
- answer body에 source path 또는 source id가 포함된다.
- context 부족 시 부족하다고 명시한다.
- `--format text` 동작이 유지된다.
- 기존 ask CLI tests가 깨지지 않는다.

---

## Task 7 — Add v08.5 tests

### 목적

v08.5에서 추가된 실제 graph population, derived wiki activation, answer quality를 regression으로 고정한다.

### 테스트 파일 후보

- `tests/test_v08_5_real_graph_population.py`
- `tests/test_v08_5_real_derived_wiki.py`
- `tests/test_v08_5_answer_quality.py`

### 테스트 항목

#### test_v08_5_real_graph_population.py

1. source summary fixture를 기반으로 rebuild 실행
2. Job/Patch/Skill/Fact node 생성 확인
3. MENTIONS/SUPPORTS/VALID_IN_PATCH edge 생성 확인
4. graph export 파일 생성 확인
5. rebuild idempotency 확인

#### test_v08_5_real_derived_wiki.py

1. graph fixture 기반으로 generated wiki 생성
2. jobs/patches/skills page 생성 확인
3. generated page에 related source 포함 확인
4. `wiki/index.md` 링크 확인
5. idempotency 확인

#### test_v08_5_answer_quality.py

1. ask answer가 source body 전체를 그대로 덤프하지 않는지 확인
2. 요약형 구조 포함 확인
3. related entity 포함 확인
4. sources 포함 확인
5. 부족한 context일 때 uncertainty note 확인

### Acceptance criteria

- 새 테스트는 red test로 먼저 실패해야 한다.
- 구현 후 새 테스트가 통과해야 한다.
- 기존 v06/v07/v08 테스트가 유지되어야 한다.

---

## Task 8 — Documentation and runbook update

### 목적

새 세션이나 agent가 같은 workflow를 반복할 수 있게 문서화한다.

### 추가 문서

- `docs/runbooks/domain-graph-refresh.md`

### 갱신 문서

- `README.md`
- `docs/specs/README.md`
- `docs/runbooks/ask.md`
- `docs/runbooks/generate-derived-wiki.md`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/plans/v08/README.md` 또는 새 `docs/plans/v08_5/README.md`

### domain-graph-refresh runbook 구조

```text
1. Source summary audit
2. Dry-run domain graph rebuild
3. Actual domain graph rebuild
4. Graph report generation
5. Graph report review
6. Graph-derived wiki generation
7. FTS re-indexing
8. Ask smoke test
9. Full regression
10. Handoff update
```

### Acceptance criteria

- README가 v0.6 중심으로만 보이지 않는다.
- specs README에 v08/v08.5가 현재 spec으로 표시된다.
- domain graph refresh 절차가 한 문서에서 재현 가능하다.
- CURRENT_HANDOFF.md에 v08.5 완료 상태와 검증 결과가 남는다.

---

## Task 9 — Final verification

### 목적

v08.5 완료 전 전체 regression과 smoke test를 수행한다.

### 필수 명령

```bash
python tools/rebuild_domain_graph.py --dry-run --verbose
python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph
python tools/generate_derived_wiki.py --dry-run --verbose
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python -m unittest discover -s tests -p "test_*.py"
python scripts/check_docs_freshness.py --all
python scripts/finish_task.py
```

### 완료 기록

`docs/handoff/CURRENT_HANDOFF.md`에 다음을 기록한다.

- 완료 phase: v08.5 Managed Wiki Knowledge Base Activation completed
- 마지막 완료 task
- 실행한 검증 명령
- 각 명령의 결과
- 다음 작업: v09 scope 대기 또는 namespace 확장 검토
- 아직 하지 말 것:
  - BIS namespace 확장
  - raid namespace 확장
  - item namespace 확장
  - crawling/polling
  - vector DB / graph DB

---

## 7. 대표 smoke query

v08.5 완료 후 최소 다음 질문을 확인한다.

```bash
python tools/ask.py "건브 7.5 변경점 알려줘" --format json
python tools/ask.py "No Mercy 관련 변경 있어?" --format json
python tools/ask.py "7.5에서 어떤 직업이 언급됐어?" --format json
python tools/ask.py "건브 관련 source 보여줘" --format json
```

각 결과는 다음 조건을 만족해야 한다.

- `status = ok`
- `contexts`가 비어 있지 않다.
- source summary 또는 derived wiki context가 포함된다.
- answer body가 source dump가 아니다.
- sources가 포함된다.
- context 부족 시 부족하다고 말한다.

---

## 8. 완료 후 다음 단계

v08.5가 완료된 뒤에야 다음 확장을 검토한다.

우선순위 후보:

1. BIS namespace
2. raid/encounter namespace
3. item/gearset namespace
4. official patch note source workflow
5. stronger relation extraction
6. answer evaluation harness
7. vector search integration
8. graph community summary

단, 이 spec에서는 위 항목을 구현하지 않는다.

---

## 9. Agent handoff prompt

아래 프롬프트를 다음 agent에게 줄 수 있다.

```text
Goal: Implement v08.5 — Managed Wiki Knowledge Base Activation for ffxiv-claw-bot.

Context:
v08 engine is already implemented. Do not add new BIS, raid, item, crawler, polling, Discord slash command, vector DB, graph DB, or LLM API features. This task is to activate and validate the existing v08 domain graph/wiki/RAG engine against real wiki/source_summaries data and improve answer quality.

Tasks:
1. Audit wiki/source_summaries and write docs/reports/2026-05-17-v08_5-source-audit.md.
2. Run tools/rebuild_domain_graph.py --dry-run --verbose.
3. Run tools/rebuild_domain_graph.py --reset-domain-graph --verbose.
4. Verify graph_nodes and graph_edges contain real Job, Patch, Skill, Fact, SourceDocument, WikiPage nodes and required edge types.
5. Generate graph/GRAPH_REPORT.md and validate node counts, edge counts, top entities, and quality warnings.
6. Run tools/generate_derived_wiki.py --dry-run --verbose and then tools/generate_derived_wiki.py --verbose.
7. Re-index wiki documents into SQLite FTS.
8. Improve ask.py answer quality so answers are structured topic summaries with related entities, confirmed facts, sources, and uncertainty notes, not raw source dumps.
9. Add red tests for real graph population, derived wiki generation, FTS visibility, and answer quality before implementing behavior changes.
10. Update README.md, docs/specs/README.md, docs/runbooks/ask.md, docs/runbooks/generate-derived-wiki.md, add docs/runbooks/domain-graph-refresh.md, and update docs/handoff/CURRENT_HANDOFF.md.
11. Run full regression:
    python -m unittest discover -s tests -p "test_*.py"
    python scripts/check_docs_freshness.py --all
    python scripts/finish_task.py

Acceptance criteria:
- graph/GRAPH_REPORT.md shows nonzero Job, Patch, Skill, and Fact counts.
- graph/domain_graph.json and graph/entity_index.json exist and reflect real source summaries.
- wiki/jobs/*.md, wiki/patches/*.md, and wiki/skills/*.md contain at least one generated page each.
- wiki/index.md links generated derived wiki pages.
- ask.py returns structured topic summaries with sources for representative questions:
  python tools/ask.py "건브 7.5 변경점 알려줘" --format json
  python tools/ask.py "No Mercy 관련 변경 있어?" --format json
- Existing v06/v07/v08 tests continue to pass.
- CURRENT_HANDOFF.md records v08.5 completion status and exact verification commands/results.
```

---

## 10. 핵심 요약

v08.5의 핵심은 다음이다.

```text
새 기능 추가 금지
-> 실제 graph 채우기
-> graph report로 품질 확인
-> graph-derived wiki 생성
-> FTS 재색인
-> ask 답변 품질 개선
-> runbook/handoff 고정
```

이 단계가 끝나야 ffxiv-claw-bot은 단순한 RAG 엔진이 아니라 “관리되는 wiki 지식체”로 운영 가능한 상태가 된다.
