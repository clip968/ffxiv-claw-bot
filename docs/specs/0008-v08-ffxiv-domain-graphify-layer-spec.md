# v08 Spec — FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval

## 0. 문서 정보

- 문서명: v08 Spec — FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval
- 대상 프로젝트: ffxiv-claw-bot / FFXIV OpenClaw Bot
- 상태: In Progress (v08-02 completed)
- 목적: 현재 FTS 기반 RAG + provenance graph 구조를 FFXIV 도메인 entity graph 기반 RAG로 확장한다.
- 전제: Lost Ark 등 비-FFXIV 오염 데이터 정리는 이미 완료되었다고 가정한다.

---

## 1. 배경

현재 시스템은 다음 구조를 가진다.

- `wiki/source_summaries/`: source별 요약 문서
- `wiki/jobs/`: 직업별 derived wiki 자리. 현재 실질 데이터 없음 또는 매우 제한적
- `wiki/index.md`: wiki index
- `db/ffxiv.sqlite`: `sources`, `wiki_pages`, `wiki_fts`, `graph_nodes`, `graph_edges` 저장
- `graph/nodes.json`, `graph/edges.json`: DB graph export/cache

현재 graph는 대부분 다음 형태다.

- `SourceDocument -> SOURCE_OF -> WikiPage`

즉, 현재 graph는 도메인 의미 그래프라기보다 source와 wiki page 간 출처 추적 그래프에 가깝다.

현재 retrieval은 주로 SQLite FTS5 기반이다.

현재 구조:

    user question
      -> SQLite FTS
      -> source summary / wiki page context
      -> grounded answer

v08의 목표 구조:

    user question
      -> entity matcher
      -> FFXIV domain graph traversal
      -> FTS retrieval
      -> evidence merge/rank
      -> grounded answer

Graphify를 그대로 붙이는 것이 아니라, Graphify의 핵심 형태를 FFXIV 도메인에 맞게 재구성한다.

Graphify에서 차용할 요소:

- graph export
- graph report
- entity/relation 중심 memory layer
- graph-first context navigation
- raw source를 매번 직접 뒤지는 대신 graph를 통해 관련 context를 찾는 방식

Graphify를 그대로 사용하지 않는 이유:

- FFXIV는 Job, Patch, Skill, Item, GearSet, Encounter 같은 도메인 ontology가 필요하다.
- 패치 버전별 유효성 관리가 필요하다.
- 출처 기반 fact 검증이 필요하다.
- ask pipeline에서 entity normalization과 graph traversal을 직접 제어해야 한다.
- `graphify-out/`을 source of truth로 쓰면 현재 `db/ffxiv.sqlite`, `wiki/`, `graph/` 구조와 충돌한다.

---

## 2. v08 목표

v08의 목표는 다음이다.

    v08 = FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval

구체적으로는 다음을 구현한다.

1. FFXIV entity registry 추가
2. source summary 기반 entity extraction 구현
3. relation/fact extraction 구현
4. graph schema 확장
5. source summary -> domain graph rebuild 구현
6. derived wiki 자동 생성
   - `wiki/jobs/`
   - `wiki/patches/`
   - `wiki/skills/`
7. Graphify-style report/export 생성
   - `graph/GRAPH_REPORT.md`
   - `graph/domain_graph.json`
   - `graph/entity_index.json`
8. ask pipeline에 graph-aware retrieval 추가
9. extractor / graph rebuild / derived wiki / retrieval 테스트 추가

---

## 3. Non-goals

v08에서 하지 않는다.

- 공식 FFXIV 패치노트 실시간 크롤러
- Discord command 전체 개편
- BIS, opener, rotation 전체 자동 생성
- 모든 FFXIV 아이템/음식/마테리아 ontology 완성
- LLM 기반 extractor의 production-grade 완성
- 복잡한 graph visualization HTML 구현
- community detection 기반 Graphify clone 구현
- graph DB 도입
- vector DB 도입

v08은 graph 구조와 retrieval 연결을 만드는 단계다. “모든 도메인 지식을 완성”하는 단계가 아니다.

---

## 4. 현재 상태와 v08 이후 상태

### 4.1 현재 상태

    source_summaries
      -> wiki_pages
      -> SQLite FTS
      -> shallow provenance graph

그래프 의미:

    SourceDocument
      -> SOURCE_OF
      -> WikiPage

### 4.2 v08 이후 상태

    source_summaries
      -> entity extraction
      -> relation/fact extraction
      -> FFXIV domain graph
      -> derived wiki
      -> graph report/export
      -> graph-aware retrieval
      -> FTS + graph hybrid context

