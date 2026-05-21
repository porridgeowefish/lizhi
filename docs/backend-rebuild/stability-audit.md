# Stability Audit

Last updated: `2026-05-22`

This document records the project issues that are most likely to damage long-term maintainability, delivery confidence, and architecture stability.

## P0

### P0-1 Iteration completion was overstated by the old doc set

- Location:
  - `docs/INDEX.md`
  - `docs/backend-rebuild/backend-consensus.md`
  - `docs/backend-rebuild/planning-memory.md`
- Problem:
  - The old docs framed the project as if iter-1 had effectively entered a stable integration phase, while the implementation still lacked the PRD's time-awareness core.
- Why it is dangerous:
  - Teams start polishing presentation and frontend before the target contract exists.
  - Review quality drops because "working" is mistaken for "accepted."
- Evidence:
  - `iter-1-prd.md` requires `event_start_at`, `event_end_at`, `deadline_at`, `time_status`, and `timeliness_level`.
  - `backend/app/db/models.py` and `backend/app/schemas/responses.py` do not contain those fields.
- Status:
  - [x] recorded
  - [x] doc entry points corrected
  - [ ] code still incomplete

### P0-2 There was no single source of truth for target vs current vs risk

- Location:
  - `docs/backend-rebuild/current-state.md`
  - `docs/backend-rebuild/iter-1-prd.md`
  - historical planning and consensus docs
- Problem:
  - The repo had a PRD and a current-state doc, but no explicit audit layer describing the gap and no remediation board tracking what was fixed.
- Why it is dangerous:
  - Gaps remain invisible.
  - The team repeatedly rediscovers the same issues.
  - People argue from memory instead of written state.
- Status:
  - [x] recorded
  - [x] audit doc added
  - [x] remediation board added

### P0-3 Cloud scale reality was easy to confuse with local snapshot reality

- Location:
  - local SQLite projection
  - backend sync records
  - operational documentation
- Problem:
  - A stale local projection created the impression that the dataset was roughly `94` articles, while the verified upstream cloud dataset is already `500+`.
- Why it is dangerous:
  - Architecture decisions get made against the wrong scale.
  - Query, storage, and sync risks appear later than they should.
- Verified snapshot:
  - upstream cloud: `146` sources, `538` articles
  - local projection after manual sync: `540` articles
- Status:
  - [x] recorded
  - [x] verified against upstream
  - [x] current-state doc now includes explicit scale snapshot section

### P0-4 Article sync previously behaved like a silent truncation pipeline

- Location:
  - `backend/app/infrastructure/connectors/werss.py`
  - `backend/app/application/services/ingestion_service.py`
  - `backend/app/core/config.py`
- Problem:
  - `fetch_articles()` uses one request shape and relies on `limit`; earlier local sync state strongly suggested only the visible page was being projected at least in earlier runs.
- Why it is dangerous:
  - Any misunderstanding around page semantics turns into silent data loss.
  - This is the kind of bug that looks like a healthy sync because the job still completes.
- Current note:
  - After manual verification on `2026-05-22`, a fresh sync pulled `538` cloud articles successfully.
  - Even so, the project still lacks an explicit pagination and completeness contract in docs and tests.
- Status:
  - [x] recorded
  - [ ] sync semantics still under-specified in docs
  - [ ] no regression test proving full-source completeness

## P1

### P1-1 The PRD's time-awareness contract is still missing in code

- Location:
  - `docs/backend-rebuild/iter-1-prd.md`
  - `backend/app/db/models.py`
  - `backend/app/application/services/ingestion_service.py`
  - `backend/app/application/services/query_service.py`
  - `backend/app/api/routes/articles.py`
  - `backend/app/schemas/responses.py`
- Problem:
  - Iter-1 promises time extraction, time status, timeliness governance, and expired-content hiding, but the implementation still only has `published_at`, `content_type`, and `display_level`.
- Why it is dangerous:
  - The project's central product claim is not implemented.
  - Any ranking or "participable" logic built on top of this would be fake.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P1-2 Sync idempotency is overstated

- Location:
  - `backend/app/application/services/ingestion_service.py`
  - `backend/app/db/models.py`
  - `backend/app/domain/enums.py`
- Problem:
  - Existing rows are rewritten and counted as updates even when there is no meaningful change.
  - `IngestionStatus.UNCHANGED` exists but is not actually used as a stable semantic.
- Why it is dangerous:
  - Metrics lie.
  - Write amplification grows.
  - Future incremental sync work starts from a misleading baseline.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P1-3 Sync path is still structurally expensive for larger scale

- Location:
  - `backend/app/application/services/ingestion_service.py`
  - `backend/app/infrastructure/connectors/werss.py`
- Problem:
  - The pipeline still performs frequent commits, per-item work, and detail fetching patterns that are too expensive for a growing dataset.
