# ═══════════════════════════════════════════════════════════
# ADRIANA LEXICON — Semantic Core Language (SCL) v1.0
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
# DOMAINS:
#   aqua      — Aquaponics subsystem
#   flywheel  — Flywheel energy storage
#   silk      — Silk wiring / strand network
#   pressure  — AC Lobby pressure differential
#   system    — Cross-domain / meta operations
#
# GRAMMAR:
#   Expressions are glyph chains separated by '-'
#   Pattern: [entity]-[condition]-[action]
#   Multiple actions chain: [entity]-[condition]-[action]-[action]
#   Conditional branch: [entity]-[condition]-[action]|[entity]-[condition]-[action]
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

# ─── CONDITIONS (Thresholds / Qualifiers) ─────────────────

θ | condition | system | threshold_high | Above safe threshold | value > threshold_high
θ↓ | condition | system | threshold_low | Below safe threshold | value < threshold_low
📈 | condition | system | rising | Value is increasing | delta > 0
📉 | condition | system | declining | Value is decreasing | delta < 0
⚡ | condition | system | critical | At critical level | value at critical
⚖️ | condition | system | balanced | Within safe range | value in safe_range
🔴 | condition | system | alarm | Alarm state triggered | alarm == True
🟢 | condition | system | nominal | All within spec | status == nominal
∅ | condition | system | absent | Value missing / zero | value == 0 or None
≈ | condition | system | approximate | Near threshold | abs(value - threshold) < margin

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
📡 | action | system | signal | Send Silk Web signal | action.signal
🔍 | action | system | scan | Run diagnostic scan | action.sensor_calibrate
⏸️ | action | system | pause | Pause / hold state | action.pause
