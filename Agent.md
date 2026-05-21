# Agent.md

This file defines the default engineering principles for humans and agents working in this repository.

## Working Style

- Build the simplest thing that makes the next iteration safer.
- Prefer explicit contracts over implied behavior.
- Keep the data model honest before polishing the interface.
- Treat sync, storage, ranking, and observability as product behavior, not implementation detail.
- Write docs as operating assets, not as presentation filler.

## Karpathy Development Principles

These principles are adapted for an AI-native development workflow.

1. Make the truth cheap to inspect.
   - A teammate or agent should be able to answer "what does the system do now?" in minutes.
2. Keep the loop tight.
   - Small changes, fast verification, clear diffs, frequent commits.
3. Prefer runnable evidence over verbal confidence.
   - If a claim matters, back it with code, data, tests, logs, or docs.
4. Compress ambiguity early.
   - Convert fuzzy goals into fields, enums, contracts, and acceptance criteria.
5. Separate facts from plans.
   - Current state, target state, and remediation must live in different docs.
6. Optimize for future editing.
   - Good structure beats clever shortcuts.
7. Use AI for leverage, not for abdication.
   - Agents may draft, inspect, and propose, but repository truth must stay explicit and reviewable.
8. Keep the system explainable.
   - Ranking, filtering, and classification should be traceable to rules, evidence, and state.
9. Preserve mechanical sympathy.
   - Think about sync volume, write amplification, query shape, and operational failure modes early.
10. Leave breadcrumbs.
   - Every meaningful decision should have a doc home and a commit boundary.

## Repository Rules

- `docs/` is the documentation home.
- `docs/INDEX.md` is the top-level documentation entry.
- `docs/governance/DOCUMENT_REGISTRY.md` is the document registry.
- `docs/governance/ALIGNMENT_CONSENSUS.md` defines how HTML is used for alignment.
- `docs/backend-rebuild/iter-1-prd.md` is the active iter-1 PRD source of truth.
- `docs/backend-rebuild/current-state.md` describes implemented reality.
- `docs/backend-rebuild/stability-audit.md` records stability risks.
- `docs/backend-rebuild/remediation-board.md` tracks checked and unchecked remediation items.

## Change Discipline

- Make structural changes in small, reviewable batches.
- Do not mix repository hygiene, product design, and code behavior changes in one commit unless unavoidable.
- When a document becomes stale, update it or explicitly mark it stale.
- Avoid duplicate source-of-truth documents.
- Prefer Markdown for durable repo knowledge.
- Use HTML only as the interactive alignment surface when comparison, selection, or visual decision-making is the goal.

