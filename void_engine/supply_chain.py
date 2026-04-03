"""
Supply Chain Intelligence — PROJECT VOID
==========================================
Physical supplier data for the VOID Chronometer and 4000-Series Sovereign Node.

Four material categories:
  1. MMC (Mineralized Mycelium Composite) substrate
  2. Piezo-quartz pallet stones for 432 Hz escapement
  3. Transgenic / bio-engineered silk (hairspring)
  4. 4000-Series node hardware enclosure manufacturing

Each category contains evaluated vendor dicts with scores and recommended vendor.
"""

from __future__ import annotations
from typing import Dict, List

# ---------------------------------------------------------------------------
# WEIGHT CONFIGURATION FOR VENDOR MATRIX
# ---------------------------------------------------------------------------
SCORE_WEIGHTS = {
    "quality":     0.30,
    "cost":        0.15,
    "delivery":    0.15,
    "capability":  0.20,
    "reliability": 0.10,
    "compliance":  0.10,
}


def _weighted_total(v: Dict) -> float:
    return round(
        v["quality_score"]     * SCORE_WEIGHTS["quality"]
        + v["cost_score"]      * SCORE_WEIGHTS["cost"]
        + v["delivery_score"]  * SCORE_WEIGHTS["delivery"]
        + v["capability_score"] * SCORE_WEIGHTS["capability"]
        + v["reliability_score"] * SCORE_WEIGHTS["reliability"]
        + v["compliance_score"] * SCORE_WEIGHTS["compliance"],
        2,
    )


# ---------------------------------------------------------------------------
# CATEGORY 1 — MMC (Mineralized Mycelium Composite) Substrate
# ---------------------------------------------------------------------------
_CAT1_VENDORS_RAW = [
    {
        "name": "Ecovative Design",
        "location": "Green Island, NY, USA",
        "specialisation": "Mycelium composites for packaging, insulation, and biomedical substrates",
        "strengths": [
            "Pioneer in industrial mycelium manufacturing; largest production scale in the US",
            "Proprietary AirMycelium technology enables rapid growth cycles (5–7 days)",
            "FDA food-contact clearance signals biocompatibility maturity",
            "Open to R&D partnership agreements and custom substrate formulations",
        ],
        "concerns": [
            "Primary focus on packaging applications; biomedical-grade MMC requires custom NPD track",
            "US-based adds transatlantic logistics cost and lead-time risk",
            "UFLPA agricultural input traceability may require additional documentation",
            "IP ownership clauses in co-development agreements need close scrutiny",
        ],
        "estimated_cost_range": "£120–£280/kg (prototype); £60–£140/kg at volume >500 kg",
        "lead_time": "16–24 weeks (first article); 8–12 weeks (steady state)",
        "compliance": ["FDA 21 CFR Part 177", "REACH compliant", "ISO 9001:2015 certified"],
        "quality_score": 4,
        "cost_score": 3,
        "delivery_score": 3,
        "capability_score": 5,
        "reliability_score": 4,
        "compliance_score": 4,
        "recommended": True,
        "role": "Primary",
    },
    {
        "name": "MycoWorks",
        "location": "Emeryville, CA, USA",
        "specialisation": "Fine Mycelium™ sheets for luxury goods, wearables, and precision substrates",
        "strengths": [
            "Fine Mycelium™ process produces material with leather-like mechanical consistency",
            "High repeatability between batches — critical for precision horological base plates",
            "Existing luxury/fashion supply relationships demonstrate premium-material track record",
            "Active biomedical research programme creates alignment with VOID chronometer specs",
        ],
        "concerns": [
            "Premium pricing reflects luxury positioning; cost per kg among highest in category",
            "Minimum order quantities (MOQs) designed for fashion-volume runs, not watchmaking micro-batches",
            "Current production capacity prioritised for Hermès partnership — VOID as secondary customer",
            "Calcium-silica mineralisation process not standard; requires co-development NDA",
        ],
        "estimated_cost_range": "£280–£550/kg (prototype); £150–£220/kg at volume >1,000 kg",
        "lead_time": "20–30 weeks (first article); 12–16 weeks (steady state)",
        "compliance": ["ISO 9001:2015", "California Prop 65 compliant", "B-Corp certified"],
        "quality_score": 5,
        "cost_score": 2,
        "delivery_score": 2,
        "capability_score": 4,
        "reliability_score": 4,
        "compliance_score": 4,
        "recommended": False,
        "role": "Backup",
    },
    {
        "name": "Mogu",
        "location": "Inarzo, Varese, Italy (EU)",
        "specialisation": "Mycelium acoustic panels and structural composites; EU bioeconomy sector leader",
        "strengths": [
            "EU-based — simplifies REACH/CE compliance and avoids UFLPA exposure",
            "Structural composite expertise translates to baseplate rigidity requirements",
            "Active research partnerships with EU biomedical universities",
            "Reasonable MOQs and willingness to supply small R&D batches",
        ],
        "concerns": [
            "Limited experience with precision engineering tolerances (<50 μm flatness)",
            "No established track record in horological-grade substrate supply",
            "Post-Brexit UK export documentation adds 3–5 days administrative friction",
            "Calcium-silica mineralisation density targeting at 78% not yet demonstrated",
        ],
        "estimated_cost_range": "£95–£190/kg (prototype); £55–£110/kg at volume >300 kg",
        "lead_time": "14–20 weeks (first article); 8–14 weeks (steady state)",
        "compliance": ["CE marked products", "REACH SVHC compliant", "ISO 14001"],
        "quality_score": 3,
        "cost_score": 4,
        "delivery_score": 4,
        "capability_score": 3,
        "reliability_score": 3,
        "compliance_score": 4,
        "recommended": False,
        "role": "EU Alternative",
    },
    {
        "name": "Bolt Threads",
        "location": "Emeryville, CA, USA",
        "specialisation": "Bio-engineered materials: Mylo™ mycelium leather and Microsilk™ protein fibres",
        "strengths": [
            "Dual capability in both mycelium composites AND silk proteins — unique cross-category vendor",
            "Strong IP portfolio in bio-materials; potential licensing rather than supply relationship",
            "Deep biotech R&D bench — able to engineer custom MMC mineralisation on contract",
            "Strategic investor base (Stella McCartney, Patagonia) signals long-term viability",
        ],
        "concerns": [
            "Currently prioritising consumer fashion brands; not accepting new industrial accounts",
            "IP-heavy organisation — tooling ownership and co-development IP must be negotiated carefully",
            "NNN risk in any China-based sub-processing arrangements",
            "Cost structure reflects biotech R&D overhead, not manufacturing efficiency",
        ],
        "estimated_cost_range": "£320–£600/kg (prototype); £180–£280/kg at volume >2,000 kg",
        "lead_time": "24–36 weeks (first article); 14–20 weeks (steady state)",
        "compliance": ["FDA GRAS designation for protein materials", "ISO 9001:2015", "B-Corp certified"],
        "quality_score": 5,
        "cost_score": 1,
        "delivery_score": 2,
        "capability_score": 5,
        "reliability_score": 3,
        "compliance_score": 4,
        "recommended": False,
        "role": "Strategic Reserve",
    },
]

