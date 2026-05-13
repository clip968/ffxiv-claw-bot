# FFXIV OpenClaw Bot — 전체 설계

> 원본: Notion "ffxiv bot" 페이지 (https://www.notion.so/35f4bf16ed1f80fd9245d782f99be303)
> 동기화: 2026-05-14

---

# 0. 최종 목표

목표는 Discord에서 호출 가능한 FFXIV 전용 OpenClaw agent를 만드는 것이다.

```
Discord
  ↓
OpenClaw agent: ffxiv
  ↓
FFXIV Tool Layer
  ├─ URL/문서/패치노트 수집
  ├─ raw archive 저장
  ├─ LLM Wiki 문서 생성
  ├─ Graphify-inspired 관계 그래프 생성
  ├─ SQLite FTS 검색
  └─ 근거 기반 답변 생성
```

기존 `main` agent는 일반 작업에 그대로 사용하고, FFXIV 관련 요청만 `ffxiv` agent로 분리한다.

```
agent:main
  → 일반 대화, 개발 질문, 기존 Discord 응답

agent:ffxiv
  → 파판14 패치노트, 직업 변경점, 공대 문서, 매크로, BIS, 공략 검색
```

---

# 1. 브런치 프로젝트 참고 포인트

브런치 프로젝트의 핵심 아이디어를 FFXIV bot에 적용하면 다음과 같다.

| 참고 아이디어 | FFXIV bot 적용 방식 |
|---|---|
| 텔레그램으로 자료 저장 | Discord 명령으로 URL, 문서, 메모 저장 |
| 검색 결과를 일회성 답변에만 쓰지 않음 | 모든 원문을 `raw/`에 저장하고 metadata를 남김 |
| LLM Wiki | 원문을 FFXIV 개념 단위의 markdown wiki로 재컴파일 |
| Graphify | 패치, 직업, 스킬, 레이드, 매크로, BIS 관계를 graph로 추출 |
| 임베딩 의존 최소화 | 초기는 SQLite FTS5 + metadata + graph traversal로 구현 |
| 개인 지식 저장소 | Google Drive `FFXIV_KB`와 Discord 저장 요청을 지속 반영 |

중요한 차이는 브런치 프로젝트를 그대로 복제하지 않는다는 점이다. FFXIV는 패치 번호, 직업명, 스킬명, 레이드명처럼 고유명사가 뚜렷하므로 초기 버전에서는 벡터 DB 없이도 실용적인 검색을 만들 수 있다.

---

# 2. 실제 작업 경로

프로젝트 루트는 WSL 기준으로 다음에 둔다.

```
/mnt/d/programming/ffxiv-claw-bot
```

초기 디렉터리 구조는 다음으로 고정한다.

```
/mnt/d/programming/ffxiv-claw-bot/
  ├─ agent.md
  ├─ README.md
  ├─ CLAUDE.md
  ├─ config/
  │   ├─ sources.yaml
  │   ├─ aliases.yaml
  │   └─ tool_config.yaml
  │
  ├─ raw/
  │   ├─ drive/
  │   ├─ urls/
  │   ├─ patchnotes/
  │   └─ discord/
  │
  ├─ wiki/
  │   ├─ source_summaries/
  │   ├─ patch/
  │   ├─ jobs/
  │   ├─ raids/
  │   ├─ mechanics/
  │   ├─ items/
  │   ├─ macros/
  │   ├─ bis/
  │   └─ index.md
  │
  ├─ graph/
  │   ├─ nodes.json
  │   ├─ edges.json
  │   ├─ graph.json
  │   └─ communities.json
  │
  ├─ docs/
  │   └─ specs/
  │
  ├─ db/
  │   └─ ffxiv.sqlite
  │
  ├─ tools/
  │   ├─ init_db.py
  │   ├─ ingest_url.py
  │   ├─ compile_wiki.py
  │   ├─ search_kb.py
  │   ├─ answer.py
  │   ├─ build_graph.py
  │   ├─ graph_path.py
  │   ├─ index_fts.py (보류)
  │   ├─ ingest_discord_note.py (예정)
  │   ├─ sync_drive.py (예정)
  │   └─ crawl_patchnotes.py (예정)
  │
  ├─ prompts/
  │   ├─ answer_policy.md
  │   ├─ wiki_compiler.md (예정)
  │   ├─ entity_extractor.md (예정)
  │   ├─ graph_extractor.md (예정)
  │   └─ query_parser.md (예정)
  │
  └─ tests/
      ├─ fixtures/
      ├─ test_ingest_url.py (예정)
      ├─ test_compile_wiki.py (예정)
      ├─ test_search_kb.py (예정)
      └─ test_graph_path.py (예정)
```

---

# 3. 데이터 소스 설계

초기 데이터 소스는 네 종류로 잡는다.

```
1. 공식 패치노트
2. 사용자가 Discord에서 저장한 URL
3. Google Drive FFXIV_KB 폴더
4. 직접 작성한 공대 문서, 매크로, BIS 시트
```

Google Drive 구조는 다음처럼 둔다.

```
Google Drive/FFXIV_KB/
  ├─ patch_notes/
  ├─ job_guides/
  ├─ raid_guides/
  ├─ static_docs/
  ├─ macros/
  ├─ bis_sheets/
  └─ personal_notes/
```

원문 저장 정책은 다음과 같다.

```
raw/patchnotes/7_5_official.html
raw/urls/lodestone_2026_05_13_xxx.html
raw/drive/black_mage_guide.md
raw/drive/static_rules.xlsx
raw/discord/2026_05_13_note_001.md
```

각 원문에는 metadata를 남긴다.

```json
{
  "source_id": "src_20260513_0001",
  "source_type": "official_patchnote",
  "source_url": "https://example.com/patchnote",
  "title": "Patch 7.5 Notes",
  "language": "ko",
  "patch": "7.5",
  "job": null,
  "raid": null,
  "collected_at": "2026-05-13T12:00:00Z",
  "hash": "sha256...",
  "raw_path": "raw/patchnotes/7_5_official.html"
}
```

---

# 4. SQLite DB 스키마

초기 DB는 `db/ffxiv.sqlite` 하나로 충분하다.

```sql
CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  source_type TEXT NOT NULL,
  title TEXT,
  source_url TEXT,
  raw_path TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  language TEXT,
  patch TEXT,
  job TEXT,
  raid TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS wiki_pages (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  title TEXT NOT NULL,
  path TEXT NOT NULL,
  patch TEXT,
  job TEXT,
  raid TEXT,
  source_ids TEXT NOT NULL,
  confidence TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS wiki_fts USING fts5(
  page_id,
  title,
  body,
  tokenize = 'unicode61'
);

CREATE TABLE IF NOT EXISTS graph_nodes (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL,
  name TEXT NOT NULL,
  aliases TEXT,
  properties TEXT
);

CREATE TABLE IF NOT EXISTS graph_edges (
  id TEXT PRIMARY KEY,
  source_id TEXT NOT NULL,
  target_id TEXT NOT NULL,
  type TEXT NOT NULL,
  confidence TEXT NOT NULL,
  score REAL,
  source_page_id TEXT,
  source_ids TEXT,
  properties TEXT
);

CREATE TABLE IF NOT EXISTS ingest_log (
  id TEXT PRIMARY KEY,
  action TEXT NOT NULL,
  target TEXT NOT NULL,
  status TEXT NOT NULL,
  message TEXT,
  created_at TEXT NOT NULL
);
```

---

# 5. LLM Wiki 설계

LLM Wiki는 원문을 그대로 저장하는 계층이 아니다. 원문을 FFXIV 지식 단위로 다시 분해하고, 서로 연결 가능한 markdown 문서로 재구성하는 계층이다.

예를 들어 공식 패치노트 하나가 들어오면 다음 문서로 쪼갠다.

```
raw/patchnotes/7_5_official.html
  ↓
wiki/patch/7_5.md
wiki/jobs/black_mage/7_5.md
wiki/jobs/warrior/7_5.md
wiki/raids/arcadion_savage_3.md
wiki/items/food_potion_7_5.md
```

위키 문서 frontmatter는 다음 형식으로 통일한다.

```
---
id: job_black_mage_patch_7_5
type: job_patch_change
title: "흑마도사 7.5 변경점"
patch: "7.5"
job: "black_mage"
raid: null
sources:
  - src_20260513_0001
confidence: "source_grounded"
updated_at: "2026-05-13T12:00:00Z"
---

# 흑마도사 7.5 변경점

## 핵심 요약

...

## 변경된 스킬

...

## 플레이 영향

...

## 관련 문서

- [[patch_7_5]]
- [[job_black_mage]]
- [[bis_black_mage_7_5]]
```

문서 타입은 다음으로 시작한다.

```
PatchPage
JobPage
JobPatchChangePage
RaidPage
MechanicPage
MacroPage
BISPage
ItemPage
StaticPage
SourceSummaryPage
```

---

# 6. Graphify-inspired 그래프 설계

Graphify를 그대로 구현하지 않고, FFXIV에 필요한 경량 그래프만 만든다.

노드 타입은 다음으로 시작한다.

```
Patch
Job
Skill
Raid
Mechanic
Item
Macro
BIS
StaticRule
Guide
SourceDocument
WikiPage
```

예시 노드:

```json
{
  "id": "job:black_mage",
  "type": "Job",
  "name": "흑마도사",
  "aliases": ["흑마", "BLM", "Black Mage"]
}
```

```json
{
  "id": "patch:7.5",
  "type": "Patch",
  "name": "Patch 7.5",
  "aliases": ["7.5", "패치 7.5"]
}
```

엣지 타입은 다음으로 시작한다.

```
AFFECTS
MODIFIES
ADDS
REMOVES
HAS_SKILL
HAS_MACRO
HAS_BIS
MENTIONS
RELATED_TO
SOURCE_OF
USED_BY_STATIC
REPLACES
CONFLICTS_WITH
```

예시 엣지:

```json
{
  "source": "patch:7.5",
  "target": "job:black_mage",
  "type": "AFFECTS",
  "confidence": "EXTRACTED",
  "source_page": "wiki/patch/7_5.md"
}
```

```json
{
  "source": "job:black_mage",
  "target": "bis:black_mage_7_5",
  "type": "HAS_BIS",
  "confidence": "INFERRED",
  "score": 0.82,
  "source_page": "wiki/jobs/black_mage/7_5.md"
}
```

confidence는 세 단계로 둔다.

```
EXTRACTED
  원문 또는 wiki 문서에 명시적으로 존재하는 관계

INFERRED
  문서 조합으로 추론한 관계

AMBIGUOUS
  관계 가능성은 있으나 확정하기 어려운 관계
```

---

# 7. 검색 계층

초기 버전에서는 임베딩 모델을 쓰지 않는다.

검색은 다음 순서로 처리한다.

```
사용자 질문
  ↓
query_parser
  - patch, job, raid, skill, item, macro 후보 추출
  ↓
metadata filter
  - patch=7.5, job=black_mage 등으로 후보 축소
  ↓
SQLite FTS5
  - wiki title/body 키워드 검색
  ↓
graph traversal
  - 추출된 entity 기준 1~2 hop 확장
  ↓
context pack 생성
  ↓
answer.py가 근거 기반 답변 생성
```

FFXIV는 고유명사가 많기 때문에 다음 별칭 사전이 중요하다.

```yaml
jobs:
  black_mage:
    ko: ["흑마", "흑마도사"]
    en: ["BLM", "Black Mage"]
  warrior:
    ko: ["전사"]
    en: ["WAR", "Warrior"]

patches:
  "7.5": ["7.5", "패치 7.5", "Patch 7.5"]

raids:
  arcadion_savage_3:
    ko: ["영식 3층", "아르카디아 영식 3층"]
    en: ["AAC Savage 3", "Arcadion Savage 3"]
```

임베딩 추가는 v0.4 이후로 미룬다.

```
v0.1~v0.3
  SQLite FTS5 + metadata + graph traversal

v0.4+
  필요한 경우 BGE-M3 또는 다른 embedding 모델 추가
```

---

# 8. OpenClaw agent 설정 방향

실제 설정 필드는 현재 설치된 OpenClaw schema에서 확인해야 한다. 개념적으로는 다음 방향이다.

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "default": true,
        "workspace": "/home/clip968/.openclaw/workspace"
      },
      {
        "id": "ffxiv",
        "workspace": "/mnt/d/programming/ffxiv-claw-bot",
        "groupChat": {
          "mentionPatterns": [
            "ffxiv",
            "ff14",
            "파판",
            "파판봇"
          ]
        },
        "skills": ["ffxiv-kb"]
      }
    ]
  }
}
```

Discord 사용 예시는 다음과 같다.

```
@claw_bot ffxiv 최신 패치노트 요약해줘
@claw_bot ffxiv 7.5 흑마 변경점 알려줘
@claw_bot ffxiv 이 URL 저장해줘: https://...
@claw_bot ffxiv drive 동기화해줘
@claw_bot ffxiv 우리 공대 3층 매크로 보여줘
@claw_bot ffxiv 흑마랑 이번 BIS 문서가 어떻게 연결돼?
```

안정화 후에는 채널 바인딩을 둔다.

```
#ffxiv-ask
  → agent:ffxiv

#general-ai
  → agent:main
```
