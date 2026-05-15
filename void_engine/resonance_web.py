"""
Resonance Web Crawler — PROJECT VOID
Mesa Agent Internet Access Module (v2 — Manus Search Backend)

Gives the Mesa swarm the ability to reach into the outside world and find
correlations between internal void concepts and external knowledge.

Architecture:
  - When running inside a Manus session: uses search results fed via JSON files
  - When running standalone: uses the Manus search tool output cached in data/
  - The agents don't scrape directly — they INTERPRET search results through
    the resonance scoring system

The key insight: the search is not keyword matching. It's SHAPE matching.
The agents take a concept and look for where that PATTERN appears in the world.

Flow:
  1. ConceptVector — translates a void concept into multiple search angles
  2. ResonanceProbe — scores results by resonance (pattern matching, not keywords)
  3. WebThread — a single discovered connection between void and world
  4. ResonanceWeb — the accumulated mesh of all discovered connections
  5. MesaWebAgent — extends SandboxAgent with internet capability

Requires: requests, beautifulsoup4 (both pre-installed in Manus sandbox)
"""

import hashlib
import json
import logging
import os
import re
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# --- Constants ---

RESONANCE_THRESHOLD = 0.25  # Minimum resonance score to keep a thread
MAX_THREADS_PER_PROBE = 7   # Cap results per concept probe
WEB_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "resonance_web")
SEARCH_CACHE_PATH = os.path.join(WEB_STORAGE_PATH, "search_cache")
USER_AGENT = "VoidEngine-ResonanceProbe/2.0 (Project VOID; resonance-search)"
REQUEST_TIMEOUT = 10
RATE_LIMIT_DELAY = 2.0  # seconds between requests

# --- Void Concept Vocabulary (for vector translation) ---

CONCEPT_DOMAINS = {
    "genesis": ["origin", "seed", "creation", "emergence", "first principle"],
    "aqua": ["flow", "nutrient", "cycle", "growth", "sustenance"],
    "signal": ["pulse", "frequency", "transmission", "carrier", "wave"],
    "transform": ["change", "shift", "mutation", "phase transition", "metamorphosis"],
    "boundary": ["threshold", "edge", "limit", "membrane", "interface"],
    "soil": ["foundation", "substrate", "ground", "root", "base layer"],
}

GLYPH_RESONANCE_MAP = {
    "α": {"concepts": ["origin", "seed", "beginning", "source code", "genesis"],
           "fields": ["cosmology", "embryology", "information theory", "thermodynamics"]},
    "β": {"concepts": ["growth", "sprout", "expansion", "development", "branching"],
           "fields": ["mycology", "network theory", "urban planning", "fractal mathematics"]},
    "γ": {"concepts": ["signal", "pulse", "frequency", "carrier wave", "resonance"],
           "fields": ["acoustics", "quantum mechanics", "neuroscience", "radio engineering"]},
    "δ": {"concepts": ["change", "shift", "delta", "transformation", "phase"],
           "fields": ["chemistry", "economics", "climate science", "evolutionary biology"]},
    "ε": {"concepts": ["threshold", "edge", "boundary", "liminal", "membrane"],
           "fields": ["topology", "cell biology", "architecture", "consciousness studies"]},
    "Ψ": {"concepts": ["mind", "psyche", "wave function", "consciousness", "observer"],
           "fields": ["quantum physics", "psychology", "philosophy of mind", "AI alignment"]},
    "◆": {"concepts": ["core", "diamond", "pressure", "crystallisation", "permanence"],
           "fields": ["materials science", "geology", "data structures", "cryptography"]},
    "◇": {"concepts": ["void", "emptiness", "potential", "container", "space"],
           "fields": ["cosmology", "zen philosophy", "vacuum physics", "architecture"]},
    "⚡": {"concepts": ["ignition", "spark", "energy", "activation", "lightning"],
           "fields": ["electrochemistry", "neuroscience", "plasma physics", "entrepreneurship"]},
    "∞": {"concepts": ["infinity", "recursion", "loop", "eternal", "self-reference"],
           "fields": ["mathematics", "set theory", "consciousness", "cosmology"]},
}

