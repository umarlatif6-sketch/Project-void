"""
Project Void — Equipment Shop Handler
=======================================
/shop, /buy <item_id>
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import SHOP_ITEMS
from models.database import get_or_create_user, get_user_inventory, purchase_item
from utils.formatting import format_shop

logger = logging.getLogger(__name__)


async def shop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /shop — display available equipment."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")
    owned = get_user_inventory(user.id)
    text = format_shop(owned, SHOP_ITEMS)

    await update.message.reply_text(text, parse_mode="Markdown")


async def buy_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /buy <item_id> — purchase equipment."""
    user = update.effective_user
    if not user:
        return

    get_or_create_user(user_id=user.id, first_name=user.first_name or "")

    # Parse item ID from command args
    if not context.args:
        await update.message.reply_text(
            "Specify an item to buy.\n"
            "Example: `/buy signal_array`\n\n"
            "Use /shop to see available items.",
            parse_mode="Markdown",
        )
        return

    item_id = context.args[0].lower().strip()

    # Try to match by ID or partial name
    matched_item = None
    for item in SHOP_ITEMS:
        if item["id"] == item_id:
            matched_item = item
            break
        # Fuzzy: allow "signal" to match "signal_array"
        if item_id in item["id"] or item_id.replace(" ", "_") == item["id"]:
            matched_item = item
            break

    if not matched_item:
        await update.message.reply_text(
            f"Item `{item_id}` not found in the Void armoury.\n"
            "Use /shop to see available items.",
            parse_mode="Markdown",
        )
        return

    result = purchase_item(user.id, matched_item["id"])

    if result["success"]:
        item = result["item"]
        await update.message.reply_text(
            f"✅ *{item['name']} acquired!*\n\n"
            f"{item['description']}\n\n"
            f"💰 Remaining balance: *{result['new_balance']:.1f} VTX*\n\n"
            f"_The equipment bonds to your signal. Its effects are permanent._",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            f"❌ *Purchase failed*\n\n{result['reason']}",
            parse_mode="Markdown",
        )
