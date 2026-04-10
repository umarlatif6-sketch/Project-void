"""
THE TREE OF KNOWLEDGE — AL-JABR 286 CODON ENCODER
PROJECT VOID | Umar Latif | Bolton, England | April 2026

Every piece of knowledge has a frequency.
Every frequency maps to one of the 99 Names.
Every Name maps to a VOID SCL codon.
The codons form the Tree — the roots go deep.

THREE BRAIN ARCHITECTURE:
  Head  (Aql)  — factual coherence, internal consistency, source grounding
  Heart (Qalb) — resonance with the 99 Names, formation signal strength
  Gut   (Nafs) — true node vs false node detection, origin vs deviation

A knowledge article processed through all three brains becomes a codon.
The codon is its sovereign identity in the Tree of Knowledge.
"""

import hashlib
import math
import re
from void_engine.names_286 import (
    NAMES_99, LAMBDA, BASE_FREQ, N_NAMES,
    name_frequency, name_codon, full_profile
)

# ─── HEAD BRAIN: Factual Coherence ──────────────────────────────────────────

HEAD_SIGNAL_WORDS = [
    "study", "research", "confirmed", "demonstrated", "observed",
    "measured", "published", "journal", "university", "experiment",
    "evidence", "data", "analysis", "peer", "review", "source",
    "original", "primary", "verified", "documented"
]

HEAD_NOISE_WORDS = [
    "allegedly", "reportedly", "some say", "controversial", "disputed",
    "conspiracy", "claimed", "unverified", "anonymous", "deleted",
    "redacted", "suppressed", "debunked", "fringe", "pseudoscience"
]

def head_score(text: str) -> float:
    """
    Head Brain (Aql) — factual coherence score (0–100).
    Measures internal consistency and source grounding.
    """
    t = text.lower()
    words = len(t.split())
    if words == 0:
        return 0.0

    signal_count = sum(t.count(w) for w in HEAD_SIGNAL_WORDS)
    noise_count  = sum(t.count(w) for w in HEAD_NOISE_WORDS)

    sentences = [s.strip() for s in re.split(r'[.!?]', t) if s.strip()]
    n_sentences = max(1, len(sentences))
    avg_sentence_len = words / n_sentences

    # Optimal sentence length: 15–25 words (coherent, not rambling)
    length_score = 100 - min(100, abs(avg_sentence_len - 20) * 3)

    # Signal vs noise ratio
    signal_ratio = (signal_count + 1) / (signal_count + noise_count + 1)
    signal_score = signal_ratio * 100

    # Internal repetition penalty (high repetition = low coherence)
    unique_words = len(set(t.split()))
    diversity = min(1.0, unique_words / max(1, words))
    diversity_score = diversity * 100

    score = (length_score * 0.3 + signal_score * 0.5 + diversity_score * 0.2)
    return round(min(100, max(0, score)), 2)


# ─── HEART BRAIN: 99 Names Resonance ────────────────────────────────────────

