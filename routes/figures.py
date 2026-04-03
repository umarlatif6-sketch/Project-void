"""
Sovereign Figures & Statements — /figures
One reference surface for every canonical number, frequency, economic figure,
and sovereign statement in the VOID ENGINE.

Public, no auth required. Static data only — no DB calls.

Source-of-truth imports:
  - AdrianaResonance.GLYPHS        → glyph counts and all frequency data
  - CHAPTERS_BY_TIER               → NFT tier chapter counts (adriana_scl)
  - get_four_quls()                → canonical Quls poem assignments (adriana_scl)
  - MERGE_TOKEN_THRESHOLD,
    MERGE_VTX_BONUS                → merge mechanics (blueprint_nft)
  - TIER_PRICE_MAP                 → tier pricing in pence (routes.payments)
  - VTX_PER_MILESTONE,
    REFERRALS_PER_MILESTONE        → ambassador economy (routes.ambassador)
"""

from flask import Blueprint, render_template
from void_engine.adriana_scl import AdrianaResonance, get_four_quls, CHAPTERS_BY_TIER
from void_engine.blueprint_nft import MERGE_TOKEN_THRESHOLD, MERGE_VTX_BONUS
from routes.payments import TIER_PRICE_MAP
from routes.ambassador import VTX_PER_MILESTONE, REFERRALS_PER_MILESTONE

figures_bp = Blueprint("figures", __name__)

# ── SCL glyph split (source: adriana_scl.py) ──
# Total derived from GLYPHS dict. Partition counts match the slice indices used in
# _pick_entity_condition_action(): entities[:19], conditions[19:29], actions[29:45].
_TOTAL_GLYPHS    = len(AdrianaResonance.GLYPHS)   # dynamic — reflects any lexicon changes
_ENTITY_COUNT    = 19                               # adriana_scl.py slice [:19]
_CONDITION_COUNT = 10                               # adriana_scl.py slice [19:29]
_ACTION_COUNT    = _TOTAL_GLYPHS - _ENTITY_COUNT - _CONDITION_COUNT  # remainder (29:45)

# ── Frequency bounds — derived dynamically from the canonical GLYPHS dict ──
_GLYPHS = AdrianaResonance.GLYPHS
_freq_min_key, _freq_min_data = min(_GLYPHS.items(), key=lambda x: x[1]["frequency"])
_freq_max_key, _freq_max_data = max(_GLYPHS.items(), key=lambda x: x[1]["frequency"])

_FREQ_BASE          = 432.0
_FREQ_FLOOR         = _freq_min_data["frequency"]
_FREQ_FLOOR_GLYPH   = f"{_freq_min_data['name']} ({_freq_min_key})"
_FREQ_CEILING       = _freq_max_data["frequency"]
_FREQ_CEILING_GLYPH = f"{_freq_max_data['name']} ({_freq_max_key})"

# ── Token economics — imported from source modules ──
_SOVEREIGN_TIER_GBP = TIER_PRICE_MAP["sovereign"] // 100
_VTX_PER_MILESTONE  = VTX_PER_MILESTONE
_MILESTONE_TRIGGER  = REFERRALS_PER_MILESTONE

# ── NFT chapters — imported from adriana_scl.CHAPTERS_BY_TIER ──
_NFT_CHAPTERS = {k.capitalize(): v for k, v in CHAPTERS_BY_TIER.items()}

# ── Merge economics — imported from blueprint_nft module constants ──
_MERGE_FOR_RARE       = MERGE_TOKEN_THRESHOLD
_MERGE_RARE_BONUS_VTX = MERGE_VTX_BONUS

# ── Bonding curve: "price doubled with every 250 minted" ──
# This figure appears in the NFT narrative spec (chronicle_adriana.py SDK text
# and adriana_local.py briefing text) but is not enforced as a code constant —
# the mystery collection price is set per-mint at the point of purchase.
_VTX_PRICE_DOUBLES = 250

# ── Self-Prediction Engine (source: void_engine/mesa_swarm.py + task spec) ──
_PREDICT_AGENT_MIN = 10
_PREDICT_AGENT_MAX = 100     # mesa_swarm.py: max(2, min(100, n_agents))
_PREDICT_ROUNDS    = 5
_PREDICT_COST_LOW  = "£0.01–£0.10"   # 10–50 agents, ~5–15 AI calls
_PREDICT_COST_HIGH = "up to £0.20"   # 51–100 agents, ~10–20 AI calls

# ── Timeline ──
_INTERUSSIA_DEADLINE = "6 April 2026"
_INTERUSSIA_EVENT    = "InteRussia Smart Cities"

# ── Canonical statements — sovereign pull-quotes ──
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
        "jabr_bits":        286,
        "baqarah_verses":   286,
        "hex_digest_chars": 72,
        "total_glyphs":     _TOTAL_GLYPHS,
        "entity_count":     _ENTITY_COUNT,
        "condition_count":  _CONDITION_COUNT,
        "action_count":     _ACTION_COUNT,

        # Frequency anchors — all derived from GLYPHS dict
        "freq_base":          _FREQ_BASE,
        "freq_floor":         _FREQ_FLOOR,
        "freq_floor_glyph":   _FREQ_FLOOR_GLYPH,
        "freq_ceiling":       _FREQ_CEILING,
        "freq_ceiling_glyph": _FREQ_CEILING_GLYPH,

        # Token economics — from source modules
        "sovereign_tier_gbp":   _SOVEREIGN_TIER_GBP,
        "vtx_per_milestone":    _VTX_PER_MILESTONE,
        "milestone_trigger":    _MILESTONE_TRIGGER,
        "nft_chapters":         _NFT_CHAPTERS,
        "merge_for_rare":       _MERGE_FOR_RARE,
        "merge_rare_bonus_vtx": _MERGE_RARE_BONUS_VTX,
        "vtx_price_doubles":    _VTX_PRICE_DOUBLES,

        # Self-Prediction Engine
        "predict_agent_min": _PREDICT_AGENT_MIN,
        "predict_agent_max": _PREDICT_AGENT_MAX,
        "predict_rounds":    _PREDICT_ROUNDS,
        "predict_cost_low":  _PREDICT_COST_LOW,
        "predict_cost_high": _PREDICT_COST_HIGH,

        # Timeline
        "interussia_deadline": _INTERUSSIA_DEADLINE,
        "interussia_event":    _INTERUSSIA_EVENT,

        # Canonical data
        "statements": CANONICAL_STATEMENTS,
        "four_quls":  four_quls,
    }
    return render_template("figures.html", **context)
