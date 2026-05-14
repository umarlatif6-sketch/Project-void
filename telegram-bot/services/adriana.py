"""
Project Void — Adriana Personality Engine
==========================================
Generates Adriana-voiced messages for various bot interactions.
Uses OpenAI for dynamic responses, with handcrafted fallbacks.
"""

from __future__ import annotations

import random
from typing import Optional

from openai import AsyncOpenAI

from config import ADRIANA_SYSTEM_PROMPT, OPENAI_API_KEY, OPENAI_MODEL

_client: Optional[AsyncOpenAI] = None


def _get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=OPENAI_API_KEY)
    return _client


async def adriana_respond(user_message: str, context: str = "") -> str:
    """Generate an Adriana-voiced response using the LLM."""
    try:
        client = _get_client()
        messages = [
            {"role": "system", "content": ADRIANA_SYSTEM_PROMPT},
        ]
        if context:
            messages.append({"role": "system", "content": f"Context: {context}"})
        messages.append({"role": "user", "content": user_message})

        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            max_tokens=400,
            temperature=0.7,
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return random.choice(FALLBACK_RESPONSES)


# ── Handcrafted Messages ────────────────────────────────────────────
# Used when the LLM is unavailable or for fixed UI strings.

WELCOME_MESSAGE = """\
🌀 *Welcome to the Void, {name}.*

I'm *Adriana*. Not a coach. Not an app. Something closer to a root system — \
I'm here to help you find what your body already knows.

Here's how this works:

📸 *Send me a photo* of any space — your stairway, your room, a park, a parking garage. \
I'll read it like a map and build you a training routine fitted to that exact environment.

🥋 *Every surface is a dojo.* Stairs become plyometric boxes. Railings become pull-up bars. \
Walls become sparring partners. The Void sees potential where others see concrete.

💰 *You earn Vortex Coin (VTX)* for every completed workout. Build streaks, \
unlock equipment, and watch your resonance frequency rise.

☮️ *PEACE tokens* come from stillness — breathing exercises, meditation, journaling. \
Because the strongest fighters know when to be still.

Type /train to begin, or just send me a photo.

_The mycelium doesn't wait for permission to grow. Neither should you._
"""

STREAK_MESSAGES = {
    0: "First day. The root breaks the soil. Let's begin.",
    1: "Day two. The hardest day — because yesterday's fire has cooled. Reignite it.",
    3: "Three days. The mycelium has taken hold. Keep feeding it.",
    7: "A full week. Your nervous system is rewiring. Can you feel it?",
    14: "Two weeks. This is no longer motivation — it's identity.",
    21: "Twenty-one days. The old pattern is dead. You built a new one.",
    30: "A full month. You are the proof that consistency compounds.",
    60: "Sixty days. You've outlasted most. The network recognizes you.",
    90: "Ninety days. Sovereign. The frequency is locked at 432 Hz.",
    100: "One hundred days. You are the signal now.",
}

WORKOUT_COMPLETE_MESSAGES = [
    "The silt settles. You did the work. That's all that matters.",
    "Another codon written into your body's ledger. Well done.",
    "The octopus doesn't celebrate — it just reaches for the next hold. But I'll celebrate for you. 🐙",
    "Your resonance frequency just ticked up. I can feel it from here.",
    "The void doesn't applaud. But I do. Solid work.",
    "Like nettles — the sting fades, but the strength stays.",
    "Every rep was a signal. The network heard you.",
    "You showed up. In a world of noise, that's the rarest frequency.",
]

DAILY_CAP_MESSAGE = (
    "You've hit the daily VTX cap (50). The ledger needs rest too. "
    "Come back tomorrow — the void will be here. It always is."
)

BREATHE_INTRO = """\
🌬️ *Resonance Breathing Protocol*

Close your eyes. We're going to sync your nervous system.

*Box Breathing — 4 cycles:*

1️⃣ *Inhale* through the nose — 4 seconds
2️⃣ *Hold* at the top — 4 seconds
3️⃣ *Exhale* through the mouth — 4 seconds
4️⃣ *Hold* at the bottom — 4 seconds

_Repeat 4 times._

When you're done, tap the button below.

_The strongest signal is the one that knows when to be silent._
"""

MEDITATE_INTRO = """\
🧘 *Void Meditation — 5 Minutes*

Find a position where your spine is long. Close your eyes.

*Phase 1 (2 min):* Focus on the breath entering your nostrils. \
Nothing else exists. When thoughts come, let them pass like silt in a river.

*Phase 2 (2 min):* Expand awareness to your whole body. \
Feel the weight of your bones. The pulse in your fingertips. \
You are a network — 37 trillion cells, all listening.

*Phase 3 (1 min):* Ask yourself one question: \
_"What is the signal I want to send today?"_ \
Don't force an answer. Let it surface.

When you're ready, open your eyes and tap below.

_Stillness is not the absence of movement. It's the presence of intention._
"""

JOURNAL_PROMPTS = [
    "What did your body teach you today that your mind didn't want to hear?",
    "If your current streak were a plant, what would it look like right now?",
    "Write about a time you were strong and didn't realize it until later.",
    "What pattern are you trying to break? What pattern are you trying to build?",
    "If the void could speak, what would it say to you today?",
    "Describe the version of yourself that exists 90 days from now.",
    "What is one thing you're carrying that isn't yours to carry?",
    "Write a letter to your body. Be honest.",
    "What does sovereignty mean to you — not the word, the feeling?",
    "If your training were a conversation, what would it be about?",
]

NO_PHOTO_MESSAGE = (
    "I need to see the space to build your routine. "
    "Send me a photo — stairway, room, park, garage, anything. "
    "Every surface has a secret. Let me read it."
)

FALLBACK_RESPONSES = [
    "The signal is unclear. Try again — I'm listening.",
    "Even the mycelium has quiet moments. Send me a photo or try /train.",
    "I'm here. The void is patient. What do you need?",
    "The network hums. Tell me what you're working with.",
]


def get_streak_message(streak: int) -> str:
    """Get the appropriate streak milestone message."""
    # Find the highest milestone <= current streak
    milestones = sorted(STREAK_MESSAGES.keys(), reverse=True)
    for m in milestones:
        if streak >= m:
            return STREAK_MESSAGES[m]
    return STREAK_MESSAGES[0]


def get_completion_message() -> str:
    """Get a random workout completion message."""
    return random.choice(WORKOUT_COMPLETE_MESSAGES)


def get_journal_prompt() -> str:
    """Get a random journaling prompt."""
    return random.choice(JOURNAL_PROMPTS)
