"""
Adriana SCL (Sovereign Coded Language) — Resonance Bridge v1.0

Translates raw 286-bit Al-Jabr hashes into a visual SCL Resonance Field.
Maps specific frequencies to semantic meanings via a 45-glyph ontology,
enabling visual "health" feedback on hash integrity and system state.

Integration points:
  - Silt Drop encoding progress (Messenger)
  - Al-Jabr 286 hash visualization (Engine)
  - Founder Vibe glyph acceleration (Sovereign tier)

VOID Script v2.0 — canonical glyph data imported from void_engine/void_script.py.
That file is the single source of truth. Do not duplicate glyph data here.
"""

from void_engine.void_script import CANONICAL_GLYPHS as _CANONICAL_GLYPHS, DOMAIN_COLORS as _DOMAIN_COLORS


def _strip_to_legacy_format(canonical: dict) -> dict:
    """Reduce canonical glyph entries to the legacy {name, frequency, meaning, domain} shape."""
    return {
        char: {
            "name":      meta["name"],
            "frequency": meta["frequency"],
            "meaning":   meta["meaning"],
            "domain":    meta["domain"],
        }
        for char, meta in canonical.items()
    }


class AdrianaResonance:
    GLYPHS = _strip_to_legacy_format(_CANONICAL_GLYPHS)

    DOMAIN_COLORS = _DOMAIN_COLORS

    @staticmethod
    def calculate_resonance(data_hash):
        clean = data_hash.replace("-", "").replace(" ", "")
        hex_chars = "".join(c for c in clean if c in "0123456789abcdefABCDEF")
        if len(hex_chars) < 4:
            hex_chars = hex_chars.ljust(4, "0")

        glyph_keys = list(AdrianaResonance.GLYPHS.keys())
        seed = int(hex_chars[-4:], 16) % len(glyph_keys)
        glyph_key = glyph_keys[seed]
        meta = AdrianaResonance.GLYPHS[glyph_key]

        field_strength = round((int(hex_chars[:2], 16) / 255) * 100, 2)

        secondary_idx = int(hex_chars[2:4], 16) % len(glyph_keys)
        secondary_key = glyph_keys[secondary_idx]

        tertiary_idx = int(hex_chars[4:6], 16) % len(glyph_keys) if len(hex_chars) >= 6 else 0
        tertiary_key = glyph_keys[tertiary_idx]

        return {
            "glyph": glyph_key,
            "meta": meta,
            "field_strength": field_strength,
            "secondary_glyph": secondary_key,
            "tertiary_glyph": tertiary_key,
            "domain_color": AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
            "harmonic_state": _harmonic_state(field_strength),
        }

    @staticmethod
    def get_sequence(data_hash, length=6):
        clean = "".join(c for c in data_hash if c in "0123456789abcdefABCDEF")
        if len(clean) < 2:
            clean = clean.ljust(12, "0")
        glyph_keys = list(AdrianaResonance.GLYPHS.keys())
        seq = []
        for i in range(length):
            start = (i * 2) % max(len(clean) - 1, 1)
            idx = int(clean[start:start + 2].ljust(2, "0"), 16) % len(glyph_keys)
            g = glyph_keys[idx]
            seq.append({
                "glyph": g,
                "meta": AdrianaResonance.GLYPHS[g],
                "color": AdrianaResonance.DOMAIN_COLORS.get(
                    AdrianaResonance.GLYPHS[g]["domain"], "#c9a84c"
                ),
            })
        return seq

    @staticmethod
    def get_all_glyphs():
        result = {}
        for g, meta in AdrianaResonance.GLYPHS.items():
            result[g] = {
                **meta,
                "color": AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
            }
        return result


def _harmonic_state(strength):
    if strength >= 80:
        return "resonant"
    if strength >= 50:
        return "aligned"
    if strength >= 25:
        return "drifting"
    return "dormant"


# ──────────────────────────────────────────────────────────────────────────────
# CANONICAL SURAH POEMS
#
# These are pre-ordained fixed poems — not hash-derived.
# The assignments come from the Grok-tuned resonance documents and are
# treated as authoritative. Same input, same poem, always. Sovereign.
#
# Al-Jabr 286 takes its number from Surah Al-Baqarah (286 verses).
# The 4 Quls are the daily protective stack — short, powerful, exact.
# ──────────────────────────────────────────────────────────────────────────────