# Shape translations — how void concepts map to external fields
SHAPE_TRANSLATIONS = {
    "containment": [
        "topology enclosure boundary",
        "cell membrane selective permeability",
        "prison architecture panopticon",
        "containerisation isolation namespace",
        "quantum confinement potential well",
    ],
    "frequency": [
        "acoustic resonance standing wave",
        "quantum harmonic oscillator",
        "circadian rhythm entrainment",
        "radio frequency carrier modulation",
        "neural oscillation synchronisation",
    ],
    "crystallisation": [
        "nucleation crystal growth self-organisation",
        "self-organising emergence pattern formation",
        "dissipative structures far from equilibrium",
        "seed crystal supersaturated solution",
        "information crystallisation knowledge management",
    ],
    "void": [
        "vacuum energy zero point field",
        "sunyata emptiness buddhism",
        "negative space architecture design",
        "null hypothesis statistical inference",
        "dark energy cosmological constant",
    ],
    "force": [
        "potential energy field gradient",
        "affordance ecological psychology",
        "tensegrity structural integrity compression",
        "force carrier boson exchange",
        "social force model crowd dynamics",
    ],
    "seed": [
        "bootstrap problem computing initialisation",
        "initial conditions chaos theory sensitivity",
        "morphogenetic field developmental biology",
        "seed crystal nucleation",
        "primordial fluctuation cosmology",
    ],
    "dungeon": [
        "containment architecture nested isolation",
        "liminal space psychology threshold",
        "chroot jail namespace isolation",
        "labyrinth sacred geometry pilgrimage",
        "recursive descent parsing compiler",
    ],
    "visit": [
        "transient state physics temporary",
        "pilgrimage sacred geography temporary",
        "temporary autonomous zone hakim bey",
        "observer effect quantum measurement",
        "sampling signal processing nyquist",
    ],
    "distraction": [
        "peripheral attention cognition creativity",
        "stochastic resonance signal processing noise",
        "lateral thinking creativity de bono",
        "serendipity scientific discovery",
        "noise-induced order constructive noise",
    ],
    "compression": [
        "information entropy shannon coding",
        "lossy lossless encoding perception",
        "haiku poetry compression meaning density",
        "kolmogorov complexity minimal description",
        "holographic principle information boundary",
    ],
    "resonance": [
        "sympathetic vibration coupled oscillators",
        "morphic resonance sheldrake hypothesis",
        "stochastic resonance weak signal amplification",
        "Schumann resonance earth electromagnetic",
        "acoustic resonance room modes standing waves",
    ],
    "prism": [
        "spectral decomposition Fourier transform",
        "dispersion medium wavelength dependent",
        "analysis synthesis duality signal processing",
        "refraction Snell law interface",
        "chromatic aberration lens design",
    ],
}


# --- Data Structures ---

@dataclass
class ConceptVector:
    """
    A void concept translated into multiple search angles.
    Not keywords — shapes. Each angle is a different way the same
    concept might appear in the outside world.
    """
    source_concept: str
    source_glyph: Optional[str]
    source_domain: Optional[str]
    search_angles: List[str] = field(default_factory=list)
    fields_to_probe: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "source_concept": self.source_concept,
            "source_glyph": self.source_glyph,
            "source_domain": self.source_domain,
            "search_angles": self.search_angles,
            "fields_to_probe": self.fields_to_probe,
        }


