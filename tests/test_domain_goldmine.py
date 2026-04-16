from scripts.domain_goldmine import (
    build_domain_candidates,
    check_domain_likely_availability,
    generate_labels,
    score_domain_label,
)


class _Resp:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


def test_generate_labels_contains_seed() -> None:
    labels = generate_labels(["styrofo"], max_labels=80)
    assert "styrofo" in labels
    assert any(label.startswith("styrofo") for label in labels)


def test_score_domain_label_rewards_portfolio_fit() -> None:
    score, fit = score_domain_label("voidsignalvault", ["void", "signal", "github"])
    assert score >= 70
    assert fit >= 2


def test_check_domain_likely_availability_on_404(monkeypatch) -> None:
    def _fake_get(url: str, timeout: float):
        assert "rdap.org/domain/styrofoalpha.com" in url
        return _Resp(404, "")

    monkeypatch.setattr("scripts.domain_goldmine.requests.get", _fake_get)
    status, signal = check_domain_likely_availability("styrofoalpha.com")
    assert status == "likely_available"
    assert signal == "rdap_404"


def test_build_domain_candidates_respects_check_limit(monkeypatch) -> None:
    calls = {"count": 0}

    def _fake_get(url: str, timeout: float):
        calls["count"] += 1
        return _Resp(200, "registered")

    monkeypatch.setattr("scripts.domain_goldmine.requests.get", _fake_get)

    candidates = build_domain_candidates(
        seed_phrases=["styrofo"],
        tlds=["com", "io"],
        portfolio_tags=["void"],
        max_labels=20,
        check_limit=5,
    )

    assert calls["count"] == 5
    assert len(candidates) > 0
    assert sum(1 for c in candidates if c.availability == "unchecked") > 0
