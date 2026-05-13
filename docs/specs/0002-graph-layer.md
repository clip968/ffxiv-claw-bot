# Spec 0002: Graph Layer

## Status

Accepted

## Scope

이 spec은 v0.2 graph layer의 현재 구현 계약을 정의한다.

현재 구현 파일:

- `tools/build_graph.py`
- `tools/graph_path.py`
- `tools/search_kb.py`
- `tools/answer.py`
- `graph/nodes.json`
- `graph/edges.json`
- `db/ffxiv.sqlite`

## Graph node / edge 개념

graph는 wiki/source 관계를 보조 근거로 표현한다.

현재 deterministic 구현은 `wiki_pages`와 `source_ids`를 기반으로 다음 node를 만든다.

- `page:<wiki_page_id>`: WikiPage node
- `src:<source_id>`: SourceDocument node

현재 edge:

- `SOURCE_OF`: source document -> wiki page

edge id 형식:

```text
<source_id>--<edge_type>--<target_id>
```

## Deterministic graph 생성 원칙

`tools/build_graph.py`는 LLM 없이 DB의 `wiki_pages` 값을 기반으로 graph를 생성한다.

반복 실행 시 `INSERT ... ON CONFLICT(id) DO UPDATE`를 사용해 node와 edge를 upsert한다.

`--llm-enhanced` 옵션은 CLI에 존재하지만 현재 placeholder이며 실제 LLM extraction은 구현되어 있지 않다.

## build_graph.py 역할

전체 graph 생성:

```bash
python tools/build_graph.py
```

특정 source만 처리:

```bash
python tools/build_graph.py --source-id <source_id>
```

현재 동작:

1. `wiki_pages`를 조회한다.
2. 각 wiki page를 `WikiPage` node로 upsert한다.
3. `wiki_pages.source_ids` JSON을 읽는다.
4. 각 source id를 `SourceDocument` node로 upsert한다.
5. source document에서 wiki page로 `SOURCE_OF` edge를 upsert한다.
6. `graph/nodes.json`과 `graph/edges.json`으로 export한다.

## graph_path.py 역할

`tools/graph_path.py`는 `graph_edges`를 조회하는 CLI다.

source node에서 나가는 edge 조회:

```bash
python tools/graph_path.py --source src:<source_id>
```

source/target 직접 관계 조회:

```bash
python tools/graph_path.py --source src:<source_id> --target page:<wiki_page_id>
```

BFS 조회:

```bash
python tools/graph_path.py --node page:<wiki_page_id> --depth 2
```

`--source`도 `--node`도 없으면 `status: error`를 출력한다.

## search 결과의 graph path 포함 방식

`tools/search_kb.py`는 검색된 `wiki_fts.page_id`에 대해 `page:<page_id>` graph node를 만들고, 해당 node가 source 또는 target인 edge를 조회한다.

결과의 `graph_paths`는 문자열 목록이다.

```text
<source_id> --<edge_type>--> <target_id>
```

`tools/answer.py`는 context pack에 `graph_paths`를 포함한다. `--format text` 출력에서는 "관계 그래프" 섹션에 graph path를 표시한다.

## 원칙

graph는 답변 보조 근거이며 원문 출처를 대체하지 않는다.

FFXIV 답변은 `wiki/source_summaries`와 `sources`를 통해 추적 가능한 원문 근거를 우선한다. graph path는 관련 문서 연결을 보강하는 역할이다.

## 성공 기준

- `build_graph.py`가 `wiki_pages` 기반 node/edge를 생성한다.
- 생성 결과가 `graph_nodes`, `graph_edges`에 upsert된다.
- 생성 결과가 `graph/nodes.json`, `graph/edges.json`으로 export된다.
- `graph_path.py`가 source, direct, BFS query를 JSON으로 출력한다.
- `search_kb.py` 결과에 `graph_paths` 필드가 포함된다.
- `answer.py` context pack에 `graph_paths` 필드가 포함된다.

## 확인 명령

```bash
python tools/build_graph.py
python tools/build_graph.py --source-id <source_id>
python tools/graph_path.py --source src:<source_id>
python tools/graph_path.py --source src:<source_id> --target page:<wiki_page_id>
python tools/graph_path.py --node page:<wiki_page_id> --depth 2
python tools/search_kb.py "lodestone"
python tools/answer.py "lodestone"
```

현재 graph layer 전용 unittest는 TODO다.
