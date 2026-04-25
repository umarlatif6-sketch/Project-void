# Project VOID 14-Day Proof Plan
Date: April 25, 2026
Owner: Umar Latif
Chosen edge: ORYX Audit Filtering + Repair-State Governance

## Why this wedge
This wedge is the fastest route from vision to buyer-proof because it already has:
- Authenticated API surface for audit retrieval and filters.
- Persisted repair-state model (aligned, recoverable, quarantined).
- Frontend controls for operational filtering.
- Existing test coverage in backend and endpoint layers.

Core evidence anchors:
- .oryx/backend/app.py
- .oryx/backend/oryx_engine/auth_store.py
- .oryx/frontend/app.js
- tests/test_oryx_audit_repair_state.py
- tests/test_oryx_repair_state_endpoints.py

## The one claim to prove in 14 days
Project VOID reduces operational risk triage time for multi-agent workflows by giving policy-bounded, filterable audit provenance with repair-state classification.

## KPI scoreboard (must be numeric)
1. Time to isolate incident from audit trail (target: 50 percent faster than baseline).
2. Mean queries to find root action (target: 40 percent fewer).
3. Unauthorized audit access success rate (target: 0 percent; fail closed).
4. Filter correctness pass rate (target: 100 percent on action, actor_email, repair_state).
5. Test pass stability across repeated runs (target: 100 percent on selected suite).

## 14-day execution schedule
Day 1
- Freeze scope to ORYX audit path only.
- Record baseline triage workflow and timings.

Day 2
- Finalize acceptance criteria for filters and repair-state semantics.
- Define exact KPI measurement protocol.

### Day 2 Lock (Completed Criteria)
- Filter contract acceptance:
	- `action` filter returns only exact action matches.
	- `actor_email` filter is case-normalized to lowercase.
	- `repair_state` filter returns only one of `aligned`, `recoverable`, `quarantined`.
	- Pagination uses bounded `limit` and non-negative `offset`.
- Authorization acceptance:
	- Unauthenticated access to audit endpoints returns HTTP 401.
	- Unassigned users receive HTTP 403 for summary and audit endpoints.
- Evidence acceptance:
	- Proofboard suite must remain green (current baseline: 13 passed, 0 failed).

### Day 2 KPI Protocol (Locked)
- Scenario count: 3 minimum scenarios (`s1`, `s2`, `s3`) each run in `baseline` and `post_wedge` mode.
- Timing formula:
	- `duration_seconds = end_ts_utc - start_ts_utc` (UTC timestamps).
	- KPI 1 (% reduction) = `((avg_baseline_duration - avg_post_duration) / avg_baseline_duration) * 100`.
- Query formula:
	- KPI 2 (% fewer queries) = `((avg_baseline_queries - avg_post_queries) / avg_baseline_queries) * 100`.
- Unauthorized formula:
	- KPI 3 (%) = `(sum_unauthorized_successes / sum_unauthorized_attempts) * 100`.
	- Target remains exactly `0`.
- Filter correctness formula:
	- Per scenario = `(filter_returned_count / filter_expected_count) * 100`.
	- KPI 4 = mean across all scenarios.
- Stability formula:
	- KPI 5 (%) = `(successful_runs / total_runs) * 100` for the proofboard test command.

Data capture template:
- `data/void_proofboard/day2_kpi_measurement_template.csv`

Day 3
- Validate existing endpoint behavior for action, actor_email, repair_state, paging.
- Log defects only in this wedge.

Day 4
- Harden any edge cases discovered in Day 3.
- Add targeted tests for any missed filter combinations.

Day 5
- Create repeatable incident triage scenario set (3 scenarios minimum).
- Capture baseline and post-fix timing data.

Day 6
- Run unauthorized/forbidden access checks for audit and summary routes.
- Verify fail-closed behavior remains intact.

Day 7
- Midpoint checkpoint: update proof table with measured numbers.
- Stop all non-wedge work.

Day 8
- Improve audit response clarity (field naming, meta counts, paging trust).
- Keep API contract stable.

Day 9
- Add scenario documentation for operator runbook use.
- Validate UI filter behavior against API output.

Day 10
- Execute repeated stability runs on test subset.
- Capture pass-rate and failure modes.

Day 11
- Produce buyer-safe one-page evidence summary.
- No speculative claims.

Day 12
- Produce cloud-partner framing paragraph with measured KPI delta.
- Explicitly state boundaries and non-claims.

Day 13
- Dry-run external walkthrough (15 minutes).
- Tighten wording for legal and business consistency.

Day 14
- Publish final proof pack and scoreboard artifact.
- Decision gate: continue, pivot, or stop.

## Permanent edge tool (chosen)
Tool name: VOID Proofboard
Path: scripts/void_proofboard.sh
Purpose: One command that runs wedge-critical tests and emits a dated KPI artifact in data/void_proofboard/.

Why this is the edge:
- Converts belief into evidence.
- Forces repeatable proof cadence.
- Gives cloud/legal/investor conversations measurable ground truth.

## Decision gate after day 14
Continue this wedge only if at least 4 out of 5 KPIs hit target.
If fewer than 4 KPIs hit target, pivot scope immediately and rerun a new 14-day cycle.

## Founder rule for this cycle
No new metaphors in external claims unless directly paired with measurable system behavior.
