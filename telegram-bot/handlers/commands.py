"""
Project Void — Core Command Handlers
======================================
/start, /train, /balance, /streak, /stats, /help
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from models.database import get_or_create_user, get_user, get_user_stats
from services.adriana import WELCOME_MESSAGE, get_streak_message
from utils.formatting import format_balance, format_stats

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start — onboard new users."""
    user = update.effective_user
    if not user:
        return

    db_user = get_or_create_user(
        user_id=user.id,
        username=user.username or "",
        first_name=user.first_name or "Sovereign",
    )

    name = user.first_name or "Sovereign"
    msg = WELCOME_MESSAGE.format(name=name)

    await update.message.reply_text(msg, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help — show available commands."""
    text = (
        "🌀 *Void Command Reference*\n\n"
        "📸 *Send a photo* — Analyze any space for training\n"
        "/train — Start a workout (send a photo first)\n"
        "/done — Mark current workout as complete & earn VTX\n"
        "/balance — Check your VTX and PEACE balances\n"
        "/streak — View your training streak\n"
        "/shop — Browse the equipment shop\n"
        "/buy <item> — Purchase equipment\n"
        "/breathe — Guided breathing exercise (+PEACE)\n"
        "/meditate — Void meditation session (+PEACE)\n"
        "/journal — Reflective journaling prompt (+PEACE)\n"
        "/stats — Full sovereign profile\n"
        "/help — This message\n\n"
        "_The void responds to action. Start with a photo._"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /balance — show VTX and PEACE balances."""
    user = update.effective_user
    if not user:
        return

    db_user = get_or_create_user(user_id=user.id, first_name=user.first_name or "")
    await update.message.reply_text(format_balance(db_user), parse_mode="Markdown")


async def streak_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /streak — show current streak and milestone message."""
    user = update.effective_user
    if not user:
        return

    db_user = get_or_create_user(user_id=user.id, first_name=user.first_name or "")
    streak = db_user["streak_days"]
    msg = get_streak_message(streak)

    text = (
        f"🔥 *Streak: {streak} day{'s' if streak != 1 else ''}*\n\n"
        f"_{msg}_"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /stats — comprehensive user profile."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")
    stats = get_user_stats(user.id)

    if not stats:
        await update.message.reply_text(
            "No data yet. Send a photo and start training to build your profile."
        )
        return

    await update.message.reply_text(format_stats(stats), parse_mode="Markdown")
