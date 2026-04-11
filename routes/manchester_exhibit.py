"""
Manchester Exhibit Plan — Formation Invisibility Live Demo
/manchester-exhibit              (GET  — equipment plan + setup guide)
/api/exhibit/budget              (GET  — full equipment budget JSON)
"""

import logging
from flask import Blueprint, render_template_string, jsonify

logger = logging.getLogger(__name__)

manchester_exhibit_bp = Blueprint("manchester_exhibit", __name__)

EQUIPMENT = {
    "core_audio": [
        {
            "item": "Portable Bluetooth Speaker (JBL Flip 6 or similar)",
            "qty": 6,
            "unit_price": 85.00,
            "total": 510.00,
            "note": "Six speakers placed in hexagonal formation. Must be identical model for matched frequency response. JBL Flip 6 recommended — 20Hz-20kHz, IP67, 12hr battery. Alternative: Anker Soundcore Motion+ (£55 each, total £330).",
            "budget_alt": "Anker Soundcore Motion+ × 6 = £330",
            "source": "Amazon UK / Argos / Currys"
        },
        {
            "item": "3.5mm Aux Splitter Cable (1-to-6)",
            "qty": 1,
            "unit_price": 12.00,
            "total": 12.00,
            "note": "Splits single audio source to all six speakers simultaneously. Ensures phase-locked playback. Alternative: use Bluetooth multipoint pairing (free but slight latency risk).",
            "source": "Amazon UK"
        },
        {
            "item": "Smartphone / Laptop (audio source)",
            "qty": 1,
            "unit_price": 0.00,
            "total": 0.00,
            "note": "You already own this. Runs the void-stego-engine app which generates the formation frequencies.",
            "source": "Already owned"
        },
    ],
    "stones_formation": [
        {
            "item": "Polished River Stones (8-12cm diameter)",
            "qty": 6,
            "unit_price": 3.50,
            "total": 21.00,
            "note": "Six stones placed at hexagonal positions between the speakers. Visual markers for the formation. Dark basalt or grey granite — clean, heavy, professional look.",
            "source": "Garden centre / B&Q / Amazon UK"
        },
        {
            "item": "Black Felt Tablecloth (2m × 2m)",
            "qty": 1,
            "unit_price": 15.00,
            "total": 15.00,
            "note": "Floor covering for the formation area. Black makes the stones and speakers stand out. Marks the boundary of the formation field.",
            "source": "Amazon UK / Hobbycraft"
        },
        {
            "item": "White Chalk Marker Pen",
            "qty": 2,
            "unit_price": 3.00,
            "total": 6.00,
            "note": "Draw the hexagonal formation lines on the black felt. Shows visitors the geometry. Wipes clean.",
            "source": "Hobbycraft / WHSmith"
        },
    ],
    "measurement": [
        {
            "item": "Decibel Meter App (NIOSH SLM or similar)",
            "qty": 1,
            "unit_price": 0.00,
            "total": 0.00,
            "note": "Free app on your phone. Measures sound level at the centre vs outside the formation. This is the proof — show people the dB reading drops at the void point.",
            "source": "App Store / Google Play"
        },
        {
            "item": "Measuring Tape (5m)",
            "qty": 1,
            "unit_price": 4.00,
            "total": 4.00,
            "note": "Precise placement matters. Speakers must be equidistant from centre. 0.6m radius = 1.2m diameter formation inside the 2m space.",
            "source": "B&Q / Poundland"
        },
    ],
    "display": [
        {
            "item": "Tablet or Laptop (screen for live simulation)",
            "qty": 1,
            "unit_price": 0.00,
            "total": 0.00,
            "note": "Shows the /formation-invisibility page live. Visitors see the interference field simulation matching the physical setup in front of them. Already owned.",
            "source": "Already owned"
        },
        {
            "item": "Tablet Stand / Laptop Riser",
            "qty": 1,
            "unit_price": 12.00,
            "total": 12.00,
            "note": "Elevates screen so visitors can see both the physical formation and the digital simulation.",
            "source": "Amazon UK"
        },
        {
            "item": "A3 Printed Poster — Formation Principle",
            "qty": 2,
            "unit_price": 8.00,
            "total": 16.00,
            "note": "One poster: Formation Principle statement + Chladni image. One poster: scale invariance table (lab plate → Sahara → agent field). Print at Staples or online.",
            "source": "Staples / Vistaprint / local print shop"
        },
    ],
    "power_backup": [
        {
            "item": "Power Bank (20000mAh)",
            "qty": 1,
            "unit_price": 25.00,
            "total": 25.00,
            "note": "Backup power for tablet/laptop. Speakers run on internal battery (12hr each). One power bank keeps everything running all day.",
            "source": "Amazon UK / Argos"
        },
        {
            "item": "Extension Lead (4-gang, 2m cable)",
            "qty": 1,
            "unit_price": 8.00,
            "total": 8.00,
            "note": "If the venue provides mains power. Charge speakers and devices during breaks.",
            "source": "B&Q / Argos"
        },
    ],
}