@dataclass
class WebThread:
    """
    A single discovered connection between the void and the outside world.
    A tangent point where internal architecture touches external reality.
    """
    thread_id: str
    source_concept: str
    search_angle: str
    url: str
    title: str
    snippet: str
    resonance_score: float
    field: str
    discovered_at: str
    hex_signature: str

    def to_dict(self) -> Dict:
        return {
            "thread_id": self.thread_id,
            "source_concept": self.source_concept,
            "search_angle": self.search_angle,
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "resonance_score": self.resonance_score,
            "field": self.field,
            "discovered_at": self.discovered_at,
            "hex_signature": self.hex_signature,
        }


@dataclass
class ResonanceWeb:
    """
    The accumulated mesh of all discovered connections.
    Grows with each session. Each thread is a node.
    Connections between threads form when they share concepts or fields.
    """
    threads: List[WebThread] = field(default_factory=list)
    session_count: int = 0
    total_probes: int = 0
    total_searches: int = 0

    def add_thread(self, thread: WebThread):
        if not any(t.url == thread.url for t in self.threads):
            self.threads.append(thread)

    def get_connections(self) -> List[Dict]:
        """Find connections between threads (shared concepts or fields)."""
        connections = []
        for i, t1 in enumerate(self.threads):
            for t2 in self.threads[i+1:]:
                # Check concept word overlap
                words1 = set(t1.source_concept.lower().split())
                words2 = set(t2.source_concept.lower().split())
                shared = words1 & words2
                # Check field match
                same_field = t1.field == t2.field
                # Check snippet resonance (do snippets share unusual words?)
                snippet_words1 = set(w for w in t1.snippet.lower().split() if len(w) > 5)
                snippet_words2 = set(w for w in t2.snippet.lower().split() if len(w) > 5)
                snippet_overlap = snippet_words1 & snippet_words2

                if len(shared) >= 2 or same_field or len(snippet_overlap) >= 3:
                    connections.append({
                        "from": t1.thread_id,
                        "to": t2.thread_id,
                        "from_title": t1.title[:50],
                        "to_title": t2.title[:50],
                        "shared_words": list(shared),
                        "same_field": same_field,
                        "snippet_resonance": list(snippet_overlap)[:5],
                        "strength": len(shared) * 0.3 + (0.3 if same_field else 0) + len(snippet_overlap) * 0.1,
                    })
        return sorted(connections, key=lambda c: c["strength"], reverse=True)

    def get_field_map(self) -> Dict[str, int]:
        """Map of fields to thread counts."""
        field_map = {}
        for t in self.threads:
            field_map[t.field] = field_map.get(t.field, 0) + 1
        return dict(sorted(field_map.items(), key=lambda x: x[1], reverse=True))

    def to_dict(self) -> Dict:
        return {
            "thread_count": len(self.threads),
            "session_count": self.session_count,
            "total_probes": self.total_probes,
            "total_searches": self.total_searches,
            "field_map": self.get_field_map(),
            "threads": [t.to_dict() for t in self.threads],
            "connections": self.get_connections(),
        }

    def save(self, path: Optional[str] = None):
        save_path = path or os.path.join(WEB_STORAGE_PATH, "resonance_web.json")
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info("Resonance web saved: %d threads, %d connections",
                    len(self.threads), len(self.get_connections()))

    @classmethod
    def load(cls, path: Optional[str] = None) -> "ResonanceWeb":
        load_path = path or os.path.join(WEB_STORAGE_PATH, "resonance_web.json")
        web = cls()
        if os.path.exists(load_path):
            try:
                with open(load_path) as f:
                    data = json.load(f)
                web.session_count = data.get("session_count", 0)
                web.total_probes = data.get("total_probes", 0)
                web.total_searches = data.get("total_searches", 0)
                for td in data.get("threads", []):
                    web.threads.append(WebThread(**td))
            except Exception as e:
                logger.warning("Could not load resonance web: %s", e)
        return web


# --- Core Functions ---

