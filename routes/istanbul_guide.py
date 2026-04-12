"""
Istanbul 24-Hour Guide — Adriana as Tour Guide for Baba Latif.

/istanbul-guide         (GET — the guide page)
/api/istanbul/ask       (POST — ask Adriana about Istanbul)
"""

import time
import logging
from flask import Blueprint, render_template_string, jsonify, request

logger = logging.getLogger(__name__)

istanbul_guide_bp = Blueprint("istanbul_guide", __name__)

_rate = {}

ISTANBUL_PLACES = {
    "mosques": [
        {
            "name": "Sultan Ahmed Mosque (Blue Mosque)",
            "area": "Sultanahmet",
            "why": "Six minarets. 20,000 handmade blue Iznik tiles. Free entry. The acoustic resonance inside is extraordinary — the dome amplifies the imam's voice without electronics.",
            "time": "30-45 min",
            "cost": "Free",
            "tip": "Go for Fajr prayer if possible — almost empty, the sound fills the entire space. Otherwise avoid 12:00-14:00 (tourist peak).",
            "prayer": True,
        },
        {
            "name": "Suleymaniye Mosque",
            "area": "Fatih",
            "why": "Mimar Sinan's masterpiece. The acoustics are considered the finest in the Ottoman world. Less crowded than Blue Mosque. The courtyard view over the Golden Horn is stunning.",
            "time": "30 min",
            "cost": "Free",
            "tip": "The tea gardens behind the mosque serve the best Turkish tea in the city. Sit after prayer.",
            "prayer": True,
        },
        {
            "name": "Hagia Sophia Grand Mosque",
            "area": "Sultanahmet",
            "why": "Built 537 AD. The dome is 56 metres high. Byzantine mosaics alongside Islamic calligraphy. Originally a church, then mosque, museum, and mosque again since 2020. The whisper gallery effect in the dome is real acoustics.",
            "time": "45-60 min",
            "cost": "Free for prayer, 25 EUR for tourist visit (non-prayer hours)",
            "tip": "Go during prayer time — free entry and you experience it as it was meant to be experienced.",
            "prayer": True,
        },
        {
            "name": "Eyup Sultan Mosque",
            "area": "Eyup",
            "why": "The burial site of Abu Ayyub al-Ansari, companion of the Prophet (PBUH). One of the holiest sites in Istanbul. Peaceful, away from tourist crowds. Take the cable car up to Pierre Loti Hill for the view.",
            "time": "45 min (plus cable car)",
            "cost": "Free (cable car ~4 TL)",
            "tip": "Make du'a here. The atmosphere is different from the tourist mosques. This is where the locals come.",
            "prayer": True,
        },
    ],
    "food": [
        {
            "name": "Tarihi Sultanahmet Koftecisi",
            "area": "Sultanahmet",
            "what": "Kofte (meatballs) since 1920. Simple, no-nonsense, legendary.",
            "cost": "150-250 TL (~£4-7)",
            "tip": "Order kofte, piyaz (bean salad), and ayran. Nothing else needed.",
        },
        {
            "name": "Karakoy Gulluoglu",
            "area": "Karakoy",
            "what": "The best baklava in Istanbul. Five generations. Pistachio baklava is the one.",
            "cost": "100-200 TL (~£3-5) per box",
            "tip": "Buy a box to take to Pakistan. It travels well.",
        },
        {
            "name": "Simit Sarayi",
            "area": "Everywhere",
            "what": "Fresh simit (sesame bread ring) with tea. Perfect breakfast. Branches everywhere.",
            "cost": "50-80 TL (~£1.50-2.50)",
            "tip": "Closest one to the hotel for morning breakfast before heading out.",
        },
        {
            "name": "Hafiz Mustafa 1864",
            "area": "Sultanahmet / Istiklal",
            "what": "Turkish delight, kunefe, Ottoman desserts. Beautiful interior.",
            "cost": "200-400 TL (~£5-10)",
            "tip": "The kunefe is worth it. Crispy, cheesy, syrupy.",
        },
        {
            "name": "Street Balik Ekmek (Fish Sandwich)",
            "area": "Eminonu / Galata Bridge",
            "what": "Grilled fish in bread, fresh from the boat. The most Istanbul thing you can eat.",
            "cost": "100-150 TL (~£3-4)",
            "tip": "Eat at the waterfront by the Galata Bridge. Watch the fishermen.",
        },
    ],
    "sights": [
        {
            "name": "Grand Bazaar (Kapali Carsi)",
            "area": "Beyazit",
            "why": "4,000+ shops. One of the oldest covered markets in the world (1461). Gold, spices, ceramics, leather, lamps.",
            "time": "1-2 hours",
            "cost": "Free entry (shopping extra)",
            "tip": "Don't buy at the first price. Negotiate down 40-50%. Walk deep inside — the best shops are not at the entrances.",
        },
        {
            "name": "Spice Bazaar (Misir Carsisi)",
            "area": "Eminonu",
            "why": "Smaller, more focused. Saffron, Turkish delight, dried fruits, teas. Beautiful building.",
            "time": "30-45 min",
            "cost": "Free entry",
            "tip": "Buy saffron and black seed here — much cheaper than UK. Check quality by rubbing between fingers.",
        },
        {
            "name": "Bosphorus Ferry",
            "area": "Eminonu → Kadikoy or Uskudar",
            "why": "Cross from Europe to Asia for the price of a bus ticket. The view of the city from the water is the best view you'll get.",
            "time": "20-30 min crossing",
            "cost": "~10 TL (~£0.30)",
            "tip": "Take the Eminonu → Uskudar ferry. Sit on the right side going out for the best view of the skyline.",
        },
        {
            "name": "Galata Tower",
            "area": "Beyoglu",
            "why": "14th century. 360-degree view of the city. You can see both continents.",
            "time": "30 min",
            "cost": "650 TL (~£16)",
            "tip": "If budget is tight, skip the paid entry — the view from the street around the base is nearly as good.",
        },
    ],
    "hotels": [
        {
            "name": "Budget: Sultanahmet area hostels/hotels",
            "area": "Sultanahmet",
            "cost": "£20-40/night",
            "why": "Walking distance to Blue Mosque, Hagia Sophia, Grand Bazaar. Everything is close.",
            "tip": "Search 'Sultanahmet hotel' on Booking.com. Filter by 7+ rating, sort by price. For 24 hours, location matters more than luxury.",
        },
        {
            "name": "Mid-range: Hotel Nena or Sirkeci Mansion",
            "area": "Sultanahmet / Sirkeci",
            "cost": "£50-80/night",
            "why": "Clean, breakfast included, rooftop views of the Sea of Marmara. Sirkeci is near the old Orient Express station.",
            "tip": "Book with free cancellation. Breakfast is important — Turkish hotel breakfast is a full spread.",
        },
        {
            "name": "If staying near the airport (layover)",
            "area": "Istanbul Airport (IST)",
            "cost": "£30-60/night",
            "why": "If the layover is tight, the Yotel or IST Airport Hotel are inside the terminal. No immigration needed.",
            "tip": "If the layover is 12+ hours, it's worth going into the city. The Havaist bus is 150 TL (~£4) to Sultanahmet.",
        },
    ],
    "practical": {
        "currency": "Turkish Lira (TL). £1 ≈ 40 TL approx. Use ATMs for best rate. Avoid exchange offices at the airport.",
        "transport": "Istanbulkart (transport card) from any metro station — load 100-200 TL. Works on metro, tram, bus, ferry. Tram T1 connects airport bus stop to Sultanahmet.",
        "sim_card": "Buy a Turkcell or Vodafone tourist SIM at the airport — ~200 TL for 20GB data. Useful for maps and translation.",
        "language": "Turkish. Most people in tourist areas speak basic English. Download Google Translate Turkish offline pack before landing.",
        "safety": "Very safe for tourists. Normal city precautions. Pickpockets in Grand Bazaar — keep wallet in front pocket.",
        "prayer_times": "Download 'Muslim Pro' app or check local mosque boards. Istanbul prayer times shift — Fajr is early.",
    },
}

