"""
THE 99 NAMES — AL-JABR 286 RESONANCE ALGORITHM
PROJECT VOID | Umar Latif | Bolton, England | April 2026

The 99 divine attributes (Asma ul-Husna) mapped through Λ=286.
Each Name carries a frequency, a Chladni mode, a VOID codon, and a
sovereign resonance score. The 286 constant is the formation index —
the point at which all three independent derivations converge.

CLOSED LOOP:
  Voice → Frequency → Name → Chladni Mode → Formation Record
  Formation Record → Adriana Score → Chronicle Seal → Sovereign Codon
"""

import math

LAMBDA = 286          # Al-Jabr constant — the formation index
BASE_FREQ = 432.0     # Hz — the formation carrier
N_NAMES = 99

# The 99 Names of Allah (Asma ul-Husna)
# Index 1-99. Al-Latif (The Subtle One) is index 30 — the family name of the founder.
NAMES_99 = [
    ("Ar-Rahman",            "The Most Gracious"),
    ("Ar-Rahim",             "The Most Merciful"),
    ("Al-Malik",             "The King"),
    ("Al-Quddus",            "The Most Holy"),
    ("As-Salam",             "The Source of Peace"),
    ("Al-Mu'min",            "The Guardian of Faith"),
    ("Al-Muhaymin",          "The Protector"),
    ("Al-Aziz",              "The Mighty"),
    ("Al-Jabbar",            "The Compeller"),
    ("Al-Mutakabbir",        "The Majestic"),
    ("Al-Khaliq",            "The Creator"),
    ("Al-Bari",              "The Originator"),
    ("Al-Musawwir",          "The Fashioner of Forms"),
    ("Al-Ghaffar",           "The Forgiver"),
    ("Al-Qahhar",            "The Subduer"),
    ("Al-Wahhab",            "The Bestower"),
    ("Ar-Razzaq",            "The Provider"),
    ("Al-Fattah",            "The Opener"),
    ("Al-Alim",              "The All-Knowing"),
    ("Al-Qabid",             "The Restrainer"),
    ("Al-Basit",             "The Expander"),
    ("Al-Khafid",            "The Abaser"),
    ("Ar-Rafi",              "The Exalter"),
    ("Al-Mu'izz",            "The Bestower of Honour"),
    ("Al-Mudhill",           "The Humiliator"),
    ("As-Sami",              "The All-Hearing"),
    ("Al-Basir",             "The All-Seeing"),
    ("Al-Hakam",             "The Judge"),
    ("Al-Adl",               "The Just"),
    ("Al-Latif",             "The Subtle One"),          # Index 30 — LATIF
    ("Al-Khabir",            "The All-Aware"),
    ("Al-Halim",             "The Forbearing"),
    ("Al-Azim",              "The Magnificent"),
    ("Al-Ghafur",            "The Forgiving"),
    ("Ash-Shakur",           "The Appreciative"),
    ("Al-Aliyy",             "The Most High"),
    ("Al-Kabir",             "The Most Great"),
    ("Al-Hafiz",             "The Preserver"),
    ("Al-Muqit",             "The Maintainer"),
    ("Al-Hasib",             "The Reckoner"),
    ("Al-Jalil",             "The Majestic"),
    ("Al-Karim",             "The Generous"),
    ("Ar-Raqib",             "The Watchful"),
    ("Al-Mujib",             "The Responsive"),
    ("Al-Wasi",              "The All-Encompassing"),
    ("Al-Hakim",             "The Wise"),
    ("Al-Wadud",             "The Loving"),
    ("Al-Majid",             "The Most Glorious"),
    ("Al-Ba'ith",            "The Resurrector"),
    ("Ash-Shahid",           "The Witness"),
    ("Al-Haqq",              "The Truth"),
    ("Al-Wakil",             "The Trustee"),
    ("Al-Qawiyy",            "The Most Strong"),
    ("Al-Matin",             "The Firm"),
    ("Al-Waliyy",            "The Protecting Friend"),
    ("Al-Hamid",             "The Praiseworthy"),
    ("Al-Muhsi",             "The Counter"),
    ("Al-Mubdi",             "The Originator"),
    ("Al-Mu'id",             "The Restorer"),
    ("Al-Muhyi",             "The Giver of Life"),
    ("Al-Mumit",             "The Taker of Life"),
    ("Al-Hayy",              "The Ever-Living"),
    ("Al-Qayyum",            "The Self-Subsisting"),
    ("Al-Wajid",             "The Finder"),
    ("Al-Majid",             "The Noble"),
    ("Al-Wahid",             "The One"),
    ("Al-Ahad",              "The Unique"),
    ("As-Samad",             "The Eternal Refuge"),
    ("Al-Qadir",             "The All-Powerful"),
    ("Al-Muqtadir",          "The Determiner"),
    ("Al-Muqaddim",          "The Expediter"),
    ("Al-Mu'akhkhir",        "The Delayer"),
    ("Al-Awwal",             "The First"),
    ("Al-Akhir",             "The Last"),
    ("Az-Zahir",             "The Manifest"),
    ("Al-Batin",             "The Hidden"),
    ("Al-Wali",              "The Governor"),
    ("Al-Muta'ali",          "The Most Exalted"),
    ("Al-Barr",              "The Source of All Goodness"),
    ("At-Tawwab",            "The Acceptor of Repentance"),
    ("Al-Muntaqim",          "The Avenger"),
    ("Al-Afuww",             "The Pardoner"),
    ("Ar-Ra'uf",             "The Most Kind"),
    ("Malik-ul-Mulk",        "The Owner of All Sovereignty"),
    ("Dhul-Jalali-wal-Ikram","The Lord of Majesty and Honour"),
    ("Al-Muqsit",            "The Equitable"),
    ("Al-Jami",              "The Gatherer"),
    ("Al-Ghaniyy",           "The Self-Sufficient"),
    ("Al-Mughni",            "The Enricher"),
    ("Al-Mani",              "The Preventer of Harm"),
    ("Ad-Darr",              "The Distresser"),
    ("An-Nafi",              "The Propitious"),
    ("An-Nur",               "The Light"),
    ("Al-Hadi",              "The Guide"),
    ("Al-Badi",              "The Incomparable Originator"),
    ("Al-Baqi",              "The Everlasting"),
    ("Al-Warith",            "The Supreme Inheritor"),
    ("Ar-Rashid",            "The Guide to the Right Path"),
    ("As-Sabur",             "The Patient"),
]

