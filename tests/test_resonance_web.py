from __future__ import annotations

from void_engine.resonance_web import (
    ResonanceWeb,
    create_search_manifest,
    ingest_search_results,
    run_resonance_session,
    translate_concept_to_vectors,
)


def test_translate_concept_to_vectors_generates_angles() -> None:
    vector = translate_concept_to_vectors(
        concept="containment resonance seed",
        glyph="◆",
        domain="signal",
    )

    assert vector.source_concept == "containment resonance seed"
    assert vector.search_angles
    assert len(vector.search_angles) <= 10
    assert vector.fields_to_probe


def test_ingest_search_results_keeps_resonant_threads() -> None:
    concept = "containment resonance crystallisation"
    results = [
        {
            "title": "Resonance and containment in crystal lattice boundary conditions",
            "url": "https://example.com/resonance",
            "snippet": "Phase transition, nucleation, resonance, and membrane boundary in confined systems.",
        },
        {
            "title": "Cooking recipes",
            "url": "https://example.com/cook",
            "snippet": "Simple weeknight meals and shopping lists.",
        },
    ]

    threads = ingest_search_results(concept, results, ["physics", "biology"])

    assert threads
    assert all(t.resonance_score >= 0.25 for t in threads)
    assert any("resonance" in t.title.lower() for t in threads)


def test_create_search_manifest_returns_queries() -> None:
    manifest = create_search_manifest(["void containment", "seed resonance"])

    assert "void containment" in manifest
    assert "seed resonance" in manifest
    assert manifest["void containment"]
    assert manifest["seed resonance"]


def test_run_resonance_session_increments_and_stores_threads(tmp_path) -> None:
    web = ResonanceWeb()
    search_results = {
        "containment resonance": [
            {
                "title": "Contained resonance in membrane systems",
                "url": "https://example.com/membrane",
                "snippet": "Boundary, oscillation, and resonant confinement in biological membranes.",
            }
        ]
    }

    out = run_resonance_session(
        concepts=[{"concept": "containment resonance", "glyph": "◆", "domain": "signal"}],
        search_results=search_results,
        web=web,
    )

    assert out.session_count == 1
    assert out.total_probes == 1
    assert out.threads
