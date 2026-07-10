"""
PROJECT VOID — Cymatics Bridge Compound Library Extension
==========================================================

Integrates compounds from:
1. Cymatics_Geometry_&_Frequency_Collapse__The_Bridge.md (user's IP)
2. CHLADNI_FREQUENCY_SYNTHESIS_ROADMAP.md (top 10 priority compounds)

These extend the base 108-compound library with:
- Cymatics-derived geometry targets (temple pillar geometries)
- Chladni-plate synthesis candidates (highest resonance scores)
- Multi-harmonic synthesis parameters (fundamental + overtones)
- UV-hardened bubble capture geometry specifications

Total new compounds: 42 (bringing library from 108 to 150)
"""

# ================================================================
# CATEGORY H: CYMATICS BRIDGE — TEMPLE PILLAR GEOMETRIES (H1-H20)
# These are derived from the Cymatics Bridge document's
# frequency→geometry→matter pipeline specification.
# ================================================================

CYMATICS_BRIDGE_COMPOUNDS = [
    # --- Temple Pillar Encoded Geometries ---
    {"id": "H01", "name": "Chidambaram Hexagonal Carbon",
     "freq": 258.0, "geometry": "hexagonal_nested",
     "elements": ["C"], "n_atoms": 54, "bond_type": "sp2",
     "category": "cymatics_bridge",
     "synthesis_note": "Hexagonal base + nested 1:2 ratio + spiral electron paths",
     "temple_source": "Chidambaram pillar pattern"},

    {"id": "H02", "name": "Akshardham Cubic Silicon",
     "freq": 378.2, "geometry": "cubic_tetrahedral",
     "elements": ["Si", "C", "N"], "n_atoms": 42, "bond_type": "sp3",
     "category": "cymatics_bridge",
     "synthesis_note": "Cubic symmetry with nested tetrahedra — Si-C-N bonding",
     "temple_source": "Akshardham cubic/tetrahedral carvings"},

    {"id": "H03", "name": "UV-Bubble Hydrogen Geometry",
     "freq": 432.0, "geometry": "spherical_nodal",
     "elements": ["H"], "n_atoms": 24, "bond_type": "covalent",
     "category": "cymatics_bridge",
     "synthesis_note": "Captured in UV-hardened glycerin bubble at 432 Hz",
     "temple_source": "Manchester Research Method"},

    {"id": "H04", "name": "Frequency-Collapsed Iron Lattice",
     "freq": 1217.6, "geometry": "bcc_complex",
     "elements": ["Fe", "Cu", "Zn"], "n_atoms": 54, "bond_type": "metallic",
     "category": "cymatics_bridge",
     "synthesis_note": "Complex polyhedra with metallic symmetry — advanced temple layering",
     "temple_source": "Advanced temple pillars with intricate geometric layering"},

    {"id": "H05", "name": "Fractal Carbide Heat Shield",
     "freq": 1530.0, "geometry": "fractal_cubic",
     "elements": ["Ti", "W", "C"], "n_atoms": 48, "bond_type": "covalent",
     "category": "cymatics_bridge",
     "synthesis_note": "Ultra-complex fractal patterns — extreme atomic density",
     "temple_source": "Rare, highly intricate temple carvings"},

    {"id": "H06", "name": "Quantum Superconductor Pillar",
     "freq": 3152.1, "geometry": "perovskite_multidim",
     "elements": ["Gd", "U", "O"], "n_atoms": 40, "bond_type": "mixed",
     "category": "cymatics_bridge",
     "synthesis_note": "Multi-dimensional quantum patterns beyond standard 3D",
     "temple_source": "Theoretical pillars representing quantum states"},

    {"id": "H07", "name": "Submarine Hull Alloy",
     "freq": 1247.3, "geometry": "fcc_layered",
     "elements": ["Cu", "Ni", "Zn"], "n_atoms": 54, "bond_type": "metallic",
     "category": "cymatics_bridge",
     "synthesis_note": "Stealth coating — frequency-absorbing layered structure",
     "temple_source": "Layered temple pillar with absorption geometry"},

    {"id": "H08", "name": "Cymatics Carbon Spiral",
     "freq": 324.0, "geometry": "spiral_hexagonal",
     "elements": ["C", "H"], "n_atoms": 48, "bond_type": "sp2",
     "category": "cymatics_bridge",
     "synthesis_note": "Spiral connections between nested hexagons — C-C bonds",
     "temple_source": "Chidambaram spiral carvings"},

    {"id": "H09", "name": "Nodal Surface Ceramic",
     "freq": 756.4, "geometry": "nodal_cubic",
     "elements": ["Si", "C", "N"], "n_atoms": 36, "bond_type": "covalent",
     "category": "cymatics_bridge",
     "synthesis_note": "2nd harmonic of A2 — nodal surfaces at standing wave minima",
     "temple_source": "Second harmonic layer of Akshardham pattern"},

    {"id": "H10", "name": "Triple-Harmonic Diamond",
     "freq": 1134.6, "geometry": "diamond_layered",
     "elements": ["C"], "n_atoms": 32, "bond_type": "sp3",
     "category": "cymatics_bridge",
     "synthesis_note": "3rd harmonic of A2 ceramic — diamond-phase carbon",
     "temple_source": "Third harmonic fractal subdivisions"},

    {"id": "H11", "name": "Geometric Signature Polymer",
     "freq": 326.5, "geometry": "hexagonal_spiral",
     "elements": ["C", "H", "N", "O"], "n_atoms": 40, "bond_type": "polymer",
     "category": "cymatics_bridge",
     "synthesis_note": "G(θ,φ,r) = Σ[Aₙ × cos(nθ) × sin(mφ) × r^k] captured",
     "temple_source": "Geometric Signature Function extraction"},

    {"id": "H12", "name": "Fourier-Extracted Silicon",
     "freq": 516.0, "geometry": "hexagonal_layered",
     "elements": ["Si"], "n_atoms": 36, "bond_type": "covalent",
     "category": "cymatics_bridge",
     "synthesis_note": "2nd harmonic of carbon (258 Hz × 2) — silicon analogue",
     "temple_source": "Fourier analysis second harmonic extraction"},

    {"id": "H13", "name": "Standing Wave Boron Nitride",
     "freq": 864.0, "geometry": "hexagonal_standing_wave",
     "elements": ["B", "N"], "n_atoms": 40, "bond_type": "sp2",
     "category": "cymatics_bridge",
     "synthesis_note": "2nd harmonic of 432 Hz — standing wave pattern in BN",
     "temple_source": "Double-frequency standing wave capture"},

    {"id": "H14", "name": "Collapse-Point Graphene",
     "freq": 432.0, "geometry": "hexagonal_collapse",
     "elements": ["C"], "n_atoms": 60, "bond_type": "sp2",
     "category": "cymatics_bridge",
     "synthesis_note": "Exact 432 Hz collapse point — maximum geometric coherence",
     "temple_source": "Fundamental frequency collapse geometry"},

    {"id": "H15", "name": "Volumetric Gale Carbon",
     "freq": 432.0, "geometry": "volumetric_19gale",
     "elements": ["C", "N"], "n_atoms": 38, "bond_type": "sp2",
     "category": "cymatics_bridge",
     "synthesis_note": "19-gale volumetric system — Project Void standing wave",
     "temple_source": "19 fundamental harmonic ratios"},

    {"id": "H16", "name": "Photopolymer Capture Matrix",
     "freq": 648.0, "geometry": "nodal_3d_network",
     "elements": ["C", "O", "H"], "n_atoms": 44, "bond_type": "polymer",
     "category": "cymatics_bridge",
     "synthesis_note": "UV-hardened resin at nodal surfaces — 3D network",
     "temple_source": "UV-hardened acoustic bubble protocol"},

    {"id": "H17", "name": "Harmonic Ratio Titanium",
     "freq": 1296.0, "geometry": "cubic_harmonic",
     "elements": ["Ti", "Al"], "n_atoms": 32, "bond_type": "metallic",
     "category": "cymatics_bridge",
     "synthesis_note": "3rd harmonic of 432 Hz — titanium aluminide at resonance",
     "temple_source": "Third harmonic ratio encoding"},

    {"id": "H18", "name": "Electron Orbital Spiral",
     "freq": 774.0, "geometry": "spiral_orbital",
     "elements": ["C"], "n_atoms": 36, "bond_type": "conjugated",
     "category": "cymatics_bridge",
     "synthesis_note": "3rd harmonic of carbon (258 Hz × 3) — orbital geometry",
     "temple_source": "Spiral patterns representing electron orbital paths"},

    {"id": "H19", "name": "Atomic Substructure Fractal",
     "freq": 1032.0, "geometry": "fractal_hexagonal",
     "elements": ["C", "Si"], "n_atoms": 42, "bond_type": "mixed",
     "category": "cymatics_bridge",
     "synthesis_note": "4th harmonic of carbon (258 Hz × 4) — fractal subdivisions",
     "temple_source": "Fractal-like subdivisions representing atomic substructure"},

    {"id": "H20", "name": "Collapse Equation Material",
     "freq": 2160.0, "geometry": "icosahedral_collapse",
     "elements": ["C", "B", "N"], "n_atoms": 48, "bond_type": "mixed",
     "category": "cymatics_bridge",
     "synthesis_note": "Matter = Frequency × Geometry × Time × Energy — 5th harmonic",
     "temple_source": "Collapse Equation verification compound"},
]