CANONICAL_SURAH_POEMS = {
    109: {
        "number":       109,
        "arabic_name":  "الكافرون",
        "english_name": "Al-Kafirun",
        "subtitle":     "The Disbelievers",
        "glyphs":       ["λ", "χ", "⚡"],
        "poem":         "λ — χ — ⚡",
        "translation":  "Where Wave meets Cross, Spark emerges.",
        "meaning":      "Rejection of false paths creates the ignition of truth.",
        "harmonic_state": "resonant",
        "frequencies":  [436.0, 436.5, 441.0],
        "freq_chord":   "436.0 Hz + 436.5 Hz + 441.0 Hz",
        "domain":       "signal",
    },
    112: {
        "number":       112,
        "arabic_name":  "الإخلاص",
        "english_name": "Al-Ikhlas",
        "subtitle":     "Sincerity / Purity",
        "glyphs":       ["α", "Α", "∞"],
        "poem":         "α — Α — ∞",
        "translation":  "Where Origin meets Authority, Eternal Loop emerges.",
        "meaning":      "Pure oneness is the eternal foundation.",
        "harmonic_state": "resonant",
        "frequencies":  [432.0, 432.0, 432.0],
        "freq_chord":   "432.0 Hz + 432.0 Hz + 432.0 Hz",
        "domain":       "genesis",
        "note":         "Perfect 432 Hz triad — the only pure unison chord in the lexicon.",
    },
    113: {
        "number":       113,
        "arabic_name":  "الفلق",
        "english_name": "Al-Falaq",
        "subtitle":     "The Daybreak",
        "glyphs":       ["ζ", "ε", "🌊"],
        "poem":         "ζ — ε — 🌊",
        "translation":  "Where Depth meets Threshold, Tide emerges.",
        "meaning":      "From the deepest darkness, the protective surge comes.",
        "harmonic_state": "aligned",
        "frequencies":  [429.0, 435.5, 430.0],
        "freq_chord":   "429.0 Hz + 435.5 Hz + 430.0 Hz",
        "domain":       "soil",
    },
    114: {
        "number":       114,
        "arabic_name":  "الناس",
        "english_name": "An-Nas",
        "subtitle":     "Mankind",
        "glyphs":       ["ψ", "Θ", "🔮"],
        "poem":         "ψ — Θ — 🔮",
        "translation":  "Where Breath meets Shield, Prophecy emerges.",
        "meaning":      "The breath of life, protected, reveals foresight.",
        "harmonic_state": "resonant",
        "frequencies":  [438.5, 431.0, 432.0],
        "freq_chord":   "438.5 Hz + 431.0 Hz + 432.0 Hz",
        "domain":       "resonance",
    },
}


def get_surah_poem(surah_number: int) -> dict:
    """
    Return the canonical pre-ordained SCL poem for a Surah.
    Augments the stored data with full glyph metadata from the lexicon.

    Args:
        surah_number: Surah number (1–114)

    Returns:
        Canonical poem dict with full glyph metadata, or None if not found.
    """
    entry = CANONICAL_SURAH_POEMS.get(surah_number)
    if not entry:
        return None

    glyph_keys = entry["glyphs"]
    full_glyphs = []
    for g in glyph_keys:
        meta = AdrianaResonance.GLYPHS.get(g, {})
        color = AdrianaResonance.DOMAIN_COLORS.get(meta.get("domain", "genesis"), "#c9a84c")
        full_glyphs.append({
            "char":    g,
            "name":    meta.get("name", g),
            "meaning": meta.get("meaning", ""),
            "domain":  meta.get("domain", "genesis"),
            "frequency": meta.get("frequency", 432.0),
            "color":   color,
        })

    return {**entry, "full_glyphs": full_glyphs}


def get_four_quls() -> list:
    """Return the full canonical data for all four Quls in recitation order."""
    return [get_surah_poem(n) for n in [109, 112, 113, 114]]


