"""
VOID Sovereign Trade Engine — The £1 Protocol Tools
PROJECT VOID — Root Protocol Implementation

Trade journal, frequency analyser, and Chladni visualiser for the £1 Protocol.
This is not a trading bot. This is a sovereignty mirror.

The journal records: Time, Feeling, Gap, Result.
The analyser finds: Your frequency pattern.
The visualiser shows: Your Chladni plate — where your resonance is strongest.
"""

import csv
import hashlib
import json
import logging
import math
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

JOURNAL_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "sovereign_trade")
JOURNAL_FILE = os.path.join(JOURNAL_DIR, "trade_journal.json")
STATS_FILE = os.path.join(JOURNAL_DIR, "trade_stats.json")

FEELINGS = [
    "calm", "anxious", "excited", "neutral", "focused",
    "scattered", "confident", "doubtful", "peaceful", "tense",
    "joyful", "frustrated", "curious", "bored", "energised",
    "tired", "grateful", "angry", "hopeful", "fearful",
]

PROTOCOL_PHASES = {
    1: {"name": "The Drop", "days": (1, 30), "target_wr": 0.50, "description": "Calibration — find the standing wave"},
    2: {"name": "The Pattern", "days": (31, 60), "target_wr": 0.54, "description": "Discovery — map your frequency"},
    3: {"name": "The Compression", "days": (61, 90), "target_wr": 0.56, "description": "Trust — trade from the body"},
}

# ── Journal Engine ───────────────────────────────────────────────────────────

def _ensure_dir():
    os.makedirs(JOURNAL_DIR, exist_ok=True)