def translate_concept_to_vectors(
    concept: str,
    glyph: Optional[str] = None,
    domain: Optional[str] = None,
) -> ConceptVector:
    """
    Translate a void concept into multiple search vectors.
    Searches for the SHAPE of the concept in different fields.
    """
    vector = ConceptVector(
        source_concept=concept,
        source_glyph=glyph,
        source_domain=domain,
    )

    words = concept.lower().split()
    core_terms = [w for w in words if len(w) > 3 and w not in
                  {"this", "that", "with", "from", "into", "only", "been",
                   "have", "what", "when", "where", "does", "just", "more"}]

    # Angle 1: Direct concept reframed for research
    vector.search_angles.append(f"{' '.join(core_terms[:4])} theory research")

    # Angle 2: Glyph resonance map
    if glyph and glyph in GLYPH_RESONANCE_MAP:
        glyph_data = GLYPH_RESONANCE_MAP[glyph]
        for gc in glyph_data["concepts"][:2]:
            vector.search_angles.append(f"{gc} {' '.join(core_terms[:2])}")
        vector.fields_to_probe.extend(glyph_data["fields"])

    # Angle 3: Domain vocabulary
    if domain and domain in CONCEPT_DOMAINS:
        domain_words = CONCEPT_DOMAINS[domain]
        for dw in domain_words[:2]:
            vector.search_angles.append(f"{dw} {' '.join(core_terms[:3])}")

    # Angle 4: Shape translations (the concept in a different field)
    for key, translations in SHAPE_TRANSLATIONS.items():
        if key in concept.lower():
            vector.search_angles.extend(translations[:3])
            break

    # Angle 5: Cross-domain question
    if len(core_terms) >= 2:
        vector.search_angles.append(f"why {' '.join(core_terms[:3])} important")

    # Deduplicate and cap
    vector.search_angles = list(dict.fromkeys(vector.search_angles))[:10]

    if not vector.fields_to_probe:
        vector.fields_to_probe = ["physics", "philosophy", "computer science", "biology", "architecture"]

    return vector


def _compute_resonance_score(
    concept: str,
    title: str,
    snippet: str,
    field: str,
) -> float:
    """
    Score how strongly an external result resonates with the void concept.
    Pattern matching, not keyword matching.
    """
    score = 0.0
    concept_lower = concept.lower()
    concept_words = set(concept_lower.split())
    result_text = (title + " " + snippet).lower()
    result_words = set(result_text.split())

    # Direct word overlap (weak signal)
    overlap = concept_words & result_words
    meaningful_overlap = [w for w in overlap if len(w) > 4]
    score += len(meaningful_overlap) * 0.06

    # Structural resonance: pattern indicators
    pattern_indicators = {
        "containment": ["boundary", "enclosed", "isolated", "contained", "cell",
                       "membrane", "wall", "confine", "trap", "cage", "vessel"],
        "emergence": ["emerges", "self-organis", "spontaneous", "bottom-up",
                     "complex", "emergent", "arise", "manifest"],
        "frequency": ["resonan", "harmonic", "oscillat", "vibrat", "wave",
                     "Hz", "frequency", "periodic", "rhythm"],
        "void": ["empty", "vacuum", "nothing", "absence", "zero", "void",
                "null", "negative space", "sunyata"],
        "recursion": ["self-refer", "recursive", "fractal", "nested", "meta",
                     "loop", "self-similar", "iterate"],
        "transformation": ["transform", "phase", "transition", "metamorph",
                          "shift", "change", "convert", "transmut"],
        "compression": ["compress", "encod", "densit", "information", "entropy",
                       "lossless", "compact", "minimal"],
        "crystallisation": ["crystal", "nucleat", "solidif", "pattern", "lattice",
                           "seed", "precipitat", "supersaturat"],
        "force": ["force", "potential", "energy", "field", "gradient",
                 "tensile", "compress", "push", "pull"],
        "visit": ["transient", "temporary", "pilgrim", "journey", "passage",
                 "liminal", "threshold", "transit"],
        "distraction": ["peripheral", "lateral", "serendip", "noise",
                       "stochastic", "diverge", "tangent"],
        "seed": ["seed", "initial", "bootstrap", "primordial", "germ",
                "nucleus", "origin", "embryo"],
    }

    for pattern_name, indicators in pattern_indicators.items():
        if pattern_name in concept_lower:
            matches = sum(1 for ind in indicators if ind in result_text)
            score += matches * 0.08

    # Cross-pattern resonance (concept doesn't contain the word but result does)
    all_indicators = [ind for inds in pattern_indicators.values() for ind in inds]
    cross_matches = sum(1 for ind in all_indicators if ind in result_text)
    score += min(cross_matches * 0.02, 0.15)

    # Field relevance
    if field.lower() in result_text:
        score += 0.08

    # Academic/depth indicators
    depth_words = ["theory", "principle", "mechanism", "framework", "model",
                  "hypothesis", "paradigm", "axiom", "theorem"]
    depth_matches = sum(1 for dw in depth_words if dw in result_text)
    score += depth_matches * 0.04

    # Length bonus (substantial content)
    if len(snippet) > 150 and score > 0.1:
        score += 0.05

    return min(1.0, round(score, 3))