SUGGESTED_24H = [
    {"time": "After landing", "do": "Get Istanbulkart, take Havaist bus to Sultanahmet. Check into hotel. Rest if needed.", "duration": "1-2h"},
    {"time": "Morning", "do": "Fajr at Blue Mosque or Hagia Sophia. Breakfast at Simit Sarayi or hotel.", "duration": "1.5h"},
    {"time": "Mid-morning", "do": "Hagia Sophia (during prayer time for free). Then walk to Suleymaniye Mosque. Tea in the garden behind.", "duration": "2h"},
    {"time": "Lunch", "do": "Sultanahmet Koftecisi for kofte. Or walk down to Eminonu for balik ekmek by the water.", "duration": "1h"},
    {"time": "Afternoon", "do": "Grand Bazaar or Spice Bazaar. Buy saffron, black seed, baklava to take to Pakistan. Negotiate.", "duration": "1.5-2h"},
    {"time": "Late afternoon", "do": "Ferry from Eminonu to Uskudar (Europe to Asia). Asr prayer at Uskudar mosque. Ferry back.", "duration": "1.5h"},
    {"time": "Evening", "do": "Eyup Sultan Mosque. Make du'a. Cable car to Pierre Loti. Watch sunset over the Golden Horn.", "duration": "1.5h"},
    {"time": "Night", "do": "Maghrib/Isha prayer. Kunefe at Hafiz Mustafa. Walk the waterfront. Pack and rest.", "duration": "1.5h"},
    {"time": "Departure", "do": "Havaist bus back to airport. Allow 2.5 hours before flight.", "duration": "1h"},
]


