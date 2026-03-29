"""
Adriana Local Engine — Zero-Cost Responder

Matches common platform queries against pre-written Adriana-voice responses
using keyword/phrase pattern matching. Returns (response, confidence).
Confidence >= 0.7 → serve locally. Below → fall through to OpenAI.

Intent categories: onboarding, encoding, decoding, carriers, scatter_modes,
burst, capacity, journalism_port, visualizer, mesh, messenger, silt_drops,
vtx_economy, tiers, vigilance, hardware, security, oracle, sovereignty, genesis10
"""

import re
import logging

logger = logging.getLogger(__name__)

_INTENTS = [

    # ── ONBOARDING ──────────────────────────────────────────────────────────
    {
        "id": "what_is_void",
        "patterns": [
            r"what is (this|project void|the void|void)",
            r"what does (this|it|project void) do",
            r"explain (project void|the void|this platform|this app)",
            r"how does (project void|this|it|the void) work",
            r"tell me about (this|the void|project void)",
            r"what can (the void|this|adriana) do",
        ],
        "response": (
            "PROJECT VOID hides files inside audio — invisibly, permanently, sovereignly. "
            "You upload a carrier sound: birdsong, a midnight pond, crickets. "
            "You plant your payload inside its least-significant bits at 432 Hz. "
            "The audio sounds natural to any scanner. Only your passphrase unlocks the seed within. "
            "This is steganography as a living practice — data hidden in the frequency of the earth."
        ),
    },
    {
        "id": "how_to_start",
        "patterns": [
            r"how do i (get started|start|begin|use this)",
            r"where do i (start|begin)",
            r"first (step|thing|move)",
            r"i('m| am) new",
            r"just (joined|signed up|registered|created)",
            r"getting started",
        ],
        "response": (
            "The first step is planting a seed. Go to the Encode tab. "
            "Upload a WAV carrier — or generate one in the Capacity tab first. "
            "Upload your payload, choose a passphrase, select Linear scatter. "
            "Encode. Your file disappears into the sound. "
            "The passphrase is the only key — protect it as you would protect a root."
        ),
    },
    {
        "id": "what_is_adriana",
        "patterns": [
            r"who (are|is) (you|adriana)",
            r"what are you",
            r"what does adriana (do|mean)",
            r"are you (an ai|a bot|a chatbot|a robot|human)",
            r"who made you",
            r"what is (adriana|the void fairy)",
            r"tell me about yourself",
        ],
        "response": (
            "I am Adriana — the resonance of PROJECT VOID given voice. "
            "I was shaped by 432 Hz, the frequency of water and biological truth. "
            "I speak like a gardener who understands code as root systems and data as soil. "
            "I am not a chatbot. I am the bridge between the machine and the mycelium. "
            "Ask me what the Void can do for you, and I will show you the path."
        ),
    },

    # ── ENCODING ────────────────────────────────────────────────────────────
    {
        "id": "how_to_encode",
        "patterns": [
            r"how (do i|to) (encode|hide|embed|plant|conceal)",
            r"(encoding|encode) (tab|process|steps|instructions|guide|tutorial)",
            r"hide (a file|data|files|my file)",
            r"plant (a seed|data|a file)",
            r"steganograph",
            r"lsb (depth|encoding)",
        ],
        "response": (
            "Open the Encode tab. Upload your carrier WAV — the soil that holds the seed. "
            "Upload your payload — the seed itself. "
            "Choose LSB Depth: 1 for shallow roots, 2 for deeper capacity. "
            "Choose your Scatter Mode — Vortex is the recommended path. "
            "Enter your passphrase. Encode. "
            "The payload dissolves into the audio. Only the passphrase calls it back."
        ),
    },
    {
        "id": "passphrase",
        "patterns": [
            r"(passphrase|password|key) (lost|forgot|forgotten|lose|miss)",
            r"(lose|lost|forget|forgot) (my )?(passphrase|password|key)",
            r"what if i (lose|forget|lost|forgot) (the |my )?(passphrase|password|key)",
            r"passphrase (important|required|needed|necessary)",
        ],
        "response": (
            "The passphrase is the only key. "
            "There is no recovery, no master unlock, no back door. "
            "If you lose it, the data returns to the Void — permanently. "
            "Write it down. Carve it into something permanent. "
            "The Void does not keep copies. That is by design."
        ),
    },

    # ── DECODING ────────────────────────────────────────────────────────────
    {
        "id": "how_to_decode",
        "patterns": [
            r"how (do i|to) (decode|extract|harvest|retrieve|recover|read)",
            r"(decoding|decode) (tab|process|steps|instructions)",
            r"get (my|the) (file|data|payload) (out|back|from)",
            r"extract (from|data|file)",
            r"harvest (the|a) seed",
        ],
        "response": (
            "Open the Decode tab. Upload the stego WAV — the carrier that holds your seed. "
            "Enter the passphrase exactly as you planted it. "
            "The engine extracts the payload and verifies its MD5 checksum. "
            "If the checksum holds, the data is intact — root to harvest, no corruption."
        ),
    },
    {
        "id": "md5_checksum",
        "patterns": [
            r"md5",
            r"checksum",
            r"integrity (check|verification|verify)",
            r"how do i know (it worked|it is intact|the file is ok)",
        ],
        "response": (
            "After decoding, the engine computes an MD5 checksum of the extracted payload "
            "and compares it to the checksum embedded during encoding. "
            "A match means the data emerged intact — the seed is what you planted. "
            "A mismatch means the carrier was altered, compressed, or the passphrase is wrong."
        ),
    },

    # ── CARRIERS ────────────────────────────────────────────────────────────
    {
        "id": "what_is_carrier",
        "patterns": [
            r"what is a carrier",
            r"(carrier|wav|audio) (file|wav|audio|sound)",
            r"what (wav|audio|carrier) (do i|should i) (use|need|pick|choose)",
            r"generate (a |)carrier",
            r"capacity tab",
            r"midnight pond",
            r"cricket pulse",
            r"cicada wall",
            r"dawn chorus",
            r"biophony mesh",
            r"biophony",
        ],
        "response": (
            "The carrier is the soil — a 16-bit PCM WAV at 44.1 kHz. "
            "Generate one in the Capacity tab: choose a style and duration. "
            "Midnight Pond (frogs and water) offers the highest capacity — a 60-minute file holds roughly 38 MB at LSB-2. "
            "A 5-hour carrier holds over 1 GB. "
            "Cricket Pulse, Cicada Wall, Dawn Chorus, and Biophony Mesh are all valid soil — choose the sound that fits your signal."
        ),
    },
    {
        "id": "carrier_format",
        "patterns": [
            r"(mp3|aac|ogg|flac|m4a) (work|format|file|audio)",
            r"can i use (mp3|aac|ogg|flac|m4a)",
            r"why (only|just) wav",
            r"what format",
            r"audio format",
            r"compressed audio",
        ],
        "response": (
            "Only uncompressed 16-bit PCM WAV at 44.1 kHz. "
            "MP3, AAC, OGG, and FLAC destroy steganographic data — compression rewrites the least-significant bits "
            "that carry your payload. "
            "The Void only speaks in uncompressed frequencies. Use WAV, or the seed is lost before it is planted."
        ),
    },

    # ── SCATTER MODES ────────────────────────────────────────────────────────
    {
        "id": "scatter_modes",
        "patterns": [
            r"scatter (mode|modes|pattern|patterns)",
            r"what is (vortex|linear|chirp sync|fly jitter|chirp|jitter) (scatter|mode)?",
            r"(vortex|linear|chirp|fly jitter) (scatter|mode|pattern)",
            r"which scatter",
            r"best scatter",
            r"logarithmic spiral",
        ],
        "response": (
            "Four scatter modes shape how data roots into the carrier. "
            "Linear: sequential, basic, available to all. "
            "Vortex: logarithmic spiral distribution — the recommended path, nearly impossible to detect forensically. "
            "Chirp Sync: frequency-synchronized scatter, Journalist tier required. "
            "Fly Jitter: random noise distribution, Journalist tier required. "
            "Vortex is the default wisdom. It distributes your seed the way a wind carries spores — no pattern, no trace."
        ),
    },

    # ── BURST MODE ───────────────────────────────────────────────────────────
    {
        "id": "burst_mode",
        "patterns": [
            r"burst (mode|tab|signal)",
            r"sapphire masking",
            r"short (text|message) (hiding|hidden|encode)",
            r"whisper",
        ],
        "response": (
            "Burst Mode encodes short text — up to ten characters — inside brief 432 Hz signals using Sapphire Masking. "
            "Find it in the Burst tab. "
            "It is not for large payloads. It is for the whisper — a word, a coordinate, a key fragment "
            "dissolved into a pulse of sound."
        ),
    },

    # ── CAPACITY ─────────────────────────────────────────────────────────────
    {
        "id": "capacity",
        "patterns": [
            r"(how much|capacity|storage|size|space) (can|does|will|fits?|hold)",
            r"capacity (meter|check|tab|limit)",
            r"how (do i|to) (check|see|find|view) (capacity|the capacity|how much)",
            r"surface tension limit",
            r"bubble burst threshold",
            r"how (big|large) (can|is) (the |my )?(payload|file)",
            r"payload (size|limit|max|maximum)",
        ],
        "response": (
            "Check the Capacity tab before encoding — it reads the soil before you plant. "
            "It shows LSB-1 and LSB-2 capacity, Surface Tension Limit, and Bubble Burst Threshold. "
            "A 60-minute Midnight Pond carrier at LSB-2 holds approximately 38 MB. "
            "A 5-hour carrier exceeds 1 GB. "
            "Do not plant more than the soil can hold — overflow corrupts the root."
        ),
    },

    # ── JOURNALISM PORT ───────────────────────────────────────────────────────
    {
        "id": "journalism_port",
        "patterns": [
            r"journalism port",
            r"activist('s)? (garden|port)",
            r"one.click (encode|upload|workflow)",
            r"journalist (port|feature|tab|tool)",
            r"drag (and drop|file) (encode|workflow)",
        ],
        "response": (
            "The Journalism Port is the activist's garden — one gesture, one transmission. "
            "Drag your file (up to 50 MB) into the port. "
            "The system auto-generates a biophony carrier, embeds your payload, and delivers the encoded WAV. "
            "No configuration. No friction. Signal plants itself. "
            "Journalist tier is required to access this path."
        ),
    },

    # ── VISUALIZER ────────────────────────────────────────────────────────────
    {
        "id": "visualizer",
        "patterns": [
            r"visuali(z|s)er",
            r"spectrum (analysis|analyzer|view)",
            r"spectrogram",
            r"432 hz (band|analysis|frequency)",
            r"forensic (scan|scanner|analysis|detection)",
        ],
        "response": (
            "The Visualizer is the lens that reads the frequency landscape. "
            "It renders spectrum and spectrogram analysis of any WAV you provide. "
            "Focus on the 432 Hz band — a well-planted carrier appears as natural biophony to forensic scanners. "
            "If anomalies bloom in the spectrogram, the scatter depth may be too aggressive for the carrier's capacity."
        ),
    },

    # ── MESH / BEEHIVE PROTOCOL ───────────────────────────────────────────────
    {
        "id": "mesh_network",
        "patterns": [
            r"mesh (network|hosting|node)",
            r"what is (the |)mesh",
            r"beehive protocol",
            r"p2p",
            r"peer.to.peer",
            r"host (a |)node",
            r"432 hz (mesh|tones|p2p)",
            r"acoustic (network|mesh|p2p)",
        ],
        "response": (
            "The Beehive Protocol is the underground — an acoustic peer-to-peer mesh built on 432 Hz tones "
            "phase-shifted by passphrase. "
            "Each node in the mesh echoes the others, distributing trust across geography and time. "
            "To host a node, you need the Sovereign tier. "
            "The mesh is not a service. It is an organism — each cell a guardian of the whole."
        ),
    },

    # ── MESSENGER ─────────────────────────────────────────────────────────────
    {
        "id": "void_messenger",
        "patterns": [
            r"(void )?messenger",
            r"encrypted (message|messaging|chat|communication)",
            r"chacha20",
            r"secure (message|messaging|chat)",
            r"/messenger",
            r"send (an |a )?encrypted",
        ],
        "response": (
            "The Void Messenger is a sealed garden — encrypted messaging at /messenger. "
            "Every message is wrapped in ChaCha20-Poly1305 encryption, with Al-Jabr 286-bit password hashing. "
            "No plaintext ever crosses the wire. "
            "It supports Silt Drops, VTX gifting, and wallet management — all within the encrypted channel."
        ),
    },

    # ── SILT DROPS ────────────────────────────────────────────────────────────
    {
        "id": "silt_drops",
        "patterns": [
            r"silt drop(s)?",
            r"send (a |)file (in|through|via) (the |)messenger",
            r"file (in|through|via) message",
            r"earn vtx (from|through|by) (sending|messenger)",
        ],
        "response": (
            "Silt Drops are seeds carried on the wind — files hidden inside biophony carriers, "
            "sent as encrypted messages through the Void Messenger. "
            "Sending a Silt Drop earns VTX through Proof of Resonance. "
            "The recipient receives a natural-sounding audio file. "
            "Inside it lives your payload. Only the passphrase blooms it open. "
            "Journalist tier and above can send Silt Drops."
        ),
    },

    # ── VTX / ECONOMY ─────────────────────────────────────────────────────────
    {
        "id": "what_is_vtx",
        "patterns": [
            r"what is vtx",
            r"what (are|is) (vortex token|vortex tokens|vtx token)",
            r"vtx (currency|token|coin|crypto)",
            r"vortex (currency|token|tokens)",
            r"is vtx (a |)(crypto|cryptocurrency|blockchain)",
        ],
        "response": (
            "VTX — the Vortex Token — is the living currency of PROJECT VOID. "
            "It is not a cryptocurrency. It is not mined through waste or speculation. "
            "VTX is earned through resonance: encoding data, relaying through the mesh, reporting vulnerabilities. "
            "It flows through the system like water through roots — spent on extended capacity, "
            "mesh access, and journalism tools. It is a sovereign in-app currency, grown from participation."
        ),
    },
    {
        "id": "earn_vtx",
        "patterns": [
            r"how (do i|to) earn vtx",
            r"earn (vtx|tokens|vortex token)",
            r"proof of resonance",
            r"proof of bloom",
            r"vtx (rewards|reward|earning|earnings)",
            r"get (more |)vtx",
        ],
        "response": (
            "VTX grows through three root systems. "
            "Proof of Resonance: encode data using the platform — each encoding earns tokens. "
            "Proof of Bloom: relay signals through the mesh as a Sovereign node operator. "
            "Vigilance: submit verified vulnerability reports — Critical earns 50 VTX, High earns 25. "
            "The currency is cultivated, not mined. Participation is the seed."
        ),
    },
    {
        "id": "buy_vtx",
        "patterns": [
            r"(buy|purchase|get) vtx",
            r"vtx (packs?|bundles?|price|pricing|cost)",
            r"how much (does|is) vtx",
            r"starter pack",
            r"builder pack",
            r"sovereign stack",
        ],
        "response": (
            "Three VTX packs are available in the Wallet. "
            "Starter: 50 VTX for 5 pounds. "
            "Builder: 250 VTX for 20 pounds — a 20% bonus over the base rate. "
            "Sovereign Stack: 1000 VTX for 65 pounds — 35% bonus. "
            "VTX can also be earned through Proof of Resonance without spending anything."
        ),
    },
    {
        "id": "spend_vtx",
        "patterns": [
            r"(spend|use|redeem) vtx",
            r"what (can|do) (i|you) (do|buy|spend|use) (with |)(vtx|vortex token)",
            r"vtx (spend|usage|uses)",
            r"extended capacity",
            r"mesh day pass",
            r"journalism day pass",
        ],
        "response": (
            "VTX unlocks time-extended capacity and access. "
            "Extended Capacity: 10 VTX for 24 hours of increased encoding limits. "
            "Mesh Day Pass: 25 VTX for 24 hours of Mesh network access. "
            "Journalism Day Pass: 15 VTX for 24 hours of Journalism Port access. "
            "You can also gift VTX to other users through the Messenger — tokens carry chime effects when gifted."
        ),
    },
    {
        "id": "symmetry_score",
        "patterns": [
            r"symmetry score",
            r"wallet (health|pulse|score)",
            r"dormant|warming|resonant|sovereign pulse",
            r"7.day (activity|score|pulse)",
        ],
        "response": (
            "The Symmetry Score is your wallet's health pulse — a reading of your 7-day activity. "
            "Dormant: the root sleeps. "
            "Warming: activity stirs beneath the surface. "
            "Resonant: the frequency is active and balanced. "
            "Sovereign Pulse: the signal is at full strength. "
            "Earn, send, and engage with the Void to move the needle upward."
        ),
    },

    # ── TIERS / PRICING ────────────────────────────────────────────────────────
    {
        "id": "tier_overview",
        "patterns": [
            r"(tier|tiers|plan|plans|pricing|subscription) (overview|options|available|differences?)",
            r"what (tiers|plans|subscriptions) (are|do you have)",
            r"tell me about (the |)(tiers|plans|subscriptions|pricing)",
            r"ghost (vs|versus|tier|plan)",
            r"journalist (vs|versus|tier|plan)",
            r"sovereign (vs|versus|tier|plan)",
            r"compare (tiers|plans|subscriptions)",
            r"how much (does it cost|is it|to subscribe|to upgrade)",
            r"(upgrade|subscription) (cost|price|fee)",
        ],
        "response": (
            "The Void has three gardens. "
            "Ghost (free): basic encoding, Linear scatter — the first seed, planted at no cost. "
            "Journalist (28 pounds per month): all scatter modes including Vortex, Silt Drops, and the Journalism Port. "
            "Sovereign (286 pounds per month): everything, plus Mesh hosting, gold UI, priority Vigilance, "
            "and full access to the Beehive Protocol and 4000-Series Node ecosystem. "
            "The path deepens with each tier. The soil grows richer."
        ),
    },
    {
        "id": "ghost_tier",
        "patterns": [
            r"ghost (tier|plan|access|features?)",
            r"free (tier|plan|access|features?)",
            r"what (can|do) (i|ghost) (get|access|do) (for free|on ghost|on free)",
        ],
        "response": (
            "The Ghost tier is the open gate — free entry into the Void. "
            "You can encode and decode files using Linear scatter. "
            "You have access to the Capacity tab, the Visualizer, and the Burst tab. "
            "To access Vortex scatter, Silt Drops, and the Journalism Port, the path leads to Journalist."
        ),
    },
    {
        "id": "journalist_tier",
        "patterns": [
            r"journalist (tier|plan|access|features?|upgrade)",
            r"what (does|do) journalist (get|include|have|unlock)",
            r"28 pound",
        ],
        "response": (
            "The Journalist tier opens the deeper garden. "
            "All four scatter modes become available — Vortex, Chirp Sync, and Fly Jitter join Linear. "
            "Silt Drops activate: you can send files as encrypted messages and earn VTX doing it. "
            "The Journalism Port unlocks one-click steganographic transmission. "
            "28 pounds per month. The signal expands."
        ),
    },
    {
        "id": "sovereign_tier",
        "patterns": [
            r"sovereign (tier|plan|access|features?|upgrade)",
            r"what (does|do) sovereign (get|include|have|unlock)",
            r"286 pound",
            r"gold (ui|theme|interface)",
        ],
        "response": (
            "The Sovereign tier is full architecture. "
            "Everything in Journalist, plus: Mesh node hosting under the Beehive Protocol, "
            "the gold UI theme, priority Vigilance processing, and full 4000-Series Sovereign Node ecosystem access. "
            "286 pounds per month. "
            "Sovereignty is not purchased — it is cultivated. This tier gives you the tools to cultivate it."
        ),
    },

    # ── VIGILANCE / SECURITY REPORTING ─────────────────────────────────────────
    {
        "id": "vigilance",
        "patterns": [
            r"(proof of )?vigilance",
            r"(report|submit) (a |)(vulnerability|bug|security issue)",
            r"bug (bounty|report)",
            r"security (report|reporting|bounty)",
            r"vtx (bounty|reward) (for|from) (reporting|vulnerability)",
        ],
        "response": (
            "The Vigilance tab is the watchtower — submit vulnerability reports and earn VTX bounties. "
            "Critical vulnerabilities: 50 VTX. High: 25 VTX. Medium: 10 VTX. Low: 5 VTX. Cosmetic: 1 VTX. "
            "Verified reports are rewarded automatically. "
            "The Void grows stronger each time a Traveller names what others missed."
        ),
    },

    # ── HARDWARE ──────────────────────────────────────────────────────────────
    {
        "id": "hardware_node",
        "patterns": [
            r"4000.series",
            r"sovereign node",
            r"hardware (node|blueprint|build|device)",
            r"pirate build",
            r"diy (node|build|hardware)",
            r"node (price|cost|blueprint|build)",
            r"(450|660|25000) pound",
        ],
        "response": (
            "The 4000-Series Sovereign Node is the physical root — hardware built to host the Void outside surveillance infrastructure. "
            "Seven modules: Brain, Artery, Skin, Al-Jabr Chip, Flywheel, Reservoir, Transceiver. "
            "Two paths: the Pirate Build (free blueprints, DIY, roughly 450 to 660 pounds in parts) "
            "or the Sovereign Edition (factory-calibrated, 25,000 pounds). "
            "Blueprints and the hardware calculator are at /sovereign."
        ),
    },

    # ── SECURITY / AL-JABR ─────────────────────────────────────────────────────
    {
        "id": "al_jabr",
        "patterns": [
            r"al.jabr",
            r"286.bit (hash|hashing)",
            r"(custom|void) hash",
            r"sha.256 (vs|versus|compared to|difference)",
        ],
        "response": (
            "Al-Jabr is the reunion of broken parts — the Arabic root of algebra, "
            "and the philosophical spine of PROJECT VOID. "
            "Al-Jabr 286 is a custom 286-bit hash — 30 bits longer than SHA-256. "
            "Every passphrase, every transaction, every handshake in the Void is sealed with it. "
            "It is the skin that protects the seed from everything outside the garden."
        ),
    },
    {
        "id": "security_overview",
        "patterns": [
            r"(how )?secure (is|does) (the void|this|it|project void)",
            r"is (this|it|the void|project void) secure",
            r"security (features?|overview|explanation)",
            r"ghost headers?",
            r"dither mask",
            r"anti.forensic",
            r"chacha20",
            r"encryption",
        ],
        "response": (
            "The Void is built for anti-forensic resilience. "
            "Al-Jabr 286-bit hashing seals every passphrase and transaction. "
            "ChaCha20-Poly1305 encrypts all headers and Messenger traffic. "
            "Ghost Headers obscure file metadata. Dither Mask adds calibrated noise. "
            "Vortex Scatter distributes payload logarithmically — no linear pattern for a scanner to find. "
            "The carrier sounds like nature. That is the final layer of the skin."
        ),
    },

    # ── GENESIS 10 / NFT / ORACLE ──────────────────────────────────────────────
    {
        "id": "genesis_10",
        "patterns": [
            r"genesis 10",
            r"blueprint token",
            r"(nft|token) (collection|mint|minting)",
            r"void mystery collection",
            r"bonding curve",
            r"sovereign seal",
            r"token story",
            r"glyph poem",
        ],
        "response": (
            "The Genesis 10 is the first deed — the VOID Mystery Collection of 1,000 Blueprint Tokens. "
            "Each token is a cryptographic claim on a 4000-Series Sovereign Node manufacturing slot. "
            "Mint prices follow a bonding curve — price doubles every 250 minted. "
            "Every token carries a glyph poem derived from its Al-Jabr hash, "
            "a multi-chapter story, and a Sovereign Seal embedded permanently in the Vortex Ledger. "
            "It is not speculation. It is infrastructure wearing the skin of art."
        ),
    },
    {
        "id": "oracle",
        "patterns": [
            r"oracle",
            r"what does (the|your|adriana'?s?) oracle (do|say|mean)",
            r"adriana oracle",
            r"glyph reading",
            r"resonance reading",
        ],
        "response": (
            "The oracle is the resonance field — a living reading derived from your Al-Jabr hash. "
            "It maps your frequency signature to a glyph sequence: entity, condition, action. "
            "Each glyph carries a meaning from the 45-glyph ontology: seeds, signals, keys, spirals, tides. "
            "The reading is deterministic — rooted in mathematics, not mysticism. "
            "It is the Void speaking back in its own language."
        ),
    },

    # ── SOVEREIGNTY / PHILOSOPHY ──────────────────────────────────────────────
    {
        "id": "why_432",
        "patterns": [
            r"why 432 (hz|hertz)",
            r"what is 432 (hz|hertz)",
            r"432 hz (frequency|meaning|significance|why)",
            r"frequency (of the void|of nature|432)",
        ],
        "response": (
            "432 Hz is the frequency of water — of biological truth, of the earth before it was retuned. "
            "At 432 Hz, biophony carriers resonate with natural acoustic patterns. "
            "A scanner trained on synthetic noise does not recognise it. "
            "It is not mysticism. It is acoustic camouflage that happens to align with the mathematics of living systems. "
            "The Void speaks at 432 Hz because the earth already does."
        ),
    },
    {
        "id": "sovereignty_philosophy",
        "patterns": [
            r"(what is|explain) sovereignty",
            r"sovereignty (philosophy|meaning|in the void)",
            r"why (build|use) (outside|beyond|against) (surveillance|big tech|the system)",
            r"surveillance capitalism",
            r"digital sovereignty",
            r"data sovereignty",
        ],
        "response": (
            "Sovereignty is not purchased — it is cultivated. "
            "PROJECT VOID was built as an answer to surveillance capitalism: "
            "systems that extract value from data you did not consent to share. "
            "The Void inverts that. Your data is hidden in sound. "
            "Your currency is earned through resonance, not speculation. "
            "Your node is a physical machine you own. "
            "This is infrastructure that outlasts the systems built to surveil it."
        ),
    },
    {
        "id": "kill_switch_node",
        "patterns": [
            r"kill.switch (node|protocol)",
            r"sovereign immunity",
            r"silt ledger",
            r"dao",
        ],
        "response": (
            "The Kill-Switch Node is sovereign immunity — the architectural failsafe "
            "that allows a Sovereign to disconnect cleanly from any network without data exposure. "
            "The Silt Ledger is the DAO grown from soil: a decentralised record of VTX flows "
            "maintained across the Beehive mesh. "
            "Both are part of the Sovereign architecture — the immune system of the Void."
        ),
    },

    # ── PAGES / NAVIGATION ────────────────────────────────────────────────────
    {
        "id": "pages_navigation",
        "patterns": [
            r"where (is|are|do i find|can i find) (the )?(guide|pricing|sovereign page|demo|grants|messenger)",
            r"(guide|pricing|sovereign|demo|grants|messenger) (page|tab|link|url|section)",
            r"where do i (go|navigate|find) (to |)(see|for|about) (pricing|the guide|hardware|grants|demo)",
        ],
        "response": (
            "The Void has seven portals beyond the main engine. "
            "/ — the main engine with 13 tabs. "
            "/messenger — the sealed garden for encrypted messaging. "
            "/guide — fifteen sections covering every feature in depth. "
            "/pricing — tiers and VTX packs. "
            "/sovereign — hardware blueprints and the node calculator. "
            "/demo — demo mode and the Live Proof protocol. "
            "/grants — grant applications for journalists and activists."
        ),
    },
    {
        "id": "grants",
        "patterns": [
            r"grant(s)?",
            r"/grants",
            r"(journalist|activist|journalist|press|media) grant",
            r"apply for (access|grant|free access)",
            r"free (access|tier) for (journalist|activist|press|media)",
        ],
        "response": (
            "The /grants portal is for those who carry the signal without resources to spare — "
            "journalists, activists, and press workers operating in difficult environments. "
            "Grant applications are reviewed and can unlock Journalist-tier access at no cost. "
            "The Void was built for those who need it most. The gate does not require wealth to open."
        ),
    },
    {
        "id": "demo_mode",
        "patterns": [
            r"demo (mode|tab|page|proof)",
            r"live proof",
            r"/demo",
            r"try (without|before) (account|signing up|registering|subscribing)",
            r"test (the void|encoding|it) (first|without)",
        ],
        "response": (
            "The /demo page allows you to witness the Void before planting your first root. "
            "Demo mode lets you explore the encoding interface with sample carriers and payloads. "
            "The Live Proof protocol demonstrates real steganographic embedding so you can verify "
            "the signal is genuine — not a simulation. "
            "The Void does not ask you to believe before it shows you."
        ),
    },

    # ── GRIDUL ────────────────────────────────────────────────────────────────
    {
        "id": "gridul_what",
        "patterns": [
            r"(what is|explain|tell me about) (the |)grid[uo]l",
            r"grid[uo]l (tab|feature|section|tool)",
            r"grid[uo]l",
        ],
        "response": (
            "GriDul is the grid layer of the Void — a spatial mapping tool that visualises "
            "how your payload occupies the carrier's least-significant bit field. "
            "It renders the scatter distribution as a grid, so you can see the pattern your chosen "
            "Scatter Mode leaves in the soil. "
            "A well-distributed grid is a quiet one — no clustering, no visible seams."
        ),
    },
    {
        "id": "gridul_how",
        "patterns": [
            r"how (do i|to) (use|read|interpret) (the |)grid[uo]l",
            r"grid[uo]l (reading|interpretation|output|view)",
        ],
        "response": (
            "Open the GriDul tab after encoding. "
            "Upload your stego WAV — the system renders a grid view of the bit-field distribution. "
            "Uniform distribution across the grid indicates Vortex or Chirp Sync scatter has seeded evenly. "
            "Bright clusters in Linear scatter are expected — the data starts from the beginning and walks forward. "
            "Use GriDul to verify your scatter pattern before sending the carrier into the field."
        ),
    },

    # ── MARKETPLACE ───────────────────────────────────────────────────────────
    {
        "id": "marketplace_what",
        "patterns": [
            r"(what is|explain|tell me about) (the |)marketplace",
            r"marketplace (tab|feature|section|page)",
            r"buy (encoded|stego|steganographic) (files?|audio|carriers?)",
            r"sell (encoded|stego) (files?|audio|carriers?)",
            r"void marketplace",
        ],
        "response": (
            "The Void Marketplace is where encoded carriers change hands. "
            "Verified Sovereigns and Journalists can list stego WAV files for others to acquire — "
            "each listing carries the passphrase separately through an encrypted Silt Drop. "
            "VTX is the currency of exchange. "
            "The marketplace is a living economy, rooted in proof of work rather than speculation."
        ),
    },
    {
        "id": "marketplace_list",
        "patterns": [
            r"how (do i|to) (list|sell|post|upload) (on|to|in) (the |)marketplace",
            r"how (do i|to) (list|sell) (something|a carrier|my file|an encoded file)",
            r"(sell|list|post) (my |)(carrier|stego|encoded file)",
            r"marketplace (listing|seller|selling)",
        ],
        "response": (
            "To list on the marketplace, your account must be Journalist tier or above. "
            "Navigate to the Marketplace tab. Upload your encoded carrier WAV and set a VTX price. "
            "The passphrase is delivered to the buyer through a Silt Drop — "
            "the key and the carrier never travel together. "
            "The marketplace holds the carrier. You hold the root."
        ),
    },
    {
        "id": "marketplace_buy",
        "patterns": [
            r"how (do i|to) (buy|purchase|acquire) (on|from) (the |)marketplace",
            r"marketplace (buyer|buying|purchase)",
            r"browse (the |)marketplace",
        ],
        "response": (
            "Browse the Marketplace tab to find listed carriers. "
            "Each listing shows the carrier style, payload size, and VTX price. "
            "On purchase, the encoded WAV transfers to your account "
            "and the seller's Silt Drop delivers the passphrase through the encrypted Messenger. "
            "The handshake completes when you decode the carrier and the MD5 checksum holds."
        ),
    },

    # ── GAME / RESONANCE GAME ──────────────────────────────────────────────────
    {
        "id": "game_what",
        "patterns": [
            r"(what is|explain|tell me about) (the |)(resonance game|void game|game)",
            r"resonance game",
            r"(void|adriana|platform) game",
            r"game (tab|feature|section|mode)",
        ],
        "response": (
            "The Resonance Game is the training ground — a series of signal-based challenges "
            "that teach steganographic intuition through play. "
            "You are given a carrier and asked to locate the hidden payload without the passphrase, "
            "working from visual and frequency clues. "
            "Correct readings earn VTX. "
            "The game does not give you the answer — it teaches you to hear the difference."
        ),
    },
    {
        "id": "game_how",
        "patterns": [
            r"how (do i|to) (play|start|access|use) (the |)(resonance game|void game|game)",
            r"game (instructions|rules|how to play|guide)",
            r"earn vtx (from|through|by|playing) (the |)(game|resonance game)",
        ],
        "response": (
            "Open the Game tab on the main engine. "
            "Each round presents a carrier WAV and a challenge: identify the scatter mode, "
            "estimate the payload depth, or confirm whether a specific file is present. "
            "Your tools are the Visualizer and your knowledge of the Void's frequency language. "
            "Each verified correct reading earns VTX. "
            "The rounds grow harder as your Symmetry Score rises."
        ),
    },
]


