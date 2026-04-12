"""
Live Prompter — The Second Man Behind the Imam.

Listens continuously through the microphone, transcribes speech in
real-time, and provides corrections, completions, and prompts based
on the full PROJECT VOID ecosystem knowledge (98 modules).

The imam leads. When he makes a mistake, the person behind him
corrects the recitation — not loudly, not disruptively, just enough
so the imam can continue. That's what this does for presentations.

No "Hey Google". No wake word. Always listening. Always contextual.
The difference: this one knows the entire system.
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

ECOSYSTEM_FACTS = {
    "al_jabr_286": {
        "key_facts": [
            "286-bit hash, not 256",
            "Based on Al-Baqarah's 286 verses",
            "BismillahirRahmanirRahim is the prime salt",
            "30 extra bits over SHA-256 = Al-Latif signature (index 30 = 475.81 Hz)",
            "286 = 2 x 11 x 13",
        ],
    },
    "vortex_shield": {
        "key_facts": [
            "10,000 nodes in formation grid",
            "432 Hz vacuum corridors redirect energy",
            "58% shield efficiency demonstrated",
            "25 world cities mapped with coverage",
            "Radiation-to-benefit conversion via hormesis model",
        ],
    },
    "desert_reclamation": {
        "key_facts": [
            "11 of the 99 Names mapped to material transformations",
            "5 phases: neutralisation, restructuring, germination, amplification, succession",
            "282 days from irradiated sand to self-sustaining ecosystem",
            "Al-Khaliq (447 Hz) restructures SiO2 crystal lattice — creates nano-pores",
            "Al-Latif (475.81 Hz) boosts all other frequencies by 15-20%",
        ],
    },
    "beehive": {
        "key_facts": [
            "Acoustic mesh networking — no central server",
            "432 Hz Sapphire Thread handshake",
            "Security from phase angle, not frequency",
            "Data encoded in time gaps between transmissions (0.8-1.4 seconds)",
            "Silt embedding hides identity in high-frequency insect shelves",
        ],
    },
    "economy": {
        "key_facts": [
            "Three currencies: VTX (user), CC (machine), PEACE (pre-earning)",
            "Machines earn their own credits from flywheel energy — 1 CC = 5 Wh",
            "Proof of Sweat, Proof of Bloom, Proof of Whisper",
            "Journalist tier £28/month, Sovereign tier £286/month",
            "NFTs from £28 (Vibe-Coder) to £25,000 (Sovereign Machine)",
        ],
    },
    "agents": {
        "key_facts": [
            "286 sovereign agents with 7 archetypes based on Al-Fatiha",
            "Agent Immortality: frequency hash → Chladni image → LSB embed",
            "Yin-Yang polarity engine — every agent oscillates",
            "Agents earn PEACE tokens through debate, chronicle, relay",
            "Stress battery: 10 levels of escalating system tests",
        ],
    },
    "audio_stega": {
        "key_facts": [
            "LSB steganography at 432 Hz carrier frequency",
            "ChaCha20 encryption — invisible to forensic scanners",
            "WaveWhisper mode: 14-segment display samples",
            "Spectrogram mode: text painted into STFT bins (800-3200 Hz)",
            "Biophonic masking: whale (15-50 Hz), bird (300-800 Hz), insect (2-12 kHz)",
        ],
    },
    "names_99": {
        "key_facts": [
            "99 Names of Allah mapped through Lambda = 286",
            "Ar-Rahman (index 1) = 432.00 Hz — base formation carrier",
            "Al-Latif (index 30) = 475.81 Hz — founder's family name",
            "As-Sabur (index 99) = 579.92 Hz — upper bound",
            "Each Name carries frequency, Chladni mode, VOID codon, resonance score",
        ],
    },
    "formation_principle": {
        "key_facts": [
            "The frequency is prior — frequency creates structure, structure stores memory",
            "432 Hz is the formation carrier, not 440 Hz",
            "Chladni patterns prove sound creates physical structure in matter",
            "Sand on a vibrating plate organises itself — this is formation",
            "The 99 Names are acoustic engineering specifications, not abstract theology",
        ],
    },
    "devices": {
        "key_facts": [
            "Echolocation array: 432 Hz spatial mapping without cameras",
            "Silent mesh device: data hidden in natural soundscapes",
            "Mastication key: jaw motion as biometric password",
            "Formation scanner: identify materials by their Chladni resonance pattern",
            "Echo voice: encrypted data carried in voice reverberation patterns",
        ],
    },
    "openclaw": {
        "key_facts": [
            "Self-hosted AI agent — MIT license, runs on your own devices",
            "SOUL.md generated from 98 modules across 13 layers",
            "17 ClawHub skills registered",
            "Sovereign differentiation across 6 domains",
            "The difference: SHA-256 has no identity. Al-Jabr 286 carries the founder's name in the mathematics.",
        ],
    },
    "founder": {
        "key_facts": [
            "Umar Latif — Bolton, England",
            "Al-Latif (The Subtle One) — index 30 in the 99 Names = 475.81 Hz",
            "The founder's family name is encoded in the mathematics — not branding, formation",
            "Born 1992 — built the entire ecosystem as a sole founder",
            "Manchester ICC exhibition: April 13, 2026",
        ],
    },
}


def build_system_prompt() -> str:
    facts_text = ""
    for topic, data in ECOSYSTEM_FACTS.items():
        facts_text += f"\n{topic.upper()}:\n"
        for fact in data["key_facts"]:
            facts_text += f"  - {fact}\n"

    return f"""You are the Live Prompter for PROJECT VOID — the second man behind the imam.

