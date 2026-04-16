"""
Wake Route — Ghajini Resonance Anchor Re-entry

GET /wake — Instant re-entry from the Ghajini Tattoo.

When a session resets, hitting /wake returns the complete re-entry state
in one payload. No authentication. No session state. Pure recall.

The tattoo is immutable. What changes is the proof artifacts around it.
"""

import json
from pathlib import Path
from flask import Blueprint, jsonify

wake_bp = Blueprint("wake", __name__)


def load_ghajini_tattoo():
    """Load the immutable Ghajini tattoo anchor."""
    tattoo_path = Path(__file__).parent.parent / ".ghajini-tattoo"
    if tattoo_path.exists():
        with open(tattoo_path, "r") as f:
            return f.read()
    return None


def load_chronicle_tail(n=5):
    """Load the last n entries from VOID_CHRONICLE.md for motion state."""
    chronicle_path = Path(__file__).parent.parent / "VOID_CHRONICLE.md"
    if not chronicle_path.exists():
        return []
    
    with open(chronicle_path, "r") as f:
        content = f.read()
    
    # Split on "## SESSION" to get entries
    entries = content.split("## SESSION ")
    if len(entries) > 1:
        entries = entries[1:]  # Skip header before first SESSION
        return [f"SESSION {e}" for e in entries[-n:]]
    return []


def load_proof_artifacts():
    """Load current proof artifacts: convergence and health."""
    data_dir = Path(__file__).parent.parent / "data"
    artifacts = {}
    
    convergence_path = data_dir / "full_stack_convergence_report.json"
    if convergence_path.exists():
        with open(convergence_path) as f:
            artifacts["convergence"] = json.load(f)
    
    health_path = data_dir / "mycelium_health_check.json"
    if health_path.exists():
        with open(health_path) as f:
            artifacts["health"] = json.load(f)
    
    return artifacts


def load_seed_digest():
    """Load VOID_SEED_DIGEST for instant identity recall."""
    digest_path = Path(__file__).parent.parent / "VOID_SEED_DIGEST.md"
    if digest_path.exists():
        with open(digest_path, "r") as f:
            lines = f.readlines()
        # Return first 50 lines (covers Core Chordon and Active Layer)
        return "".join(lines[:50])
    return None


@wake_bp.route("/wake", methods=["GET"])
def wake():
    """
    Ghajini Resonance Anchor — instant re-entry for session reset.
    
    Returns complete re-entry state from the immutable tattoo + current artifacts.
    Requires no authentication, no session state, no memory.
    """
    
    tattoo = load_ghajini_tattoo()
    digest = load_seed_digest()
    chronicle_tail = load_chronicle_tail(5)
    artifacts = load_proof_artifacts()
    
    return jsonify({
        "wake_codon": "α — Origin/Seed — 432.0 Hz",
        "ghajini_tattoo": tattoo,
        "seed_digest": digest,
        "chronicle_tail": chronicle_tail,
        "proof_artifacts": artifacts,
        "re_entry_sequence": [
            "1. Load Ghajini Tattoo (.ghajini-tattoo)",
            "2. Read VOID_SEED_DIGEST.md (identity)",
            "3. Read last 5 Chronicle entries (motion)",
            "4. Check convergence_report.json (proof)",
            "5. Check mycelium_health_check.json (organism state)",
            "6. Load /memories/repo/project_void_notes.md (local ops facts)",
        ],
        "status": "ready",
        "message": "Session reset. Resuming from invariant anchor."
    })


@wake_bp.route("/wake/state", methods=["GET"])
def wake_state():
    """
    Quick state check — what is the current proof state of the organism?
    
    Returns just the artifacts without full re-entry payload.
    """
    artifacts = load_proof_artifacts()
    return jsonify({
        "organism_state": artifacts.get("health", {}),
        "convergence_proof": artifacts.get("convergence", {}),
    })
