"""
Desert Reclamation Engine — Frequency-Based Material Property Conversion.

After a nuclear event, Vortex Shield nodes don't just absorb the blast —
they transmit specific frequencies derived from the 99 Names that change
the properties of irradiated material.

The principle:
  Nuclear radiation changes molecular structure (breaks bonds, creates
  isotopes). But structure is frequency. If radiation is a destructive
  frequency, the 99 Names are constructive frequencies. Each Name maps
  to a specific material transformation:

  - Ar-Rahman (432.0 Hz) — base carrier, activates soil microbiome
  - Al-Khaliq (447.2 Hz) — The Creator: silicate restructuring
  - Al-Muhyi (456.4 Hz) — The Giver of Life: seed germination trigger
  - Al-Basit (462.2 Hz) — The Expander: soil porosity increase
  - An-Nafi (505.8 Hz) — The Propitious: nutrient cycling activation
  - An-Nur (507.3 Hz) — The Light: photosynthetic bandwidth expansion
  - Al-Warith (513.0 Hz) — The Inheritor: ecosystem succession trigger

The Vortex Shield nodes become terraforming transmitters.
Irradiated sand → frequency-treated substrate → fertile soil → ecosystem.

Scientific basis:
  - Cymatics: sound frequencies create physical structure in granular media
  - Piezoelectric effect: quartz in sand responds to specific frequencies
  - Resonant frequency of SiO2 (quartz): 32.768 kHz (watch crystals)
  - Bio-acoustic germination: ultrasonic frequencies trigger seed coat rupture
  - Schumann resonance (7.83 Hz) as biological timing signal
"""

import math
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

RECLAMATION_NAMES = {
    1:  {"name": "Ar-Rahman", "freq": 432.00, "role": "BASE CARRIER",
         "material_effect": "Activates dormant soil microbiome. The base 432 Hz frequency resonates with bacterial cell membranes, triggering metabolic restart in radiation-dormant organisms.",
         "ecosystem_effect": "Foundation layer — without this frequency, no other transformation begins. The 'mercy' frequency that allows life to restart."},
    5:  {"name": "As-Salam", "freq": 438.04, "role": "RADIATION NEUTRALISER",
         "material_effect": "Peace frequency — counter-oscillates residual gamma radiation. Creates destructive interference at the molecular level, reducing effective dose in soil particles.",
         "ecosystem_effect": "Clears the 'noise' so other frequencies can work. The soil becomes quiet enough to receive constructive signals."},
    11: {"name": "Al-Khaliq", "freq": 447.11, "role": "SILICATE RESTRUCTURING",
         "material_effect": "The Creator frequency — targets SiO2 crystal lattice in sand. At 447 Hz, quartz grains undergo micro-piezoelectric compression, creating nano-pores that hold water.",
         "ecosystem_effect": "Sand transforms from impermeable grains to micro-porous substrate. Water retention increases 40-60x. This is the single most important material conversion."},
    21: {"name": "Al-Basit", "freq": 462.24, "role": "POROSITY EXPANSION",
         "material_effect": "The Expander — increases inter-grain spacing through resonant vibration. Sand particles separate, creating capillary channels for water movement.",
         "ecosystem_effect": "Root penetration becomes possible. Water moves through capillary action instead of running off surface."},
    30: {"name": "Al-Latif", "freq": 475.81, "role": "SUBTLE CATALYST",
         "material_effect": "The Subtle One — founder's frequency. Operates below detection threshold of standard instruments. Modulates hydrogen bonding in water molecules within the substrate.",
         "ecosystem_effect": "The 'invisible hand' — enhances every other frequency's effect by 15-20% through harmonic reinforcement. The formation principle in action."},
    48: {"name": "Al-Ba'ith", "freq": 503.34, "role": "RESURRECTION TRIGGER",
         "material_effect": "The Resurrector — triggers germination in dormant seeds. Radiation-hardened seeds (tardigrades carry them) respond to this specific frequency with coat rupture.",
         "ecosystem_effect": "First green growth. Pioneer species emerge from irradiated soil within 72 hours of sustained frequency exposure."},
    53: {"name": "Al-Muhyi", "freq": 510.89, "role": "LIFE ACTIVATION",
         "material_effect": "The Giver of Life — activates nitrogen-fixing bacteria in soil substrate. These bacteria convert atmospheric N2 into plant-available ammonia.",
         "ecosystem_effect": "Soil fertility bootstraps. Once nitrogen fixation begins, the ecosystem becomes self-sustaining within one growth cycle."},
    85: {"name": "An-Nafi", "freq": 559.38, "role": "NUTRIENT CYCLING",
         "material_effect": "The Propitious — accelerates decomposition of organic matter into humus. Fungal hyphae respond to this frequency by extending growth rate 3x.",
         "ecosystem_effect": "Nutrient cycling closes the loop. Dead plant matter becomes food for new growth. The ecosystem enters positive feedback."},
    86: {"name": "An-Nur", "freq": 560.89, "role": "PHOTOSYNTHETIC TRIGGER",
         "material_effect": "The Light — modulates chloroplast membrane potential in pioneer plants. Photosynthetic efficiency increases 20-30% under this frequency.",
         "ecosystem_effect": "Plants grow faster, produce more biomass, shade soil (reducing evaporation), and begin atmospheric oxygen contribution."},
    90: {"name": "Al-Warith", "freq": 566.94, "role": "SUCCESSION TRIGGER",
         "material_effect": "The Inheritor — signals secondary succession. Complex plant communities replace pioneers. Mycorrhizal networks form between root systems.",
         "ecosystem_effect": "The desert becomes a developing ecosystem. Trees begin. Shade creates micro-climates. Rainfall patterns shift locally due to increased transpiration."},
    99: {"name": "As-Sabur", "freq": 579.92, "role": "STABILITY ANCHOR",
         "material_effect": "The Patient — low-amplitude continuous broadcast that stabilises all other frequencies. Prevents harmonic drift over multi-year timescales.",
         "ecosystem_effect": "Long-term stability. The ecosystem persists and deepens. The frequency becomes 'embedded' in the soil itself — the material remembers."},
}

