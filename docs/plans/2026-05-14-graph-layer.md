# Graph Layer Implementation Plan (v0.2)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a lightweight entity-relationship graph layer over existing wiki documents, enabling `patch:7.5 → AFFECTS → job:black_mage` style queries.

**Architecture:** Two CLI tools — `build_graph.py` extracts entities/edges from wiki markdown (frontmatter + wikilinks + body keywords) and persists to `graph_nodes`/`graph_edges` DB tables + JSON export. `graph_path.py` queries the graph via direct lookups and BFS traversal.

**Tech Stack:** Python 3.10+, SQLite3, argparse, JSON, regex

---

### File Changes Overview

| File | Action | Responsibility |
|---|---|---|
| `tools/build_graph.py` | **Create** | Scan wiki files, extract entities + edges, upsert DB, export JSON |
| `tests/test_build_graph.py` | **Create** | Test extraction logic in isolation |
| `tools/graph_path.py` | **Create** | Query graph via CLI (direct + BFS) |
| `tests/test_graph_path.py` | **Create** | Test query logic against known graph state |
| `graph/nodes.json` | **Auto-generated** | Export of all graph_nodes |
| `graph/edges.json` | **Auto-generated** | Export of all graph_edges |

---

### Task 1: `tools/build_graph.py` — core extraction + DB persistence

**Files:**
- Create: `tools/build_graph.py`
- Create: `tests/test_build_graph.py`

- [ ] **Step 1: Write failing test for frontmatter parsing**

```python
# tests/test_build_graph.py
from tools.build_graph import parse_frontmatter

def test_parse_frontmatter_with_fields():
    content = """---
id: test_page
type: job_patch_change
title: "흑마도사 7.5 변경점"
patch: "7.5"
job: "black_mage"
raid: "arcadion_savage_3"
---

# Body content
"""
    result = parse_frontmatter(content)
    assert result["patch"] == "7.5"
    assert result["job"] == "black_mage"
    assert result["raid"] == "arcadion_savage_3"

def test_parse_frontmatter_empty():
    content = "# No frontmatter\n\nJust body"
    result = parse_frontmatter(content)
    assert result == {}

def test_parse_frontmatter_partial():
    content = """---
patch: "7.5"
---

# Body
"""
    result = parse_frontmatter(content)
    assert result["patch"] == "7.5"
    assert "job" not in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_build_graph.py::test_parse_frontmatter_with_fields tests/test_build_graph.py::test_parse_frontmatter_empty tests/test_build_graph.py::test_parse_frontmatter_partial -v`

Expected: FAIL (ImportError: no module tools.build_graph)

- [ ] **Step 3: Implement `parse_frontmatter()`**

```python
# tools/build_graph.py (partial)
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parse_frontmatter(content: str) -> dict[str, str]:
    """Extract YAML-like frontmatter fields from markdown content.
    
    Handles format:
    ---
    key: "value"
    key2: value
    ---
    """
    m = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not m:
        return {}
    
    fields: dict[str, str] = {}
    for line in m.group(1).splitlines():
        line = line.strip()
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            fields[key] = val
    return fields
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_build_graph.py -v`

Expected: PASS (3 tests)

- [ ] **Step 5: Write failing test for wikilink extraction**

```python
# tests/test_build_graph.py (add these)
from tools.build_graph import extract_wikilinks

def test_extract_wikilinks_basic():
    content = "See [[patch_7_5]] and [[job_black_mage]] for details."
    result = extract_wikilinks(content)
    assert result == ["patch_7_5", "job_black_mage"]

def test_extract_wikilinks_none():
    content = "No links here."
    result = extract_wikilinks(content)
    assert result == []

def test_extract_wikilinks_malformed():
    content = "Broken [[link and also [[valid_link]] here"
    result = extract_wikilinks(content)
    assert result == ["valid_link"]
```

- [ ] **Step 6: Run test to verify it fails**

Run: `python -m pytest tests/test_build_graph.py::test_extract_wikilinks_basic tests/test_build_graph.py::test_extract_wikilinks_none tests/test_build_graph.py::test_extract_wikilinks_malformed -v`

