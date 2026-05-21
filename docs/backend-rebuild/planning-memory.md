# Planning Memory

## Current Mission

The current mission is to make the project safe for sustained iteration, not just locally runnable.

## Immediate Priorities

1. keep the docs aligned with the code and the PRD
2. make the implementation gaps visible instead of implicit
3. reduce false signals of completion in architecture and iteration docs
4. prepare the backend for time-aware filtering and ranking
5. make the data pipeline safe for larger cloud volume

## Current Risk Posture

- Cloud data volume has already exceeded the earlier local baseline.
- The code has a working sync path, but the iter-1 PRD is only partially implemented.
- The biggest threat is alignment drift between product promises, code behavior, and docs.

## Source Of Truth Rule

- `iter-1-prd.md` defines the target.
- `current-state.md` describes what currently exists.
- `stability-audit.md` describes what is broken, risky, or misleading.
- `remediation-board.md` tracks what has been corrected and what remains.

## What To Avoid

- treating a working UI as evidence of product completion
- letting temporary investigation artifacts masquerade as stable consensus
- adding new scope before fixing schema, time logic, and ranking foundations
- relying on memory instead of checked remediation records

## Next Engineering Milestones

1. stabilize documentation and alignment assets
2. add time-related schema and API contract
3. design storage split for projection, raw payload, and content snapshot
4. harden sync strategy for larger datasets
5. expand tests around time, ranking, and data integrity