for v in _CAT1_VENDORS_RAW:
    v["weighted_total"] = _weighted_total(v)

CATEGORY_MMC = {
    "id": "mmc",
    "name": "MMC Substrate",
    "full_name": "Mineralized Mycelium Composite (MMC) Substrate",
    "material_spec": (
        "Mycelium composite baseplate grown on agricultural waste substrate, "
        "mineralised with calcium-silicate matrix to achieve 78% active node density. "
        "Dimensions: 38.6 mm diameter × 3.2 mm thickness. Flatness tolerance: ≤30 μm. "
        "Surface hardness: ≥60 Shore D. Moisture resistance: ≤0.8% absorption at 72 h."
    ),
    "patent_claims": ["#101", "#102"],
    "volume_requirement": "50 units (prototype); 500 units/year (production)",
    "quality_standard": "ISO 9001:2015; surface finish Ra ≤1.6 μm",
    "timeline": "First article Q3 2026; production ramp Q1 2027",
    "glyph": "◆",
    "vendors": _CAT1_VENDORS_RAW,
    "recommended_primary": "Ecovative Design",
    "recommended_backup": "Mogu",
    "primary_reasoning": (
        "Ecovative's scale, biocompatibility track record, and openness to R&D partnerships "
        "make them the strongest primary candidate. Their AirMycelium technology achieves "
        "7-day growth cycles matching VOID's 78% node density target."
    ),
    "backup_reasoning": (
        "Mogu offers the best EU-based alternative, reducing geopolitical and compliance risk "
        "while providing structural composite expertise relevant to baseplate rigidity."
    ),
    "risk_flags": {
        "financial": "Ecovative raised Series B in 2023; burn rate unknown. Require financial health disclosure in RFQ.",
        "operational": "First-article lead time 16–24 weeks creates timeline risk for Q3 2026 prototype.",
        "geopolitical": "All primary vendors US-based; transatlantic logistics exposed to tariff volatility post-2025.",
        "compliance": "UFLPA traceability required for any agricultural input sourced from Xinjiang. Request supply chain map.",
    },
    "negotiation_leverage": [
        "Volume commitment: offer 500-unit/year production contract to unlock R&D pricing on prototype batches",
        "MOQ flexibility: request 10-unit sampling run at prototype pricing before committing to first article",
        "Tooling ownership: insist on retaining ownership of custom mold geometry and mineralisation parameters",
        "IP protection: require NDA covering all custom substrate formulations developed jointly",
        "Payment terms: milestone-based payment (30% on PO, 40% first article approval, 30% delivery)",
    ],
}

# ---------------------------------------------------------------------------
# CATEGORY 2 — Piezo-Quartz Pallet Stones for 432 Hz Escapement
# ---------------------------------------------------------------------------
_CAT2_VENDORS_RAW = [
    {
        "name": "Mojon-Fleurier SA",
        "location": "Fleurier, Canton Neuchâtel, Switzerland",
        "specialisation": "Precision horological escapement components; pallet stones and lever assemblies",
        "strengths": [
            "Swiss watchmaking heritage; manufactures for major Maisons including Patek Philippe and Rolex sub-suppliers",
            "Experience with non-standard pallet stone materials beyond synthetic ruby",
            "Ultra-precision grinding to ±0.5 μm — critical for 432 Hz resonance accuracy",
            "ISO 9001 and ISO 14001 certified; full metrology reporting per delivery",
        ],
        "concerns": [
            "Extremely high per-unit cost at prototype quantities; minimum viable order may exceed budget",
            "Piezo-quartz as pallet stone material is non-standard; extended qualification period required",
            "Long lead times driven by capacity allocation to major OEM clients",
            "Swiss-to-UK logistics adds CHF/GBP exposure and customs documentation",
        ],
        "estimated_cost_range": "£180–£420/stone (prototype); £45–£120/stone at volume >1,000",
        "lead_time": "20–28 weeks (first article); 10–14 weeks (steady state)",
        "compliance": ["ISO 9001:2015", "ISO 14001:2015", "CE Declaration of Conformity", "REACH compliant"],
        "quality_score": 5,
        "cost_score": 2,
        "delivery_score": 2,
        "capability_score": 5,
        "reliability_score": 5,
        "compliance_score": 5,
        "recommended": True,
        "role": "Primary",
    },
    {
        "name": "Donzé Baume SA",
        "location": "Les Breuleux, Jura, Switzerland",
        "specialisation": "Escapement manufacturing; lever and wheel sets for high-frequency oscillators",
        "strengths": [
            "Specialises in high-frequency escapements — direct experience with non-standard frequency tuning",
            "In-house frequency analysis lab for resonance verification at custom Hz targets",
            "Open to collaboration on experimental materials including quartz composites",
            "Competitive pricing vs. Mojon-Fleurier for equivalent precision tier",
        ],
        "concerns": [
            "Smaller scale increases concentration risk if capacity is reallocated",
            "Limited export track record to UK; Brexit tariff handling needs confirmation",
            "Piezo-quartz material sourcing not vertically integrated — requires third-party crystal supply",
            "Financial disclosure limited; privately held with no public accounts",
        ],
        "estimated_cost_range": "£140–£320/stone (prototype); £38–£95/stone at volume >1,000",
        "lead_time": "18–24 weeks (first article); 8–12 weeks (steady state)",
        "compliance": ["ISO 9001:2015", "REACH compliant", "Swiss watch industry quality standards (NIHS)"],
        "quality_score": 4,
        "cost_score": 3,
        "delivery_score": 3,
        "capability_score": 4,
        "reliability_score": 4,
        "compliance_score": 4,
        "recommended": False,
        "role": "Backup",
    },
    {
        "name": "Citizen Precision Components (UK)",
        "location": "Letchworth Garden City, Hertfordshire, UK",
        "specialisation": "Precision machined components; sub-micron grinding for instrumentation and optics",
        "strengths": [
            "UK-based eliminates import duties and logistics complexity post-Brexit",
            "Proven capability in precision quartz component machining for scientific instruments",
            "Access to UK Catapult manufacturing R&D network for piezo-quartz qualification",
            "Short communication cycles; on-site meetings viable for NDA-sensitive specifications",
        ],
        "concerns": [
            "No established horological supply track record — escapement-specific geometry is specialist",
            "Piezo-quartz polishing to optical-grade surface finish (Ra ≤0.05 μm) requires process validation",
            "Limited batch history with wristwatch-scale components (typically larger industrial parts)",
            "May require 6–9 months of process development before first article qualification",
        ],
        "estimated_cost_range": "£95–£280/stone (prototype incl. process dev); £30–£80/stone at volume",
        "lead_time": "24–36 weeks (first article incl. process dev); 10–16 weeks (steady state)",
        "compliance": ["ISO 9001:2015", "ISO 13485 (medical device components)", "REACH compliant"],
        "quality_score": 3,
        "cost_score": 4,
        "delivery_score": 3,
        "capability_score": 3,
        "reliability_score": 3,
        "compliance_score": 5,
        "recommended": False,
        "role": "UK Domestic Alternative",
    },
    {
        "name": "Corundum Components Ltd",
        "location": "Lichfield, Staffordshire, UK",
        "specialisation": "Synthetic gemstone and crystal components; ruby, sapphire, and quartz palettes",
        "strengths": [
            "Established supplier to UK watchmakers and scientific instrument manufacturers",
            "Experience with alternative pallet stone materials beyond standard synthetic ruby",
            "Flexible MOQs — can supply 10-unit prototype runs at semi-competitive pricing",
            "UK-based with ISO 9001 certification; compliant with UK REACH (post-Brexit)",
        ],
        "concerns": [
            "Piezo-quartz (as opposed to standard fused quartz) requires new material qualification",
            "Frequency characterisation at 432 Hz not part of standard QC process",
            "Small company; capacity constraints if production volumes exceed ~5,000 stones/year",
            "Limited R&D resource for co-development of resonance-tuned crystal geometries",
        ],
        "estimated_cost_range": "£60–£180/stone (prototype); £22–£55/stone at volume >2,000",
        "lead_time": "12–18 weeks (first article); 6–10 weeks (steady state)",
        "compliance": ["ISO 9001:2015", "UK REACH compliant", "RoHS compliant"],
        "quality_score": 3,
        "cost_score": 5,
        "delivery_score": 4,
        "capability_score": 3,
        "reliability_score": 3,
        "compliance_score": 5,
        "recommended": False,
        "role": "Cost-Optimised Alternative",
    },
]

