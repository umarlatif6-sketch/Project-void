"""
Dual-Mode Solar Harvester Power Profile
=========================================
Codifies the passive solar harvester used to power Sovereign Nodes.

The harvester operates in two complementary modes:
  - ELECTRICITY mode  (ambient >= 15 °C): photovoltaic panels produce usable
    electrical energy fed directly to the flywheel charge bus.
  - HEATING mode      (ambient < 15 °C): thermal absorber panels transfer heat
    to the machine enclosure, reducing the energy cost of keeping the biological
    substrate and silk wiring within optimal temperature bands.
  - OFF_ANGLE         : temporary shade / polar night condition — harvester
    output near zero.

The 15 °C crossover was chosen because at lower temperatures the photovoltaic
efficiency of the chosen CIGS thin-film panels drops below the heating
efficiency of the selective absorber coating.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

SolarMode = Literal["electricity", "heating", "off_angle"]

# ── Physical constants ─────────────────────────────────────────────────────
CROSSOVER_TEMP_C: float = 15.0
"""Temperature (°C) below which the harvester switches from electricity to heating mode."""

PANEL_AREA_M2: float = 2.4
"""Total panel aperture area in square metres."""

SOLAR_IRRADIANCE_NOMINAL_W_M2: float = 850.0
"""Nominal solar irradiance used for peak calculations (W/m²), ~0.85 of 1000 W/m² STC."""

# ── Electricity mode ───────────────────────────────────────────────────────
ELECTRICITY_MODE_EFFICIENCY: float = 0.18
"""CIGS thin-film photovoltaic efficiency at STC (18%)."""

ELECTRICITY_PEAK_OUTPUT_W: float = PANEL_AREA_M2 * SOLAR_IRRADIANCE_NOMINAL_W_M2 * ELECTRICITY_MODE_EFFICIENCY
"""Peak electrical output (W) ≈ 367 W under nominal irradiance."""

ELECTRICITY_DAILY_YIELD_KWH: float = round(ELECTRICITY_PEAK_OUTPUT_W * 5.5 / 1000, 2)
"""Estimated daily yield (kWh) assuming 5.5 peak sun hours (Novosibirsk summer average)."""

# ── Heating mode ──────────────────────────────────────────────────────────
HEATING_MODE_EFFICIENCY: float = 0.90
"""Selective-absorber thermal efficiency (90%) — most incident energy becomes heat."""

HEATING_PEAK_OUTPUT_W: float = PANEL_AREA_M2 * SOLAR_IRRADIANCE_NOMINAL_W_M2 * HEATING_MODE_EFFICIENCY
"""Peak thermal output (W) ≈ 1836 W — far exceeds electrical mode because losses are lower."""

HEATING_DAILY_YIELD_KWH_THERMAL: float = round(HEATING_PEAK_OUTPUT_W * 4.0 / 1000, 2)
"""Estimated daily thermal yield (kWh) assuming 4.0 usable sun hours (Novosibirsk winter)."""

# ── Node power draw budget ─────────────────────────────────────────────────
NODE_POWER_DRAW_W: dict[str, float] = {
    "full_compute": 85.0,
    "mesh_relay":   25.0,
    "sleep":         4.5,
    "idle":         18.0,
}
"""Node power draw (W) in each operational state."""

NODE_STANDBY_HOURS_FROM_SOLAR: float = round(
    ELECTRICITY_DAILY_YIELD_KWH * 1000 / NODE_POWER_DRAW_W["idle"], 1
)
"""Estimated hours of idle-state operation per day from solar alone (electricity mode)."""


@dataclass(frozen=True)
class SolarStatus:
    mode: SolarMode
    ambient_temp_c: float
    estimated_output_w: float
    efficiency: float
    grid_independent: bool
    description: str


def get_solar_mode(ambient_temp_c: float, irradiance_w_m2: float = SOLAR_IRRADIANCE_NOMINAL_W_M2) -> SolarStatus:
    """
    Return the current solar harvester mode and estimated output given ambient
    temperature and (optionally) measured irradiance.

    Args:
        ambient_temp_c: Current outdoor temperature in degrees Celsius.
        irradiance_w_m2: Measured solar irradiance in W/m². Defaults to nominal.

    Returns:
        SolarStatus dataclass with mode, output estimate, and a human-readable description.
    """
    if irradiance_w_m2 < 50.0:
        return SolarStatus(
            mode="off_angle",
            ambient_temp_c=ambient_temp_c,
            estimated_output_w=0.0,
            efficiency=0.0,
            grid_independent=False,
            description="Harvester off-angle or in darkness — minimal output.",
        )

    if ambient_temp_c >= CROSSOVER_TEMP_C:
        output_w = PANEL_AREA_M2 * irradiance_w_m2 * ELECTRICITY_MODE_EFFICIENCY
        is_grid_independent = output_w >= NODE_POWER_DRAW_W["idle"]
        return SolarStatus(
            mode="electricity",
            ambient_temp_c=ambient_temp_c,
            estimated_output_w=round(output_w, 1),
            efficiency=ELECTRICITY_MODE_EFFICIENCY,
            grid_independent=is_grid_independent,
            description=(
                f"Electricity mode active. {output_w:.0f} W photovoltaic output. "
                f"Node is {'grid-independent' if is_grid_independent else 'drawing from flywheel reserve'}."
            ),
        )
    else:
        output_w = PANEL_AREA_M2 * irradiance_w_m2 * HEATING_MODE_EFFICIENCY
        return SolarStatus(
            mode="heating",
            ambient_temp_c=ambient_temp_c,
            estimated_output_w=round(output_w, 1),
            efficiency=HEATING_MODE_EFFICIENCY,
            grid_independent=False,
            description=(
                f"Heating mode active. {output_w:.0f} W thermal output reducing substrate heating load. "
                f"Below {CROSSOVER_TEMP_C}°C crossover — PV output would be suboptimal."
            ),
        )


def get_profile_summary() -> dict:
    """Return a machine-readable summary of the harvester power profile."""
    return {
        "crossover_temp_c": CROSSOVER_TEMP_C,
        "panel_area_m2": PANEL_AREA_M2,
        "electricity_mode": {
            "efficiency_pct": round(ELECTRICITY_MODE_EFFICIENCY * 100, 1),
            "peak_output_w": round(ELECTRICITY_PEAK_OUTPUT_W, 1),
            "daily_yield_kwh": ELECTRICITY_DAILY_YIELD_KWH,
        },
        "heating_mode": {
            "efficiency_pct": round(HEATING_MODE_EFFICIENCY * 100, 1),
            "peak_output_w_thermal": round(HEATING_PEAK_OUTPUT_W, 1),
            "daily_yield_kwh_thermal": HEATING_DAILY_YIELD_KWH_THERMAL,
        },
        "node_power_draw_w": NODE_POWER_DRAW_W,
        "idle_hours_from_solar_per_day": NODE_STANDBY_HOURS_FROM_SOLAR,
    }