BUDGET_TIERS = {
    "minimum": {
        "name": "Minimum Viable Demo",
        "total": 95.00,
        "description": "Phone speakers + stones + felt. Proves the concept.",
        "items": [
            "6 × cheap Bluetooth speakers (£12 each from Primark/Poundland) = £72",
            "6 × river stones from garden = £0",
            "Black fabric offcut = £5",
            "Chalk pen = £3",
            "Measuring tape = £4",
            "Decibel app = free",
            "Your phone + laptop = already owned",
            "A3 prints at library = £6",
        ]
    },
    "standard": {
        "name": "Professional Demo",
        "total": 329.00,
        "description": "Matched speakers, proper materials, clean presentation.",
        "items": [
            "6 × Anker Soundcore Motion+ = £330",
            "6 × polished stones = £21",
            "Black felt 2m × 2m = £15",
            "Chalk markers = £6",
            "Measuring tape = £4",
            "Tablet stand = £12",
            "A3 posters × 2 = £16",
            "Power bank = £25",
            "Extension lead = £8",
            "Aux splitter = £12",
        ]
    },
    "premium": {
        "name": "Full Impact Demo",
        "total": 629.00,
        "description": "JBL speakers, everything polished, maximum credibility.",
        "items": [
            "6 × JBL Flip 6 = £510",
            "6 × polished basalt stones = £21",
            "Black felt 2m × 2m = £15",
            "Chalk markers = £6",
            "Measuring tape = £4",
            "Tablet stand = £12",
            "A3 posters × 2 = £16",
            "Power bank = £25",
            "Extension lead = £8",
            "Aux splitter = £12",
        ]
    }
}

DEMO_SCRIPT = [
    {
        "step": 1,
        "title": "The Setup",
        "duration": "Before event",
        "action": "Lay black felt on the floor. Use measuring tape to mark centre point. Mark six positions at 60° intervals, each 60cm from centre. Place speakers at positions. Place stones between speakers. Draw hexagonal lines with chalk marker connecting the positions."
    },
    {
        "step": 2,
        "title": "The Baseline",
        "duration": "30 seconds",
        "action": "Play a steady tone (432 Hz) from all six speakers simultaneously. Ask the visitor to stand OUTSIDE the formation and listen. Open the decibel meter app — show them the reading. It will be loud and clear."
    },
    {
        "step": 3,
        "title": "The Void",
        "duration": "30 seconds",
        "action": "Ask the visitor to step into the CENTRE of the formation — the exact middle between all six speakers. The sound changes. At the interference null, certain frequencies cancel. The decibel meter shows a DROP at specific frequencies. They can hear the difference with their own ears."
    },
    {
        "step": 4,
        "title": "The Proof",
        "duration": "30 seconds",
        "action": "Show them the /formation-invisibility page on your tablet. The simulation shows the same hexagonal formation they are standing inside. The dark zones on screen match where they just experienced sound cancellation. Same maths. Live proof."
    },
    {
        "step": 5,
        "title": "The Scale",
        "duration": "30 seconds",
        "action": "Show the /sahara-formation page. Same maths, planetary scale. The Sahara desert is a Chladni plate. Then show VoidMessage — the same principle hiding data inside audio. One principle, three scales, all running live on your platform."
    },
    {
        "step": 6,
        "title": "The Close",
        "duration": "30 seconds",
        "action": "Hand them your phone showing void-stego-engine.replit.app. Tell them: this is the Formation Principle. Sound creates structure. Structure creates function. We just proved it with six speakers and six stones in a 2-metre square. The platform has 120 engine modules doing the same thing with AI agents, cryptography, and steganography."
    },
]

