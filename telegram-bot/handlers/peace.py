"""
Project Void — PEACE Token Handlers
=====================================
/breathe, /meditate, /journal
Non-extractive actions that earn PEACE tokens.
"""

from __future__ import annotations

import logging

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from config import PEACE_BREATHE_REWARD, PEACE_JOURNAL_REWARD, PEACE_MEDITATE_REWARD
from models.database import (
    award_peace,
    get_or_create_user,
    get_user_inventory,
)
from services.adriana import BREATHE_INTRO, MEDITATE_INTRO, get_journal_prompt

logger = logging.getLogger(__name__)


# ── Breathing ────────────────────────────────────────────────────────

async def breathe_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /breathe — guided breathing exercise."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")

    keyboard = [[InlineKeyboardButton("🌬️ Breathing Complete", callback_data="peace_breathe")]]
    await update.message.reply_text(
        BREATHE_INTRO,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ── Meditation ───────────────────────────────────────────────────────

async def meditate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /meditate — guided meditation (requires Resonance Badge)."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")

    # Check if user has Resonance Badge
    inventory = get_user_inventory(user.id)
    if "resonance_badge" not in inventory:
        await update.message.reply_text(
            "🔒 *Meditation Locked*\n\n"
            "The /meditate command requires the *Resonance Badge* from the /shop.\n\n"
            "Until then, /breathe is always available — "
            "the breath is the first key to stillness.",
            parse_mode="Markdown",
        )
        return

    keyboard = [[InlineKeyboardButton("🧘 Meditation Complete", callback_data="peace_meditate")]]
    await update.message.reply_text(
        MEDITATE_INTRO,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ── Journaling ───────────────────────────────────────────────────────

async def journal_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /journal — reflective journaling prompt."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")

    prompt = get_journal_prompt()
    context.user_data["journal_prompt"] = prompt
    context.user_data["awaiting_journal"] = True

    await update.message.reply_text(
        f"📝 *Journal Prompt*\n\n"
        f"_{prompt}_\n\n"
        f"Write your response below. Take your time — "
        f"the void doesn't rush.\n\n"
        f"_Send your entry as a message and you'll earn PEACE tokens._",
        parse_mode="Markdown",
    )


async def handle_journal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Check if the user is in journaling mode and process their entry.
    Returns True if the message was handled as a journal entry.
    """
    if not context.user_data.get("awaiting_journal"):
        return False

    user = update.effective_user
    if not user or not update.message or not update.message.text:
        return False

    entry_text = update.message.text.strip()

    # Require minimum length for meaningful journaling
    if len(entry_text) < 20:
        await update.message.reply_text(
            "Dig a little deeper. The roots need more than a sentence to grow.\n"
            "Write at least a few lines — this is for you, not for me."
        )
        return True

    # Award PEACE
    result = award_peace(user.id, "journal", PEACE_JOURNAL_REWARD)

    prompt = context.user_data.get("journal_prompt", "")
    context.user_data["awaiting_journal"] = False
    context.user_data.pop("journal_prompt", None)

    await update.message.reply_text(
        f"📝 *Journal Entry Recorded*\n\n"
        f"☮️ *+{result['awarded']:.0f} PEACE earned*"
        f"{' (includes Mycelium Wrap bonus)' if result.get('bonus', 0) > 0 else ''}\n"
        f"Balance: {result['balance']:.1f} PEACE\n\n"
        f"_What you wrote matters. Not because I read it — "
        f"because you did._",
        parse_mode="Markdown",
    )
    return True


# ── PEACE Completion Callbacks ───────────────────────────────────────

async def peace_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle PEACE action completion callbacks."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    action = query.data.replace("peace_", "")

    reward_map = {
        "breathe": (PEACE_BREATHE_REWARD, "Breathing"),
        "meditate": (PEACE_MEDITATE_REWARD, "Meditation"),
    }

    if action not in reward_map:
        await query.edit_message_text("Unknown action.")
        return

    base_reward, action_name = reward_map[action]
    result = award_peace(user.id, action, base_reward)

    bonus_text = ""
    if result.get("bonus", 0) > 0:
        bonus_text = f" _(+{result['bonus']} Mycelium Wrap bonus)_"

    messages = {
        "breathe": (
            "The breath returns to stillness. Your nervous system just recalibrated.\n\n"
            "Like a river settling after rain — the silt finds its place."
        ),
        "meditate": (
            "You touched the signal beneath the noise. That takes courage.\n\n"
            "The octopus has neurons in every arm. You just reminded yours to listen."
        ),
    }

    await query.edit_message_text(
        f"☮️ *{action_name} Complete*\n\n"
        f"{messages.get(action, '')}\n\n"
        f"*+{result['awarded']:.0f} PEACE earned*{bonus_text}\n"
        f"Balance: *{result['balance']:.1f} PEACE*",
        parse_mode="Markdown",
    )
