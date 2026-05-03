"""
Adriana Corpus Builder — Codon-Indexed Knowledge Extractor

Extracts all VOID platform knowledge into a structured, codon-indexed dataset.
Each chunk has: codon, one-line expansion, full prose, domain, and Hz fingerprint.

Sources:
  - adriana.lex                 → glyph definitions
  - void_language_glossary.json → semantic vocabulary
  - void_codon_vocab.py         → platform zone codons
  - adriana_local.py            → intent/response pairs
  - manus_context.json          → platform context
  - void_script.py              → canonical glyphs
"""

import json
import logging
import os
import re

logger = logging.getLogger(__name__)

_HERE = os.path.dirname(__file__)
_EXTERNAL_DELTA_PACK_PATH = os.path.abspath(os.path.join(_HERE, "..", "data", "adriana_delta_pack.json"))


def _load_glossary() -> list:
    path = os.path.join(_HERE, "void_language_glossary.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_manus_context() -> dict:
    path = os.path.join(_HERE, "manus_context.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_external_delta_pack() -> dict | None:
    path = _EXTERNAL_DELTA_PACK_PATH
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_lex() -> list:
    """
    Parse adriana.lex into a list of glyph entry dicts.
    Format: glyph | category | domain | key | description | python_equivalent | hz_fingerprint
    """
    path = os.path.join(_HERE, "adriana.lex")
    entries = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or line.startswith("=") or line.startswith("-"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 7:
                continue
            entries.append({
                "glyph": parts[0],
                "category": parts[1],
                "domain": parts[2],
                "key": parts[3],
                "description": parts[4],
                "python_equivalent": parts[5],
                "hz": _safe_float(parts[6]),
            })
    return entries


def _safe_float(val: str) -> float:
    try:
        return float(val.strip())
    except (ValueError, AttributeError):
        return 432.0


def _load_intents() -> list:
    """
    Load raw intent dicts from adriana_local._INTENTS (module-level list).
    Each dict has keys: id, patterns (raw strings), response.
    """
    from void_engine import adriana_local
    return list(getattr(adriana_local, "_INTENTS", []))


def _load_codon_vocab() -> list:
    from void_engine.void_codon_vocab import PLATFORM_CODONS
    return PLATFORM_CODONS


def _load_canonical_glyphs() -> dict:
    from void_engine.void_script import CANONICAL_GLYPHS
    return CANONICAL_GLYPHS


def build_corpus() -> list:
    """
    Build and return the full codon-indexed knowledge corpus.

    Returns a list of dicts, each with:
      - id:        unique string identifier
      - codon:     three-glyph chain (e.g. 'ψ·Ψ·◆')
      - expansion: one-line compressed meaning (~15 tokens)
      - prose:     full knowledge paragraph
      - domain:    semantic domain label
      - hz:        Hz fingerprint (float)
      - source:    source file/module label
    """
    chunks = []

    # ── 1. Platform zone codons from void_codon_vocab.py ─────────────────────
    for zone in _load_codon_vocab():
        chunks.append({
            "id": f"codon_zone_{zone['id']}",
            "codon": zone["codon"],
            "expansion": zone["expansion"],
            "prose": (
                f"{zone['name']} ({zone['codon']}): {zone['expansion']} "
                f"Platform route: {zone.get('route', 'n/a')}. "
                f"Frequency band: {zone.get('band', 'mid')} at {zone.get('hz', 432)} Hz."
            ),
            "domain": _band_to_domain(zone.get("band", "mid")),
            "hz": float(zone.get("hz", 432)),
            "source": "void_codon_vocab",
        })

    # ── 2. Adriana Lexicon glyph entries from adriana.lex ────────────────────
    for entry in _load_lex():
        glyph = entry["glyph"]
        codon = f"{glyph}·Ψ·◆"
        chunks.append({
            "id": f"lex_{entry['key']}",
            "codon": codon,
            "expansion": f"{glyph} ({entry['category']}): {entry['description']}",
            "prose": (
                f"VOID Script Lexicon — {glyph} | {entry['category']} | "
                f"domain: {entry['domain']} | key: {entry['key']} | "
                f"{entry['description']} | sensor: {entry['python_equivalent']} | "
                f"Hz: {entry['hz']}"
            ),
            "domain": entry["domain"],
            "hz": entry["hz"],
            "source": "adriana.lex",
        })

    # ── 3. Canonical glyph definitions from void_script.py ───────────────────
    glyphs = _load_canonical_glyphs()
    glyph_keys = list(glyphs.keys())
    entities = [g for g, m in glyphs.items() if m["role"] == "entity"]
    conditions = [g for g, m in glyphs.items() if m["role"] == "condition"]
    actions = [g for g, m in glyphs.items() if m["role"] == "action"]

    for char, meta in glyphs.items():
        codon = _derive_glyph_codon(char, meta, entities, conditions, actions)
        chunks.append({
            "id": f"glyph_{meta['name'].lower().replace(' ', '_').replace('-', '_')}",
            "codon": codon,
            "expansion": f"{char} ({meta['name']}): {meta['meaning']} at {meta['frequency']} Hz.",
            "prose": (
                f"VOID Script glyph {char} — {meta['name']}. "
                f"Meaning: {meta['meaning']}. Domain: {meta['domain']}. "
                f"Frequency: {meta['frequency']} Hz. Role: {meta['role']}. "
                f"Visual: {meta.get('glyph_description', '')}"
            ),
            "domain": meta["domain"],
            "hz": float(meta["frequency"]),
            "source": "void_script",
        })

    # ── 3. Platform vocabulary from void_language_glossary.json ──────────────
    for entry in _load_glossary():
        codon = _vocab_codon(entry.get("key", ""), glyphs, entities, conditions, actions)
        chunks.append({
            "id": f"vocab_{entry['key']}",
            "codon": codon,
            "expansion": f"{entry.get('chosen_word', entry['english'])}: {entry.get('void_definition', entry['description'])[:80]}",
            "prose": (
                f"VOID Language term: {entry['english']} → {entry.get('chosen_word', '')} "
                f"({entry.get('original_script', '')} from {entry.get('source_language', '')}). "
                f"{entry.get('void_definition', entry.get('description', ''))} "
                f"Hz fingerprint: {entry.get('hz_fingerprint', 432.0)} "
                f"({entry.get('hz_rationale', '')})."
            ),
            "domain": _key_to_domain(entry.get("key", "")),
            "hz": float(entry.get("hz_fingerprint", 432.0)),
            "source": "void_language_glossary",
        })

    # ── 4. Intent/response pairs from adriana_local.py ───────────────────────
    intents = _load_intents()
    for intent in intents:
        intent_id = intent.get("id", "unknown")
        response = intent.get("response", "")
        patterns = intent.get("patterns", [])
        sample_pattern = patterns[0] if patterns else ""
        codon = _intent_codon(intent_id, glyphs, entities, conditions, actions)
        expansion = response[:100].strip()
        if len(response) > 100:
            expansion += "..."
        chunks.append({
            "id": f"intent_{intent_id}",
            "codon": codon,
            "expansion": expansion,
            "prose": (
                f"Adriana intent '{intent_id}': {response} "
                f"Trigger patterns include: {sample_pattern}."
            ),
            "domain": _intent_to_domain(intent_id),
            "hz": 432.0,
            "source": "adriana_local",
        })

    # ── 5. Key platform concepts from manus_context.json ─────────────────────
    ctx = _load_manus_context()
    for system_key, system_desc in ctx.get("core_systems", {}).items():
        codon = _system_codon(system_key, glyphs, entities, conditions, actions)
        chunks.append({
            "id": f"system_{system_key.lower()}",
            "codon": codon,
            "expansion": f"{system_key}: {str(system_desc)[:80]}",
            "prose": f"VOID core system — {system_key}: {system_desc}",
            "domain": _system_to_domain(system_key),
            "hz": 432.0,
            "source": "manus_context",
        })

    for concept_key, concept_val in ctx.get("naming_ontology", {}).items():
        codon = _vocab_codon(concept_key, glyphs, entities, conditions, actions)
        chunks.append({
            "id": f"naming_{concept_key}",
            "codon": codon,
            "expansion": f"{concept_key}: {str(concept_val)[:80]}",
            "prose": f"VOID naming ontology — {concept_key}: {concept_val}",
            "domain": _key_to_domain(concept_key),
            "hz": 432.0,
            "source": "manus_context",
        })

    # ── 6. External Adriana delta pack from fork integration ────────────────
    delta_pack = _load_external_delta_pack()
    if delta_pack:
        for idx, entry in enumerate(delta_pack.get("entries", []), start=1):
            chunks.append({
                "id": f"external_fork_{idx}",
                "codon": entry.get("codon", "B-..-Z"),
                "expansion": entry.get("expansion", "External fork delta"),
                "prose": entry.get("prose", f"External fork asset {entry.get('path', 'unknown')}"),
                "domain": entry.get("domain", "reference"),
                "hz": float(entry.get("hz", 432.0)),
                "source": entry.get("source", "external_ai_agents_fork"),
            })

    _REQUIRED_SOURCES = {
        "void_codon_vocab", "adriana.lex", "void_script",
        "adriana_local", "manus_context", "void_language_glossary",
    }
    sources_present = {c["source"] for c in chunks}
    missing = _REQUIRED_SOURCES - sources_present
    if missing:
        logger.warning(
            "Adriana corpus missing chunks from required sources: %s. "
            "Training coverage may be reduced.",
            missing,
        )
    by_source = {src: sum(1 for c in chunks if c["source"] == src) for src in sources_present}
    logger.info("Adriana corpus built: %d chunks — %s", len(chunks), by_source)
    return chunks


# ── Domain/codon mapping helpers ─────────────────────────────────────────────

def _band_to_domain(band: str) -> str:
    return {"low": "genesis", "mid": "resonance", "high": "signal"}.get(band, "resonance")


def _key_to_domain(key: str) -> str:
    mapping = {
        "void": "genesis", "resonance": "resonance", "silt": "silt",
        "sovereign": "governance", "echo": "mesh", "kinetic": "signal",
        "silk": "mesh", "mycelium": "mesh", "peace": "harmony", "genesis": "genesis",
    }
    return mapping.get(key, "resonance")


def _intent_to_domain(intent_id: str) -> str:
    mapping = {
        "what_is_void": "genesis", "how_to_start": "genesis", "what_is_adriana": "resonance",
        "how_to_encode": "signal", "passphrase": "security", "how_to_decode": "signal",
        "md5_checksum": "data", "what_is_carrier": "signal", "carrier_format": "signal",
        "scatter_modes": "vortex", "burst_mode": "signal", "capacity": "data",
        "journalism_port": "mesh", "visualizer": "signal", "mesh_network": "mesh",
        "void_messenger": "security", "silt_drops": "silt", "what_is_vtx": "ledger",
        "earn_vtx": "ledger", "buy_vtx": "ledger", "spend_vtx": "ledger",
        "symmetry_score": "ledger", "tier_overview": "governance", "ghost_tier": "governance",
        "journalist_tier": "governance", "sovereign_tier": "governance",
    }
    return mapping.get(intent_id, "resonance")


def _system_to_domain(system_key: str) -> str:
    mapping = {
        "VoidEcho": "signal", "SphereKey": "security", "VTX_PEACE": "ledger",
        "BlueprintNFT": "genesis", "GeographyNFT": "genesis", "Adriana": "resonance",
        "BeehiveMesh": "mesh", "QiSync": "signal", "MycoVOID": "mesh",
        "VoidGame": "temporal", "VoidLanguage": "resonance", "CodonDistilEngine": "data",
    }
    return mapping.get(system_key, "resonance")


def _stable_index(key: str, n: int) -> int:
    """Deterministic index using SHA-256 so corpus codon assignments never vary."""
    import hashlib
    digest = hashlib.sha256(key.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") % n


def _derive_glyph_codon(char: str, meta: dict, entities: list, conditions: list, actions: list) -> str:
    role = meta.get("role", "entity")
    if role == "entity":
        e = char
        c = conditions[_stable_index(char + "c", len(conditions))] if conditions else "Ψ"
        a = actions[_stable_index(char + "a", len(actions))] if actions else "◆"
    elif role == "condition":
        e = entities[_stable_index(char + "e", len(entities))] if entities else "ψ"
        c = char
        a = actions[_stable_index(char + "a", len(actions))] if actions else "◆"
    else:
        e = entities[_stable_index(char + "e", len(entities))] if entities else "ψ"
        c = conditions[_stable_index(char + "c", len(conditions))] if conditions else "Ψ"
        a = char
    return f"{e}·{c}·{a}"


def _vocab_codon(key: str, glyphs: dict, entities: list, conditions: list, actions: list) -> str:
    _VOCAB_CODON_MAP = {
        "void": "α·Π·◆",
        "resonance": "ψ·Ψ·◆",
        "silt": "ι·Ξ·⟐",
        "sovereign": "ψ·Α·◆",
        "echo": "λ·Λ·☀",
        "kinetic": "φ·Δ·⚡",
        "silk": "ν·Θ·⬡",
        "mycelium": "ζ·Π·⬡",
        "peace": "π·Φ·∞",
        "genesis": "α·Β·◆",
    }
    return _VOCAB_CODON_MAP.get(key, "ψ·Ψ·◆")


def _intent_codon(intent_id: str, glyphs: dict, entities: list, conditions: list, actions: list) -> str:
    _INTENT_CODON_MAP = {
        "what_is_void": "α·Π·◆",
        "how_to_start": "ε·Γ·◆",
        "what_is_adriana": "ψ·Ψ·◆",
        "how_to_encode": "ι·Β·⟐",
        "passphrase": "κ·Θ·◆",
        "how_to_decode": "υ·Ξ·◆",
        "md5_checksum": "μ·Α·◆",
        "what_is_carrier": "λ·Λ·☀",
        "carrier_format": "λ·Λ·◆",
        "scatter_modes": "ξ·Φ·🌊",
        "burst_mode": "γ·Δ·⚡",
        "capacity": "ρ·Σ·◆",
        "journalism_port": "ε·Γ·⟐",
        "visualizer": "γ·Φ·☀",
        "mesh_network": "χ·Γ·⬡",
        "void_messenger": "κ·Θ·⬡",
        "silt_drops": "ι·Ξ·⟐",
        "what_is_vtx": "σ·Σ·⟐",
        "earn_vtx": "σ·Δ·⚡",
        "buy_vtx": "σ·Β·⟐",
        "spend_vtx": "σ·Α·⟐",
        "symmetry_score": "π·Σ·∞",
        "tier_overview": "ψ·Α·◆",
        "ghost_tier": "α·Γ·◆",
        "journalist_tier": "ε·Β·⟐",
        "sovereign_tier": "ψ·Ψ·⬡",
    }
    return _INTENT_CODON_MAP.get(intent_id, "ψ·Ψ·◆")


def _system_codon(system_key: str, glyphs: dict, entities: list, conditions: list, actions: list) -> str:
    _SYSTEM_CODON_MAP = {
        "VoidEcho": "λ·Λ·☀",
        "SphereKey": "κ·Θ·◆",
        "VTX_PEACE": "σ·Σ·⟐",
        "BlueprintNFT": "α·Β·◆",
        "GeographyNFT": "α·Π·◆",
        "Adriana": "ψ·Ψ·◆",
        "BeehiveMesh": "χ·Γ·⬡",
        "QiSync": "μ·Φ·☀",
        "MycoVOID": "ζ·Π·⬡",
        "VoidGame": "τ·Δ·🔮",
        "VoidLanguage": "ψ·Α·◆",
        "CodonDistilEngine": "ρ·Ξ·⟐",
    }
    return _SYSTEM_CODON_MAP.get(system_key, "ψ·Ψ·◆")