for v in _CAT2_VENDORS_RAW:
    v["weighted_total"] = _weighted_total(v)

CATEGORY_PIEZO = {
    "id": "piezo",
    "name": "Piezo-Quartz Pallet Stones",
    "full_name": "Piezo-Quartz Pallet Stones for 432 Hz Vortex-Torsion Escapement",
    "material_spec": (
        "Piezoelectric quartz crystal pallet stones, polished to optical grade (Ra ≤0.05 μm). "
        "Geometry: entry pallet 52.3°, exit pallet 75.1° (non-standard for 432 Hz tuning). "
        "Material: AT-cut synthetic piezoelectric quartz. "
        "Resonance verification: fundamental mode frequency 432 Hz ±0.1 Hz at 20°C. "
        "Dimensions per stone: 1.8 mm × 0.6 mm × 0.4 mm."
    ),
    "patent_claims": ["#102", "#103"],
    "volume_requirement": "20 stones (prototype); 200 stones/year (production — 2 per movement)",
    "quality_standard": "NIHS horological standards; resonance verified by impedance analyser",
    "timeline": "First article Q4 2026; production Q2 2027",
    "glyph": "⚡",
    "vendors": _CAT2_VENDORS_RAW,
    "recommended_primary": "Mojon-Fleurier SA",
    "recommended_backup": "Donzé Baume SA",
    "primary_reasoning": (
        "Mojon-Fleurier's ultra-precision grinding (±0.5 μm) and frequency verification capability "
        "is essential for the 432 Hz resonance specification. Their track record with major Maisons "
        "provides confidence in delivery consistency despite premium cost."
    ),
    "backup_reasoning": (
        "Donzé Baume's in-house frequency analysis lab and openness to experimental materials "
        "makes them the strongest alternative, with meaningful cost savings vs. Mojon-Fleurier."
    ),
    "risk_flags": {
        "financial": "Both primary Swiss vendors are privately held SMEs; request 3-year audited accounts.",
        "operational": "Piezo-quartz is non-standard pallet material; build 12-week material qualification buffer into timeline.",
        "geopolitical": "CHF strength vs. GBP adds 8–15% cost volatility; consider fixed-price EUR contracts.",
        "compliance": "UK REACH (post-Brexit) requires separate substance declarations from EU REACH; confirm with each vendor.",
    },
    "negotiation_leverage": [
        "Volume commitment: 432 Hz escapement is potentially licensable — offer royalty stream on licensed movements",
        "Exclusivity window: offer 18-month UK exclusivity on 432 Hz pallet geometry to drive engagement",
        "Tooling ownership: provide precision grinding mandrel design — retain IP, offer tooling loan agreement",
        "Payment terms: 50% upfront (covers crystal blank sourcing), 50% on first-article approval",
        "Reference value: Swiss vendor will value UK biomedical meeting reference — offer joint press release rights",
    ],
}

