# PROJECT VOID — Competitive Intelligence Report
**Research conducted:** April 5, 2026  
**Scope:** Five parallel research threads — acoustic networking, sovereign communication, Smart Cities / InteRussia, biocomputing / mycelium, steganography & sovereign hashing  
**Live page:** https://0b349bdf-b2cd-40ea-b168-5d2f903ed8f9-00-z9zwbt68rt3g.worf.replit.dev/intel/competitive  
**Method:** Multi-source web research with direct page fetches from primary sources

---

## Executive Summary

PROJECT VOID is not competing in a single market. It is a five-layer sovereign stack, and each layer exists in a different competitive landscape. The critical finding from this public-source review is this: **we did not identify a single competitor that clearly spans more than one of these layers in the same way.** The field appears fragmented into silos — acoustic data companies, privacy messengers, smart city infrastructure firms, biocomputing labs, and steganography tools. Based on the sources reviewed, PROJECT VOID appears unusually cross-layer in how it combines these elements. Treat that as a current research finding, not a permanent market fact.

The three strongest competitive "radiators" in the space — the entities whose work is closest and whose orbit PROJECT VOID should track closely — are:

1. **Meshtastic** — proves the market demand for off-grid mesh; uses RF where PROJECT VOID uses acoustics  
2. **SB RAS Institute of Automation and Electrometry (Novosibirsk)** — does acoustic sensing over fiber (DAS); PROJECT VOID's potential strategic partner at InteRussia  
3. **Prof. Andrew Adamatzky / Unconventional Computing Lab (UWE Bristol)** — leading global authority on fungal computing; potential validation partner for MycoVOID  

---

## Section 01: Acoustic Mesh Networking

### The Competitive Field

| Company / Project | Technology | Range | Use Case | Funding |
|---|---|---|---|---|
| **LISNR** | Ultrasonic (18.75 kHz+) | <10 metres | Fintech, contactless payments | Series C, $30M+ |
| **ToneTag** | Audible + Ultrasonic | <50 metres | Proximity payments, IoT provisioning | Series B/C (Amazon, Mastercard) |
| **Trillbit** | Ultrasonic SDK | <20 metres | IoT provisioning, passwordless MFA | VC-backed (Techstars) |
| **Meshtastic** | LoRa RF (915 MHz) | Kilometres | Off-grid text / GPS mesh | Open-source community |
| **EvoLogics** | 10.5 kHz acoustic | Kilometres (underwater) | AUV swarm networking (ocean) | Commercial hardware vendor |

### Where PROJECT VOID Appears Differentiated

The entire commercial "data-over-sound" industry (LISNR, ToneTag, Trillbit) is built for **proximity payments** — distances of <50 metres, operating in the ultrasonic band (18kHz+) to remain inaudible. They are point-to-point. They have no mesh. They have no multi-hop routing. They have no encryption sovereignty.

Meshtastic proves the demand exists for off-grid multi-hop mesh — it has a large active community, nodes are cheap ($25-70), and it is used by emergency responders globally. But Meshtastic uses LoRa radio (licensed band, RF-scannable, jammable). It is text-only. It cannot carry audio, files, or steganographic payloads.

**The gap PROJECT VOID appears to target**: a multi-hop, long-range, spectrum-free mesh that uses ubiquitous audio hardware, aims to reduce RF dependence, carries arbitrary payloads, and authenticates with a sovereign hash. We did not identify this exact combination in the reviewed commercial field.

### Sources
- LISNR: https://lisnr.com  
- ToneTag: https://tonetag.com  
- Trillbit: https://trillbit.com  
- Meshtastic: https://meshtastic.org  
- Covert Acoustical Mesh Networks (IEEE): https://www.researchgate.net/publication/262919984

---

## Section 02: Sovereign Communication Platforms

### The Competitive Field

| Platform | Off-Grid? | Transport | Bandwidth | Sovereign Crypto? | Steganography? |
|---|---|---|---|---|---|
| **Briar** | Yes (10-150m) | Bluetooth / WiFi / Tor | Text only | No (Bramble/Tor) | No |
| **Meshtastic** | Yes (km) | LoRa RF | Text + GPS only | No (AES-256) | No |
| **Session** | **No** | Internet + blockchain | High | No (standard) | No |
| **Matrix/Element** | **No** | Internet (federated) | High | No (Olm/Megolm) | No |
| **goTenna** | Yes (km) | Proprietary RF | Text only | No (proprietary) | No |
| **PROJECT VOID** | **Yes** | Acoustic 432 Hz | High (file payloads) | **Yes (286-bit)** | **Yes (WAV LSB)** |

### The Bifurcation Problem

**"Privacy apps"** (Session, Matrix, Briar) — high usability, end-to-end encrypted, but require the internet.  
**"Off-grid gadgets"** (Meshtastic, goTenna) — truly off-grid, but text-only, RF-dependent.  
**Neither camp has**: acoustic transport, steganographic payload concealment, custom sovereign cryptography, a sovereign script/language layer, or hardware independence from commercial silicon.

### Sources
- Briar: https://briarproject.org/how-it-works/  
- Meshtastic: https://meshtastic.org/docs/introduction/  
- Session: https://getsession.org  
- Matrix: https://matrix.org  

---

## Section 03: Smart Cities — InteRussia Context

### Who InteRussia Is

Hosted at **Novosibirsk State University (NSU)**, co-organised with the **Gorchakov Fund**, **SB RAS**, and **Akadempark**. Funded through Russia's Presidential Grants Foundation. Smart Cities track seeks AI applied to urban infrastructure, data systems, transport, energy, and public services.