Expected: FAIL (ImportError)

- [ ] **Step 7: Implement `extract_wikilinks()`**

```python
# tools/build_graph.py (add)
def extract_wikilinks(content: str) -> list[str]:
    """Extract [[wikilink]] references from markdown content."""
    return re.findall(r"\[\[([^\]]+)\]\]", content)
```

- [ ] **Step 8: Run test to verify it passes**

Run: `python -m pytest tests/test_build_graph.py::test_extract_wikilinks_basic tests/test_build_graph.py::test_extract_wikilinks_none tests/test_build_graph.py::test_extract_wikilinks_malformed -v`

Expected: PASS (3 tests)

- [ ] **Step 9: Write failing test for entity extraction from body keywords**

```python
# tests/test_build_graph.py (add)
from tools.build_graph import extract_body_entities

def test_extract_body_entities_patch():
    content = "This covers Patch 7.5 and related changes."
    result = extract_body_entities(content)
    assert "patch:7.5" in result

def test_extract_body_entities_job():
    content = "Black Mage rotation changes in 7.5"
    result = extract_body_entities(content)
    # "Black Mage" should map to job:black_mage
    assert "job:black_mage" in result

def test_extract_body_entities_none():
    content = "General discussion."
    result = extract_body_entities(content)
    assert result == []
```

- [ ] **Step 10: Run test to verify it fails**

Run: `python -m pytest tests/test_build_graph.py::test_extract_body_entities_patch tests/test_build_graph.py::test_extract_body_entities_job tests/test_build_graph.py::test_extract_body_entities_none -v`

Expected: FAIL (ImportError)

- [ ] **Step 11: Implement `extract_body_entities()`**

```python
# tools/build_graph.py (add)
import json
import sqlite3

DB_PATH = ROOT / "db" / "ffxiv.sqlite"

# Regex patterns for entity detection in body text
ENTITY_PATTERNS: list[tuple[str, str, re.Pattern]] = [
    ("patch", "patch:{ver}", re.compile(r"(?:patch|패치)\s*(\d+[\._]\d+)", re.IGNORECASE)),
    ("job", "job:{name}", re.compile(r"(Black\s*Mage|BLM|흑마|White\s+Mage|WHM|학자)", re.IGNORECASE)),
    ("raid", "raid:{name}", re.compile(r"(Arcadion|에덴|영식)", re.IGNORECASE)),
]

# Simple job name mapping
JOB_NAMES: dict[str, str] = {
    "black mage": "black_mage",
    "blm": "black_mage",
    "흑마": "black_mage",
    "white mage": "white_mage",
    "whm": "white_mage",
    "scholar": "scholar",
    "sch": "scholar",
}


def extract_body_entities(content: str) -> list[dict]:
    """Scan body text for known entity patterns.
    
    Returns list of {id, type, name} dicts.
    """
    entities: list[dict] = []
    seen: set[str] = set()
    
    for ent_type, id_template, pattern in ENTITY_PATTERNS:
        for m in pattern.finditer(content):
            raw = m.group(1).lower().strip()
            
            if ent_type == "job":
                # Map job name to canonical ID
                canonical = JOB_NAMES.get(raw, raw.replace(" ", "_"))
                entity_id = f"job:{canonical}"
                name = m.group(1)  # Original display name
            elif ent_type == "patch":
                ver = raw.replace("_", ".")
                entity_id = f"patch:{ver}"
                name = f"Patch {ver}"
            elif ent_type == "raid":
                entity_id = f"raid:{raw.replace(' ', '_').lower()}"
                name = m.group(1)
            else:
                continue
            
            if entity_id not in seen:
                seen.add(entity_id)
                entities.append({"id": entity_id, "type": ent_type.capitalize(), "name": name})
    
    return entities
```

- [ ] **Step 12: Run test to verify it passes**

Run: `python -m pytest tests/test_build_graph.py::test_extract_body_entities_patch tests/test_build_graph.py::test_extract_body_entities_job tests/test_build_graph.py::test_extract_body_entities_none -v`

