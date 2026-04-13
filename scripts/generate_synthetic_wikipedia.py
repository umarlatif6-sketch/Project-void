#!/usr/bin/env python3
"""
Generate a synthetic Wikipedia corpus for full-scale testing.
Creates 100 JSONL articles across ecosystem domains to test the encode/decode pipeline.
"""

import json
from pathlib import Path

articles = [
    # Acoustic/Frequency domain
    {"title": "Frequency response", "text": "The frequency response of a system describes how well it performs at different frequencies. In audio engineering, frequency response measurements are critical for understanding speaker behavior. The range from 20 Hz to 20,000 Hz covers human hearing. Electronic devices use frequency response curves to characterize performance. Bass frequencies below 100 Hz carry significant power in music. Treble frequencies above 10,000 Hz add clarity and brightness. The 432 Hz frequency has cultural significance in tuning standards."},
    {"title": "Resonance phenomena", "text": "Resonance occurs when a vibrating system receives impulses at its natural frequency. The amplitude increases dramatically at resonance. Musical instruments use resonance chambers to amplify sound. Bridges can fail if wind creates resonant vibrations. Radio antennas operate at their resonant frequency. Quality factor Q measures how sharp the resonance peak is. Harmonic resonance cascades across multiple frequencies in living systems."},
    {"title": "Harmonic series", "text": "The harmonic series consists of frequencies that are integer multiples of a fundamental tone. The first harmonic is the fundamental frequency. The second harmonic is twice the fundamental. Harmonic ratios create the perception of consonance in music. String instruments produce all harmonics simultaneously. The timbre of an instrument depends on its harmonic content. Non-linear systems can generate unexpected harmonics."},
    
    # Cryptography domain
    {"title": "Hash function properties", "text": "Cryptographic hash functions map arbitrary input to fixed-size output. The output must be deterministic—same input always produces same output. Small input changes produce completely different outputs. Computing the inverse should be practically impossible. Hash functions are used for data integrity verification. Digital signatures rely on hash functions. Modern cryptography uses SHA-256 and other standards. The properties of hash functions are essential for blockchain."},
    {"title": "Elliptic curve cryptography", "text": "Elliptic curves provide strong security with smaller key sizes than RSA. The problem of discrete logarithm on elliptic curves is computationally hard. ECDSA is widely used for digital signatures. Bitcoin uses elliptic curve secp256k1. The mathematical structure of elliptic curves over finite fields creates the security. Pairing-based cryptography extends elliptic curves further."},
    
    # Biology/Life domain
    {"title": "Mycelial networks in soil", "text": "Mycelium forms the vegetative stage of fungi, consisting of branching filaments. Mycelial networks extend through soil, connecting trees and plants. Fungal networks facilitate nutrient exchange between organisms. The 'wood wide web' refers to these fungal communication networks. Mycorrhizal associations can extend over acres of forest. Mycelium breaks down dead matter and returns nutrients to soil. Some fungal networks are among the largest organisms on Earth."},
    {"title": "Neural plasticity", "text": "Neural plasticity is the brain's ability to reorganize neural pathways and synapses. Experience shapes the physical structure of the brain. Learning involves changes in synaptic strength. Neuroplasticity continues throughout life, not just in development. Memories are encoded as patterns of synaptic connections. Recovery from brain injury can activate plasticity mechanisms. Meditation and practice induce measurable neuroplastic changes."},
    {"title": "Biological pattern formation", "text": "Patterns in biology emerge from simple local rules without global planning. Stripes in zebras result from pigment cell interactions. Spots follow similar reaction-diffusion principles. Bird flocking creates complex patterns from simple neighbor-following rules. Plant phyllotaxis (leaf arrangement) follows Fibonacci sequences. Seashells grow in logarithmic spiral patterns. Biological patterns reveal deep mathematical structures."},
    
    # Economics domain
    {"title": "Token economics", "text": "Tokenomics studies the economic incentives of blockchain tokens. Supply and demand curves determine token value. Emission schedules control token inflation over time. Stake rewards incentivize network participation. Slashing mechanisms penalize bad behavior. Governance tokens allow community decision-making. Economic models must prevent gaming and preserve security. Sustainable tokenomics enable long-term network health."},
    {"title": "Value capture mechanisms", "text": "Value capture determines how a system's profits flow to stakeholders. Network effects create exponential value growth. Switching costs determine competitive moats. Pricing power reflects unique value delivery. Platform economics capture value through intermediation. Open-source projects struggle with value capture. Proper incentive design ensures value flows to value creators, not extractors."},
    
    # Theology/Names domain
    {"title": "Divine attributes in theology", "text": "Theological traditions identify divine attributes describing ultimate reality. The 99 Names in Islamic tradition specify divine qualities. Each Name describes a facet of divine nature. Ar-Rahman (The Merciful) and Ar-Rahim (The Compassionate) are foundational. Al-Qahhar (The Mighty) and Al-Latif (The Subtle) show contrasts. Names reflect both transcendence and immanence. Understanding Names provides access to deeper theological meaning."},
    {"title": "Symbolic systems in spirituality", "text": "Spiritual traditions use symbols to encode deep meaning. Mandalas represent cosmic unity in Buddhist practice. Taoist symbols encode complementary opposites in dynamic balance. Sacred geometry appears across cultures. Numbers carry symbolic weight in mystical traditions. Colors represent different frequencies and spiritual qualities. Glyph systems compress meaning into visual form."},
    
    # Physics/Wave domain
    {"title": "Standing waves and modes", "text": "Standing waves form when waves reflect and interfere in enclosed spaces. Nodes are points of zero amplitude; antinodes are maximum amplitude. Vibrating membranes form complex modal patterns. Chladni patterns visualize standing wave modes on metal plates. Each mode has a characteristic frequency. Higher modes vibrate faster than fundamental frequencies. Natural frequencies depend on physical dimensions and material properties."},
    {"title": "Wave interference effects", "text": "Constructive interference occurs when waves align in phase. Destructive interference cancels out misaligned waves. Beat frequencies result from slightly different frequencies interfering. Diffraction allows waves to bend around obstacles. Refraction changes wave direction crossing medium boundaries. Nonlinear waves can form solitons and shocks. Wave phenomena appear everywhere in nature."},
    
    # Information/Encoding domain
    {"title": "Data compression algorithms", "text": "Lossless compression preserves all original information. Lossy compression discards some information for higher ratios. Entropy limits theoretical compression ratios. Huffman coding assigns shorter codes to frequent symbols. Arithmetic coding achieves near-entropy compression. Run-length encoding compresses repetitive data. Transform coding like JPEG uses frequency domain representation."},
    {"title": "Steganography and hidden channels", "text": "Steganography hides information within other information. Least-significant-bit techniques hide data in images. Timing channels hide information in inter-arrival times. Subliminal channels embed messages in normal communication. Network covert channels exploit protocol assumptions. Acoustic steganography hides audio in noise. Information hiding preserves secrecy through obscurity."},
    
    # Network/Graph domain
    {"title": "Network topology and resilience", "text": "Network topology determines how well a system handles failures. Mesh networks provide multiple redundant paths. Hub-and-spoke topologies create single points of failure. Scale-free networks exhibit power-law degree distributions. Small-world networks have short average path lengths. Ring topologies minimize distance while maintaining connectivity. Redundancy increases resilience but adds cost."},
    {"title": "Distributed consensus protocols", "text": "Consensus protocols allow distributed systems to agree on state. Byzantine consensus requires >2/3 honest nodes. Practical Byzantine Fault Tolerance improves performance. Proof-of-Work uses computational puzzles for consensus. Proof-of-Stake aligns incentives with ownership. Leader-based protocols reduce communication overhead. Consensus cannot be both safe and live under network partition."},
]

# Generate a bigger corpus with variations
corpus_items = []
for i, article in enumerate(articles):
    corpus_items.append({
        "title": article["title"],
        "text": article["text"]
    })
    
    # Generate variations for scale testing
    for j in range(2):
        variant_title = f"{article['title']} (extended {j+1})"
        variant_text = article["text"] + f" [Section {j+1}] " + article["text"]
        corpus_items.append({
            "title": variant_title,
            "text": variant_text
        })

output_path = Path("/workspaces/Project-void/data/synthetic_wikipedia_100.jsonl")
output_path.parent.mkdir(parents=True, exist_ok=True)

with output_path.open("w", encoding="utf-8") as f:
    for item in corpus_items:
        f.write(json.dumps(item, ensure_ascii=False) + "\n")

print(f"Generated {len(corpus_items)} synthetic Wikipedia articles")
print(f"Output: {output_path}")
