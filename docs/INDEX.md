# Documentation Index

## Current Status

- iter-1 is partially implemented
- iter-1 is not yet accepted against its PRD
- backend documentation now uses audit + remediation docs as the entry point

## Recommended Read Order

1. [governance/DOCUMENT_REGISTRY.md](governance/DOCUMENT_REGISTRY.md)
2. [governance/ALIGNMENT_CONSENSUS.md](governance/ALIGNMENT_CONSENSUS.md)
3. [backend-rebuild/stability-audit.md](backend-rebuild/stability-audit.md)
4. [backend-rebuild/remediation-board.md](backend-rebuild/remediation-board.md)
5. [backend-rebuild/current-state.md](backend-rebuild/current-state.md)
6. [backend-rebuild/iter-1-prd.md](backend-rebuild/iter-1-prd.md)
7. [backend-rebuild/backend-consensus.md](backend-rebuild/backend-consensus.md)

## Iteration Reality

| Iteration | Status | Meaning |
| --- | --- | --- |
| iter-1 | partial | sync, projection, content filtering exist; time-aware governance and ranking are missing |
| iter-2 | not started | multi-page frontend and source management are not the current priority |
| iter-3 | not started | product expression should wait for backend contract stabilization |
| iter-4 | not started | MySQL or PostgreSQL migration should be driven by data architecture decisions |
| iter-5 | not started | deployment work should follow backend contract and storage hardening |

## Backend Documents

| Asset | Description |
| --- | --- |
| [backend-rebuild/stability-audit.md](backend-rebuild/stability-audit.md) | graded problem list focused on long-term stability |
| [backend-rebuild/remediation-board.md](backend-rebuild/remediation-board.md) | checked and unchecked remediation board |
| [backend-rebuild/current-state.md](backend-rebuild/current-state.md) | runtime topology, DB, API, and sync notes |
| [backend-rebuild/iter-1-prd.md](backend-rebuild/iter-1-prd.md) | iter-1 target contract |
| [backend-rebuild/backend-consensus.md](backend-rebuild/backend-consensus.md) | concise statement of current shared understanding |
| [backend-rebuild/rebuild-constraints.md](backend-rebuild/rebuild-constraints.md) | naming and implementation constraints |
| [backend-rebuild/reuse-decision-table.md](backend-rebuild/reuse-decision-table.md) | reusable decision mapping |
| [backend-rebuild/planning-memory.md](backend-rebuild/planning-memory.md) | current planning memory |

## Architecture Snapshot

```text
WeRSS Cloud -> Backend (WerssConnector) -> SQLite projection -> REST API -> Frontend
```