Expected: PASS (3 tests)

- [ ] **Step 13: Write failing test for `extract_entities_from_wiki_page()` (integration)**

```python
# tests/test_build_graph.py (add)
from pathlib import Path
from tools.build_graph import extract_entities_from_wiki_page

def test_extract_entities_from_page(tmp_path):
    content = """---
patch: "7.5"
job: "black_mage"
---

# Test

See [[patch_notes_7_5]] for details.

Black Mage rotation changes discussed here.
"""
    page_path = tmp_path / "test_page.md"
    page_path.write_text(content, encoding="utf-8")
    
    result = extract_entities_from_wiki_page(str(page_path))
    # Should have 2 nodes from frontmatter
    assert "patch:7.5" in result["nodes"]
    assert "job:black_mage" in result["nodes"]
    # Should have MENTIONS edge from wikilink
    assert any(e["type"] == "MENTIONS" for e in result["edges"])
```

- [ ] **Step 14: Run test to verify it fails**

Run: `python -m pytest tests/test_build_graph.py::test_extract_entities_from_page -v`

Expected: FAIL (ImportError)

- [ ] **Step 15: Implement `extract_entities_from_wiki_page()`**

```python
# tools/build_graph.py (add)
def extract_entities_from_wiki_page(page_path: str) -> dict:
    """Extract nodes and edges from a single wiki markdown page.
    
    Returns:
    {
        "page_id": "...",
        "nodes": {"entity_id": {type, name}, ...},
        "edges": [{"source": ..., "target": ..., "type": ...}, ...]
    }
    """
    content = Path(page_path).read_text(encoding="utf-8")
    fm = parse_frontmatter(content)
    
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    
    # Extract page_id from path
    page_path_obj = Path(page_path)
    page_id = f"page:{page_path_obj.stem}"
    nodes[page_id] = {"type": "WikiPage", "name": page_path_obj.stem}
    
    # Node types from frontmatter fields
    field_node_map = {
        "patch": ("patch:{val}", "Patch"),
        "job": ("job:{val}", "Job"),
        "raid": ("raid:{val}", "Raid"),
    }
    
    for field, (id_template, node_type) in field_node_map.items():
        val = fm.get(field)
        if val:
            node_id = id_template.replace("{val}", val)
            nodes[node_id] = {"type": node_type, "name": val}
    
    # Edge from co-occurrence: if patch+job in same page → AFFECTS
    patch_id = f"patch:{fm['patch']}" if "patch" in fm else None
    job_id = f"job:{fm['job']}" if "job" in fm else None
    if patch_id and job_id:
        edges.append({
            "source": patch_id, "target": job_id, "type": "AFFECTS",
            "confidence": "EXTRACTED", "source_page": page_path,
        })
    
    # Edges from [[wikilinks]] → MENTIONS
    wikilinks = extract_wikilinks(content)
    for link in wikilinks:
        edges.append({
            "source": page_id, "target": link, "type": "MENTIONS",
            "confidence": "EXTRACTED", "source_page": page_path,
        })
    
    # Body entity detection → RELATED_TO edges
    if not fm:  # Only for pages without structured frontmatter
        body_entities = extract_body_entities(content)
        for ent in body_entities:
            if ent["id"] not in nodes:
                nodes[ent["id"]] = {"type": ent["type"], "name": ent["name"]}
            edges.append({
                "source": page_id, "target": ent["id"], "type": "RELATED_TO",
                "confidence": "INFERRED", "source_page": page_path,
            })
    
    return {"page_id": page_id, "nodes": nodes, "edges": edges}
```

- [ ] **Step 16: Run test to verify it passes**

Run: `python -m pytest tests/test_build_graph.py::test_extract_entities_from_page -v`

Expected: PASS

- [ ] **Step 17: Write failing test for DB upsert**