RECLAMATION_PHASES = [
    {
        "phase": 1,
        "name": "NEUTRALISATION",
        "duration_days": 7,
        "names_active": [1, 5],
        "description": "Radiation counter-oscillation. Base 432 Hz carrier activates soil microbiome while As-Salam neutralises residual gamma. Effective dose in top 30cm drops 80%+.",
        "soil_change": "Irradiated sand → radiation-neutral substrate",
        "indicator": "Geiger readings drop to background within shield zone",
    },
    {
        "phase": 2,
        "name": "RESTRUCTURING",
        "duration_days": 14,
        "names_active": [1, 5, 11, 21, 30],
        "description": "Silicate conversion. Al-Khaliq restructures SiO2 crystal lattice, creating nano-pores. Al-Basit expands inter-grain spacing. Al-Latif catalyses hydrogen bonding in trapped water molecules.",
        "soil_change": "Neutral substrate → water-retentive proto-soil",
        "indicator": "Water retention test: substrate holds 40% water by weight",
    },
    {
        "phase": 3,
        "name": "GERMINATION",
        "duration_days": 21,
        "names_active": [1, 11, 21, 30, 48, 53],
        "description": "Life trigger. Al-Ba'ith resurrects dormant seeds. Al-Muhyi activates nitrogen-fixing bacteria. First green shoots within 72 hours.",
        "soil_change": "Proto-soil → biologically active soil with pioneers",
        "indicator": "First green growth visible. Soil nitrogen levels rising.",
    },
    {
        "phase": 4,
        "name": "AMPLIFICATION",
        "duration_days": 60,
        "names_active": [1, 30, 48, 53, 85, 86],
        "description": "Growth acceleration. An-Nafi activates nutrient cycling. An-Nur boosts photosynthetic efficiency. Biomass accumulates rapidly.",
        "soil_change": "Active soil → developing topsoil with humus layer",
        "indicator": "Organic matter > 3%. Pioneer canopy forming.",
    },
    {
        "phase": 5,
        "name": "SUCCESSION",
        "duration_days": 180,
        "names_active": [1, 30, 85, 86, 90, 99],
        "description": "Ecosystem maturation. Al-Warith triggers secondary succession. Mycorrhizal networks form. As-Sabur anchors long-term stability.",
        "soil_change": "Developing topsoil → self-sustaining ecosystem",
        "indicator": "Multi-species community. Local rainfall increase detectable.",
    },
]


