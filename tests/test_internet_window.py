from __future__ import annotations

from datetime import datetime, timezone

from void_engine.internet_window import (
    CapturedPage,
    InternetWindow,
    WindowBrowser,
    WindowIndex,
    compute_bridge_hash,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def test_captured_page_roundtrip_bytes() -> None:
    page = CapturedPage(
        url="https://example.com/a",
        title="Containment as Boundary",
        content="Boundary resonance and selective membrane containment.",
        snippet="Boundary resonance.",
        source_type="article",
        field="biology",
        captured_at=_now_iso(),
    )

    encoded = page.to_bytes()
    decoded = CapturedPage.from_bytes(encoded)

    assert decoded.url == page.url
    assert decoded.title == page.title
    assert decoded.content == page.content
    assert decoded.sha256 == page.sha256


def test_window_index_roundtrip_bytes() -> None:
    index = WindowIndex(
        window_id="WIN-abc123",
        created_at=_now_iso(),
        session_name="test_session",
        total_pages=2,
        total_bytes=1234,
        source_concepts=["containment", "resonance"],
        fields_covered=["physics", "biology"],
        page_manifest=[{"frame": 1, "title": "A", "url": "u", "field": "physics", "sha256": "x", "size": 10}],
        sha256_composite="deadbeef",
    )

    encoded = index.to_bytes()
    decoded = WindowIndex.from_bytes(encoded)

    assert decoded.window_id == index.window_id
    assert decoded.session_name == index.session_name
    assert decoded.total_pages == index.total_pages
    assert decoded.sha256_composite == index.sha256_composite


def test_build_index_and_browser_search() -> None:
    window = InternetWindow()
    window.add_page(
        CapturedPage(
            url="https://example.com/1",
            title="Resonance in Acoustic Systems",
            content="Acoustic resonance appears with standing wave harmonics.",
            snippet="resonance standing wave",
            source_type="paper",
            field="physics",
            captured_at=_now_iso(),
        )
    )
    window.add_page(
        CapturedPage(
            url="https://example.com/2",
            title="Membrane Containment",
            content="Cell membranes provide selective containment boundaries.",
            snippet="containment boundary membrane",
            source_type="article",
            field="biology",
            captured_at=_now_iso(),
        )
    )

    idx = window.build_index("session_demo", ["resonance", "containment"])
    assert idx.total_pages == 2
    assert idx.window_id.startswith("WIN-")

    browser = WindowBrowser(window)
    results = browser.search("resonance wave")
    assert results
    top_idx, top_score, _snippet = results[0]
    assert top_idx == 0
    assert top_score > 0


def test_compute_bridge_hash_length_and_stability() -> None:
    h1 = compute_bridge_hash("a" * 72, "b" * 64)
    h2 = compute_bridge_hash("a" * 72, "b" * 64)
    h3 = compute_bridge_hash("a" * 72, "c" * 64)

    assert len(h1) == 68
    assert h1 == h2
    assert h1 != h3
