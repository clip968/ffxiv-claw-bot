# 작업 로그 - ingest_url 이후 다음 단계

> 원본: Notion "작업 로그 - ingest_url 이후 다음 단계"
> https://www.notion.so/35f4bf16ed1f81939d01e561ba0748d8
> 동기화: 2026-05-14

**상태: ✅ 완료**

---

## 현재 상태 (로그 작성 시점)

`tools/ingest_url.py` 생성까지 완료.

완료된 항목:

```
- 프로젝트 폴더: /mnt/d/programming/ffxiv-claw-bot
- SQLite DB 초기화 완료
- tools/init_db.py 완료
- tools/ingest_url.py 생성 완료
```

## 검증 내용

```bash
cd /mnt/d/programming/ffxiv-claw-bot
python tools/ingest_url.py "https://na.finalfantasyxiv.com/lodestone/"
```

확인:

```bash
ls -lh raw/urls/
sqlite3 db/ffxiv.sqlite "SELECT id, source_type, title, raw_path FROM sources;"
```

성공 기준:

```
1. raw/urls/ 안에 HTML 파일이 생김
2. sources 테이블에 URL metadata가 들어감
3. 같은 URL을 다시 넣었을 때 deduplicated: true 또는 중복 방지 동작 확인
```

## 다음 순서 (로그 작성 시점 기준)

```
1. ingest_url.py 테스트
2. compile_wiki.py 최소 버전 구현
3. index_fts.py 구현
4. search_kb.py 구현
5. 이후 LLM Wiki compiler 고도화
```