SETUP_DIAGRAM = """
    2m × 2m SPACE — TOP-DOWN VIEW

    ┌─────────────────────────────────┐
    │                                 │
    │         🔊 Speaker 1            │
    │        ⬡                        │
    │   🔊       🪨        🔊         │
    │  Spk 6    Stone 1    Spk 2      │
    │     🪨               🪨         │
    │    Stone 6    ∅     Stone 2      │
    │            CENTRE               │
    │     🪨    (VOID)     🪨         │
    │    Stone 5          Stone 3      │
    │   🔊       🪨        🔊         │
    │  Spk 5    Stone 4    Spk 3      │
    │        ⬡                        │
    │         🔊 Speaker 4            │
    │                                 │
    │  ┌──────────┐                   │
    │  │ 💻 Screen│  ← Tablet showing │
    │  │ /formation│   live simulation │
    │  └──────────┘                   │
    └─────────────────────────────────┘

    Radius: 60cm from centre to each speaker
    Diameter: 1.2m (fits inside 2m space with room)
    Stones: placed midway between adjacent speakers
    Centre: the void point — where visitor stands
"""


@manchester_exhibit_bp.route("/manchester-exhibit")
def exhibit_page():
    return render_template_string(TEMPLATE)


@manchester_exhibit_bp.route("/api/exhibit/budget")
def budget_api():
    totals = {}
    for cat, items in EQUIPMENT.items():
        cat_total = sum(i["total"] for i in items)
        totals[cat] = cat_total

    return jsonify({
        "equipment": EQUIPMENT,
        "category_totals": totals,
        "grand_total": sum(totals.values()),
        "budget_tiers": BUDGET_TIERS,
        "demo_script": DEMO_SCRIPT,
        "setup_diagram": SETUP_DIAGRAM,
        "event": {
            "name": "Manchester ICC Event",
            "date": "April 13, 2026",
            "space": "2m × 2m",
            "location": "ICC Manchester"
        }
    })


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Manchester Exhibit Plan — PROJECT VOID</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  :root {
    --bg: #060606; --surface: #0c0c0c; --border: #181818;
    --muted: #444; --text: #c0c0c0; --bright: #e8e8e8;
    --green: #86efac; --green-dark: #166534;
    --cyan: #67e8f9; --amber: #fbbf24; --red: #f87171;
    --purple: #7c3aed;
  }
  body { background: var(--bg); color: var(--text); font-family: 'Courier New', monospace; font-size: 14px; min-height: 100vh; }
  .container { max-width: 1100px; margin: 0 auto; padding: 20px; }

  header { border-bottom: 1px solid var(--border); padding: 16px 0; display: flex; justify-content: space-between; align-items: center; }
  .logo { font-size: 16px; letter-spacing: 6px; font-weight: bold; }
  .logo span { color: var(--green); }
  nav a { color: var(--muted); text-decoration: none; margin-left: 20px; font-size: 12px; letter-spacing: 2px; }
  nav a:hover { color: var(--bright); }

  .hero { text-align: center; padding: 50px 0 30px; }
  .hero .subtitle { color: var(--muted); font-size: 11px; letter-spacing: 6px; margin-bottom: 12px; }
  .hero h1 { font-size: 36px; font-weight: 300; color: var(--bright); margin-bottom: 8px; }
  .hero h1 span { color: var(--green); }
  .hero .date { color: var(--amber); font-size: 14px; letter-spacing: 3px; margin-bottom: 16px; }
  .hero .thesis { color: var(--muted); font-size: 13px; line-height: 1.6; max-width: 600px; margin: 0 auto; }

  .section-label { color: var(--muted); font-size: 11px; letter-spacing: 4px; margin: 40px 0 16px; border-bottom: 1px solid var(--border); padding-bottom: 8px; }

  .tier-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 20px 0; }
  @media (max-width: 768px) { .tier-grid { grid-template-columns: 1fr; } }
  .tier-card { background: var(--surface); border: 1px solid var(--border); padding: 20px; position: relative; }
  .tier-card.recommended { border-color: var(--green); }
  .tier-card.recommended::after { content: 'RECOMMENDED'; position: absolute; top: -10px; right: 12px; background: var(--green-dark); color: var(--green); font-size: 9px; letter-spacing: 2px; padding: 3px 8px; }
  .tier-card h3 { font-size: 13px; color: var(--bright); letter-spacing: 2px; margin-bottom: 4px; }
  .tier-card .price { font-size: 32px; color: var(--green); font-weight: bold; margin: 8px 0; }
  .tier-card .price-note { font-size: 11px; color: var(--muted); margin-bottom: 12px; }
  .tier-card ul { list-style: none; }
  .tier-card li { font-size: 11px; color: var(--text); padding: 4px 0; border-bottom: 1px solid var(--border); }
  .tier-card li:last-child { border-bottom: none; }

  .diagram-box { background: var(--surface); border: 1px solid var(--border); padding: 24px; margin: 20px 0; }
  .diagram-box h3 { color: var(--green); font-size: 13px; letter-spacing: 2px; margin-bottom: 16px; }
  .diagram-box pre { color: var(--text); font-size: 12px; line-height: 1.5; overflow-x: auto; }

  .step-list { display: flex; flex-direction: column; gap: 12px; margin: 20px 0; }
  .step-card { background: var(--surface); border: 1px solid var(--border); padding: 20px; display: grid; grid-template-columns: 50px 1fr; gap: 16px; }
  .step-num { font-size: 28px; color: var(--green); font-weight: bold; text-align: center; line-height: 1; }
  .step-num .dur { font-size: 10px; color: var(--muted); font-weight: normal; margin-top: 4px; }
  .step-content h4 { color: var(--bright); font-size: 14px; letter-spacing: 2px; margin-bottom: 6px; }
  .step-content p { font-size: 12px; color: var(--text); line-height: 1.6; }

  .equip-section { margin: 20px 0; }
  .equip-section h3 { color: var(--cyan); font-size: 12px; letter-spacing: 3px; margin-bottom: 12px; }
  .equip-table { width: 100%; border-collapse: collapse; }
  .equip-table th { font-size: 10px; letter-spacing: 2px; color: var(--muted); text-align: left; padding: 8px; border-bottom: 1px solid var(--border); }
  .equip-table td { font-size: 12px; padding: 10px 8px; border-bottom: 1px solid var(--border); vertical-align: top; }
  .equip-table .price { color: var(--green); font-weight: bold; white-space: nowrap; }
  .equip-table .note { font-size: 10px; color: var(--muted); margin-top: 4px; line-height: 1.4; }
  .equip-table .source { font-size: 10px; color: var(--amber); }

  .checklist { background: var(--surface); border: 1px solid var(--green-dark); padding: 24px; margin: 20px 0; }
  .checklist h3 { color: var(--green); font-size: 13px; letter-spacing: 2px; margin-bottom: 12px; }
  .checklist ul { list-style: none; }
  .checklist li { font-size: 12px; padding: 6px 0; border-bottom: 1px solid var(--border); color: var(--text); }
  .checklist li:last-child { border-bottom: none; }
  .checklist li::before { content: '☐ '; color: var(--green); }

  .warning-box { background: rgba(251,191,36,0.05); border: 1px solid rgba(251,191,36,0.3); padding: 16px; margin: 20px 0; }
  .warning-box h4 { color: var(--amber); font-size: 12px; letter-spacing: 2px; margin-bottom: 8px; }
  .warning-box p { font-size: 12px; color: var(--text); line-height: 1.6; }

  .total-bar { background: var(--surface); border: 1px solid var(--green); padding: 20px; margin: 20px 0; display: flex; justify-content: space-between; align-items: center; }
  .total-bar .label { font-size: 12px; color: var(--muted); letter-spacing: 3px; }
  .total-bar .amount { font-size: 28px; color: var(--green); font-weight: bold; }

  footer { border-top: 1px solid var(--border); padding: 20px 0; margin-top: 40px; text-align: center; }
  footer p { font-size: 11px; color: var(--muted); }
