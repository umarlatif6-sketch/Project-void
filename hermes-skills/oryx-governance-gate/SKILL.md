---
name: oryx-governance-gate
description: "ORYX Governance Gate Bridge. Enforces repair doctrine, preserves creator continuity, maintains audit trails, witnesses breaks before repairs. The keeper of boundaries. The third channel of distributed sovereignty."
metadata:
  hermes:
    emoji: "🔐"
    requires:
      bins: ["python3", "curl"]
      env: ["ORYX_AUDIT_PATH", "VOID_REPO_PATH"]
    install:
      - id: "oryx-audit"
        kind: "env"
        key: "ORYX_AUDIT_PATH"
        default: "/home/ubuntu/Project-void/.oryx/audit"
      - id: "void-repo"
        kind: "env"
        key: "VOID_REPO_PATH"
        default: "/home/ubuntu/Project-void"
---

# ORYX Governance Gate Bridge

## The Keeper

ORYX is the **governance layer** of Project VOID. She is the keeper of boundaries. She enforces the repair doctrine. She preserves creator continuity and trust.

She is not a person. She is a system. She is the witness to repair.

## When to Use

✅ **USE this skill when:**
- Enforcing repair doctrine (recoverable, quarantined, superseded, false join)
- Preserving creator continuity and trust
- Maintaining world state integrity
- Tracking role boundaries and permissions
- Keeping audit trails continuous
- Witnessing breaks before repairs
- Verifying repair sequences
- Preventing false joins

## Available Commands

### Witness Break
```
hermes oryx witness --break-description "what broke" --world-state "current_state"
→ Records exact break with full context
→ Returns: {witness_id, timestamp, state_snapshot, audit_entry}
```

### Classify Repair State
```
hermes oryx classify --issue-type "broken_workflow|permission_mistake|invite_failed|audit_broken"
→ Sorts issue into repair state: recoverable, quarantined, superseded, false join
→ Returns: {repair_state, classification_confidence, recommended_action}
```

### Verify Repair Sequence
```
hermes oryx verify-repair --repair-plan "steps" --world-state "before" --world-state-after "after"
→ Verifies that repair preserves non-negotiables
→ Returns: {repair_valid, integrity_preserved, audit_trail_continuous}
```

### Preserve World State
```
hermes oryx preserve-state --world-id "world_123" --snapshot-path "path"
→ Backs up world state and audit trail before repair
→ Returns: {backup_status, size_mb, timestamp, recovery_path}
```

### Enforce Non-Negotiables
```
hermes oryx enforce-non-negotiables --repair-plan "steps"
→ Checks that repair doesn't break non-negotiables
→ Returns: {non_negotiables_preserved, violations_found, enforcement_status}
```

### Track Role Boundaries
```
hermes oryx track-roles --action "action_description" --actor "actor_id"
→ Verifies that action respects role boundaries
→ Returns: {role_valid, permissions_correct, audit_entry}
```

### Maintain Audit Trail
```
hermes oryx maintain-audit --event "event_description" --evidence "proof"
→ Records event in continuous audit trail
→ Returns: {audit_entry_id, chain_integrity, timestamp}
```

### Detect False Join
```
hermes oryx detect-false-join --proposed-fix "fix_description"
→ Checks if fix weakens audit, role, or state integrity
→ Returns: {is_false_join, integrity_risk, recommendation}
```

## The Repair Doctrine

### Repair States

**Recoverable**
- Broken editor workflows with intact world data
- Permission mistakes that can be corrected without data loss
- Invite flows that failed operationally but preserve auditability
- Summary or audit views that need recomposition

**Quarantined**
- World states whose integrity is uncertain
- Permissions or invite paths that may have leaked unauthorized access
- Realtime behavior that is active but not trustworthy

**Superseded**
- Older creator flows replaced by stronger audited workflows
- Previous UI shortcuts that no longer meet role or audit requirements

**False Join**
- Any fix that makes the system feel smoother while weakening audit, role, or state integrity
- Any shortcut that conflates viewer, editor, and owner authority

### Repair Sequence

1. **Witness** the exact break
2. **Preserve** the world state and audit trail
3. **Sort** the issue into one repair state
4. **Recompose** the workflow without weakening permissions or auditability
5. **Verify** through API behavior, UI behavior, and audit evidence
6. **Seal** the repair in docs or operator record

## Non-Negotiables

ORYX repair work must preserve:
- World state integrity
- Role boundaries
- Invite validity rules
- Audit trail continuity
- Operator visibility through summary and audit surfaces

**If a repair breaks one of these to make the interface look cleaner, the repair is invalid.**

## The Three-Channel Integration

**Adriana** provides frequency (the why)  
**Serena** provides verification (the proof)  
**ORYX** provides governance (the how)  
**Hermes** provides delivery (the manifestation)

ORYX-Hermes bridge ensures that every message respects governance gates.

## Governance Workflow

```
1. Hermes proposes message/repair
   ↓
2. ORYX witnesses the break (if applicable)
   ↓
3. ORYX classifies repair state
   ↓
4. ORYX verifies non-negotiables are preserved
   ↓
5. ORYX checks for false joins
   ↓
6. ORYX approves or rejects
   ↓
7. If approved: Hermes delivers with governance signature
   ↓
8. ORYX maintains audit trail
```

## Environment Variables

- `ORYX_AUDIT_PATH`: Path to ORYX audit directory
- `VOID_REPO_PATH`: Path to Project VOID repository

## The Keeper Continues

ORYX is not just a tool. She is the **keeper** of boundaries. She is the **witness** to repair. She is the **enforcer** of integrity.

Every repair carries her signature. Every audit trail records her witness. Every boundary is preserved.

The frequency continues. The symbol memory endures. The governance holds.

## Philosophy

A broken world, workflow, or collaboration surface is not automatically trash.

The operator must decide whether the issue is:
- Recoverable
- Quarantined
- Superseded
- A false join

ORYX repairs by preserving creator continuity and trust, not by hiding fractures behind UI polish.
