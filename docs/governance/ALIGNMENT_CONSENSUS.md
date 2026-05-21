# Alignment Consensus

## Purpose

This document defines how the project uses HTML during alignment.

## Consensus

- Markdown is the durable repository memory.
- HTML is the interactive alignment surface.
- HTML is used when the team needs:
  - side-by-side comparison
  - option selection
  - visual workflows
  - paged review
  - guided product or architecture alignment
- HTML must not become the only source of truth.
- Once an alignment round is settled, the result must be written back into Markdown docs.

## Required Flow

1. Produce HTML when interaction or visual comparison helps.
2. Review and decide in HTML.
3. Convert the accepted result into Markdown.
4. Update the relevant source-of-truth docs.
5. If the HTML artifact is still useful, keep it as a reference, not as the authoritative contract.

## Where Alignment Lands

- product target -> `docs/backend-rebuild/iter-1-prd.md`
- implemented reality -> `docs/backend-rebuild/current-state.md`
- risk and misalignment -> `docs/backend-rebuild/stability-audit.md`
- action tracking -> `docs/backend-rebuild/remediation-board.md`

