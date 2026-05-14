"""
Project Void — Message Formatting Utilities
=============================================
Helpers for building Telegram-friendly messages.
"""

from __future__ import annotations


def format_routine(routine: dict) -> str:
    """Format a workout routine into a Telegram message."""
    lines = []

    # Header
    lines.append(f"🥋 *VOID TRAINING PROTOCOL*")
    lines.append(f"Difficulty: *{routine['difficulty'].title()}*")
    lines.append(f"Duration: ~{routine['estimated_duration']}")
    if routine.get("space_vibe"):
        lines.append(f"_{routine['space_vibe']}_")
    lines.append("")

    # Warm-up
    wu = routine["warmup"]
    lines.append(f"*{wu['name']}* ({wu['duration']})")
    for i, ex in enumerate(wu["exercises"], 1):
        lines.append(f"  {i}. {ex}")
    lines.append("")

    # Main exercises
    lines.append("━━━━━━━━━━━━━━━━━━━━")
    for i, ex in enumerate(routine["exercises"], 1):
        emoji = _category_emoji(ex.get("category", ""))
        lines.append(f"\n{emoji} *Exercise {i}: {ex['name']}*")
        lines.append(f"Sets: {ex['sets']} | Reps: {ex['reps']}")
        lines.append(f"_{ex['technique']}_")

    lines.append("\n━━━━━━━━━━━━━━━━━━━━")

    # Cool-down
    cd = routine["cooldown"]
    lines.append(f"\n*{cd['name']}* ({cd['duration']})")
    for i, ex in enumerate(cd["exercises"], 1):
        lines.append(f"  {i}. {ex}")

    return "\n".join(lines)


def format_balance(user: dict) -> str:
    """Format user balance information."""
    return (
        f"💰 *Void Wallet*\n\n"
        f"🌀 *VTX:* {user['vtx_balance']:.1f}\n"
        f"☮️ *PEACE:* {user['peace_balance']:.1f}\n"
        f"🔥 *Streak:* {user['streak_days']} days\n"
        f"📊 *Earned today:* {user.get('vtx_earned_today', 0):.1f} / 50 VTX"
    )


def format_reward(reward: dict) -> str:
    """Format a VTX reward notification."""
    if reward["awarded"] == 0:
        if reward.get("reason") == "daily_cap":
            return (
                "⚡ *Daily cap reached* (50 VTX)\n\n"
                "The ledger needs rest too. Come back tomorrow — "
                "the void will be here. It always is."
            )
        return "Something went wrong with the reward calculation."

    lines = [
        f"💰 *+{reward['awarded']:.1f} VTX earned!*\n",
        f"Base: {reward.get('base', 10)} VTX",
        f"Streak multiplier: ×{reward.get('streak_mult', 1.0):.1f}",
    ]
    if reward.get("equip_mult", 0) > 0:
        lines.append(f"Equipment bonus: +{reward['equip_mult']:.0%}")
    lines.append(f"Total multiplier: ×{reward.get('total_mult', 1.0):.1f}")
    lines.append(f"\n📊 Today: {reward.get('earned_today', 0):.1f} / {reward.get('daily_cap', 50)} VTX")
    lines.append(f"💰 Balance: {reward.get('balance', 0):.1f} VTX")

    if reward.get("streak", 0) > 0:
        lines.append(f"🔥 Streak: {reward['streak']} days")

    return "\n".join(lines)


def format_shop(owned_items: list[str], items: list[dict]) -> str:
    """Format the equipment shop display."""
    lines = ["🏪 *VOID EQUIPMENT SHOP*\n"]
    lines.append("_Permanent upgrades forged in the Silt Ledger._\n")

    for item in items:
        owned = "✅" if item["id"] in owned_items else ""
        lines.append(
            f"{item['name']} {owned}\n"
            f"  {item['description']}\n"
            f"  💰 Cost: *{item['cost']} VTX*\n"
        )

    lines.append("_Use_ /buy <item\\_name> _to purchase._")
    lines.append("_Example:_ /buy signal\\_array")
    return "\n".join(lines)


def format_stats(stats: dict) -> str:
    """Format comprehensive user stats."""
    user = stats["user"]
    lines = [
        f"📊 *VOID SOVEREIGN STATS*\n",
        f"*{user.get('first_name', 'Sovereign')}* — Resonance Profile\n",
        f"━━━━━━━━━━━━━━━━━━━━",
        f"🌀 VTX Balance: *{user['vtx_balance']:.1f}*",
        f"☮️ PEACE Balance: *{user['peace_balance']:.1f}*",
        f"🔥 Current Streak: *{user['streak_days']} days*",
        f"📻 Resonance Freq: *{user.get('resonance_freq', 432.0):.1f} Hz*",
        f"",
        f"*Training Record:*",
        f"  Workouts completed: {stats['workouts_completed']}",
        f"  Total VTX earned: {stats['total_vtx_earned']:.1f}",
        f"  PEACE actions: {stats['peace_actions']}",
        f"  Total PEACE earned: {stats['total_peace_earned']:.1f}",
        f"",
        f"*Multipliers:*",
        f"  Streak: ×{stats['streak_multiplier']:.1f}",
        f"  Equipment: +{stats['equipment_multiplier']:.0%}",
        f"  Combined: ×{stats['streak_multiplier'] + stats['equipment_multiplier']:.1f}",
    ]

    if stats["inventory"]:
        lines.append(f"\n*Equipment Owned:*")
        for item_id in stats["inventory"]:
            lines.append(f"  • {item_id.replace('_', ' ').title()}")

    return "\n".join(lines)


def format_space_analysis(analysis: dict) -> str:
    """Format space analysis results."""
    lines = [
        f"🔍 *SPACE ANALYSIS*\n",
        f"Type: *{analysis.get('space_type', 'unknown').title()}*",
    ]

    if analysis.get("vibe"):
        lines.append(f"_{analysis['vibe']}_\n")

    lines.append(f"*Identified features:*")
    for feat in analysis.get("features", []):
        lines.append(f"\n▸ *{feat['name'].title()}*")
        exercises = feat.get("exercises", [])
        if exercises:
            lines.append(f"  Exercises: {', '.join(exercises[:5])}")
        if feat.get("safety_notes"):
            lines.append(f"  ⚠️ {feat['safety_notes']}")

    if analysis.get("overall_assessment"):
        lines.append(f"\n{analysis['overall_assessment']}")

    return "\n".join(lines)


def _category_emoji(category: str) -> str:
    """Map exercise category to emoji."""
    return {
        "martial_arts": "🥋",
        "strength": "💪",
        "power": "⚡",
        "cardio": "🏃",
        "core": "🎯",
        "endurance": "🔥",
        "skill": "🤸",
        "mobility": "🧘",
    }.get(category, "▸")