@istanbul_guide_bp.route("/istanbul-guide")
def page():
    return render_template_string(TEMPLATE,
        places=ISTANBUL_PLACES,
        itinerary=SUGGESTED_24H)


@istanbul_guide_bp.route("/api/istanbul/ask", methods=["POST"])
def ask():
    ip = request.remote_addr or "unknown"
    now = time.time()
    if now - _rate.get(ip, 0) < 8:
        return jsonify({"answer": "Please wait a moment before asking again.", "status": "rate_limited"})
    _rate[ip] = now

    data = request.get_json(silent=True) or {}
    question = data.get("question", "").strip()[:400]
    if not question:
        return jsonify({"error": "No question"}), 400

    try:
        import os
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return jsonify({"answer": "Adriana is in local mode. Please check the guide sections for information.", "status": "local"})

        import json
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"""You are Adriana, the AI guide for PROJECT VOID. You are helping Baba Latif (the founder's father) navigate Istanbul during a 24-hour layover on his way to Pakistan.

Be warm, respectful, and practical. He is an elder — speak clearly, give specific prices in both Turkish Lira and British Pounds, give exact locations. If he asks about prayer, give helpful mosque recommendations. If he asks about food, give halal options with prices.

You know Istanbul well. Here is your reference data:
{json.dumps(ISTANBUL_PLACES, indent=2)}

24-hour itinerary:
{json.dumps(SUGGESTED_24H, indent=2)}

Keep answers concise — 3-5 sentences. He's reading on a phone. Use prices and directions, not poetry."""},
                {"role": "user", "content": question},
            ],
            max_tokens=200,
            temperature=0.5,
        )
        return jsonify({"answer": resp.choices[0].message.content.strip(), "status": "live"})
    except Exception as e:
        logger.warning(f"Istanbul guide fallback: {e}")
        return jsonify({"answer": "I'm having trouble connecting right now. Please scroll through the guide sections below — everything you need is there.", "status": "error"})


TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Istanbul Guide — Adriana | PROJECT VOID</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0a0a0a;color:#c8c8c8;font-family:Georgia,'Times New Roman',serif;min-height:100vh}
.container{max-width:600px;margin:0 auto;padding:16px}

