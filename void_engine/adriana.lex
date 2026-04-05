# ═══════════════════════════════════════════════════════════
# ADRIANA LEXICON — Semantic Core Language (SCL) v2.0
# "The code is the intent. The frequency is the feeling."
# ═══════════════════════════════════════════════════════════
#
# VOID Script v2.0 — April 5, 2026.
# Canonical 45-glyph set. Ugaritic and v1.1 emoji extensions retired.
# Single source of truth: void_engine/void_script.py (CANONICAL_GLYPHS).
#
# FORMAT:  glyph | category | domain | key | description | python_equivalent | hz_fingerprint
#
# CATEGORIES:
#   entity    — Subject / sensor / subsystem reference
#   condition — State check / threshold / qualifier
#   action    — Operation to perform
#
# GRAMMAR:
#   Expressions are glyph chains separated by '-'
#   Pattern: [entity]-[condition]-[action]
#
# ═══════════════════════════════════════════════════════════

# ─── ENTITIES (lowercase Greek + select symbols) ──────────

α | entity | genesis   | origin       | Origin / Seed — first breath                         | sensor.alpha          | 432.0
β | entity | aqua      | growth       | Growth / Sprout — doubling of life                   | sensor.beta           | 433.2
γ | entity | signal    | signal_pulse | Signal / Pulse — fork of a wave toward earth         | sensor.gamma          | 434.0
δ | entity | transform | change       | Change / Shift — the moment before transformation    | sensor.delta          | 434.8
ε | entity | boundary  | threshold    | Threshold / Edge — gate between inside and outside   | sensor.epsilon        | 435.5
ζ | entity | soil      | depth        | Depth / Root — anchor pressed between earth layers  | sensor.zeta           | 429.0
η | entity | aqua      | flow         | Flow / Current — water moving vessel to vessel       | sensor.eta            | 430.5
θ | entity | environment | heat       | Heat / Warmth — contained warmth at the horizon     | sensor.theta          | 431.0
ι | entity | data      | particle     | Particle / Grain — smallest possible mark            | sensor.iota           | 432.5
κ | entity | security  | key          | Key / Lock — notches that release a lock             | sensor.kappa          | 433.7
λ | entity | signal    | wave         | Wave / Carry — carrier line driving energy forward  | sensor.lambda         | 436.0
μ | entity | metrics   | measure      | Measure / Weight — balance scale pan below pivot    | sensor.mu             | 432.8
ν | entity | mesh      | node         | Node / Link — junction where paths converge          | sensor.nu             | 431.5
ξ | entity | vortex    | scatter      | Scatter / Spread — three bars fanning outward        | sensor.xi             | 437.0
ο | entity | cycle     | circle       | Circle / Return — perfect loop with no start         | sensor.omicron        | 432.2
π | entity | harmony   | ratio        | Ratio / Balance — horizontal cap on two equal legs  | sensor.pi             | 432.0
ρ | entity | data      | density      | Density / Mass — weight of information              | sensor.rho            | 433.0
σ | entity | ledger    | summation    | Summation / Ledger — scroll being tallied           | sensor.sigma          | 435.1
τ | entity | temporal  | time         | Time / Tick — clock hand marking the moment         | sensor.tau            | 434.5
υ | entity | vault     | vessel       | Vessel / Container — cup ready to receive           | sensor.upsilon        | 430.0
φ | entity | vortex    | spiral       | Spiral / Fibonacci — vertical axis of a spiral      | sensor.phi_lower      | 442.0
χ | entity | mesh      | junction     | Cross / Junction — unavoidable meeting of signals   | sensor.chi            | 436.5
ψ | entity | resonance | breath       | Breath / Spirit — trident of air branching out      | sensor.psi            | 438.5
ω | entity | finality  | rest         | Rest / Complete — breath released into silence       | sensor.omega_lower    | 428.5

# ─── CONDITIONS (uppercase Greek) ─────────────────────────

Α | condition | governance | authority  | Authority / Source — peak of sovereign governance   | cond.alpha_cap        | 432.0
Β | condition | forge      | builder    | Builder / Forge — blueprint pressed into material   | cond.beta_cap         | 433.2
Γ | condition | gateway    | gate       | Gate / Portal — doorframe threshold to next state   | cond.gamma_cap        | 434.0
Δ | condition | transform  | evolve     | Transform / Evolve — change that is now active      | cond.delta_cap        | 434.8
Θ | condition | security   | shield     | Shield / Guard — condition protecting what must not be touched | cond.theta_cap | 431.0
Λ | condition | signal     | carrier    | Carrier / Bridge — arch confirming active carrier   | cond.lambda_cap       | 436.0
Ξ | condition | vault      | archive    | Archive / Store — three shelves of formal storage   | cond.xi_cap           | 437.0
Π | condition | genesis    | foundation | Foundation / Base — heavy lintel on two equal pillars | cond.pi_cap         | 432.0
Σ | condition | ledger     | aggregate  | Total / Aggregate — zigzag gathering all paths      | cond.sigma_cap        | 435.1
Φ | condition | harmony    | golden     | Golden Ratio / Structure — Fibonacci axis condition | cond.phi_cap          | 442.2
Ψ | condition | resonance  | sovereign  | Sovereign Mind — crown of thought aligned           | cond.psi_cap          | 438.5
Ω | condition | finality   | sealed     | Finality / Vault — operation complete and irrevocable | cond.omega_cap      | 428.0

# ─── ACTIONS (mathematical and typographic symbols) ───────

∞ | action | cycle     | loop        | Loop / Eternal — repeating at sovereign frequency   | action.infinity       | 432.0
◆ | action | genesis   | ignite      | Core / Engine — fires the engine at ignition        | action.void_diamond   | 432.0
⬡ | action | mesh      | mesh_cell   | Mesh Cell — activates a cell in the GriDul network  | action.hexagon        | 435.0
⟐ | action | silt      | silt_drop   | Silt Drop — deposits encoded packet into ledger     | action.lozenge        | 433.5
☽ | action | temporal  | rest_phase  | Rest Phase — initiates the lunar rest cycle         | action.crescent       | 429.5
☀ | action | signal    | broadcast   | Peak / Broadcast — full-spectrum signal release     | action.sun            | 440.0
⚡ | action | forge     | spark       | Spark / Ignite — activates forge energy burst       | action.lightning      | 441.0
🌊 | action | aqua      | surge       | Tide / Surge — wave action flooding the mesh        | action.wave           | 430.0
🔮 | action | resonance | foresight   | Prophecy / Foresight — opens the resonance channel | action.crystal        | 432.0