# ---------------------------------------------------------------------------
# CATEGORY 3 — Transgenic / Bio-Engineered Silk (Hairspring)
# ---------------------------------------------------------------------------
_CAT3_VENDORS_RAW = [
    {
        "name": "Spiber Inc.",
        "location": "Tsuruoka, Yamagata Prefecture, Japan",
        "specialisation": "Brewed Protein™ structural proteins; spider silk analogues for industrial applications",
        "strengths": [
            "World's largest fermentation-based structural protein production facility (Tsuruoka + Thailand plant)",
            "Brewed Protein™ demonstrated piezoelectric properties in published peer-reviewed literature",
            "Existing partnerships with The North Face, Goldwin — proven supply chain maturity",
            "Open to advanced materials research partnerships; active R&D collaboration programme",
        ],
        "concerns": [
            "Japan-to-UK logistics adds 3–4 weeks transit and customs complexity",
            "Primary product form is fibre/yarn; conversion to hairspring geometry requires downstream processing",
            "UFLPA does not apply (Japanese origin) but export control checks required for dual-use materials",
            "Coatings with piezoelectric polymer are outside current standard product offering",
        ],
        "estimated_cost_range": "£2,400–£5,500/gram (prototype); £800–£1,800/gram at volume",
        "lead_time": "24–36 weeks (first article incl. geometry development); 14–20 weeks (steady state)",
        "compliance": ["ISO 9001:2015", "OEKO-TEX STANDARD 100", "Japan JIS standards", "EU REACH compliant"],
        "quality_score": 5,
        "cost_score": 2,
        "delivery_score": 2,
        "capability_score": 5,
        "reliability_score": 4,
        "compliance_score": 4,
        "recommended": True,
        "role": "Primary",
    },
    {
        "name": "Bolt Threads",
        "location": "Emeryville, CA, USA",
        "specialisation": "Microsilk™ recombinant spider silk protein; bio-engineered fibre for luxury and technical applications",
        "strengths": [
            "Microsilk™ has documented piezoelectric response in silk-fibre mesh arrays",
            "Single vendor for both MMC (Mylo™) and silk — simplifies supply chain management",
            "US biotech IP protection framework strong; co-development agreements well-tested",
            "Published data on electrical conductivity and piezoelectric coefficient of Microsilk™",
        ],
        "concerns": [
            "Not accepting new industrial accounts as of 2025; existing pipeline full",
            "Premium biotech pricing reflects investor-driven cost structure, not manufacturing efficiency",
            "IP assignment clauses aggressive — joint development IP retention requires careful negotiation",
            "US export of dual-use bio-engineered materials may trigger additional review under BIS",
        ],
        "estimated_cost_range": "£3,200–£7,000/gram (prototype); £1,200–£2,400/gram at volume",
        "lead_time": "28–40 weeks (first article); 16–24 weeks (steady state)",
        "compliance": ["FDA GRAS (protein materials)", "ISO 9001:2015", "B-Corp certified", "REACH compliant"],
        "quality_score": 5,
        "cost_score": 1,
        "delivery_score": 1,
        "capability_score": 5,
        "reliability_score": 3,
        "compliance_score": 4,
        "recommended": False,
        "role": "Strategic Alternative",
    },
    {
        "name": "AMSilk GmbH",
        "location": "Planegg-Martinsried, Bavaria, Germany (EU)",
        "specialisation": "Biosteel™ recombinant spider silk; biomedical-grade silk proteins for medical devices",
        "strengths": [
            "Biomedical-grade protein silk with ISO 13485 (medical device) certification — highly relevant",
            "EU-based — REACH/CE compliance straightforward; Brexit documentation manageable",
            "Existing supply to Adidas, Airbus — demonstrates technical precision manufacturing capability",
            "Active engagement with academic institutions for novel application research",
        ],
        "concerns": [
            "Production volumes relatively modest vs. Spiber; scaling to VOID production runs needs confirmation",
            "Biosteel™ product line primarily in fibre form; hairspring-geometry spinning is custom process",
            "Piezoelectric polymer coating not part of current product portfolio",
            "German export documentation for biological materials adds administrative overhead",
        ],
        "estimated_cost_range": "£1,800–£4,200/gram (prototype); £650–£1,400/gram at volume",
        "lead_time": "20–30 weeks (first article); 12–18 weeks (steady state)",
        "compliance": ["ISO 13485:2016 (medical devices)", "ISO 9001:2015", "EU REACH", "CE marked materials"],
        "quality_score": 4,
        "cost_score": 3,
        "delivery_score": 3,
        "capability_score": 4,
        "reliability_score": 4,
        "compliance_score": 5,
        "recommended": False,
        "role": "EU Backup / Biomedical Grade",
    },
]

for v in _CAT3_VENDORS_RAW:
    v["weighted_total"] = _weighted_total(v)

CATEGORY_SILK = {
    "id": "silk",
    "name": "Transgenic Silk (Hairspring)",
    "full_name": "Transgenic / Bio-Engineered Silk — Piezoelectric Hairspring",
    "material_spec": (
        "Recombinant spider-silk protein fibre drawn to hairspring geometry: "
        "free length 4.2 mm, wire diameter 0.018 mm (18 μm), coil turns 12.5. "
        "Coating: piezoelectric PVDF-TrFE polymer at 0.8 μm thickness. "
        "Electrical output: ≥0.8 mV/mmHg blood-pressure variation at 37°C. "
        "Biocompatibility: ISO 10993 cytotoxicity compliant."
    ),
    "patent_claims": ["#101", "#103"],
    "volume_requirement": "10 hairsprings (prototype); 100 hairsprings/year (production — 1 per movement)",
    "quality_standard": "ISO 13485 biomedical device standard; piezoelectric output verified per unit",
    "timeline": "First article Q1 2027; production Q3 2027",
    "glyph": "ν",
    "vendors": _CAT3_VENDORS_RAW,
    "recommended_primary": "Spiber Inc.",
    "recommended_backup": "AMSilk GmbH",
    "primary_reasoning": (
        "Spiber's scale, published piezoelectric data for Brewed Protein™, and research partnership "
        "programme make them the strongest primary candidate despite Japan logistics. Their Thailand "
        "plant provides geographic diversification against Japanese supply disruption."
    ),
    "backup_reasoning": (
        "AMSilk's ISO 13485 medical device certification is uniquely aligned with the VOID Chronometer's "
        "biomedical application and provides EU-based supply resilience."
    ),
    "risk_flags": {
        "financial": "Spiber raised $110M Series F in 2021; further funding rounds in 2024 indicate ongoing burn. Confirm runway.",
        "operational": "Hairspring geometry (18 μm wire diameter) requires specialist drawing equipment not standard in silk production.",
        "geopolitical": "Japan-based primary; South-East Asia manufacturing expansion creates UFLPA-adjacent risk — request full origin map.",
        "compliance": "Transgenic organism import into UK requires DEFRA GMO import notification (EC 1946/2003 retained law).",
    },
    "negotiation_leverage": [
        "Research credit: offer co-authorship on UK biomedical meeting patent filing — significant reputational value for Spiber",
        "Exclusivity: 18-month exclusivity on hairspring-geometry Brewed Protein™ application",
        "Volume ramp: commit to 100 units/year starting Q3 2027 with 3-year take-or-pay",
        "IP split: propose 70/30 IP ownership split (VOID/vendor) for custom piezoelectric coating process",
        "Tooling: provide VOID-funded custom drawing die — retain ownership, licence to vendor for VOID production only",
    ],
}