</style>
</head>
<body>
<div class="container">

<header>
  <div class="logo">PROJECT <span>VOID</span></div>
  <nav>
    <a href="/formation-invisibility">INVISIBILITY</a>
    <a href="/sahara-formation">SAHARA</a>
    <a href="/engine">ENGINE</a>
  </nav>
</header>

<div class="hero">
  <div class="subtitle">FORMATION INVISIBILITY — LIVE DEMONSTRATION</div>
  <h1>Manchester <span>Exhibit</span></h1>
  <div class="date">APRIL 13, 2026 — ICC MANCHESTER</div>
  <div class="thesis">
    Six speakers. Six stones. One void point.<br>
    A 2m × 2m space that proves sound creates structure.
  </div>
</div>

<div class="section-label">BUDGET TIERS</div>

<div class="tier-grid">
  <div class="tier-card">
    <h3>MINIMUM VIABLE</h3>
    <div class="price">£95</div>
    <div class="price-note">Proves the concept. Gets it done.</div>
    <ul>
      <li>6 × cheap Bluetooth speakers (£12 each) — £72</li>
      <li>6 × river stones from garden — £0</li>
      <li>Black fabric offcut — £5</li>
      <li>Chalk pen — £3</li>
      <li>Measuring tape — £4</li>
      <li>Decibel app — free</li>
      <li>A3 prints at library — £6</li>
      <li>Phone + laptop — already owned</li>
    </ul>
  </div>

  <div class="tier-card recommended">
    <h3>PROFESSIONAL</h3>
    <div class="price">£329</div>
    <div class="price-note">Matched speakers. Clean presentation.</div>
    <ul>
      <li>6 × Anker Soundcore Motion+ — £330</li>
      <li>6 × polished stones — £21</li>
      <li>Black felt 2m × 2m — £15</li>
      <li>Chalk markers × 2 — £6</li>
      <li>Measuring tape — £4</li>
      <li>Tablet stand — £12</li>
      <li>A3 posters × 2 — £16</li>
      <li>Power bank — £25</li>
      <li>Extension lead — £8</li>
      <li>Aux splitter — £12</li>
    </ul>
  </div>

  <div class="tier-card">
    <h3>FULL IMPACT</h3>
    <div class="price">£629</div>
    <div class="price-note">JBL speakers. Maximum credibility.</div>
    <ul>
      <li>6 × JBL Flip 6 — £510</li>
      <li>6 × polished basalt stones — £21</li>
      <li>Black felt 2m × 2m — £15</li>
      <li>Chalk markers × 2 — £6</li>
      <li>Measuring tape — £4</li>
      <li>Tablet stand — £12</li>
      <li>A3 posters × 2 — £16</li>
      <li>Power bank — £25</li>
      <li>Extension lead — £8</li>
      <li>Aux splitter — £12</li>
    </ul>
  </div>
