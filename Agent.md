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

## Test-Driven Workflow

- Start behavior changes by writing or updating the smallest test that captures the expected behavior.
- Let the first test fail for the right reason before implementing the fix when practical.
- Implement the narrowest code change that makes the test pass.
- Add regression tests for bugs before changing production code.
- Keep tests close to the behavior under change; broaden coverage when the change touches shared contracts, queues, persistence, or user-facing flows.
- Run the relevant test subset before finishing, and record any tests that could not be run.
- Do not use manual browser checks as a substitute for automated tests when the behavior can be tested in code.

## Test Process Hygiene

- Any process started only for testing or verification must be terminated as soon as the test is complete.
- This includes local dev servers, one-off workers, queue consumers, browser automation helpers, tunnels, database shells, and temporary scripts.
- Before finishing a task, check for test-created background processes when the work started any long-running command.
- Prefer bounded commands such as `--once`, explicit timeouts, or systemd timers over unbounded loops during tests.
- Do not leave zombie, orphaned, or ghost processes competing for ports, database locks, CPU, or external API quotas.