# ---------------------------------------------------------------------------
# CATEGORY 4 — 4000-Series Node Hardware Enclosure Manufacturing
# ---------------------------------------------------------------------------
_CAT4_VENDORS_RAW = [
    {
        "name": "Renishaw plc (UK Precision Engineering Division)",
        "location": "Wotton-under-Edge, Gloucestershire, UK",
        "specialisation": "Ultra-precision machined components; metrology, medical devices, and scientific instruments",
        "strengths": [
            "UK's foremost precision engineering company with world-class metrology capability",
            "Existing relationships with NHS and UK biomedical sector — ideal for UK meeting positioning",
            "In-house additive manufacturing for MMC mold tooling alongside traditional CNC machining",
            "AS9100 (aerospace) and ISO 13485 (medical) certified — exceeds hardware enclosure requirements",
        ],
        "concerns": [
            "Premium pricing reflects engineering capability; cost per unit high at prototype quantities",
            "Not typically a production contract manufacturer; volume runs >500 units may need sub-contractor",
            "Lead times driven by capacity allocation to core instrumentation business",
            "4000-Series enclosure volume requirements (10s–100s) may be below attractive minimum for Renishaw",
        ],
        "estimated_cost_range": "£8,500–£18,000/unit (prototype enclosure, machined); £2,400–£4,800/unit at volume",
        "lead_time": "14–20 weeks (prototype); 10–16 weeks (production)",
        "compliance": ["AS9100 Rev D", "ISO 13485:2016", "ISO 9001:2015", "REACH compliant", "CE marked"],
        "quality_score": 5,
        "cost_score": 2,
        "delivery_score": 3,
        "capability_score": 5,
        "reliability_score": 5,
        "compliance_score": 5,
        "recommended": True,
        "role": "Primary (UK)",
    },
    {
        "name": "Precision Micro Ltd",
        "location": "Hall Green, Birmingham, UK",
        "specialisation": "Photochemical etching and precision sheet metal components for watchmaking and electronics",
        "strengths": [
            "UK-based specialist in watch-grade precision components (movement blanks, bridges, plates)",
            "Photochemical etching achieves ±5 μm tolerances on 2D profiles without tool pressure",
            "Existing watchmaking supply chain relationships; familiar with horological tolerances",
            "Flexible for small batch runs — optimal for VOID's initial 50-unit production",
        ],
        "concerns": [
            "3D enclosure geometry requires hybrid approach (etching + CNC); process complexity increases",
            "MMC integration with metal enclosure elements requires co-design not within standard scope",
            "Limited capacity for full 4000-Series enclosure assembly (component supply, not full assembly)",
            "No ISO 13485 certification; may limit use if chronometer classified as medical device",
        ],
        "estimated_cost_range": "£3,200–£7,500/unit (prototype); £1,100–£2,200/unit at volume",
        "lead_time": "10–16 weeks (prototype); 6–10 weeks (production)",
        "compliance": ["ISO 9001:2015", "AS9100 Rev D", "REACH compliant", "RoHS 3 compliant"],
        "quality_score": 4,
        "cost_score": 4,
        "delivery_score": 4,
        "capability_score": 3,
        "reliability_score": 4,
        "compliance_score": 4,
        "recommended": False,
        "role": "UK Component Supplier",
    },
    {
        "name": "Viet Precision Industrial (VPI)",
        "location": "Binh Duong Province, Vietnam",
        "specialisation": "CNC precision machining for electronics, medical devices, and consumer hardware at volume",
        "strengths": [
            "Significant cost advantage for volume production (100–10,000 units/year)",
            "Modern 5-axis CNC capacity and ISO 13485 certification for medical-grade manufacturing",
            "Established UK/EU export supply chain with customs broker network",
            "Vietnam not subject to UFLPA; lower geopolitical risk than Chinese alternatives",
        ],
        "concerns": [
            "Distance creates quality management overhead; on-site inspection visits expensive",
            "IP protection in Vietnam weaker than UK/EU; NNN agreement essential before sharing specifications",
            "Language/communication friction increases design iteration cycle time",
            "For prototype volumes (10–50 units), cost advantage over UK suppliers is minimal after logistics",
        ],
        "estimated_cost_range": "£4,800–£9,200/unit (prototype incl. tooling amortisation); £800–£1,800/unit at volume",
        "lead_time": "18–24 weeks (prototype + tooling); 8–12 weeks (production)",
        "compliance": ["ISO 13485:2016", "ISO 9001:2015", "RoHS 3 compliant", "CE (self-declaration)"],
        "quality_score": 3,
        "cost_score": 4,
        "delivery_score": 3,
        "capability_score": 3,
        "reliability_score": 3,
        "compliance_score": 3,
        "recommended": False,
        "role": "Volume Alternative",
    },
    {
        "name": "Grupo Vitro Precision (Mexico)",
        "location": "Monterrey, Nuevo León, Mexico",
        "specialisation": "Precision machining and assembly for medical devices, aerospace, and luxury goods",
        "strengths": [
            "USMCA proximity to North American market if VOID expands US distribution",
            "Medical device manufacturing experience (FDA 21 CFR Part 820 registered facility)",
            "Competitive volume pricing with strong quality management systems",
            "Spanish-language negotiations if team has Spanish capability",
        ],
        "concerns": [
            "Mexico-UK supply chain is logistically complex; no existing freight corridor established",
            "Primarily oriented to North American clients; UK regulatory compliance documentation is non-standard for them",
            "IP protection: Mexican IP law less robust for precision engineering trade secrets",
            "Time zone (CST, UTC-6) creates 6-hour communication gap with UK-based VOID team",
        ],
        "estimated_cost_range": "£5,200–£10,500/unit (prototype); £900–£2,100/unit at volume",
        "lead_time": "20–26 weeks (prototype); 10–14 weeks (production)",
        "compliance": ["ISO 9001:2015", "FDA 21 CFR Part 820", "IATF 16949 (automotive grade quality)"],
        "quality_score": 3,
        "cost_score": 3,
        "delivery_score": 2,
        "capability_score": 3,
        "reliability_score": 3,
        "compliance_score": 3,
        "recommended": False,
        "role": "North American Volume Alternative",
    },
]

for v in _CAT4_VENDORS_RAW:
    v["weighted_total"] = _weighted_total(v)

CATEGORY_HARDWARE = {
    "id": "hardware",
    "name": "4000-Series Node Enclosure",
    "full_name": "4000-Series Sovereign Node Hardware Enclosure Manufacturing",
    "material_spec": (
        "Titanium Grade 5 (Ti-6Al-4V) primary enclosure shell, CNC machined, "
        "electropolished to Ra ≤0.4 μm. Internal chamber for MMC baseplate integration: "
        "38.6 mm diameter cavity, tolerance H7/h6 fit. "
        "Crown assembly: 316L stainless steel. Sapphire crystal: scratch-resistant, "
        "AR coated, 0.8 mm minimum. Case dimensions: 44 mm diameter × 14 mm lug-to-lug. "
        "IPX8 water resistance (30 m). Mass: ≤92 g without strap."
    ),
    "patent_claims": ["#101", "#102", "#103"],
    "volume_requirement": "10 units (prototype); 50 units/year (initial production)",
    "quality_standard": "ISO 13485 for biomedical classification; AS9100 for aerospace-grade precision",
    "timeline": "Prototype Q2 2026; initial production Q4 2026",
    "glyph": "Β",
    "vendors": _CAT4_VENDORS_RAW,
    "recommended_primary": "Renishaw plc (UK Precision Engineering Division)",
    "recommended_backup": "Precision Micro Ltd",
    "primary_reasoning": (
        "Renishaw's UK-based precision engineering capability, ISO 13485 certification, and existing "
        "biomedical sector relationships make them the ideal primary for the UK prototype phase. "
        "Their metrology capability will validate the 38.6 mm MMC cavity tolerance critical for integration."
    ),
    "backup_reasoning": (
        "Precision Micro's watchmaking supply chain experience and flexible small-batch capability "
        "make them the optimal component supplier for etched internal components and bridges."
    ),
    "risk_flags": {
        "financial": "Renishaw is FTSE-listed with strong balance sheet; lowest financial risk in category.",
        "operational": "Titanium machining requires specialist coolant management; confirm Renishaw's Ti experience.",
        "geopolitical": "UK-based primary insulates from tariff volatility; Vietnam/Mexico as volume alternatives carry geopolitical exposure.",
        "compliance": "If Chronometer classified as medical device (blood pressure monitoring via hairspring), ISO 13485 mandatory throughout supply chain.",
    },
    "negotiation_leverage": [
        "UK biomedical positioning: Renishaw values proximity to NHS/biomedical clients — offer reference introduction to UK meeting contacts",
        "Volume escalation: commit to volume ramp schedule (10 → 50 → 200 units) with signed letter of intent",
        "Tooling co-investment: propose shared tooling investment with VOID retaining geometry IP",
        "Press opportunity: offer Renishaw case study feature in VOID white paper for UK biomedical publication",
        "MOQ flexibility: request 5-unit sampling run at prototype pricing to validate fit with MMC cavity before full order",
    ],
}