- Why it is dangerous:
  - Slower syncs collide with scheduler cadence.
  - SQLite becomes increasingly fragile under write-heavy patterns.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P1-4 Job observability is not strong enough to be trusted as a product feature

- Location:
  - `backend/app/application/services/ingestion_service.py`
  - `backend/app/schemas/responses.py`
  - `docs/backend-rebuild/iter-1-prd.md`
- Problem:
  - Stage lifecycle handling is not strongly documented or guaranteed in failure paths.
  - Product language currently gives more confidence than the implementation deserves.
- Why it is dangerous:
  - Operators trust job and item records that may not reflect final truth under failure.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P1-5 Sync entry points do not have an explicit mutual exclusion contract

- Location:
  - `backend/app/main.py`
  - `backend/app/api/routes/sync.py`
  - `backend/app/application/services/ingestion_service.py`
- Problem:
  - Startup sync, scheduled sync, and manual sync are not protected by an explicit lock or lease contract.
- Why it is dangerous:
  - Duplicate ingestion, write contention, and inconsistent metrics become more likely under load.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P1-6 Category taxonomy is drifting away from the PRD

- Location:
  - `backend/app/application/classification.py`
  - `docs/backend-rebuild/iter-1-prd.md`
  - `frontend/src/App.vue`
- Problem:
  - The implementation still uses taxonomy that differs from the iter-1 target, especially around `activity` vs `club_activity`, and the absence of PRD-first classes such as `competition` and `notice`.
- Why it is dangerous:
  - Historical data becomes harder to remap.
  - Frontend tabs and category stats drift away from product semantics.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P1-7 Upstream HTML is rendered directly in the frontend

- Location:
  - `frontend/src/App.vue`
  - `backend/app/api/serializers.py`
  - `backend/app/schemas/responses.py`
- Problem:
  - `content_html` is passed through and rendered with `v-html` without a documented sanitization contract.
- Why it is dangerous:
  - This is a real content injection surface, not just a theoretical concern.
- Status:
  - [x] recorded
  - [ ] unresolved in code

## P2

### P2-1 Documentation entry points mixed durable facts with temporary workflow residue

- Location:
  - `docs/backend-rebuild/README.md`
  - `docs/backend-rebuild/planning-memory.md`
- Problem:
  - The old entry docs contained duplicated workflow text and temporary collaboration patterns that were louder than the engineering truth of the project.
- Why it is dangerous:
  - New contributors read process residue before architecture and risk posture.
- Status:
  - [x] resolved in docs this round

### P2-2 Iteration roadmap ordering was too optimistic

- Location:
  - `docs/INDEX.md`
- Problem:
  - The old iteration table implied a straightforward march into frontend, product expression, MySQL, and deployment while core data and time contracts were still missing.
- Why it is dangerous:
  - Work sequencing becomes presentation-led instead of contract-led.
- Status:
  - [x] corrected in docs this round

### P2-3 Some contracts look complete but are still brittle

- Location:
  - `backend/app/application/services/query_service.py`
  - `backend/app/application/services/ingestion_service.py`
  - `backend/app/domain/enums.py`
  - `backend/app/api/routes/health.py`
- Problem:
  - Category stats omit empty buckets.
  - `fetch_content` behaves like an extra stage without being formalized in the declared stage model.
  - health checks only prove shallow configuration truth.
- Why it is dangerous:
  - Dashboards and automation scripts must guess too much.
- Status:
  - [x] recorded
  - [ ] unresolved in code

### P2-4 The test suite mostly proves happy paths

- Location:
  - `backend/tests/test_api.py`
  - `backend/tests/test_classification.py`
- Problem:
  - The highest-risk behaviors still lack dedicated tests:
    - time-awareness
    - sync completeness
    - repeated sync semantics
    - partial failure semantics
    - concurrency collisions
- Why it is dangerous:
  - Regressions can pass CI and only surface on real data.
- Status:
  - [x] recorded
  - [ ] unresolved in code

## This Round: Solved At The Structure And Docs Layer

- [x] Added an explicit audit document
- [x] Added an explicit remediation board
- [x] Corrected the doc entry points to reflect current reality
- [x] Reframed the current phase as `post-sync baseline, pre-acceptance`
- [x] Reordered backend docs around truth, risk, and remediation
- [x] Removed duplicated and misleading process-heavy wording from core entry docs

## This Round: Still Open In Code

- [ ] time-aware schema and response contract
- [ ] rule-based time extraction pipeline
- [ ] timeliness-aware filtering and sorting
- [ ] raw payload vs projection vs content snapshot storage strategy
- [ ] sync mutual exclusion and stronger observability semantics
- [ ] taxonomy migration plan
- [ ] HTML sanitization contract
- [ ] high-risk regression tests
