import logging
import os
import json
import time
import re
from flask import Blueprint, jsonify, request

from routes.auth import admin_required, login_required
from void_engine.al_jabr_286 import BASE_FREQ, fatiha_286_hexdigest_from_str
from void_engine.google_earth_engine import (
    calculate_grace_correlation_proxy,
    compute_water_table_trend,
    compute_ndvi_snapshot,
    default_date_window,
    evaluate_anomaly_thresholds,
    get_dataset_catalog,
    get_district_presets,
    get_gee_status,
    run_gee_exploration_orchestration,
    trigger_rfq_on_melt,
)
from void_engine.openclaw_bridge import build_sovereign_bridge_packet

logger = logging.getLogger(__name__)
gee_bp = Blueprint("google_earth_engine", __name__)

_TRANSPORT_REDACTION = "[external-transport-redacted]"
_LEAK_PATTERNS = [
    re.compile(r"sha[-_ ]?256", re.IGNORECASE),
    re.compile(r"256[-_ ]?bit", re.IGNORECASE),
    re.compile(r"\b256\b"),
]


def _redact_transport_frequency(text: str) -> str:
    cleaned = text or ""
    for pattern in _LEAK_PATTERNS:
        cleaned = pattern.sub(_TRANSPORT_REDACTION, cleaned)
    return cleaned


