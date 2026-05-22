# Backend Consensus

Last updated: `2026-05-22`

## Current Phase

The project is in the `iter-1 acceptance hardening` phase.

The goal is no longer "can sync content". The goal is a complete, runnable, maintainable, opportunity-first system whose behavior matches the iter-1 PRD.

## Fixed Consensus

- `posts` is the only internal content model and public API noun.
- No legacy content compatibility layer is kept.
- WeRSS may still expose upstream `/articles` endpoints; that name must remain contained inside the connector implementation.
- Strong prescreening runs before raw payload storage, detail fetch, LLM extraction, projection, and persistence.
- Prescreened content does not enter `raw_payloads`, `posts`, or `post_projections`.
- Prescreened content writes only a minimal `discarded_posts` trace.
- LLM may create one-time summaries and candidate structured fields for new or changed posts.
- Final `participation_status`, `time_status`, and `ranking_score` are rule-derived.
- Frontend consumes only `/api/posts`, `/api/sources`, `/api/sync`, and `/api/health`.

## Core Tables

- `sources`
- `raw_payloads`
- `posts`
- `post_categories`
- `post_projections`
- `discarded_posts`
- `sync_jobs`
- `sync_job_items`

## Public APIs

- `GET /api/posts`
- `GET /api/posts/{post_id}`
- `GET /api/posts/categories`
- `GET /api/sources`
- `POST /api/sync`
- `GET /api/sync/jobs/{job_id}`
- `GET /api/health`

## Engineering Priorities

1. Keep PRD, docs, runtime schema, and frontend API usage aligned.
2. Keep filtering and ranking explainable through explicit rules.
3. Treat cloud sync, discard counts, and job status as acceptance evidence.
4. Keep deployment one-command and verify health, posts API, and sync smoke checks.
5. Remove stale docs, old tables, local runtime databases, and obsolete mock code instead of carrying them forward.