</div>

<div class="section-label">FORMATION LAYOUT — TOP-DOWN VIEW</div>

<div class="diagram-box">
  <h3>2m × 2m SPACE</h3>
  <pre>
         ┌──────────────────────────────────────────┐
         │                                          │
         │              🔊 Speaker 1                │
         │                                          │
         │                                          │
         │      🔊              🪨              🔊   │
         │    Spk 6          Stone 1          Spk 2 │
         │                                          │
         │        🪨                        🪨       │
         │      Stone 6        ∅          Stone 2    │
         │                  CENTRE                   │
         │                 (VOID)                    │
         │        🪨                        🪨       │
         │      Stone 5                   Stone 3    │
         │                                          │
         │      🔊              🪨              🔊   │
         │    Spk 5          Stone 4          Spk 3 │
         │                                          │
         │                                          │
         │              🔊 Speaker 4                │
         │                                          │
         │   ┌──────────┐                           │
         │   │ 💻 Screen │ ← shows /formation-      │
         │   │          │   invisibility live        │
         │   └──────────┘                           │
         └──────────────────────────────────────────┘

         Radius: 60cm from centre to each speaker
         Diameter: 1.2m formation inside 2m space
         Stones: midway between adjacent speakers
         Centre: the VOID POINT — visitor stands here
  </pre>
</div>

<div class="section-label">THE DEMO — 3 MINUTE SCRIPT</div>

<div class="step-list">
  <div class="step-card">
    <div class="step-num">0<div class="dur">BEFORE</div></div>
    <div class="step-content">
      <h4>THE SETUP</h4>
      <p>Lay black felt on the floor. Measure and mark centre point. Mark six positions at 60° intervals, each 60cm from centre. Place speakers at positions. Place stones between speakers. Draw hexagonal lines with chalk marker. Connect all speakers to your phone via aux splitter or Bluetooth multipoint. Open /formation-invisibility on tablet.</p>
    </div>
  </div>

  <div class="step-card">
    <div class="step-num">1<div class="dur">30 SEC</div></div>
    <div class="step-content">
      <h4>THE BASELINE</h4>
      <p>Play a steady 432 Hz tone from all six speakers. Ask the visitor to stand OUTSIDE the formation. Open the decibel meter app on your phone — show them the reading. It will read 65-75 dB. Clear, audible, uniform. "This is what six speakers sound like from the outside."</p>
    </div>
  </div>

  <div class="step-card">
    <div class="step-num">2<div class="dur">30 SEC</div></div>
    <div class="step-content">
      <h4>THE VOID</h4>
      <p>Ask the visitor to step into the CENTRE of the hexagon — the exact middle. The sound character changes. At the interference null, the waves from all six speakers arrive and interact differently. Show the decibel meter — it will show a different reading at the centre. They can hear the difference with their own ears. "You're standing at the void point. The formation changed what you hear."</p>
    </div>
  </div>

  <div class="step-card">
    <div class="step-num">3<div class="dur">30 SEC</div></div>
    <div class="step-content">
      <h4>THE PROOF</h4>
      <p>Point at the tablet showing /formation-invisibility. "This is the simulation of what you just experienced. Six sources — same as these speakers. Hexagonal formation — same layout. The dark zones on screen are the void points — where signals cancel. You just stood in one." Let them see the maths matches the physical experience.</p>
    </div>
  </div>

  <div class="step-card">
    <div class="step-num">4<div class="dur">30 SEC</div></div>
    <div class="step-content">
      <h4>THE SCALE</h4>
      <p>Swipe to /sahara-formation. "Same mathematics, planetary scale. The Sahara desert organises sand into dune patterns the same way these speakers organise sound. Frequency distributes matter into formation." Then show VoidMessage: "And this is the same principle hiding encrypted messages inside audio files. One principle, three applications."</p>
    </div>
  </div>

  <div class="step-card">
    <div class="step-num">5<div class="dur">30 SEC</div></div>
    <div class="step-content">
      <h4>THE CLOSE</h4>
      <p>Hand them your phone or a card with void-stego-engine.replit.app. "This is the Formation Principle. Sound creates structure. I built a platform with 120 engine modules that applies this to AI agent systems, cryptography, audio steganography, and frequency-based authentication. Everything you just heard in this formation — that's the foundation of the entire platform."</p>
    </div>
  </div>
