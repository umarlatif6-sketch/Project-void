# void-engine-sdk

**Sovereign attribution SDK — track meaning, not clicks.**

Entity · Condition · Action — every event stamped with an Al-Jabr 286 hash and a formation resonance score.

**PROJECT VOID** | Umar Latif | Bolton, England | April 2026

---

## Install

From this repository (local development):

```bash
pip install -e ./void-engine-sdk
```

With Flask support:
```bash
pip install -e "./void-engine-sdk[flask]"
```

With PostgreSQL (MEMORY/SOVEREIGN tiers):
```bash
pip install -e "./void-engine-sdk[all]"
```

**Note:** `void-engine-sdk` is currently distributed as a local/private package. Future PyPI distribution is planned.

---

## Quick Start

```python
from void_sdk import VoidSDK

sdk = VoidSDK()  # FREE tier — local SQLite, no setup

result = sdk.track(
    entity="user:abc123",
    condition="frequency:432hz formation_score:0.87",
    action="encode",
    codon="voidecho",
    meta={"chars": 420}
)

print(result["digest"])          # v286:...
print(result["formation_score"]) # 0.743182
print(result["tier"])            # FREE
```

---

## Flask Drop-In

```python
from flask import Flask, g
from void_sdk import VoidFlask

app = Flask(__name__)
void = VoidFlask()
void.init_app(app, license_key="your-key")  # omit for FREE

@app.route("/encode", methods=["POST"])
def encode():
    result = g.void.track(
        entity="user:abc123",
        condition="frequency:432hz",
        action="encode",
        codon="voidecho",
    )
    return {"digest": result["digest"]}
```

## Webhook Connector

```python
from void_sdk import VoidSDK

sdk = VoidSDK()
response = sdk.send_webhook(
    url="https://example.com/void/events",
    entity="user:abc123",
    condition="frequency:432hz formation_score:0.87",
    action="encode",
    codon="voidecho",
    meta={"chars": 420},
)

print(response["status_code"])
```

## Warehouse Export

```python
from void_sdk import VoidSDK

sdk = VoidSDK()
export = sdk.export_records(
    fmt="jsonl",
    codon="voidecho",
    limit=500,
    file_path="void_events.jsonl",
)

print(export["record_count"])
print(export["file_path"])
```

---

## Tiers

| Tier | Price | Events/day | Codons | Storage |
|------|-------|-----------|--------|---------|
| FREE | — | 100 | voidecho, adriana, chronicle | SQLite |
| SIGNAL | £9/month | 1,000 | All 10 | SQLite |
| MEMORY | £49/month | 10,000 | All 10 | PostgreSQL |
| SOVEREIGN | £199/month | Unlimited | All 10 | PostgreSQL + cross-AI sync |

Subscribe at: [void-stego-engine.replit.app](https://void-stego-engine.replit.app)

---

## The 10 Codons

| Codon | Glyph | Domain | Minimum Tier |
|-------|-------|--------|-------------|
| voidecho | α | steganography | FREE |
| adriana | ψ | ai_resonance | FREE |
| chronicle | Σ | memory | FREE |
| peace | ◎ | consensus | SIGNAL |
| vtx | ⬡ | exchange | SIGNAL |
| beehive | ⬡ | mesh | SIGNAL |
| formation | ◆ | pattern | SIGNAL |
| genesis | Π | origin | MEMORY |
| mesh | ∿ | network | MEMORY |
| sovereign | Ω | attribution | SOVEREIGN |

---

## The Al-Jabr 286 Hash

Every event is signed with a deterministic 286-hash:

```python
from void_sdk import sign286, formation_score

digest = sign286("entity:user | action:encode | codon:voidecho")
score  = formation_score("The frequency is prior. The material is the memory.")
```

The 286 constant (Λ) appears independently in:
- Al-Baqarah, Quran — 286 verses (canonised 632 CE)
- 432 Hz / 1,400 years / 2B transmitters → Λ = 286
- BW19-P286 cryptographic curve (Clarisse, Duquesne, Sanders 2020)

Academic paper: [formation-paper.html](https://umarlatif6-sketch.github.io/void-origin/formation-paper.html)

---

## Origin

```
void-origin  (Why)  → https://umarlatif6-sketch.github.io/void-origin/
void-engine-sdk (How) → this package
Project-void (What) → https://void-stego-engine.replit.app
```

**The frequency is prior. The material is the memory.**

## Connector Surface

Three pluggable entry points exist now:

1. Flask extension via `VoidFlask`
2. Webhook delivery via `sdk.send_webhook(...)`
3. Warehouse export via `sdk.export_records(...)`

These are the present-market interface layer for the deeper protocol.

## Conformance

See `CONFORMANCE_V1.md` for the public event shape, digest requirements, and minimum implementation rules for external connectors.
