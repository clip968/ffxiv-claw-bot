# v08 Implementation Plan — FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval

## 0. 목적

이 문서는 `v08 Spec — FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval`을 실제 구현 작업으로 분해한 implementation plan이다.

v08의 목표는 현재의 구조를 다음처럼 확장하는 것이다.

    현재:
      source_summaries
        -> wiki_pages
        -> SQLite FTS
        -> shallow provenance graph

    v08 목표:
      source_summaries
        -> entity extraction
        -> relation/fact extraction
        -> FFXIV domain graph
        -> derived wiki
        -> graph report/export
        -> graph-aware hybrid retrieval

핵심 구현 목표:

1. FFXIV entity registry 추가
2. Job / Patch / Skill / Fact graph 생성
3. source summary 기반 relation/fact extraction
4. `wiki/jobs`, `wiki/patches`, `wiki/skills` derived wiki 생성
5. `graph/GRAPH_REPORT.md`, `graph/domain_graph.json`, `graph/entity_index.json` 생성
6. ask pipeline에 graph-aware retrieval 추가
7. 테스트로 idempotency, fallback, retrieval 병합 검증

전제:

- Lost Ark 등 비-FFXIV 오염 데이터 정리는 이미 완료됨
- 기존 FTS 기반 RAG는 유지해야 함
- graph layer는 기존 ask pipeline에 additive하게 붙여야 함
- DB source of truth는 `db/ffxiv.sqlite`
- `graph/*.json`과 `graph/GRAPH_REPORT.md`는 export/report 산출물

---

## 1. 구현 원칙

### 1.1 기존 기능을 깨지 않는다

v08은 기존 FTS 기반 ask를 대체하지 않는다.

기존 흐름:

    question -> SQLite FTS -> answer context

v08 추가 흐름:

    question -> entity matcher -> graph neighborhood retrieval -> FTS result와 병합

graph retrieval이 실패해도 기존 FTS-only 흐름은 작동해야 한다.

### 1.2 DB가 source of truth다

다음은 DB에서 파생된 산출물이다.

- `graph/nodes.json`
- `graph/edges.json`
- `graph/domain_graph.json`
- `graph/entity_index.json`
- `graph/GRAPH_REPORT.md`
- `wiki/jobs/*.md`
- `wiki/patches/*.md`
- `wiki/skills/*.md`

### 1.3 idempotency를 보장한다

같은 입력에 대해 여러 번 실행해도 node, edge, fact, derived wiki가 중복 생성되면 안 된다.

필수:

- node id deterministic
- edge id deterministic
- fact id deterministic
- file generation deterministic

### 1.4 relation은 보수적으로 생성한다

확실하지 않은 관계는 `Fact`로 만들지 않는다.

- 단순 동시 등장: `MENTIONS` 또는 낮은 confidence의 `RELATED_TO`
- patch + job/skill + change trigger가 있을 때만 `Fact` 생성
- buff/nerf 판단은 v08에서 기본 생성하지 않음

### 1.5 implementation 순서

반드시 아래 순서로 구현한다.

1. entity registry
2. entity extractor
3. relation/fact extractor
4. graph storage/upsert helper
5. domain graph rebuild CLI
6. graph export/report
7. derived wiki generator
8. graph-aware retrieval
9. end-to-end smoke test

---

## 2. 예상 디렉터리 구조

v08 구현 후 권장 구조:

    data/
      ffxiv_entities/
        jobs.json
        skills.json
        patches.json
        items.json
        encounters.json

    tools/
      extract_entities.py
      extract_relations.py
      rebuild_domain_graph.py
      generate_derived_wiki.py
      generate_graph_report.py

    graph/
      nodes.json
      edges.json
      domain_graph.json
      entity_index.json
      GRAPH_REPORT.md

    wiki/
      source_summaries/
      jobs/
      patches/
      skills/
      index.md

    tests/
      test_entity_extractor.py
      test_relation_extractor.py
      test_domain_graph_rebuild.py
      test_derived_wiki.py
      test_graph_report.py
      test_hybrid_retrieval.py
      test_v08_e2e.py

실제 repo 구조가 `src/` 패키지 중심이면 `tools/`는 얇은 CLI wrapper로 두고, 핵심 로직은 `src/...` 하위 모듈로 둔다.

권장 내부 모듈명 예:

    src/ffxiv_bot/graph/entity_registry.py
    src/ffxiv_bot/graph/entity_extractor.py
    src/ffxiv_bot/graph/relation_extractor.py
    src/ffxiv_bot/graph/domain_graph.py
    src/ffxiv_bot/graph/export.py
    src/ffxiv_bot/graph/report.py
    src/ffxiv_bot/wiki/derived_wiki.py
    src/ffxiv_bot/retrieval/hybrid.py

repo가 아직 패키지 구조를 갖추지 않았다면, v08에서는 `tools/` 중심으로 구현해도 된다. 단, 테스트 가능한 pure function은 별도 모듈로 분리한다.

---

## 3. Task 1 — Entity Registry 추가

### 목표

FFXIV 도메인 entity를 canonical id로 정규화할 수 있는 registry를 추가한다.

v08 필수 entity type:

- Job
- Patch
- Skill

v08 optional entity type:

- Item
- Encounter
- GearSet

### 생성 파일

필수:

    data/ffxiv_entities/jobs.json
    data/ffxiv_entities/skills.json
    data/ffxiv_entities/patches.json

