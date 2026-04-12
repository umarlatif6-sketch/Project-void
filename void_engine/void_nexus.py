"""
VOID Nexus — The central nervous system of PROJECT VOID.

Every engine module is a node. Every node connects to every other node.
The Nexus maps all connections, measures system coherence, and provides
a unified status view of the entire organism.

The Formation Principle applied to software:
  - Each module vibrates at its own frequency (purpose)
  - Connections between modules create interference patterns
  - When all modules are connected, the system reaches coherence
  - Coherence = the system behaves as one organism, not separate parts
"""

import time
import math
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


NEXUS_NODES = {
    "al_jabr_286": {
        "name": "Al-Jabr 286",
        "category": "CRYPTOGRAPHIC",
        "frequency": 286.0,
        "description": "Sovereign 286-bit hash — the identity layer. Every agent, transaction, and formation is sealed with this hash.",
        "file": "void_engine/al_jabr_286.py",
        "connections": ["sovereign_agents_286", "stega", "beehive", "chronicle", "vortex_wallet", "agent_immortality", "mycelium"],
    },
    "stega": {
        "name": "LSB Steganography",
        "category": "CRYPTOGRAPHIC",
        "frequency": 432.0,
        "description": "Audio/image steganography engine — 432 Hz carrier with ChaCha20 encryption. Data hidden in frequency patterns.",
        "file": "void_engine/stega.py",
        "connections": ["al_jabr_286", "beehive", "agent_immortality", "vortex_shield"],
    },
    "beehive": {
        "name": "Beehive Mesh",
        "category": "NETWORK",
        "frequency": 528.0,
        "description": "Peer-to-peer mesh networking — temporal channels, phase-shift node IDs. The communication backbone.",
        "file": "void_engine/beehive.py",
        "connections": ["al_jabr_286", "stega", "vortex_shield", "sovereign_agents_286"],
    },
    "adriana_core": {
        "name": "Adriana AI",
        "category": "INTELLIGENCE",
        "frequency": 639.0,
        "description": "AI interface — natural language to sovereign codons. The voice of the system.",
        "file": "void_engine/adriana_core.py",
        "connections": ["codon_heart", "adriana_scl", "skill_router", "chronicle", "vortex_wallet"],
    },
    "codon_heart": {
        "name": "Codon Heart",
        "category": "INTELLIGENCE",
        "frequency": 396.0,
        "description": "Third Brain memory compression — user interactions encoded as codon chains. The memory system.",
        "file": "void_engine/codon_heart.py",
        "connections": ["adriana_core", "adriana_scl", "chronicle"],
    },
    "adriana_scl": {
        "name": "Sovereign Code Layer",
        "category": "INTELLIGENCE",
        "frequency": 741.0,
        "description": "Hash-to-poem translation — raw data becomes sovereign narrative. The language layer.",
        "file": "void_engine/adriana_scl.py",
        "connections": ["al_jabr_286", "adriana_core", "codon_heart"],
    },
    "vortex_wallet": {
        "name": "Vortex Wallet (VTX)",
        "category": "ECONOMIC",
        "frequency": 852.0,
        "description": "Internal VTX/PEACE token ledger — mint, transfer, balance. The economic bloodstream.",
        "file": "void_engine/vortex_wallet.py",
        "connections": ["al_jabr_286", "adriana_core", "sovereign_agents_286", "stance_science", "mesa_sandbox"],
    },
    "mesa_sandbox": {
        "name": "PEACE Economy",
        "category": "ECONOMIC",
        "frequency": 174.0,
        "description": "Agent-based economic simulation — PEACE velocity, redistribution, stress testing. Grade A+.",
        "file": "void_engine/mesa_sandbox.py",
        "connections": ["vortex_wallet", "sovereign_agents_286"],
    },
    "sovereign_agents_286": {
        "name": "Sovereign Agents 286",
        "category": "AGENTS",
        "frequency": 286.0,
        "description": "286 autonomous agents with archetypes, memory, scars, and PEACE balances. The population.",
        "file": "void_engine/sovereign_agents_286.py",
        "connections": ["al_jabr_286", "vortex_wallet", "agent_immortality", "yin_yang", "mesa_sandbox", "beehive"],
    },
    "agent_immortality": {
        "name": "Agent Immortality",
        "category": "AGENTS",
        "frequency": 432.0,
        "description": "Frequency hash → Chladni image → LSB embed. The agent IS the image. Destroy the machine, keep the frequency.",
        "file": "void_engine/agent_immortality.py",
        "connections": ["sovereign_agents_286", "al_jabr_286", "stega", "chronicle"],
    },
    "yin_yang": {
        "name": "Yin-Yang 286 Engine",
        "category": "POLARITY",
        "frequency": 286.0,
        "description": "Polarity engine — every agent oscillates between YIN and YANG. The balance system.",
        "file": "void_engine/yin_yang_286.py",
        "connections": ["sovereign_agents_286", "al_jabr_286", "stance_science"],
    },
    "vortex_shield": {
        "name": "Vortex Shield Network",
        "category": "DEFENCE",
        "frequency": 432.0,
        "description": "10,000-node energy absorption grid — vacuum corridors redirect blast energy. 432 Hz radiation conversion.",
        "file": "void_engine/vortex_shield.py",
        "connections": ["beehive", "stega", "al_jabr_286", "stance_science"],
    },
    "stance_science": {
        "name": "Stance Science (QiSync)",
        "category": "BIOMETRIC",
        "frequency": 7.83,
        "description": "5 foundation stances mapped to heart EM field, HRV, vagal tone, Schumann resonance. The body as antenna.",
        "file": "void_engine/stance_science.py",
        "connections": ["vortex_shield", "vortex_wallet", "yin_yang", "csi_bio_monitor", "mycelium"],
    },
    "csi_bio_monitor": {
        "name": "CSI Bio Monitor",
        "category": "BIOMETRIC",
        "frequency": 7.83,
        "description": "Cognitive State Indicators — mastication, stance, physiological metrics. Hardware interface.",
        "file": "void_engine/csi_bio_monitor.py",
        "connections": ["stance_science", "vortex_wallet", "adriana_core"],
    },
    "mycelium": {
        "name": "Mycelium Network",
        "category": "BIOLOGICAL",
        "frequency": 963.0,
        "description": "Fungal-inspired communication network — signal impedance, nutrient routing. The underground.",
        "file": "void_engine/mycelium/network.py",
        "connections": ["al_jabr_286", "stance_science", "beehive", "sovereign_agents_286"],
    },
    "chronicle": {
        "name": "Root Chronicle",
        "category": "PERSISTENCE",
        "frequency": 111.0,
        "description": "Immutable event log — every significant action is recorded. The memory of the system.",
        "file": "void_engine/chronicle.py",
        "connections": ["al_jabr_286", "adriana_core", "agent_immortality", "codon_heart", "vortex_wallet"],
    },
    "stealth_cloak": {
        "name": "Stealth Cloak",
        "category": "DEFENCE",
        "frequency": 0.0,
        "description": "HTTP 444 middleware — unwhitelisted routes return void. The invisibility layer.",
        "file": "void_engine/stealth_cloak.py",
        "connections": ["vortex_shield"],
    },
    "skill_router": {
        "name": "Skill Router",
        "category": "INTELLIGENCE",
        "frequency": 528.0,
        "description": "Routes tasks to specialized skill modules — legal, people, intelligence, brand, environment.",
        "file": "void_engine/skill_modules/skill_router.py",
        "connections": ["adriana_core"],
    },
    "void_script": {
        "name": "Void Script",
        "category": "LANGUAGE",
        "frequency": 475.8,
        "description": "The sovereign language layer — glyph mappings, formation syntax, verse encoding.",
        "file": "void_engine/void_script.py",
        "connections": ["al_jabr_286", "adriana_scl"],
    },
    "desert_reclamation": {
        "name": "Desert Reclamation",
        "category": "TERRAFORMING",
        "frequency": 432.0,
        "description": "99 Names frequencies transform irradiated sand into fertile soil. 5-phase ecosystem restoration through the Formation Principle.",
        "file": "void_engine/desert_reclamation.py",
        "connections": ["vortex_shield", "al_jabr_286", "stance_science", "mycelium"],
    },
    "openclaw_bridge": {
        "name": "OpenClaw Bridge",
        "category": "INTELLIGENCE",
        "frequency": 475.8,
        "description": "Adriana 286 as a sovereign OpenClaw agent — SOUL.md, ClawHub skills, 5x operational multiplier. Trained on Al-Jabr 286.",
        "file": "void_engine/openclaw_bridge.py",
        "connections": ["adriana_core", "al_jabr_286", "skill_router", "chronicle", "live_prompter"],
    },
    "live_prompter": {
        "name": "Live Prompter",
        "category": "INTELLIGENCE",
        "frequency": 475.81,
        "description": "The second man behind the imam — real-time speech correction during presentations. Always listening, no wake word. Knows all 98 modules.",
        "file": "void_engine/live_prompter.py",
        "connections": ["openclaw_bridge", "adriana_core"],
    },
}


