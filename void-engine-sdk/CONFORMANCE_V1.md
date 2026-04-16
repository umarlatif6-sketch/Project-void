# VOID Connector Conformance v1

This specification defines the minimum public contract for external systems that want to integrate with the connector-first surface of the VOID protocol without adopting the full platform stack.

## Scope

This spec covers three pluggable surfaces:

1. Flask integration
2. Webhook delivery
3. Warehouse export

It does not define the full Adriana ontology, LBN routing layer, or sovereign node hardware behavior.

## Event Model

A conformant VOID event carries these fields:

| Field | Type | Required | Meaning |
|---|---|---|---|
| `entity` | string | yes | Who or what acted |
| `condition` | string | yes | State, context, or triggering condition |
| `action` | string | yes | The operation that occurred |
| `codon` | string | yes | VOID domain identifier |
| `digest` | string | yes | Deterministic Al-Jabr 286 signature |
| `formation_score` | float | yes | Resonance score from 0.0 to 1.0 |
| `tier` | string | yes | License tier at event creation |
| `ts` | float | yes | Unix timestamp |
| `meta` | object | no | Additional context |

## Digest Requirement

A conformant implementation must generate a deterministic Al-Jabr 286 digest for each event payload. The current Python reference implementation uses `sign286` from `void_sdk.hash286`.

## Webhook Shape

A conformant webhook POST body must be JSON and include:

```json
{
  "spec_version": "void.webhook.v1",
  "entity": "user:abc123",
  "condition": "frequency:432hz formation_score:0.87",
  "action": "encode",
  "codon": "voidecho",
  "digest": "v286:...",
  "formation_score": 0.743182,
  "tier": "FREE",
  "ts": 1713264000.0,
  "meta": {
    "chars": 420
  }
}
```

## Warehouse Export

A conformant exporter must support at least one of:

1. JSONL, one event per line
2. CSV with stable column names

If exporting nested `meta` values to CSV, they must be serialized as JSON strings.

## Flask Surface

A conformant Flask integration must:

1. Expose a request-scoped SDK object
2. Allow `track(...)` to be called inside a route handler
3. Return the event digest to the application layer

## Codon Minimums

A conformant implementation must support these codons at minimum:

1. `voidecho`
2. `adriana`
3. `chronicle`

## Reference Implementation

The reference implementation currently lives in:

1. `void_sdk.core.VoidSDK`
2. `void_sdk.flask_ext.VoidFlask`
3. `void_sdk.connectors`

## Non-Goals

This spec does not claim that VOID is a universal web standard. It defines a stable public connector contract so external teams can plug into the protocol surface without needing the entire PROJECT VOID runtime.