선택:

    data/ffxiv_entities/items.json
    data/ffxiv_entities/encounters.json

로더:

    tools/extract_entities.py

또는 패키지 구조 사용 시:

    src/ffxiv_bot/graph/entity_registry.py

### 데이터 형식

`jobs.json` 예:

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

`skills.json` 예:

    [
      {
        "type": "Skill",
        "canonical": "No Mercy",
        "slug": "no_mercy",
        "aliases": ["No Mercy", "노 머시", "노머시"],
        "job": "Gunbreaker"
      }
    ]

`patches.json` 예:

    [
      {
        "type": "Patch",
        "canonical": "Patch 7.5",
        "slug": "7_5",
        "aliases": ["7.5", "Patch 7.5", "패치 7.5"]
      }
    ]

### 구현 요구사항

Registry loader는 다음 기능을 제공해야 한다.

- 모든 registry JSON 로드
- alias -> canonical entity 매핑
- canonical entity -> node id 변환
- node id -> entity metadata 조회
- 긴 alias 우선 정렬
- 중복 alias 감지
- ambiguity warning 생성

권장 node id 규칙:

    Job:    job:<slug>
    Patch:  patch:<slug>
    Skill:  skill:<slug>
    Item:   item:<slug>
    Encounter: encounter:<slug>

예:

    job:gunbreaker
    patch:7_5
    skill:no_mercy

### Red tests

먼저 실패하는 테스트를 작성한다.

파일:

    tests/test_entity_extractor.py

테스트 항목:

1. `Gunbreaker`가 `job:gunbreaker`로 정규화된다.
2. `GNB`가 `job:gunbreaker`로 정규화된다.
3. `건브`가 `job:gunbreaker`로 정규화된다.
4. `No Mercy`가 `skill:no_mercy`로 정규화된다.
5. `7.5`, `Patch 7.5`, `패치 7.5`가 `patch:7_5`로 정규화된다.
6. 같은 alias가 두 entity에 중복 등록되면 warning 또는 error를 낸다.

### 완료 조건

- registry JSON이 존재한다.
- registry loader가 테스트를 통과한다.
- alias matching의 기본 자료구조가 준비된다.

---

## 4. Task 2 — Entity Extractor 구현

### 목표

source summary 또는 wiki page text에서 FFXIV entity를 추출한다.

입력:

- text
- optional source_id
- entity registry

출력:

    [
      {
        "node_id": "job:gunbreaker",
        "type": "Job",
        "canonical": "Gunbreaker",
        "matched_alias": "건브",
        "span": [10, 12],
        "confidence": 0.9
      }
    ]

### 수정/생성 파일

권장:

    src/ffxiv_bot/graph/entity_extractor.py

또는 단순 구조:

    tools/extract_entities.py

CLI wrapper:

    python tools/extract_entities.py --text "건브 7.5 No Mercy 변경점"
    python tools/extract_entities.py --source-id <source_id>
    python tools/extract_entities.py --wiki-root wiki

### 구현 요구사항

1. registry alias를 긴 순서대로 검사한다.
2. 영어 alias는 case-insensitive match를 기본으로 한다.
3. 짧은 영어 약어는 word boundary를 엄격히 적용한다.
4. 한국어 alias는 substring match를 허용하되 중복 span을 제거한다.
5. 같은 canonical entity가 여러 번 등장해도 결과는 하나로 dedup한다.
6. matched_alias와 span은 debug/report 용도로 보존한다.
7. 반환 결과는 deterministic order를 가진다.
   - type priority: Patch, Job, Skill, Item, Encounter
   - 같은 type이면 canonical name 기준 정렬

### Red tests

파일:

    tests/test_entity_extractor.py

추가 테스트:

1. `"건브 7.5 변경점"`에서 `job:gunbreaker`, `patch:7_5`가 추출된다.
2. `"GNB No Mercy"`에서 `job:gunbreaker`, `skill:no_mercy`가 추출된다.
3. `"Gunbreaker Gunbreaker GNB"`에서 `job:gunbreaker`가 한 번만 나온다.
4. `"No Mercy duration changed in Patch 7.5"`에서 skill과 patch가 추출된다.
5. 짧은 alias가 다른 단어 내부에서 오탐되지 않는다.

### 완료 조건

- entity extractor가 pure function으로 테스트 가능하다.
- CLI 또는 import 방식으로 source summary text를 처리할 수 있다.
- dedup과 alias normalization이 동작한다.

---

## 5. Task 3 — Relation / Fact Extractor 구현

### 목표

추출된 entity와 source summary text를 기반으로 relation과 fact를 생성한다.

### 수정/생성 파일

권장:

    src/ffxiv_bot/graph/relation_extractor.py

또는 단순 구조:

    tools/extract_relations.py

### Relation 모델

권장 내부 데이터 구조:

    {
      "source_node_id": "src:local_x",
      "target_node_id": "job:gunbreaker",
      "relation_type": "MENTIONS",
      "properties": {
        "matched_alias": "건브"
      },
      "source_id": "local_x",
      "confidence": 0.9
    }

### Fact 모델

권장 내부 데이터 구조:

    {
      "node_id": "fact:<hash>",
      "type": "Fact",
      "text": "Patch 7.5 includes adjustments to Gunbreaker and No Mercy.",
      "subject": "skill:no_mercy",
      "relation": "CHANGED_IN",
      "object": "patch:7_5",
      "source_id": "local_x",
      "confidence": 0.8,
      "extraction_method": "rule_based_v1"
    }