```python
# tests/test_build_graph.py (add)
import sqlite3
from tools.build_graph import upsert_nodes, upsert_edges

def test_upsert_nodes(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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
    """)
    
    nodes = {"patch:7.5": {"type": "Patch", "name": "7.5"},
             "job:black_mage": {"type": "Job", "name": "black_mage"}}
    upsert_nodes(conn, nodes)
    
    count = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
    assert count == 2
    
    # Upsert again (should not duplicate)
    upsert_nodes(conn, nodes)
    count = conn.execute("SELECT COUNT(*) FROM graph_nodes").fetchone()[0]
    assert count == 2
```

- [ ] **Step 18: Run test to verify it fails**

Run: `python -m pytest tests/test_build_graph.py::test_upsert_nodes -v`

Expected: FAIL (ImportError)

- [ ] **Step 19: Implement `upsert_nodes()` and `upsert_edges()`**

```python
# tools/build_graph.py (add)
def upsert_nodes(conn: sqlite3.Connection, nodes: dict[str, dict]) -> None:
    """Upsert graph_nodes: INSERT ON CONFLICT DO UPDATE."""
    for node_id, info in nodes.items():
        conn.execute("""
            INSERT INTO graph_nodes (id, type, name, aliases, properties)
            VALUES (?, ?, ?, NULL, NULL)
            ON CONFLICT(id) DO UPDATE SET
              type = excluded.type,
              name = excluded.name
        """, (node_id, info["type"], info["name"]))
    conn.commit()


def make_edge_id(src: str, tgt: str, etype: str) -> str:
    return f"{src}--{etype}--{tgt}"


def upsert_edges(conn: sqlite3.Connection, page_edges: list[dict]) -> None:
    """Upsert graph_edges: INSERT ON CONFLICT DO UPDATE."""
    for e in page_edges:
        edge_id = make_edge_id(e["source"], e["target"], e["type"])
        conn.execute("""
            INSERT INTO graph_edges (id, source_id, target_id, type, confidence, score, source_page_id, properties)
            VALUES (?, ?, ?, ?, ?, NULL, ?, NULL)
            ON CONFLICT(id) DO UPDATE SET
              type = excluded.type,
              confidence = excluded.confidence,
              source_page_id = excluded.source_page_id
        """, (edge_id, e["source"], e["target"], e["type"], e["confidence"], e["source_page"]))
    conn.commit()
```

- [ ] **Step 20: Run test to verify it passes**

Run: `python -m pytest tests/test_build_graph.py::test_upsert_nodes -v`

Expected: PASS

- [ ] **Step 21: Write failing test for JSON export**

```python
# tests/test_build_graph.py (add)
from tools.build_graph import export_json

def test_export_json(tmp_path):
    nodes = [{"id": "patch:7.5", "type": "Patch", "name": "7.5"}]
    edges = [{"source": "patch:7.5", "target": "job:black_mage", "type": "AFFECTS"}]
    
    export_json(nodes, edges, str(tmp_path))
    
    import json
    nodes_data = json.loads((tmp_path / "nodes.json").read_text())
    edges_data = json.loads((tmp_path / "edges.json").read_text())
    assert len(nodes_data) == 1
    assert len(edges_data) == 1
```

- [ ] **Step 22: Run test to verify it fails**

Run: `python -m pytest tests/test_build_graph.py::test_export_json -v`

Expected: FAIL (ImportError)

- [ ] **Step 23: Implement `export_json()` and `main()`**

