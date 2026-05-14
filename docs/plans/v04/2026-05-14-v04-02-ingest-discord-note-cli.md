# v0.4-02: Ingest Discord Note CLI

## Spec

- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- Master plan: `docs/plans/2026-05-14-v04-openclaw-drive-ingest.md`

## Status

**Proposed**

## Context

OpenClaw adapter가 직접 Drive API나 DB를 만지면 테스트와 재사용이 어렵다.
Discord/OpenClaw 입력은 먼저 repo-local CLI로 정규화하고, 이 CLI가 Drive publish와 후속 rebuild를 호출하도록 분리한다.

## Checklist

- [ ] `tools/ingest_discord_note.py` CLI 신설
- [ ] 입력 옵션 설계: `--title`, `--body`, `--url`, `--category`, `--author`, `--channel`, `--created-at`
- [ ] `--dry-run`과 `--apply` 중 정확히 하나 요구
- [ ] `--publish-drive` 플래그 설계: apply 시 Drive publish 호출 여부
- [ ] URL 저장 요청은 기존 `tools/ingest_url.py`와 어떻게 결합할지 결정
- [ ] text note 저장 요청은 Drive publish request로 변환
- [ ] markdown/text file 입력은 파일 내용을 읽어 publish request로 변환
- [ ] output JSON shape를 v04-00 계약과 일치시킴
- [ ] unittest: text note dry-run JSON 검증
- [ ] unittest: URL input dry-run JSON 검증
- [ ] unittest: invalid category rejected 검증
- [ ] unittest: `--dry-run`은 Drive publish를 호출하지 않음 검증
- [ ] docs/runbooks 또는 spec 업데이트 필요 여부 확인

## Verification

```bash
python -m unittest tests.test_ingest_discord_note
python -m unittest discover -s tests -p "test_*.py"
python tools/ingest_discord_note.py --dry-run --category personal_notes --title "Raid note" --body "remember clock spots"
```

## Key Decisions

- Discord/OpenClaw adapter는 이 CLI의 JSON 입출력만 의존한다.
- Drive publish가 실패하면 local DB에 성공으로 기록하지 않는다.
- local-only 저장 모드는 별도 필요성이 확인될 때 추가한다.

