# Graph Layer Design (v0.2)

> Date: 2026-05-14
> Status: Design draft

---

## 1. Objective

Build a lightweight entity-relationship graph over existing wiki documents. This enables queries like `patch:7.5 → AFFECTS → job:black_mage` that FTS5 alone cannot answer.

The graph layer sits between `wiki/source_summaries/` and the answer pipeline:

```
wiki/source_summaries/*.md
  ↓
build_graph.py (pattern-based + optional LLM)
  ↓
graph_nodes / graph_edges tables (SQLite)
  ↓
graph/nodes.json + graph/edges.json (export)
  ↓
graph_path.py (query CLI)
  ↓
answer.py (future: graph-enhanced context)
```

---

## 2. Extraction Strategy (Hybrid)

### Phase A — Pattern-based (always runs, deterministic)

| Pattern | Example Input | Output |
|---|---|---|
| Frontmatter fields | `patch: "7.5"` → Patch node `patch:7.5` | Entity node |
| Frontmatter fields | `job: "black_mage"` → Job node `job:black_mage` | Entity node |
| Frontmatter fields | `raid: "arcadion_savage_3"` → Raid node `raid:arcadion_savage_3` | Entity node |
| Co-occurrence in same page | patch + job in one page → edge | `patch:7.5 --AFFECTS--> job:black_mage` |
| `[[wikilink]]` in body | `[[patch_7_5]]` → edge | `current --MENTIONS--> patch:7_5` |
| Wiki file existence | file exists at `wiki/jobs/black_mage.md` | WikiPage node `page:black_mage` |

### Phase B — LLM-enhanced (optional, `--llm-enhanced` flag)

- Reads each wiki page body
- Sends to LLM with `prompts/graph_extractor.md` prompt
- Extracts implicit relationships (skill names, mechanics, item references not in wikilinks)
- Produces `EXTRACTED` or `AMBIGUOUS` confidence edges

---

## 3. Node Types

Defined in `docs/specs/01-architecture.md` §6:

| Type | ID Format | Example |
|---|---|---|
| `Patch` | `patch:{version}` | `patch:7.5` |
| `Job` | `job:{name}` | `job:black_mage` |
| `Skill` | `skill:{name}` | `skill:flare` |
| `Raid` | `raid:{name}` | `raid:arcadion_savage_3` |
| `Mechanic` | `mech:{name}` | `mech:limit_cut` |
| `Item` | `item:{name}` | `item:raid_food_hq` |
| `Macro` | `macro:{name}` | `macro:savage_3` |
| `BIS` | `bis:{job}_{patch}` | `bis:black_mage_7_5` |
| `WikiPage` | `page:{page_id}` | `page:src_2026...` |
| `Guide` | `guide:{name}` | `guide:black_mage_opener` |

---

## 4. Edge Types

| Type | Direction | Example |
|---|---|---|
| `AFFECTS` | Patch → Job/Raid | `patch:7.5 → AFFECTS → job:black_mage` |
| `MODIFIES` | Patch → Skill | `patch:7.5 → MODIFIES → skill:flare` |
| `HAS_SKILL` | Job → Skill | `job:black_mage → HAS_SKILL → skill:flare` |
| `HAS_MACRO` | Raid → Macro | `raid:savage_3 → HAS_MACRO → macro:savage_3` |
| `HAS_BIS` | Job → BIS | `job:black_mage → HAS_BIS → bis:black_mage_7_5` |
| `MENTIONS` | Any → Any | `page:src_... → MENTIONS → patch:7.5` |
| `RELATED_TO` | Any → Any | `job:black_mage → RELATED_TO → raid:arcadion_savage_3` |

Edge confidence levels: `EXTRACTED` (explicit in source), `INFERRED` (derived from co-occurrence), `AMBIGUOUS` (uncertain).

---

## 5. Tools

### 5a. `tools/build_graph.py`

```bash
# Build/refresh entire graph from all wiki pages
python tools/build_graph.py

# Incremental update from a single source
python tools/build_graph.py --source-id src_20260514_...

# Include LLM-based extraction
python tools/build_graph.py --llm-enhanced
```

Algorithm:

```
scan wiki/source_summaries/*.md
for each file:
  parse frontmatter via regex (---\n...\n---)
  extract patch/job/raid fields → upsert nodes
  if both patch and job exist in same page: upsert edge AFFECTS
  extract [[wikilink]] patterns → upsert edges MENTIONS
  if --llm-enhanced: send body to LLM for additional extraction

export graph/nodes.json, graph/edges.json
```

DB operations use `INSERT ... ON CONFLICT(id) DO UPDATE` (upsert) so repeated runs are idempotent.

### 5b. `tools/graph_path.py`

```bash
# Direct relationship query
python tools/graph_path.py --source patch:7.5 --target job:black_mage

# Breadth-first exploration
python tools/graph_path.py --node job:black_mage --depth 2

# All edges from a source
python tools/graph_path.py --source patch:7.5
```

Query logic:
- `--source + --target`: `SELECT * FROM graph_edges WHERE source_id=? AND target_id=?`
- `--node + --depth`: Application-level BFS (up to depth 3, SQLite recursive CTE may work)
- All results as JSON

---

## 6. File Changes

| File | Action |
|---|---|
| `tools/build_graph.py` | **Create** — ~150 lines |
| `tools/graph_path.py` | **Create** — ~100 lines |
| `prompts/graph_extractor.md` | **Create** — LLM extraction prompt (Phase 2) |
| `graph/nodes.json` | **Auto-generated** by build_graph |
| `graph/edges.json` | **Auto-generated** by build_graph |
| `tools/init_db.py` | No change (tables already exist) |

---

## 7. Verification

```bash
# Build graph from existing wiki pages
python tools/build_graph.py

# Check exported JSON files
ls -la graph/nodes.json graph/edges.json

# Query relationships
python tools/graph_path.py --source patch:7.5 --target job:black_mage

# Exploratory query
python tools/graph_path.py --node job:black_mage --depth 2

# Incremental rebuild
python tools/build_graph.py --source-id src_20260514_...
```

---

## 8. Out of Scope (v0.2)

- Graph visualization / UI
- Graph-based answer enhancement (answer.py integration, v0.3)
- Granular entity aliasing via `config/aliases.yaml` (Phase 2)
- Auto-pruning stale nodes/edges