def _wrap_sovereign_payload(payload: dict, objective: str, channel: str = "gee") -> dict:
    envelope = build_sovereign_bridge_packet(objective, channel=channel)
    if not envelope:
        fallback_seed = f"{channel}|{objective}|{time.time_ns()}"
        fallback_packet_id = fatiha_286_hexdigest_from_str(fallback_seed)[:64]
        envelope = {
            "packet_id": fallback_packet_id,
            "chain": 286,
            "base_frequency_hz": BASE_FREQ,
            "bridge_mode": "sovereign_opaque_transport",
        }

    normalized = dict(payload)
    normalized.setdefault("ok", True)
    normalized["sovereign_packet_id"] = envelope.get("packet_id")
    normalized["chain"] = envelope.get("chain", 286)
    normalized["base_frequency_hz"] = envelope.get("base_frequency_hz", BASE_FREQ)
    normalized["bridge_mode"] = envelope.get("bridge_mode", "sovereign_opaque_transport")
    normalized["al_jabr_286_hash"] = fatiha_286_hexdigest_from_str(
        json.dumps(payload, sort_keys=True, default=str)
    )
    normalized["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return normalized


def _sovereign_response(payload: dict, objective: str, status: int = 200, channel: str = "gee"):
    return jsonify(_wrap_sovereign_payload(payload, objective=objective, channel=channel)), status


@gee_bp.route("/api/gee/status", methods=["GET"])
def gee_status():
    payload = get_gee_status()
    return _sovereign_response(payload, objective="gee status surface")


@gee_bp.route("/api/gee/district-presets", methods=["GET"])
def gee_district_presets():
    country = (request.args.get("country") or "Pakistan").strip() or "Pakistan"
    payload = get_district_presets(country=country)
    return _sovereign_response(payload, objective=f"gee district presets {country}")


@gee_bp.route("/api/gee/datasets", methods=["GET"])
def gee_dataset_catalog():
    payload = get_dataset_catalog()
    return _sovereign_response(payload, objective="gee dataset catalog")


@gee_bp.route("/api/gee/ndvi", methods=["POST"])
@login_required
def gee_ndvi():
    data = request.get_json(silent=True) or {}

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except Exception:  # noqa: BLE001
        return _sovereign_response({"ok": False, "error": "lat_lon_required"}, objective="gee ndvi invalid input", status=400)

    start_date = (data.get("start_date") or "").strip()
    end_date = (data.get("end_date") or "").strip()
    if not start_date or not end_date:
        start_date, end_date = default_date_window(45)

    try:
        buffer_m = int(data.get("buffer_m", 250) or 250)
        max_cloud_pct = float(data.get("max_cloud_pct", 20.0) or 20.0)
        scale = int(data.get("scale", 10) or 10)
    except Exception:  # noqa: BLE001
        return _sovereign_response({"ok": False, "error": "invalid_numeric_params"}, objective="gee ndvi invalid numeric params", status=400)

    try:
        result = compute_ndvi_snapshot(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            buffer_m=buffer_m,
            max_cloud_pct=max_cloud_pct,
            scale=scale,
        )
        return _sovereign_response(result, objective=f"gee ndvi {lat},{lon}")
    except ValueError as exc:
        return _sovereign_response({"ok": False, "error": str(exc)}, objective="gee ndvi validation error", status=400)
    except Exception as exc:  # noqa: BLE001
        logger.error("GEE NDVI route failed: %s", exc)
        return _sovereign_response(
            {"ok": False, "error": "gee_execution_failed", "detail": _redact_transport_frequency(str(exc))},
            objective="gee ndvi execution error",
            status=502,
        )


@gee_bp.route("/api/gee/water-table-trend", methods=["POST"])
@login_required
def gee_water_table_trend():
    data = request.get_json(silent=True) or {}

    start_date = (data.get("start_date") or "").strip()
    end_date = (data.get("end_date") or "").strip()
    if not start_date or not end_date:
        start_date, end_date = default_date_window(365 * 5)

    country = (data.get("country") or "Pakistan").strip() or "Pakistan"

    lat = data.get("lat")
    lon = data.get("lon")
    if lat is not None and lon is not None:
        try:
            lat = float(lat)
            lon = float(lon)
        except Exception:  # noqa: BLE001
            return _sovereign_response({"ok": False, "error": "invalid_lat_lon"}, objective="gee water trend invalid lat lon", status=400)
    else:
        lat = None
        lon = None

    try:
        buffer_m = int(data.get("buffer_m", 25_000) or 25_000)
        scale = int(data.get("scale", 30_000) or 30_000)
    except Exception:  # noqa: BLE001
        return _sovereign_response({"ok": False, "error": "invalid_numeric_params"}, objective="gee water trend invalid numeric params", status=400)

    try:
        result = compute_water_table_trend(
            start_date=start_date,
            end_date=end_date,
            country=country,
            lat=lat,
            lon=lon,
            buffer_m=buffer_m,
            scale=scale,
        )
        objective = f"gee water trend {country}" if lat is None else f"gee water trend point {lat},{lon}"
        return _sovereign_response(result, objective=objective)
    except ValueError as exc:
        return _sovereign_response({"ok": False, "error": str(exc)}, objective="gee water trend validation error", status=400)
    except Exception as exc:  # noqa: BLE001
        logger.error("GEE water-table route failed: %s", exc)
        return _sovereign_response(
            {"ok": False, "error": "gee_execution_failed", "detail": _redact_transport_frequency(str(exc))},
            objective="gee water trend execution error",
            status=502,
        )


@gee_bp.route("/api/gee/anomaly-thresholds", methods=["POST"])
@login_required
def gee_anomaly_thresholds():
    data = request.get_json(silent=True) or {}
    water_slope = data.get("water_trend_slope_cm_per_year")
    ndvi_mean = data.get("ndvi_mean")

    try:
        water_slope = float(water_slope) if water_slope is not None else None
        ndvi_mean = float(ndvi_mean) if ndvi_mean is not None else None
    except Exception:  # noqa: BLE001
        return _sovereign_response({"ok": False, "error": "invalid_numeric_params"}, objective="gee anomaly invalid numeric params", status=400)

    result = evaluate_anomaly_thresholds(
        water_trend_slope_cm_per_year=water_slope,
        ndvi_mean=ndvi_mean,
    )
    return _sovereign_response(result, objective="gee anomaly threshold evaluation")


@gee_bp.route("/api/gee/rfq-state", methods=["POST"])
@login_required
def gee_rfq_state():
    data = request.get_json(silent=True) or {}

    district_key = str(data.get("district_key") or "soan_valley").strip() or "soan_valley"
    dry_period = bool(data.get("dry_period", False))

    grace_correlation = data.get("grace_correlation")
    water_slope = data.get("water_trend_slope_cm_per_year")

    try:
        grace_correlation = float(grace_correlation) if grace_correlation is not None else None
        water_slope = float(water_slope) if water_slope is not None else None
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "invalid_numeric_params"},
            objective="gee rfq state invalid numeric params",
            status=400,
        )

    if grace_correlation is None:
        grace_correlation = calculate_grace_correlation_proxy(
            water_trend_slope_cm_per_year=water_slope,
        )

    result = trigger_rfq_on_melt(
        district_key=district_key,
        grace_correlation=grace_correlation,
        water_trend_slope_cm_per_year=water_slope,
        dry_period=dry_period,
    )
    return _sovereign_response(result, objective=f"gee rfq state {district_key}")