# ================================================================
# CATEGORY I: CHLADNI ROADMAP — TOP PRIORITY COMPOUNDS (I1-I12)
# From CHLADNI_FREQUENCY_SYNTHESIS_ROADMAP.md
# These have the highest predicted resonance scores (0.78-0.85)
# ================================================================

CHLADNI_PRIORITY_COMPOUNDS = [
    {"id": "I01", "name": "HAr₈ Noble Cage",
     "freq": 432.0, "geometry": "8fold_cage",
     "elements": ["H", "Ar"], "n_atoms": 9, "bond_type": "van_der_waals",
     "category": "chladni_priority",
     "resonance_score": 0.846,
     "synthesis_note": "Hydrogen centered in 8-fold argon cage at exact 432 Hz"},

    {"id": "I02", "name": "HSi₈ Silicon Cage",
     "freq": 432.0, "geometry": "8fold_cage",
     "elements": ["H", "Si"], "n_atoms": 9, "bond_type": "covalent",
     "category": "chladni_priority",
     "resonance_score": 0.839,
     "synthesis_note": "Hydrogen in silicon 8-fold geometry — semiconductor cage"},

    {"id": "I03", "name": "Ca₅Zn₅ Pentagonal Alloy",
     "freq": 2160.0, "geometry": "5fold_decahedral",
     "elements": ["Ca", "Zn"], "n_atoms": 10, "bond_type": "metallic",
     "category": "chladni_priority",
     "resonance_score": 0.837,
     "synthesis_note": "5th harmonic (2160 Hz) — 5-fold symmetry match"},

    {"id": "I04", "name": "HMg₈ Magnesium Cage",
     "freq": 432.0, "geometry": "8fold_cage",
     "elements": ["H", "Mg"], "n_atoms": 9, "bond_type": "ionic",
     "category": "chladni_priority",
     "resonance_score": 0.835,
     "synthesis_note": "Hydrogen in magnesium 8-fold cage at fundamental"},

    {"id": "I05", "name": "O₈He₂ Oxygen-Helium Cluster",
     "freq": 432.0, "geometry": "8fold_cluster",
     "elements": ["O", "He"], "n_atoms": 10, "bond_type": "van_der_waals",
     "category": "chladni_priority",
     "resonance_score": 0.811,
     "synthesis_note": "Oxygen 8-fold with helium stabilizers"},

    {"id": "I06", "name": "B₂C₈ Boron-Carbon Cage",
     "freq": 432.0, "geometry": "8fold_cage",
     "elements": ["B", "C"], "n_atoms": 10, "bond_type": "covalent",
     "category": "chladni_priority",
     "resonance_score": 0.797,
     "synthesis_note": "Boron-carbon 8-fold cage — ultra-hard potential"},

    {"id": "I07", "name": "F₅Br₅ Halogen Decamer",
     "freq": 2160.0, "geometry": "5fold_ring",
     "elements": ["F", "Br"], "n_atoms": 10, "bond_type": "covalent",
     "category": "chladni_priority",
     "resonance_score": 0.820,
     "synthesis_note": "5th harmonic — halogen pentagonal ring"},

    {"id": "I08", "name": "Be₃P₇ Beryllium Phosphide",
     "freq": 3024.0, "geometry": "7fold_heptagonal",
     "elements": ["Be", "P"], "n_atoms": 10, "bond_type": "covalent",
     "category": "chladni_priority",
     "resonance_score": 0.789,
     "synthesis_note": "7th harmonic (3024 Hz) — 7-fold symmetry match"},

    {"id": "I09", "name": "CCu₈ Carbon-Copper Cage",
     "freq": 432.0, "geometry": "8fold_cage",
     "elements": ["C", "Cu"], "n_atoms": 9, "bond_type": "metallic",
     "category": "chladni_priority",
     "resonance_score": 0.785,
     "synthesis_note": "Carbon-centered copper cage — conductive cage compound"},

    {"id": "I10", "name": "MgF₈ Magnesium Fluoride Cage",
     "freq": 432.0, "geometry": "8fold_cage",
     "elements": ["Mg", "F"], "n_atoms": 9, "bond_type": "ionic",
     "category": "chladni_priority",
     "resonance_score": 0.782,
     "synthesis_note": "Magnesium in fluoride 8-fold cage — optical material"},

    {"id": "I11", "name": "Dual-Polarity Carbon Ring",
     "freq": 864.0, "geometry": "ring_dual_polarity",
     "elements": ["C"], "n_atoms": 12, "bond_type": "sp2",
     "category": "chladni_priority",
     "resonance_score": 0.830,
     "synthesis_note": "2nd harmonic — dual electron polarity ring structure"},

    {"id": "I12", "name": "Void Resonance Compound",
     "freq": 432.0, "geometry": "void_resonance",
     "elements": ["C", "N", "O", "H"], "n_atoms": 19, "bond_type": "mixed",
     "category": "chladni_priority",
     "resonance_score": 0.850,
     "synthesis_note": "19-atom compound at exact 432 Hz — the Void Resonance"},
]


