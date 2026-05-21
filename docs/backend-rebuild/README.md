# Backend Rebuild Docs

This directory is the backend decision center for the current project state.

## What Belongs Here

- current facts about the running backend
- iter-level product and engineering requirements
- architecture and naming constraints
- long-lived audit and remediation records
- docs that keep the code, roadmap, and PRD aligned

## Read Order

1. `stability-audit.md`
2. `remediation-board.md`
3. `current-state.md`
4. `iter-1-prd.md`
5. `backend-consensus.md`
6. `rebuild-constraints.md`
7. `reuse-decision-table.md`

## Source Of Truth Rules

1. Markdown is the durable source of truth.
2. Architecture, PRD, and current state must not contradict each other.
3. When the code changes, update the docs that describe runtime behavior and scope.
4. Historical brainstorming should not be presented as current consensus.
5. If a document is stale, either update it or explicitly mark it as stale.

## Current Working Reality

- Backend is runnable locally.
- Frontend is integrated to the current backend contract.
- Cloud upstream has been verified and is materially larger than the earlier local snapshot.
- Iter-1 is partially implemented, but not yet accepted against its own PRD.
- Time extraction, timeliness governance, and rule-based ranking are still missing from the implementation.

## Key Docs

- `stability-audit.md`
  - structured problem list for long-term stability risks
- `remediation-board.md`
  - checked and unchecked remediation board
- `current-state.md`
  - runtime topology, DB, API, and sync behavior
- `iter-1-prd.md`
  - target contract for iter-1
- `backend-consensus.md`
  - concise statement of what the team should currently believe

## Architecture Snapshot

```text
WeRSS Cloud -> WerssConnector -> IngestionService -> SQLite projection -> REST API -> Frontend
```
