# v0.4-00: OpenClaw Ingest Contract

## Spec

- `docs/specs/01-architecture.md`
- `docs/specs/03-roadmap.md`
- `docs/adrs/0002-drive-is-canonical-source.md`

## Status

**Proposed**

## Context

OpenClaw/Discord 저장 요청은 URL, 짧은 메모, markdown/text 파일, 첨부 파일처럼 입력 형태가 섞인다.
구현 전에 저장 요청과 결과 JSON 계약을 먼저 고정해야 Drive write, CLI ingest, OpenClaw adapter가 같은 인터페이스를 공유할 수 있다.

## Checklist

- [ ] 입력 타입 결정: URL, text note, markdown file, plain text file, binary attachment
- [ ] ingest request JSON 필드 결정: `source_type`, `content_type`, `title`, `body`, `url`, `attachments`, `category`, `author`, `channel`, `created_at`
- [ ] category 매핑 결정: `patch_notes`, `job_guides`, `raid_guides`, `static_docs`, `macros`, `bis_sheets`, `personal_notes`
- [ ] result JSON 필드 결정: `status`, `action`, `drive_file_id`, `drive_url`, `source_id`, `raw_path`, `rebuild_status`, `message`
- [ ] dry-run result와 apply result 차이 결정
- [ ] 오류 계약 결정: invalid input, unsupported attachment, Drive auth missing, Drive write failed, rebuild failed
- [ ] OpenClaw/Discord 응답 문구 기준 결정
- [ ] 관련 spec 업데이트 필요 여부 확인

## Verification

문서 계약 plan이므로 red test는 작성하지 않는다.
구현 단계에서는 이 plan의 request/result JSON 예시를 기준으로 unittest를 먼저 작성한다.

```bash
python scripts/check_docs_freshness.py --all
```

## Key Decisions

- Drive를 canonical source로 유지한다.
- OpenClaw adapter는 repo tool을 호출하는 thin wrapper로 둔다.
- MCP/skill은 호출 껍데기이며 저장 계약은 repo `tools/`와 `docs/`에 둔다.

