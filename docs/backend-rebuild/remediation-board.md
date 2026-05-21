# Remediation Board

Last updated: `2026-05-22`

This board tracks stability work that matters for long-term development, not just for short-term demos.

## Completed In This Round

- [x] Created `stability-audit.md` as the explicit problem register.
- [x] Created `remediation-board.md` as the checked and unchecked execution board.
- [x] Updated `docs/INDEX.md` so the entry point reflects current project reality instead of an optimistic iteration ladder.
- [x] Updated `backend-rebuild/README.md` to define read order and source-of-truth rules.
- [x] Updated `backend-rebuild/backend-consensus.md` to stop presenting the project as a mature integration phase.
- [x] Updated `backend-rebuild/planning-memory.md` to focus on alignment, target gaps, and safe iteration.
- [x] Verified upstream cloud scale and corrected the stale `94 articles` mental model.

## Open P0 Items

- [x] Add an explicit section to `current-state.md` for:
  - verified cloud scale snapshot
  - local projection snapshot
  - what those numbers do and do not prove
- [ ] Write down the sync completeness contract:
  - what counts as a complete source sync
  - how pagination is guaranteed
  - what test proves it
- [ ] Add time-aware article fields to the schema:
  - `event_start_at`
  - `event_end_at`
  - `deadline_at`
  - `time_status`
  - `timeliness_level`
- [ ] Add API exposure for the time-aware fields in list and detail responses.

## Open P1 Items

- [ ] Define a rule-based ranking contract before adding more UI prioritization behavior.
- [ ] Define a taxonomy migration plan from current categories to PRD categories.
- [ ] Add a data architecture note for:
  - raw payload
  - normalized content
  - projection record
- [ ] Add a sync hardening note covering:
  - idempotency
  - incremental sync
  - concurrent sync protection
  - detail content fetch strategy
- [ ] Add a query hardening note covering:
  - search strategy
  - pagination strategy
  - required indexes
  - future DB migration criteria
- [ ] Define a frontend HTML sanitization contract for `content_html`.

## Open P2 Items

- [ ] Revisit iteration ordering after time-aware iter-1 scope is truly complete.
- [ ] Mark any remaining historical docs as stale if they are no longer authoritative.
- [ ] Add a regression-test checklist for the highest-risk scenarios.

## Exit Criteria For "Iter-1 Accepted"

- [ ] PRD-required time fields exist in schema and API
- [ ] default list hides expired content through `timeliness_level`
- [ ] `time_status` filtering exists
- [ ] rule-based opportunity ranking is defined and documented
- [ ] tests cover time extraction, timeliness, sync completeness, and repeated sync behavior
- [ ] current-state, PRD, and implementation no longer contradict each other
