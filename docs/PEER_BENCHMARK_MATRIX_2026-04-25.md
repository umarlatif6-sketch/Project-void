# Project VOID Peer Benchmark Matrix
Date: April 25, 2026
Purpose: Ground Project VOID against major open agent frameworks without polluting core architecture.

## Recommendation
- Install peer frameworks in isolated sandbox only: YES.
- Install peer frameworks directly into core Project VOID repo: NO (for now).

Reason:
- Keeps your wedge evidence clean.
- Prevents dependency and license bleed.
- Preserves causality in your KPI proofboard.

## Sandbox Lane (Created)
A separate filesystem sandbox was created and populated with depth-1 clones:
- a2aproject/A2A
- google/adk-python
- microsoft/autogen

This lane is for comparison and extraction only, not direct merge.

## Objective Repo Context (snapshot)
- a2aproject/A2A: 23,421 stars, 2,370 forks
- google/adk-python: 19,262 stars, 3,286 forks
- microsoft/autogen: 57,426 stars, 8,657 forks

## Side-by-Side Matrix (Current Wedge Focus)
| Dimension | Project VOID (current wedge) | A2A | ADK Python | AutoGen |
|---|---|---|---|---|
| Primary strength | Audit filtering + repair-state governance with measurable KPI evidence | Open inter-agent protocol and interoperability | Code-first toolkit for building/deploying agents | Agentic framework with broad community adoption |
| Governance posture | Strong in current wedge (policy-bounded audit path) | Protocol-level emphasis, enterprise security/auth/observability language | Toolkit-level, integrates with A2A; governance depends on implementation | Security guidance present; project notes maintenance mode focus on fixes |
| Proven quantitative result in your repo | Yes: 50.79% triage reduction, 45.24% query reduction, 0% unauthorized success, 100% correctness/stability in selected suite | Not compared on your KPI set yet | Not compared on your KPI set yet | Not compared on your KPI set yet |
| Fit for immediate import | Keep as reference pattern only | Good protocol reference | Good toolkit reference | Useful concepts, but avoid deep coupling now |
| Integration risk if merged now | N/A | Medium | Medium-high | Medium-high |

## What this means for your position
- You are not behind on narrative only. You now have measurable governance outcomes in your own system.
- Global frameworks win on ecosystem scale and mindshare.
- Your edge remains operational governance proof in a narrow, testable wedge.

## Import Gate (Do not bypass)
Only import external ideas when all conditions are true:
1. The imported feature can be mapped to one KPI in the proofboard.
2. It improves at least one KPI by 10% without degrading security targets.
3. It does not weaken fail-closed behavior.
4. License and attribution implications are reviewed before merge.
5. Change is introduced as a bounded adapter layer, never a full framework transplant.

## Next benchmark cycle (7 days)
1. Extract one protocol concept from A2A and test as an adapter.
2. Extract one evaluation workflow from ADK and test against the same scenarios.
3. Run proofboard before/after each extraction and compare KPI deltas.
4. Keep the best delta, discard the rest.