```python
# tools/build_graph.py (add)
def export_json(nodes: list[dict], edges: list[dict], output_dir: str) -> None:
    """Export nodes and edges as JSON files."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "nodes.json").write_text(
        json.dumps(nodes, ensure_ascii=False, indent=2), encoding="utf-8")
    (out / "edges.json").write_text(
        json.dumps(edges, ensure_ascii=False, indent=2), encoding="utf-8")


def build_graph(source_id: str | None = None, llm_enhanced: bool = False) -> dict:
    """Main build function: scan wiki, extract entities, upsert DB, export JSON."""
    summary_dir = ROOT / "wiki" / "source_summaries"
    
    if source_id:
        files = [summary_dir / f"{source_id}.md"]
    else:
        files = sorted(summary_dir.glob("*.md"))
    
    all_nodes: dict[str, dict] = {}
    all_edges: list[dict] = []
    processed = 0
    
    with sqlite3.connect(DB_PATH) as conn:
        for f in files:
            if not f.exists():
                continue
            result = extract_entities_from_wiki_page(str(f))
            all_nodes.update(result["nodes"])
            all_edges.extend(result["edges"])
            upsert_nodes(conn, result["nodes"])
            upsert_edges(conn, result["edges"])
            processed += 1
        
        # Fetch all from DB for export
        db_nodes = [
            dict(row) for row in
            conn.execute("SELECT id, type, name, aliases, properties FROM graph_nodes ORDER BY id")
        ]
        db_edges = [
            dict(row) for row in
            conn.execute("SELECT id, source_id, target_id, type, confidence, score, source_page_id, source_ids, properties FROM graph_edges ORDER BY id")
        ]
    
    export_json(db_nodes, db_edges, str(ROOT / "graph"))
    
    return {
        "status": "ok",
        "processed": processed,
        "nodes": len(all_nodes),
        "edges": len(all_edges),
        "db_nodes": len(db_nodes),
        "db_edges": len(db_edges),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build knowledge graph from wiki pages.")
    parser.add_argument("--source-id", help="Only process a specific source ID")
    parser.add_argument("--llm-enhanced", action="store_true", help="Enable LLM-based extraction (placeholder)")
    args = parser.parse_args()
    
    result = build_graph(args.source_id, args.llm_enhanced)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
```

- [ ] **Step 24: Run all tests to verify**

Run: `python -m pytest tests/test_build_graph.py -v`

Expected: All tests PASS

- [ ] **Step 25: Commit**

Run:
```bash
git add tools/build_graph.py tests/test_build_graph.py
git commit -m "feat: build_graph.py 추가 — wiki markdown → entity/edge 추출 + DB upsert + JSON export"
```

---

### Task 2: `tools/graph_path.py` — graph query CLI

**Files:**
- Create: `tools/graph_path.py`
- Create: `tests/test_graph_path.py`

- [ ] **Step 1: Write failing test for direct source→target query**

```python
# tests/test_graph_path.py
import sqlite3
import json
from pathlib import Path
from tools.graph_path import query_direct, format_json

def test_query_direct_found(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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
    """)
    conn.execute("""
        INSERT INTO graph_edges (id, source_id, target_id, type, confidence, score, source_page_id)
        VALUES ('p7.5--AFFECTS--blm', 'patch:7.5', 'job:black_mage', 'AFFECTS', 'EXTRACTED', NULL, 'wiki/test.md')
    """)
    conn.commit()
    
    edges = query_direct(conn, "patch:7.5", "job:black_mage")
    assert len(edges) == 1
    assert edges[0]["type"] == "AFFECTS"

def test_query_direct_not_found(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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
    """)
    
    edges = query_direct(conn, "patch:7.5", "job:nonexistent")
    assert edges == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_graph_path.py::test_query_direct_found tests/test_graph_path.py::test_query_direct_not_found -v`

Expected: FAIL (ImportError)

- [ ] **Step 3: Implement `query_direct()`**

```python
# tools/graph_path.py
import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "db" / "ffxiv.sqlite"


def query_direct(conn: sqlite3.Connection, source_id: str, target_id: str) -> list[dict]:
    """Find direct edges between source and target."""
    rows = conn.execute(
        "SELECT source_id, target_id, type, confidence, score, source_page_id "
        "FROM graph_edges WHERE source_id = ? AND target_id = ?",
        (source_id, target_id),
    ).fetchall()
    return [dict(r) for r in rows]


def query_by_source(conn: sqlite3.Connection, source_id: str) -> list[dict]:
    """Find all edges from a source node."""
    rows = conn.execute(
        "SELECT source_id, target_id, type, confidence, score, source_page_id "
        "FROM graph_edges WHERE source_id = ?",
        (source_id,),
    ).fetchall()
    return [dict(r) for r in rows]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_graph_path.py::test_query_direct_found tests/test_graph_path.py::test_query_direct_not_found -v`

Expected: PASS

