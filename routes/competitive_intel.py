from flask import Blueprint, render_template

competitive_intel_bp = Blueprint("competitive_intel", __name__)


@competitive_intel_bp.route("/intel/competitive")
def competitive_intel():
    data = _get_intel_data()
    return render_template("competitive_intel.html", data=data)


def _get_intel_data():
    radiators = [
        {
            "name": "Meshtastic",
            "url": "https://meshtastic.org",
            "tag": "Radiator 01",
            "why": (
                "Proven the market. Hundreds of thousands of off-grid mesh nodes "
                "deployed globally by emergency responders, hikers, and civic "
                "infrastructure operators. Hardware costs $25–70. They have the "
                "community. They don't have the protocol."
            ),
            "gap": (
                "LoRa RF only — scannable, jammable, spectrum-adjacent. Text and "
                "GPS coordinates only — no file payloads, no audio, no steganography. "
                "Smartphone-dependent for the UI. Cannot carry a sovereign hash."
            ),
            "color": "teal",
        },
        {
            "name": "SB RAS Institute of Automation & Electrometry",
            "url": "https://www.sbras.ru/en",
            "tag": "Radiator 02 — InteRussia",
            "why": (
                "Located at the fellowship venue in Novosibirsk. Already deploying "
                "Distributed Acoustic Sensing (DAS) — urban acoustic monitoring "
                "over fibre optic cables. They understand acoustic networks and "
                "Smart Cities from the inside."
            ),
            "gap": (
                "DAS requires physical cable installation — expensive, "
                "infrastructure-locked, cannot reach where cable doesn't go. "
                "Beehive Protocol is the wireless acoustic complement: sensing "
                "where cable cannot reach, at £85/node."
            ),
            "color": "gold",
        },
        {
            "name": "Prof. Andrew Adamatzky — Unconventional Computing Lab",
            "url": "https://uwe.ac.uk/research/centres-and-groups/unconventional-computing",
            "tag": "Radiator 03 — MycoVOID",
            "why": (
                "The world's leading published authority on fungal computing. "
                "Demonstrated AND/OR logic gates from electrical spikes in oyster "
                "fungi. Ohio State 2025 independently confirmed shiitake memristors "
                "at 5.85 kHz — the exact frequency of the MRB-4000 spec."
            ),
            "gap": (
                "Academic research only — no hardware integration, no "
                "communications stack, no sovereign energy harvesting. "
                "Potential validation partner for MycoVOID, not a competitor."
            ),
            "color": "violet",
        },
    ]

    sections = [
        {
            "id": "acoustic",
            "num": "01",
            "title": "Acoustic Mesh Networking",
            "subtitle": "Beehive Protocol — 432 Hz sovereign mesh",
            "summary": (
                "The entire commercial 'data-over-sound' industry (LISNR, ToneTag, "
                "Trillbit) is built for proximity payments — distances under 50 metres, "
                "ultrasonic band (18 kHz+), point-to-point, no mesh, no multi-hop "
                "routing. Meshtastic proves the market for off-grid mesh, but uses RF "
                "(LoRa, 915 MHz). The 432 Hz audible band for multi-hop acoustic mesh "
                "is commercially unoccupied."
            ),
            "competitors": [
                {
                    "name": "LISNR",
                    "range": "<10 m",
                    "transport": "Ultrasonic 18.75 kHz+",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Fintech / contactless payments",
                    "funding": "Series C · $30M+",
                    "url": "https://lisnr.com",
                },
                {
                    "name": "ToneTag",
                    "range": "<50 m",
                    "transport": "Audible + Ultrasonic",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Proximity payments / IoT",
                    "funding": "Series B/C (Amazon, Mastercard)",
                    "url": "https://tonetag.com",
                },
                {
                    "name": "Trillbit",
                    "range": "<20 m",
                    "transport": "Ultrasonic SDK",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "IoT provisioning / MFA",
                    "funding": "VC (Techstars)",
                    "url": "https://trillbit.com",
                },
                {
                    "name": "Meshtastic",
                    "range": "Kilometres",
                    "transport": "LoRa RF 915 MHz",
                    "mesh": "Yes",
                    "sovereign": "No",
                    "use": "Off-grid text / GPS",
                    "funding": "Open-source community",
                    "url": "https://meshtastic.org",
                },
                {
                    "name": "EvoLogics",
                    "range": "Kilometres (underwater)",
                    "transport": "10.5 kHz acoustic",
                    "mesh": "Limited",
                    "sovereign": "No",
                    "use": "AUV swarm networking",
                    "funding": "Commercial hardware",
                    "url": "https://evologics.de",
                },
                {
                    "name": "PROJECT VOID — Beehive",
                    "range": "Multi-hop (Seven Seas)",
                    "transport": "Acoustic 432 Hz",
                    "mesh": "Yes — 7 hop limit",
                    "sovereign": "Yes — Al-Jabr 286",
                    "use": "Sovereign mesh / Smart Cities",
                    "funding": "Self-funded",
                    "url": "/apply/interussia",
                },
            ],
            "void_edge": (
                "No commercial player uses 432 Hz for mesh networking. "
                "Everyone else went ultrasonic to avoid the challenges that make "
                "Beehive unique. The multi-hop architecture with sovereign phase-shift "
                "authentication exists nowhere else in this space."
            ),
        },
        {
            "id": "comms",
            "num": "02",
            "title": "Sovereign Communication",
            "subtitle": "Silt + Beehive + Adriana — layered sovereignty",
            "summary": (
                "The privacy communication market in 2025 is split: "
                "internet-dependent apps with good bandwidth (Session, Matrix), "
                "or off-grid gadgets with text-only bandwidth (Meshtastic, goTenna). "
                "The empty cell — off-grid, high bandwidth, sovereign crypto, "
                "steganographic concealment, hardware independence — is PROJECT VOID."
            ),
            "competitors": [
                {
                    "name": "Briar",
                    "range": "10–150 m",
                    "transport": "Bluetooth / WiFi / Tor",
                    "mesh": "Yes (limited)",
                    "sovereign": "No",
                    "use": "Activists / journalists",
                    "funding": "Donations (2.6M+ downloads)",
                    "url": "https://briarproject.org",
                },
                {
                    "name": "Meshtastic",
                    "range": "Kilometres",
                    "transport": "LoRa RF",
                    "mesh": "Yes",
                    "sovereign": "No",
                    "use": "Off-grid text / GPS",
                    "funding": "Open-source",
                    "url": "https://meshtastic.org",
                },
                {
                    "name": "Session",
                    "range": "Internet required",
                    "transport": "Blockchain onion routing",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Privacy messaging",
                    "funding": "Session Technology Foundation",
                    "url": "https://getsession.org",
                },
                {
                    "name": "Matrix / Element",
                    "range": "Internet required",
                    "transport": "Federated HTTPS",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Enterprise / govts",
                    "funding": "Element (commercial) + Foundation",
                    "url": "https://element.io",
                },
                {
                    "name": "goTenna",
                    "range": "Kilometres",
                    "transport": "Proprietary RF",
                    "mesh": "Yes",
                    "sovereign": "No",
                    "use": "Military / outdoor",
                    "funding": "Series C",
                    "url": "https://gotennamesh.com",
                },
                {
                    "name": "PROJECT VOID",
                    "range": "Multi-hop acoustic",
                    "transport": "Acoustic 432 Hz",
                    "mesh": "Yes",
                    "sovereign": "Yes — 286-bit + Adriana",
                    "use": "Sovereign comms / journalism",
                    "funding": "Self-funded",
                    "url": "/apply/interussia",
                },
            ],
            "void_edge": (
                "The only platform combining acoustic transport, file-payload "
                "steganography (Silt), sovereign 45-glyph script (Adriana), and "
                "286-bit cryptographic independence — running on £85 hardware "
                "with zero cloud dependency."
            ),
        },
        {
            "id": "biocomp",
            "num": "03",
            "title": "Biocomputing & Mycelium",
            "subtitle": "MycoVOID — MRB-4000 bio-battery · RMW-01 Bio-Steel",
            "summary": (
                "Academic fungal computing research is producing logic gates and "
                "memristors in controlled lab environments. Ohio State confirmed "
                "shiitake memristors at 5.85 kHz — the exact MRB-4000 frequency — "
                "in peer-reviewed 2025 work. The commercial field is thin; "
                "MycoVOID is hardware-integrated where academia remains bench-level."
            ),
            "competitors": [
                {
                    "name": "Ohio State (Dr. LaRocco)",
                    "range": "Lab (5.85 kHz)",
                    "transport": "Shiitake memristors",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Academic — confirms MRB-4000 spec",
                    "funding": "University research",
                    "url": "https://news.osu.edu/powered-by-mushrooms-living-computers-are-on-the-rise/",
                },
                {
                    "name": "UWE Bristol (Adamatzky)",
                    "range": "Lab",
                    "transport": "Fungal logic gates",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Academic — leading authority",
                    "funding": "EPSRC / university",
                    "url": "https://uwe.ac.uk",
                },
                {
                    "name": "Mycosoft Labs",
                    "range": "Software / FCI",
                    "transport": "Hypha language",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Mycelium-to-digital interface",
                    "funding": "Early-stage startup",
                    "url": "https://medium.com/@mycosoft.inc",
                },
                {
                    "name": "NASA Ames",
                    "range": "Lunar / space",
                    "transport": "Radiotrophic shielding",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Astronaut radiation protection",
                    "funding": "Federal (NASA)",
                    "url": "https://nasa.gov",
                },
                {
                    "name": "PROJECT VOID — MycoVOID",
                    "range": "Hardware-integrated",
                    "transport": "Ganoderma lucidum energy harvesting",
                    "mesh": "Yes — node housing",
                    "sovereign": "Yes — Grown Not Smelted",
                    "use": "Sovereign bio-battery + chassis",
                    "funding": "Self-funded",
                    "url": "/apply/interussia",
                },
            ],
            "void_edge": (
                "Only platform integrating mycelium biocomputing into sovereign "
                "communications hardware. Ganoderma lucidum for radiotrophic "
                "energy harvesting is unoccupied in commercial and academic research. "
                "Ohio State's 2025 peer-reviewed work independently validates "
                "the MRB-4000's 5.85 kHz shiitake memristor specification."
            ),
        },
        {
            "id": "stega",
            "num": "04",
            "title": "Steganography & Sovereign Hashing",
            "subtitle": "Silt Journalism · Al-Jabr 286 — 432 Hz anchor",
            "summary": (
                "The steganography tool market (stego-lsb, SilentEye, OpenStego) "
                "uses standard LSB replacement — detectable by Aletheia and similar "
                "steganalysis tools. Silt's scatter modes (Fly Jitter, Chirp Sync) "
                "behave like LSB Matching (±1), significantly harder to detect. "
                "No documented cryptographic hash in any academic or standards body "
                "uses a frequency anchor. Al-Jabr 286's 432 Hz anchor is unique."
            ),
            "competitors": [
                {
                    "name": "stego-lsb (Python)",
                    "range": "Standard LSB",
                    "transport": "WAV / image",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "General steganography",
                    "funding": "Open-source",
                    "url": "https://github.com/ragibson/Steganography",
                },
                {
                    "name": "SilentEye / OpenStego",
                    "range": "Standard LSB",
                    "transport": "Image / WAV",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "GUI steganography",
                    "funding": "Open-source",
                    "url": "https://www.openstego.com",
                },
                {
                    "name": "HIFI-Stego (IEEE TASLP 2025)",
                    "range": "Audio feature decoupling",
                    "transport": "Audio (MP3/WAV)",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "AI-resistant audio hiding",
                    "funding": "Academic",
                    "url": "https://ieeexplore.ieee.org/document/9332132/",
                },
                {
                    "name": "SecureDrop",
                    "range": "Tor metadata hiding",
                    "transport": "HTTPS / Tor",
                    "mesh": "No",
                    "sovereign": "No",
                    "use": "Whistleblowing / journalism",
                    "funding": "Freedom of the Press Foundation",
                    "url": "https://securedrop.org",
                },
                {
                    "name": "PROJECT VOID — Silt",
                    "range": "4 scatter modes + ChaCha20",
                    "transport": "16-bit PCM WAV",
                    "mesh": "Yes — Beehive acoustic",
                    "sovereign": "Yes — Al-Jabr 286 ghost offset",
                    "use": "Sovereign journalism / covert telemetry",
                    "funding": "Self-funded",
                    "url": "/apply/interussia",
                },
            ],
            "void_edge": (
                "The only steganographic platform integrated into a decentralised "
                "acoustic mesh. No other tool uses a frequency-anchored hash (432 Hz) "
                "for ghost offset derivation. SecureDrop hides metadata; Silt hides "
                "the existence of communication itself inside ambient audio."
            ),
        },
    ]

    monitoring = [
        {
            "name": "Meshtastic",
            "url": "https://meshtastic.org",
            "alert": "https://www.google.com/alerts?q=Meshtastic+mesh+network&hl=en",
            "watch": "Hardware partnerships, bandwidth improvements, Smart City deployments",
        },
        {
            "name": "Briar",
            "url": "https://briarproject.org",
            "alert": "https://www.google.com/alerts?q=Briar+messenger+mesh+off-grid&hl=en",
            "watch": "Transport layer changes, range improvements, new relay modes",
        },
        {
            "name": "LISNR",
            "url": "https://lisnr.com",
            "alert": "https://www.google.com/alerts?q=LISNR+acoustic+data+transmission&hl=en",
            "watch": "Mesh capability announcements, range extension claims, partnerships",
        },
        {
            "name": "Ecovative Design",
            "url": "https://ecovative.com",
            "alert": "https://www.google.com/alerts?q=Ecovative+mycelium+conductive+composite&hl=en",
            "watch": "Conductive mycelium research, patents, smart materials announcements",
        },
        {
            "name": "Mycosoft Labs",
            "url": "https://medium.com/@mycosoft.inc",
            "alert": "https://www.google.com/alerts?q=Mycosoft+Labs+fungal+computer&hl=en",
            "watch": "Hypha language development, hardware partnerships, funding rounds",
        },
        {
            "name": "SB RAS Novosibirsk",
            "url": "https://sbras.ru/en",
            "alert": "https://www.google.com/alerts?q=SB+RAS+Novosibirsk+acoustic+sensing+smart+city&hl=en",
            "watch": "DAS deployments, acoustic research publications, InteRussia collaborations",
        },
        {
            "name": "Prof. Adamatzky / UWE Bristol",
            "url": "https://uwe.ac.uk",
            "alert": "https://www.google.com/alerts?q=Adamatzky+fungal+computing+mycelium&hl=en",
            "watch": "New papers, hardware integration work, industry partnerships",
        },
    ]

    return {
        "radiators": radiators,
        "sections": sections,
        "monitoring": monitoring,
        "research_date": "April 5, 2026",
        "sources_count": 27,
        "threads": 5,
    }