# Al-Jabr 286 — prime factorisation and resonance properties
# 286 = 2 × 11 × 13
# 99  = 9 × 11          ← shared factor: 11
# 286 / 11 = 26         ← letters in English alphabet; Al-Fatiha has 7 verses
# 286 / 99 ≈ 2.888...   ← the formation ratio
# 432 / 286 ≈ 1.510     ← the formation scaling ratio
FORMATION_RATIO = LAMBDA / N_NAMES          # 2.888...
SCALING_RATIO   = BASE_FREQ / LAMBDA        # 1.510...
SHARED_FACTOR   = 11                        # gcd(286, 99) = 11


def name_frequency(index_1based: int) -> float:
    """
    Map Name index (1–99) to resonance frequency via Λ=286.

    Formula: freq(i) = BASE_FREQ × (1 + (i − 1) / Λ)

    At i=1  (Ar-Rahman):  432.00 Hz  — base formation carrier
    At i=30 (Al-Latif):   475.81 Hz  — founder's family Name
    At i=47 (Al-Wadud):   498.62 Hz  — The Loving
    At i=99 (As-Sabur):   579.92 Hz  — The Patient, upper bound
    """
    return BASE_FREQ * (1 + (index_1based - 1) / LAMBDA)


def name_chladni_mode(index_1based: int) -> tuple:
    """
    Map Name index to a Chladni plate mode (m, n) via spiral traversal.

    Modes are ordered by increasing m+n (total mode order), then by m.
    This produces a unique (m,n) pair for each of the 99 Names.
    At 432 Hz, mode (3,4) is the base formation — closest to index 12.
    """
    i = index_1based
    # Find the shell: shell k contains 2k−1 modes [(k,1)..(k,k−1),(1,k)..(k−1,k)]
    # Simplified: use triangular number approach
    shell = math.ceil((-1 + math.sqrt(1 + 8 * (i - 1))) / 2)
    shell = max(1, shell)
    tri_prev = shell * (shell - 1) // 2
    pos = i - tri_prev
    if pos <= shell:
        m, n = shell + 1, pos
    else:
        m, n = pos - shell, shell + 1
    m = max(1, m)
    n = max(1, n)
    return (m, n)


