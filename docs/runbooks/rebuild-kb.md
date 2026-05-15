# Rebuild KB Runbook

이 문서는 현재 레포에서 실제 가능한 로컬 KB 재빌드 명령을 기록한다.

## DB 초기화

```bash
python tools/init_db.py
```

주의:

- `db/ffxiv.sqlite`를 생성 또는 갱신한다.
- 기존 DB 내용 보존/마이그레이션 정책은 TODO다.

## URL ingest

```bash
python tools/ingest_url.py "<URL>"
```

결과 JSON의 `source_id`를 다음 compile 단계에 사용한다.

## Wiki compile

```bash
python tools/compile_wiki.py --source-id <source_id>
```

현재 `compile_wiki.py`는 raw HTML을 읽어 `wiki/source_summaries/<source_id>.md`를 만들고 `wiki_fts`를 갱신한다.
HTML 텍스트 추출은 BeautifulSoup이 설치되어 있으면 BeautifulSoup을 사용하고, 없으면 표준 라이브러리 fallback을 사용한다.

Local Storage에서 snapshot된 Markdown/text source도 같은 방향으로 처리한다. 현재 구현은 `drive_document`, `local_file`, `local_document` source의 raw Markdown/text를 HTML 파싱 없이 그대로 사용한다.

## FTS index rebuild

현재 별도 `index_fts.py`는 없다.

FTS 갱신은 `compile_wiki.py --source-id <source_id>` 실행 중 source 단위로 수행된다.

전체 FTS 재빌드 명령은 TODO다.

## Local Rebuild After Ingest (`tools/local_rebuild.py`)

v04-04 rebuild wrapper that connects compile_wiki → index_fts → build_graph after a successful local ingest.

### Programmatic usage

```python
from tools.local_rebuild import rebuild_after_ingest

result = rebuild_after_ingest(
    ingest_result,
    root_path=Path("."),
    db_path=Path("db/ffxiv.sqlite"),
    dry_run=True,
)
print(result["status"])  # "ok" in dry-run mode
for action in result["actions"]:
    print(action["action"], action["status"])
```

### Partial failure policy

| Condition | Result |
|---|---|
| Upstream ingest `status != "ok"` | `status="skipped"`, no rebuild |
| `compile_wiki` fails | `compile_wiki=failed`, `index_fts=skipped`; `build_graph` continues |
| `build_graph` fails | `status="partial"`, compile success preserved |

### Dry-run result format

```json
{
  "status": "ok",
  "dry_run": true,
  "source_id": "local_001",
  "source_type": "local_document",
  "actions": [
    {"action": "compile_wiki", "source_id": "local_001", "status": "planned", ...},
    {"action": "index_fts",    "source_id": "local_001", "status": "planned", ...},
    {"action": "build_graph",  "source_id": "local_001", "status": "planned", ...}
  ]
}
```

## Graph build

전체 graph build:

```bash
python tools/build_graph.py
```

source 단위 graph build:

```bash
python tools/build_graph.py --source-id <source_id>
```

결과:

- `graph/nodes.json`
- `graph/edges.json`
- `graph_nodes`
- `graph_edges`

## Search smoke test

```bash
python tools/search_kb.py "lodestone"
```

FTS5 query sanitization: user input is sanitized before MATCH to prevent FTS5 syntax errors.
Characters `@`, `/`, `"`, `(`, `)`, `-`, `+`, `*`, `^`, `:` are stripped automatically.
Defense-in-depth catches `sqlite3.OperationalError` and returns empty results.

## Answer smoke test

```bash
python tools/answer.py "lodestone"
python tools/answer.py "lodestone" --format text
```

Answer.py wraps `search_fts()` in try/except for `sqlite3.OperationalError` as a second layer.
If FTS5 still errors or returns no results, `"찾을 수 없습니다"` is produced instead of a crash.

## 전체 재빌드 순서

현재 실제 가능한 source 단위 순서:

```text
python tools/init_db.py
python tools/ingest_url.py "<URL>"
python tools/compile_wiki.py --source-id <source_id>
python tools/build_graph.py --source-id <source_id>
python tools/search_kb.py "lodestone"
python tools/answer.py "lodestone"
```

TODO:

- 기존 raw 전체를 순회하는 재빌드 명령
- 전체 wiki/FTS 재색인 명령
- Drive raw를 compile하는 명령