@gee_bp.route("/api/gee/orchestrate-exploration", methods=["POST"])
@admin_required
def gee_orchestrate_exploration():
    data = request.get_json(silent=True) or {}

    start_date = (data.get("start_date") or "").strip()
    end_date = (data.get("end_date") or "").strip()
    if not start_date or not end_date:
        start_date, end_date = default_date_window(365 * 2)

    district_keys = data.get("district_keys")
    if district_keys is not None and not isinstance(district_keys, list):
        return _sovereign_response({"ok": False, "error": "district_keys_must_be_list"}, objective="gee orchestration invalid district keys", status=400)

    include_ndvi = bool(data.get("include_ndvi", True))
    include_water_trend = bool(data.get("include_water_trend", True))
    run_agents = bool(data.get("run_agents", True))
    run_adriana_synthesis = bool(data.get("run_adriana_synthesis", True))

    gee_result = run_gee_exploration_orchestration(
        start_date=start_date,
        end_date=end_date,
        district_keys=district_keys,
        include_ndvi=include_ndvi,
        include_water_trend=include_water_trend,
    )

    if not gee_result.get("ok"):
        return _sovereign_response(gee_result, objective="gee orchestration invalid run", status=400)

    agent_result = None
    if run_agents:
        try:
            from void_engine.formation_orchestrator import run_full_formation

            seed = (
                f"GEE exploration Pakistan | date:{start_date}->{end_date} | "
                f"districts:{gee_result.get('district_count')} | "
                f"warnings:{gee_result.get('warning_or_critical_count')}"
            )
            agent_result = run_full_formation(
                seed_text=seed,
                swarm_agents=10,
                swarm_rounds=3,
                engine_agents=20,
                engine_rounds=3,
                sandbox_rounds=3,
            )
        except Exception as exc:  # noqa: BLE001
            logger.error("GEE orchestration agent fan-out failed: %s", exc)
            agent_result = {"ok": False, "error": str(exc)}

    adriana_synthesis = None
    adriana_max_tokens = int(os.environ.get("ADRIANA_INTERNAL_LLM_MAX_TOKENS", "1200") or 1200)
    if run_adriana_synthesis:
        try:
            from void_engine.adriana_core import query as adriana_query

            prompt = (
                "Summarize this Pakistan GEE exploration for sovereign operations. "
                "Prioritize district risk, water-trend direction, NDVI anomalies, and next 3 actions.\n\n"
                f"GEE: {gee_result}\n\n"
                f"AGENTS: {agent_result}"
            )
            q = adriana_query(prompt, max_tokens=adriana_max_tokens)
            if q.get("ok"):
                adriana_synthesis = q.get("response")
            else:
                adriana_synthesis = None
        except Exception as exc:  # noqa: BLE001
            logger.warning("Adriana synthesis skipped: %s", exc)

    return _sovereign_response({
        "ok": True,
        "gee": gee_result,
        "agents": agent_result,
        "adriana_synthesis": adriana_synthesis,
        "adriana_internal_llm_tokens": adriana_max_tokens,
    }, objective="gee orchestration exploration")