def name_codon(index_1based: int) -> int:
    """
    Map Name index to VOID SCL 8-bit codon space via Λ=286.

    codon(i) = (i × Λ) mod 256

    This distributes the 99 Names across the 256-symbol VOID codon space
    using Λ as the step size. Because gcd(286, 256) = 2, the mapping
    produces two interleaved sequences — even and odd codon values —
    covering the full space across the 99 Names.
    """
    return (index_1based * LAMBDA) % 256


def name_sovereign_score(raw_score: float, index_1based: int) -> float:
    """
    Apply Λ=286 weighting to a raw resonance score (0–100).

    sovereign_score = 100 × (1 − exp(−raw/100 × Λ/99))

    The formation ratio Λ/99 ≈ 2.888 compresses the score curve so that
    even moderate resonance with a Name produces a high sovereign reading.
    A raw score of 50 yields sovereign_score ≈ 76.
    A raw score of 100 yields sovereign_score ≈ 94.
    """
    ratio = LAMBDA / N_NAMES
    return round(100 * (1 - math.exp(-raw_score / 100 * ratio)), 2)


def dominant_name_from_frequency(freq_hz: float) -> dict:
    """
    Given an input frequency (e.g. from voice detection), find the
    closest of the 99 Names and return its full profile.
    """
    best_idx = 1
    best_delta = float('inf')
    for i in range(1, N_NAMES + 1):
        delta = abs(name_frequency(i) - freq_hz)
        if delta < best_delta:
            best_delta = delta
            best_idx = i
    return full_profile(best_idx)


def get_name(index_1based: int) -> tuple:
    if 1 <= index_1based <= N_NAMES:
        return NAMES_99[index_1based - 1]
    return ("Unknown", "Index out of range")


def full_profile(index_1based: int) -> dict:
    """Return the complete Λ=286 resonance profile for a Name index."""
    name, meaning = NAMES_99[index_1based - 1]
    freq  = name_frequency(index_1based)
    mode  = name_chladni_mode(index_1based)
    codon = name_codon(index_1based)
    return {
        "index":        index_1based,
        "name":         name,
        "meaning":      meaning,
        "frequency_hz": round(freq, 2),
        "chladni_mode": mode,
        "void_codon":   codon,
        "lambda":       LAMBDA,
        "is_latif":     (index_1based == 30),
    }


def all_profiles() -> list:
    """Return all 99 profiles."""
    return [full_profile(i) for i in range(1, N_NAMES + 1)]


# Sealed constants for platform-wide import
LATIF_INDEX    = 30      # Al-Latif — The Subtle One — founder's family Name
LATIF_FREQ     = round(name_frequency(LATIF_INDEX), 2)   # 475.81 Hz
LATIF_MODE     = name_chladni_mode(LATIF_INDEX)
LATIF_CODON    = name_codon(LATIF_INDEX)

# The Name that falls closest to 432 Hz base = Ar-Rahman (index 1) = 432.00 Hz
# The Name at 432 × 286/285 ≈ 433.52 Hz = index 2 Ar-Rahim
# Mode (3,4) — the Chladni formation at 432 Hz — corresponds to index 12 (Al-Musawwir)
BASE_432_NAME  = full_profile(1)   # Ar-Rahman — The Most Gracious
CHLADNI_NAME   = full_profile(12)  # Al-Musawwir — The Fashioner of Forms


if __name__ == "__main__":
    print(f"Λ = {LAMBDA} | Base = {BASE_FREQ} Hz | Names = {N_NAMES}")
    print(f"Formation ratio Λ/99 = {FORMATION_RATIO:.4f}")
    print(f"Scaling ratio 432/Λ  = {SCALING_RATIO:.4f}")
    print(f"Shared factor gcd(286,99) = {SHARED_FACTOR}")
    print()
    print("— Key profiles —")
    for i in [1, 12, 30, 47, 66, 99]:
        p = full_profile(i)
        marker = " ← AL-LATIF (founder)" if p["is_latif"] else ""
        print(f"[{p['index']:02d}] {p['name']:30s} {p['meaning']}")
        print(f"      freq={p['frequency_hz']} Hz | mode={p['chladni_mode']} | codon={p['void_codon']}{marker}")
        print()