# ---------------------------------------------------------------------------
# ALL CATEGORIES REGISTRY
# ---------------------------------------------------------------------------
ALL_CATEGORIES = [CATEGORY_MMC, CATEGORY_PIEZO, CATEGORY_SILK, CATEGORY_HARDWARE]

CATEGORY_MAP = {cat["id"]: cat for cat in ALL_CATEGORIES}


def get_all_categories() -> List[Dict]:
    return ALL_CATEGORIES


def get_category(category_id: str) -> Dict | None:
    return CATEGORY_MAP.get(category_id)


def get_vendor_matrix_rows() -> List[Dict]:
    """Return flat list of all vendors across all categories for CSV export."""
    rows = []
    for cat in ALL_CATEGORIES:
        for v in cat["vendors"]:
            rows.append({
                "category_id": cat["id"],
                "category_name": cat["full_name"],
                "vendor_name": v["name"],
                "location": v["location"],
                "specialisation": v["specialisation"],
                "estimated_cost_range": v["estimated_cost_range"],
                "lead_time": v["lead_time"],
                "compliance": "; ".join(v["compliance"]),
                "quality_score": v["quality_score"],
                "cost_score": v["cost_score"],
                "delivery_score": v["delivery_score"],
                "capability_score": v["capability_score"],
                "reliability_score": v["reliability_score"],
                "compliance_score": v["compliance_score"],
                "weighted_total": v["weighted_total"],
                "role": v.get("role", ""),
                "recommended": "YES" if v.get("recommended") else "",
            })
    return rows