def _hex_signature(content: str) -> str:
    """Generate Al-Jabr style hex signature."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


def ingest_search_results(
    concept: str,
    results: List[Dict[str, str]],
    fields_to_probe: List[str] = None,
) -> List[WebThread]:
    """
    Ingest pre-fetched search results (from Manus search tool or cache)
    and score them for resonance.

    Args:
        concept: The void concept being probed
        results: List of dicts with 'title', 'url', 'snippet' keys
        fields_to_probe: List of fields to check against

    Returns:
        List of WebThread objects above resonance threshold
    """
    threads = []
    now = datetime.now(timezone.utc).isoformat()
    fields = fields_to_probe or ["general"]

    for r in results:
        title = r.get("title", "")
        url = r.get("url", "")
        snippet = r.get("snippet", "")

        if not title or not url:
            continue

        # Detect field
        detected_field = "general"
        result_text = (title + " " + snippet).lower()
        for f in fields:
            if f.lower() in result_text:
                detected_field = f
                break

        score = _compute_resonance_score(concept, title, snippet, detected_field)

        if score >= RESONANCE_THRESHOLD:
            thread_content = f"{concept}|{url}|{title}|{now}"
            thread = WebThread(
                thread_id=_hex_signature(thread_content),
                source_concept=concept,
                search_angle="manus_search",
                url=url,
                title=title,
                snippet=snippet[:500],
                resonance_score=score,
                field=detected_field,
                discovered_at=now,
                hex_signature=_hex_signature(thread_content),
            )
            threads.append(thread)

    threads.sort(key=lambda t: t.resonance_score, reverse=True)
    return threads[:MAX_THREADS_PER_PROBE]


def cache_search_results(concept: str, results: List[Dict]):
    """Cache search results for offline/repeated use."""
    os.makedirs(SEARCH_CACHE_PATH, exist_ok=True)
    filename = _hex_signature(concept) + ".json"
    filepath = os.path.join(SEARCH_CACHE_PATH, filename)
    with open(filepath, "w") as f:
        json.dump({
            "concept": concept,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "results": results,
        }, f, indent=2)


def load_cached_results(concept: str) -> Optional[List[Dict]]:
    """Load cached search results if available."""
    filename = _hex_signature(concept) + ".json"
    filepath = os.path.join(SEARCH_CACHE_PATH, filename)
    if os.path.exists(filepath):
        with open(filepath) as f:
            data = json.load(f)
        return data.get("results", [])
    return None


def run_resonance_session(
    concepts: List[Dict[str, Any]],
    search_results: Optional[Dict[str, List[Dict]]] = None,
    web: Optional[ResonanceWeb] = None,
) -> ResonanceWeb:
    """
    Run a full resonance session.

    Args:
        concepts: List of dicts with 'concept', optional 'glyph', 'domain'
        search_results: Dict mapping concept strings to their search results
                       (pre-fetched via Manus search tool)
        web: Existing ResonanceWeb to extend

    Returns:
        Updated ResonanceWeb
    """
    if web is None:
        web = ResonanceWeb.load()

    web.session_count += 1
    search_results = search_results or {}

    for c in concepts:
        concept = c.get("concept", "")
        if not concept:
            continue

        glyph = c.get("glyph")
        domain = c.get("domain")

        vector = translate_concept_to_vectors(concept, glyph, domain)
        web.total_probes += 1

        # Get results from provided search_results, cache, or empty
        results = search_results.get(concept, [])
        if not results:
            results = load_cached_results(concept) or []

        if results:
            # Cache for future use
            cache_search_results(concept, results)

            threads = ingest_search_results(concept, results, vector.fields_to_probe)
            web.total_searches += len(threads)

            for thread in threads:
                web.add_thread(thread)
                logger.info(
                    "  [%.3f] %s | %s",
                    thread.resonance_score, thread.field, thread.title[:60]
                )
        else:
            logger.info("  No results available for: %s", concept)
            logger.info("  Search angles generated: %s", vector.search_angles[:3])

    web.save()
    return web


# --- Mesa Agent Integration ---

class MesaWebAgent:
    """
    Extends the SandboxAgent concept with internet capability.
    Each MesaWebAgent probes the web through its assigned glyph/domain lens.
    """

    def __init__(self, agent_id: int, assigned_glyph: str, assigned_domain: str):
        self.agent_id = agent_id
        self.assigned_glyph = assigned_glyph
        self.assigned_domain = assigned_domain
        self.threads_discovered: List[WebThread] = []
        self.probes_made = 0
        self.search_angles_generated: List[str] = []

    def generate_angles(self, concept: str) -> List[str]:
        """Generate search angles for a concept through this agent's lens."""
        vector = translate_concept_to_vectors(
            concept, self.assigned_glyph, self.assigned_domain
        )
        self.search_angles_generated.extend(vector.search_angles)
        return vector.search_angles

    def ingest_results(self, concept: str, results: List[Dict]) -> List[WebThread]:
        """Ingest search results and score through this agent's lens."""
        self.probes_made += 1
        vector = translate_concept_to_vectors(
            concept, self.assigned_glyph, self.assigned_domain
        )
        threads = ingest_search_results(concept, results, vector.fields_to_probe)
        self.threads_discovered.extend(threads)
        return threads

    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "assigned_glyph": self.assigned_glyph,
            "assigned_domain": self.assigned_domain,
            "probes_made": self.probes_made,
            "threads_discovered": len(self.threads_discovered),
            "search_angles_generated": len(self.search_angles_generated),
            "top_threads": [t.to_dict() for t in self.threads_discovered[:3]],
        }


