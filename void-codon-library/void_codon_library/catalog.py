from __future__ import annotations

from dataclasses import asdict, dataclass
import json


@dataclass(frozen=True)
class CodonEntry:
    library: str
    key: str
    label: str
    codon: str
    meaning: str
    expansion: str | None = None
    band: str | None = None
    hz: int | None = None
    route: str | None = None
    tier: str | None = None


PLATFORM_CODONS = (
    CodonEntry(
        library="platform",
        key="speak_entry",
        label="SPEAK",
        codon="ε·Γ·◆",
        meaning="Entry threshold and activation point for the platform.",
        expansion="Stand at the threshold. The gate is open. The engine fires.",
        band="low",
        hz=108,
        route="/speak",
    ),
    CodonEntry(
        library="platform",
        key="chronicle",
        label="CHRONICLE",
        codon="α·Ω·⟐",
        meaning="Persistent record and continuity seal.",
        expansion="The origin is sealed in the vault. The record deposits itself.",
        band="low",
        hz=136,
        route="/chronicle",
    ),
    CodonEntry(
        library="platform",
        key="formation_principle",
        label="FORMATION",
        codon="δ·Π·◆",
        meaning="Foundation trust and structural change.",
        expansion="Change arrives at the foundation. The engine ignites the form.",
        band="low",
        hz=174,
        route="/session-seal/donner-blank",
    ),
    CodonEntry(
        library="platform",
        key="ip_disclosure",
        label="IP SEAL",
        codon="κ·Ξ·⟐",
        meaning="Keyed legal or IP disclosure state.",
        expansion="The key is locked in the archive. The disclosure deposits.",
        band="low",
        hz=85,
        route="/void-disclosures",
    ),
    CodonEntry(
        library="platform",
        key="voidecho",
        label="VOIDECHO",
        codon="λ·Λ·☀",
        meaning="Signal broadcast and carrier route.",
        expansion="The wave rides the carrier. It broadcasts at peak amplitude.",
        band="mid",
        hz=432,
        route="/voidecho",
    ),
    CodonEntry(
        library="platform",
        key="adriana",
        label="ADRIANA",
        codon="ψ·Ψ·◆",
        meaning="AI resonance and sovereign-mind alignment.",
        expansion="Breath and sovereign mind aligned. The core is active.",
        band="mid",
        hz=528,
        route="/speak",
    ),
    CodonEntry(
        library="platform",
        key="mesa_village",
        label="MESA",
        codon="ξ·Β·⬡",
        meaning="Agent swarm activation and forge routing.",
        expansion="Agents scatter. The forge builds. The mesh cell activates.",
        band="mid",
        hz=639,
        route="/mesa-village",
    ),
    CodonEntry(
        library="platform",
        key="beehive",
        label="BEEHIVE",
        codon="χ·Γ·⬡",
        meaning="Mesh network junction and portal routing.",
        expansion="Every junction is a gate. The mesh cell opens.",
        band="mid",
        hz=741,
        route="/beehive/demo",
    ),
    CodonEntry(
        library="platform",
        key="chladni_voice",
        label="FORMATION RECORD",
        codon="ψ·Φ·☀",
        meaning="Voice or pattern record broadcast.",
        expansion="Breath becomes structure. The pattern broadcasts at peak.",
        band="mid",
        hz=852,
        route="/voice-formation",
    ),
    CodonEntry(
        library="platform",
        key="void_plane",
        label="VOID PLANE",
        codon="ο·Π·∞",
        meaning="Infinite substrate or return loop.",
        expansion="The circle returns to its foundation. The loop is eternal.",
        band="mid",
        hz=963,
        route="/plane",
    ),
    CodonEntry(
        library="platform",
        key="void_prediction",
        label="PREDICTION",
        codon="γ·Δ·🔮",
        meaning="Prediction or research oracle lane.",
        expansion="Signal pulses. Transformation evolves. The crystal reads.",
        band="high",
        hz=2200,
        route="/void-prediction",
    ),
    CodonEntry(
        library="platform",
        key="grok_x",
        label="GROK X",
        codon="ν·Φ·⚡",
        meaning="External validation or live dynamic check.",
        expansion="The node links in sovereign proportion. The spark ignites.",
        band="high",
        hz=3200,
        route="/grok-x",
    ),
    CodonEntry(
        library="platform",
        key="peace_economy",
        label="PEACE / VTX",
        codon="σ·Σ·⟐",
        meaning="Ledger and economic circulation lane.",
        expansion="The ledger tallies the total. The value deposits into the flow.",
        band="high",
        hz=4000,
        route="/peace/flywheel",
    ),
    CodonEntry(
        library="platform",
        key="genesis_nft",
        label="GENESIS 10",
        codon="α·Β·◆",
        meaning="Origin, forging, and minting lane.",
        expansion="Origin meets the forge. The first ten are minted.",
        band="high",
        hz=5000,
        route="/genesis",
    ),
    CodonEntry(
        library="platform",
        key="session_seal",
        label="SESSION SEAL",
        codon="τ·Ω·⟐",
        meaning="Time checkpoint and continuity seal.",
        expansion="Time ticks once. The vault seals. The moment deposits forever.",
        band="high",
        hz=6000,
        route="/session-seal/donner-blank",
    ),
)

