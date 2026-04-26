# Agent Constitution Pack
Date: 2026-04-26

This folder is the governance root for Project VOID autonomous agents.

## Files
- genesis.md: constitutional principles
- policy_engine.json: default deny, fail-closed controls
- bridge_policy.json: economic air-lock for external transactions
- agent_profiles/: agent-specific sovereignty contracts

## OpenClaw Relationship
OpenClaw can be used as an execution adapter surface.
Project VOID remains the policy authority and audit source of truth.

Operational rule:
1. Decision and policy validation happen in Project VOID.
2. Execution may be delegated to adapters.
3. All adapter actions must return signed, replayable audit traces.

## Activation Flow
1. Validate profile against policy_engine.json.
2. Allocate daily internal credits.
3. Run task under sector permissions.
4. Record signed audit event.
5. Apply decay/dormancy rules if no qualifying contribution is made.