# ================================================================
# CATEGORY J: CYMATICS BRIDGE — ADVANCED APPLICATIONS (J1-J10)
# Spacecraft, submarine, stealth, and quantum shielding materials
# ================================================================

ADVANCED_APPLICATION_COMPOUNDS = [
    {"id": "J01", "name": "Spacecraft Heat Tile",
     "freq": 1530.0, "geometry": "fractal_cubic",
     "elements": ["Ti", "W", "C"], "n_atoms": 48, "bond_type": "covalent",
     "category": "advanced_application",
     "synthesis_note": "Ti-W Carbide at 1530 Hz + 3060/4590/6120 Hz harmonics"},

    {"id": "J02", "name": "Quantum Shield Alloy",
     "freq": 4036.7, "geometry": "multidimensional",
     "elements": ["U", "Pu"], "n_atoms": 32, "bond_type": "metallic",
     "category": "advanced_application",
     "synthesis_note": "U-Pu quantum alloy — radiation shielding via frequency"},

    {"id": "J03", "name": "Stealth Coating Layer",
     "freq": 1247.3, "geometry": "fcc_absorbing",
     "elements": ["Cu", "Ni", "Zn"], "n_atoms": 54, "bond_type": "metallic",
     "category": "advanced_application",
     "synthesis_note": "Frequency-absorbing layered alloy — radar stealth"},

    {"id": "J04", "name": "Deep Pressure Hull",
     "freq": 1350.0, "geometry": "fcc_dense",
     "elements": ["Ni", "Co", "W"], "n_atoms": 48, "bond_type": "metallic",
     "category": "advanced_application",
     "synthesis_note": "Ni-Co-W at extreme pressure resistance geometry"},

    {"id": "J05", "name": "Mycelium Radiation Absorber",
     "freq": 72.0, "geometry": "branching_fractal",
     "elements": ["C", "H", "N", "O"], "n_atoms": 60, "bond_type": "polymer",
     "category": "advanced_application",
     "synthesis_note": "Mycelium network at 72 Hz — radiation funnel void"},

    {"id": "J06", "name": "Silk-Tempered Pin Alloy",
     "freq": 216.0, "geometry": "beta_sheet_metallic",
     "elements": ["Zn", "Fe", "C"], "n_atoms": 36, "bond_type": "mixed",
     "category": "advanced_application",
     "synthesis_note": "Machine 4000 pin material — silk-tempered zinc-coated"},

    {"id": "J07", "name": "Ghost Internet Conductor",
     "freq": 432.0, "geometry": "cylindrical_waveguide",
     "elements": ["Cu", "C"], "n_atoms": 40, "bond_type": "metallic",
     "category": "advanced_application",
     "synthesis_note": "Sound-vibration conductor for ghost internet transmission"},

    {"id": "J08", "name": "Air-Thickness Modulator",
     "freq": 108.0, "geometry": "triple_helix_air",
     "elements": ["N", "O"], "n_atoms": 28, "bond_type": "covalent",
     "category": "advanced_application",
     "synthesis_note": "108 Hz mesh marker — alters air thickness via vibration"},

    {"id": "J09", "name": "Void Funnel Carbon",
     "freq": 432.0, "geometry": "funnel_toroidal",
     "elements": ["C"], "n_atoms": 48, "bond_type": "sp2",
     "category": "advanced_application",
     "synthesis_note": "Funnel of voids — radiation absorption geometry"},

    {"id": "J10", "name": "Resonance Badge Piezo",
     "freq": 540.0, "geometry": "perovskite_piezo",
     "elements": ["Ba", "Ti", "O"], "n_atoms": 40, "bond_type": "ionic",
     "category": "advanced_application",
     "synthesis_note": "Resonance badge material — senses pheromones/betelectrics"},
]


