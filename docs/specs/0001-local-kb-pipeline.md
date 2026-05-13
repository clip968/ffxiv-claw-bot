# Spec 0001: Local KB Pipeline

## Status

Accepted

## Scope

이 spec은 v0.1 local KB pipeline의 현재 구현 계약을 정의한다.

현재 구현 파일:

- `tools/init_db.py`
- `tools/ingest_url.py`
- `tools/compile_wiki.py`
- `tools/search_kb.py`
- `tools/answer.py`
- `db/ffxiv.sqlite`
- `raw/urls/`
- `wiki/source_summaries/`

## Pipeline

```text
URL
  -> raw/urls 저장
  -> sources DB 기록
  -> wiki/source_summaries markdown 생성
  -> wiki_fts 색인
  -> search_kb.py 검색
  -> answer.py context pack 생성
```

## Raw 저장 규칙

`tools/ingest_url.py`는 URL을 fetch한 뒤 원문 HTML을 `raw/urls/` 아래에 저장한다.

파일명은 URL host/path를 safe filename으로 바꾼 값과 source id를 조합한다.

```text
raw/urls/<safe_url>_<source_id>.html
```

현재 source id 형식:

```text
src_<YYYYMMDD_HHMMSS>_<uuid8>
```

동일 내용은 `content_hash` 기준으로 중복 저장하지 않는다.

## sources DB 기록

`tools/init_db.py`는 `sources` 테이블을 만든다.

현재 `tools/ingest_url.py`가 기록하는 주요 값:

- `id`: source id
- `source_type`: `url`
- `title`: HTML title 또는 URL host fallback
- `source_url`: 원본 URL
- `raw_path`: `raw/urls/...html`
- `content_hash`: HTML text의 sha256
- `created_at`, `updated_at`: UTC ISO timestamp

`language`, `patch`, `job`, `raid`는 현재 URL ingest 단계에서 자동 추출하지 않는다.

## Wiki markdown 생성

`tools/compile_wiki.py`는 `sources.raw_path`의 HTML을 읽고 BeautifulSoup으로 텍스트를 추출한다.

출력 위치:

```text
wiki/source_summaries/<source_id>.md
```

현재 markdown 형식:

```markdown
# <title>

> Source: `<source_id>`

---

<extracted body text>
```

컴파일 결과는 `wiki_pages`에 upsert된다.

## SQLite FTS 색인

`tools/init_db.py`는 FTS5 virtual table `wiki_fts`를 만든다.

`tools/compile_wiki.py`는 같은 `page_id`를 먼저 삭제한 뒤 `wiki_fts`에 다시 삽입한다.

현재 FTS 컬럼:

- `page_id`
- `title`
- `body`

tokenizer:

```sql
tokenize = 'unicode61'
```

## search_kb.py 역할

`tools/search_kb.py`는 `wiki_fts MATCH ?`로 검색하고 `wiki_pages`와 JOIN한다.

JSON 결과에는 현재 다음 필드가 포함된다.

- `page_id`
- `title`
- `type`
- `path`
- `score`
- `snippet`
- `graph_paths`

빈 쿼리는 `status: error`를 반환한다. FTS5 query syntax error도 `status: error`로 반환한다.

## answer.py 역할

`tools/answer.py`는 검색 결과를 사용해 context pack을 만든다.

기본 출력은 JSON이다.

```bash
python tools/answer.py "lodestone"
```

텍스트 출력도 지원한다.

```bash
python tools/answer.py "lodestone" --format text
```

현재 옵션:

- `--limit`: 포함할 최대 문서 수, 기본 3
- `--max-chars`: 문서별 본문 발췌 최대 문자 수, 기본 1000
- `--format`: `json` 또는 `text`

## Context pack

context pack은 답변 생성에 사용할 근거 묶음이다.

현재 context item 필드:

- `page_id`
- `title`
- `path`
- `score`
- `snippet`
- `content_excerpt`
- `graph_paths`

## 출처 기반 답변 원칙

답변은 현재 로컬 KB에 저장된 문서만 기준으로 한다.

검색 결과가 없으면 `answer.py --format text`는 관련 문서를 찾을 수 없다고 출력한다. context에 없는 FFXIV 정보는 추정하지 않는다.

## 성공 기준

- URL ingest가 raw HTML을 저장하고 `sources`에 기록한다.
- 같은 content hash는 중복 저장하지 않는다.
- source id로 wiki summary를 생성할 수 있다.
- wiki summary가 `wiki_pages`와 `wiki_fts`에 반영된다.
- `search_kb.py`가 FTS 결과를 JSON으로 출력한다.
- `answer.py`가 context pack을 JSON으로 출력한다.

## 확인 명령

```bash
python tools/init_db.py
python tools/ingest_url.py "<URL>"
python tools/compile_wiki.py --source-id <source_id>
python tools/search_kb.py "lodestone"
python tools/answer.py "lodestone"
python tools/answer.py "lodestone" --format text
```

현재 저장된 테스트는 `sync_drive` 중심이다. v0.1 pipeline 전용 unittest는 TODO다.
