# Document Registry

This file is the repository index-management document.

## Source Of Truth Roles

| Role | Document |
| --- | --- |
| Agent working agreement | `Agent.md` |
| Documentation entry | `docs/INDEX.md` |
| Alignment process | `docs/governance/ALIGNMENT_CONSENSUS.md` |
| Iter-1 target | `docs/backend-rebuild/iter-1-prd.md` |
| Implemented reality | `docs/backend-rebuild/current-state.md` |
| Shared consensus | `docs/backend-rebuild/backend-consensus.md` |
| Stability risks | `docs/backend-rebuild/stability-audit.md` |
| Execution checklist | `docs/backend-rebuild/remediation-board.md` |

## Active Documents

| Path | Status | Notes |
| --- | --- | --- |
| `README.md` | active | repository entry |
| `Agent.md` | active | primary agent and human engineering rules |
| `CLAUDE.md` | active | pointer to `Agent.md` |
| `docs/INDEX.md` | active | documentation read order |
| `docs/governance/ALIGNMENT_CONSENSUS.md` | active | HTML alignment rules |
| `docs/governance/DOCUMENT_REGISTRY.md` | active | this registry |
| `docs/backend-rebuild/iter-1-prd.md` | active | target product contract |
| `docs/backend-rebuild/current-state.md` | active | runtime truth |
| `docs/backend-rebuild/backend-consensus.md` | active | latest shared agreement |
| `docs/backend-rebuild/stability-audit.md` | active | risk register |
| `docs/backend-rebuild/remediation-board.md` | active | checked execution board |
| `docs/backend-rebuild/rebuild-constraints.md` | active | rebuild constraints |
| `docs/backend-rebuild/reuse-decision-table.md` | active | migration decision notes |
| `docs/backend-rebuild/planning-memory.md` | active | working memory |
| `docs/archive/README.md` | active | archive semantics |

## Removed As Obsolete

- old content-type iteration docs
- old interactive alignment exports
- old frontend design mocks

## Maintenance Rules

- A current product contract must use `posts`, not internal `articles`.
- If a document still describes removed APIs or tables, update or delete it in the same change.
- HTML is only for short-lived alignment. Durable decisions must land in Markdown.
- Runtime databases, secrets, caches, and deployment artifacts do not belong in the repository.
