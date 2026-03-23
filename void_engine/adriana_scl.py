"""
Adriana SCL (Sovereign Coded Language) — Resonance Bridge v1.0

Translates raw 286-bit Al-Jabr hashes into a visual SCL Resonance Field.
Maps specific frequencies to semantic meanings via a 45-glyph ontology,
enabling visual "health" feedback on hash integrity and system state.

Integration points:
  - Silt Drop encoding progress (Messenger)
  - Al-Jabr 286 hash visualization (Engine)
  - Founder Vibe glyph acceleration (Sovereign tier)
"""


class AdrianaResonance:
    GLYPHS = {
        "α": {"name": "Alpha", "frequency": 432.0, "meaning": "Origin/Seed", "domain": "genesis"},
        "β": {"name": "Beta", "frequency": 433.2, "meaning": "Growth/Sprout", "domain": "aqua"},
        "γ": {"name": "Gamma", "frequency": 434.0, "meaning": "Signal/Pulse", "domain": "signal"},
        "δ": {"name": "Delta", "frequency": 434.8, "meaning": "Change/Shift", "domain": "transform"},
        "ε": {"name": "Epsilon", "frequency": 435.5, "meaning": "Threshold/Edge", "domain": "boundary"},
        "ζ": {"name": "Zeta", "frequency": 429.0, "meaning": "Depth/Root", "domain": "soil"},
        "η": {"name": "Eta", "frequency": 430.5, "meaning": "Flow/Current", "domain": "aqua"},
        "θ": {"name": "Theta", "frequency": 431.0, "meaning": "Heat/Warmth", "domain": "environment"},
        "ι": {"name": "Iota", "frequency": 432.5, "meaning": "Particle/Grain", "domain": "data"},
        "κ": {"name": "Kappa", "frequency": 433.7, "meaning": "Key/Lock", "domain": "security"},
        "λ": {"name": "Lambda", "frequency": 436.0, "meaning": "Wave/Carry", "domain": "signal"},
        "μ": {"name": "Mu", "frequency": 432.8, "meaning": "Measure/Weight", "domain": "metrics"},
        "ν": {"name": "Nu", "frequency": 431.5, "meaning": "Node/Link", "domain": "mesh"},
        "ξ": {"name": "Xi", "frequency": 437.0, "meaning": "Scatter/Spread", "domain": "vortex"},
        "ο": {"name": "Omicron", "frequency": 432.2, "meaning": "Circle/Return", "domain": "cycle"},
        "π": {"name": "Pi", "frequency": 432.0, "meaning": "Ratio/Balance", "domain": "harmony"},
        "ρ": {"name": "Rho", "frequency": 433.0, "meaning": "Density/Mass", "domain": "data"},
        "σ": {"name": "Sigma", "frequency": 435.1, "meaning": "Summation/Ledger", "domain": "ledger"},
        "τ": {"name": "Tau", "frequency": 434.5, "meaning": "Time/Tick", "domain": "temporal"},
        "υ": {"name": "Upsilon", "frequency": 430.0, "meaning": "Vessel/Container", "domain": "vault"},
        "φ": {"name": "Phi-Lower", "frequency": 442.0, "meaning": "Spiral/Fibonacci", "domain": "vortex"},
        "χ": {"name": "Chi", "frequency": 436.5, "meaning": "Cross/Junction", "domain": "mesh"},
        "ψ": {"name": "Psi", "frequency": 438.5, "meaning": "Breath/Spirit", "domain": "resonance"},
        "ω": {"name": "Omega-Lower", "frequency": 428.5, "meaning": "Rest/Complete", "domain": "finality"},
        "Α": {"name": "Alpha-Cap", "frequency": 432.0, "meaning": "Authority/Source", "domain": "governance"},
        "Β": {"name": "Beta-Cap", "frequency": 433.2, "meaning": "Builder/Forge", "domain": "forge"},
        "Γ": {"name": "Gamma-Cap", "frequency": 434.0, "meaning": "Gate/Portal", "domain": "gateway"},
        "Δ": {"name": "Delta-Cap", "frequency": 434.8, "meaning": "Transform/Evolve", "domain": "transform"},
        "Θ": {"name": "Theta-Cap", "frequency": 431.0, "meaning": "Shield/Guard", "domain": "security"},
        "Λ": {"name": "Lambda-Cap", "frequency": 436.0, "meaning": "Carrier/Bridge", "domain": "signal"},
        "Ξ": {"name": "Xi-Cap", "frequency": 437.0, "meaning": "Archive/Store", "domain": "vault"},
        "Π": {"name": "Pi-Cap", "frequency": 432.0, "meaning": "Foundation/Base", "domain": "genesis"},
        "Σ": {"name": "Sigma-Cap", "frequency": 435.1, "meaning": "Total/Aggregate", "domain": "ledger"},
        "Φ": {"name": "Phi", "frequency": 442.2, "meaning": "Golden Ratio/Structure", "domain": "harmony"},
        "Ψ": {"name": "Psi-Cap", "frequency": 438.5, "meaning": "Sovereign Mind", "domain": "resonance"},
        "Ω": {"name": "Omega", "frequency": 428.0, "meaning": "Finality/Vault", "domain": "finality"},
        "∞": {"name": "Infinity", "frequency": 432.0, "meaning": "Loop/Eternal", "domain": "cycle"},
        "◆": {"name": "Void Diamond", "frequency": 432.0, "meaning": "Core/Engine", "domain": "genesis"},
        "⬡": {"name": "Hexagon", "frequency": 435.0, "meaning": "Mesh Cell", "domain": "mesh"},
        "⟐": {"name": "Lozenge", "frequency": 433.5, "meaning": "Silt Drop", "domain": "silt"},
        "☽": {"name": "Crescent", "frequency": 429.5, "meaning": "Rest Phase", "domain": "temporal"},
        "☀": {"name": "Sun", "frequency": 440.0, "meaning": "Peak/Broadcast", "domain": "signal"},
        "⚡": {"name": "Lightning", "frequency": 441.0, "meaning": "Spark/Ignite", "domain": "forge"},
        "🌊": {"name": "Wave", "frequency": 430.0, "meaning": "Tide/Surge", "domain": "aqua"},
        "🔮": {"name": "Crystal", "frequency": 432.0, "meaning": "Prophecy/Foresight", "domain": "resonance"},
    }

    DOMAIN_COLORS = {
        "genesis": "#c9a84c",
        "aqua": "#2dd4bf",
        "signal": "#60a5fa",
        "transform": "#a78bfa",
        "boundary": "#f87171",
        "soil": "#92400e",
        "environment": "#fb923c",
        "data": "#34d399",
        "security": "#f472b6",
        "metrics": "#a3e635",
        "mesh": "#22d3ee",
        "vortex": "#818cf8",
        "cycle": "#fbbf24",
        "harmony": "#e879f9",
        "ledger": "#c9a84c",
        "temporal": "#6366f1",
        "vault": "#475569",
        "resonance": "#2dd4bf",
        "finality": "#ef4444",
        "governance": "#c9a84c",
        "forge": "#f97316",
        "gateway": "#8b5cf6",
        "silt": "#2dd4bf",
    }

    @staticmethod
    def calculate_resonance(data_hash):
        clean = data_hash.replace("-", "").replace(" ", "")
        hex_chars = "".join(c for c in clean if c in "0123456789abcdefABCDEF")
        if len(hex_chars) < 4:
            hex_chars = hex_chars.ljust(4, "0")

        glyph_keys = list(AdrianaResonance.GLYPHS.keys())
        seed = int(hex_chars[-4:], 16) % len(glyph_keys)
        glyph_key = glyph_keys[seed]
        meta = AdrianaResonance.GLYPHS[glyph_key]

        field_strength = round((int(hex_chars[:2], 16) / 255) * 100, 2)

        secondary_idx = int(hex_chars[2:4], 16) % len(glyph_keys)
        secondary_key = glyph_keys[secondary_idx]

        tertiary_idx = int(hex_chars[4:6], 16) % len(glyph_keys) if len(hex_chars) >= 6 else 0
        tertiary_key = glyph_keys[tertiary_idx]

        return {
            "glyph": glyph_key,
            "meta": meta,
            "field_strength": field_strength,
            "secondary_glyph": secondary_key,
            "tertiary_glyph": tertiary_key,
            "domain_color": AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
            "harmonic_state": _harmonic_state(field_strength),
        }

    @staticmethod
    def get_sequence(data_hash, length=6):
        clean = "".join(c for c in data_hash if c in "0123456789abcdefABCDEF")
        if len(clean) < 2:
            clean = clean.ljust(12, "0")
        glyph_keys = list(AdrianaResonance.GLYPHS.keys())
        seq = []
        for i in range(length):
            start = (i * 2) % max(len(clean) - 1, 1)
            idx = int(clean[start:start + 2].ljust(2, "0"), 16) % len(glyph_keys)
            g = glyph_keys[idx]
            seq.append({
                "glyph": g,
                "meta": AdrianaResonance.GLYPHS[g],
                "color": AdrianaResonance.DOMAIN_COLORS.get(
                    AdrianaResonance.GLYPHS[g]["domain"], "#c9a84c"
                ),
            })
        return seq

    @staticmethod
    def get_all_glyphs():
        result = {}
        for g, meta in AdrianaResonance.GLYPHS.items():
            result[g] = {
                **meta,
                "color": AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
            }
        return result