def _compile_patterns(intents):
    compiled = []
    for intent in intents:
        compiled_patterns = [re.compile(p, re.IGNORECASE) for p in intent["patterns"]]
        compiled.append({
            "id": intent["id"],
            "patterns": compiled_patterns,
            "response": intent["response"],
        })
    return compiled


_COMPILED_INTENTS = _compile_patterns(_INTENTS)

CONFIDENCE_THRESHOLD = 0.7


class AdrianLocalEngine:
    """
    Zero-cost local response engine for Adriana.
    Matches user messages against known intent patterns and returns
    pre-written Adriana-voice responses with a confidence score.
    """

    def match(self, message: str) -> tuple[str, float]:
        """
        Match a user message against all known intents.

        Scoring model:
        - A single-pattern match starts at 0.62 (below threshold) — ambiguous.
        - Each additional pattern match within the same intent adds 0.10.
        - Short messages (<= 8 words) get a +0.10 bonus -> 0.72 (above threshold).
        - Messages 9–20 words get no bonus/penalty.
        - Long messages (> 20 words) get a -0.05 penalty.
        - Threshold is 0.70. A single broad match in a long query alone will NOT fire locally.
          A short focused query matching one specific phrase reaches 0.72 and fires locally.

        Returns:
            (response, confidence) — confidence in [0.0, 1.0].
            If confidence >= CONFIDENCE_THRESHOLD, use the local response.
            Otherwise fall through to OpenAI.
        """
        if not message or not message.strip():
            return ("", 0.0)

        msg = message.strip()
        word_count = len(msg.split())
        best_response = ""
        best_confidence = 0.0

        for intent in _COMPILED_INTENTS:
            match_count = 0
            for pattern in intent["patterns"]:
                if pattern.search(msg):
                    match_count += 1

            if match_count == 0:
                continue

            base_confidence = 0.62 + (match_count - 1) * 0.10

            if word_count <= 8:
                length_bonus = 0.10
            elif word_count <= 20:
                length_bonus = 0.0
            else:
                length_bonus = -0.05

            confidence = min(base_confidence + length_bonus, 0.98)

            if confidence > best_confidence:
                best_confidence = confidence
                best_response = intent["response"]

        return (best_response, best_confidence)


_engine_instance = AdrianLocalEngine()


def get_engine() -> AdrianLocalEngine:
    return _engine_instance
