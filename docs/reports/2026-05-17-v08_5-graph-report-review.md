# v08.5 Graph Report Review

## Summary

- Report generated: yes
- Report path: `graph/GRAPH_REPORT.md` (local generated output, ignored by Git)
- Total nodes: 78
- Total edges: 339
- Job count: 5
- Patch count: 3
- Skill count: 4
- Fact count: 14

## Edge Coverage

| Edge Type | Count | Status |
|---|---:|---|
| `SOURCE_OF` | 46 | ok |
| `MENTIONS` | 198 | ok |
| `HAS_SKILL` | 4 | ok |
| `SUPPORTS` | 14 | ok |
| `VALID_IN_PATCH` | 14 | ok |
| `AFFECTS_JOB` | 59 | ok |
| `AFFECTS_SKILL` | 4 | ok |
| `DERIVED_FROM` | 0 | expected before v08.5-04 derived wiki generation |

## Top Entities

Top mentioned jobs:

- Dark Knight: 30
- Gunbreaker: 30
- Black Mage: 28
- Paladin: 28
- Warrior: 26

Top mentioned patches:

- Patch 7.0: 20
- Patch 7.1: 20
- Patch 7.5: 8

Top mentioned skills:

- Continuation: 4
- Ley Lines: 4

## Quality Warnings

| Warning | Cause | Action |
|---|---|---|
| entities without mentions: 2 | `skill:no_mercy` and `skill:fight_or_flight` exist in the registry but are not directly mentioned by the current source summaries. | Not a blocker for v08.5. Keep registry nodes for query/entity matching and improve source coverage or aliases in a later data-quality task if answer coverage requires it. |

## Decision

- Proceed to derived wiki generation: yes
- Reason: graph report is non-empty, all required domain node and edge counts are non-zero, and the only warning is source coverage for registry skills rather than a graph rebuild failure.