- [ ] **Step 5: Write failing test for BFS traversal**

```python
# tests/test_graph_path.py (add)
from tools.graph_path import query_bfs

def test_query_bfs_depth_1(tmp_path):
    db_path = tmp_path / "test.db"
    conn = sqlite3.connect(db_path)
    conn.executescript("""
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
    """)
    conn.execute("""
        INSERT INTO graph_edges VALUES
        ('e1', 'patch:7.5', 'job:black_mage', 'AFFECTS', 'EXTRACTED', NULL, 'wiki/p7.5', NULL, NULL),
        ('e2', 'patch:7.5', 'raid:arcadion', 'AFFECTS', 'EXTRACTED', NULL, 'wiki/p7.5', NULL, NULL),
        ('e3', 'job:black_mage', 'bis:black_mage_7_5', 'HAS_BIS', 'INFERRED', 0.82, 'wiki/blm', NULL, NULL)
    """)
    conn.commit()
    
    result = query_bfs(conn, "patch:7.5", depth=1)
    assert len(result["edges"]) == 2  # Only depth-1 edges from patch:7.5
    assert "patch:7.5" in result["nodes"]
    assert "job:black_mage" in result["nodes"]
    assert "raid:arcadion" in result["nodes"]
```

- [ ] **Step 6: Run test to verify it fails**

Run: `python -m pytest tests/test_graph_path.py::test_query_bfs_depth_1 -v`

Expected: FAIL (ImportError)

- [ ] **Step 7: Implement `query_bfs()`**

```python
# tools/graph_path.py (add)
def query_bfs(conn: sqlite3.Connection, start_id: str, depth: int = 2) -> dict:
    """BFS traversal from start_id up to given depth.
    
    Returns {"nodes": set, "edges": list} with unique nodes and edges.
    """
    visited_nodes: set[str] = {start_id}
    visited_edges: set[str] = set()
    current: set[str] = {start_id}
    all_edges: list[dict] = []
    
    for _ in range(depth):
        if not current:
            break
        
        placeholders = ",".join("?" for _ in current)
        rows = conn.execute(
            f"SELECT source_id, target_id, type, confidence, score, source_page_id, id "
            f"FROM graph_edges WHERE source_id IN ({placeholders}) OR target_id IN ({placeholders})",
            list(current) + list(current),
        ).fetchall()
        
        next_nodes: set[str] = set()
        for r in rows:
            edge_id = r[-1]
            if edge_id in visited_edges:
                continue
            visited_edges.add(edge_id)
            all_edges.append({
                "source_id": r[0], "target_id": r[1], "type": r[2],
                "confidence": r[3], "score": r[4], "source_page_id": r[5],
            })
            if r[0] not in visited_nodes:
                visited_nodes.add(r[0])
                next_nodes.add(r[0])
            if r[1] not in visited_nodes:
                visited_nodes.add(r[1])
                next_nodes.add(r[1])
        
        current = next_nodes
    
    return {"nodes": sorted(visited_nodes), "edges": all_edges}
```

- [ ] **Step 8: Run test to verify it passes**

Run: `python -m pytest tests/test_graph_path.py::test_query_bfs_depth_1 -v`

Expected: PASS

- [ ] **Step 9: Write failing test for JSON output formatting**

```python
# tests/test_graph_path.py (add)
def test_format_json_direct():
    result = format_json("direct", "patch:7.5", {"target": "job:black_mage"},
                         edges=[{"source_id": "patch:7.5", "target_id": "job:black_mage", "type": "AFFECTS"}])
    parsed = json.loads(result)
    assert parsed["status"] == "ok"
    assert parsed["mode"] == "direct"
    assert parsed["params"]["source"] == "patch:7.5"
    assert parsed["params"]["target"] == "job:black_mage"
    assert len(parsed["edges"]) == 1

def test_format_json_empty():
    result = format_json("bfs", "patch:7.5", {"depth": 2},
                         nodes=[], edges=[])
    parsed = json.loads(result)
    assert parsed["status"] == "ok"
    assert parsed["edges"] == []
    assert parsed["nodes"] == []
```