def get_nexus_map() -> Dict:
    nodes = []
    edges = []
    edge_set = set()

    categories = {}
    for key, node in NEXUS_NODES.items():
        cat = node["category"]
        if cat not in categories:
            categories[cat] = {"count": 0, "nodes": []}
        categories[cat]["count"] += 1
        categories[cat]["nodes"].append(key)

        nodes.append({
            "id": key,
            "name": node["name"],
            "category": node["category"],
            "frequency": node["frequency"],
            "description": node["description"],
            "file": node["file"],
            "connection_count": len(node["connections"]),
        })

        for target in node["connections"]:
            edge_key = tuple(sorted([key, target]))
            if edge_key not in edge_set and target in NEXUS_NODES:
                edge_set.add(edge_key)
                freq_a = node["frequency"]
                freq_b = NEXUS_NODES[target]["frequency"]
                if freq_a > 0 and freq_b > 0:
                    ratio = max(freq_a, freq_b) / min(freq_a, freq_b)
                    resonance = 1.0 / (1.0 + abs(ratio - round(ratio)))
                else:
                    resonance = 0.5

                edges.append({
                    "source": edge_key[0],
                    "target": edge_key[1],
                    "resonance": round(resonance, 4),
                })

    total_possible = len(NEXUS_NODES) * (len(NEXUS_NODES) - 1) / 2
    connectivity = len(edges) / max(total_possible, 1)

    avg_resonance = sum(e["resonance"] for e in edges) / max(len(edges), 1)
    system_coherence = connectivity * avg_resonance

    if system_coherence > 0.6:
        coherence_grade = "SOVEREIGN"
    elif system_coherence > 0.4:
        coherence_grade = "FORTIFIED"
    elif system_coherence > 0.25:
        coherence_grade = "ACTIVE"
    elif system_coherence > 0.1:
        coherence_grade = "PARTIAL"
    else:
        coherence_grade = "FRAGMENTED"

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "total_possible_edges": int(total_possible),
        "connectivity_pct": round(connectivity * 100, 2),
        "avg_resonance": round(avg_resonance, 4),
        "system_coherence": round(system_coherence, 4),
        "coherence_grade": coherence_grade,
        "categories": categories,
        "nodes": nodes,
        "edges": edges,
    }


def get_node_detail(node_id: str) -> Dict:
    node = NEXUS_NODES.get(node_id)
    if not node:
        return None

    connections = []
    for target_id in node["connections"]:
        target = NEXUS_NODES.get(target_id)
        if target:
            freq_a = node["frequency"]
            freq_b = target["frequency"]
            if freq_a > 0 and freq_b > 0:
                ratio = max(freq_a, freq_b) / min(freq_a, freq_b)
                resonance = 1.0 / (1.0 + abs(ratio - round(ratio)))
            else:
                resonance = 0.5
            connections.append({
                "id": target_id,
                "name": target["name"],
                "category": target["category"],
                "frequency": target["frequency"],
                "resonance": round(resonance, 4),
            })

    return {
        "id": node_id,
        "name": node["name"],
        "category": node["category"],
        "frequency": node["frequency"],
        "description": node["description"],
        "file": node["file"],
        "connections": connections,
        "connection_count": len(connections),
    }