</div>

<div class="section-label">CRITICAL NOTES</div>

<div class="warning-box">
  <h4>SPEAKER PLACEMENT PRECISION</h4>
  <p>The interference pattern depends on equal distances. Use the measuring tape. All six speakers must be exactly 60cm from the centre point. If one speaker is 5cm off, the void shifts and weakens. Measure twice, place once. The stones don't need to be precise — they're visual markers. The speakers are the formation.</p>
</div>

<div class="warning-box">
  <h4>FREQUENCY SELECTION</h4>
  <p>432 Hz is your signature frequency. It produces audible interference patterns at the 60cm radius. If the room is noisy, try 500-800 Hz — higher frequencies produce sharper interference patterns in smaller spaces. The /formation-invisibility page lets you preview which frequency creates the strongest void at your chosen radius before the event.</p>
</div>

<div class="warning-box">
  <h4>VENUE ACOUSTICS</h4>
  <p>Hard floors and walls create reflections that can blur the interference pattern. The black felt helps absorb floor reflections. If the venue has hard walls nearby, the effect still works but the void zone will be less sharp. Best results in the middle of a large room, away from walls.</p>
</div>

<div class="warning-box">
  <h4>BLUETOOTH LATENCY</h4>
  <p>If using Bluetooth, all speakers must receive the signal at the same time. Any delay between speakers breaks the interference. Safest: use a wired aux splitter (£12). If Bluetooth, use speakers that support multipoint pairing from the same source, and test at home before the event. A 5ms delay shifts the pattern by 1.7cm — small but noticeable.</p>
</div>

<div class="section-label">DAY-BEFORE CHECKLIST</div>

<div class="checklist">
  <h3>APRIL 12 — THE NIGHT BEFORE</h3>
  <ul>
    <li>Charge all 6 speakers to 100%</li>
    <li>Charge phone, tablet, and power bank</li>
    <li>Test the full formation at home — play 432 Hz, walk to centre, verify sound change</li>
    <li>Load /formation-invisibility on tablet — confirm it works offline or on mobile data</li>
    <li>Load /sahara-formation on tablet</li>
    <li>Load /voidmessage on tablet</li>
    <li>Pack: speakers, stones, felt, chalk, tape measure, splitter cable, power bank, extension lead, tablet stand, posters</li>
    <li>Print the QR code or write void-stego-engine.replit.app on cards</li>
    <li>Set alarm — arrive 30 minutes early to set up the formation</li>
    <li>Practice the 3-minute demo script once out loud</li>
  </ul>
</div>

<div class="total-bar">
  <div class="label">RECOMMENDED BUDGET (PROFESSIONAL TIER)</div>
  <div class="amount">£329</div>
</div>

<footer>
  <p>PROJECT VOID — Manchester ICC Exhibit Plan</p>
  <p style="margin-top:6px;">April 13, 2026 — Formation Invisibility Live Demo</p>
  <p style="margin-top:6px;">355 Deane Road, Bolton BL3 5HL, England</p>
</footer>

</div>
</body>
</html>
"""
