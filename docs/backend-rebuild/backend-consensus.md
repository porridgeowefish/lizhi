# Backend Consensus

## Current Phase

We are in the `post-sync baseline, pre-acceptance` phase.

This means:

- the local stack runs end to end
- the upstream cloud has been verified
- the local projection is no longer just a toy snapshot
- iter-1 is still incomplete against its own PRD
- the next work should optimize for alignment and correctness, not for adding surface area

## What Is True Right Now

- The active implementation target is still `backend`.
- Frontend is consuming the current backend response shape.
- The backend connects directly to WeRSS cloud through `WerssConnector`.
- The current local projection is SQLite-based.
- Sync jobs, sync job items, article projection, and rule-based content filtering are implemented.
- Time extraction, timeliness governance, and rule-based opportunity ranking are not implemented yet.

## Aligned Iter-1 Decisions

The team has now aligned these product and architecture choices:

- time fields will formally include `event_start_at`, `event_end_at`, `deadline_at`, `time_status`, and `timeliness_level`
- `deadline_at` has higher decision priority than `event_end_at` for opportunity validity
- `participation_status` will be a formal field
- the default feed is an opportunity-first feed
- `ranking_score` will be a formal rule-derived field
- storage direction is `raw payload + normalized post + query projection`
- summary is the default feed-facing representation; original content is reference and fallback

## Agreed Layer Boundaries

- `core`
- `domain`
- `application`
- `db`
- `infrastructure`
- `api`
- `tests`

## Agreed Tables In Use

- `sources`
- `articles`
- `article_categories`
- `sync_jobs`
- `sync_job_items`

## Agreed Product Reality

- The system is not yet an accepted iter-1 implementation.
- The current build should be treated as a functional baseline, not as a completed backend.
- The biggest risk is false confidence caused by the presence of a working UI and a passing small test suite.

## Agreed API Reality

- `GET /api/articles`
- `GET /api/articles/{id}`
- `GET /api/articles/categories`
- `GET /api/sources`
- `POST /api/sync`
- `GET /api/sync/jobs/{job_id}`
- `GET /api/health`

These APIs currently support content filtering and basic sync observability.
They do not yet satisfy the iter-1 time-awareness contract.

## Agreed Engineering Priorities

1. keep docs, PRD, and runtime behavior aligned
2. stop describing partial work as complete iter capability
3. add time-aware data model and governance before expanding more UI surface
4. implement the aligned `participation_status` and `ranking_score` contract
5. improve query, sync, and storage design before data volume grows further
6. preserve explainability by keeping rule-based logic explicit

## Required Companion Docs

- `stability-audit.md`
- `remediation-board.md`
- `current-state.md`
- `iter-1-prd.md`
