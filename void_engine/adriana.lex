# ═══════════════════════════════════════════════════════════
# ADRIANA LEXICON — Semantic Core Language (SCL) v1.2
# "The code is the intent. The frequency is the feeling."
# ═══════════════════════════════════════════════════════════
#
# FORMAT:  glyph | category | domain | key | description | python_equivalent | hz_fingerprint
#
# hz_fingerprint: the resonance tone (Hz) assigned to this glyph/concept.
#   When Adriana references this glyph, the associated frequency is surfaced —
#   making the lexicon speak in tone, not just definition.
#   Sources: adriana_scl.py GLYPHS table (entity/condition glyphs);
#            functional resonance (action glyphs); 432 Hz Vortex Standard.
#
# CATEGORIES:
#   entity    — Subject / sensor / subsystem reference
#   condition — State check / threshold / qualifier
#   action    — Operation to perform
#
# DOMAINS (v1.0 — biological/physical systems):
#   aqua          — Aquaponics subsystem
#   flywheel      — Flywheel energy storage
#   silk          — Silk wiring / strand network
#   pressure      — AC Lobby pressure differential
#   system        — Cross-domain / meta operations
#
# DOMAINS (v1.1 — multi-domain skill extensions):
#   intelligence  — Research, analysis, financial intelligence
#   signal        — Content, brand, SEO, ad creative
#   ledger        — Legal, finance, invoicing, tax, data
#   mesh          — People networks, recruitment, SDR, resume
#   soil          — Physical world: real estate, supply chain
#
# GRAMMAR:
#   Expressions are glyph chains separated by '-'
#   Pattern: [entity]-[condition]-[action]
#   Multiple actions chain: [entity]-[condition]-[action]-[action]
#   Conditional branch: [entity]-[condition]-[action]|[entity]-[condition]-[action]
#   Skill dispatch: [skill_entity]-[skill_condition]-[skill_action]
#                   → routes through skill_router.py to execute() interface
#
# ═══════════════════════════════════════════════════════════

# ─── ENTITIES (Subjects) ──────────────────────────────────

α | entity | aqua | heat | Water temperature sensor | sensor.aqua_temperature | 432.0
ψ | entity | aqua | life | Plankton life state / health | sensor.aqua_dissolved_oxygen | 438.5
ω | entity | aqua | water | Water level / volume | sensor.aqua_water_level | 428.5
μ | entity | aqua | ph | pH balance sensor | sensor.aqua_ph | 432.8
ν | entity | aqua | nutrient | Ammonia / nutrient level | sensor.aqua_ammonia | 431.5
π | entity | aqua | pump | Pump cycle counter | sensor.aqua_pump_cycles | 432.0

Φ | entity | flywheel | spin | Flywheel RPM | sensor.flywheel_rpm | 442.2
Ε | entity | flywheel | energy | Energy reserve (Wh) | sensor.flywheel_energy | 435.5
Θ | entity | flywheel | temp | Flywheel temperature | sensor.flywheel_temperature | 431.0
Γ | entity | flywheel | vibration | Flywheel vibration (g) | sensor.flywheel_vibration | 434.0

σ | entity | silk | strand | Silk strand resistance | sensor.silk_total_resistance | 435.1
δ | entity | silk | drift | Resistance delta / drift | sensor.silk_resistance_delta | 434.8
λ | entity | silk | link | Strand continuity / link | sensor.silk_strand_count | 436.0

Ρ | entity | pressure | chamber | Internal pressure (atm) | sensor.pressure_internal | 433.0
Χ | entity | pressure | curtain | Air Curtain velocity | sensor.air_curtain_velocity | 436.5
Ν | entity | pressure | nitrogen | Nitrogen boil rate | sensor.nitrogen_boil_rate | 431.5
Σ | entity | pressure | seal | Seal integrity (%) | sensor.seal_integrity | 435.1

Ω | entity | system | void | The Void Engine itself | system.void | 432.0
∞ | entity | system | connection | Network / signal link | system.connection | 432.0

# ─── SKILL ENTITIES (v1.1 — Multi-Domain) ────────────────
# Each glyph is globally unique — no collision with v1.0 set above.

🔬 | entity | intelligence | research_lens | Deep research focal point / synthesis entity | skill.intelligence.deep_research | 432.0
⚔️ | entity | intelligence | competitor | Competitor / market rival entity | skill.intelligence.competitor | 441.0
💹 | entity | intelligence | stock_entity | Financial market / stock entity | skill.intelligence.stock | 435.1

