# FFXIV OpenClaw Bot 초기 설계 (Archive)

> Notion `ffxiv bot` 페이지에서 2026-05-14 가져옴.
> 현재 repo와 일부 내용이 다를 수 있다. 최종 구현 상태는 항상 `docs/specs/`를 기준으로 한다.

---

이 문서는 초기 프로젝트 설계 단계에서 작성한 방대한 실행 계획이다.
**핵심 방향**은 이후 v0.1~v0.3 구현에서 이미 반영되었고,
현재는 과거 참고용으로만 보관한다.

## 원본 출처

- Notion page: `ffxiv bot` (최상위 페이지)
- URL: https://www.notion.so/35f4bf16ed1f80fd9245d782f99be303

## 포함 내용

- 최종 Discord agent 구상
- 브런치 프로젝트 참고 포인트
- 초기 디렉터리 구조 (일부 현재와 다름)
- 데이터 소스 설계 (4종: 패치노트, URL, Drive, 직접 문서)
- SQLite DB 스키마 (현재 `tools/init_db.py` 기준과 거의 동일)
- LLM Wiki 설계 (에자일하게 변경됨)
- Graphify-inspired 그래프 설계
- 검색 계층 설계 (SQLite FTS5 + metadata + graph traversal)
- Tool Layer 명세 (agent.md 초안 포함)
- Phase 1~10 로드맵 (현재 v0.3 진행 중)

## 현재와 다른 점

- 초기에는 `index_fts.py`를 별도 도구로 분리할 예정이었으나, 실제로는 `compile_wiki.py`가 FTS까지 처리
- `tools/build_graph.py`는 LLM 없이 deterministic하게 구현됨 (초기 설계와 일치)
- `tools/sync_drive.py`는 manifest 기반 dry-run으로 먼저 구현됨 (실제 Drive API는 아직)
- Discord 연결과 OpenClaw agent는 아직 구현되지 않음
- `raw/drive/`는 아직 생성되지 않음 (--apply 구현 후 생성 예정)