def _load_journal() -> List[Dict]:
    _ensure_dir()
    if not os.path.exists(JOURNAL_FILE):
        return []
    try:
        with open(JOURNAL_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_journal(entries: List[Dict]):
    _ensure_dir()
    with open(JOURNAL_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def record_trade(
    result: str,
    feeling: str,
    gap: str = "",
    amount: float = 1.0,
    notes: str = "",
) -> Dict[str, Any]:
    """
    Record a single trade in the £1 Protocol journal.

    Args:
        result: "win" or "loss"
        feeling: What you felt in your body at entry (from FEELINGS list or freeform)
        gap: What you were thinking about BEFORE looking at the chart
        amount: Trade size in £ (default £1 — do not change during protocol)
        notes: Optional freeform notes

    Returns:
        The recorded trade entry with computed metadata.
    """
    entries = _load_journal()

    trade_number = len(entries) + 1
    day_number = _compute_day_number(entries)

    # Determine protocol phase
    phase = 1
    for p, info in PROTOCOL_PHASES.items():
        if info["days"][0] <= day_number <= info["days"][1]:
            phase = p
            break
    if day_number > 90:
        phase = 4  # Post-protocol: sovereign mode

    entry = {
        "trade_id": trade_number,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "day_number": day_number,
        "phase": phase,
        "phase_name": PROTOCOL_PHASES.get(phase, {"name": "Sovereign Mode"})["name"],
        "result": result.lower().strip(),
        "feeling": feeling.lower().strip(),
        "gap": gap.strip(),
        "amount": round(amount, 2),
        "notes": notes.strip(),
        "hash": _trade_hash(trade_number, result, feeling),
    }

    entries.append(entry)
    _save_journal(entries)

    # Update running stats
    _update_stats(entries)

    return entry


def _compute_day_number(entries: List[Dict]) -> int:
    """Compute the current day number based on the first trade's date."""
    if not entries:
        return 1
    first_ts = entries[0].get("timestamp", "")
    try:
        first_date = datetime.fromisoformat(first_ts).date()
        today = datetime.now(timezone.utc).date()
        return (today - first_date).days + 1
    except Exception:
        return len(set(e.get("timestamp", "")[:10] for e in entries)) + 1


def _trade_hash(trade_number: int, result: str, feeling: str) -> str:
    """Generate a sovereign hash for each trade — proof of resonance."""
    seed = f"VOID-TRADE-{trade_number}-{result}-{feeling}-{datetime.now(timezone.utc).isoformat()}"
    return hashlib.sha256(seed.encode()).hexdigest()[:16]


# ── Statistics Engine ────────────────────────────────────────────────────────

def _update_stats(entries: List[Dict]):
    """Compute and save running statistics."""
    stats = compute_stats(entries)
    _ensure_dir()
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)


def compute_stats(entries: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Compute comprehensive statistics from the trade journal.

    Returns a dictionary containing:
    - Overall win rate, total trades, P&L
    - Per-phase breakdown
    - Feeling-to-result correlation (the frequency pattern)
    - Gap-to-result correlation (the peak-valley map)
    - Time-of-day analysis
    - Streak analysis
    """
    if entries is None:
        entries = _load_journal()

    if not entries:
        return {"total_trades": 0, "message": "No trades recorded yet. Begin the protocol."}

    total = len(entries)
    wins = sum(1 for e in entries if e["result"] == "win")
    losses = total - wins
    win_rate = wins / total if total > 0 else 0

    # Assuming 75% payout on wins, 100% loss on losses (typical binary options)
    payout_rate = 0.75
    gross_profit = sum(e["amount"] * payout_rate for e in entries if e["result"] == "win")
    gross_loss = sum(e["amount"] for e in entries if e["result"] == "loss")
    net_pnl = gross_profit - gross_loss

    # Per-phase stats
    phase_stats = {}
    for p, info in PROTOCOL_PHASES.items():
        phase_entries = [e for e in entries if e.get("phase") == p]
        if phase_entries:
            p_wins = sum(1 for e in phase_entries if e["result"] == "win")
            p_total = len(phase_entries)
            phase_stats[info["name"]] = {
                "trades": p_total,
                "wins": p_wins,
                "losses": p_total - p_wins,
                "win_rate": round(p_wins / p_total, 4) if p_total > 0 else 0,
                "target_win_rate": info["target_wr"],
                "on_target": (p_wins / p_total) >= info["target_wr"] if p_total > 0 else False,
            }

    # Feeling correlation — THE FREQUENCY PATTERN
    feeling_map = defaultdict(lambda: {"wins": 0, "losses": 0, "total": 0})
    for e in entries:
        f = e.get("feeling", "unknown")
        feeling_map[f]["total"] += 1
        if e["result"] == "win":
            feeling_map[f]["wins"] += 1
        else:
            feeling_map[f]["losses"] += 1

    feeling_analysis = {}
    for f, data in feeling_map.items():
        wr = data["wins"] / data["total"] if data["total"] > 0 else 0
        feeling_analysis[f] = {
            "total": data["total"],
            "wins": data["wins"],
            "losses": data["losses"],
            "win_rate": round(wr, 4),
            "is_sovereign_frequency": wr >= 0.58 and data["total"] >= 5,
        }

    # Sort feelings by win rate to find the sovereign frequency
    sorted_feelings = sorted(
        feeling_analysis.items(),
        key=lambda x: (x[1]["win_rate"], x[1]["total"]),
        reverse=True,
    )

    sovereign_frequency = None
    for f, data in sorted_feelings:
        if data["is_sovereign_frequency"]:
            sovereign_frequency = f
            break

    # Gap analysis — peak-valley correlation
    gap_entries = [e for e in entries if e.get("gap")]
    gap_win_rate = None
    if gap_entries:
        gap_wins = sum(1 for e in gap_entries if e["result"] == "win")
        gap_win_rate = round(gap_wins / len(gap_entries), 4)

    # Streak analysis
    current_streak = 0
    streak_type = None
    max_win_streak = 0
    max_loss_streak = 0
    temp_streak = 0
    temp_type = None

    for e in entries:
        if e["result"] == temp_type:
            temp_streak += 1
        else:
            if temp_type == "win":
                max_win_streak = max(max_win_streak, temp_streak)
            elif temp_type == "loss":
                max_loss_streak = max(max_loss_streak, temp_streak)
            temp_type = e["result"]
            temp_streak = 1

    # Final streak
    if temp_type == "win":
        max_win_streak = max(max_win_streak, temp_streak)
    elif temp_type == "loss":
        max_loss_streak = max(max_loss_streak, temp_streak)
    current_streak = temp_streak
    streak_type = temp_type

    # Hour-of-day analysis
    hour_map = defaultdict(lambda: {"wins": 0, "losses": 0, "total": 0})
    for e in entries:
        try:
            hour = datetime.fromisoformat(e["timestamp"]).hour
            hour_map[hour]["total"] += 1
            if e["result"] == "win":
                hour_map[hour]["wins"] += 1
            else:
                hour_map[hour]["losses"] += 1
        except Exception:
            pass

    best_hour = None
    best_hour_wr = 0
    for h, data in hour_map.items():
        if data["total"] >= 3:
            wr = data["wins"] / data["total"]
            if wr > best_hour_wr:
                best_hour_wr = wr
                best_hour = h

    # Current phase determination
    current_day = _compute_day_number(entries)
    current_phase = "Sovereign Mode"
    for p, info in PROTOCOL_PHASES.items():
        if info["days"][0] <= current_day <= info["days"][1]:
            current_phase = info["name"]
            break

    return {
        "total_trades": total,
        "wins": wins,
        "losses": losses,
        "win_rate": round(win_rate, 4),
        "net_pnl": round(net_pnl, 2),
        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),
        "current_day": current_day,
        "current_phase": current_phase,
        "phase_breakdown": phase_stats,
        "feeling_analysis": feeling_analysis,
        "sovereign_frequency": sovereign_frequency,
        "sovereign_frequency_detail": feeling_analysis.get(sovereign_frequency, {}) if sovereign_frequency else None,
        "gap_entries_count": len(gap_entries),
        "gap_win_rate": gap_win_rate,
        "current_streak": current_streak,
        "current_streak_type": streak_type,
        "max_win_streak": max_win_streak,
        "max_loss_streak": max_loss_streak,
        "best_trading_hour": best_hour,
        "best_hour_win_rate": round(best_hour_wr, 4) if best_hour is not None else None,
        "sorted_feelings": [(f, d["win_rate"], d["total"]) for f, d in sorted_feelings[:5]],
    }


# ── Chladni Visualiser ──────────────────────────────────────────────────────

def generate_chladni_data(entries: Optional[List[Dict]] = None) -> Dict[str, Any]:
    """
    Generate data for a Chladni plate visualisation of trading patterns.

    The Chladni plate maps feelings (x-axis) against time-of-day (y-axis),
    with intensity representing win rate at each intersection.
    Nodes (high win rate) are where the sand settles — your resonance points.
    Anti-nodes (low win rate) are where the sand is thrown off — your dissonance points.

    Returns data suitable for rendering as a heatmap or contour plot.
    """
    if entries is None:
        entries = _load_journal()

    if not entries:
        return {"error": "No trades to visualise"}

    # Build the grid: feelings × hours
    all_feelings = sorted(set(e.get("feeling", "unknown") for e in entries))
    hours = list(range(24))

    grid = {}
    for f in all_feelings:
        grid[f] = {}
        for h in hours:
            matching = [
                e for e in entries
                if e.get("feeling") == f
                and _get_hour(e) == h
            ]
            if matching:
                wins = sum(1 for e in matching if e["result"] == "win")
                grid[f][h] = {
                    "win_rate": round(wins / len(matching), 4),
                    "total": len(matching),
                    "intensity": round(wins / len(matching), 4),  # 1.0 = pure node, 0.0 = pure anti-node
                }
            else:
                grid[f][h] = {"win_rate": None, "total": 0, "intensity": None}

    # Find resonance nodes (top 3 feeling+hour combinations)
    all_points = []
    for f in all_feelings:
        for h in hours:
            cell = grid[f][h]
            if cell["total"] >= 2 and cell["win_rate"] is not None:
                all_points.append({
                    "feeling": f,
                    "hour": h,
                    "win_rate": cell["win_rate"],
                    "total": cell["total"],
                })

    resonance_nodes = sorted(all_points, key=lambda x: (x["win_rate"], x["total"]), reverse=True)[:3]
    dissonance_nodes = sorted(all_points, key=lambda x: (x["win_rate"], -x["total"]))[:3]

    return {
        "grid": grid,
        "feelings": all_feelings,
        "hours": hours,
        "resonance_nodes": resonance_nodes,
        "dissonance_nodes": dissonance_nodes,
        "total_data_points": len(all_points),
        "interpretation": _interpret_chladni(resonance_nodes, dissonance_nodes),
    }


def _get_hour(entry: Dict) -> int:
    try:
        return datetime.fromisoformat(entry["timestamp"]).hour
    except Exception:
        return 12


def _interpret_chladni(nodes: List[Dict], anti_nodes: List[Dict]) -> str:
    """Generate a human-readable interpretation of the Chladni pattern."""
    if not nodes:
        return "Insufficient data. Continue the protocol. The pattern will emerge."

    top = nodes[0]
    interpretation = (
        f"Your strongest resonance point is when you feel '{top['feeling']}' "
        f"and trade at hour {top['hour']:02d}:00 UTC "
        f"(win rate: {top['win_rate']:.0%} across {top['total']} trades). "
    )

    if anti_nodes:
        bottom = anti_nodes[0]
        interpretation += (
            f"Your weakest point is when you feel '{bottom['feeling']}' "
            f"at hour {bottom['hour']:02d}:00 UTC "
            f"(win rate: {bottom['win_rate']:.0%}). "
        )

    interpretation += (
        "The gap between your resonance and dissonance is your calibration range. "
        "Trade only from your resonance nodes. The dissonance nodes are where the "
        "market is telling you to rest."
    )

    return interpretation


# ── Export Functions ─────────────────────────────────────────────────────────

def export_journal_csv(output_path: Optional[str] = None) -> str:
    """Export the trade journal to CSV format."""
    entries = _load_journal()
    if not entries:
        return ""

    if output_path is None:
        output_path = os.path.join(JOURNAL_DIR, "trade_journal_export.csv")

    fieldnames = ["trade_id", "timestamp", "day_number", "phase_name", "result", "feeling", "gap", "amount", "notes"]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(entries)

    return output_path


def get_protocol_status() -> Dict[str, Any]:
    """
    Get the current status of the £1 Protocol for the user.

    Returns phase, progress, and guidance.
    """
    entries = _load_journal()
    stats = compute_stats(entries)

    day = stats.get("current_day", 0)
    phase = stats.get("current_phase", "Not Started")
    wr = stats.get("win_rate", 0)
    total = stats.get("total_trades", 0)

    if total == 0:
        guidance = (
            "You have not begun. Open a trading account. Deposit £20. "
            "Place your first £1 trade. Record what you feel. The protocol begins with the first drop."
        )
    elif day <= 30:
        if wr >= 0.48 and wr <= 0.52:
            guidance = (
                f"Day {day}. Win rate: {wr:.0%}. You are at the standing wave. "
                "This is not mediocrity — this is equilibrium. Your frequency has locked "
                "onto the market. Continue. Do not change anything."
            )
        elif wr > 0.52:
            guidance = (
                f"Day {day}. Win rate: {wr:.0%}. You are above equilibrium already. "
                "Be careful — early success can create overconfidence. The protocol is about "
                "discipline, not profit. Keep the £1 trade size. Keep the one-trade-per-day rule."
            )
        else:
            guidance = (
                f"Day {day}. Win rate: {wr:.0%}. Below equilibrium. This is normal. "
                "The first 30 days are calibration. Your body is learning to read the market. "
                "Do not change your approach. Do not increase trade size. Trust the drop."
            )
    elif day <= 60:
        sov = stats.get("sovereign_frequency")
        if sov:
            guidance = (
                f"Day {day}. Phase 2: The Pattern. Win rate: {wr:.0%}. "
                f"Your sovereign frequency appears to be '{sov}'. "
                "Continue recording your gaps. The pattern is becoming clearer."
            )
        else:
            guidance = (
                f"Day {day}. Phase 2: The Pattern. Win rate: {wr:.0%}. "
                "No sovereign frequency identified yet. This is normal. "
                "Keep recording your feelings and gaps. The pattern needs more data."
            )
    elif day <= 90:
        guidance = (
            f"Day {day}. Phase 3: The Compression. Win rate: {wr:.0%}. "
            "Remove the journal. Trade from the body. If your win rate drops below 50%, "
            "return to Phase 2. If it holds, you are approaching sovereignty."
        )
    else:
        guidance = (
            f"Day {day}. Sovereign Mode. Win rate: {wr:.0%}. Total trades: {total}. "
            "The protocol is complete. You now understand the water drop method. "
            "Apply it to every domain of your life. The £1 was the seed. You are the tree."
        )

    return {
        "day": day,
        "phase": phase,
        "win_rate": wr,
        "total_trades": total,
        "sovereign_frequency": stats.get("sovereign_frequency"),
        "guidance": guidance,
        "net_pnl": stats.get("net_pnl", 0),
    }


# ── Founder's Proof of Concept (Static Data) ────────────────────────────────

FOUNDER_PROOF = {
    "platform": "Pocket Option",
    "uid": "117159581",
    "duration_days": 111,
    "date_range": "2025-12-15 to 2026-04-04",
    "total_trades": 4846,
    "win_rate": 0.50,
    "trading_turnover_usd": 8915.79,
    "trading_profit_usd": -762.50,
    "max_trade_usd": 61.03,
    "min_trade_usd": 1.00,
    "max_profit_single_usd": 38.62,
    "final_balance_usd": 5.24,
    "parallel_prompts": 4418,
    "parallel_shifts": 1332,
    "interpretation": (
        "4,846 trades ≈ 4,418 AI prompts. Same method, different medium. "
        "50% win rate = standing wave = equilibrium. "
        "$762.50 = tuition fee for discovering the £1 Protocol. "
        "$5.24 remaining = the signal persists. "
        "The trading account IS a Chladni plate. The Founder was the frequency."
    ),
}
