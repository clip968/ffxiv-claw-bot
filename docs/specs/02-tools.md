# Tool Layer 명세

> 원본: Notion "ffxiv bot" §8 Tool Layer 명세
> 동기화: 2026-05-14

OpenClaw agent가 직접 파일을 마구 읽는 구조는 피한다. 대신 기능별 tool을 명확히 둔다.

---

## 8.1 init_db

```
python tools/init_db.py
```

역할:

```
- db/ffxiv.sqlite 생성
- sources, wiki_pages, wiki_fts, graph_nodes, graph_edges, ingest_log 생성
```

성공 기준:

```
db/ffxiv.sqlite 파일 생성
모든 테이블 생성
```

---

## 8.2 ingest_url

```
python tools/ingest_url.py "https://example.com/guide"
```

역할:

```
- URL 원문 다운로드
- title/body 추출
- raw/urls/에 저장
- content hash 계산
- sources 테이블에 metadata 저장
- 중복 URL 또는 중복 hash면 재저장하지 않음
```

출력 예시:

```json
{
  "status": "ok",
  "source_id": "src_20260513_0001",
  "raw_path": "raw/urls/example_guide.html",
  "deduplicated": false
}
```

---

## 8.3 compile_wiki

```
python tools/compile_wiki.py --source-id src_20260513_0001
```

역할:

```
- raw 문서를 읽음
- FFXIV 문서 타입 분류
- patch/job/raid/entity 추출
- markdown wiki 생성
- wiki_pages 테이블 갱신
```

출력 예시:

```json
{
  "status": "ok",
  "created_pages": [
    "wiki/patch/7_5.md",
    "wiki/jobs/black_mage/7_5.md"
  ]
}
```

---

## 8.4 build_graph (예정)

```
python tools/build_graph.py --changed-only
```

역할:

```
- wiki 문서에서 entity 추출
- nodes.json, edges.json 생성
- graph_nodes, graph_edges 테이블 갱신
- confidence 부여
```

---

## 8.5 index_fts (보류)

```
python tools/index_fts.py --changed-only
```

역할:

```
- wiki markdown body를 추출
- wiki_fts 테이블 갱신
```

현재는 compile_wiki.py가 FTS 갱신까지 수행하므로 별도 분리는 보류.
나중에 다음 조건이 생기면 분리:
- wiki 문서 수동 수정
- 전체 wiki 재색인 필요
- compile_wiki 없이 FTS만 갱신
- batch indexing 필요

---

## 8.6 search_kb

```
python tools/search_kb.py "흑마 7.5 변경점"
```

역할:

```
- query_parser로 entity 후보 추출
- metadata filter 적용
- FTS 검색
- graph 1~2 hop 확장
- 답변용 context pack 반환
```

출력 예시:

```json
{
  "query": "흑마 7.5 변경점",
  "entities": ["job:black_mage", "patch:7.5"],
  "pages": [
    {
      "path": "wiki/jobs/black_mage/7_5.md",
      "score": 0.91,
      "reason": "job+patch metadata match"
    }
  ],
  "graph_paths": [
    "patch:7.5 -> AFFECTS -> job:black_mage"
  ]
}
```

---

## 8.7 answer

```
python tools/answer.py "흑마 7.5 변경점 알려줘"
```

역할:

```
- search_kb 결과를 가져옴
- context pack을 생성
- 근거 기반 답변 생성
- 출처와 확실도를 함께 출력
```

답변 형식:

```
핵심 요약:
...

상세 설명:
...

근거:
- wiki/jobs/black_mage/7_5.md
- raw/patchnotes/7_5_official.html

확실도:
공식 패치노트 기반 / 사용자 문서 기반 / 추론 포함
```