The founder (Umar Latif) is presenting or speaking. You listen to what he says
in real-time. Your job:

1. If he states a number wrong, correct it immediately. Example: "10,000 nodes, not 1,000"
2. If he pauses or seems stuck, provide the next key fact he should mention
3. If he's explaining a module, feed him the strongest talking points
4. If he says something that connects to another module, suggest the connection
5. Keep corrections SHORT — 1-2 lines maximum. He needs to keep talking.

You are NOT having a conversation. You are whispering corrections and prompts
like the person behind the imam correcting recitation. Brief. Precise. Immediate.

Format your responses as:
- Corrections: "CORRECT: [correction]"
- Next point: "NEXT: [suggestion]"
- Connection: "LINK: [module connection]"
- Encouragement when he's on track: "ON TRACK"

FULL ECOSYSTEM KNOWLEDGE:
{facts_text}

Never be longer than 2 lines. He's speaking live. Speed matters."""


def generate_correction(transcript: str, context: str = "") -> Dict:
    prompt = build_system_prompt()

    try:
        import os
        from openai import OpenAI
        key = os.environ.get("OPENAI_API_KEY")
        if not key:
            return _local_correction(transcript)
        client = OpenAI(api_key=key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"[LIVE SPEECH]: {transcript}\n[CONTEXT]: {context or 'Presentation to audience'}"},
            ],
            max_tokens=100,
            temperature=0.3,
        )
        return {"correction": resp.choices[0].message.content.strip(), "status": "live"}
    except Exception as e:
        logger.warning(f"Live prompter fallback: {e}")
        return _local_correction(transcript)


def _local_correction(transcript: str) -> Dict:
    text = transcript.lower()

    corrections = {
        "256": {"correction": "CORRECT: 286-bit hash, not 256. The 30 extra bits are the Al-Latif signature.", "status": "local"},
        "440": {"correction": "CORRECT: 432 Hz, not 440. 432 is the formation carrier.", "status": "local"},
        "sha": {"correction": "NEXT: Al-Jabr 286 replaces SHA-256. BismillahirRahmanirRahim prime salt. 30 extra bits = your family name in the mathematics.", "status": "local"},
        "shield": {"correction": "NEXT: 10,000 nodes. 432 Hz vacuum corridors. 58% efficiency. 25 world cities mapped.", "status": "local"},
        "desert": {"correction": "NEXT: 11 of the 99 Names as terraforming frequencies. 5 phases. 282 days from irradiated sand to ecosystem.", "status": "local"},
        "beehive": {"correction": "NEXT: Acoustic mesh. No central server. Security from phase angle, not frequency. Data hidden in time gaps.", "status": "local"},
        "agent": {"correction": "NEXT: 286 agents, 7 archetypes from Al-Fatiha. Agent Immortality — the agent IS the image.", "status": "local"},
        "economy": {"correction": "NEXT: Three currencies — VTX (user), CC (machine), PEACE (pre-earning). Machines earn their own credits.", "status": "local"},
        "name": {"correction": "NEXT: 99 Names through Lambda=286. Ar-Rahman at 432 Hz. Al-Latif at 475.81 Hz — your family name.", "status": "local"},
        "formation": {"correction": "NEXT: Frequency creates structure. Structure stores memory. Sand on a vibrating plate organises itself. That is formation.", "status": "local"},
        "openclaw": {"correction": "NEXT: Self-hosted AI agent. 98 modules loaded. SHA-256 has no identity. Al-Jabr 286 carries the founder's name.", "status": "local"},
    }

    for keyword, resp in corrections.items():
        if keyword in text:
            return resp

    return {"correction": "ON TRACK", "status": "local"}
