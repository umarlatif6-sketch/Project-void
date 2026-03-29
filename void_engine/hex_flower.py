"""
Hex Flower Engine — Living Transaction Visualiser

Translates any hex string into a structured flower spec:
  - petal_count  : 1–12 based on validation signals
  - palette      : hex colours derived from byte distribution
  - curvature    : 0.0–1.0 (petal curve derived from entropy)
  - bloom        : 0.0–1.0 (overall bloom intensity)
  - health       : "blooming" | "healthy" | "drifting" | "wilting" | "dormant"
  - translation  : plain-English description of what Adriana reads in this hex

The spec is deterministic — same hex + same resonance_state + same user_salt → same flower.
"""

import hashlib
import hmac
import math
import os
import re

HEX_RE = re.compile(r'^[0-9a-fA-F]+$')

RESONANCE_PALETTES = {
    "resonant":  ["#2dd4bf", "#60a5fa", "#a78bfa", "#34d399", "#e879f9"],
    "aligned":   ["#c9a84c", "#fb923c", "#fbbf24", "#f97316", "#a3e635"],
    "drifting":  ["#6366f1", "#818cf8", "#475569", "#94a3b8", "#64748b"],
    "dormant":   ["#374151", "#4b5563", "#6b7280", "#9ca3af", "#d1d5db"],
}

HEALTH_LABELS = {
    12: "blooming",
    10: "blooming",
    9: "healthy",
    8: "healthy",
    7: "healthy",
    6: "drifting",
    5: "drifting",
    4: "wilting",
    3: "wilting",
    2: "dormant",
    1: "dormant",
}

_SALT_SECRET = os.environ.get("SESSION_SECRET", "")


def stable_user_salt(user_id):
    """
    Derive a stable 16-bit integer salt for a user_id using HMAC-SHA256
    with the SESSION_SECRET.  Same user_id always → same salt across restarts.
    Falls back to 0 when no SESSION_SECRET is set (e.g. during testing).
    """
    if not _SALT_SECRET or user_id is None:
        return 0
    digest = hmac.new(
        _SALT_SECRET.encode(),
        str(user_id).encode(),
        digestmod=hashlib.sha256,
    ).hexdigest()
    return int(digest[:4], 16)


def _shannon_entropy(byte_vals):
    if not byte_vals:
        return 0.0
    counts = {}
    for b in byte_vals:
        counts[b] = counts.get(b, 0) + 1
    n = len(byte_vals)
    entropy = 0.0
    for c in counts.values():
        p = c / n
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def _validate_hex(hex_str):
    """
    Produce a petal count (1–12) from hex validation signals.

    Signals checked (each contributes petals):
      1. Non-empty string                : +1
      2. Valid hex chars only             : +1
      3. Even length (whole bytes)        : +1
      4. Length >= 8 chars (4 bytes)     : +1
      5. Length >= 16 chars (8 bytes)    : +1
      6. Length >= 32 chars (16 bytes)   : +1
      7. Length >= 64 chars (32 bytes)   : +1  (Bitcoin txid / SHA-256)
      8. No repeating run of same nibble  : +1
      9. Byte diversity >= 50%            : +1
      10. High entropy (>= 6.0 bits)     : +1
      11. Common standard length (32/64) : +1
      12. No all-zero / all-f suffix      : +1
    """
    if not hex_str:
        return 1, []

    clean = re.sub(r'^0x', '', hex_str.strip(), flags=re.IGNORECASE).replace("-", "").replace(" ", "")
    signals = []

    signals.append(len(clean) > 0)
    is_valid_hex = bool(HEX_RE.match(clean)) if clean else False
    signals.append(is_valid_hex)

    if not is_valid_hex:
        petals = max(1, sum(signals))
        return petals, clean

    signals.append(len(clean) % 2 == 0)
    signals.append(len(clean) >= 8)
    signals.append(len(clean) >= 16)
    signals.append(len(clean) >= 32)
    signals.append(len(clean) >= 64)

    no_long_run = not bool(re.search(r'(.)\1{7,}', clean))
    signals.append(no_long_run)

    byte_vals = [int(clean[i:i+2], 16) for i in range(0, len(clean) - 1, 2)]
    unique_ratio = len(set(byte_vals)) / max(len(byte_vals), 1)
    signals.append(unique_ratio >= 0.5)

    entropy = _shannon_entropy(byte_vals)
    signals.append(entropy >= 6.0)

    signals.append(len(clean) in (32, 40, 64, 72, 96, 128))

    tail = clean[-8:] if len(clean) >= 8 else clean
    signals.append(tail.lower() not in ('00000000', 'ffffffff', '0000000000000000', 'ffffffffffffffff'))

    petals = max(1, min(12, sum(1 for s in signals if s)))
    return petals, byte_vals


