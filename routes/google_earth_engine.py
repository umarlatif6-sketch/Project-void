import logging
import os
import json
import time
import re
import importlib.util
import secrets
from pathlib import Path
from flask import Blueprint, jsonify, request, session

from routes.auth import admin_required, login_required, tier_required
from void_engine.al_jabr_286 import BASE_FREQ, fatiha_286_hexdigest_from_str
from void_engine.google_earth_engine import (
    calculate_grace_correlation_proxy,
    compute_mineral_overlay_swir,
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
from void_engine.wearable.mycelium_adriana_translator import (
    load_device_profile_schema,
    translate_sensor_packet,
)

logger = logging.getLogger(__name__)
gee_bp = Blueprint("google_earth_engine", __name__)

_ROOT = Path(__file__).resolve().parents[1]
_RFQ_AUDIT_LOG_PATH = _ROOT / "data" / "rfq_audit_log.jsonl"
_ION_RESURRECTION_MODULE_PATH = _ROOT / "infrastructure" / "energy_systems" / "ion_resurrection.py"
_WEARABLE_AUDIT_LOG_PATH = _ROOT / "data" / "wearable_ingest_audit.jsonl"
_WEARABLE_INGEST_TOKEN_ENV = "VOID_WEARABLE_INGEST_TOKEN"

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


def _append_rfq_audit_event(event: dict) -> None:
    _RFQ_AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _RFQ_AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True, default=str) + "\n")


def _read_rfq_audit_events(limit: int = 50) -> list[dict]:
    if not _RFQ_AUDIT_LOG_PATH.exists():
        return []

    rows: list[dict] = []
    with _RFQ_AUDIT_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit <= 0:
        return rows
    return rows[-limit:]


def _extract_wearable_token() -> str:
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    if not token:
        token = request.headers.get("X-Wearable-Token", "").strip()
    return token


def _append_wearable_audit_event(event: dict) -> None:
    _WEARABLE_AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _WEARABLE_AUDIT_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, sort_keys=True, default=str) + "\n")


def _read_wearable_audit_events(limit: int = 50) -> list[dict]:
    if not _WEARABLE_AUDIT_LOG_PATH.exists():
        return []
    rows: list[dict] = []
    with _WEARABLE_AUDIT_LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return rows[-max(1, min(limit, 500)):]


def _get_ion_resurrection_module():
    if not _ION_RESURRECTION_MODULE_PATH.exists():
        raise FileNotFoundError(f"missing_module: {_ION_RESURRECTION_MODULE_PATH}")

    spec = importlib.util.spec_from_file_location(
        "void_ion_resurrection",
        _ION_RESURRECTION_MODULE_PATH,
    )
    if not spec or not spec.loader:
        raise RuntimeError("ion_resurrection_module_load_failed")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@gee_bp.route("/api/gee/status", methods=["GET"])
def gee_status():
    payload = get_gee_status()
    return _sovereign_response(payload, objective="gee status surface")


@gee_bp.route("/api/wearable/device-profile-schema", methods=["GET"])
@tier_required("journalist")
def wearable_device_profile_schema():
    try:
        schema = load_device_profile_schema()
        return _sovereign_response(schema, objective="wearable device profile schema", channel="wearable")
    except Exception as exc:  # noqa: BLE001
        logger.error("Wearable schema read failed: %s", exc)
        return _sovereign_response(
            {"ok": False, "error": "schema_unavailable", "detail": _redact_transport_frequency(str(exc))},
            objective="wearable schema read error",
            status=502,
            channel="wearable",
        )