- [ ] **Step 10: Run test to verify it fails**

Run: `python -m pytest tests/test_graph_path.py::test_format_json_direct tests/test_graph_path.py::test_format_json_empty -v`

Expected: FAIL (ImportError)

- [ ] **Step 11: Implement `format_json()` and `main()`**

```python
# tools/graph_path.py (add)
def format_json(mode: str, source_id: str | None, params: dict,
                nodes: list | None = None, edges: list | None = None) -> str:
    """Format query result as JSON string."""
    result: dict = {
        "status": "ok",
        "mode": mode,
        "params": {"source": source_id, **params},
    }
    if nodes is not None:
        result["nodes"] = nodes
    if edges is not None:
        result["edges"] = edges
    return json.dumps(result, ensure_ascii=False, indent=2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Query knowledge graph.")
    parser.add_argument("--source", help="Source node ID")
    parser.add_argument("--target", help="Target node ID (for direct query)")
    parser.add_argument("--node", help="Start node for BFS traversal")
    parser.add_argument("--depth", type=int, default=2, help="BFS depth (default: 2)")
    args = parser.parse_args()
    
    if not args.source and not args.node:
        print(json.dumps({"status": "error", "message": "Provide --source, --source+--target, or --node+--depth"}))
        return
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        
        if args.source and args.target:
            edges = query_direct(conn, args.source, args.target)
            print(format_json("direct", args.source, {"target": args.target}, edges=edges))
        elif args.source:
            edges = query_by_source(conn, args.source)
            print(format_json("source", args.source, {}, edges=edges))
        elif args.node:
            result = query_bfs(conn, args.node, args.depth)
            print(format_json("bfs", args.node, {"depth": args.depth},
                              nodes=result["nodes"], edges=result["edges"]))


if __name__ == "__main__":
    main()
```

- [ ] **Step 12: Run test to verify it passes**

Run: `python -m pytest tests/test_graph_path.py::test_format_json_direct tests/test_graph_path.py::test_format_json_empty -v`

Expected: PASS

- [ ] **Step 13: Run all tests for graph_path**

Run: `python -m pytest tests/test_graph_path.py -v`

Expected: All PASS

- [ ] **Step 14: Commit**

Run:
```bash
git add tools/graph_path.py tests/test_graph_path.py
git commit -m "feat: graph_path.py 추가 — graph 쿼리 CLI (direct + BFS)"
```

---

### Task 3: End-to-end verification on real data

**Context:** Run against the existing wiki page to verify the full pipeline end-to-end.

- [ ] **Step 1: Run build_graph on existing wiki pages**

Run:
```bash
python tools/build_graph.py
```

Expected output like:
```json
{
  "status": "ok",
  "processed": 1,
  "nodes": 3,
  "edges": 1,
  "db_nodes": 3,
  "db_edges": 1
}
```
(The lodestone page may produce minimal entities since it has no patch/job/raid frontmatter, but body entity detection should find some.)

- [ ] **Step 2: Verify exported JSON files**

Run:
```bash
ls -la graph/nodes.json graph/edges.json
python -c "import json; d=json.load(open('graph/nodes.json')); print(len(d),'nodes'); [print(f'  {n[\"id\"]}: {n[\"type\"]}') for n in d]"
python -c "import json; d=json.load(open('graph/edges.json')); print(len(d),'edges'); [print(f'  {e[\"source_id\"]} --{e[\"type\"]}--> {e[\"target_id\"]}') for e in d]"
```

- [ ] **Step 3: Test graph_path queries**

Run:
```bash
python tools/graph_path.py --source patch:7.5
python tools/graph_path.py --node page:src_20260514_002930_4323e58d --depth 1
```

- [ ] **Step 4: Test incremental build**

Run:
```bash
python tools/build_graph.py --source-id src_20260514_002930_4323e58d
```
Expected: Same result, idempotent.

- [ ] **Step 5: Commit final verification**

Run:
```bash
git add graph/nodes.json graph/edges.json
git commit -m "feat: graph 데이터 초기 생성 (Lodestone page)"
```
