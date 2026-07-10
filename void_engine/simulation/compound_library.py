"""
PROJECT VOID — Compound Library
================================

108 compounds organized by category, each with:
- Frequency (Hz) — derived from 432 Hz harmonic system
- Geometry — the target molecular geometry
- Elements — constituent atoms
- Category — application domain

This is the Frequency Periodic Table.
"""

COMPOUNDS = [
    # ================================================================
    # CATEGORY A: LIGHTWEIGHT STRUCTURAL COMPOUNDS (A1-A15)
    # ================================================================
    {"id": "A01", "name": "C-H-N-O Polymer", "freq": 326.5, "geometry": "hexagonal_spiral", "elements": ["C", "H", "N", "O"], "n_atoms": 40, "bond_type": "sp2", "category": "lightweight_structural"},
    {"id": "A02", "name": "Si-C-N Ceramic", "freq": 378.2, "geometry": "cubic_tetrahedral", "elements": ["Si", "C", "N"], "n_atoms": 36, "bond_type": "sp3", "category": "lightweight_structural"},
    {"id": "A03", "name": "B-N Nanotube", "freq": 432.0, "geometry": "cylindrical_hexagonal", "elements": ["B", "N"], "n_atoms": 48, "bond_type": "sp2", "category": "lightweight_structural"},
    {"id": "A04", "name": "C-Si Carbide Fiber", "freq": 345.6, "geometry": "linear_tetrahedral", "elements": ["C", "Si"], "n_atoms": 32, "bond_type": "sp3", "category": "lightweight_structural"},
    {"id": "A05", "name": "Al-O-N Oxynitride", "freq": 389.0, "geometry": "spinel_cubic", "elements": ["Al", "O", "N"], "n_atoms": 42, "bond_type": "ionic", "category": "lightweight_structural"},
    {"id": "A06", "name": "C-B Boron Carbide", "freq": 410.4, "geometry": "rhombohedral", "elements": ["C", "B"], "n_atoms": 45, "bond_type": "covalent", "category": "lightweight_structural"},
    {"id": "A07", "name": "Mg-Al Spinel", "freq": 356.8, "geometry": "cubic_spinel", "elements": ["Mg", "Al", "O"], "n_atoms": 56, "bond_type": "ionic", "category": "lightweight_structural"},
    {"id": "A08", "name": "Ti-Al Intermetallic", "freq": 367.2, "geometry": "tetragonal", "elements": ["Ti", "Al"], "n_atoms": 32, "bond_type": "metallic", "category": "lightweight_structural"},
    {"id": "A09", "name": "C Aerogel Matrix", "freq": 216.0, "geometry": "fractal_network", "elements": ["C"], "n_atoms": 60, "bond_type": "sp2_sp3", "category": "lightweight_structural"},
    {"id": "A10", "name": "Si-O Aerogel", "freq": 288.0, "geometry": "amorphous_network", "elements": ["Si", "O"], "n_atoms": 48, "bond_type": "covalent", "category": "lightweight_structural"},
    {"id": "A11", "name": "Al-B Boride", "freq": 399.6, "geometry": "hexagonal_layered", "elements": ["Al", "B"], "n_atoms": 36, "bond_type": "covalent", "category": "lightweight_structural"},
    {"id": "A12", "name": "C-N Nitride Film", "freq": 421.2, "geometry": "beta_hexagonal", "elements": ["C", "N"], "n_atoms": 40, "bond_type": "sp3", "category": "lightweight_structural"},
    {"id": "A13", "name": "Be-Al Alloy", "freq": 334.8, "geometry": "hcp", "elements": ["Be", "Al"], "n_atoms": 36, "bond_type": "metallic", "category": "lightweight_structural"},
    {"id": "A14", "name": "Li-Al Hydride", "freq": 302.4, "geometry": "monoclinic", "elements": ["Li", "Al", "H"], "n_atoms": 48, "bond_type": "ionic", "category": "lightweight_structural"},
    {"id": "A15", "name": "Mg-B Diboride", "freq": 378.0, "geometry": "hexagonal_AlB2", "elements": ["Mg", "B"], "n_atoms": 36, "bond_type": "covalent", "category": "lightweight_structural"},

    # ================================================================
    # CATEGORY B: HIGH-STRENGTH ALLOYS (B1-B15)
    # ================================================================
    {"id": "B01", "name": "Fe-Cu-Zn Alloy", "freq": 1217.6, "geometry": "bcc_complex", "elements": ["Fe", "Cu", "Zn"], "n_atoms": 54, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B02", "name": "Ti-V-Cr Superalloy", "freq": 1296.0, "geometry": "bcc_ordered", "elements": ["Ti", "V", "Cr"], "n_atoms": 54, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B03", "name": "Ni-Co-W Alloy", "freq": 1350.0, "geometry": "fcc_complex", "elements": ["Ni", "Co", "W"], "n_atoms": 48, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B04", "name": "Fe-Ni-Mo Steel", "freq": 1188.0, "geometry": "martensite", "elements": ["Fe", "Ni", "Mo"], "n_atoms": 54, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B05", "name": "Ti-Nb-Zr Shape Memory", "freq": 1242.0, "geometry": "bcc_to_hcp", "elements": ["Ti", "Nb", "Zr"], "n_atoms": 48, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B06", "name": "Co-Cr-Mo Bioalloy", "freq": 1274.4, "geometry": "fcc_hcp", "elements": ["Co", "Cr", "Mo"], "n_atoms": 48, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B07", "name": "Cu-Ni-Zn Stealth", "freq": 1247.3, "geometry": "fcc_layered", "elements": ["Cu", "Ni", "Zn"], "n_atoms": 54, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B08", "name": "Fe-Mn-Si Austenite", "freq": 1166.4, "geometry": "fcc_austenite", "elements": ["Fe", "Mn", "Si"], "n_atoms": 54, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B09", "name": "Nb-Ti-Al Turbine", "freq": 1382.4, "geometry": "L12_ordered", "elements": ["Nb", "Ti", "Al"], "n_atoms": 48, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B10", "name": "W-Re Refractory", "freq": 1512.0, "geometry": "bcc_solid_solution", "elements": ["W", "Re"], "n_atoms": 32, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B11", "name": "Zr-Cu-Al Metallic Glass", "freq": 1123.2, "geometry": "amorphous_icosahedral", "elements": ["Zr", "Cu", "Al"], "n_atoms": 60, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B12", "name": "Fe-B Amorphous", "freq": 1080.0, "geometry": "amorphous_dense", "elements": ["Fe", "B"], "n_atoms": 50, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B13", "name": "Ni-Al Intermetallic", "freq": 1296.0, "geometry": "L12_cubic", "elements": ["Ni", "Al"], "n_atoms": 32, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B14", "name": "Ti-Mo-V Beta", "freq": 1328.4, "geometry": "bcc_beta", "elements": ["Ti", "Mo", "V"], "n_atoms": 48, "bond_type": "metallic", "category": "high_strength_alloy"},
    {"id": "B15", "name": "Cr-Mn-Fe-Co-Ni HEA", "freq": 1404.0, "geometry": "fcc_random", "elements": ["Cr", "Mn", "Fe", "Co", "Ni"], "n_atoms": 50, "bond_type": "metallic", "category": "high_strength_alloy"},

    # ================================================================
    # CATEGORY C: THERMAL-RESISTANT MATERIALS (C1-C15)
    # ================================================================
    {"id": "C01", "name": "Ti-W Carbide", "freq": 1530.0, "geometry": "cubic_rocksalt", "elements": ["Ti", "W", "C"], "n_atoms": 48, "bond_type": "covalent", "category": "thermal_resistant"},
    {"id": "C02", "name": "Hf-C Carbide", "freq": 1620.0, "geometry": "rocksalt", "elements": ["Hf", "C"], "n_atoms": 32, "bond_type": "covalent", "category": "thermal_resistant"},
    {"id": "C03", "name": "Ta-Hf-C Ternary", "freq": 1728.0, "geometry": "rocksalt_ordered", "elements": ["Ta", "Hf", "C"], "n_atoms": 48, "bond_type": "covalent", "category": "thermal_resistant"},
    {"id": "C04", "name": "Zr-B2 Diboride", "freq": 1458.0, "geometry": "hexagonal_AlB2", "elements": ["Zr", "B"], "n_atoms": 36, "bond_type": "covalent", "category": "thermal_resistant"},
    {"id": "C05", "name": "Si-C Moissanite", "freq": 1566.0, "geometry": "wurtzite", "elements": ["Si", "C"], "n_atoms": 32, "bond_type": "sp3", "category": "thermal_resistant"},
    {"id": "C06", "name": "Al2O3 Corundum", "freq": 1440.0, "geometry": "rhombohedral_corundum", "elements": ["Al", "O"], "n_atoms": 40, "bond_type": "ionic", "category": "thermal_resistant"},
    {"id": "C07", "name": "Y2O3-ZrO2 YSZ", "freq": 1494.0, "geometry": "fluorite_cubic", "elements": ["Y", "Zr", "O"], "n_atoms": 48, "bond_type": "ionic", "category": "thermal_resistant"},
    {"id": "C08", "name": "MgO Periclase", "freq": 1404.0, "geometry": "rocksalt_simple", "elements": ["Mg", "O"], "n_atoms": 32, "bond_type": "ionic", "category": "thermal_resistant"},
    {"id": "C09", "name": "W Tungsten Pure", "freq": 1836.0, "geometry": "bcc_pure", "elements": ["W"], "n_atoms": 32, "bond_type": "metallic", "category": "thermal_resistant"},
    {"id": "C10", "name": "Re Rhenium Pure", "freq": 1782.0, "geometry": "hcp_pure", "elements": ["Re"], "n_atoms": 32, "bond_type": "metallic", "category": "thermal_resistant"},
    {"id": "C11", "name": "Si3N4 Nitride", "freq": 1512.0, "geometry": "hexagonal_Si3N4", "elements": ["Si", "N"], "n_atoms": 42, "bond_type": "covalent", "category": "thermal_resistant"},
    {"id": "C12", "name": "BN Cubic", "freq": 1674.0, "geometry": "zinc_blende", "elements": ["B", "N"], "n_atoms": 32, "bond_type": "sp3", "category": "thermal_resistant"},
    {"id": "C13", "name": "TiN Nitride", "freq": 1548.0, "geometry": "rocksalt_TiN", "elements": ["Ti", "N"], "n_atoms": 32, "bond_type": "covalent", "category": "thermal_resistant"},
    {"id": "C14", "name": "Cr2O3 Chromia", "freq": 1476.0, "geometry": "corundum", "elements": ["Cr", "O"], "n_atoms": 40, "bond_type": "ionic", "category": "thermal_resistant"},
    {"id": "C15", "name": "Mo-Si2 Silicide", "freq": 1602.0, "geometry": "tetragonal_C11b", "elements": ["Mo", "Si"], "n_atoms": 36, "bond_type": "covalent", "category": "thermal_resistant"},

    # ================================================================
    # CATEGORY D: EXOTIC/QUANTUM MATERIALS (D1-D15)
    # ================================================================
    {"id": "D01", "name": "Gd-U Superconductor", "freq": 3152.1, "geometry": "perovskite_layered", "elements": ["Gd", "U", "O"], "n_atoms": 40, "bond_type": "mixed", "category": "exotic_quantum"},
    {"id": "D02", "name": "U-Pu Quantum Alloy", "freq": 4036.7, "geometry": "multidimensional", "elements": ["U", "Pu"], "n_atoms": 32, "bond_type": "metallic", "category": "exotic_quantum"},
    {"id": "D03", "name": "Y-Ba-Cu-O YBCO", "freq": 2592.0, "geometry": "perovskite_ortho", "elements": ["Y", "Ba", "Cu", "O"], "n_atoms": 52, "bond_type": "mixed", "category": "exotic_quantum"},
    {"id": "D04", "name": "Bi-Sr-Ca-Cu-O BSCCO", "freq": 2808.0, "geometry": "perovskite_tetra", "elements": ["Bi", "Sr", "Ca", "Cu", "O"], "n_atoms": 60, "bond_type": "mixed", "category": "exotic_quantum"},
    {"id": "D05", "name": "Nb-Sn A15", "freq": 2376.0, "geometry": "A15_cubic", "elements": ["Nb", "Sn"], "n_atoms": 32, "bond_type": "metallic", "category": "exotic_quantum"},
    {"id": "D06", "name": "MgB2 Diboride SC", "freq": 2160.0, "geometry": "hexagonal_SC", "elements": ["Mg", "B"], "n_atoms": 36, "bond_type": "covalent", "category": "exotic_quantum"},
    {"id": "D07", "name": "Fe-Se Chalcogenide", "freq": 2268.0, "geometry": "tetragonal_PbO", "elements": ["Fe", "Se"], "n_atoms": 32, "bond_type": "mixed", "category": "exotic_quantum"},
    {"id": "D08", "name": "Bi2Te3 Topological", "freq": 2484.0, "geometry": "rhombohedral_layered", "elements": ["Bi", "Te"], "n_atoms": 40, "bond_type": "covalent", "category": "exotic_quantum"},
    {"id": "D09", "name": "Cd-As Dirac Semimetal", "freq": 2700.0, "geometry": "tetragonal_I41", "elements": ["Cd", "As"], "n_atoms": 32, "bond_type": "covalent", "category": "exotic_quantum"},
    {"id": "D10", "name": "WTe2 Weyl Semimetal", "freq": 2916.0, "geometry": "orthorhombic_Td", "elements": ["W", "Te"], "n_atoms": 36, "bond_type": "covalent", "category": "exotic_quantum"},
    {"id": "D11", "name": "SmB6 Kondo Insulator", "freq": 3024.0, "geometry": "cubic_CsCl", "elements": ["Sm", "B"], "n_atoms": 42, "bond_type": "mixed", "category": "exotic_quantum"},
    {"id": "D12", "name": "TaAs Weyl", "freq": 3132.0, "geometry": "tetragonal_I41md", "elements": ["Ta", "As"], "n_atoms": 32, "bond_type": "covalent", "category": "exotic_quantum"},
    {"id": "D13", "name": "Graphene Quantum Dot", "freq": 5184.0, "geometry": "hexagonal_confined", "elements": ["C"], "n_atoms": 42, "bond_type": "sp2", "category": "exotic_quantum"},
    {"id": "D14", "name": "MoS2 Monolayer", "freq": 2052.0, "geometry": "hexagonal_2H", "elements": ["Mo", "S"], "n_atoms": 36, "bond_type": "covalent", "category": "exotic_quantum"},
    {"id": "D15", "name": "h-BN Monolayer", "freq": 1944.0, "geometry": "hexagonal_flat", "elements": ["B", "N"], "n_atoms": 36, "bond_type": "sp2", "category": "exotic_quantum"},

    # ================================================================
    # CATEGORY E: BIOLOGICAL/ORGANIC COMPOUNDS (E1-E15)
    # ================================================================
    {"id": "E01", "name": "Chitin Helix", "freq": 144.0, "geometry": "helical", "elements": ["C", "H", "N", "O"], "n_atoms": 30, "bond_type": "polymer", "category": "biological"},
    {"id": "E02", "name": "Collagen Triple Helix", "freq": 108.0, "geometry": "triple_helix", "elements": ["C", "H", "N", "O"], "n_atoms": 45, "bond_type": "polymer", "category": "biological"},
    {"id": "E03", "name": "Keratin Alpha Helix", "freq": 162.0, "geometry": "alpha_helix", "elements": ["C", "H", "N", "O", "S"], "n_atoms": 36, "bond_type": "polymer", "category": "biological"},
    {"id": "E04", "name": "Silk Fibroin Beta Sheet", "freq": 216.0, "geometry": "beta_sheet", "elements": ["C", "H", "N", "O"], "n_atoms": 48, "bond_type": "polymer", "category": "biological"},
    {"id": "E05", "name": "Cellulose Chain", "freq": 180.0, "geometry": "linear_chain", "elements": ["C", "H", "O"], "n_atoms": 42, "bond_type": "polymer", "category": "biological"},
    {"id": "E06", "name": "DNA Double Helix", "freq": 432.0, "geometry": "double_helix", "elements": ["C", "H", "N", "O", "P"], "n_atoms": 60, "bond_type": "polymer", "category": "biological"},
    {"id": "E07", "name": "Melanin Polymer", "freq": 288.0, "geometry": "stacked_planar", "elements": ["C", "H", "N", "O"], "n_atoms": 40, "bond_type": "conjugated", "category": "biological"},
    {"id": "E08", "name": "Spider Silk Crystallite", "freq": 252.0, "geometry": "beta_nanocrystal", "elements": ["C", "H", "N", "O"], "n_atoms": 48, "bond_type": "polymer", "category": "biological"},
    {"id": "E09", "name": "Lignin Network", "freq": 198.0, "geometry": "3d_network", "elements": ["C", "H", "O"], "n_atoms": 50, "bond_type": "polymer", "category": "biological"},
    {"id": "E10", "name": "Hemoglobin Heme", "freq": 324.0, "geometry": "porphyrin_planar", "elements": ["C", "H", "N", "Fe"], "n_atoms": 44, "bond_type": "coordination", "category": "biological"},
    {"id": "E11", "name": "Chlorophyll Ring", "freq": 360.0, "geometry": "porphyrin_Mg", "elements": ["C", "H", "N", "O", "Mg"], "n_atoms": 48, "bond_type": "coordination", "category": "biological"},
    {"id": "E12", "name": "ATP Molecule", "freq": 396.0, "geometry": "nucleotide_tri", "elements": ["C", "H", "N", "O", "P"], "n_atoms": 47, "bond_type": "covalent", "category": "biological"},
    {"id": "E13", "name": "Mycelium Network Node", "freq": 72.0, "geometry": "branching_fractal", "elements": ["C", "H", "N", "O"], "n_atoms": 36, "bond_type": "polymer", "category": "biological"},
    {"id": "E14", "name": "Nacre Aragonite Layer", "freq": 270.0, "geometry": "orthorhombic_layered", "elements": ["Ca", "C", "O"], "n_atoms": 40, "bond_type": "ionic", "category": "biological"},
    {"id": "E15", "name": "Elastin Random Coil", "freq": 126.0, "geometry": "random_coil", "elements": ["C", "H", "N", "O"], "n_atoms": 36, "bond_type": "polymer", "category": "biological"},

    # ================================================================
    # CATEGORY F: ENERGY MATERIALS (F1-F15)
    # ================================================================
    {"id": "F01", "name": "LiFePO4 Cathode", "freq": 864.0, "geometry": "olivine", "elements": ["Li", "Fe", "P", "O"], "n_atoms": 48, "bond_type": "ionic", "category": "energy"},
    {"id": "F02", "name": "Li-Co-O Layered", "freq": 918.0, "geometry": "layered_R3m", "elements": ["Li", "Co", "O"], "n_atoms": 36, "bond_type": "ionic", "category": "energy"},
    {"id": "F03", "name": "Na-ion Prussian Blue", "freq": 756.0, "geometry": "cubic_framework", "elements": ["Na", "Fe", "C", "N"], "n_atoms": 52, "bond_type": "mixed", "category": "energy"},
    {"id": "F04", "name": "Si Anode Nanoparticle", "freq": 810.0, "geometry": "diamond_cubic", "elements": ["Si"], "n_atoms": 32, "bond_type": "covalent", "category": "energy"},
    {"id": "F05", "name": "TiO2 Anatase", "freq": 972.0, "geometry": "tetragonal_anatase", "elements": ["Ti", "O"], "n_atoms": 36, "bond_type": "ionic", "category": "energy"},
    {"id": "F06", "name": "Perovskite Solar CH3NH3PbI3", "freq": 1080.0, "geometry": "perovskite_cubic", "elements": ["C", "N", "H", "Pb", "I"], "n_atoms": 48, "bond_type": "mixed", "category": "energy"},
    {"id": "F07", "name": "CdTe Solar", "freq": 1026.0, "geometry": "zinc_blende_CdTe", "elements": ["Cd", "Te"], "n_atoms": 32, "bond_type": "covalent", "category": "energy"},
    {"id": "F08", "name": "GaAs Solar", "freq": 1134.0, "geometry": "zinc_blende_GaAs", "elements": ["Ga", "As"], "n_atoms": 32, "bond_type": "covalent", "category": "energy"},
    {"id": "F09", "name": "V2O5 Vanadium Oxide", "freq": 702.0, "geometry": "orthorhombic_layered", "elements": ["V", "O"], "n_atoms": 42, "bond_type": "ionic", "category": "energy"},
    {"id": "F10", "name": "MnO2 Birnessite", "freq": 648.0, "geometry": "layered_birnessite", "elements": ["Mn", "O"], "n_atoms": 36, "bond_type": "ionic", "category": "energy"},
    {"id": "F11", "name": "Solid Electrolyte Li7La3Zr2O12", "freq": 1188.0, "geometry": "garnet_cubic", "elements": ["Li", "La", "Zr", "O"], "n_atoms": 56, "bond_type": "ionic", "category": "energy"},
    {"id": "F12", "name": "Pt Catalyst Nanoparticle", "freq": 1296.0, "geometry": "fcc_truncated_octa", "elements": ["Pt"], "n_atoms": 38, "bond_type": "metallic", "category": "energy"},
    {"id": "F13", "name": "ZnO Piezoelectric", "freq": 594.0, "geometry": "wurtzite_ZnO", "elements": ["Zn", "O"], "n_atoms": 32, "bond_type": "ionic", "category": "energy"},
    {"id": "F14", "name": "BaTiO3 Ferroelectric", "freq": 540.0, "geometry": "perovskite_tetragonal", "elements": ["Ba", "Ti", "O"], "n_atoms": 40, "bond_type": "ionic", "category": "energy"},
    {"id": "F15", "name": "Graphite Anode", "freq": 486.0, "geometry": "hexagonal_layered_AB", "elements": ["C"], "n_atoms": 48, "bond_type": "sp2", "category": "energy"},

    # ================================================================
    # CATEGORY G: FREQUENCY-SPECIFIC VOID COMPOUNDS (G1-G18)
    # ================================================================
    {"id": "G01", "name": "Void Graphene (Base)", "freq": 432.0, "geometry": "hexagonal", "elements": ["C"], "n_atoms": 50, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G02", "name": "Void Water (6th)", "freq": 2592.0, "geometry": "icosahedral", "elements": ["O", "H"], "n_atoms": 36, "bond_type": "hydrogen", "category": "void_frequency"},
    {"id": "G03", "name": "Void Shell (12th)", "freq": 5184.0, "geometry": "geodesic_C60", "elements": ["C"], "n_atoms": 60, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G04", "name": "Void Chitin (1/3)", "freq": 144.0, "geometry": "helical", "elements": ["C", "H", "N", "O"], "n_atoms": 30, "bond_type": "polymer", "category": "void_frequency"},
    {"id": "G05", "name": "Void Diamond (2nd)", "freq": 864.0, "geometry": "diamond_cubic", "elements": ["C"], "n_atoms": 32, "bond_type": "sp3", "category": "void_frequency"},
    {"id": "G06", "name": "Void Nanotube (3rd)", "freq": 1296.0, "geometry": "cylindrical", "elements": ["C"], "n_atoms": 48, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G07", "name": "Void Carbyne (4th)", "freq": 1728.0, "geometry": "linear_chain", "elements": ["C"], "n_atoms": 24, "bond_type": "sp", "category": "void_frequency"},
    {"id": "G08", "name": "Void Lonsdaleite (5th)", "freq": 2160.0, "geometry": "hexagonal_diamond", "elements": ["C"], "n_atoms": 32, "bond_type": "sp3", "category": "void_frequency"},
    {"id": "G09", "name": "Void Schwarzite (7th)", "freq": 3024.0, "geometry": "negative_curvature", "elements": ["C"], "n_atoms": 48, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G10", "name": "Void Graphyne (8th)", "freq": 3456.0, "geometry": "hexagonal_acetylenic", "elements": ["C"], "n_atoms": 36, "bond_type": "sp_sp2", "category": "void_frequency"},
    {"id": "G11", "name": "Void Pentacene (9th)", "freq": 3888.0, "geometry": "planar_acene", "elements": ["C", "H"], "n_atoms": 36, "bond_type": "conjugated", "category": "void_frequency"},
    {"id": "G12", "name": "Void C240 (10th)", "freq": 4320.0, "geometry": "icosahedral_giant", "elements": ["C"], "n_atoms": 60, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G13", "name": "Void Toroid (11th)", "freq": 4752.0, "geometry": "toroidal", "elements": ["C"], "n_atoms": 48, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G14", "name": "Void Helicene (13th)", "freq": 5616.0, "geometry": "helical_aromatic", "elements": ["C", "H"], "n_atoms": 42, "bond_type": "conjugated", "category": "void_frequency"},
    {"id": "G15", "name": "Void Trefoil (14th)", "freq": 6048.0, "geometry": "trefoil_knot", "elements": ["C"], "n_atoms": 36, "bond_type": "sp2", "category": "void_frequency"},
    {"id": "G16", "name": "Void Cage (15th)", "freq": 6480.0, "geometry": "dodecahedral", "elements": ["C", "H"], "n_atoms": 40, "bond_type": "sp3", "category": "void_frequency"},
    {"id": "G17", "name": "Void Prism (16th)", "freq": 6912.0, "geometry": "prismatic", "elements": ["C", "B", "N"], "n_atoms": 36, "bond_type": "mixed", "category": "void_frequency"},
    {"id": "G18", "name": "Void Tesseract (19th)", "freq": 8208.0, "geometry": "hypercubic_projection", "elements": ["C"], "n_atoms": 48, "bond_type": "sp2", "category": "void_frequency"},
]

# Total: 108 compounds
assert len(COMPOUNDS) == 108, f"Expected 108 compounds, got {len(COMPOUNDS)}"

# Category summary
CATEGORIES = {
    "A": "Lightweight Structural (A01-A15)",
    "B": "High-Strength Alloys (B01-B15)",
    "C": "Thermal-Resistant (C01-C15)",
    "D": "Exotic/Quantum (D01-D15)",
    "E": "Biological/Organic (E01-E15)",
    "F": "Energy Materials (F01-F15)",
    "G": "Void Frequency-Specific (G01-G18)",
}

if __name__ == "__main__":
    print(f"PROJECT VOID — Frequency Periodic Table")
    print(f"Total compounds: {len(COMPOUNDS)}")
    print(f"\nCategories:")
    for cat_id, desc in CATEGORIES.items():
        count = sum(1 for c in COMPOUNDS if c['id'].startswith(cat_id))
        print(f"  {cat_id}: {desc} ({count} compounds)")
    print(f"\nFrequency range: {min(c['freq'] for c in COMPOUNDS)} Hz — {max(c['freq'] for c in COMPOUNDS)} Hz")
    print(f"All derived from 432 Hz base frequency")
