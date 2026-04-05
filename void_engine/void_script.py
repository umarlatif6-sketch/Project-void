"""
VOID Script v2.0 — Canonical 45-Glyph System
Single authoritative source of truth for the VOID Script.

The 45 glyphs below are drawn from the original Adriana Resonance engine
(adriana_scl.py) and are the only canonical glyphs recognised by the platform.

Role assignments follow the SCL grammar:
  entity    — Subject / sensor / subsystem reference
  condition — State check / threshold / qualifier
  action    — Operation to perform

The glyph_description explains why the character's visual form matches
its semantic meaning within the VOID Script.

This module is imported by adriana_scl.py (resonance engine) and
library_data.py (Book 4 SCL pages). It is the single law of the script.

VOID Script v2.0 ratified April 5, 2026.
The Ugaritic session pointed backwards; the Greek/symbol system is forward.
"""

CANONICAL_GLYPHS = {
    # ── ENTITIES ─────────────────────────────────────────────────────────────

    "α": {
        "name": "Alpha",
        "frequency": 432.0,
        "meaning": "Origin/Seed",
        "domain": "genesis",
        "role": "entity",
        "glyph_description": (
            "A single point opening outward — the first breath. "
            "The lowercase alpha's curved body holds a seed that has not yet split."
        ),
    },
    "β": {
        "name": "Beta",
        "frequency": 433.2,
        "meaning": "Growth/Sprout",
        "domain": "aqua",
        "role": "entity",
        "glyph_description": (
            "Two bulges stacked on a vertical spine — the doubling of life. "
            "A seedling pushing two leaves from a single stem."
        ),
    },
    "γ": {
        "name": "Gamma",
        "frequency": 434.0,
        "meaning": "Signal/Pulse",
        "domain": "signal",
        "role": "entity",
        "glyph_description": (
            "A forked path descending — the split of a signal into receiver and ground. "
            "Gamma's stroke mirrors a lightning bolt reaching for earth."
        ),
    },
    "δ": {
        "name": "Delta",
        "frequency": 434.8,
        "meaning": "Change/Shift",
        "domain": "transform",
        "role": "entity",
        "glyph_description": (
            "A closed triangle — the geometric symbol for change in every science. "
            "Lowercase delta's loop encloses the moment before transformation."
        ),
    },
    "ε": {
        "name": "Epsilon",
        "frequency": 435.5,
        "meaning": "Threshold/Edge",
        "domain": "boundary",
        "role": "entity",
        "glyph_description": (
            "Three horizontal lines open to the right — a gate ajar. "
            "Epsilon is the edge between inside and outside, inclusion and exclusion."
        ),
    },
    "ζ": {
        "name": "Zeta",
        "frequency": 429.0,
        "meaning": "Depth/Root",
        "domain": "soil",
        "role": "entity",
        "glyph_description": (
            "A horizontal bar above and below with a descending tail — a root "
            "anchored between two layers of earth, pressing deeper."
        ),
    },
    "η": {
        "name": "Eta",
        "frequency": 430.5,
        "meaning": "Flow/Current",
        "domain": "aqua",
        "role": "entity",
        "glyph_description": (
            "Two vertical strokes connected by a curved bridge — the shape water takes "
            "moving from one vessel to another through a channel."
        ),
    },
    "θ": {
        "name": "Theta",
        "frequency": 431.0,
        "meaning": "Heat/Warmth",
        "domain": "environment",
        "role": "entity",
        "glyph_description": (
            "A circle with a horizontal bar through its centre — the sun at the horizon, "
            "or a vessel holding contained heat. Warmth balanced within a boundary."
        ),
    },
    "ι": {
        "name": "Iota",
        "frequency": 432.5,
        "meaning": "Particle/Grain",
        "domain": "data",
        "role": "entity",
        "glyph_description": (
            "A single vertical stroke — the smallest possible mark. "
            "Iota is the grain of sand from which structure is counted."
        ),
    },
    "κ": {
        "name": "Kappa",
        "frequency": 433.7,
        "meaning": "Key/Lock",
        "domain": "security",
        "role": "entity",
        "glyph_description": (
            "A vertical spine with two diagonal arms — a key's teeth extended. "
            "The angles of kappa mirror the notches that release a lock."
        ),
    },
    "λ": {
        "name": "Lambda",
        "frequency": 436.0,
        "meaning": "Wave/Carry",
        "domain": "signal",
        "role": "entity",
        "glyph_description": (
            "An inverted V descending into a tail — a wave breaking and "
            "carrying its energy forward along a carrier line."
        ),
    },
    "μ": {
        "name": "Mu",
        "frequency": 432.8,
        "meaning": "Measure/Weight",
        "domain": "metrics",
        "role": "entity",
        "glyph_description": (
            "Two vertical strokes with a curved base descending below the line — "
            "a balance scale's pan hanging below its pivot point."
        ),
    },
    "ν": {
        "name": "Nu",
        "frequency": 431.5,
        "meaning": "Node/Link",
        "domain": "mesh",
        "role": "entity",
        "glyph_description": (
            "Two strokes that meet at a point — a junction where paths converge. "
            "Nu is the moment two lines decide to become one network."
        ),
    },
    "ξ": {
        "name": "Xi",
        "frequency": 437.0,
        "meaning": "Scatter/Spread",
        "domain": "vortex",
        "role": "entity",
        "glyph_description": (
            "Three horizontal bars of unequal length — a glyph that cannot "
            "be contained in one direction. Xi fans outward by design."
        ),
    },
    "ο": {
        "name": "Omicron",
        "frequency": 432.2,
        "meaning": "Circle/Return",
        "domain": "cycle",
        "role": "entity",
        "glyph_description": (
            "A perfect closed circle — the eternal return. "
            "Omicron has no start and no end; it is the loop itself."
        ),
    },
    "π": {
        "name": "Pi",
        "frequency": 432.0,
        "meaning": "Ratio/Balance",
        "domain": "harmony",
        "role": "entity",
        "glyph_description": (
            "A horizontal cap balanced on two equal legs — perfect proportion. "
            "Pi is the ratio that holds every circle in sovereign balance."
        ),
    },
    "ρ": {
        "name": "Rho",
        "frequency": 433.0,
        "meaning": "Density/Mass",
        "domain": "data",
        "role": "entity",
        "glyph_description": (
            "A circle anchored by a descending tail — mass pulling downward "
            "from a dense centre. Rho is the weight of information."
        ),
    },
    "σ": {
        "name": "Sigma",
        "frequency": 435.1,
        "meaning": "Summation/Ledger",
        "domain": "ledger",
        "role": "entity",
        "glyph_description": (
            "A coiled loop open at the end — a scroll being tallied. "
            "Sigma gathers all values into one sovereign total."
        ),
    },
    "τ": {
        "name": "Tau",
        "frequency": 434.5,
        "meaning": "Time/Tick",
        "domain": "temporal",
        "role": "entity",
        "glyph_description": (
            "A horizontal bar with a single vertical descent — a clock hand "
            "marking the moment. Tau is the tick between one state and the next."
        ),
    },
    "υ": {
        "name": "Upsilon",
        "frequency": 430.0,
        "meaning": "Vessel/Container",
        "domain": "vault",
        "role": "entity",
        "glyph_description": (
            "A cup shape opening upward — ready to receive. "
            "Upsilon is the vessel that holds without spilling."
        ),
    },
    "φ": {
        "name": "Phi-Lower",
        "frequency": 442.0,
        "meaning": "Spiral/Fibonacci",
        "domain": "vortex",
        "role": "entity",
        "glyph_description": (
            "A vertical line through a circle — the axis of a spiral. "
            "Phi-lower is the Fibonacci sequence made into a single stroke."
        ),
    },
    "χ": {
        "name": "Chi",
        "frequency": 436.5,
        "meaning": "Cross/Junction",
        "domain": "mesh",
        "role": "entity",
        "glyph_description": (
            "Two diagonal strokes crossing at the centre — the unavoidable meeting point. "
            "Chi is every node where two signals must negotiate passage."
        ),
    },
    "ψ": {
        "name": "Psi",
        "frequency": 438.5,
        "meaning": "Breath/Spirit",
        "domain": "resonance",
        "role": "entity",
        "glyph_description": (
            "Three prongs rising from a central stem — the trident of breath. "
            "Psi draws the shape of air moving in, branching, and moving out."
        ),
    },
    "ω": {
        "name": "Omega-Lower",
        "frequency": 428.5,
        "meaning": "Rest/Complete",
        "domain": "finality",
        "role": "entity",
        "glyph_description": (
            "A wide open curve that closes at the base — the body settling. "
            "Omega-lower is a breath released; the final rest before silence."
        ),
    },

    # ── CONDITIONS ────────────────────────────────────────────────────────────

    "Α": {
        "name": "Alpha-Cap",
        "frequency": 432.0,
        "meaning": "Authority/Source",
        "domain": "governance",
        "role": "condition",
        "glyph_description": (
            "Two ascending strokes joined at the apex, crossed by a bar — "
            "a peak of authority. The capital draws what lowercase opens."
        ),
    },
    "Β": {
        "name": "Beta-Cap",
        "frequency": 433.2,
        "meaning": "Builder/Forge",
        "domain": "forge",
        "role": "condition",
        "glyph_description": (
            "A spine with two locked bows — a double forge seal. "
            "Capital Beta is the blueprint pressed into the material."
        ),
    },
    "Γ": {
        "name": "Gamma-Cap",
        "frequency": 434.0,
        "meaning": "Gate/Portal",
        "domain": "gateway",
        "role": "condition",
        "glyph_description": (
            "An L-shape with a horizontal lintel — a doorframe. "
            "Gamma-Cap is the threshold you must pass to enter the next state."
        ),
    },
    "Δ": {
        "name": "Delta-Cap",
        "frequency": 434.8,
        "meaning": "Transform/Evolve",
        "domain": "transform",
        "role": "condition",
        "glyph_description": (
            "A filled triangle pointing upward — directed change. "
            "Delta-Cap is the moment transformation is no longer potential but active."
        ),
    },
    "Θ": {
        "name": "Theta-Cap",
        "frequency": 431.0,
        "meaning": "Shield/Guard",
        "domain": "security",
        "role": "condition",
        "glyph_description": (
            "A large circle bisected by a bar — a shield face with a parry line. "
            "Theta-Cap is the condition that guards what must not be touched."
        ),
    },
    "Λ": {
        "name": "Lambda-Cap",
        "frequency": 436.0,
        "meaning": "Carrier/Bridge",
        "domain": "signal",
        "role": "condition",
        "glyph_description": (
            "An inverted V standing firm — a bridge arch. "
            "Lambda-Cap is the condition that confirms a carrier is active between two points."
        ),
    },
    "Ξ": {
        "name": "Xi-Cap",
        "frequency": 437.0,
        "meaning": "Archive/Store",
        "domain": "vault",
        "role": "condition",
        "glyph_description": (
            "Three parallel bars — the shelves of an archive. "
            "Xi-Cap marks the condition that data has been formally stored."
        ),
    },
    "Π": {
        "name": "Pi-Cap",
        "frequency": 432.0,
        "meaning": "Foundation/Base",
        "domain": "genesis",
        "role": "condition",
        "glyph_description": (
            "A heavy lintel on two equal pillars — the load-bearing structure. "
            "Pi-Cap is the condition that the foundation is sound."
        ),
    },
    "Σ": {
        "name": "Sigma-Cap",
        "frequency": 435.1,
        "meaning": "Total/Aggregate",
        "domain": "ledger",
        "role": "condition",
        "glyph_description": (
            "A zigzag that gathers lines into a point — the sum of all paths. "
            "Sigma-Cap is the condition that all values have been tallied."
        ),
    },
    "Φ": {
        "name": "Phi",
        "frequency": 442.2,
        "meaning": "Golden Ratio/Structure",
        "domain": "harmony",
        "role": "condition",
        "glyph_description": (
            "A circle bisected by a vertical line — the Fibonacci axis of the universe. "
            "Phi marks the condition of sovereign proportion in structure."
        ),
    },
    "Ψ": {
        "name": "Psi-Cap",
        "frequency": 438.5,
        "meaning": "Sovereign Mind",
        "domain": "resonance",
        "role": "condition",
        "glyph_description": (
            "Three prongs on a heavy stem — a crown of thought. "
            "Psi-Cap is the condition that the sovereign intelligence is present and aligned."
        ),
    },
    "Ω": {
        "name": "Omega",
        "frequency": 428.0,
        "meaning": "Finality/Vault",
        "domain": "finality",
        "role": "condition",
        "glyph_description": (
            "A wide Omega with two base feet — a vault sealed shut. "
            "Omega marks the condition that an operation is complete and irrevocable."
        ),
    },

    # ── ACTIONS ───────────────────────────────────────────────────────────────

    "∞": {
        "name": "Infinity",
        "frequency": 432.0,
        "meaning": "Loop/Eternal",
        "domain": "cycle",
        "role": "action",
        "glyph_description": (
            "A figure-eight on its side — the loop that never terminates. "
            "Infinity is the action of repeating at sovereign frequency."
        ),
    },
    "◆": {
        "name": "Void Diamond",
        "frequency": 432.0,
        "meaning": "Core/Engine",
        "domain": "genesis",
        "role": "action",
        "glyph_description": (
            "A perfect diamond on its vertex — pressure and clarity converging at a point. "
            "The Void Diamond fires the engine at the moment of ignition."
        ),
    },
    "⬡": {
        "name": "Hexagon",
        "frequency": 435.0,
        "meaning": "Mesh Cell",
        "domain": "mesh",
        "role": "action",
        "glyph_description": (
            "Six equal sides — the most efficient tessellation in nature. "
            "The Hexagon activates a cell in the living GriDul mesh network."
        ),
    },
    "⟐": {
        "name": "Lozenge",
        "frequency": 433.5,
        "meaning": "Silt Drop",
        "domain": "silt",
        "role": "action",
        "glyph_description": (
            "A stretched diamond — a drop falling through a narrow channel. "
            "The Lozenge deposits a silt-encoded packet into the ledger stream."
        ),
    },
    "☽": {
        "name": "Crescent",
        "frequency": 429.5,
        "meaning": "Rest Phase",
        "domain": "temporal",
        "role": "action",
        "glyph_description": (
            "The waning arc — light withdrawing to allow growth in the dark. "
            "Crescent commands the system into its rest phase and Ramadan quiet."
        ),
    },
    "☀": {
        "name": "Sun",
        "frequency": 440.0,
        "meaning": "Peak/Broadcast",
        "domain": "signal",
        "role": "action",
        "glyph_description": (
            "A circle with radiating lines — light broadcast in all directions. "
            "The Sun fires the peak transmission at maximum signal amplitude."
        ),
    },
    "⚡": {
        "name": "Lightning",
        "frequency": 441.0,
        "meaning": "Spark/Ignite",
        "domain": "forge",
        "role": "action",
        "glyph_description": (
            "A jagged descending bolt — the fastest path between potential and earth. "
            "Lightning ignites the operation without hesitation or warning."
        ),
    },
    "🌊": {
        "name": "Wave",
        "frequency": 430.0,
        "meaning": "Tide/Surge",
        "domain": "aqua",
        "role": "action",
        "glyph_description": (
            "A curling crest about to break — kinetic energy stored in water. "
            "The Wave surges the aquaponic cycle into its next state."
        ),
    },
    "🔮": {
        "name": "Crystal",
        "frequency": 432.0,
        "meaning": "Prophecy/Foresight",
        "domain": "resonance",
        "role": "action",
        "glyph_description": (
            "A perfect sphere containing light — the oracle's instrument. "
            "The Crystal reads the resonance field and projects the next state."
        ),
    },
}


