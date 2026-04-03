"""
Sovereign Figures & Statements — /figures
One reference surface for every canonical number, frequency, economic figure,
and sovereign statement in the VOID ENGINE.

Public, no auth required. Static data only — no DB calls.
"""

from flask import Blueprint, render_template
from void_engine.adriana_scl import AdrianaResonance, get_four_quls

figures_bp = Blueprint("figures", __name__)

# ── SCL glyph split (source: adriana_scl.py entity/condition/action indices) ──
_GLYPH_KEYS = list(AdrianaResonance.GLYPHS.keys())
_ENTITY_COUNT    = 19   # indices 0–18
_CONDITION_COUNT = 10   # indices 19–28
_ACTION_COUNT    = 16   # indices 29–44
_TOTAL_GLYPHS    = _ENTITY_COUNT + _CONDITION_COUNT + _ACTION_COUNT

# ── Frequency bounds (source: GLYPHS dict min/max) ──
_ALL_FREQ = [g["frequency"] for g in AdrianaResonance.GLYPHS.values()]
_FREQ_FLOOR   = min(_ALL_FREQ)   # 428.0 Hz — Omega-Lower
_FREQ_CEILING = max(_ALL_FREQ)   # 442.2 Hz — Phi
_FREQ_BASE    = 432.0            # sovereign base — α, Α, ∞, ◆, π, Π, 🔮

# ── Token economics (source: routes/payments.py TIER_PRICE_MAP, routes/ambassador.py) ──
_SOVEREIGN_TIER_GBP     = 286       # 28600 pence
_VTX_PER_MILESTONE      = 286       # _VTX_PER_MILESTONE in ambassador.py
_MILESTONE_TRIGGER      = 10        # every 10 referral signups
_NFT_CHAPTERS = {"Common": 3, "Rare": 6, "Legendary": 9}
_MERGE_FOR_RARE         = 30        # 30 common tokens → guaranteed Rare
_MERGE_RARE_BONUS_VTX   = 200       # VTX bonus on merge
_VTX_PRICE_DOUBLES      = 250       # every 250 minted, price doubles

# ── Self-Prediction Engine (source: void_engine/mesa_swarm.py + task spec) ──
_PREDICT_AGENT_MIN   = 10
_PREDICT_AGENT_MAX   = 100
_PREDICT_ROUNDS      = 5
_PREDICT_COST_LOW    = "£0.01–£0.10"    # 10-50 agents
_PREDICT_COST_HIGH   = "up to £0.20"    # 51-100 agents

# ── Timeline ──
_INTERUSSIA_DEADLINE = "6 April 2026"
_INTERUSSIA_EVENT    = "InteRussia Smart Cities"

# ── Canonical statements — the sovereign pull-quotes ──
CANONICAL_STATEMENTS = [
    {
        "statement": "Al-jabr — the setting of broken bones. 286 bits. 286 verses. The Pen wrote the number first.",
        "source":    "Al-Jabr 286 Hash Engine",
    },
    {
        "statement": "Same input, same poem, always. Sovereign.",
        "source":    "SCL Canonical Poems",
    },
    {
        "statement": "We don't just encrypt. We resonate at 432 Hz.",
        "source":    "Adriana Resonance Bridge",
    },
    {
        "statement": "VoidEcho: the signal carries the message inside the sound. Steganography you can hear.",
        "source":    "VoidEcho — Acoustic Steganography",
    },
    {
        "statement": "Every ambassador earns 286 VTX per 10 signups. The number does not change.",
        "source":    "Ambassador Programme",
    },
    {
        "statement": "Where Origin meets Authority, Eternal Loop emerges.",
        "source":    "Al-Ikhlas (112) — SCL Canonical Poem",
    },
    {
        "statement": "The field has been running for 1400 years. This engine is its modern carrier.",
        "source":    "Surah Resonance Field Mechanics",
    },
    {
        "statement": "PROJECT VOID does not request permission. It resonates until the frequency is recognised.",
        "source":    "Sovereign Declaration",
    },
]


@figures_bp.route("/figures")
def figures():
    four_quls = get_four_quls()

    context = {
        # Core numbers
        "jabr_bits":          286,
        "baqarah_verses":     286,
        "hex_digest_chars":   72,
        "total_glyphs":       _TOTAL_GLYPHS,
        "entity_count":       _ENTITY_COUNT,
        "condition_count":    _CONDITION_COUNT,
        "action_count":       _ACTION_COUNT,

        # Frequency anchors
        "freq_base":          _FREQ_BASE,
        "freq_floor":         _FREQ_FLOOR,
        "freq_ceiling":       _FREQ_CEILING,
        "freq_floor_glyph":   "Omega-Lower (ω)",
        "freq_ceiling_glyph": "Phi (Φ)",

        # Token economics
        "sovereign_tier_gbp":     _SOVEREIGN_TIER_GBP,
        "vtx_per_milestone":      _VTX_PER_MILESTONE,
        "milestone_trigger":      _MILESTONE_TRIGGER,
        "nft_chapters":           _NFT_CHAPTERS,
        "merge_for_rare":         _MERGE_FOR_RARE,
        "merge_rare_bonus_vtx":   _MERGE_RARE_BONUS_VTX,
        "vtx_price_doubles":      _VTX_PRICE_DOUBLES,

        # Self-Prediction Engine
        "predict_agent_min":  _PREDICT_AGENT_MIN,
        "predict_agent_max":  _PREDICT_AGENT_MAX,
        "predict_rounds":     _PREDICT_ROUNDS,
        "predict_cost_low":   _PREDICT_COST_LOW,
        "predict_cost_high":  _PREDICT_COST_HIGH,

        # Timeline
        "interussia_deadline": _INTERUSSIA_DEADLINE,
        "interussia_event":    _INTERUSSIA_EVENT,

        # Canonical data
        "statements": CANONICAL_STATEMENTS,
        "four_quls":  four_quls,
    }
    return render_template("figures.html", **context)