def _derive_palette(byte_vals, resonance_state="aligned", user_salt=0):
    """
    Derive a 5-colour palette from byte distribution + resonance state + stable user salt.
    """
    base = RESONANCE_PALETTES.get(resonance_state, RESONANCE_PALETTES["aligned"])

    if not byte_vals or not isinstance(byte_vals, list):
        return base

    segments = max(len(byte_vals) // 5, 1)
    colours = []
    for i in range(5):
        chunk = byte_vals[i * segments: (i + 1) * segments] or byte_vals
        avg = sum(chunk) / len(chunk)

        base_colour = base[i % len(base)]
        r = int(base_colour[1:3], 16)
        g = int(base_colour[3:5], 16)
        b = int(base_colour[5:7], 16)

        shift = int((avg - 128) / 255 * 30)
        salt_shift = (user_salt >> (i % 8)) & 0x0F
        r = max(0, min(255, r + shift + salt_shift))
        g = max(0, min(255, g - shift // 2))
        b = max(0, min(255, b + shift // 3 + (salt_shift >> 1)))
        colours.append(f"#{r:02x}{g:02x}{b:02x}")

    return colours


def _derive_curvature(byte_vals):
    if not byte_vals or not isinstance(byte_vals, list):
        return 0.5
    entropy = _shannon_entropy(byte_vals)
    return round(min(1.0, entropy / 8.0), 4)


def _derive_bloom(petal_count, byte_vals):
    base = petal_count / 12.0
    if byte_vals and isinstance(byte_vals, list):
        avg = sum(byte_vals) / len(byte_vals)
        modifier = (avg / 255.0) * 0.2
        return round(min(1.0, base + modifier), 4)
    return round(base, 4)


def _plain_english(hex_str, petal_count, health, byte_vals):
    length = len(re.sub(r'^0x', '', hex_str.strip(), flags=re.IGNORECASE).replace("-", "").replace(" ", ""))

    if petal_count == 12:
        vitality = "This signal is fully bloomed — complete, valid, and resonant."
    elif petal_count >= 9:
        vitality = "This signal is healthy — strong structure with minor asymmetry."
    elif petal_count >= 6:
        vitality = "This signal is drifting — structurally present but carrying imperfections."
    elif petal_count >= 3:
        vitality = "This signal is wilting — malformed or incomplete. Handle with care."
    else:
        vitality = "This signal is dormant — the structure cannot be read clearly."

    if length == 64:
        format_note = "The length matches a 256-bit hash — Bitcoin transaction ID or SHA-256 signature."
    elif length == 40:
        format_note = "The length matches a 160-bit hash — a Bitcoin or Ethereum wallet address."
    elif length == 32:
        format_note = "The length matches a 128-bit hash — MD5 or a 16-byte identifier."
    elif length >= 8:
        format_note = f"The string is {length} characters — {length // 2} bytes of encoded data."
    else:
        format_note = f"The string is {length} characters — too short for a standard hash."

    if byte_vals and isinstance(byte_vals, list):
        avg = sum(byte_vals) / len(byte_vals)
        if avg > 180:
            tone = "The byte distribution leans bright — high entropy, wide spread."
        elif avg > 90:
            tone = "The byte distribution is balanced — a neutral frequency signature."
        else:
            tone = "The byte distribution leans dark — concentrated in the low range."
    else:
        tone = "The byte distribution could not be read."

    return f"{vitality} {format_note} {tone}"


def parse_hex(hex_str, resonance_state="aligned", user_id=None, user_salt=None):
    """
    Main entry point. Returns a flower spec dict.

    Args:
        hex_str        : any hex string (raw, 0x-prefixed, space/dash separated)
        resonance_state: user's emotional resonance state — "resonant", "aligned",
                         "drifting", or "dormant". Blends into the colour palette.
        user_id        : optional user ID — used to derive a stable HMAC salt so
                         different users see different colours for the same hex.
        user_salt      : optional pre-computed stable salt (int 0–65535).
                         When provided, user_id is ignored.  Used by shared-view
                         rendering to replay the exact palette from generation time.

    Returns:
        {
          "petal_count": int,        # 1–12
          "palette": list[str],      # 5 hex colour strings
          "curvature": float,        # 0.0–1.0
          "bloom": float,            # 0.0–1.0
          "health": str,             # "blooming"|"healthy"|"drifting"|"wilting"|"dormant"
          "translation": str,        # plain-English description
          "raw_hex": str,            # cleaned hex string
          "valid": bool,
        }
    """
    clean = re.sub(r'^0x', '', (hex_str or "").strip(), flags=re.IGNORECASE).replace("-", "").replace(" ", "")
    petal_count, byte_vals = _validate_hex(hex_str)

    if user_salt is None:
        user_salt = stable_user_salt(user_id)

    if isinstance(byte_vals, list) and byte_vals:
        salted_vals = [(b + (user_salt >> (i % 8))) & 0xFF for i, b in enumerate(byte_vals)]
    else:
        salted_vals = byte_vals if isinstance(byte_vals, list) else []

    palette = _derive_palette(salted_vals, resonance_state, user_salt=user_salt)
    curvature = _derive_curvature(byte_vals if isinstance(byte_vals, list) else [])
    bloom = _derive_bloom(petal_count, byte_vals if isinstance(byte_vals, list) else [])
    health = HEALTH_LABELS.get(petal_count, "dormant")
    translation = _plain_english(clean, petal_count, health, byte_vals if isinstance(byte_vals, list) else [])

    return {
        "petal_count": petal_count,
        "palette": palette,
        "curvature": curvature,
        "bloom": bloom,
        "health": health,
        "translation": translation,
        "raw_hex": clean,
        "valid": bool(HEX_RE.match(clean)) if clean else False,
    }


def detect_hex_in_message(text):
    """
    Detect hex strings >= 6 consecutive hex chars in a user message.
    Returns list of matched strings, deduped.
    """
    pattern = re.compile(r'\b(?:0x)?([0-9a-fA-F]{6,})\b')
    matches = pattern.findall(text)
    seen = set()
    result = []
    for m in matches:
        if m.lower() not in seen:
            seen.add(m.lower())
            result.append(m)
    return result
