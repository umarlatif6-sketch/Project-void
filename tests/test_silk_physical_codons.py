from __future__ import annotations

from void_engine.google_earth_engine import (
    calculate_grace_correlation_proxy,
    trigger_rfq_on_melt,
)
from void_foundation import calculate_thread_tension


def test_calculate_grace_correlation_proxy_none():
    assert calculate_grace_correlation_proxy(water_trend_slope_cm_per_year=None) is None


def test_calculate_grace_correlation_proxy_is_bounded():
    val = calculate_grace_correlation_proxy(water_trend_slope_cm_per_year=-3.2)
    assert val == 0.99


def test_trigger_rfq_on_melt_triggers_for_soan_threshold():
    payload = trigger_rfq_on_melt(
        district_key="soan_valley",
        grace_correlation=0.9,
        water_trend_slope_cm_per_year=-1.1,
        dry_period=False,
    )

    assert payload["rfq_triggered"] is True
    assert payload["rfq_profile"] == "heavy_weave"
    assert payload["recommended_silk_to_zinc_ratio"] == "66:34"
    assert payload["chain"] == 286


def test_trigger_rfq_on_melt_does_not_trigger_outside_target_district():
    payload = trigger_rfq_on_melt(
        district_key="lahore",
        grace_correlation=0.95,
        water_trend_slope_cm_per_year=-1.5,
    )

    assert payload["rfq_triggered"] is False
    assert payload["rfq_profile"] == "baseline"


def test_calculate_thread_tension_profiles_heavy_weave():
    result = calculate_thread_tension(moisture_correlation=0.9)

    assert result["weave_profile"] == "heavy_weave"
    assert result["target_tension_newton"] > result["base_tension_newton"]