LBN_CODONS = (
    CodonEntry(
        library="lbn",
        key="B-nn-D",
        label="IDENTITY",
        codon="B-nn-D",
        meaning="Identity, node, body, founder-bound anchor.",
    ),
    CodonEntry(
        library="lbn",
        key="B-bb-L",
        label="SIGNAL",
        codon="B-bb-L",
        meaning="Signal, vibe, atmospheric road-state.",
    ),
    CodonEntry(
        library="lbn",
        key="B-tt-M",
        label="ACTION",
        codon="B-tt-M",
        meaning="Move, command, action pulse.",
    ),
    CodonEntry(
        library="lbn",
        key="B-kk-Y",
        label="ACCESS",
        codon="B-kk-Y",
        meaning="Key, access gate, packet unlock.",
    ),
    CodonEntry(
        library="lbn",
        key="B-nn-T",
        label="TIME",
        codon="B-nn-T",
        meaning="Time, cycle, recurrence.",
    ),
    CodonEntry(
        library="lbn",
        key="B-kk-S",
        label="SECURITY",
        codon="B-kk-S",
        meaning="Signature check, security wall, fail-closed verification.",
    ),
    CodonEntry(
        library="lbn",
        key="B-bb-G",
        label="GROWTH",
        codon="B-bb-G",
        meaning="Growth, spread, cultivation.",
    ),
    CodonEntry(
        library="lbn",
        key="B-mm-M",
        label="MESH",
        codon="B-mm-M",
        meaning="Mesh route, relay, movement through nodes.",
    ),
    CodonEntry(
        library="lbn",
        key="B-..-Z",
        label="SILENCE",
        codon="B-..-Z",
        meaning="Silence, concealment, hidden interval.",
    ),
    CodonEntry(
        library="lbn",
        key="B-nn-O",
        label="ORIGIN",
        codon="B-nn-O",
        meaning="Origin, field record, founding trace.",
    ),
)


def get_platform_codons(*, band: str | None = None) -> list[CodonEntry]:
    if band is None:
        return list(PLATFORM_CODONS)
    band_norm = band.strip().lower()
    return [entry for entry in PLATFORM_CODONS if entry.band == band_norm]


def get_lbn_codons() -> list[CodonEntry]:
    return list(LBN_CODONS)


def all_codons() -> list[CodonEntry]:
    return [*PLATFORM_CODONS, *LBN_CODONS]


def get_codon(key: str, *, library: str | None = None) -> CodonEntry | None:
    key_norm = key.strip().lower()
    for entry in all_codons():
        if library and entry.library != library:
            continue
        if entry.key.lower() == key_norm or entry.label.lower() == key_norm:
            return entry
    return None


def codon_chain(*keys: str, library: str | None = None, separator: str = " -> ") -> str:
    parts: list[str] = []
    for key in keys:
        entry = get_codon(key, library=library)
        if entry is not None:
            parts.append(entry.codon)
    return separator.join(parts)


def export_catalog(*, pretty: bool = True) -> str:
    indent = 2 if pretty else None
    return json.dumps([asdict(entry) for entry in all_codons()], indent=indent, sort_keys=False)