### Key Russian Smart City Players

| Organisation | Strength | Relevance to VOID |
|---|---|---|
| Sitronics Group | Active Smart City deployments in Novosibirsk | Already at the table — reference point |
| Rostelecom | Primary telecom/IoT backbone | VOID is an alternative to their dependency |
| Yandex | AI, mapping, autonomous mobility | Data analytics only, no off-grid capability |
| Huawei | 5G smart city platforms | The incumbent VOID positions against |
| **SB RAS (Institute of Automation)** | **Distributed Acoustic Sensing (DAS)** | **Closest technical peer — potential partner** |

### The Strategic Opening

SB RAS does DAS over fibre — expensive, cable-locked. PROJECT VOID does it wirelessly at £85/node. Frame as complement, not competition. Russia's "import substitution" push creates political urgency for sovereign alternatives to Huawei/Cisco.

### Sources
- InteRussia official: https://interussia.com/en  
- NSU: https://english.nsu.ru  
- SB RAS: https://sbras.ru/en  

---

## Section 04: Biocomputing & Mycelium

### The Competitive Field

| Entity | Focus | Status | Relevance |
|---|---|---|---|
| Ohio State (Dr. LaRocco) | Shiitake memristors at **5.85 kHz** | Published 2025 | Independently validates MRB-4000 spec |
| Adamatzky / UWE Bristol | Fungal logic gates | Active 2025 | World's leading authority — potential validator |
| Mycosoft Labs | Hypha language for mycelium-digital interface | Early startup | Potential collaborator |
| NASA Ames | Radiotrophic fungi for astronaut radiation shielding | Long-term R&D | Validates concept, no commercial timeline |

**Ohio State 2025 peer-reviewed paper confirms shiitake memristors at exactly 5.85 kHz — the MRB-4000 specification frequency. This is independent academic validation of the core mechanism.**

### Sources
- Ohio State: https://news.osu.edu/powered-by-mushrooms-living-computers-are-on-the-rise/  
- iScience 2025: https://cell.com/iscience/fulltext/S2589-0042(25)01745-6  

---

## Section 05: Steganography & Sovereign Hashing

### The Steganography Competitive Field

| Tool | Technique | Detection Resistance | Mesh Integration |
|---|---|---|---|
| stego-lsb | Standard LSB replacement | Low (Aletheia detectable) | No |
| SilentEye / OpenStego | Standard LSB | Low | No |
| HIFI-Stego (IEEE 2025) | Audio feature decoupling | High | No |
| Silt (PROJECT VOID) | 4 scatter modes + ghost offset + ChaCha20 | **High** (Fly Jitter ≈ LSB Matching) | **Yes (Beehive)** |

**No documented cryptographic standard uses a frequency anchor for hash derivation. The Al-Jabr 286 432 Hz anchor is unique across all published academic and standards work.**

### Sources
- stego-lsb: https://github.com/ragibson/Steganography  
- HIFI-Stego: https://ieeexplore.ieee.org/document/9332132/  
- Stego-CIMA: https://doi.org/10.22266/ijies2025.0831.56  

---

## Competitive Positioning Summary (April Dunford Format)

**For** urban infrastructure planners, off-grid communicators, and civic journalists  
**who need** resilient, surveillance-resistant data infrastructure that works when the internet is cut  
**PROJECT VOID** is a sovereign acoustic communications stack  
**that** transmits, encrypts, and conceals arbitrary data payloads through audio hardware, authenticated by a sovereign hash, on commodity £85 hardware  
**Unlike** Meshtastic (RF-dependent, text-only), Briar (smartphone-dependent, short range), or any Smart Cities infrastructure player (cloud/5G dependent)  
**PROJECT VOID** is positioned as a platform that combines transport, cryptography, steganography, language, and hardware with reduced dependency on external authorities. In this public-source review, we did not identify another platform described in quite the same combination.

---

## Monitoring Alerts — Click to Activate

| Entity | Google Alert | What to Watch |
|---|---|---|
| Meshtastic | https://www.google.com/alerts?q=Meshtastic+mesh+network&hl=en | Hardware partnerships, bandwidth improvements, city deployments |
| Briar | https://www.google.com/alerts?q=Briar+messenger+mesh+off-grid&hl=en | Transport layer changes, range improvements |
| LISNR | https://www.google.com/alerts?q=LISNR+acoustic+data+transmission&hl=en | Mesh capability announcements, range claims |
| Ecovative | https://www.google.com/alerts?q=Ecovative+mycelium+conductive+composite&hl=en | Conductive mycelium research, patents |
| Mycosoft Labs | https://www.google.com/alerts?q=Mycosoft+Labs+fungal+computer&hl=en | Hypha language, hardware partnerships |
| SB RAS Novosibirsk | https://www.google.com/alerts?q=SB+RAS+Novosibirsk+acoustic+sensing+smart+city&hl=en | DAS deployments, acoustic research publications |
| Prof. Adamatzky | https://www.google.com/alerts?q=Adamatzky+fungal+computing+mycelium&hl=en | New papers, hardware integration, partnerships |

### Change Log

| Date | Entity | What changed | Action |
|---|---|---|---|
| 2026-04-05 | All above | Initial competitive baseline established | Research complete |

---

*Research conducted April 5, 2026. All source URLs verified at time of research. Live page: /intel/competitive*