### 구현 relation

필수:

- `SourceDocument -> MENTIONS -> Entity`
- `WikiPage -> MENTIONS -> Entity`
- `Job -> HAS_SKILL -> Skill`
- `SourceDocument -> SUPPORTS -> Fact`
- `Fact -> VALID_IN_PATCH -> Patch`
- `Fact -> AFFECTS_JOB -> Job`
- `Fact -> AFFECTS_SKILL -> Skill`

선택:

- `Entity -> RELATED_TO -> Entity`

### Fact 생성 규칙

Fact는 다음 조건을 모두 만족할 때 생성한다.

1. Patch entity가 있다.
2. Job 또는 Skill entity가 있다.
3. change trigger가 있다.

영어 trigger:

    changed
    adjusted
    potency
    recast
    duration
    effect
    added
    removed
    increased
    decreased
    now
    no longer

한국어 trigger:

    변경
    조정
    위력
    재사용
    지속시간
    효과
    추가
    삭제
    증가
    감소
    이제
    더 이상

### Red tests

파일:

    tests/test_relation_extractor.py

테스트 항목:

1. Job entity가 있으면 `SourceDocument -> MENTIONS -> Job` edge가 생성된다.
2. Skill entity가 있으면 `SourceDocument -> MENTIONS -> Skill` edge가 생성된다.
3. Patch entity가 있으면 `SourceDocument -> MENTIONS -> Patch` edge가 생성된다.
4. registry에 skill.job이 있으면 `Job -> HAS_SKILL -> Skill` edge가 생성된다.
5. patch + skill + trigger가 있으면 Fact node가 생성된다.
6. trigger가 없으면 Fact node가 생성되지 않는다.
7. Fact는 `SUPPORTS`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL` edge를 가진다.

### 완료 조건

- relation extractor가 entity extractor 결과를 입력으로 받는다.
- Fact 생성이 보수적으로 동작한다.
- relation/fact 생성 결과가 deterministic하다.

---

## 6. Task 4 — Graph Storage / Upsert Helper 구현

### 목표

domain graph node/edge/fact를 SQLite에 안전하게 저장한다.

### 수정/생성 파일

권장:

    src/ffxiv_bot/graph/domain_graph.py

또는 단순 구조:

    tools/rebuild_domain_graph.py 내부 helper

### DB 컬럼 확인

기존 `graph_nodes`, `graph_edges` schema를 먼저 확인한다.

명령 예:

    sqlite3 db/ffxiv.sqlite ".schema graph_nodes"
    sqlite3 db/ffxiv.sqlite ".schema graph_edges"

기존 schema가 부족하면 additive migration을 적용한다.

### 권장 graph_nodes 컬럼

    id TEXT PRIMARY KEY
    type TEXT NOT NULL
    name TEXT NOT NULL
    canonical_name TEXT
    aliases_json TEXT
    properties_json TEXT
    created_at TEXT
    updated_at TEXT

### 권장 graph_edges 컬럼

    id TEXT PRIMARY KEY
    source_node_id TEXT NOT NULL
    target_node_id TEXT NOT NULL
    relation_type TEXT NOT NULL
    properties_json TEXT
    source_id TEXT
    confidence REAL
    created_at TEXT
    updated_at TEXT

### Migration 원칙

- destructive migration 금지
- 기존 provenance graph 보존
- 필요한 컬럼만 `ALTER TABLE ADD COLUMN`
- 인덱스는 없으면 생성

권장 index:

    CREATE INDEX IF NOT EXISTS idx_graph_nodes_type ON graph_nodes(type);
    CREATE INDEX IF NOT EXISTS idx_graph_nodes_canonical_name ON graph_nodes(canonical_name);
    CREATE INDEX IF NOT EXISTS idx_graph_edges_source_node ON graph_edges(source_node_id);
    CREATE INDEX IF NOT EXISTS idx_graph_edges_target_node ON graph_edges(target_node_id);
    CREATE INDEX IF NOT EXISTS idx_graph_edges_relation_type ON graph_edges(relation_type);
    CREATE INDEX IF NOT EXISTS idx_graph_edges_source_id ON graph_edges(source_id);

### Upsert 요구사항

함수 예:

    upsert_node(conn, node)
    upsert_edge(conn, edge)
    upsert_fact(conn, fact)
    get_neighbors(conn, node_id, depth=1)
    get_nodes_by_type(conn, node_type)
    get_edges_by_relation(conn, relation_type)

id 규칙:

    src:<source_id>
    page:<page_slug>
    job:<slug>
    patch:<slug>
    skill:<slug>
    fact:<stable_hash>
    edge:<stable_hash>

edge hash 입력:

    source_node_id + relation_type + target_node_id + source_id

fact hash 입력:

    source_id + subject_node_id + relation + object_node_id + normalized_fact_text

### Red tests

파일:

    tests/test_domain_graph_rebuild.py

초기 storage 중심 테스트:

1. 같은 node를 두 번 upsert해도 row가 하나만 존재한다.
2. 같은 edge를 두 번 upsert해도 row가 하나만 존재한다.
3. Fact id가 같은 입력에서 항상 동일하다.
4. provenance graph node가 삭제되지 않는다.

### 완료 조건

- graph upsert가 idempotent하다.
- 기존 `SOURCE_OF` edge가 유지된다.
- domain graph와 provenance graph가 같은 table에 공존한다.

---

## 7. Task 5 — Domain Graph Rebuild CLI 구현

### 목표

source summaries를 읽어 FFXIV domain graph를 rebuild한다.

### 생성 파일

    tools/rebuild_domain_graph.py

### CLI

필수 옵션:

    python tools/rebuild_domain_graph.py

권장 옵션:

    --db-path db/ffxiv.sqlite
    --wiki-root wiki
    --entities-dir data/ffxiv_entities
    --graph-dir graph
    --dry-run
    --source-id <source_id>
    --reset-domain-graph
    --verbose

### 동작 순서

1. DB 연결
2. graph schema/migration 확인
3. entity registry 로드
4. source summaries 로드
5. SourceDocument node upsert
6. WikiPage node upsert
7. Job/Patch/Skill node upsert
8. source summary별 entity extraction
9. `MENTIONS` edge 생성
10. registry 기반 `HAS_SKILL` edge 생성
11. relation/fact extraction
12. Fact node upsert
13. Fact 관련 edge upsert
14. graph export 호출
15. graph report 호출

### Source summary 로드

가능한 입력:

- `wiki/source_summaries/*.md`
- DB `wiki_pages`
- DB `sources`

우선순위:

1. DB source_id와 연결된 wiki page가 있으면 DB metadata 사용
2. 파일 path가 있으면 file content 사용
3. DB body/content가 있으면 fallback

### `--reset-domain-graph`

주의:

- provenance graph는 삭제하지 않는다.
- domain graph node/edge만 삭제한다.
- 삭제 대상 type:
  - Job
  - Patch
  - Skill
  - Item
  - Encounter
  - GearSet
  - Fact
- 삭제 대상 relation:
  - MENTIONS
  - HAS_SKILL
  - SUPPORTS
  - VALID_IN_PATCH
  - AFFECTS_JOB
  - AFFECTS_SKILL
  - RELATED_TO
  - DERIVED_FROM

### Red tests

파일:

    tests/test_domain_graph_rebuild.py

테스트 항목:

1. fixture source summary에서 domain nodes가 생성된다.
2. fixture source summary에서 MENTIONS edge가 생성된다.
3. patch + skill + trigger에서 Fact가 생성된다.
4. rebuild를 두 번 실행해도 node/edge 수가 증가하지 않는다.
5. `--dry-run`은 DB를 변경하지 않는다.
6. `--source-id`는 특정 source만 처리한다.
7. `--reset-domain-graph`는 provenance graph를 보존한다.

### 완료 조건

- CLI가 repo root에서 실행된다.
- dry-run이 가능하다.
- idempotent rebuild가 가능하다.
- domain graph가 DB에 저장된다.

---

## 8. Task 6 — Graph Export 구현

### 목표

DB graph를 Graphify-style 산출물로 export한다.

### 생성 파일

권장:

    src/ffxiv_bot/graph/export.py
    tools/generate_graph_report.py

또는 CLI 통합:

    tools/rebuild_domain_graph.py 실행 끝에서 export 수행

### 출력 파일

    graph/nodes.json
    graph/edges.json
    graph/domain_graph.json
    graph/entity_index.json

### `nodes.json`

권장 형식:

    [
      {
        "id": "job:gunbreaker",
        "type": "Job",
        "name": "Gunbreaker",
        "canonical_name": "Gunbreaker",
        "aliases": ["Gunbreaker", "GNB", "건브", "건브레이커"],
        "properties": {}
      }
    ]

### `edges.json`

권장 형식:

    [
      {
        "id": "edge:...",
        "source": "job:gunbreaker",
        "target": "skill:no_mercy",
        "relation": "HAS_SKILL",
        "source_id": null,
        "confidence": 1.0,
        "properties": {}
      }
    ]

### `domain_graph.json`

권장 형식:

    {
      "metadata": {
        "schema_version": "v08",
        "generated_at": "2026-05-17T00:00:00Z",
        "node_count": 123,
        "edge_count": 456
      },
      "nodes": [],
      "edges": []
    }

### `entity_index.json`

alias 기반 query matching용 index.

예:

    {
      "gunbreaker": "job:gunbreaker",
      "gnb": "job:gunbreaker",
      "건브": "job:gunbreaker",
      "no mercy": "skill:no_mercy",
      "7.5": "patch:7_5"
    }

### Red tests

파일:

    tests/test_graph_report.py

또는:

    tests/test_graph_export.py

테스트 항목:

1. `nodes.json`이 생성된다.
2. `edges.json`이 생성된다.
3. `domain_graph.json` metadata가 포함된다.
4. `entity_index.json`에 alias가 포함된다.
5. JSON은 valid JSON이다.

### 완료 조건

- export 파일이 deterministic하게 생성된다.
- entity_index가 ask pipeline에서 사용할 수 있다.

---

## 9. Task 7 — Graph Report 구현

### 목표

Graphify의 `GRAPH_REPORT.md`에 해당하는 FFXIV graph report를 생성한다.

### 생성 파일

    graph/GRAPH_REPORT.md

생성 로직:

    src/ffxiv_bot/graph/report.py

또는:

    tools/generate_graph_report.py

### Report 필수 섹션

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
    - SOURCE_OF
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

### Quality warning 기준

1. source summary가 있는데 entity가 하나도 추출되지 않은 source
2. Fact node가 있는데 `SUPPORTS` edge가 없는 경우
3. Fact node가 있는데 `VALID_IN_PATCH` edge가 없는 경우
4. Job/Skill/Patch node가 있는데 MENTIONS edge가 없는 경우
5. registry alias가 중복되거나 ambiguous한 경우

### Red tests

파일:

    tests/test_graph_report.py

테스트 항목:

1. `GRAPH_REPORT.md`가 생성된다.
2. Summary 섹션이 있다.
3. Node Counts 섹션이 있다.
4. Edge Counts 섹션이 있다.
5. Top Mentioned Jobs 섹션이 있다.
6. Quality Warnings 섹션이 있다.

### 완료 조건

- report만 읽어도 현재 graph 상태를 파악할 수 있다.
- OpenClaw/Codex agent가 작업 시작 전에 참고할 수 있는 수준이어야 한다.

---

## 10. Task 8 — Derived Wiki Generator 구현

### 목표

domain graph를 기반으로 derived wiki를 생성한다.

### 생성 파일

    tools/generate_derived_wiki.py

권장 내부 모듈:

    src/ffxiv_bot/wiki/derived_wiki.py

### CLI

    python tools/generate_derived_wiki.py

권장 옵션:

    --db-path db/ffxiv.sqlite
    --wiki-root wiki
    --graph-dir graph
    --types jobs,patches,skills
    --dry-run
    --verbose

### 생성 대상

필수:

    wiki/jobs/*.md
    wiki/patches/*.md
    wiki/skills/*.md

### Job wiki 구조

예:

    # Gunbreaker

    ## Summary
    Current KB-level summary for Gunbreaker.

    ## Related Patches
    - Patch 7.5

    ## Skills
    - No Mercy
    - Continuation

    ## Recent Facts
    - Fact text...

    ## Related Sources
    - source_id: local_x
      - title: ...
      - path: wiki/source_summaries/...

    ## Graph Links
    - Job:Gunbreaker -> HAS_SKILL -> Skill:No Mercy
    - Fact:... -> AFFECTS_JOB -> Job:Gunbreaker

### Patch wiki 구조

예:

    # Patch 7.5

    ## Summary
    Current KB-level summary for Patch 7.5.

    ## Affected Jobs
    - Gunbreaker

    ## Affected Skills
    - No Mercy

    ## Facts
    - Fact text...

    ## Related Sources
    - source_id: local_x

### Skill wiki 구조

예:

    # No Mercy

    ## Summary
    Current KB-level summary for No Mercy.

    ## Job
    - Gunbreaker

    ## Related Patches
    - Patch 7.5

    ## Facts
    - Fact text...

    ## Related Sources
    - source_id: local_x

### wiki/index.md 갱신

`wiki/index.md`에 다음 섹션을 추가 또는 갱신한다.

    ## Derived Wiki

    ### Jobs
    - [Gunbreaker](jobs/gunbreaker.md)

    ### Patches
    - [Patch 7.5](patches/7_5.md)

    ### Skills
    - [No Mercy](skills/no_mercy.md)

### Red tests

파일:

    tests/test_derived_wiki.py

테스트 항목:

1. `wiki/jobs/gunbreaker.md`가 생성된다.
2. job wiki에 related skills가 포함된다.
3. job wiki에 related patches가 포함된다.
4. job wiki에 related sources가 포함된다.
5. `wiki/patches/7_5.md`가 생성된다.
6. `wiki/skills/no_mercy.md`가 생성된다.
7. `wiki/index.md`가 갱신된다.
8. 같은 입력으로 두 번 실행해도 결과가 안정적이다.

### 완료 조건

- derived wiki가 graph에서 파생된다.
- source summary와 연결이 유지된다.
- 사용자가 직접 읽을 수 있는 품질의 Markdown이 생성된다.

---

## 11. Task 9 — Graph-aware Hybrid Retrieval 구현

### 목표

ask pipeline에서 FTS 결과와 graph 결과를 병합한다.

### 수정 파일

기존 ask entrypoint를 확인한 뒤 수정한다.

가능한 파일명 예:

    tools/ask.py
    src/ffxiv_bot/ask.py
    src/ffxiv_bot/retrieval.py

신규 helper 권장:

    src/ffxiv_bot/retrieval/hybrid.py

### 신규 함수

권장 함수:

    load_entity_index(graph_dir)
    match_query_entities(question, entity_index)
    retrieve_graph_neighborhood(conn, entity_ids, depth=2)
    retrieve_fts_results(conn, question, limit=5)
    merge_retrieval_results(fts_results, graph_results, limit=8)
    build_answer_context(merged_results)

### Query flow

    question
      -> match_query_entities
      -> retrieve_graph_neighborhood
      -> retrieve_fts_results
      -> merge_retrieval_results
      -> build_answer_context
      -> existing answer generator

### Entity matching 예

입력:

    건브 7.5 변경점 알려줘

출력:

    [
      "job:gunbreaker",
      "patch:7_5"
    ]

### Graph neighborhood 우선순위

1. matched entity와 연결된 Fact
2. Fact를 support하는 SourceDocument
3. matched entity와 연결된 WikiPage
4. matched entity와 연결된 Job/Skill/Patch
5. derived wiki page

### Merge policy

간단한 v08 정책:

- FTS top 5
- graph-derived result top 5
- source_id 또는 page_id 기준 중복 제거
- 최종 context 최대 8개
- graph result가 없으면 FTS-only fallback
- FTS result가 없고 graph result만 있으면 graph-only context 허용

### Ranking policy

초기 점수 예:

    base score:
      FTS result: original FTS score
      graph result: 1.0

    boosts:
      exact entity match: +0.5
      Fact-backed source: +0.4
      derived wiki page: +0.2
      patch match: +0.3

    penalties:
      no source_id: -0.3
      no patch when query has patch: -0.2

v08에서는 단순 구현으로 충분하다. 복잡한 랭킹은 v09로 넘긴다.

### Red tests

파일:

    tests/test_hybrid_retrieval.py

테스트 항목:

1. `"건브 7.5 변경점 알려줘"`에서 `job:gunbreaker`, `patch:7_5`가 match된다.
2. graph neighborhood가 관련 Fact 또는 SourceDocument를 반환한다.
3. FTS result와 graph result가 병합된다.
4. 중복 source가 제거된다.
5. graph 결과가 없어도 FTS-only fallback이 동작한다.
6. FTS 결과가 없어도 graph-only context가 구성된다.

### 완료 조건

- ask pipeline이 graph-aware retrieval을 호출한다.
- 기존 FTS-only behavior는 fallback으로 남아 있다.
- retrieval helper는 독립 테스트 가능하다.

---

## 12. Task 10 — End-to-End Smoke Test

### 목표

v08 전체 파이프라인이 최소 fixture에서 동작하는지 검증한다.

### 생성 파일

    tests/test_v08_e2e.py

또는 기존 테스트 구조에 맞춰 추가한다.

### Fixture 입력

임시 source summary 예:

    # Source Summary

    Patch 7.5 includes adjustments to Gunbreaker.
    No Mercy duration was changed.

### 기대 결과

Entity:

    job:gunbreaker
    patch:7_5
    skill:no_mercy

Graph:

    SourceDocument -> MENTIONS -> Job
    SourceDocument -> MENTIONS -> Patch
    SourceDocument -> MENTIONS -> Skill
    Job -> HAS_SKILL -> Skill
    SourceDocument -> SUPPORTS -> Fact
    Fact -> VALID_IN_PATCH -> Patch
    Fact -> AFFECTS_JOB -> Job
    Fact -> AFFECTS_SKILL -> Skill

Files:

    graph/domain_graph.json
    graph/entity_index.json
    graph/GRAPH_REPORT.md
    wiki/jobs/gunbreaker.md
    wiki/patches/7_5.md
    wiki/skills/no_mercy.md

Retrieval:

    question: 건브 7.5 변경점 알려줘
    expected matched entities:
      - job:gunbreaker
      - patch:7_5
    expected context:
      - source summary or fact-backed graph result

### 완료 조건

- 단일 test command로 e2e fixture가 통과한다.
- 실제 DB를 오염시키지 않는다.
- tmp DB 또는 transaction rollback을 사용한다.

---

## 13. 권장 commit 단위

가능하면 task 단위로 commit한다.

1. `test: add v08 entity registry tests`
2. `feat: add FFXIV entity registry`
3. `feat: add rule-based entity extractor`
4. `test: add relation and fact extraction tests`
5. `feat: add relation and fact extractor`
6. `feat: add domain graph storage helpers`
7. `feat: add domain graph rebuild CLI`
8. `feat: add graph export and report`
9. `feat: add derived wiki generator`
10. `feat: add graph-aware hybrid retrieval`
11. `test: add v08 end-to-end smoke test`
12. `docs: add v08 implementation notes`

---

## 14. 실행 명령 예시

### 전체 테스트

    pytest

### v08 관련 테스트만 실행

    pytest tests/test_entity_extractor.py
    pytest tests/test_relation_extractor.py
    pytest tests/test_domain_graph_rebuild.py
    pytest tests/test_derived_wiki.py
    pytest tests/test_graph_report.py
    pytest tests/test_hybrid_retrieval.py
    pytest tests/test_v08_e2e.py

### domain graph rebuild

    python tools/rebuild_domain_graph.py --db-path db/ffxiv.sqlite --wiki-root wiki --entities-dir data/ffxiv_entities --graph-dir graph

### dry-run

    python tools/rebuild_domain_graph.py --dry-run --verbose

### 특정 source만 rebuild

    python tools/rebuild_domain_graph.py --source-id local_a5f56616236f --verbose

### derived wiki 생성

    python tools/generate_derived_wiki.py --db-path db/ffxiv.sqlite --wiki-root wiki --graph-dir graph --types jobs,patches,skills

### graph report 생성

    python tools/generate_graph_report.py --db-path db/ffxiv.sqlite --graph-dir graph

---

## 15. 구현 중 주의사항

### 15.1 source_id / page_id 연결

기존 DB의 `sources`, `wiki_pages`, `wiki_fts` schema를 먼저 확인한다.

특히 다음 mapping을 명확히 해야 한다.

    source_id -> source summary file
    source_id -> wiki_page
    wiki_page -> wiki_fts row
    wiki_page -> graph node

이 mapping이 불명확하면 derived wiki와 graph retrieval에서 출처 연결이 깨진다.

### 15.2 기존 provenance graph 보존

현재 graph가 얕더라도 `SourceDocument -> SOURCE_OF -> WikiPage`는 유지한다.

v08 domain graph는 이 위에 추가한다.

### 15.3 파일 생성은 deterministic하게 한다

Markdown 생성 시 정렬 기준을 고정한다.

권장 정렬:

- Job: canonical name
- Patch: version descending 또는 ascending 중 하나로 통일
- Skill: canonical name
- Source: source_id
- Fact: fact text 또는 fact id

### 15.4 한국어 alias 처리

한국어 alias는 word boundary가 영어처럼 작동하지 않는다.

따라서 한국어 alias는 substring match를 사용하되, 긴 alias 우선과 overlap 제거를 적용한다.

예:

    건브레이커
    건브

긴 alias를 먼저 매칭하지 않으면 `건브레이커` 안에서 `건브`가 먼저 잡힐 수 있다.

### 15.5 약어 오탐 방지

`WAR`, `DRK`, `SAM`, `MCH` 같은 짧은 약어는 일반 텍스트와 충돌할 수 있다.

대응:

- uppercase abbreviation은 case-sensitive로 처리
- word boundary 필요
- ambiguity warning report에 표시

### 15.6 Fact 생성은 보수적으로

Fact는 답변 근거에 직접 쓰일 수 있으므로 과생성하면 위험하다.

v08에서는 다음 경우에만 Fact 생성:

    Patch entity 있음
    Job 또는 Skill entity 있음
    change trigger 있음

그 외에는 `MENTIONS`만 생성한다.

---

## 16. Definition of Done

v08 implementation은 다음을 모두 만족해야 완료다.

### Graph

- `Job`, `Patch`, `Skill`, `Fact` node가 생성된다.
- `MENTIONS`, `HAS_SKILL`, `SUPPORTS`, `VALID_IN_PATCH`, `AFFECTS_JOB`, `AFFECTS_SKILL`, `DERIVED_FROM` edge가 생성된다.
- domain graph rebuild가 idempotent하다.
- 기존 provenance graph가 보존된다.

### Export / Report

- `graph/nodes.json` 생성
- `graph/edges.json` 생성
- `graph/domain_graph.json` 생성
- `graph/entity_index.json` 생성
- `graph/GRAPH_REPORT.md` 생성
- report에 node count, edge count, top entities, quality warnings가 포함된다.

### Derived Wiki

- `wiki/jobs/*.md` 생성
- `wiki/patches/*.md` 생성
- `wiki/skills/*.md` 생성
- 각 derived wiki에 related sources 포함
- `wiki/index.md`가 갱신됨

### Retrieval

- 질문에서 entity를 match한다.
- graph neighborhood retrieval을 수행한다.
- graph result와 FTS result를 병합한다.
- graph result가 없어도 FTS-only fallback이 작동한다.
- 기존 FTS 테스트가 깨지지 않는다.

### Tests

다음 테스트 파일 또는 동등한 테스트가 통과한다.

- `tests/test_entity_extractor.py`
- `tests/test_relation_extractor.py`
- `tests/test_domain_graph_rebuild.py`
- `tests/test_derived_wiki.py`
- `tests/test_graph_report.py`
- `tests/test_hybrid_retrieval.py`
- `tests/test_v08_e2e.py`

---

## 17. Agent 작업 지시문

아래 문장을 agent에게 task 시작 프롬프트로 사용할 수 있다.

    v08 implementation을 진행한다.
    목표는 FFXIV Domain Graphify Layer + Derived Wiki + Hybrid Retrieval 구현이다.
    먼저 현재 repo 구조와 DB schema를 확인하고, 기존 FTS/RAG 동작을 깨지 않는 additive 방식으로 구현한다.
    implementation.md의 Task 1부터 순서대로 진행한다.
    각 task는 red test를 먼저 작성한 뒤 구현한다.
    기존 provenance graph는 보존한다.
    `db/ffxiv.sqlite`를 source of truth로 두고, `graph/*.json`, `graph/GRAPH_REPORT.md`, `wiki/jobs`, `wiki/patches`, `wiki/skills`는 파생 산출물로 생성한다.
    같은 입력으로 rebuild를 여러 번 실행해도 node/edge/fact/wiki가 중복 생성되지 않아야 한다.
    graph retrieval이 실패해도 기존 FTS-only ask는 fallback으로 동작해야 한다.
    완료 후 실행한 테스트, 변경 파일, 생성 산출물, 남은 리스크를 요약한다.

---

## 18. Task별 agent 프롬프트

### Task 1 prompt

    v08 Task 1을 수행한다.
    `data/ffxiv_entities/`에 jobs.json, skills.json, patches.json을 추가하고 entity registry loader를 구현한다.
    먼저 tests/test_entity_extractor.py에 alias normalization red tests를 작성한다.
    Gunbreaker/GNB/건브/건브레이커, No Mercy, Patch 7.5 alias가 canonical node id로 정규화되어야 한다.
    구현 후 해당 테스트를 통과시킨다.
    기존 기능은 수정하지 않는다.

### Task 2 prompt

    v08 Task 2를 수행한다.
    source summary text에서 FFXIV entity를 추출하는 rule-based entity extractor를 구현한다.
    긴 alias 우선, 중복 제거, 영어 word boundary, 한국어 substring match를 처리한다.
    먼저 red tests를 작성하고, 그 후 구현한다.
    결과에는 node_id, type, canonical, matched_alias, confidence를 포함한다.

### Task 3 prompt

    v08 Task 3을 수행한다.
    extracted entities를 기반으로 MENTIONS, HAS_SKILL, SUPPORTS, VALID_IN_PATCH, AFFECTS_JOB, AFFECTS_SKILL relation과 Fact node를 생성하는 extractor를 구현한다.
    Fact는 patch + job/skill + change trigger가 있을 때만 생성한다.
    먼저 tests/test_relation_extractor.py에 red tests를 작성한 뒤 구현한다.

### Task 4 prompt

    v08 Task 4를 수행한다.
    graph_nodes, graph_edges에 domain graph를 저장하는 storage/upsert helper를 구현한다.
    기존 schema를 확인하고 destructive migration 없이 필요한 컬럼과 index만 추가한다.
    node/edge/fact id는 deterministic해야 한다.
    같은 입력을 여러 번 upsert해도 중복 row가 생기면 안 된다.
    기존 SourceDocument -> SOURCE_OF -> WikiPage provenance graph는 보존한다.

### Task 5 prompt

    v08 Task 5를 수행한다.
    `tools/rebuild_domain_graph.py` CLI를 구현한다.
    source summaries를 읽고 entity extraction, relation/fact extraction, graph upsert를 수행한다.
    옵션은 --db-path, --wiki-root, --entities-dir, --graph-dir, --dry-run, --source-id, --reset-domain-graph, --verbose를 지원한다.
    rebuild는 idempotent해야 하고 dry-run은 DB를 변경하지 않아야 한다.

### Task 6 prompt

    v08 Task 6을 수행한다.
    DB graph를 `graph/nodes.json`, `graph/edges.json`, `graph/domain_graph.json`, `graph/entity_index.json`으로 export하는 기능을 구현한다.
    JSON은 deterministic하고 valid해야 한다.
    entity_index는 query entity matching에서 사용할 수 있도록 alias -> node_id mapping을 포함해야 한다.

### Task 7 prompt

    v08 Task 7을 수행한다.
    `graph/GRAPH_REPORT.md`를 생성하는 report generator를 구현한다.
    Summary, Node Counts, Edge Counts, Top Mentioned Jobs/Patches/Skills, Quality Warnings 섹션을 포함한다.
    report만 읽어도 현재 graph 상태를 파악할 수 있어야 한다.

### Task 8 prompt

    v08 Task 8을 수행한다.
    graph 기반 derived wiki generator를 구현한다.
    `wiki/jobs/*.md`, `wiki/patches/*.md`, `wiki/skills/*.md`를 생성하고, 각 문서에 related sources와 graph links를 포함한다.
    `wiki/index.md`에 derived wiki 링크 섹션을 추가 또는 갱신한다.
    같은 입력으로 두 번 실행해도 결과가 안정적이어야 한다.

### Task 9 prompt

    v08 Task 9를 수행한다.
    ask pipeline에 graph-aware hybrid retrieval을 추가한다.
    질문에서 entity를 match하고, graph neighborhood를 조회한 뒤, 기존 FTS result와 병합한다.
    graph result가 없으면 기존 FTS-only fallback이 동작해야 한다.
    `건브 7.5 변경점 알려줘` 질문에서 job:gunbreaker와 patch:7_5가 match되는 테스트를 추가한다.

### Task 10 prompt

    v08 Task 10을 수행한다.
    v08 end-to-end smoke test를 작성한다.
    fixture source summary 하나로 domain graph rebuild, derived wiki generation, graph report generation, hybrid retrieval까지 검증한다.
    실제 DB를 오염시키지 않도록 tmp DB 또는 transaction rollback을 사용한다.

---

## 19. 최종 산출물 체크리스트

구현 완료 후 다음 파일/디렉터리를 확인한다.

    data/ffxiv_entities/jobs.json
    data/ffxiv_entities/skills.json
    data/ffxiv_entities/patches.json

    graph/nodes.json
    graph/edges.json
    graph/domain_graph.json
    graph/entity_index.json
    graph/GRAPH_REPORT.md

    wiki/jobs/
    wiki/patches/
    wiki/skills/

    tools/rebuild_domain_graph.py
    tools/generate_derived_wiki.py
    tools/generate_graph_report.py

    tests/test_entity_extractor.py
    tests/test_relation_extractor.py
    tests/test_domain_graph_rebuild.py
    tests/test_derived_wiki.py
    tests/test_graph_report.py
    tests/test_hybrid_retrieval.py
    tests/test_v08_e2e.py

최종 확인 명령:

    pytest
    python tools/rebuild_domain_graph.py --dry-run --verbose
    python tools/rebuild_domain_graph.py --verbose
    python tools/generate_derived_wiki.py --verbose
    python tools/generate_graph_report.py

---

## 20. 핵심 요약

v08 구현의 핵심은 다음 한 문장이다.

    Source summary 중심 FTS RAG를 FFXIV domain entity graph와 derived wiki를 가진 hybrid Graph RAG로 확장한다.

가장 중요한 성공 사례:

    질문:
      건브 7.5 변경점 알려줘

    내부 동작:
      건브 -> job:gunbreaker
      7.5 -> patch:7_5
      graph에서 관련 Fact / Skill / SourceDocument / WikiPage 회수
      FTS 결과와 병합
      source-grounded answer context 구성

이 동작이 가능하면 v08은 성공으로 본다.