# ---------------------------------------------------------------------------
# RFQ TEMPLATE DATA
# ---------------------------------------------------------------------------
RFQ_TEMPLATES = {
    "mmc": {
        "category_name": "Mineralized Mycelium Composite (MMC) Substrate",
        "project_background": (
            "PROJECT VOID is developing the VOID Chronometer — a sovereign wrist-engine comprising "
            "a living mycelium composite baseplate, a 286-tooth great wheel, piezo-quartz escapement, "
            "and a transgenic silk hairspring. The Chronometer carries three patent claims (#101–#103) "
            "and is being presented to UK biomedical engineering investors as part of a Series A funding round. "
            "Blueprint NFT holders hold deeds on physical manufacturing slots in the 4000-Series node."
        ),
        "material_specification": (
            "Material: Mineralized Mycelium Composite (MMC)\n"
            "Substrate: Mycelium grown on compressed agricultural waste (non-Xinjiang origin required)\n"
            "Mineralisation: Calcium-silicate matrix at 78% ± 2% active node density\n"
            "Geometry: 38.6 mm diameter disc × 3.2 mm thickness\n"
            "Flatness: ≤30 μm across full diameter\n"
            "Surface hardness: ≥60 Shore D\n"
            "Moisture resistance: ≤0.8% mass gain after 72-hour immersion at 37°C\n"
            "Surface finish: Ra ≤1.6 μm (top face); Ra ≤3.2 μm (bottom face)\n"
            "Colour: Natural off-white to light tan (no pigments unless specified)"
        ),
        "volume_and_timeline": (
            "Phase 1 (Prototype): 10 units — Q3 2026\n"
            "Phase 2 (Pre-production): 50 units — Q4 2026\n"
            "Phase 3 (Initial Production): 500 units/year — from Q1 2027\n"
            "Please quote each phase separately with pricing and lead time."
        ),
        "quality_and_compliance": (
            "Quality Standard: ISO 9001:2015 minimum\n"
            "Biocompatibility: ISO 10993 cytotoxicity testing required for biomedical classification\n"
            "Traceability: Full supply chain map for all agricultural inputs required\n"
            "UFLPA Compliance: Written declaration that no inputs originate from Xinjiang required\n"
            "COA Required: Certificate of Analysis per batch with density, hardness, and flatness data\n"
            "First Article Inspection: FAI report per AS9102 format requested"
        ),
        "pricing_format": (
            "Please provide:\n"
            "1. Unit price per phase (prototype / pre-production / production)\n"
            "2. Tooling costs (mold design and manufacture) — state ownership terms\n"
            "3. NRE (Non-Recurring Engineering) costs for custom mineralisation process\n"
            "4. Payment terms preferred\n"
            "5. Any volume break pricing above 500 units/year"
        ),
        "reference_request": (
            "Please provide:\n"
            "1. Two client references in biomedical or precision engineering applications\n"
            "2. Sample of nearest-equivalent substrate for preliminary testing (10 cm × 10 cm minimum)\n"
            "3. Published data or in-house test reports on calcium-silicate mineralisation density control"
        ),
        "evaluation_timeline": (
            "RFQ Response Deadline: 21 days from issue date\n"
            "Sample Delivery Deadline: 35 days from issue date\n"
            "Supplier Selection Decision: 60 days from issue date\n"
            "NDA/MSA Signature Target: 75 days from issue date\n"
            "Purchase Order Issue: 90 days from issue date"
        ),
    },
    "piezo": {
        "category_name": "Piezo-Quartz Pallet Stones for 432 Hz Vortex-Torsion Escapement",
        "project_background": (
            "PROJECT VOID is developing a non-standard horological escapement operating at precisely "
            "432 Hz — the VOID Vortex-Torsion Escapement. Standard synthetic ruby pallet stones are "
            "replaced with piezoelectric quartz crystals to achieve acoustic levitation at the microscopic "
            "level, preventing organic material (MMC baseplate) from grinding under oscillation. "
            "Patent Claim #102 covers the piezo-quartz pallet stone integration in a biological watch movement."
        ),
        "material_specification": (
            "Material: AT-cut synthetic piezoelectric quartz crystal\n"
            "Entry pallet geometry: 52.3° working face angle, 1.8 mm × 0.6 mm × 0.4 mm\n"
            "Exit pallet geometry: 75.1° working face angle, 1.8 mm × 0.6 mm × 0.4 mm\n"
            "Surface finish: Ra ≤0.05 μm (optical polished)\n"
            "Resonance frequency: fundamental mode 432.0 Hz ± 0.1 Hz at 20°C, 50% RH\n"
            "Piezoelectric coefficient d33: ≥2.0 pC/N\n"
            "Operating temperature: -10°C to +60°C without frequency drift >0.5 Hz\n"
            "Bonding surface: flat, parallel within 1 arc-minute for adhesive bonding to lever"
        ),
        "volume_and_timeline": (
            "Phase 1 (Prototype): 20 stones (10 entry + 10 exit) — Q4 2026\n"
            "Phase 2 (Pre-production): 100 stones — Q1 2027\n"
            "Phase 3 (Production): 200 stones/year (2 per movement × 100 movements) — from Q2 2027\n"
            "Please quote each phase separately."
        ),
        "quality_and_compliance": (
            "Quality Standard: NIHS 94-11 (Swiss horological standards) or equivalent\n"
            "Frequency Verification: Impedance analyser measurement per stone; data sheet required\n"
            "Dimensional Inspection: CMM report per batch (10% sampling minimum)\n"
            "Material Certification: Crystal grade and cut orientation certification required\n"
            "REACH Compliance: Written REACH SVHC declaration required\n"
            "UK REACH: Post-Brexit UK REACH compliance declaration required for UK delivery"
        ),
        "pricing_format": (
            "Please provide:\n"
            "1. Unit price per stone, per phase\n"
            "2. Tooling/grinding fixture costs — state ownership terms\n"
            "3. NRE for custom 432 Hz resonance geometry development\n"
            "4. Frequency characterisation cost per stone\n"
            "5. Currency: GBP preferred; CHF or EUR acceptable with hedging clause"
        ),
        "reference_request": (
            "Please provide:\n"
            "1. One reference for non-standard pallet stone material supply (non-ruby)\n"
            "2. In-house frequency characterisation capability description with equipment spec\n"
            "3. Minimum 2 sample stones machined from AT-cut quartz blank for preliminary evaluation"
        ),
        "evaluation_timeline": (
            "RFQ Response Deadline: 21 days from issue date\n"
            "Sample Stones Deadline: 42 days from issue date\n"
            "Frequency Evaluation Period: 14 days (VOID internal)\n"
            "Supplier Selection: 70 days from issue date\n"
            "First Article Order: 90 days from issue date"
        ),
    },
    "silk": {
        "category_name": "Transgenic / Bio-Engineered Silk — Piezoelectric Hairspring",
        "project_background": (
            "The VOID Chronometer's hairspring is engineered from recombinant spider-silk protein, "
            "coated with a piezoelectric polymer (PVDF-TrFE) to convert the wearer's wrist blood-pressure "
            "pulse into micro-charge for powering the VoidEcho transmitter embedded in the movement. "
            "This is the core of Patent Claim #103 — a bio-sensitive hairspring that acts as both "
            "a timekeeping regulator and a continuous biosensor. The UK biomedical meeting presentation "
            "requires a physical prototype hairspring to demonstrate the technology."
        ),
        "material_specification": (
            "Base material: Recombinant spider-silk protein fibre (MaSp1/MaSp2 analogue)\n"
            "Hairspring geometry: Archimedean spiral, free length 4.2 mm, 12.5 turns\n"
            "Wire diameter: 0.018 mm (18 μm) ± 1 μm\n"
            "Inner coil diameter: 0.6 mm; outer coil diameter: 3.8 mm\n"
            "Coating: PVDF-TrFE piezoelectric polymer, 0.8 μm ± 0.1 μm thickness\n"
            "Electrical output: ≥0.8 mV per mmHg blood-pressure variation at 37°C\n"
            "Young's modulus: 10–20 GPa (longitudinal, dry)\n"
            "Biocompatibility: ISO 10993-5 cytotoxicity compliant\n"
            "Operating temperature: 25–40°C (body temperature range)"
        ),
        "volume_and_timeline": (
            "Phase 1 (Prototype): 5 hairsprings — Q1 2027\n"
            "Phase 2 (Pre-production): 20 hairsprings — Q2 2027\n"
            "Phase 3 (Production): 100 hairsprings/year — from Q3 2027\n"
            "Note: Phase 1 timeline is critical for UK biomedical meeting demonstration (March 2027)."
        ),
        "quality_and_compliance": (
            "Quality Standard: ISO 13485:2016 (medical device manufacturing)\n"
            "Biocompatibility: ISO 10993-5 cytotoxicity test required\n"
            "Piezoelectric Output: Measured electrical response per hairspring; data sheet required\n"
            "Dimensional: Outer diameter ±0.05 mm; wire diameter ±1 μm\n"
            "GMO Compliance: UK DEFRA GMO import notification compliance required\n"
            "REACH: Full SVHC declaration for PVDF-TrFE coating chemistry\n"
            "Origin Map: Full supply chain map for protein expression organism and substrate required"
        ),
        "pricing_format": (
            "Please provide:\n"
            "1. Unit price per hairspring, per phase\n"
            "2. NRE for hairspring geometry drawing process development\n"
            "3. PVDF-TrFE coating process development cost\n"
            "4. Biocompatibility testing cost allocation\n"
            "5. IP terms for any jointly developed drawing/coating process\n"
            "6. Currency: GBP, USD, or JPY"
        ),
        "reference_request": (
            "Please provide:\n"
            "1. Published piezoelectric characterisation data for your silk protein fibre\n"
            "2. One reference for precision geometry fibre drawing (sub-20 μm diameter)\n"
            "3. Regulatory pathway advice for ISO 13485 / GMO compliance in UK market"
        ),
        "evaluation_timeline": (
            "RFQ Response Deadline: 21 days from issue date\n"
            "Feasibility Assessment Call: 30 days from issue date\n"
            "Prototype Hairspring Delivery: Q1 2027 (target)\n"
            "Supplier Selection: 90 days from issue date\n"
            "Co-development NDA Signature: 105 days from issue date"
        ),
    },
    "hardware": {
        "category_name": "4000-Series Sovereign Node Hardware Enclosure",
        "project_background": (
            "The 4000-Series Sovereign Node is the hardware platform for the VOID Chronometer — "
            "a precision wrist-engine housing the MMC baseplate, 286-tooth great wheel, Vortex-Torsion "
            "escapement, and VoidEcho transmitter. Blueprint NFT holders (Legendary tier) receive a "
            "factory-calibrated 4000-Series Node delivered to their door. "
            "The enclosure must integrate seamlessly with the biological MMC baseplate cavity "
            "while achieving IPX8 water resistance and sub-gram dimensional tolerances."
        ),
        "material_specification": (
            "Primary shell: Titanium Grade 5 (Ti-6Al-4V), CNC machined\n"
            "Case diameter: 44.0 mm ± 0.05 mm\n"
            "Case thickness: 14.0 mm ± 0.05 mm (excluding crystal)\n"
            "MMC cavity: 38.6 mm diameter × 3.4 mm depth, H7 tolerance fit\n"
            "Surface finish: Electropolished, Ra ≤0.4 μm (case); bead-blasted lugs\n"
            "Crown: 316L stainless steel, screw-down, triple-seal IPX8\n"
            "Crystal: Sapphire, double AR coated, 0.8 mm minimum thickness\n"
            "Case back: Sapphire crystal exhibition case back, 4-point screwed\n"
            "Water resistance: IPX8 (30 m / 3 bar)\n"
            "Target mass: ≤92 g (case without strap or crystal)"
        ),
        "volume_and_timeline": (
            "Phase 1 (Prototype): 5 enclosures — Q2 2026\n"
            "Phase 2 (Pre-production): 20 enclosures — Q3 2026\n"
            "Phase 3 (Initial Production): 50 enclosures — Q4 2026\n"
            "Phase 4 (Production): 100–500 units/year — from 2027 (volume-dependent routing)\n"
            "UK production required for Phase 1–3; Phase 4 open to international routing."
        ),
        "quality_and_compliance": (
            "Quality Standard: ISO 13485:2016 (if Chronometer classified medical device) or ISO 9001:2015\n"
            "Dimensional: CMM first article inspection per AS9102; 100% gauge inspection on MMC cavity\n"
            "Surface: Roughness measurement per EN ISO 4288\n"
            "Water resistance: IPX8 test per IEC 60529 — 100% test\n"
            "Material certification: Ti-6Al-4V mill certificate required\n"
            "REACH: Full compliance declaration\n"
            "Traceability: Serial number engraving on case back (laser, per VOID specification)"
        ),
        "pricing_format": (
            "Please provide:\n"
            "1. Unit price per phase (prototype / pre-production / production)\n"
            "2. CNC programming and setup NRE\n"
            "3. Tooling costs (fixtures, soft jaws) — state ownership terms\n"
            "4. Sapphire crystal sourcing cost (supply or cost-pass-through)\n"
            "5. IPX8 testing cost per unit\n"
            "6. Serial number engraving cost per unit"
        ),
        "reference_request": (
            "Please provide:\n"
            "1. Two references for titanium precision enclosure manufacture (watchmaking or medical)\n"
            "2. In-house CMM capability specification\n"
            "3. Case study or photographs of nearest-equivalent case geometry manufactured"
        ),
        "evaluation_timeline": (
            "RFQ Response Deadline: 14 days from issue date\n"
            "Factory Visit / Virtual Tour: 21 days from issue date\n"
            "Prototype Order Decision: 45 days from issue date\n"
            "Prototype Delivery Target: Q2 2026\n"
            "Production Partner Selection: 90 days from issue date"
        ),
    },
}