def spawn_web_swarm(
    concepts: List[str],
    search_results: Dict[str, List[Dict]],
    agent_count: int = 5,
) -> Tuple[List[MesaWebAgent], ResonanceWeb]:
    """
    Spawn a swarm of MesaWebAgents, each with a different glyph/domain lens,
    and have them collectively interpret search results for a set of concepts.
    """
    glyphs = list(GLYPH_RESONANCE_MAP.keys())
    domains = list(CONCEPT_DOMAINS.keys())

    agents = []
    for i in range(min(agent_count, len(glyphs))):
        agent = MesaWebAgent(
            agent_id=i,
            assigned_glyph=glyphs[i % len(glyphs)],
            assigned_domain=domains[i % len(domains)],
        )
        agents.append(agent)

    web = ResonanceWeb.load()
    web.session_count += 1

    for concept in concepts:
        results = search_results.get(concept, [])
        for agent in agents:
            threads = agent.ingest_results(concept, results)
            for thread in threads:
                web.add_thread(thread)

    web.save()
    return agents, web


# --- Manus Integration Helper ---

def create_search_manifest(concepts: List[str]) -> Dict[str, List[str]]:
    """
    Generate a search manifest — the list of search queries that Manus
    should execute for a set of void concepts. This is the bridge between
    the Mesa agents and the Manus search tool.

    Returns a dict mapping each concept to its generated search angles.
    """
    manifest = {}
    for concept in concepts:
        vector = translate_concept_to_vectors(concept)
        manifest[concept] = vector.search_angles
    return manifest


