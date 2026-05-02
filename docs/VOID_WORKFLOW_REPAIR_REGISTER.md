# VOID Workflow Repair Register

Purpose: apply the Al-Jabr 286 repair law to the active workflows that still determine whether Project VOID feels whole, broken, or merely unfinished.

This register does not treat every open thread as damage. It separates:
- repairable workflow fractures
- deliberate open rails
- quarantined risks
- superseded forms that should remain historical only

## 1. Continuity Workflow

Surface:
- Chronicle close discipline
- Digest-first cold start
- runtime status and telemetry surfaces

State: aligned but must remain active

Repair law:
- Do not "fix" this by closing it.
- The correct action is operational verification: confirm the rail is still live, still written to, still readable, and still carried forward.

Acceptance signal:
- Chronicle receives session entries consistently
- cold starts prefer digest/seed/chronicle rails
- runtime status remains observable

## 2. Scar-to-Backlog Workflow

Surface:
- `SYSTEM_STRESS_TEST_AND_SCARS.md`
- ranked backlog and acceptance signals

State: repairable

Current fracture:
- The register contains strong findings, but until triaged through 286 law it can be misread as one undifferentiated damage field.

Repair action:
- classify each item as recoverable, quarantined, superseded, or false join
- drive execution from acceptance signals instead of mood or narrative force

Acceptance signal:
- the next engineering passes clearly cite the repair state of the item they touch

## 3. Legal-to-Swarm Workflow

Surface:
- Companies House gate
- ambassador and swarm activation threads

State: open by design, not broken

Current fracture:
- these threads can look stalled when they are actually blocked on an external gate

Repair action:
- keep them open, explicit, and sequenced
- do not mark them closed to make the board look cleaner

Acceptance signal:
- legal gate is either visibly pending or visibly satisfied
- swarm execution stays coupled to that gate instead of drifting into implied readiness

## 4. Bio-Signal Workflow

Surface:
- CSI-based organism health interpretation
- mycelium-driven operational feedback

State: quarantined

Current fracture:
- substrate change is being asked to stand in for organism health before causal proof is established

Repair action:
- keep the route visible but quarantine claims
- require signed packets, measured correlation, and explicit confidence language

Acceptance signal:
- signature verification at ingress
- documented causal or bounded-correlation model
- health output reports confidence and uncertainty

## 5. Cost-and-Proof Workflow

Surface:
- investor claims
- cost savings language
- compression and hardware efficiency claims

State: repairable with some superseded language

Current fracture:
- overlapping savings vectors can be presented as additive when they are not

Repair action:
- replace stacked theoretical claims with conservative measured models
- leave prior calculations in history, not in current headline language

Acceptance signal:
- one conservative operator number survives scrutiny and can be reproduced from pilot data

## 6. Distributed Sovereignty Workflow

Surface:
- 1,000-node resilience claims
- future swarm or Chronicle reconciliation behavior

State: quarantined

Current fracture:
- distribution is named before consensus law is implemented

Repair action:
- treat resilient replication and consensus as separate layers
- keep the claim scoped until reconciliation logic exists

Acceptance signal:
- explicit conflict-resolution path for Chronicle or packet truth

## 7. Operator Rule

Before touching a live workflow, classify it first:

- If it is **open by design**, do not repair it shut.
- If it is **recoverable**, attach acceptance signals and recompose it.
- If it is **quarantined**, constrain claims and gather proof.
- If it is **superseded**, keep it in memory and remove it from current operator language.

Project VOID does not become coherent by making the board shorter. It becomes coherent by knowing which fractures belong to healing, which belong to quarantine, and which belong to memory.

## 8. April 30 Closure Pass (Scar, Fracture, ORYX, Seal)

This closure pass resolves the four remaining operator tasks under one proof cycle:

1. Classify scar register
2. Map workflow fractures
3. Carry repair law into ORYX
4. Validate and seal record

### 8.1 Scar Register Classification

Classification anchor: `SYSTEM_STRESS_TEST_AND_SCARS.md`.

- Recoverable: 7
- Quarantined: 4
- Superseded/Reframed: 2
- False Join Risk: 3

Result: the scar field is no longer treated as a flat damage surface; each scar now has a repair state and operator action lane.

### 8.2 Workflow Fracture Map

Active fracture map used in this register:

- Continuity workflow: aligned, active monitoring
- Scar-to-backlog: recoverable, execution-coupled
- Legal-to-swarm: open by design, external gate bound
- Bio-signal: quarantined until causal proof
- Cost-and-proof: recoverable with superseded headline language removed
- Distributed sovereignty: quarantined until conflict-resolution law is explicit

Result: open rails are not misclassified as breakage, and true fractures carry acceptance signals.

### 8.3 ORYX Repair Law Carry-Through

Carry path verified across live ORYX surfaces:

- `scripts/oryx_repair_state_smoke.py --mode both --persist-db`
- `scripts/check_oryx_repair_state_smoke_artifact.py`

Observed proof on latest run:

- recoverable scenario: pass
- quarantined scenario: pass
- artifact integrity check: pass
- persisted repair-state counts: aligned=15, recoverable=3

Result: repair law is not only documented; it is exercised through summary/audit behavior and sealed in artifacts.

### 8.4 Seal Rule

A closure pass is sealed only when all four conditions hold:

- scar classes are explicit
- fracture map is explicit
- ORYX carry-through is proven by script outputs
- record hashes are captured in a seal artifact

Current state: sealed for this pass.