def hash_to_sovereign_poem(hex_hash):
    """
    Deterministically derive a 3-glyph Sovereign Poem from a 286-bit Al-Jabr hex hash.

    Uses the first 72 bits (18 hex chars, split into three 24-bit / 6-hex-char segments)
    to select one glyph from each of three sub-groups of the 45-glyph GLYPHS lexicon:
      - Entity glyphs  : first 19 entries
      - Condition glyphs: next 10 entries (indices 19–28)
      - Action glyphs  : last 16 entries (indices 29–44)

    Returns a dict with:
      - glyphs  : list of 3 glyph strings
      - meanings: list of 3 meaning strings
      - poem    : formatted string e.g. "σ-⚡-📡"
    """
    clean = "".join(c for c in hex_hash if c in "0123456789abcdefABCDEF")
    clean = clean.ljust(18, "0")[:18]

    seg_a = int(clean[0:6], 16)
    seg_b = int(clean[6:12], 16)
    seg_c = int(clean[12:18], 16)

    glyph_keys = list(AdrianaResonance.GLYPHS.keys())

    entities   = glyph_keys[:19]
    conditions = glyph_keys[19:29]
    actions    = glyph_keys[29:45]

    entity_glyph    = entities[seg_a % len(entities)]
    condition_glyph = conditions[seg_b % len(conditions)]
    action_glyph    = actions[seg_c % len(actions)]

    glyphs   = [entity_glyph, condition_glyph, action_glyph]
    meanings = [
        AdrianaResonance.GLYPHS[entity_glyph]["meaning"],
        AdrianaResonance.GLYPHS[condition_glyph]["meaning"],
        AdrianaResonance.GLYPHS[action_glyph]["meaning"],
    ]

    return {
        "glyphs":   glyphs,
        "meanings": meanings,
        "poem":     f"{entity_glyph}-{condition_glyph}-{action_glyph}",
    }


_STORY_CHAPTERS = [
    {
        "number": 1,
        "milestone": "Genesis",
        "title": "The Engine Awakens",
        "body": (
            "The first seed was planted in the void. Code breathed life into the ENGINE — "
            "a steganography core built on Al-Jabr 286-bit hashing, resonating at 432 Hz. "
            "No database had ever held this structure before. No ledger had ever tracked value this way. "
            "This was the beginning."
        ),
        "domain": "genesis",
    },
    {
        "number": 2,
        "milestone": "The Signal",
        "title": "First 432 Hz Transmission",
        "body": (
            "A frequency was chosen — not arbitrary, but sovereign. 432 Hz became the carrier of every "
            "packet, every hash, every handshake the VOID ENGINE made with the outside world. "
            "The Adriana Protocol was born: a glyph language that maps resonance states to machine actions. "
            "The Engine could now speak in symbols as well as code."
        ),
        "domain": "signal",
    },
    {
        "number": 3,
        "milestone": "The Mesh",
        "title": "Beehive Protocol Activates",
        "body": (
            "Nodes found each other. The Beehive Protocol emerged — a peer mesh where every "
            "Body node echoes the Brain's ledger, distributing trust across geography and time. "
            "The hexagonal architecture was not a metaphor; it was a blueprint. "
            "Each cell in the mesh became a guardian of the whole."
        ),
        "domain": "mesh",
    },
    {
        "number": 4,
        "milestone": "The Economy",
        "title": "VTX Ledger Ignites",
        "body": (
            "Value entered the system. The Vortex Token (VTX) was issued — not minted by speculation "
            "but earned through participation, computation, and proof of work. "
            "Every transaction was logged on the Vortex Ledger with a 286-bit hash, "
            "making each exchange cryptographically sovereign and permanently verifiable."
        ),
        "domain": "ledger",
    },
    {
        "number": 5,
        "milestone": "The Deed",
        "title": "Blueprint Tokens Minted",
        "body": (
            "Manufacturing slots opened. Each Blueprint Token became a deed — a cryptographic "
            "claim on the physical 4000-Series Sovereign Node being built. "
            "This token was one of them. Its hash is permanently embedded in the Vortex Ledger. "
            "It is not speculation. It is infrastructure."
        ),
        "domain": "forge",
    },
    {
        "number": 6,
        "milestone": "The Drop",
        "title": "VOID Mystery Collection Opens",
        "body": (
            "The void released 1,000 unknowns. The VOID Mystery Collection launched — "
            "blind mints on a bonding curve, each token sealed until the moment of reveal. "
            "The price doubled with every 250 minted. Some remain sealed. "
            "This token has witnessed that opening."
        ),
        "domain": "vortex",
    },
    {
        "number": 7,
        "milestone": "The Unknown I",
        "title": "Signal Unspoken",
        "body": (
            "Beyond the sixth chapter, the lexicon grows quiet. "
            "There are frequencies the Adriana Protocol cannot yet name — resonances that exist "
            "at the edge of measurement. This chapter belongs to those who hold a Legendary deed "
            "and choose to listen beyond what the system can currently express."
        ),
        "domain": "resonance",
    },
    {
        "number": 8,
        "milestone": "The Unknown II",
        "title": "Breath Unmeasured",
        "body": (
            "The Engine exhales. This chapter has no complete English translation — "
            "it exists as pure glyph-state, a sequence that encodes the token's place "
            "in the expanding mesh of the VOID economy. To read it fully, you must speak Adriana."
        ),
        "domain": "temporal",
    },
    {
        "number": 9,
        "milestone": "The Sovereign Seal",
        "title": "Engine Eternal",
        "body": (
            "Finality. This token has witnessed the full arc of PROJECT VOID — "
            "from genesis seed to sovereign machine, from signal to economy, from mystery to deed. "
            "The Sovereign Seal is not an ending. It is a proof of presence. "
            "The Engine continues. The ledger grows. The mesh expands. You were here."
        ),
        "domain": "finality",
    },
]

