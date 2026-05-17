# v08.5 Source Summary Audit

## Summary

- Audit date: 2026-05-17
- Total source summaries: 26
- Usable FFXIV summaries: 20
- Empty or too-short summaries: 6
- Suspected non-FFXIV summaries: 0
- Duplicate candidates: 0
- Graph rebuild readiness: yes

## Method

Commands used:

```bash
find wiki/source_summaries -maxdepth 1 -type f -name "*.md" | sort | wc -l
find wiki/source_summaries -maxdepth 1 -type f -name "*.md" | sort | head -20
sqlite3 db/ffxiv.sqlite "SELECT 'sources', COUNT(*) FROM sources UNION ALL SELECT 'wiki_pages', COUNT(*) FROM wiki_pages UNION ALL SELECT 'graph_nodes', COUNT(*) FROM graph_nodes UNION ALL SELECT 'graph_edges', COUNT(*) FROM graph_edges;"
```

Criteria:

- A usable source summary has a Markdown title, `> Source: \`...\`` metadata, non-empty body, FFXIV relevance, and enough text to support extraction.
- A review source is not deleted or changed in this task. It is recorded when it is too short, missing registry aliases, or not present in the `sources` table.
- Duplicate candidates are checked by normalized body hash and title.
- Non-FFXIV contamination was checked for obvious off-domain terms. FFXIV item names containing words such as "Maple" are not counted as contamination.

SQLite snapshot before v08.5 graph activation:

| Table | Count |
|---|---:|
| `sources` | 24 |
| `wiki_pages` | 20 |
| `graph_nodes` | 40 |
| `graph_edges` | 20 |

Source ID consistency:

- Summary files not currently present in `sources`: `local_3be6dc5b8ea5`, `local_46d6b00b07d4`, `local_847451183af1`, `local_90439ba39663`, `local_ec3ec6f934d2`
- `sources` rows without a matching summary file: `drive_drive_file_001`, `drive_drive_file_002`, `drive_drive_file_003`

## Findings

| File | Source ID | Title | Body Length | Status | Notes |
|---|---|---|---:|---|---|
| `local_0d375d6647c8.md` | `local_0d375d6647c8` | FFXIV Patch 7.05 Notes | 90239 | usable | Registry aliases detected |
| `local_200334060298.md` | `local_200334060298` | FFXIV Patch 7.25 Notes | 81977 | usable | Registry aliases detected |
| `local_3be6dc5b8ea5.md` | `local_3be6dc5b8ea5` | Patch 7.5 Notes | 51 | review | Too short; has patch alias; source row missing |
| `local_46d6b00b07d4.md` | `local_46d6b00b07d4` | Tower Guide | 24 | review | Too short; no registry alias; source row missing |
| `local_481453189e0a.md` | `local_481453189e0a` | FFXIV Patch 7.31 Notes | 37756 | usable | Registry aliases detected |
| `local_58e80179b348.md` | `local_58e80179b348` | FFXIV Patch 7.41 Notes | 33363 | usable | Registry aliases detected |
| `local_62b39fe0be47.md` | `local_62b39fe0be47` | FFXIV 7.4 Patch Notes - Into the Mist | 168083 | usable | Registry aliases detected |
| `local_6b5fc029308c.md` | `local_6b5fc029308c` | FFXIV Patch 7.01 Notes | 23860 | usable | Registry aliases detected |
| `local_6bafe60d5c9d.md` | `local_6bafe60d5c9d` | FFXIV Patch 7.35 Notes | 78891 | usable | Registry aliases detected |
| `local_76c7536460ce.md` | `local_76c7536460ce` | FFXIV Patch 7.45 Notes | 29701 | usable | Registry aliases detected |
| `local_847451183af1.md` | `local_847451183af1` | Maintainer Provided Patch Title | 17 | review | Too short; no registry alias; source row missing |
| `local_862b7d9ed7d2.md` | `local_862b7d9ed7d2` | discord_agent_smoke_test | 77 | review | Operational smoke note; no registry alias |
| `local_90439ba39663.md` | `local_90439ba39663` | Spread Stack Macro | 20 | review | Too short; no registry alias; source row missing |
| `local_a5f56616236f.md` | `local_a5f56616236f` | FFXIV 7.5 Patch Notes - Trail to the Heavens | 127875 | usable | Registry aliases detected |
| `local_aa665865071a.md` | `local_aa665865071a` | FFXIV Patch 7.21 Notes | 35878 | usable | Registry aliases detected |
| `local_af7e32d6ff30.md` | `local_af7e32d6ff30` | FFXIV Patch 7.3 Notes | 146543 | usable | Registry aliases detected |
| `local_c45b1842a12c.md` | `local_c45b1842a12c` | FFXIV Patch 7.38 Notes | 6618 | usable | Registry aliases detected |
| `local_c4be9edd3906.md` | `local_c4be9edd3906` | FFXIV Patch 7.1 Notes | 156251 | usable | Registry aliases detected |
| `local_cbd135003ecc.md` | `local_cbd135003ecc` | FFXIV Patch 7.0 Notes | 75817 | usable | Registry aliases detected |
| `local_d0cffce5b173.md` | `local_d0cffce5b173` | FFXIV Patch 7.16 Notes | 10250 | usable | Registry aliases detected |
| `local_d45707ef39fc.md` | `local_d45707ef39fc` | FFXIV Patch 7.2 Notes | 189834 | usable | Registry aliases detected |
| `local_db3ca2238169.md` | `local_db3ca2238169` | FFXIV Patch 7.18 Notes | 9306 | usable | Registry aliases detected |
| `local_dc402787fe60.md` | `local_dc402787fe60` | FFXIV Patch 7.11 Notes | 16631 | usable | Registry aliases detected |
| `local_de4f42fe1ff1.md` | `local_de4f42fe1ff1` | FFXIV Patch 7.15 Notes | 33000 | usable | Registry aliases detected |
| `local_ec3ec6f934d2.md` | `local_ec3ec6f934d2` | Raid mitigation note | 36 | review | Too short; no registry alias; source row missing |
| `src_20260514_002930_4323e58d.md` | `src_20260514_002930_4323e58d` | FINAL FANTASY XIV, The Lodestone | 23737 | usable | Registry aliases detected |

## Exclusions or Fixes Needed

- No file needs to be excluded before v08.5 graph rebuild.
- The 6 review files are too short or operational notes. They can remain in place because they do not block graph extraction from the 20 usable summaries.
- The 5 summary files missing from `sources` should be reviewed in a later data hygiene task if provenance completeness becomes a requirement.
- The 3 `drive_*` source rows without source summary files are not blockers for v08.5 because the graph rebuild scans `wiki/source_summaries/*.md`.

## Decision

- Proceed with graph rebuild: yes
- Reason: the corpus contains 20 usable FFXIV source summaries, including Patch 7.0 through Patch 7.5 material and Lodestone content. Registry aliases are present in most long summaries, and no non-FFXIV contamination or duplicate body candidates were found.