@gee_bp.route("/api/wearable/ingest", methods=["POST"])
def wearable_ingest():
    configured = (os.environ.get(_WEARABLE_INGEST_TOKEN_ENV) or "").strip()
    if not configured:
        return _sovereign_response(
            {"ok": False, "error": "wearable_ingest_not_configured"},
            objective="wearable ingest not configured",
            status=503,
            channel="wearable",
        )

    presented = _extract_wearable_token()
    if not presented or not secrets.compare_digest(presented, configured):
        return _sovereign_response(
            {"ok": False, "error": "unauthorized"},
            objective="wearable ingest unauthorized",
            status=401,
            channel="wearable",
        )

    data = request.get_json(silent=True) or {}
    allowed = {"device_profile", "sensor_values", "timestamp"}
    extras = sorted(set(data.keys()) - allowed)
    if extras:
        return _sovereign_response(
            {"ok": False, "error": "unexpected_fields", "fields": extras},
            objective="wearable ingest unexpected fields",
            status=400,
            channel="wearable",
        )

    device_profile = data.get("device_profile")
    sensor_values = data.get("sensor_values")
    timestamp = data.get("timestamp")

    if not isinstance(device_profile, dict):
        return _sovereign_response(
            {"ok": False, "error": "device_profile_required"},
            objective="wearable ingest missing profile",
            status=400,
            channel="wearable",
        )
    if not isinstance(sensor_values, dict):
        return _sovereign_response(
            {"ok": False, "error": "sensor_values_required"},
            objective="wearable ingest missing values",
            status=400,
            channel="wearable",
        )

    try:
        clean_values = {str(k): float(v) for k, v in sensor_values.items()}
        ts = float(timestamp) if timestamp is not None else None
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "invalid_numeric_payload"},
            objective="wearable ingest invalid numeric payload",
            status=400,
            channel="wearable",
        )

    translated = translate_sensor_packet(
        device_profile=device_profile,
        sensor_values=clean_values,
        timestamp=ts,
    )
    if not translated.get("ok"):
        return _sovereign_response(
            translated,
            objective="wearable ingest translation failure",
            status=400,
            channel="wearable",
        )

    _append_wearable_audit_event({
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "device_id": translated.get("device_id"),
        "device_type": translated.get("device_type"),
        "state": translated.get("state"),
        "codon": translated.get("codon"),
        "resonance_target_hz": translated.get("resonance_target_hz"),
        "sovereign_packet_id": translated.get("sovereign_packet_id"),
    })

    return _sovereign_response(
        translated,
        objective=f"wearable ingest {translated.get('device_id')}",
        channel="wearable",
    )


@gee_bp.route("/api/wearable/audit", methods=["GET"])
@admin_required
def wearable_audit():
    try:
        limit = int(request.args.get("limit", 50) or 50)
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "invalid_limit"},
            objective="wearable audit invalid limit",
            status=400,
            channel="wearable",
        )

    events = _read_wearable_audit_events(limit=limit)
    return _sovereign_response(
        {
            "ok": True,
            "event_count": len(events),
            "events": events,
            "limit": max(1, min(limit, 500)),
        },
        objective="wearable audit read",
        channel="wearable",
    )


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


@gee_bp.route("/api/gee/mineral-overlay", methods=["POST"])
@tier_required("journalist")
def gee_mineral_overlay():
    data = request.get_json(silent=True) or {}

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "lat_lon_required"},
            objective="gee mineral overlay invalid input",
            status=400,
        )

    start_date = (data.get("start_date") or "").strip()
    end_date = (data.get("end_date") or "").strip()
    if not start_date or not end_date:
        start_date, end_date = default_date_window(180)

    try:
        buffer_m = int(data.get("buffer_m", 50_000) or 50_000)
        max_cloud_pct = float(data.get("max_cloud_pct", 20.0) or 20.0)
        scale = int(data.get("scale", 20) or 20)
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "invalid_numeric_params"},
            objective="gee mineral overlay invalid numeric params",
            status=400,
        )

    try:
        result = compute_mineral_overlay_swir(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            buffer_m=buffer_m,
            max_cloud_pct=max_cloud_pct,
            scale=scale,
        )
        return _sovereign_response(result, objective=f"gee mineral overlay {lat},{lon}")
    except ValueError as exc:
        return _sovereign_response(
            {"ok": False, "error": str(exc)},
            objective="gee mineral overlay validation error",
            status=400,
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("GEE mineral overlay route failed: %s", exc)
        return _sovereign_response(
            {"ok": False, "error": "gee_execution_failed", "detail": _redact_transport_frequency(str(exc))},
            objective="gee mineral overlay execution error",
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
@tier_required("journalist")
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

    audit_event = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "user_id": session.get("user_id"),
        "tier": session.get("tier"),
        "district_key": district_key,
        "grace_correlation": grace_correlation,
        "water_trend_slope_cm_per_year": water_slope,
        "dry_period": dry_period,
        "rfq_triggered": result.get("rfq_triggered"),
        "rfq_profile": result.get("rfq_profile"),
        "sovereign_packet_id": result.get("sovereign_packet_id"),
    }
    _append_rfq_audit_event(audit_event)

    return _sovereign_response(result, objective=f"gee rfq state {district_key}")


@gee_bp.route("/api/gee/rfq-audit", methods=["GET"])
@admin_required
def gee_rfq_audit():
    try:
        limit = int(request.args.get("limit", 50) or 50)
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "invalid_limit"},
            objective="gee rfq audit invalid limit",
            status=400,
        )

    limit = max(1, min(limit, 500))
    events = _read_rfq_audit_events(limit=limit)
    return _sovereign_response(
        {
            "ok": True,
            "limit": limit,
            "event_count": len(events),
            "events": events,
        },
        objective="gee rfq audit read",
    )