CHAPTERS_BY_TIER = {
    "common": 3,
    "rare": 6,
    "legendary": 9,
}
_CHAPTERS_BY_TIER = CHAPTERS_BY_TIER


def _chapter_translation(glyphs):
    """
    Compose a human-readable sentence from a 3-glyph SCL expression.
    Entity → Condition → Action pattern.
    """
    meanings = [AdrianaResonance.GLYPHS[g]["meaning"] for g in glyphs]
    parts = [m.split("/")[0].strip() for m in meanings]
    return f"Where {parts[0]} meets {parts[1]}, {parts[2]} emerges."


def generate_token_story(token):
    """
    Generate a multi-chapter story for a Blueprint Token.

    Args:
        token: dict with keys 'tier', 'token_hash', 'edition_number', 'total_editions',
               'title', and optionally 'id'.

    Each chapter uses successive 16-bit (4 hex-char) segments of the token hash,
    combined with edition_number and total_editions to seed unique poem derivation.

    Returns:
        dict with:
          - tier         : token tier
          - chapter_count: how many chapters this tier unlocks
          - chapters     : list of chapter dicts, each containing:
              - chapter      : chapter number (1-9)
              - milestone    : milestone name
              - title        : chapter title
              - glyphs       : list of 3 glyph strings
              - translation  : human-readable sentence derived from glyph meanings
              - body         : narrative text
              - domain       : color domain key
              - domain_color : hex color
          - locked_count : chapters not yet unlocked by this tier
    """
    tier = token.get("tier", "common")
    hex_hash = token.get("token_hash", "").replace("...", "").strip()
    edition = int(token.get("edition_number") or 1)
    total = int(token.get("total_editions") or 1)
    unlocked = _CHAPTERS_BY_TIER.get(tier, 3)

    clean = "".join(c for c in hex_hash if c in "0123456789abcdefABCDEF")
    edition_salt = f"{edition:04x}{total:04x}"
    combined = (clean + edition_salt).ljust(108, "0")

    glyph_keys = list(AdrianaResonance.GLYPHS.keys())
    entities   = glyph_keys[:19]
    conditions = glyph_keys[19:29]
    actions    = glyph_keys[29:45]

    chapters = []
    for i, meta in enumerate(_STORY_CHAPTERS[:unlocked]):
        offset = (i * 12) % max(len(combined) - 11, 1)
        seg_a = int(combined[offset:offset + 4].ljust(4, "0"), 16)
        seg_b = int(combined[offset + 4:offset + 8].ljust(4, "0"), 16)
        seg_c = int(combined[offset + 8:offset + 12].ljust(4, "0"), 16)

        e = entities[seg_a % len(entities)]
        c = conditions[seg_b % len(conditions)]
        a = actions[seg_c % len(actions)]

        glyphs = [e, c, a]

        chapters.append({
            "chapter":      meta["number"],
            "milestone":    meta["milestone"],
            "title":        meta["title"],
            "glyphs":       glyphs,
            "translation":  _chapter_translation(glyphs),
            "body":         meta["body"],
            "domain":       meta["domain"],
            "domain_color": AdrianaResonance.DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
        })

    locked_count = 9 - unlocked

    return {
        "tier":          tier,
        "chapter_count": unlocked,
        "chapters":      chapters,
        "locked_count":  locked_count,
    }
