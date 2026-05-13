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

Drive markdown/text raw 처리 지원은 TODO다.

## FTS index rebuild

현재 별도 `index_fts.py`는 없다.

FTS 갱신은 `compile_wiki.py --source-id <source_id>` 실행 중 source 단위로 수행된다.

전체 FTS 재빌드 명령은 TODO다.

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

## Answer smoke test

```bash
python tools/answer.py "lodestone"
python tools/answer.py "lodestone" --format text
```

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
