# ═══════════════════════════════════════════════════════════
# ADRIANA LEXICON — Semantic Core Language (SCL) v1.1
# "The code is the intent."
# ═══════════════════════════════════════════════════════════
#
# FORMAT:  glyph | category | domain | key | description | python_equivalent
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

α | entity | aqua | heat | Water temperature sensor | sensor.aqua_temperature
ψ | entity | aqua | life | Plankton life state / health | sensor.aqua_dissolved_oxygen
ω | entity | aqua | water | Water level / volume | sensor.aqua_water_level
μ | entity | aqua | ph | pH balance sensor | sensor.aqua_ph
ν | entity | aqua | nutrient | Ammonia / nutrient level | sensor.aqua_ammonia
π | entity | aqua | pump | Pump cycle counter | sensor.aqua_pump_cycles

Φ | entity | flywheel | spin | Flywheel RPM | sensor.flywheel_rpm
Ε | entity | flywheel | energy | Energy reserve (Wh) | sensor.flywheel_energy
Θ | entity | flywheel | temp | Flywheel temperature | sensor.flywheel_temperature
Γ | entity | flywheel | vibration | Flywheel vibration (g) | sensor.flywheel_vibration

σ | entity | silk | strand | Silk strand resistance | sensor.silk_total_resistance
δ | entity | silk | drift | Resistance delta / drift | sensor.silk_resistance_delta
λ | entity | silk | link | Strand continuity / link | sensor.silk_strand_count

Ρ | entity | pressure | chamber | Internal pressure (atm) | sensor.pressure_internal
Χ | entity | pressure | curtain | Air Curtain velocity | sensor.air_curtain_velocity
Ν | entity | pressure | nitrogen | Nitrogen boil rate | sensor.nitrogen_boil_rate
Σ | entity | pressure | seal | Seal integrity (%) | sensor.seal_integrity

Ω | entity | system | void | The Void Engine itself | system.void
∞ | entity | system | connection | Network / signal link | system.connection

# ─── SKILL ENTITIES (v1.1 — Multi-Domain) ────────────────
# Each glyph is globally unique — no collision with v1.0 set above.

🔬 | entity | intelligence | research_lens | Deep research focal point / synthesis entity | skill.intelligence.deep_research
⚔️ | entity | intelligence | competitor | Competitor / market rival entity | skill.intelligence.competitor
💹 | entity | intelligence | stock_entity | Financial market / stock entity | skill.intelligence.stock

✍️ | entity | signal | content_entity | Content creation entity / writer signal | skill.signal.content
📢 | entity | signal | campaign_entity | Campaign / advertising broadcast entity | skill.signal.campaign
🌟 | entity | signal | brand_identity | Brand identity / naming entity | skill.signal.brand
🕷️ | entity | signal | web_crawler | Web signal / SEO crawl entity | skill.signal.seo_crawler

⚖️ | entity | ledger | legal_entity | Legal agreement / contract entity | skill.ledger.legal
🧾 | entity | ledger | invoice_entity | Billing / invoice entity | skill.ledger.invoice
🏛️ | entity | ledger | tax_entity | Tax obligation / fiscal entity | skill.ledger.tax
🗃️ | entity | ledger | data_grid | Structured data / spreadsheet entity | skill.ledger.data_grid

👤 | entity | mesh | candidate_entity | Candidate / talent pool entity | skill.mesh.candidate
📨 | entity | mesh | outbound_signal | Outbound lead / prospect entity | skill.mesh.prospect
📄 | entity | mesh | profile_entity | Professional profile / CV entity | skill.mesh.profile
🎤 | entity | mesh | interview_entity | Interview / assessment entity | skill.mesh.interview

🌿 | entity | soil | nutrition_entity | Nutritional / dietary routing entity | skill.aqua.nutrition
✈️ | entity | soil | journey_entity | Travel / journey routing entity | skill.aqua.journey
🏠 | entity | soil | property_entity | Property / real estate signal entity | skill.soil.property
🏭 | entity | soil | supplier_entity | Supplier / supply chain entity | skill.soil.supplier

# ─── CONDITIONS (Thresholds / Qualifiers) ─────────────────

θ | condition | system | threshold_high | Above safe threshold | value > threshold_high
θ↓ | condition | system | threshold_low | Below safe threshold | value < threshold_low
📈 | condition | system | rising | Value is increasing | delta > 0
📉 | condition | system | declining | Value is decreasing | delta < 0
⚡ | condition | system | critical | At critical level | value at critical
🔵 | condition | system | balanced | Within safe range | value in safe_range
🔴 | condition | system | alarm | Alarm state triggered | alarm == True
🟢 | condition | system | nominal | All within spec | status == nominal
∅ | condition | system | absent | Value missing / zero | value == 0 or None
≈ | condition | system | approximate | Near threshold | abs(value - threshold) < margin

# ─── SKILL CONDITIONS (v1.1 — Multi-Domain) ───────────────
# Each glyph is globally unique — no collision with v1.0 set above.

🌐 | condition | intelligence | multi_source | Multi-source input available | skill.condition.multi_source
📊 | condition | intelligence | market_signal | Market positioning data available | skill.condition.market_signal
💱 | condition | intelligence | price_signal | Price or financial signal available | skill.condition.price_signal

