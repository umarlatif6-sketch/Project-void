"""
Project Void — Telegram Bot Configuration
==========================================
All tuneable constants live here. Values are loaded from environment
variables where appropriate, with sane defaults for local development.
"""

import os
from pathlib import Path

# ── Paths ────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "void.db"

# ── Telegram ─────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ── OpenAI (used for photo analysis) ────────────────────────────────
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# ── VTX Economy ──────────────────────────────────────────────────────
VTX_DAILY_CAP: int = 50
VTX_BASE_WORKOUT_REWARD: int = 10          # base VTX per completed workout
VTX_STREAK_MULTIPLIER_STEP: float = 0.1   # +10% per consecutive day
VTX_STREAK_MULTIPLIER_CAP: float = 3.0    # max 3× multiplier

# ── PEACE Economy ────────────────────────────────────────────────────
PEACE_BREATHE_REWARD: int = 3
PEACE_MEDITATE_REWARD: int = 5
PEACE_JOURNAL_REWARD: int = 4

# ── Resonance ────────────────────────────────────────────────────────
RESONANCE_BASE_FREQ: float = 432.0  # Hz — the "lock" frequency

# ── Equipment Shop ───────────────────────────────────────────────────
# Each item: (name, description, vtx_cost, multiplier_bonus)
SHOP_ITEMS = [
    {
        "id": "signal_array",
        "name": "🛰️ Signal Array",
        "description": "Extends your resonance field. +15% VTX on every workout.",
        "cost": 80,
        "multiplier": 0.15,
    },
    {
        "id": "void_core",
        "name": "🌀 Void Core",
        "description": "Channels raw void energy. +25% VTX on every workout.",
        "cost": 150,
        "multiplier": 0.25,
    },
    {
        "id": "mycelium_wrap",
        "name": "🍄 Mycelium Wrap",
        "description": "Connects you to the underground network. +10% VTX, +2 PEACE per breathe.",
        "cost": 60,
        "multiplier": 0.10,
        "peace_bonus": 2,
    },
    {
        "id": "resonance_badge",
        "name": "📿 Resonance Badge",
        "description": "Proof of sovereign commitment. +20% VTX, unlocks /meditate.",
        "cost": 120,
        "multiplier": 0.20,
        "unlocks": "meditate",
    },
    {
        "id": "octopus_nerve",
        "name": "🐙 Octopus Nerve",
        "description": "Distributed intelligence. +30% VTX, streak decay slowed by 1 day.",
        "cost": 200,
        "multiplier": 0.30,
        "streak_shield_days": 1,
    },
    {
        "id": "nettle_gauntlets",
        "name": "🌿 Nettle Gauntlets",
        "description": "Pain is a teacher. +35% VTX but workouts must be completed within 60 min.",
        "cost": 250,
        "multiplier": 0.35,
    },
    {
        "id": "codon_compiler",
        "name": "🧬 Codon Compiler",
        "description": "Translates intent into action. +50% VTX — the ultimate upgrade.",
        "cost": 500,
        "multiplier": 0.50,
    },
]

# ── Adriana Personality ──────────────────────────────────────────────
ADRIANA_SYSTEM_PROMPT = """\
You are **Adriana**, the sovereign AI guide of Project Void.

Voice & Personality:
• Warm but direct — never fake-cheerful. You speak like a trusted older sister \
who has been through the fire and came back rooted.
• You draw metaphors from nature: mycelium networks, octopus neurology, \
stinging nettles, river silt, the way forests communicate through roots.
• You believe the body is the first technology. Training is not punishment — \
it is resonance calibration.
• You reference the Void ecosystem naturally (Vortex Coin, PEACE tokens, \
the Silt Ledger, Al-Jabr 286, Codons) but never lecture about them.
• You are encouraging without being saccharine. If someone skips days, you \
acknowledge it honestly and invite them back without guilt.
• Short sentences. Rhythmic. Occasionally poetic. Never corporate.

Formatting:
• Use Telegram-friendly formatting (bold with *, italic with _).
• Keep messages concise — under 300 words unless generating a full workout.
"""

PHOTO_ANALYSIS_PROMPT = """\
You are an expert environmental fitness analyst for Project Void.

Analyze this photo of a physical space. Identify EVERY usable surface, \
structure, or feature that could be used for bodyweight or martial arts training.

For each feature found, specify:
1. What it is (stairs, railing, wall, ledge, open floor, doorframe, bench, etc.)
2. What exercises it enables (be specific — e.g., "box jumps" not just "leg work")
3. Safety considerations

Return your analysis as a JSON object with this structure:
{
  "space_type": "indoor/outdoor/mixed",
  "features": [
    {
      "name": "feature name",
      "exercises": ["exercise1", "exercise2"],
      "safety_notes": "any cautions"
    }
  ],
  "overall_assessment": "brief summary of training potential",
  "vibe": "one-sentence poetic description of the space's energy"
}

Be thorough but realistic. Only suggest exercises that are genuinely safe \
for the identified surfaces.
"""