def _harmonic_state(strength):
    if strength >= 80:
        return "resonant"
    if strength >= 50:
        return "aligned"
    if strength >= 25:
        return "drifting"
    return "dormant"


def hash_to_sovereign_poem(hex_hash):
    """
    Deterministically derive a 3-glyph Sovereign Poem from a 286-bit Al-Jabr hex hash.

    Uses the first 72 bits (18 hex chars, split into three 24-bit / 6-hex-char segments)
    to select one glyph from each of three sub-groups of the 45-glyph GLYPHS lexicon:
      - Entity glyphs  : first 19 entries
      - Condition glyphs: next 10 entries (indices 19–28)
      - Action glyphs  : last 16 entries (indices 29–44)

    Returns a dict with:
      - glyphs  : list of 3 glyph strings
      - meanings: list of 3 meaning strings
      - poem    : formatted string e.g. "σ-⚡-📡"
    """
    clean = "".join(c for c in hex_hash if c in "0123456789abcdefABCDEF")
    clean = clean.ljust(18, "0")[:18]

    seg_a = int(clean[0:6], 16)
    seg_b = int(clean[6:12], 16)
    seg_c = int(clean[12:18], 16)

    glyph_keys = list(AdrianaResonance.GLYPHS.keys())

    entities   = glyph_keys[:19]
    conditions = glyph_keys[19:29]
    actions    = glyph_keys[29:45]

    entity_glyph    = entities[seg_a % len(entities)]
    condition_glyph = conditions[seg_b % len(conditions)]
    action_glyph    = actions[seg_c % len(actions)]

    glyphs   = [entity_glyph, condition_glyph, action_glyph]
    meanings = [
        AdrianaResonance.GLYPHS[entity_glyph]["meaning"],
        AdrianaResonance.GLYPHS[condition_glyph]["meaning"],
        AdrianaResonance.GLYPHS[action_glyph]["meaning"],
    ]

    return {
        "glyphs":   glyphs,
        "meanings": meanings,
        "poem":     f"{entity_glyph}-{condition_glyph}-{action_glyph}",
    }