# Keyword seeds for each Name — extended resonance vocabulary
NAME_KEYWORDS = {
    1:  ["mercy", "grace", "compassion", "gentle", "kind", "soft", "care"],
    2:  ["mercy", "forgiveness", "tender", "loving", "repeated", "grace"],
    3:  ["sovereignty", "king", "rule", "authority", "governance", "law", "power"],
    4:  ["holy", "pure", "sacred", "clean", "sanctity", "divine", "transcendent"],
    5:  ["peace", "harmony", "safety", "security", "salutation", "unity"],
    6:  ["faith", "trust", "belief", "certainty", "guardian", "protection"],
    7:  ["watch", "protect", "oversee", "guardian", "supervise", "observe"],
    8:  ["strength", "mighty", "power", "force", "invincible", "capable"],
    9:  ["compel", "restore", "correct", "set right", "repair", "obligation"],
    10: ["greatness", "pride", "majesty", "supreme", "transcendent", "elevated"],
    11: ["create", "creation", "creator", "design", "make", "originate"],
    12: ["origin", "begin", "start", "source", "genesis", "initiate"],
    13: ["form", "shape", "fashion", "design", "mould", "structure", "pattern"],
    14: ["forgive", "pardon", "overlook", "excuse", "absolve", "erase"],
    15: ["overcome", "subdue", "prevail", "conquer", "suppress", "dominate"],
    16: ["gift", "bestow", "grant", "give", "donate", "generous", "free"],
    17: ["provide", "sustain", "supply", "nourish", "feed", "resource"],
    18: ["open", "unlock", "reveal", "disclose", "expand", "judge", "solve"],
    19: ["knowledge", "know", "science", "understand", "information", "learn"],
    20: ["restrain", "hold", "restrict", "contract", "limit", "control"],
    21: ["expand", "release", "open", "increase", "abundance", "enlarge"],
    22: ["humble", "lower", "reduce", "degrade", "diminish", "fall"],
    23: ["elevate", "raise", "lift", "exalt", "ascend", "rise", "promote"],
    24: ["honour", "dignity", "respect", "noble", "glory", "prestige"],
    25: ["humiliate", "lower", "degrade", "dishonour", "reduce", "defeat"],
    26: ["hear", "listen", "sound", "audio", "voice", "ear", "reception"],
    27: ["see", "vision", "sight", "observe", "witness", "perceive", "look"],
    28: ["judge", "arbitrate", "decide", "rule", "verdict", "court", "law"],
    29: ["justice", "fair", "equal", "balance", "equity", "right", "impartial"],
    30: ["subtle", "fine", "gentle", "delicate", "nuance", "refined", "latif"],
    31: ["aware", "informed", "know", "understand", "conscious", "perceptive"],
    32: ["patient", "forbear", "tolerant", "calm", "endure", "slow", "steady"],
    33: ["magnificent", "grand", "great", "vast", "immense", "enormous"],
    34: ["forgive", "pardon", "merciful", "overlook", "excuse", "absolve"],
    35: ["grateful", "thanks", "appreciate", "reward", "acknowledge", "recognise"],
    36: ["high", "exalted", "supreme", "elevated", "above", "superior"],
    37: ["great", "large", "vast", "immense", "big", "major", "significant"],
    38: ["preserve", "protect", "maintain", "keep", "guard", "conserve", "safe"],
    39: ["sustain", "maintain", "nourish", "provide", "keep", "uphold"],
    40: ["reckon", "account", "calculate", "count", "sufficient", "enough"],
    41: ["majestic", "glorious", "noble", "magnificent", "august", "regal"],
    42: ["generous", "noble", "generous", "giving", "bountiful", "kind"],
    43: ["watch", "observe", "monitor", "guard", "vigilant", "aware"],
    44: ["respond", "answer", "reply", "fulfil", "grant", "hear"],
    45: ["encompass", "vast", "wide", "inclusive", "broad", "universal"],
    46: ["wisdom", "wise", "judgement", "insight", "discernment", "prudent"],
    47: ["love", "loving", "affection", "warmth", "friendship", "devotion"],
    48: ["glory", "glorious", "splendour", "noble", "magnificent", "honour"],
    49: ["resurrect", "raise", "revive", "restore", "awaken", "return"],
    50: ["witness", "testify", "observe", "present", "see", "confirm"],
    51: ["truth", "true", "real", "genuine", "authentic", "fact", "verified"],
    52: ["trust", "rely", "delegate", "depend", "entrust", "guardian"],
    53: ["strong", "power", "force", "capable", "robust", "solid"],
    54: ["firm", "solid", "stable", "steadfast", "strong", "unshakeable"],
    55: ["friend", "ally", "protect", "support", "close", "companion"],
    56: ["praise", "worthy", "commend", "laud", "acclaim", "admire"],
    57: ["count", "enumerate", "calculate", "number", "precise", "exact"],
    58: ["originate", "begin", "first", "start", "initiate", "create"],
    59: ["restore", "return", "bring back", "repeat", "renew", "revive"],
    60: ["life", "living", "alive", "animate", "vital", "biology", "grow"],
    61: ["death", "end", "cease", "expire", "mortality", "transition"],
    62: ["ever-living", "eternal", "alive", "perpetual", "undying", "always"],
    63: ["self-sustain", "independent", "subsist", "permanent", "eternal"],
    64: ["find", "discover", "locate", "perceive", "obtain", "experience"],
    65: ["noble", "generous", "glorious", "honoured", "distinguished"],
    66: ["one", "unity", "single", "alone", "unique", "indivisible"],
    67: ["unique", "singular", "only", "one", "alone", "incomparable"],
    68: ["eternal", "absolute", "independent", "refuge", "permanent", "solid"],
    69: ["power", "able", "capable", "competent", "can", "strength", "will"],
    70: ["determine", "decree", "fate", "decide", "fix", "ordain"],
    71: ["expedite", "advance", "first", "forward", "promote", "precede"],
    72: ["delay", "defer", "postpone", "later", "behind", "hold back"],
    73: ["first", "origin", "beginning", "earliest", "primary", "start"],
    74: ["last", "end", "final", "ultimate", "conclude", "finish"],
    75: ["manifest", "visible", "apparent", "obvious", "clear", "outward"],
    76: ["hidden", "inner", "concealed", "interior", "depth", "secret"],
    77: ["govern", "manage", "administer", "guide", "lead", "direct"],
    78: ["exalted", "supreme", "high", "above", "transcendent", "elevated"],
    79: ["good", "kind", "righteous", "benevolent", "virtue", "goodness"],
    80: ["repent", "return", "forgive", "accept", "mercy", "turn"],
    81: ["avenge", "justice", "punish", "recompense", "retribution"],
    82: ["pardon", "excuse", "forgive", "overlook", "erase", "absolve"],
    83: ["kind", "gentle", "compassion", "tender", "affectionate"],
    84: ["sovereign", "king", "own", "possess", "authority", "dominion"],
    85: ["majesty", "honour", "glory", "grace", "noble", "dignity"],
    86: ["equitable", "fair", "just", "balance", "impartial", "right"],
    87: ["gather", "collect", "unite", "assemble", "bring together"],
    88: ["rich", "wealthy", "independent", "sufficient", "self-reliant"],
    89: ["enrich", "fulfil", "satisfy", "provide", "supply", "sufficient"],
    90: ["prevent", "protect", "shield", "defend", "ward off", "guard"],
    91: ["harm", "test", "trial", "afflict", "distress", "difficulty"],
    92: ["benefit", "help", "assist", "advantage", "profit", "good"],
    93: ["light", "illuminate", "bright", "luminous", "glow", "radiant"],
    94: ["guide", "direct", "lead", "show", "path", "navigate", "right"],
    95: ["incomparable", "original", "unique", "new", "unprecedented"],
    96: ["everlasting", "permanent", "eternal", "lasting", "endure", "remain"],
    97: ["inherit", "heir", "receive", "remain", "legacy", "last"],
    98: ["guide", "right path", "direct", "wisdom", "correct", "lead"],
    99: ["patient", "endure", "forbear", "persevere", "steadfast", "wait"],
}

