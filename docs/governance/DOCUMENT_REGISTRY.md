# Document Registry

This file is the index management document for the repository.

## Source Of Truth Model

The repository separates documents into four roles:

1. target
2. current state
3. risk and audit
4. execution and remediation

## Top-Level Registry

| Path | Role | Status | Notes |
| --- | --- | --- | --- |
| `README.md` | repository entry | active | short project entry |
| `Agent.md` | engineering rules | active | primary repo working agreement |
| `CLAUDE.md` | pointer | active | points to `Agent.md` |
| `docs/INDEX.md` | documentation entry | active | read order and doc map |
| `docs/governance/ALIGNMENT_CONSENSUS.md` | governance | active | HTML alignment rules |
| `docs/governance/DOCUMENT_REGISTRY.md` | governance | active | this registry |
| `docs/backend-rebuild/iter-1-prd.md` | target | active | active iter-1 PRD |
| `docs/backend-rebuild/current-state.md` | current state | active | runtime and implemented facts |
| `docs/backend-rebuild/stability-audit.md` | audit | active | graded problem list |
| `docs/backend-rebuild/remediation-board.md` | execution | active | checked and unchecked remediation board |
| `docs/backend-rebuild/backend-consensus.md` | consensus | active | concise shared understanding |
| `docs/backend-rebuild/rebuild-constraints.md` | constraints | active | naming and rebuild constraints |
| `docs/backend-rebuild/reuse-decision-table.md` | migration reference | active | reuse and non-reuse mapping |
| `docs/backend-rebuild/planning-memory.md` | planning note | active | current working memory |
| `docs/backend-rebuild/alignment-database-time-classification.html` | alignment artifact | reference | not source of truth |
| `docs/iter-1-content-type-filtering/design.md` | historical iteration doc | review-needed | likely outdated after PRD rewrite |
| `docs/iter-1-content-type-filtering/acceptance.md` | historical iteration doc | review-needed | likely outdated after PRD rewrite |
| `docs/iter-1-content-type-filtering/testing.md` | historical iteration doc | review-needed | likely outdated after PRD rewrite |
| `docs/user-stories-summary.md` | product note | review-needed | keep only if still aligned to PRD |

## Maintenance Rules

- Every active doc must have one clear role.
- If two docs describe the same thing, one must be demoted or deleted.
- Reference artifacts may exist, but they must not compete with source-of-truth docs.
- When a doc becomes obsolete, mark it `stale` or remove it.