✍️ | entity | signal | content_entity | Content creation entity / writer signal | skill.signal.content | 436.0
📢 | entity | signal | campaign_entity | Campaign / advertising broadcast entity | skill.signal.campaign | 440.0
🌟 | entity | signal | brand_identity | Brand identity / naming entity | skill.signal.brand | 442.2
🕷️ | entity | signal | web_crawler | Web signal / SEO crawl entity | skill.signal.seo_crawler | 437.0

⚖️ | entity | ledger | legal_entity | Legal agreement / contract entity | skill.ledger.legal | 433.7
🧾 | entity | ledger | invoice_entity | Billing / invoice entity | skill.ledger.invoice | 435.1
🏛️ | entity | ledger | tax_entity | Tax obligation / fiscal entity | skill.ledger.tax | 433.0
🗃️ | entity | ledger | data_grid | Structured data / spreadsheet entity | skill.ledger.data_grid | 432.8

👤 | entity | mesh | candidate_entity | Candidate / talent pool entity | skill.mesh.candidate | 431.5
📨 | entity | mesh | outbound_signal | Outbound lead / prospect entity | skill.mesh.prospect | 436.0
📄 | entity | mesh | profile_entity | Professional profile / CV entity | skill.mesh.profile | 432.5
🎤 | entity | mesh | interview_entity | Interview / assessment entity | skill.mesh.interview | 434.0

🌿 | entity | soil | nutrition_entity | Nutritional / dietary routing entity | skill.aqua.nutrition | 429.0
✈️ | entity | soil | journey_entity | Travel / journey routing entity | skill.aqua.journey | 430.0
🏠 | entity | soil | property_entity | Property / real estate signal entity | skill.soil.property | 432.2
🏭 | entity | soil | supplier_entity | Supplier / supply chain entity | skill.soil.supplier | 433.5

# ─── CONDITIONS (Thresholds / Qualifiers) ─────────────────

θ | condition | system | threshold_high | Above safe threshold | value > threshold_high | 431.0
θ↓ | condition | system | threshold_low | Below safe threshold | value < threshold_low | 430.5
📈 | condition | system | rising | Value is increasing | delta > 0 | 436.0
📉 | condition | system | declining | Value is decreasing | delta < 0 | 429.0
⚡ | condition | system | critical | At critical level | value at critical | 441.0
🔵 | condition | system | balanced | Within safe range | value in safe_range | 432.0
🔴 | condition | system | alarm | Alarm state triggered | alarm == True | 441.0
🟢 | condition | system | nominal | All within spec | status == nominal | 432.0
∅ | condition | system | absent | Value missing / zero | value == 0 or None | 428.5
≈ | condition | system | approximate | Near threshold | abs(value - threshold) < margin | 432.2

# ─── SKILL CONDITIONS (v1.1 — Multi-Domain) ───────────────
# Each glyph is globally unique — no collision with v1.0 set above.

🌐 | condition | intelligence | multi_source | Multi-source input available | skill.condition.multi_source | 432.0
📊 | condition | intelligence | market_signal | Market positioning data available | skill.condition.market_signal | 435.1
💱 | condition | intelligence | price_signal | Price or financial signal available | skill.condition.price_signal | 434.5

📡 | condition | signal | broadcast_ready | Signal is ready for broadcast | skill.condition.broadcast_ready | 440.0
🎪 | condition | signal | audience_primed | Target audience is identified and primed | skill.condition.audience_primed | 436.5
🎭 | condition | signal | identity_undefined | Brand identity is undefined or needs reshaping | skill.condition.identity_undefined | 437.0
🔎 | condition | signal | index_gap | Index gap or ranking opportunity detected | skill.condition.index_gap | 434.8

📋 | condition | ledger | terms_undefined | Contract terms or parties are unresolved | skill.condition.terms_undefined | 433.7
💰 | condition | ledger | payment_due | Payment obligation is due or pending | skill.condition.payment_due | 435.5
⚠️ | condition | ledger | liability_flagged | Potential tax liability or flag detected | skill.condition.liability_flagged | 441.0
🗂️ | condition | ledger | data_unstructured | Data is unstructured or needs formatting | skill.condition.data_unstructured | 432.5

🎯 | condition | mesh | role_defined | Role requirements and criteria are defined | skill.condition.role_defined | 433.7
🌱 | condition | mesh | lead_uncontacted | Lead is uncontacted or cold | skill.condition.lead_uncontacted | 429.0
🧭 | condition | mesh | career_path_defined | Target career direction is defined | skill.condition.career_path_defined | 432.8
🏋️ | condition | mesh | prep_required | Preparation or coaching is required | skill.condition.prep_required | 434.8