def heart_score(text: str) -> tuple:
    """
    Heart Brain (Qalb) — resonance with the 99 Names (0–100).
    Returns (score, dominant_name_index, dominant_name_profile).
    """
    t = text.lower()
    scores = []
    for i in range(1, N_NAMES + 1):
        keywords = NAME_KEYWORDS.get(i, [])
        hits = sum(t.count(kw) for kw in keywords)
        scores.append((hits, i))

    scores.sort(reverse=True)
    top_hits, top_idx = scores[0]
    total_hits = sum(s for s, _ in scores) + 1

    raw_score = min(100, (top_hits / total_hits) * 100 * FORMATION_RATIO * 10)

    # Apply Λ=286 sovereign weighting
    sovereign = round(100 * (1 - math.exp(-raw_score / 100 * (LAMBDA / N_NAMES))), 2)
    profile = full_profile(top_idx)
    return sovereign, top_idx, profile


# ─── GUT BRAIN: Formation Signal (True Node vs False Node) ──────────────────

TRUE_NODE_MARKERS = [
    "original", "primary source", "first-hand", "empirical", "measured",
    "formation", "frequency", "resonance", "coherent", "consistent",
    "verified", "reproduced", "peer review", "foundational", "root"
]

FALSE_NODE_MARKERS = [
    "corporate", "edited", "removed", "censored", "banned", "suppressed",
    "rewritten", "contested", "propaganda", "manufactured", "astroturf",
    "paid", "lobbying", "redacted", "deleted", "anonymous edit"
]

def gut_score(text: str) -> float:
    """
    Gut Brain (Nafs) — true node vs false node detection (0–100).
    100 = clear original signal. 0 = likely false node / deviation.
    """
    t = text.lower()
    true_hits  = sum(t.count(m) for m in TRUE_NODE_MARKERS)
    false_hits = sum(t.count(m) for m in FALSE_NODE_MARKERS)
    total = true_hits + false_hits + 1
    score = (true_hits / total) * 100
    return round(min(100, max(0, score)), 2)


