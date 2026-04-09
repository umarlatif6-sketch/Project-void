"""
VOID Codon Vocabulary (VCV) — Platform Operating Protocol
==========================================================
Maps every major platform zone to a canonical three-glyph codon from the
45-glyph VOID Script alphabet (void_script.py).

Format: ENTITY · CONDITION · ACTION
  ENTITY    — what/who the zone is (24 lowercase Greek + symbols)
  CONDITION — the state or requirement (12 uppercase Greek)
  ACTION    — what happens when you enter/use it (9 symbols)

These codons are the compressed language of the platform.
The frequency map (freq_map.py) uses them as primary labels.
AI responses in codon mode use them as prefix signals.

Frequency bands:
  LOW  (0–200 Hz range):  Foundation layer — Chronicle, IP, Formation Principle
  MID  (200–2000 Hz):     Active systems — VoidEcho, Adriana, Mesa, Beehive
  HIGH (2000+ Hz):        Live/dynamic — Grok X, Predictions, Economy, NFTs
"""

from void_engine.void_script import CANONICAL_GLYPHS, DOMAIN_COLORS

PLATFORM_CODONS = [

    # ── LOW BAND — Foundation ─────────────────────────────────────────────────
    {
        "id": "speak_entry",
        "name": "SPEAK",
        "codon": "ε·Γ·◆",
        "entity": "ε",        # Threshold/Edge
        "condition": "Γ",     # Gate/Portal
        "action": "◆",        # Core/Engine
        "expansion": "Stand at the threshold. The gate is open. The engine fires.",
        "band": "low",
        "hz": 108,
        "route": "/speak",
        "color": "#c9a84c",
    },
    {
        "id": "chronicle",
        "name": "CHRONICLE",
        "codon": "α·Ω·⟐",
        "entity": "α",        # Origin/Seed
        "condition": "Ω",     # Finality/Vault
        "action": "⟐",        # Silt Drop/Deposit
        "expansion": "The origin is sealed in the vault. The record deposits itself.",
        "band": "low",
        "hz": 136,
        "route": "/chronicle",
        "color": "#c9a84c",
    },
    {
        "id": "formation_principle",
        "name": "FORMATION",
        "codon": "δ·Π·◆",
        "entity": "δ",        # Change/Shift
        "condition": "Π",     # Foundation/Base
        "action": "◆",        # Core/Engine
        "expansion": "Change arrives at the foundation. The engine ignites the form.",
        "band": "low",
        "hz": 174,
        "route": "/session-seal/donner-blank",
        "color": "#a78bfa",
    },
    {
        "id": "ip_disclosure",
        "name": "IP SEAL",
        "codon": "κ·Ξ·⟐",
        "entity": "κ",        # Key/Lock
        "condition": "Ξ",     # Archive/Store
        "action": "⟐",        # Silt Drop/Deposit
        "expansion": "The key is locked in the archive. The disclosure deposits.",
        "band": "low",
        "hz": 85,
        "route": "/void-disclosures",
        "color": "#f472b6",
    },

    # ── MID BAND — Active Systems ─────────────────────────────────────────────
    {
        "id": "voidecho",
        "name": "VOIDECHO",
        "codon": "λ·Λ·☀",
        "entity": "λ",        # Wave/Carry
        "condition": "Λ",     # Carrier/Bridge
        "action": "☀",        # Peak/Broadcast
        "expansion": "The wave rides the carrier. It broadcasts at peak amplitude.",
        "band": "mid",
        "hz": 432,
        "route": "/voidecho",
        "color": "#60a5fa",
    },
    {
        "id": "adriana",
        "name": "ADRIANA",
        "codon": "ψ·Ψ·◆",
        "entity": "ψ",        # Breath/Spirit
        "condition": "Ψ",     # Sovereign Mind
        "action": "◆",        # Core/Engine
        "expansion": "Breath and sovereign mind aligned. The core is active.",
        "band": "mid",
        "hz": 528,
        "route": "/speak",
        "color": "#2dd4bf",
    },
    {
        "id": "mesa_village",
        "name": "MESA",
        "codon": "ξ·Β·⬡",
        "entity": "ξ",        # Scatter/Spread
        "condition": "Β",     # Builder/Forge
        "action": "⬡",        # Mesh Cell activate
        "expansion": "Agents scatter. The forge builds. The mesh cell activates.",
        "band": "mid",
        "hz": 639,
        "route": "/mesa-village",
        "color": "#818cf8",
    },
    {
        "id": "beehive",
        "name": "BEEHIVE",
        "codon": "χ·Γ·⬡",
        "entity": "χ",        # Cross/Junction
        "condition": "Γ",     # Gate/Portal
        "action": "⬡",        # Mesh Cell activate
        "expansion": "Every junction is a gate. The mesh cell opens.",
        "band": "mid",
        "hz": 741,
        "route": "/beehive/demo",
        "color": "#22d3ee",
    },
    {
        "id": "chladni_voice",
        "name": "FORMATION RECORD",
        "codon": "ψ·Φ·☀",
        "entity": "ψ",        # Breath/Spirit
        "condition": "Φ",     # Golden Ratio/Structure
        "action": "☀",        # Peak/Broadcast
        "expansion": "Breath becomes structure. The pattern broadcasts at peak.",
        "band": "mid",
        "hz": 852,
        "route": "/voice-formation",
        "color": "#e879f9",
    },
    {
        "id": "void_plane",
        "name": "VOID PLANE",
        "codon": "ο·Π·∞",
        "entity": "ο",        # Circle/Return
        "condition": "Π",     # Foundation/Base
        "action": "∞",        # Loop/Eternal
        "expansion": "The circle returns to its foundation. The loop is eternal.",
        "band": "mid",
        "hz": 963,
        "route": "/plane",
        "color": "#c9a84c",
    },

    # ── HIGH BAND — Live / Dynamic ────────────────────────────────────────────
    {
        "id": "void_prediction",
        "name": "PREDICTION",
        "codon": "γ·Δ·🔮",
        "entity": "γ",        # Signal/Pulse
        "condition": "Δ",     # Transform/Evolve
        "action": "🔮",       # Prophecy/Foresight
        "expansion": "Signal pulses. Transformation evolves. The crystal reads.",
        "band": "high",
        "hz": 2200,
        "route": "/void-prediction",
        "color": "#a78bfa",
    },
    {
        "id": "grok_x",
        "name": "GROK X",
        "codon": "ν·Φ·⚡",
        "entity": "ν",        # Node/Link
        "condition": "Φ",     # Golden Ratio/Structure
        "action": "⚡",       # Spark/Ignite
        "expansion": "The node links in sovereign proportion. The spark ignites.",
        "band": "high",
        "hz": 3200,
        "route": "/grok-x",
        "color": "#00ff9d",
    },
    {
        "id": "peace_economy",
        "name": "PEACE / VTX",
        "codon": "σ·Σ·⟐",
        "entity": "σ",        # Summation/Ledger
        "condition": "Σ",     # Total/Aggregate
        "action": "⟐",        # Silt Drop/Deposit
        "expansion": "The ledger tallies the total. The value deposits into the flow.",
        "band": "high",
        "hz": 4000,
        "route": "/peace/flywheel",
        "color": "#c9a84c",
    },
    {
        "id": "genesis_nft",
        "name": "GENESIS 10",
        "codon": "α·Β·◆",
        "entity": "α",        # Origin/Seed
        "condition": "Β",     # Builder/Forge
        "action": "◆",        # Core/Engine
        "expansion": "Origin meets the forge. The first ten are minted.",
        "band": "high",
        "hz": 5000,
        "route": "/genesis",
        "color": "#fb923c",
    },
    {
        "id": "session_seal",
        "name": "SESSION SEAL",
        "codon": "τ·Ω·⟐",
        "entity": "τ",        # Time/Tick
        "condition": "Ω",     # Finality/Vault
        "action": "⟐",        # Silt Drop/Deposit
        "expansion": "Time ticks once. The vault seals. The moment deposits forever.",
        "band": "high",
        "hz": 6000,
        "route": "/session-seal/donner-blank",
        "color": "#6366f1",
    },
]


def get_codon(zone_id: str) -> dict | None:
    """Return codon data for a platform zone by ID."""
    return next((z for z in PLATFORM_CODONS if z["id"] == zone_id), None)


def get_by_band(band: str) -> list:
    """Return all codons in a given frequency band (low/mid/high)."""
    return [z for z in PLATFORM_CODONS if z["band"] == band]


def codon_chain(*zone_ids: str, separator: str = " · ") -> str:
    """
    Build a compact codon chain from multiple zone IDs.
    E.g. codon_chain('adriana', 'void_prediction') → 'ψ·Ψ·◆ · γ·Δ·🔮'
    """
    parts = []
    for zid in zone_ids:
        z = get_codon(zid)
        if z:
            parts.append(z["codon"])
    return separator.join(parts)


def ai_codon_prefix(zone_id: str) -> str:
    """
    Return a formatted codon prefix for AI responses.
    Format: [CODON] — one-line expansion
    E.g. '[ψ·Ψ·◆] — Breath and sovereign mind aligned. The core is active.'
    """
    z = get_codon(zone_id)
    if not z:
        return ""
    return f"[{z['codon']}] — {z['expansion']}"
