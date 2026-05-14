"""
Project Void — Training Handlers
==================================
Photo analysis, workout generation, and workout completion.
"""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from models.database import (
    complete_workout,
    get_latest_workout,
    get_or_create_user,
    save_workout,
)
from services.adriana import get_completion_message, NO_PHOTO_MESSAGE
from services.vision import analyze_photo
from services.workout import generate_routine
from utils.formatting import format_reward, format_routine, format_space_analysis

logger = logging.getLogger(__name__)


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming photos — analyze the space."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")

    await update.message.reply_text(
        "🔍 _Reading the space... every surface has a secret._",
        parse_mode="Markdown",
    )

    # Download the photo
    photo = update.message.photo[-1]  # highest resolution
    file = await context.bot.get_file(photo.file_id)

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name
        await file.download_to_drive(tmp_path)

    try:
        # Analyze the photo
        analysis = await analyze_photo(tmp_path)

        # Store analysis in user context for /train
        context.user_data["last_analysis"] = analysis

        # Send analysis
        await update.message.reply_text(
            format_space_analysis(analysis),
            parse_mode="Markdown",
        )

        # Offer difficulty selection
        keyboard = [
            [
                InlineKeyboardButton("🟢 Beginner", callback_data="diff_beginner"),
                InlineKeyboardButton("🟡 Intermediate", callback_data="diff_intermediate"),
                InlineKeyboardButton("🔴 Advanced", callback_data="diff_advanced"),
            ]
        ]
        await update.message.reply_text(
            "Choose your difficulty and I'll build your routine:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    except Exception as e:
        logger.error(f"Photo analysis failed: {e}")
        await update.message.reply_text(
            "The signal was disrupted. Try sending the photo again — "
            "make sure it's well-lit and shows the full space."
        )
    finally:
        # Clean up temp file
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


async def difficulty_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle difficulty selection callback."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    difficulty = query.data.replace("diff_", "")
    analysis = context.user_data.get("last_analysis")

    if not analysis:
        await query.edit_message_text(
            "No space analysis found. Send me a photo first, then choose difficulty."
        )
        return

    await query.edit_message_text(
        f"⚡ _Generating {difficulty} routine from the void..._",
        parse_mode="Markdown",
    )

    # Generate routine
    routine = generate_routine(analysis, difficulty=difficulty)

    # Save to database
    workout_id = save_workout(user.id, analysis, routine)
    context.user_data["current_workout_id"] = workout_id

    # Format and send
    routine_text = format_routine(routine)

    # Split long messages if needed (Telegram limit is 4096 chars)
    if len(routine_text) > 4000:
        mid = routine_text.rfind("\n", 0, 4000)
        await query.message.reply_text(routine_text[:mid], parse_mode="Markdown")
        await query.message.reply_text(routine_text[mid:], parse_mode="Markdown")
    else:
        await query.message.reply_text(routine_text, parse_mode="Markdown")

    # Complete button
    keyboard = [[InlineKeyboardButton("✅ Workout Complete", callback_data=f"complete_{workout_id}")]]
    await query.message.reply_text(
        "When you've finished, tap below to log it and earn your VTX.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def train_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /train — generate workout from last analysis or prompt for photo."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")
    analysis = context.user_data.get("last_analysis")

    if not analysis:
        await update.message.reply_text(
            f"📸 {NO_PHOTO_MESSAGE}",
            parse_mode="Markdown",
        )
        return

    # Offer difficulty selection
    keyboard = [
        [
            InlineKeyboardButton("🟢 Beginner", callback_data="diff_beginner"),
            InlineKeyboardButton("🟡 Intermediate", callback_data="diff_intermediate"),
            InlineKeyboardButton("🔴 Advanced", callback_data="diff_advanced"),
        ]
    ]
    await update.message.reply_text(
        "I remember the space. Choose your difficulty:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def complete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle workout completion callback."""
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    if not user:
        return

    # Extract workout ID from callback data
    try:
        workout_id = int(query.data.replace("complete_", ""))
    except (ValueError, AttributeError):
        await query.edit_message_text("Could not process completion. Try /done instead.")
        return

    # Complete the workout
    reward = complete_workout(workout_id, user.id)

    # Build response
    completion_msg = get_completion_message()
    reward_text = format_reward(reward)

    await query.edit_message_text(
        f"✅ *WORKOUT LOGGED*\n\n_{completion_msg}_\n\n{reward_text}",
        parse_mode="Markdown",
    )


async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /done — mark the latest workout as complete."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")

    # Try context first, then database
    workout_id = context.user_data.get("current_workout_id")

    if not workout_id:
        latest = get_latest_workout(user.id)
        if latest and not latest["completed"]:
            workout_id = latest["id"]

    if not workout_id:
        await update.message.reply_text(
            "No active workout to complete. Send a photo and generate a routine first."
        )
        return

    reward = complete_workout(workout_id, user.id)
    completion_msg = get_completion_message()
    reward_text = format_reward(reward)

    await update.message.reply_text(
        f"✅ *WORKOUT LOGGED*\n\n_{completion_msg}_\n\n{reward_text}",
        parse_mode="Markdown",
    )

    # Clear the current workout from context
    context.user_data.pop("current_workout_id", None)