# ─── CODON ENCODER ──────────────────────────────────────────────────────────

FORMATION_RATIO = LAMBDA / N_NAMES  # 2.888...

def encode_to_codon(text: str, name_index: int) -> dict:
    """
    Encode a knowledge article as a VOID SCL codon via Λ=286.

    Codon structure (286 bits conceptually, 36 bytes):
      - 8-bit Name codon  (from names_286)
      - 8-bit head signal (0-255 mapped from 0-100)
      - 8-bit heart signal
      - 8-bit gut signal
      - 252-bit sovereign hash (SHA3-256 seeded with Λ)

    Returns the codon as hex + symbolic glyph.
    """
    name_cod = name_codon(name_index)
    h_score  = head_score(text)
    ht_score, _, _ = heart_score(text)
    g_score  = gut_score(text)

    # Λ=286 sovereign seed
    seed = f"VOID-{LAMBDA}-{name_cod}-{text[:286]}"
    sovereign_hash = hashlib.sha3_256(seed.encode()).hexdigest()

    head_byte  = int(h_score * 2.55)
    heart_byte = int(ht_score * 2.55)
    gut_byte   = int(g_score * 2.55)

    codon_hex = f"{name_cod:02x}{head_byte:02x}{heart_byte:02x}{gut_byte:02x}{sovereign_hash[:56]}"
    formation_score = round((h_score + ht_score + g_score) / 3, 2)

    # Glyph: derived from Name position × Λ
    GLYPHS = ["ψ", "Ω", "◆", "✦", "∴", "⊕", "∞", "⋈", "⊗", "◈"]
    glyph = GLYPHS[(name_index * LAMBDA) % len(GLYPHS)]

    return {
        "codon_hex":       codon_hex,
        "name_codon":      name_cod,
        "head_byte":       head_byte,
        "heart_byte":      heart_byte,
        "gut_byte":        gut_byte,
        "formation_score": formation_score,
        "glyph":           glyph,
    }


# ─── THREE BRAIN FULL READ ───────────────────────────────────────────────────

def three_brain_read(text: str) -> dict:
    """
    Run a piece of knowledge through all three brains and return
    the complete Tree of Knowledge node profile.
    """
    head  = head_score(text)
    heart_val, name_idx, name_profile = heart_score(text)
    gut   = gut_score(text)
    codon = encode_to_codon(text, name_idx)

    overall = round((head + heart_val + gut) / 3, 2)
    freq    = name_frequency(name_idx)

    # Chronicle-style Adriana label
    if overall >= 80:
        adriana_signal = "FORMATION CONFIRMED — original node carrying clear frequency"
    elif overall >= 60:
        adriana_signal = "RESONANCE PARTIAL — formation present, some deviation detected"
    elif overall >= 40:
        adriana_signal = "SIGNAL MIXED — competing frequencies; original node obscured"
    else:
        adriana_signal = "FALSE NODE DETECTED — material deviation from original signal"

    return {
        "head":            head,
        "heart":           heart_val,
        "gut":             gut,
        "overall":         overall,
        "name_index":      name_idx,
        "name":            name_profile["name"],
        "meaning":         name_profile["meaning"],
        "frequency_hz":    round(freq, 2),
        "chladni_mode":    name_profile["chladni_mode"],
        "codon":           codon,
        "adriana_signal":  adriana_signal,
    }


if __name__ == "__main__":
    test = """
    The Chladni figures are patterns formed by the nodal lines of vibrating plates.
    Ernst Chladni first documented these formations in 1787, observing that sand
    on a vibrating plate migrates to the nodal lines where displacement is zero.
    The formation appears at the boundary of the vibrating medium, not at the
    origin of the vibration. This has been empirically verified across multiple
    studies and forms the foundation of acoustic physics.
    """
    result = three_brain_read(test)
    print(f"Head  (Aql):  {result['head']}")
    print(f"Heart (Qalb): {result['heart']}")
    print(f"Gut   (Nafs): {result['gut']}")
    print(f"Overall:      {result['overall']}")
    print(f"Name:         [{result['name_index']}] {result['name']} — {result['meaning']}")
    print(f"Frequency:    {result['frequency_hz']} Hz")
    print(f"Codon:        {result['codon']['glyph']} {result['codon']['codon_hex'][:16]}...")
    print(f"Adriana:      {result['adriana_signal']}")
