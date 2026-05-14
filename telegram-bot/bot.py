"""
Project Void — Telegram Bot Entry Point
=========================================
Production-ready bot with graceful startup, shutdown, and error handling.

Usage:
    python bot.py

Environment variables:
    TELEGRAM_BOT_TOKEN  — Bot token from @BotFather
    OPENAI_API_KEY      — OpenAI API key for photo analysis
"""

from __future__ import annotations

import logging
import sys

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import TELEGRAM_BOT_TOKEN
from models.database import init_db

# ── Handlers ─────────────────────────────────────────────────────────
from handlers.commands import (
    balance_command,
    help_command,
    start_command,
    stats_command,
    streak_command,
)
from handlers.training import (
    complete_callback,
    difficulty_callback,
    done_command,
    handle_photo,
    train_command,
)
from handlers.shop import buy_command, shop_command
from handlers.peace import (
    breathe_command,
    handle_journal_entry,
    journal_command,
    meditate_command,
    peace_callback,
)

# ── Logging ──────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s — %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger("void_bot")

# Silence noisy libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)


# ── Fallback Text Handler ───────────────────────────────────────────

async def handle_text(update: Update, context) -> None:
    """Handle plain text messages — check for journal mode, else respond."""
    # Check if user is journaling
    if await handle_journal_entry(update, context):
        return

    # Default response
    await update.message.reply_text(
        "Send me a 📸 *photo of your space* and I'll build you a training routine.\n\n"
        "Or try /help to see all commands.",
        parse_mode="Markdown",
    )


# ── Error Handler ────────────────────────────────────────────────────

async def error_handler(update: object, context) -> None:
    """Log errors and notify user if possible."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something disrupted the signal. Try again in a moment.\n"
            "If this persists, the void is listening — just be patient."
        )


# ── Main ─────────────────────────────────────────────────────────────

def main() -> None:
    """Initialize and run the bot."""
    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "TELEGRAM_BOT_TOKEN not set. "
            "Create a .env file or export the variable. See README.md."
        )
        sys.exit(1)

    # Initialize database
    logger.info("Initializing Void database...")
    init_db()
    logger.info("Database ready.")

    # Build application
    logger.info("Building Void Telegram bot...")
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # ── Command Handlers ─────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("train", train_command))
    app.add_handler(CommandHandler("done", done_command))
    app.add_handler(CommandHandler("balance", balance_command))
    app.add_handler(CommandHandler("streak", streak_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CommandHandler("shop", shop_command))
    app.add_handler(CommandHandler("buy", buy_command))
    app.add_handler(CommandHandler("breathe", breathe_command))
    app.add_handler(CommandHandler("meditate", meditate_command))
    app.add_handler(CommandHandler("journal", journal_command))

    # ── Callback Query Handlers ──────────────────────────────────────
    app.add_handler(CallbackQueryHandler(difficulty_callback, pattern=r"^diff_"))
    app.add_handler(CallbackQueryHandler(complete_callback, pattern=r"^complete_"))
    app.add_handler(CallbackQueryHandler(peace_callback, pattern=r"^peace_"))

    # ── Message Handlers ─────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # ── Error Handler ────────────────────────────────────────────────
    app.add_error_handler(error_handler)

    # ── Run ──────────────────────────────────────────────────────────
    logger.info("🌀 Void bot is live. Polling for updates...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