def get_rfq_template(category_id: str) -> Dict | None:
    return RFQ_TEMPLATES.get(category_id)


def get_all_rfq_templates() -> Dict:
    return RFQ_TEMPLATES


# ---------------------------------------------------------------------------
# CHRONICLE SEEDING
# ---------------------------------------------------------------------------
def seed_supply_brief_into_chronicle() -> None:
    """
    Seed one SUPPLY_BRIEF chronicle entry summarising the four supply categories.
    Idempotent — will not duplicate if title already exists.
    """
    import logging
    logger = logging.getLogger(__name__)
    ENTRY_TITLE = "Supply Chain Intelligence — VOID Chronometer Material Categories"

    body = (
        "[SUPPLY_BRIEF] Physical Supply Chain — VOID Chronometer\n\n"
        "Four critical material categories have been identified and evaluated for the "
        "VOID Chronometer and 4000-Series Sovereign Node. Blueprint NFT holders hold "
        "manufacturing slot deeds that require a verified supply chain behind them.\n\n"

        "CATEGORY 1 — MMC SUBSTRATE (Mineralized Mycelium Composite)\n"
        "Recommended Primary: Ecovative Design (Green Island, NY, USA)\n"
        "Backup: Mogu (Inarzo, Italy, EU)\n"
        "Spec: 38.6 mm × 3.2 mm, 78% active node density, calcium-silicate mineralised.\n"
        "Timeline: First article Q3 2026. Patents: #101, #102.\n\n"

        "CATEGORY 2 — PIEZO-QUARTZ PALLET STONES (432 Hz Escapement)\n"
        "Recommended Primary: Mojon-Fleurier SA (Fleurier, Switzerland)\n"
        "Backup: Donzé Baume SA (Les Breuleux, Switzerland)\n"
        "Spec: AT-cut piezoelectric quartz, 432.0 Hz ±0.1 Hz, Ra ≤0.05 μm.\n"
        "Timeline: First article Q4 2026. Patents: #102, #103.\n\n"

        "CATEGORY 3 — TRANSGENIC SILK HAIRSPRING\n"
        "Recommended Primary: Spiber Inc. (Tsuruoka, Japan)\n"
        "Backup: AMSilk GmbH (Planegg-Martinsried, Germany)\n"
        "Spec: 18 μm wire diameter, PVDF-TrFE coating, ≥0.8 mV/mmHg electrical output.\n"
        "Timeline: First article Q1 2027. Patents: #101, #103.\n\n"

        "CATEGORY 4 — 4000-SERIES NODE HARDWARE ENCLOSURE\n"
        "Recommended Primary: Renishaw plc (Wotton-under-Edge, UK)\n"
        "Backup: Precision Micro Ltd (Birmingham, UK)\n"
        "Spec: Ti-6Al-4V, 44 mm case, IPX8, MMC cavity H7 tolerance.\n"
        "Timeline: Prototype Q2 2026. Patents: #101, #102, #103.\n\n"

        "RFQ templates for all four categories are pre-filled with VOID specifications "
        "and available at /supply-chain/rfq.html. Full vendor matrix export: /supply-chain/export.csv.\n\n"
        "Risk flags span UFLPA compliance, GMO import (UK DEFRA), IP ownership in co-development, "
        "and geopolitical exposure from US/Japan sourcing. Negotiation leverage includes volume "
        "commitments, tooling ownership retention, and UK biomedical meeting reference value."
    )

    try:
        from void_engine.chronicle_adriana import _get_db, _ensure_seed_capture_columns
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        conn = _get_db()
        try:
            cur = conn.cursor()
            _ensure_seed_capture_columns(cur)
            cur.execute(
                "SELECT id FROM chronicle_entries WHERE title = %s AND entry_type = %s LIMIT 1",
                (ENTRY_TITLE, "SUPPLY_BRIEF"),
            )
            if cur.fetchone():
                return
            al_jabr_hash = fatiha_286_hexdigest_from_str(f"SUPPLY_BRIEF|MMC|PIEZO|SILK|HARDWARE|VOID_CHRONOMETER")
            season = "FRUITIFICATION"
            try:
                from void_engine.lunar_season import get_current_season
                season = get_current_season()
            except Exception:
                pass
            cur.execute(
                """INSERT INTO chronicle_entries
                   (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash, entry_type, season)
                   VALUES (%s, %s, %s, %s, %s, %s, 'SUPPLY_BRIEF', %s)""",
                (
                    16,
                    ENTRY_TITLE,
                    "Task #90 — Physical Supply Chain Intelligence | April 2026",
                    "◆-ν-Β",
                    body,
                    al_jabr_hash,
                    season,
                ),
            )
            conn.commit()
            logger.info("SUPPLY_BRIEF chronicle entry seeded")
        finally:
            conn.close()
    except Exception as e:
        logger.warning("Supply brief chronicle seeding failed: %s", e)