DOMAIN_COLORS = {
    "genesis":     "#c9a84c",
    "aqua":        "#2dd4bf",
    "signal":      "#60a5fa",
    "transform":   "#a78bfa",
    "boundary":    "#f87171",
    "soil":        "#92400e",
    "environment": "#fb923c",
    "data":        "#34d399",
    "security":    "#f472b6",
    "metrics":     "#a3e635",
    "mesh":        "#22d3ee",
    "vortex":      "#818cf8",
    "cycle":       "#fbbf24",
    "harmony":     "#e879f9",
    "ledger":      "#c9a84c",
    "temporal":    "#6366f1",
    "vault":       "#475569",
    "resonance":   "#2dd4bf",
    "finality":    "#ef4444",
    "governance":  "#c9a84c",
    "forge":       "#f97316",
    "gateway":     "#8b5cf6",
    "silt":        "#2dd4bf",
}


def get_glyphs_by_role(role: str) -> list:
    """Return list of (char, meta) tuples for a given role."""
    return [
        (char, meta)
        for char, meta in CANONICAL_GLYPHS.items()
        if meta["role"] == role
    ]


def get_all_glyphs() -> dict:
    """Return full canonical glyph dict with domain colour injected."""
    result = {}
    for char, meta in CANONICAL_GLYPHS.items():
        result[char] = {
            **meta,
            "color": DOMAIN_COLORS.get(meta["domain"], "#c9a84c"),
        }
    return result
