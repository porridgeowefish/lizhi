# Remediation Board

Last updated: `2026-05-22`

## Completed

- [x] Created `Agent.md` and `CLAUDE.md`.
- [x] Established `docs/INDEX.md` and `docs/governance/DOCUMENT_REGISTRY.md`.
- [x] Switched product API contract from `articles` to `posts`.
- [x] Added active tables for raw payloads, normalized posts, projections, discarded posts, and sync observability.
- [x] Added strong prescreening before raw storage and LLM.
- [x] Added garbled hidden-source filtering with quality signals.
- [x] Added rule-derived `participation_status`, `time_status`, and `ranking_score`.
- [x] Added optional one-time LLM summary and candidate extraction boundary.
- [x] Updated frontend to consume `/api/posts`.
- [x] Deleted obsolete content-type docs, old HTML alignment artifacts, and old design mocks.
- [x] Added cloud deployment scripts.

## Cloud Acceptance Checklist

- [ ] Configure `/etc/campus-opportunity/backend.env` with upstream base URL, username, and password.
- [ ] Restart `campus-opportunity-backend.service`.
- [ ] Run cloud `POST /api/sync`.
- [ ] Verify `/api/posts` returns projected posts.
- [ ] Verify cloud DB has only the active iter-1 table set.
- [ ] Stop and remove old `werss-backend.service`.
- [ ] Delete old `/root/werss/backend` and `/root/werss/frontend` app directories.
- [ ] Preserve upstream 8001 support service and data.

## Still Worth Hardening After Acceptance

- [ ] Add explicit multi-page upstream pagination contract if source sizes exceed current per-source fetch limits.
- [ ] Add richer partial-failure tests for sync stages.
- [ ] Add future migration criteria from SQLite to PostgreSQL.
- [ ] Add frontend empty/error states for low-data or failed-sync cloud states.