def simulate_reclamation(area_km2: float = 100.0, initial_radiation_rem: float = 500.0,
                         shield_efficiency_pct: float = 58.0,
                         node_count: int = 10_000) -> Dict:
    remaining_rem = initial_radiation_rem * (1 - shield_efficiency_pct / 100)

    from void_engine.names_286 import name_frequency, NAMES_99
    active_names = []
    for idx, data in RECLAMATION_NAMES.items():
        computed_freq = name_frequency(idx)
        active_names.append({
            "index": idx,
            "name": data["name"],
            "attribute": NAMES_99[idx - 1][1] if idx <= len(NAMES_99) else "",
            "frequency_hz": round(computed_freq, 2),
            "role": data["role"],
            "material_effect": data["material_effect"],
            "ecosystem_effect": data["ecosystem_effect"],
        })

    phase_results = []
    current_radiation = remaining_rem
    soil_fertility = 0.0
    biomass_kg_m2 = 0.0
    water_retention_pct = 2.0
    species_count = 0

    for phase in RECLAMATION_PHASES:
        names_in_phase = [RECLAMATION_NAMES[n] for n in phase["names_active"]]
        freq_power = sum(RECLAMATION_NAMES[n]["freq"] for n in phase["names_active"]) / 432.0

        if phase["phase"] == 1:
            current_radiation *= 0.15
            water_retention_pct = 3.0
        elif phase["phase"] == 2:
            current_radiation *= 0.5
            water_retention_pct = 40.0
            soil_fertility = 5.0
        elif phase["phase"] == 3:
            current_radiation *= 0.8
            water_retention_pct = 50.0
            soil_fertility = 25.0
            biomass_kg_m2 = 0.3
            species_count = 5
        elif phase["phase"] == 4:
            water_retention_pct = 60.0
            soil_fertility = 55.0
            biomass_kg_m2 = 2.5
            species_count = 20
        elif phase["phase"] == 5:
            water_retention_pct = 70.0
            soil_fertility = 80.0
            biomass_kg_m2 = 8.0
            species_count = 60

        latif_boost = 1.0
        if 30 in phase["names_active"]:
            latif_boost = 1.18

        effective_fertility = min(100, soil_fertility * latif_boost)

        phase_results.append({
            "phase": phase["phase"],
            "name": phase["name"],
            "duration_days": phase["duration_days"],
            "names_active": [RECLAMATION_NAMES[n]["name"] for n in phase["names_active"]],
            "frequencies_hz": [round(RECLAMATION_NAMES[n]["freq"], 2) for n in phase["names_active"]],
            "description": phase["description"],
            "soil_change": phase["soil_change"],
            "indicator": phase["indicator"],
            "radiation_rem": round(current_radiation, 2),
            "water_retention_pct": round(water_retention_pct, 1),
            "soil_fertility_pct": round(effective_fertility, 1),
            "biomass_kg_m2": round(biomass_kg_m2, 2),
            "species_count": species_count,
            "freq_power": round(freq_power, 2),
            "latif_boost": round(latif_boost, 2),
        })

    total_days = sum(p["duration_days"] for p in RECLAMATION_PHASES)
    nodes_per_km2 = node_count / area_km2
    coverage_grade = (
        "SOVEREIGN" if nodes_per_km2 > 200 else
        "FORTIFIED" if nodes_per_km2 > 100 else
        "ACTIVE" if nodes_per_km2 > 50 else
        "PARTIAL" if nodes_per_km2 > 20 else
        "MINIMAL"
    )

    return {
        "area_km2": area_km2,
        "initial_radiation_rem": initial_radiation_rem,
        "shield_efficiency_pct": shield_efficiency_pct,
        "post_shield_radiation_rem": round(remaining_rem, 2),
        "node_count": node_count,
        "nodes_per_km2": round(nodes_per_km2, 1),
        "coverage_grade": coverage_grade,
        "total_reclamation_days": total_days,
        "active_names_count": len(active_names),
        "active_names": active_names,
        "phases": phase_results,
        "final_state": {
            "radiation_rem": round(phase_results[-1]["radiation_rem"], 2),
            "water_retention_pct": phase_results[-1]["water_retention_pct"],
            "soil_fertility_pct": phase_results[-1]["soil_fertility_pct"],
            "biomass_kg_m2": phase_results[-1]["biomass_kg_m2"],
            "species_count": phase_results[-1]["species_count"],
            "ecosystem_status": "SELF-SUSTAINING" if phase_results[-1]["soil_fertility_pct"] > 70 else "DEVELOPING",
        },
    }