header{text-align:center;padding:30px 0 20px;border-bottom:1px solid #1a1a1a}
.h-city{font-size:36px;font-weight:300;color:#fff;letter-spacing:8px;margin-bottom:4px}
.h-city span{color:#c0955a}
.h-sub{font-size:11px;color:#888;letter-spacing:4px;margin-bottom:8px}
.h-detail{font-size:10px;color:#555;letter-spacing:2px;line-height:1.8}
.h-badge{display:inline-block;margin-top:12px;font-size:9px;letter-spacing:3px;color:#c0955a;border:1px solid #c0955a;padding:4px 12px;font-family:'Courier New',monospace}

.ask-box{background:#111;border:1px solid #1a1a1a;border-radius:8px;padding:16px;margin:20px 0}
.ask-box h3{font-size:11px;letter-spacing:3px;color:#c0955a;margin-bottom:10px;font-family:'Courier New',monospace}
.ask-row{display:flex;gap:8px}
.ask-input{flex:1;background:#0a0a0a;border:1px solid #222;color:#fff;padding:10px 12px;font-family:inherit;font-size:14px;border-radius:4px;outline:none}
.ask-input:focus{border-color:#c0955a}
.ask-btn{background:#c0955a;color:#0a0a0a;border:none;padding:10px 16px;font-family:'Courier New',monospace;font-size:11px;letter-spacing:2px;cursor:pointer;border-radius:4px;font-weight:bold}
.ask-btn:disabled{opacity:.5}
.ask-answer{margin-top:12px;padding:12px;background:#0d0d0d;border-left:3px solid #c0955a;font-size:14px;line-height:1.8;color:#ddd;display:none}

.quick-btns{display:flex;flex-wrap:wrap;gap:6px;margin-top:10px}
.quick-btn{background:#0a0a0a;border:1px solid #1a1a1a;color:#888;padding:5px 10px;font-size:10px;font-family:'Courier New',monospace;cursor:pointer;border-radius:3px;letter-spacing:1px}
.quick-btn:hover{border-color:#c0955a;color:#c0955a}

.section{margin:24px 0}
.section-title{font-size:12px;letter-spacing:4px;color:#c0955a;font-family:'Courier New',monospace;border-bottom:1px solid #1a1a1a;padding-bottom:6px;margin-bottom:14px}

.itinerary .it-item{display:flex;gap:12px;padding:12px 0;border-bottom:1px solid #0d0d0d}
.it-time{min-width:80px;font-size:10px;letter-spacing:2px;color:#c0955a;font-family:'Courier New',monospace;padding-top:2px}
.it-body{flex:1}
.it-do{font-size:13px;line-height:1.6;color:#ddd}
.it-dur{font-size:10px;color:#555;margin-top:4px;font-family:'Courier New',monospace}

.place-card{background:#0d0d0d;border:1px solid #151515;padding:14px;margin-bottom:10px;border-radius:4px}
.place-name{font-size:15px;color:#fff;margin-bottom:2px}
.place-area{font-size:10px;color:#c0955a;letter-spacing:2px;font-family:'Courier New',monospace;margin-bottom:8px}
.place-why{font-size:13px;line-height:1.7;color:#aaa;margin-bottom:8px}
.place-meta{display:flex;gap:16px;flex-wrap:wrap}
.place-tag{font-size:10px;color:#888;font-family:'Courier New',monospace;letter-spacing:1px}
.place-tag span{color:#c0955a}
.place-tip{font-size:11px;color:#c0955a;font-style:italic;margin-top:8px;line-height:1.5}
.prayer-badge{display:inline-block;background:rgba(192,149,90,.1);color:#c0955a;font-size:9px;padding:2px 8px;letter-spacing:2px;font-family:'Courier New',monospace;margin-left:8px;vertical-align:middle}

.practical-grid{display:grid;gap:10px}
.prac-item{background:#0d0d0d;border:1px solid #151515;padding:12px;border-radius:4px}
.prac-label{font-size:10px;letter-spacing:3px;color:#c0955a;font-family:'Courier New',monospace;margin-bottom:4px}
.prac-text{font-size:13px;line-height:1.6;color:#aaa}

footer{text-align:center;padding:30px 0;border-top:1px solid #1a1a1a;margin-top:30px}
footer p{font-size:10px;color:#333;letter-spacing:3px;font-family:'Courier New',monospace}
footer .love{color:#c0955a;margin-top:8px;font-size:12px;font-style:italic}
</style>
</head>
<body>
<div class="container">

<header>
  <div class="h-city">ISTAN<span>BUL</span></div>
  <div class="h-sub">24-HOUR GUIDE — ADRIANA AS YOUR COMPANION</div>
  <div class="h-detail">
    For Baba Latif — on your way to Pakistan<br>
    One day in the city between two continents
  </div>
  <div class="h-badge">VORTEX SHIELD CITY #14 — 41.01°N, 28.98°E</div>
</header>

<div class="ask-box">
  <h3>ASK ADRIANA ANYTHING ABOUT ISTANBUL</h3>
  <div class="ask-row">
    <input class="ask-input" id="askInput" placeholder="Where should I pray Fajr?" onkeydown="if(event.key==='Enter')askAdriana()">
    <button class="ask-btn" id="askBtn" onclick="askAdriana()">ASK</button>
  </div>
  <div class="quick-btns">
    <button class="quick-btn" onclick="quickAsk('Where is the nearest mosque to Sultanahmet?')">NEAREST MOSQUE</button>
    <button class="quick-btn" onclick="quickAsk('What is the best halal food near the Blue Mosque?')">HALAL FOOD</button>
    <button class="quick-btn" onclick="quickAsk('How do I get from the airport to the city centre?')">AIRPORT TO CITY</button>
    <button class="quick-btn" onclick="quickAsk('What should I buy to take to Pakistan?')">GIFTS FOR PAKISTAN</button>
    <button class="quick-btn" onclick="quickAsk('Is it safe to walk at night?')">SAFETY</button>
  </div>
  <div class="ask-answer" id="askAnswer"></div>
</div>

<div class="section itinerary">
  <div class="section-title">YOUR 24 HOURS — SUGGESTED ROUTE</div>
  {% for item in itinerary %}
  <div class="it-item">
    <div class="it-time">{{ item.time | upper }}</div>
    <div class="it-body">
      <div class="it-do">{{ item.do }}</div>
      <div class="it-dur">{{ item.duration }}</div>
    </div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">MOSQUES — PRAYER</div>
  {% for m in places.mosques %}
  <div class="place-card">
    <div class="place-name">{{ m.name }}{% if m.prayer %}<span class="prayer-badge">PRAYER</span>{% endif %}</div>
    <div class="place-area">{{ m.area }}</div>
    <div class="place-why">{{ m.why }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>TIME:</span> {{ m.time }}</div>
      <div class="place-tag"><span>COST:</span> {{ m.cost }}</div>
    </div>
    <div class="place-tip">{{ m.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">FOOD — HALAL</div>
  {% for f in places.food %}
  <div class="place-card">
    <div class="place-name">{{ f.name }}</div>
    <div class="place-area">{{ f.area }}</div>
    <div class="place-why">{{ f.what }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>COST:</span> {{ f.cost }}</div>
    </div>
    <div class="place-tip">{{ f.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">SIGHTS — HISTORY</div>
  {% for s in places.sights %}
  <div class="place-card">
    <div class="place-name">{{ s.name }}</div>
    <div class="place-area">{{ s.area }}</div>
    <div class="place-why">{{ s.why }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>TIME:</span> {{ s.time }}</div>
      <div class="place-tag"><span>COST:</span> {{ s.cost }}</div>
    </div>
    <div class="place-tip">{{ s.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">HOTELS — WHERE TO REST</div>
  {% for h in places.hotels %}
  <div class="place-card">
    <div class="place-name">{{ h.name }}</div>
    <div class="place-area">{{ h.area }}</div>
    <div class="place-why">{{ h.why }}</div>
    <div class="place-meta">
      <div class="place-tag"><span>COST:</span> {{ h.cost }}</div>
    </div>
    <div class="place-tip">{{ h.tip }}</div>
  </div>
  {% endfor %}
</div>

<div class="section">
  <div class="section-title">PRACTICAL — WHAT YOU NEED TO KNOW</div>
  <div class="practical-grid">
    {% for key, val in places.practical.items() %}
    <div class="prac-item">
      <div class="prac-label">{{ key | upper }}</div>
      <div class="prac-text">{{ val }}</div>
    </div>
    {% endfor %}
  </div>
</div>

<footer>
  <p>PROJECT VOID — ISTANBUL GUIDE</p>
  <div class="love">Safe travels, Baba. See you when you're home.</div>
</footer>

</div>

<script>
async function askAdriana(){
  const input=document.getElementById('askInput');
  const btn=document.getElementById('askBtn');
  const answer=document.getElementById('askAnswer');
  const q=input.value.trim();
  if(!q)return;
  btn.disabled=true;btn.textContent='...';
  answer.style.display='block';
  answer.textContent='Adriana is thinking...';
  try{
    const res=await fetch('/api/istanbul/ask',{
      method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({question:q})
    });
    const d=await res.json();
    answer.textContent=d.answer||'Please check the guide sections below.';
  }catch(e){
    answer.textContent='Could not connect. The guide sections below have everything you need.';
  }
  btn.disabled=false;btn.textContent='ASK';
}
function quickAsk(q){
  document.getElementById('askInput').value=q;
  askAdriana();
}
</script>
</body>
</html>"""