# --- CLI Entry Point ---

if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    if len(sys.argv) < 2:
        print("VOID ENGINE — Resonance Web Crawler v2")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python resonance_web.py --status")
        print("    Show current web state")
        print()
        print("  python resonance_web.py --manifest <concept1> <concept2> ...")
        print("    Generate search manifest (queries for Manus to execute)")
        print()
        print("  python resonance_web.py --ingest <results.json>")
        print("    Ingest search results from file and score for resonance")
        print()
        print("  python resonance_web.py --angles <concept>")
        print("    Show search angles for a single concept")
        print()
        sys.exit(0)

    if sys.argv[1] == "--status":
        web = ResonanceWeb.load()
        data = web.to_dict()
        print(f"Resonance Web Status")
        print(f"{'=' * 40}")
        print(f"Threads:     {data['thread_count']}")
        print(f"Sessions:    {data['session_count']}")
        print(f"Probes:      {data['total_probes']}")
        print(f"Connections: {len(data['connections'])}")
        print()
        if data['field_map']:
            print("Fields covered:")
            for field, count in data['field_map'].items():
                print(f"  {field}: {count} threads")
        print()
        if data['threads']:
            print("Top threads by resonance:")
            sorted_threads = sorted(data['threads'], key=lambda t: t['resonance_score'], reverse=True)
            for t in sorted_threads[:10]:
                print(f"  [{t['resonance_score']:.3f}] {t['field']:15s} | {t['title'][:50]}")
                print(f"           concept: {t['source_concept'][:40]}")
        sys.exit(0)

    if sys.argv[1] == "--manifest":
        concepts = sys.argv[2:]
        if not concepts:
            print("Provide at least one concept.")
            sys.exit(1)
        manifest = create_search_manifest(concepts)
        print(json.dumps(manifest, indent=2))
        sys.exit(0)

    if sys.argv[1] == "--ingest":
        if len(sys.argv) < 3:
            print("Provide path to results JSON file.")
            sys.exit(1)
        filepath = sys.argv[2]
        with open(filepath) as f:
            data = json.load(f)
        # Expected format: {"concept": [...results...], ...}
        web = ResonanceWeb.load()
        web.session_count += 1
        for concept, results in data.items():
            threads = ingest_search_results(concept, results)
            web.total_probes += 1
            web.total_searches += len(threads)
            for t in threads:
                web.add_thread(t)
                print(f"  [{t.resonance_score:.3f}] {t.field:15s} | {t.title[:50]}")
        web.save()
        print(f"\nWeb now contains {len(web.threads)} threads, {len(web.get_connections())} connections.")
        sys.exit(0)

    if sys.argv[1] == "--angles":
        concept = " ".join(sys.argv[2:])
        if not concept:
            print("Provide a concept.")
            sys.exit(1)
        vector = translate_concept_to_vectors(concept)
        print(f"Concept: {concept}")
        print(f"Search angles ({len(vector.search_angles)}):")
        for i, angle in enumerate(vector.search_angles, 1):
            print(f"  {i}. {angle}")
        print(f"\nFields to probe: {', '.join(vector.fields_to_probe)}")
        sys.exit(0)

    print(f"Unknown command: {sys.argv[1]}")
    print("Run without arguments for help.")
    sys.exit(1)