📡 | condition | signal | broadcast_ready | Signal is ready for broadcast | skill.condition.broadcast_ready
🎪 | condition | signal | audience_primed | Target audience is identified and primed | skill.condition.audience_primed
🎭 | condition | signal | identity_undefined | Brand identity is undefined or needs reshaping | skill.condition.identity_undefined
🔎 | condition | signal | index_gap | Index gap or ranking opportunity detected | skill.condition.index_gap

📋 | condition | ledger | terms_undefined | Contract terms or parties are unresolved | skill.condition.terms_undefined
💰 | condition | ledger | payment_due | Payment obligation is due or pending | skill.condition.payment_due
⚠️ | condition | ledger | liability_flagged | Potential tax liability or flag detected | skill.condition.liability_flagged
🗂️ | condition | ledger | data_unstructured | Data is unstructured or needs formatting | skill.condition.data_unstructured

🎯 | condition | mesh | role_defined | Role requirements and criteria are defined | skill.condition.role_defined
🌱 | condition | mesh | lead_uncontacted | Lead is uncontacted or cold | skill.condition.lead_uncontacted
🧭 | condition | mesh | career_path_defined | Target career direction is defined | skill.condition.career_path_defined
🏋️ | condition | mesh | prep_required | Preparation or coaching is required | skill.condition.prep_required

🍽️ | condition | soil | diet_goal_set | Dietary goal or restriction is defined | skill.condition.diet_goal_set
🗺️ | condition | soil | destination_set | Destination and travel parameters are defined | skill.condition.destination_set
📍 | condition | soil | location_signal | Location and market data signals available | skill.condition.location_signal
🌍 | condition | soil | supply_chain_unmapped | Supply chain is undefined or needs mapping | skill.condition.supply_chain_unmapped

# ─── ACTIONS (Operations) ─────────────────────────────────

❄️ | action | aqua | cool | Activate cooling / reduce temp | action.sensor_calibrate
💊 | action | aqua | feed | Add nutrients / vitality dose | action.nutrient_dose
🌊 | action | aqua | flow | Trigger pump cycle | action.pump_cycle
⚗️ | action | aqua | balance | Adjust pH balance | action.sensor_calibrate

🔋 | action | flywheel | charge | Boost flywheel energy | action.flywheel_boost
🛑 | action | flywheel | brake | Reduce RPM / emergency stop | action.flywheel_boost
🔧 | action | flywheel | maintain | Calibrate / maintenance check | action.sensor_calibrate

🕸️ | action | silk | weave | Test silk strand integrity | action.silk_test
🔌 | action | silk | reconnect | Re-establish strand link | action.silk_test

🛡️ | action | pressure | shield | Activate Air Curtain | action.air_curtain_activate
💨 | action | pressure | vent | Nitrogen vent / depressurize | action.nitrogen_vent
🔓 | action | pressure | release | Deactivate Air Curtain | action.air_curtain_deactivate

↺ | action | system | retry | Retry last operation | action.retry
🔗 | action | system | signal | Send Silk Web signal | action.signal
🔍 | action | system | scan | Run diagnostic scan | action.sensor_calibrate
⏸️ | action | system | pause | Pause / hold state | action.pause

# ─── SKILL ACTIONS (v1.1 — Multi-Domain) ──────────────────
# Each glyph is globally unique — no collision with v1.0 set above.

📚 | action | intelligence | synthesise | Synthesise and distil research output | skill.intelligence.synthesise
🏹 | action | intelligence | position | Generate competitive positioning breakdown | skill.intelligence.position
🔭 | action | intelligence | analyse_signal | Read and interpret financial signal | skill.intelligence.read_signal

🖊️ | action | signal | generate_content | Generate structured long-form or short-form content | skill.signal.generate
🎨 | action | signal | create_ad | Generate ad copy and creative brief | skill.signal.create_ad
🔮 | action | signal | forge_identity | Forge brand name, identity, and positioning | skill.signal.forge_identity
⬆️ | action | signal | optimise_signal | Generate SEO audit and programmatic strategy | skill.signal.optimise

✒️ | action | ledger | draft_contract | Draft a structured legal contract template | skill.ledger.draft
🖨️ | action | ledger | generate_invoice | Generate structured invoice output | skill.ledger.invoice_generate
🔏 | action | ledger | review_tax | Generate tax summary and flag potential liabilities | skill.ledger.tax_review
📥 | action | ledger | structure_data | Generate structured tabular data output | skill.ledger.structure

🤝 | action | mesh | match_candidate | Match candidates to role requirements | skill.mesh.match
💬 | action | mesh | generate_outreach | Generate personalised outbound message sequence | skill.mesh.outreach
📝 | action | mesh | structure_profile | Structure and write a professional profile / CV | skill.mesh.resume
🗣️ | action | mesh | coach_answers | Generate interview questions and coached answers | skill.mesh.coach

🥗 | action | soil | plan_meals | Generate structured meal plan with nutritional routing | skill.aqua.plan_meals
🧳 | action | soil | build_itinerary | Build structured travel itinerary | skill.aqua.itinerary
🔑 | action | soil | analyse_property | Read and interpret property signal and market context | skill.soil.analyse_property
🛒 | action | soil | map_supply_chain | Research and map supplier network intelligence | skill.soil.supply_chain