그래프 의미:

    SourceDocument
      -> SUPPORTS
      -> Fact

    Fact
      -> ABOUT
      -> Job / Skill / Patch / Item / Encounter

    WikiPage
      -> DERIVED_FROM
      -> SourceDocument

    WikiPage
      -> MENTIONS
      -> Job / Skill / Patch

    Job
      -> HAS_SKILL
      -> Skill

    Fact
      -> VALID_IN_PATCH
      -> Patch

---

## 5. 핵심 설계 원칙

### 5.1 DB가 source of truth다

`db/ffxiv.sqlite`의 graph tables를 source of truth로 둔다.

`graph/*.json`과 `graph/GRAPH_REPORT.md`는 export/cache/report 산출물이다.

### 5.2 source summary는 증거 단위다

`wiki/source_summaries/*.md`는 source별 evidence layer다.

Derived wiki는 source summary를 대체하지 않는다. Derived wiki는 source summary와 graph에서 파생된다.

### 5.3 relation은 보수적으로 생성한다

명시적 근거가 없는 relation은 만들지 않는다.

초기 relation은 `MENTIONS`, `SUPPORTED_BY`, `DERIVED_FROM`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL`, `HAS_SKILL` 중심으로 제한한다.

### 5.4 alias normalization이 필수다

사용자는 같은 대상을 여러 방식으로 부른다.

예:

- Gunbreaker
- GNB
- 건브
- 건브레이커

따라서 entity registry를 통해 canonical node로 정규화한다.

### 5.5 graph retrieval은 FTS를 대체하지 않는다

v08에서 graph retrieval은 FTS를 보완한다.

최종 context는 다음 둘을 병합한다.

- FTS result
- graph neighborhood result

---

## 6. 데이터 모델

### 6.1 Node types

v08에서 지원할 node type:

- `SourceDocument`
- `WikiPage`
- `Job`
- `Patch`
- `Skill`
- `Item`
- `GearSet`
- `Encounter`
- `Fact`

v08 최소 구현 대상:

- `SourceDocument`
- `WikiPage`
- `Job`
- `Patch`
- `Skill`
- `Fact`

`Item`, `GearSet`, `Encounter`는 schema만 열어두고 extractor coverage는 제한적으로 둔다.

### 6.2 Edge types

v08에서 지원할 edge type:

- `SOURCE_OF`
- `DERIVED_FROM`
- `MENTIONS`
- `SUPPORTED_BY`
- `ABOUT`
- `VALID_IN_PATCH`
- `AFFECTS_JOB`
- `AFFECTS_SKILL`
- `HAS_SKILL`
- `RELATED_TO`

선택 확장:

- `INTRODUCED_IN`
- `REMOVED_IN`
- `BUFFED_IN`
- `NERFED_IN`
- `USES_ITEM`
- `HAS_GEARSET`
- `MENTIONED_IN`

초기에는 `BUFFED_IN`, `NERFED_IN`을 남발하지 않는다. buff/nerf 판단은 해석이 들어가므로 명확한 근거가 있을 때만 사용한다.

---

## 7. DB schema 확장

기존 `graph_nodes`, `graph_edges`가 있다면 destructive migration 대신 additive migration을 우선한다.

### 7.1 graph_nodes 권장 컬럼

- `id`: TEXT PRIMARY KEY
- `type`: TEXT NOT NULL
- `name`: TEXT NOT NULL
- `canonical_name`: TEXT
- `aliases_json`: TEXT
- `properties_json`: TEXT
- `created_at`: TEXT
- `updated_at`: TEXT

Node id 규칙:

- `src:<source_id>`
- `page:<wiki_page_id_or_path_slug>`
- `job:<canonical_slug>`
- `patch:<version_slug>`
- `skill:<canonical_slug>`
- `item:<canonical_slug>`
- `gearset:<canonical_slug>`
- `encounter:<canonical_slug>`
- `fact:<stable_hash>`

예:

- `job:gunbreaker`
- `patch:7_5`
- `skill:no_mercy`
- `fact:8f23a1e9c2d4`

### 7.2 graph_edges 권장 컬럼

- `id`: TEXT PRIMARY KEY
- `source_node_id`: TEXT NOT NULL
- `target_node_id`: TEXT NOT NULL
- `relation_type`: TEXT NOT NULL
- `properties_json`: TEXT
- `source_id`: TEXT
- `confidence`: REAL
- `created_at`: TEXT
- `updated_at`: TEXT

Edge id 규칙:

    edge:<hash(source_node_id, relation_type, target_node_id, source_id)>

### 7.3 Fact node properties

`Fact` node의 `properties_json` 예:

    {
      "text": "No Mercy is mentioned as changed in Patch 7.5.",
      "subject": "skill:no_mercy",
      "relation": "CHANGED_IN",
      "object": "patch:7_5",
      "evidence_source_ids": ["local_a5f56616236f"],
      "evidence_page_ids": ["wiki_local_a5f56616236f"],
      "confidence": 0.82,
      "valid_from_patch": "7.5",
      "valid_until_patch": null,
      "extraction_method": "rule_based_v1"
    }

### 7.4 Index 권장

- `graph_nodes(type)`
- `graph_nodes(canonical_name)`
- `graph_edges(source_node_id)`
- `graph_edges(target_node_id)`
- `graph_edges(relation_type)`
- `graph_edges(source_id)`

---

## 8. Entity registry

### 8.1 경로

새 디렉터리:

    data/ffxiv_entities/

권장 파일:

    data/ffxiv_entities/jobs.json
    data/ffxiv_entities/skills.json
    data/ffxiv_entities/patches.json
    data/ffxiv_entities/items.json
    data/ffxiv_entities/encounters.json

v08 필수:

    jobs.json
    skills.json
    patches.json

v08 선택:

    items.json
    encounters.json

### 8.2 jobs.json 예시

    [
      {
        "type": "Job",
        "canonical": "Gunbreaker",
        "slug": "gunbreaker",
        "aliases": ["Gunbreaker", "GNB", "건브", "건브레이커"],
        "role": "Tank"
      },
      {
        "type": "Job",
        "canonical": "Paladin",
        "slug": "paladin",
        "aliases": ["Paladin", "PLD", "나이트", "팔라딘"],
        "role": "Tank"
      }
    ]

### 8.3 skills.json 예시

    [
      {
        "type": "Skill",
        "canonical": "No Mercy",
        "slug": "no_mercy",
        "aliases": ["No Mercy", "노 머시", "노머시"],
        "job": "Gunbreaker"
      },
      {
        "type": "Skill",
        "canonical": "Continuation",
        "slug": "continuation",
        "aliases": ["Continuation", "컨티뉴에이션"],
        "job": "Gunbreaker"
      }
    ]

### 8.4 patches.json 예시

    [
      {
        "type": "Patch",
        "canonical": "Patch 7.5",
        "slug": "7_5",
        "aliases": ["7.5", "Patch 7.5", "패치 7.5"]
      }
    ]

---

## 9. Entity extraction

### 9.1 입력

- `wiki/source_summaries/*.md`
- `wiki_pages` table
- 필요시 `sources` table의 title/body/path metadata

### 9.2 출력

각 source 또는 wiki page 기준으로 추출된 entity 목록.

예:

    {
      "source_id": "local_a5f56616236f",
      "entities": [
        {
          "node_id": "job:gunbreaker",
          "type": "Job",
          "canonical": "Gunbreaker",
          "matched_alias": "건브"
        },
        {
          "node_id": "skill:no_mercy",
          "type": "Skill",
          "canonical": "No Mercy",
          "matched_alias": "No Mercy"
        },
        {
          "node_id": "patch:7_5",
          "type": "Patch",
          "canonical": "Patch 7.5",
          "matched_alias": "7.5"
        }
      ]
    }

### 9.3 기본 방식

v08에서는 deterministic dictionary 기반 extractor를 기본으로 한다.

규칙:

1. entity registry를 로드한다.
2. alias를 normalize한다.
3. 긴 alias 우선으로 매칭한다.
4. 대소문자 normalization을 적용한다.
5. 영어/한국어 alias를 모두 지원한다.
6. 같은 canonical entity는 중복 생성하지 않는다.

### 9.4 LLM extraction은 optional

LLM extractor는 v08에서 optional로 둔다.

권장 구조:

- rule-based extractor: 기본
- llm extractor: optional enrichment
- final graph write: confidence와 extraction method를 함께 저장

---

## 10. Relation / Fact extraction

### 10.1 기본 relation

#### MENTIONS

source 또는 wiki page가 entity를 언급하면 생성한다.

    SourceDocument:X -> MENTIONS -> Job:Gunbreaker
    SourceDocument:X -> MENTIONS -> Skill:No Mercy
    WikiPage:Y -> MENTIONS -> Patch:7.5

#### HAS_SKILL

skills registry에서 job이 명시되어 있으면 생성한다.

    Job:Gunbreaker -> HAS_SKILL -> Skill:No Mercy

#### DERIVED_FROM

derived wiki page가 source summary에서 생성되었으면 생성한다.

    WikiPage:jobs/gunbreaker -> DERIVED_FROM -> SourceDocument:X

#### SUPPORTED_BY

Fact가 source에 의해 뒷받침되면 생성한다.

    Fact:Y -> SUPPORTED_BY -> SourceDocument:X

또는 방향을 통일하고 싶다면 다음을 사용한다.

    SourceDocument:X -> SUPPORTS -> Fact:Y

v08에서는 하나의 방향을 정한다. 권장 방향은 다음이다.

    SourceDocument -> SUPPORTS -> Fact

#### VALID_IN_PATCH

Fact가 특정 patch에 유효하면 생성한다.

    Fact:Y -> VALID_IN_PATCH -> Patch:7.5

#### AFFECTS_JOB / AFFECTS_SKILL

Fact가 특정 job 또는 skill에 영향을 주면 생성한다.

    Fact:Y -> AFFECTS_JOB -> Job:Gunbreaker
    Fact:Y -> AFFECTS_SKILL -> Skill:No Mercy

### 10.2 Fact 생성 조건

Fact node는 아무 문장에나 만들지 않는다.

v08에서 Fact를 생성하는 조건:

1. source summary에 Patch entity가 있다.
2. Job 또는 Skill entity가 있다.
3. 변경/효과/유효성에 해당하는 trigger word가 있다.

Trigger word 예:

영어:

- changed
- adjusted
- potency
- recast
- duration
- effect
- added
- removed
- increased
- decreased
- now
- no longer

한국어:

- 변경
- 조정
- 위력
- 재사용
- 지속시간
- 효과
- 추가
- 삭제
- 증가
- 감소
- 더 이상
- 이제

초기 구현은 보수적으로 한다. trigger가 없으면 Fact를 만들지 않고 `MENTIONS`만 만든다.

### 10.3 confidence

권장 confidence:

- registry-derived relation: 1.0
- exact alias mention: 0.9
- rule-based fact with clear patch + trigger: 0.75 ~ 0.9
- co-occurrence only relation: 0.4 ~ 0.6

v08에서 co-occurrence relation은 `RELATED_TO`로만 저장하고 답변 근거로 직접 쓰지 않는다.

---

## 11. Domain graph rebuild

### 11.1 명령

새 CLI 권장:

    python tools/rebuild_domain_graph.py

선택 옵션:

    --db-path db/ffxiv.sqlite
    --wiki-root wiki
    --entities-dir data/ffxiv_entities
    --graph-dir graph
    --dry-run
    --source-id <source_id>
    --reset-domain-graph
    --verbose

### 11.2 동작

1. DB 연결
2. entity registry 로드
3. source summaries 로드
4. 기존 SourceDocument/WikiPage provenance graph 보존
5. Job/Patch/Skill node upsert
6. source summary별 entity extraction
7. `MENTIONS` edge 생성
8. registry 기반 `HAS_SKILL` edge 생성
9. rule 기반 Fact 생성
10. Fact 관련 edge 생성
11. `graph/nodes.json`, `graph/edges.json`, `graph/domain_graph.json` export
12. `graph/entity_index.json` 생성
13. `graph/GRAPH_REPORT.md` 생성

### 11.3 idempotency

같은 입력으로 여러 번 실행해도 node/edge가 중복 생성되면 안 된다.

필수 조건:

- node id deterministic
- edge id deterministic
- fact id deterministic

Fact id는 다음 요소의 hash로 만든다.

    source_id + subject_node_id + relation + object_node_id + normalized_fact_text

---

## 12. Derived wiki generation

### 12.1 명령

새 CLI 권장:

    python tools/generate_derived_wiki.py

선택 옵션:

    --db-path db/ffxiv.sqlite
    --wiki-root wiki
    --graph-dir graph
    --types jobs,patches,skills
    --dry-run
    --verbose

### 12.2 생성 대상

v08 필수:

    wiki/jobs/
    wiki/patches/
    wiki/skills/

### 12.3 Job wiki 구조

파일 예:

    wiki/jobs/gunbreaker.md

문서 구조:

    # Gunbreaker

    ## Summary
    Current KB-level summary for Gunbreaker.

    ## Related Patches
    - Patch 7.5

    ## Skills
    - No Mercy
    - Continuation

    ## Recent Facts
    - ...

    ## Related Sources
    - source_id: ...

    ## Graph Links
    - Job:Gunbreaker -> HAS_SKILL -> Skill:No Mercy
    - Fact:... -> AFFECTS_JOB -> Job:Gunbreaker

### 12.4 Patch wiki 구조

파일 예:

    wiki/patches/7_5.md

문서 구조:

    # Patch 7.5

    ## Summary
    Current KB-level summary for Patch 7.5.

    ## Affected Jobs
    - Gunbreaker
    - Paladin

    ## Affected Skills
    - No Mercy
    - Continuation

    ## Facts
    - ...

    ## Related Sources
    - source_id: ...

### 12.5 Skill wiki 구조

파일 예:

    wiki/skills/no_mercy.md

문서 구조:

    # No Mercy

    ## Summary
    Current KB-level summary for No Mercy.

    ## Job
    - Gunbreaker

    ## Related Patches
    - Patch 7.5

    ## Facts
    - ...

    ## Related Sources
    - source_id: ...

### 12.6 source linking

Derived wiki는 반드시 related source를 포함해야 한다.

문서 내부에 최소한 다음 중 하나를 포함한다.

- source id
- source title
- source summary path
- wiki page path

---

## 13. Graph export / report

### 13.1 출력 파일

v08에서 생성할 파일:

    graph/nodes.json
    graph/edges.json
    graph/domain_graph.json
    graph/entity_index.json
    graph/GRAPH_REPORT.md

### 13.2 domain_graph.json 구조

권장 구조:

    {
      "metadata": {
        "generated_at": "...",
        "node_count": 123,
        "edge_count": 456,
        "schema_version": "v08"
      },
      "nodes": [...],
      "edges": [...]
    }

### 13.3 entity_index.json 구조

질문에서 entity matching을 빠르게 하기 위한 alias index.

예:

    {
      "gunbreaker": "job:gunbreaker",
      "gnb": "job:gunbreaker",
      "건브": "job:gunbreaker",
      "no mercy": "skill:no_mercy",
      "7.5": "patch:7_5"
    }

### 13.4 GRAPH_REPORT.md 내용

필수 섹션:

    # FFXIV Graph Report

    ## Summary
    - sources
    - wiki_pages
    - graph_nodes
    - graph_edges
    - facts

    ## Node Counts
    - SourceDocument
    - WikiPage
    - Job
    - Patch
    - Skill
    - Fact

    ## Edge Counts
    - MENTIONS
    - HAS_SKILL
    - SUPPORTS
    - VALID_IN_PATCH
    - AFFECTS_JOB
    - AFFECTS_SKILL
    - DERIVED_FROM

    ## Top Mentioned Jobs

    ## Top Mentioned Patches

    ## Top Mentioned Skills

    ## Quality Warnings
    - sources without extracted entities
    - facts without supporting sources
    - facts without patch
    - entities without mentions
    - ambiguous aliases

---

## 14. Graph-aware retrieval

### 14.1 목표

v08에서는 ask pipeline을 완전히 재작성하지 않는다.

기존 FTS retrieval을 유지하되, graph neighborhood retrieval을 추가한다.

기존:

    question
      -> FTS search
      -> answer context

v08:

    question
      -> entity matching
      -> graph neighborhood retrieval
      -> FTS search
      -> merge/rank evidence
      -> answer context

### 14.2 query entity matching

입력:

    "건브 7.5 변경점 알려줘"

출력:

    [
      "job:gunbreaker",
      "patch:7_5"
    ]

matching은 `graph/entity_index.json` 또는 DB graph node aliases를 사용한다.

### 14.3 graph neighborhood retrieval

초기 구현은 1-hop 또는 2-hop으로 제한한다.

권장 우선순위:

1. matched entity와 직접 연결된 Fact
2. Fact를 support하는 SourceDocument
3. matched entity와 연결된 WikiPage
4. matched entity와 연결된 Skill/Job/Patch
5. derived wiki page

예:

    Job:Gunbreaker
      <- AFFECTS_JOB <- Fact:Y
      <- MENTIONS <- SourceDocument:X
      -> HAS_SKILL -> Skill:NoMercy

    Fact:Y
      -> VALID_IN_PATCH -> Patch:7.5
      <- SUPPORTS <- SourceDocument:X

### 14.4 FTS result와 병합

병합 기준:

- source_id 중복 제거
- wiki_page 중복 제거
- graph result는 entity match가 강하면 가중치 부여
- FTS result는 lexical relevance 유지
- 공식 source가 있다면 우선순위 부여할 수 있도록 확장 가능

권장 ranking 요소:

    score = fts_score + graph_boost + entity_overlap_boost + source_quality_boost - staleness_penalty

v08에서는 단순 구현으로 충분하다.

예:

- FTS top 5
- graph-derived source/wiki top 5
- 중복 제거 후 최대 8개 context 사용

---

## 15. Ask pipeline 변경 범위

기존 `tools/ask.py` 또는 equivalent ask module을 유지한다.

추가할 내부 함수 예:

- `load_entity_index()`
- `match_query_entities(question)`
- `retrieve_graph_neighborhood(entity_ids)`
- `merge_retrieval_results(fts_results, graph_results)`
- `build_answer_context(merged_results)`

v08 완료 시 다음 질문에서 graph path가 작동해야 한다.

    건브 7.5 변경점 알려줘
    No Mercy 관련 변경 있어?
    7.5에서 어떤 직업이 언급됐어?
    건브 관련 source 보여줘

---

## 16. 테스트 계획

### 16.1 test_entity_extractor.py

필수 테스트:

1. `Gunbreaker`, `GNB`, `건브`, `건브레이커`가 모두 `job:gunbreaker`로 정규화된다.
2. `No Mercy`가 `skill:no_mercy`로 정규화된다.
3. `7.5`, `Patch 7.5`, `패치 7.5`가 `patch:7_5`로 정규화된다.
4. 같은 entity가 한 문서에 여러 번 나와도 중복 extraction되지 않는다.

### 16.2 test_relation_extractor.py

필수 테스트:

1. source summary에 Job이 있으면 `SourceDocument -> MENTIONS -> Job` edge가 생성된다.
2. source summary에 Skill이 있으면 `SourceDocument -> MENTIONS -> Skill` edge가 생성된다.
3. registry에 job-skill 관계가 있으면 `Job -> HAS_SKILL -> Skill` edge가 생성된다.
4. patch + skill + change trigger가 있으면 Fact node가 생성된다.
5. Fact가 Patch, Job, Skill, SourceDocument와 연결된다.

### 16.3 test_domain_graph_rebuild.py

필수 테스트:

1. rebuild를 두 번 실행해도 node/edge 수가 증가하지 않는다.
2. `--source-id` 옵션이 특정 source만 처리한다.
3. `--dry-run`은 DB를 변경하지 않는다.
4. domain node와 provenance node가 공존한다.
5. graph export 파일이 생성된다.

### 16.4 test_derived_wiki.py

필수 테스트:

1. `wiki/jobs/gunbreaker.md`가 생성된다.
2. job wiki에 related skills가 들어간다.
3. job wiki에 related sources가 들어간다.
4. `wiki/patches/7_5.md`가 생성된다.
5. `wiki/skills/no_mercy.md`가 생성된다.
6. derived wiki 생성이 idempotent하다.

### 16.5 test_graph_report.py

필수 테스트:

1. `graph/GRAPH_REPORT.md`가 생성된다.
2. node type count가 포함된다.
3. edge type count가 포함된다.
4. top mentioned jobs가 포함된다.
5. quality warnings 섹션이 포함된다.

### 16.6 test_hybrid_retrieval.py

필수 테스트:

1. 질문 `"건브 7.5 변경점 알려줘"`에서 `job:gunbreaker`, `patch:7_5`가 추출된다.
2. graph retrieval이 관련 Fact 또는 SourceDocument를 반환한다.
3. FTS result와 graph result가 병합된다.
4. 중복 source가 제거된다.
5. graph 결과가 없어도 FTS-only fallback이 작동한다.

---

## 17. Acceptance criteria

v08은 다음 조건을 만족하면 완료로 본다.

### 17.1 Graph criteria

- `graph_nodes`에 `Job`, `Patch`, `Skill`, `Fact` node가 생성된다.
- `graph_edges`에 `MENTIONS`, `HAS_SKILL`, `SUPPORTS`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL`, `DERIVED_FROM` edge가 생성된다.
- `graph/nodes.json`, `graph/edges.json`, `graph/domain_graph.json`, `graph/entity_index.json`이 생성된다.
- rebuild가 idempotent하다.

### 17.2 Wiki criteria

- `wiki/jobs/*.md`가 최소 1개 이상 생성된다.
- `wiki/patches/*.md`가 최소 1개 이상 생성된다.
- `wiki/skills/*.md`가 최소 1개 이상 생성된다.
- derived wiki에는 related source가 포함된다.
- `wiki/index.md`가 derived wiki를 링크하도록 갱신된다.

### 17.3 Retrieval criteria

- 질문에서 entity를 추출할 수 있다.
- graph neighborhood retrieval을 수행할 수 있다.
- graph result와 FTS result를 병합할 수 있다.
- graph result가 없으면 기존 FTS-only 동작으로 fallback한다.

### 17.4 Report criteria

- `graph/GRAPH_REPORT.md`가 생성된다.
- node count, edge count, top entities, quality warnings가 포함된다.

### 17.5 Test criteria

- entity extractor 테스트 통과
- relation extractor 테스트 통과
- graph rebuild 테스트 통과
- derived wiki 테스트 통과
- graph report 테스트 통과
- hybrid retrieval 테스트 통과
- 기존 FTS 관련 테스트가 깨지지 않음

### 17.6 Implementation progress

- v08-01 completed on 2026-05-17: `data/ffxiv_entities/jobs.json`, `skills.json`, `patches.json` and `src/domain_graph/entity_registry.py` provide the initial Job/Patch/Skill registry and alias normalization contract.
- v08-02 completed on 2026-05-17: `src/domain_graph/entity_extractor.py` extracts registry-backed entities with long-alias-first matching, Korean substring matching, ASCII word boundaries, deduplication, spans, aliases, and confidence.

---

## 18. 작업 분해

### Task 1 — Entity registry 추가

목표:

- `data/ffxiv_entities/` 추가
- `jobs.json`, `skills.json`, `patches.json` 추가
- alias normalization 지원

산출물:

- `data/ffxiv_entities/jobs.json`
- `data/ffxiv_entities/skills.json`
- `data/ffxiv_entities/patches.json`
- entity registry loader

테스트:

- alias -> canonical node id 변환 테스트

---

### Task 2 — Entity extractor 구현

목표:

- source summary에서 Job/Patch/Skill entity를 추출한다.

산출물:

- `tools/extract_entities.py`
- 또는 내부 모듈 `src/.../entity_extractor.py`

기능:

- registry load
- alias match
- dedup
- matched alias 기록
- source_id별 extraction result 반환

테스트:

- 한국어/영어 alias 매칭
- 중복 제거
- patch version 매칭

---

### Task 3 — Relation / Fact extractor 구현

목표:

- extracted entity 기반 relation과 fact를 생성한다.

산출물:

- `tools/extract_relations.py`
- 또는 내부 모듈 `src/.../relation_extractor.py`

기능:

- `MENTIONS`
- `HAS_SKILL`
- `SUPPORTS`
- `VALID_IN_PATCH`
- `AFFECTS_JOB`
- `AFFECTS_SKILL`
- `RELATED_TO`

테스트:

- clear trigger가 있을 때 Fact 생성
- trigger가 없으면 Fact 미생성
- registry 기반 HAS_SKILL 생성

---

### Task 4 — Domain graph rebuild CLI

목표:

- source summaries에서 domain graph를 rebuild한다.

산출물:

- `tools/rebuild_domain_graph.py`

기능:

- DB 연결
- registry load
- source summaries scan
- node upsert
- edge upsert
- fact upsert
- dry-run
- source-id filter
- idempotent rebuild

테스트:

- idempotency
- dry-run
- source-id filter
- graph table write

---

### Task 5 — Graph export / report

목표:

- Graphify-style export/report를 만든다.

산출물:

- `graph/nodes.json`
- `graph/edges.json`
- `graph/domain_graph.json`
- `graph/entity_index.json`
- `graph/GRAPH_REPORT.md`

기능:

- node/edge export
- entity alias index export
- node/edge count report
- top mentioned entities
- quality warnings

테스트:

- 파일 생성
- report 섹션 검증
- entity_index alias 검증

---

### Task 6 — Derived wiki generator

목표:

- graph 기반 derived wiki를 생성한다.

산출물:

- `tools/generate_derived_wiki.py`
- `wiki/jobs/*.md`
- `wiki/patches/*.md`
- `wiki/skills/*.md`

기능:

- job 중심 wiki
- patch 중심 wiki
- skill 중심 wiki
- related sources 포함
- graph links 포함
- wiki/index.md 갱신

테스트:

- 파일 생성
- related sources 포함
- idempotency
- index 갱신

---

### Task 7 — Graph-aware retrieval

목표:

- ask pipeline에 graph retrieval을 추가한다.

산출물:

- ask module 변경
- graph retrieval helper
- merge/rank helper

기능:

- question -> entity ids
- entity ids -> graph neighborhood
- graph result + FTS result merge
- fallback to FTS-only

테스트:

- entity matching
- graph neighborhood retrieval
- FTS fallback
- duplicate removal

---

### Task 8 — End-to-end smoke test

목표:

- v08 pipeline이 end-to-end로 동작하는지 확인한다.

시나리오:

1. fixture source summary 준비
2. domain graph rebuild
3. derived wiki 생성
4. graph report 생성
5. ask query 실행
6. graph + FTS context 확인

테스트 질문:

- `건브 7.5 변경점 알려줘`
- `No Mercy 관련 변경 있어?`
- `7.5에서 언급된 직업 보여줘`

---

## 19. 권장 실행 순서

1. Entity registry 작성
2. Entity extractor red test 작성
3. Entity extractor 구현
4. Relation/fact extractor red test 작성
5. Relation/fact extractor 구현
6. DB graph upsert helper 구현
7. Domain graph rebuild CLI 구현
8. Graph export/report 구현
9. Derived wiki generator 구현
10. Hybrid retrieval helper 구현
11. ask pipeline에 graph retrieval 연결
12. End-to-end smoke test 작성
13. 문서 갱신

---

## 20. 예시 E2E 흐름

입력 source summary:

    Patch 7.5 includes adjustments to Gunbreaker. No Mercy duration was changed.

Entity extraction:

    Job:Gunbreaker
    Skill:No Mercy
    Patch:7.5

Relation / Fact extraction:

    SourceDocument:X -> MENTIONS -> Job:Gunbreaker
    SourceDocument:X -> MENTIONS -> Skill:No Mercy
    SourceDocument:X -> MENTIONS -> Patch:7.5
    Job:Gunbreaker -> HAS_SKILL -> Skill:No Mercy
    SourceDocument:X -> SUPPORTS -> Fact:Y
    Fact:Y -> AFFECTS_JOB -> Job:Gunbreaker
    Fact:Y -> AFFECTS_SKILL -> Skill:No Mercy
    Fact:Y -> VALID_IN_PATCH -> Patch:7.5

Derived wiki:

    wiki/jobs/gunbreaker.md
    wiki/patches/7_5.md
    wiki/skills/no_mercy.md

Ask query:

    "건브 7.5 변경점 알려줘"

Retrieval:

    query entities:
      - job:gunbreaker
      - patch:7_5

    graph neighborhood:
      - fact:Y
      - source:X
      - skill:no_mercy

    FTS:
      - relevant source summary pages

Answer context:

    merged graph + FTS evidence

---

## 21. Risk and mitigation

### Risk 1 — entity extraction noise

문제:

- alias가 짧으면 오탐 가능성이 있다.
- 예: `DRK`, `WAR` 같은 약어는 일반 단어와 충돌 가능성이 있다.

대응:

- 짧은 alias는 word boundary를 엄격하게 적용한다.
- 대문자 약어는 case-sensitive option을 둔다.
- ambiguity warning을 report에 남긴다.

### Risk 2 — relation hallucination

문제:

- 단순 co-occurrence를 의미 관계로 오해할 수 있다.

대응:

- co-occurrence는 `RELATED_TO`로 낮은 confidence 저장
- 답변 근거에는 `SUPPORTED_BY`와 Fact 중심 evidence만 사용
- change trigger가 없으면 Fact 생성 금지

### Risk 3 — patch validity 부족

문제:

- FFXIV 지식은 패치별로 유효성이 다르다.

대응:

- patch entity가 없으면 Fact confidence를 낮춘다.
- `facts without patch`를 report warning에 표시한다.
- ask pipeline에서 최신 패치 조건이 들어오면 patch-linked Fact를 우선한다.

### Risk 4 — 기존 FTS 동작 깨짐

문제:

- ask pipeline 변경으로 기존 검색이 깨질 수 있다.

대응:

- graph retrieval이 실패해도 FTS-only fallback
- 기존 FTS 테스트 유지
- graph-aware retrieval은 additive layer로 구현

---

## 22. v09로 넘길 항목

v08 이후 v09 후보:

- Discord command에서 graph-aware answer 노출
- graph path explanation
- source quality scoring
- 공식 패치노트 crawler
- patch freshness policy
- item / gearset / food / materia ontology 확장
- BIS / opener / rotation derived wiki
- LLM-assisted relation extraction
- graph visualization HTML
- evaluation dashboard

---

## 23. 최종 요약

v08은 현재의 FTS 기반 RAG와 얕은 provenance graph를 다음 구조로 확장하는 작업이다.

    FTS RAG + Provenance Graph
      -> FFXIV Domain Graph
      -> Derived Wiki
      -> Graph-aware Hybrid Retrieval

핵심 산출물은 다음이다.

- `data/ffxiv_entities/*.json`
- domain graph node/edge
- Fact node
- `wiki/jobs/*.md`
- `wiki/patches/*.md`
- `wiki/skills/*.md`
- `graph/GRAPH_REPORT.md`
- `graph/domain_graph.json`
- `graph/entity_index.json`
- graph-aware retrieval

v08의 가장 중요한 성공 기준은 이것이다.

    "건브 7.5 변경점 알려줘" 같은 질문에서
    Gunbreaker와 Patch 7.5를 entity로 인식하고,
    graph neighborhood와 FTS 결과를 병합하여
    source-grounded answer context를 만들 수 있어야 한다.
