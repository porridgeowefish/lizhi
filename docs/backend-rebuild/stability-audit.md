# Stability Audit

Last updated: `2026-05-22`

## P0 Risks

### P0-1 Stale contracts can reintroduce `articles`

Status: mitigated.

The active system uses `posts`. Any remaining `articles` wording must refer only to the upstream WeRSS endpoint hidden inside the connector.

### P0-2 Prescreen rules must run before expensive work

Status: implemented.

Strongly excluded content writes only to `discarded_posts`; it must not trigger raw storage, detail fetch, LLM, projections, or frontend exposure.

### P0-3 Cloud acceptance must use real upstream data

Status: in verification.

Local sample databases are not acceptance evidence. The cloud service must pass health, sync, posts API, and database-shape checks.

### P0-4 Runtime secrets and databases must stay out of the repository

Status: mitigated.

`.gitignore` excludes DBs, runtime state, caches, and secrets. Local stale database files should be deleted as part of repo hygiene.

## P1 Risks

### P1-1 Upstream pagination semantics are still shallow

Current connector fetches posts per source through the WeRSS endpoint with a configured limit. This is acceptable for iter-1 acceptance but must become an explicit completeness contract before larger-scale ingestion.

### P1-2 SQLite remains the iter-1 projection store

SQLite is acceptable for the current dataset and single-service deployment. Migration criteria should be defined before write volume, concurrent sync, or query complexity grows.

### P1-3 LLM output must stay non-authoritative

LLM summary and structured extraction are allowed, but final feed state remains rule-owned. This prevents unexplainable ranking drift.

## Required Guardrails

- Run `pytest` before deployment.
- Run `npm run build` before deployment.
- Check old content-route and old table names before acceptance; only connector endpoint and startup cleanup references are acceptable.
- Verify cloud table names after deployment.
- Keep docs current in the same change as schema or API changes.