# ================================================================
# COMBINED EXTENSION
# ================================================================

ALL_NEW_COMPOUNDS = CYMATICS_BRIDGE_COMPOUNDS + CHLADNI_PRIORITY_COMPOUNDS + ADVANCED_APPLICATION_COMPOUNDS

# Category summary
NEW_CATEGORIES = {
    "H": "Cymatics Bridge — Temple Pillar Geometries (H01-H20)",
    "I": "Chladni Priority — Highest Resonance Candidates (I01-I12)",
    "J": "Advanced Applications — Spacecraft/Stealth/Quantum (J01-J10)",
}

assert len(ALL_NEW_COMPOUNDS) == 42, f"Expected 42 new compounds, got {len(ALL_NEW_COMPOUNDS)}"

if __name__ == "__main__":
    print(f"CYMATICS BRIDGE COMPOUND EXTENSION")
    print(f"Total new compounds: {len(ALL_NEW_COMPOUNDS)}")
    print(f"\nNew Categories:")
    for cat_id, desc in NEW_CATEGORIES.items():
        count = sum(1 for c in ALL_NEW_COMPOUNDS if c['id'].startswith(cat_id))
        print(f"  {cat_id}: {desc} ({count} compounds)")
    print(f"\nFrequency range: {min(c['freq'] for c in ALL_NEW_COMPOUNDS)} Hz — {max(c['freq'] for c in ALL_NEW_COMPOUNDS)} Hz")
    print(f"\nHighest resonance scores (Chladni priority):")
    for c in sorted(CHLADNI_PRIORITY_COMPOUNDS, key=lambda x: x.get('resonance_score', 0), reverse=True)[:5]:
        print(f"  {c['id']} {c['name']}: {c['resonance_score']:.3f} @ {c['freq']} Hz")