🍽️ | condition | soil | diet_goal_set | Dietary goal or restriction is defined | skill.condition.diet_goal_set | 432.5
🗺️ | condition | soil | destination_set | Destination and travel parameters are defined | skill.condition.destination_set | 430.0
📍 | condition | soil | location_signal | Location and market data signals available | skill.condition.location_signal | 432.2
🌍 | condition | soil | supply_chain_unmapped | Supply chain is undefined or needs mapping | skill.condition.supply_chain_unmapped | 437.0

# ─── ACTIONS (Operations) ─────────────────────────────────

❄️ | action | aqua | cool | Activate cooling / reduce temp | action.sensor_calibrate | 430.0
💊 | action | aqua | feed | Add nutrients / vitality dose | action.nutrient_dose | 432.8
🌊 | action | aqua | flow | Trigger pump cycle | action.pump_cycle | 430.0
⚗️ | action | aqua | balance | Adjust pH balance | action.sensor_calibrate | 432.0

🔋 | action | flywheel | charge | Boost flywheel energy | action.flywheel_boost | 441.0
🛑 | action | flywheel | brake | Reduce RPM / emergency stop | action.flywheel_boost | 428.5
🔧 | action | flywheel | maintain | Calibrate / maintenance check | action.sensor_calibrate | 432.0

🕸️ | action | silk | weave | Test silk strand integrity | action.silk_test | 436.0
🔌 | action | silk | reconnect | Re-establish strand link | action.silk_test | 431.5

🛡️ | action | pressure | shield | Activate Air Curtain | action.air_curtain_activate | 431.0
💨 | action | pressure | vent | Nitrogen vent / depressurize | action.nitrogen_vent | 430.5
🔓 | action | pressure | release | Deactivate Air Curtain | action.air_curtain_deactivate | 432.0

↺ | action | system | retry | Retry last operation | action.retry | 432.0
🔗 | action | system | signal | Send Silk Web signal | action.signal | 436.0
🔍 | action | system | scan | Run diagnostic scan | action.sensor_calibrate | 434.5
⏸️ | action | system | pause | Pause / hold state | action.pause | 428.5

# ─── SKILL ACTIONS (v1.1 — Multi-Domain) ──────────────────
# Each glyph is globally unique — no collision with v1.0 set above.

📚 | action | intelligence | synthesise | Synthesise and distil research output | skill.intelligence.synthesise | 432.0
🏹 | action | intelligence | position | Generate competitive positioning breakdown | skill.intelligence.position | 435.1
🔭 | action | intelligence | analyse_signal | Read and interpret financial signal | skill.intelligence.read_signal | 436.0

🖊️ | action | signal | generate_content | Generate structured long-form or short-form content | skill.signal.generate | 436.0
🎨 | action | signal | create_ad | Generate ad copy and creative brief | skill.signal.create_ad | 440.0
🔮 | action | signal | forge_identity | Forge brand name, identity, and positioning | skill.signal.forge_identity | 432.0
⬆️ | action | signal | optimise_signal | Generate SEO audit and programmatic strategy | skill.signal.optimise | 437.0

✒️ | action | ledger | draft_contract | Draft a structured legal contract template | skill.ledger.draft | 433.7
🖨️ | action | ledger | generate_invoice | Generate structured invoice output | skill.ledger.invoice_generate | 435.1
🔏 | action | ledger | review_tax | Generate tax summary and flag potential liabilities | skill.ledger.tax_review | 431.0
📥 | action | ledger | structure_data | Generate structured tabular data output | skill.ledger.structure | 432.5

🤝 | action | mesh | match_candidate | Match candidates to role requirements | skill.mesh.match | 432.2
💬 | action | mesh | generate_outreach | Generate personalised outbound message sequence | skill.mesh.outreach | 436.0
📝 | action | mesh | structure_profile | Structure and write a professional profile / CV | skill.mesh.resume | 432.8
🗣️ | action | mesh | coach_answers | Generate interview questions and coached answers | skill.mesh.coach | 434.0

🥗 | action | soil | plan_meals | Generate structured meal plan with nutritional routing | skill.aqua.plan_meals | 429.0
🧳 | action | soil | build_itinerary | Build structured travel itinerary | skill.aqua.itinerary | 430.0
🔑 | action | soil | analyse_property | Read and interpret property signal and market context | skill.soil.analyse_property | 432.2
🛒 | action | soil | map_supply_chain | Research and map supplier network intelligence | skill.soil.supply_chain | 437.0