@gee_bp.route("/api/energy/ion-resurrection/simulate", methods=["POST"])
@tier_required("journalist")
def ion_resurrection_simulate():
    data = request.get_json(silent=True) or {}

    sample = data.get("sample") or {}
    env = data.get("environment") or {}

    try:
        chemistry = str(sample.get("chemistry") or "li_ion")
        open_circuit_voltage_v = float(sample.get("open_circuit_voltage_v", 3.0))
        nominal_voltage_v = float(sample.get("nominal_voltage_v", 3.7))
        internal_resistance_mohm = float(sample.get("internal_resistance_mohm", 180.0))
        state_of_health_pct = float(sample.get("state_of_health_pct", 65.0))

        temperature_c = float(env.get("temperature_c", 30.0))
        relative_humidity_pct = float(env.get("relative_humidity_pct", 60.0))
        region = str(env.get("region") or "Pakistan")

        target_frequency_hz = float(data.get("target_frequency_hz", 432.0))
        district_key = str(data.get("district_key") or "soan_valley")
        water_trend_slope_cm_per_year = data.get("water_trend_slope_cm_per_year")
        water_trend_slope_cm_per_year = (
            float(water_trend_slope_cm_per_year)
            if water_trend_slope_cm_per_year is not None
            else None
        )
    except Exception:  # noqa: BLE001
        return _sovereign_response(
            {"ok": False, "error": "invalid_numeric_params"},
            objective="ion resurrection invalid params",
            status=400,
            channel="energy",
        )

    try:
        mod = _get_ion_resurrection_module()
        resurrector = mod.IonResurrector(target_frequency_hz=target_frequency_hz)
        sample_obj = mod.BatterySample(
            chemistry=chemistry,
            open_circuit_voltage_v=open_circuit_voltage_v,
            nominal_voltage_v=nominal_voltage_v,
            internal_resistance_mohm=internal_resistance_mohm,
            state_of_health_pct=state_of_health_pct,
        )
        env_obj = mod.EnvironmentProfile(
            temperature_c=temperature_c,
            relative_humidity_pct=relative_humidity_pct,
            region=region,
        )
        result = resurrector.execute_protocol(
            sample=sample_obj,
            env=env_obj,
            district_key=district_key,
            water_trend_slope_cm_per_year=water_trend_slope_cm_per_year,
        )
        return _sovereign_response(
            result,
            objective=f"ion resurrection simulate {district_key}",
            channel="energy",
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("Ion resurrection simulation failed: %s", exc)
        return _sovereign_response(
            {"ok": False, "error": "simulation_failed", "detail": _redact_transport_frequency(str(exc))},
            objective="ion resurrection simulation error",
            status=502,
            channel="energy",
        )


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
    include_mineral_overlay = bool(data.get("include_mineral_overlay", True))
    run_agents = bool(data.get("run_agents", True))
    run_adriana_synthesis = bool(data.get("run_adriana_synthesis", True))

    gee_result = run_gee_exploration_orchestration(
        start_date=start_date,
        end_date=end_date,
        district_keys=district_keys,
        include_ndvi=include_ndvi,
        include_water_trend=include_water_trend,
        include_mineral_overlay=include_mineral_overlay,
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
