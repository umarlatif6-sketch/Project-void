import logging
import os
import threading
import concurrent.futures
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import numpy as np

from void_engine.al_jabr_286 import BASE_FREQ, fatiha_286_hexdigest_from_str
from void_engine.openclaw_bridge import build_sovereign_bridge_packet

logger = logging.getLogger(__name__)

_init_lock = threading.Lock()
_initialized = False
_init_error: str | None = None

# API stubs for district geometry and alert thresholds.
DISTRICT_PRESETS_PAKISTAN: Dict[str, Dict[str, Any]] = {
    "lahore": {
        "label": "Lahore District",
        "country": "Pakistan",
        "center": {"lat": 31.5204, "lon": 74.3587},
        "buffer_m": 35000,
    },
    "islamabad": {
        "label": "Islamabad Capital Territory",
        "country": "Pakistan",
        "center": {"lat": 33.6844, "lon": 73.0479},
        "buffer_m": 25000,
    },
    "soan_valley": {
        "label": "Soan Valley",
        "country": "Pakistan",
        "center": {"lat": 33.35, "lon": 73.1},
        "buffer_m": 45000,
    },
}

ANOMALY_THRESHOLDS_DEFAULT: Dict[str, Dict[str, float]] = {
    "water_table_decline_cm_per_year": {
        "warning": -0.5,
        "critical": -1.5,
    },
    "ndvi_mean": {
        "warning_low": 0.22,
        "critical_low": 0.15,
        "warning_high": 0.85,
    },
}

GEE_DATASET_CATALOG: Dict[str, Dict[str, str]] = {
    "ndvi_sentinel2": {
        "id": "COPERNICUS/S2_SR_HARMONIZED",
        "metric": "NDVI",
        "notes": "10m optical surface reflectance for vegetation health.",
    },
    "water_storage_grace": {
        "id": "NASA/GRACE/MASS_GRIDS/LAND",
        "metric": "lwe_thickness_csr",
        "notes": "Terrestrial water storage anomaly proxy for regional groundwater stress.",
    },
}

RFQ_POLICY_DEFAULT: Dict[str, Any] = {
    "target_district_key": "soan_valley",
    "moisture_correlation_trigger": 0.85,
    "dry_period_silk_to_zinc_ratio": "74:26",
    "high_humidity_silk_to_zinc_ratio": "66:34",
    "baseline_profile": "baseline",
    "triggered_profile": "heavy_weave",
}


def _wrap_sovereign_payload(payload: dict, objective: str, channel: str = "gee") -> dict:
    envelope = build_sovereign_bridge_packet(objective, channel=channel)
    if not envelope:
        fallback_seed = f"{channel}|{objective}|{time.time_ns()}"
        envelope = {
            "packet_id": fatiha_286_hexdigest_from_str(fallback_seed)[:64],
            "chain": 286,
            "base_frequency_hz": BASE_FREQ,
            "bridge_mode": "sovereign_opaque_transport",
        }

    wrapped = dict(payload)
    wrapped.setdefault("ok", True)
    wrapped["sovereign_packet_id"] = envelope.get("packet_id")
    wrapped["chain"] = envelope.get("chain", 286)
    wrapped["base_frequency_hz"] = envelope.get("base_frequency_hz", BASE_FREQ)
    wrapped["bridge_mode"] = envelope.get("bridge_mode", "sovereign_opaque_transport")
    wrapped["al_jabr_286_hash"] = fatiha_286_hexdigest_from_str(
        json.dumps(payload, sort_keys=True, default=str)
    )
    wrapped["timestamp"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return wrapped


def _import_ee():
    try:
        import ee  # type: ignore
        return ee
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"earthengine_api_unavailable: {exc}") from exc


def _env_truthy(name: str, default: bool = False) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _build_service_account_credentials(ee):
    service_account = (os.environ.get("GEE_SERVICE_ACCOUNT") or "").strip()
    private_key = os.environ.get("GEE_PRIVATE_KEY") or ""
    private_key_file = (os.environ.get("GEE_PRIVATE_KEY_FILE") or "").strip()

    if not service_account:
        return None

    if private_key:
        return ee.ServiceAccountCredentials(service_account, key_data=private_key.replace("\\n", "\n"))

    if private_key_file:
        return ee.ServiceAccountCredentials(service_account, key_file=private_key_file)

    raise RuntimeError(
        "missing_gee_private_key: set GEE_PRIVATE_KEY or GEE_PRIVATE_KEY_FILE when GEE_SERVICE_ACCOUNT is set"
    )


def _initialize() -> None:
    global _initialized, _init_error

    if _initialized:
        return

    with _init_lock:
        if _initialized:
            return

        ee = _import_ee()
        project = (os.environ.get("GEE_PROJECT") or "").strip() or None

        try:
            credentials = _build_service_account_credentials(ee)
            if credentials is not None:
                ee.Initialize(credentials=credentials, project=project)
            elif _env_truthy("GEE_USE_DEFAULT_AUTH", default=False):
                ee.Initialize(project=project)
            else:
                raise RuntimeError(
                    "gee_credentials_not_configured: set service-account env vars or GEE_USE_DEFAULT_AUTH=true"
                )
            _initialized = True
            _init_error = None
        except Exception as exc:  # noqa: BLE001
            _initialized = False
            _init_error = str(exc)
            raise


def get_gee_status() -> Dict[str, Any]:
    configured = bool(
        (os.environ.get("GEE_SERVICE_ACCOUNT") or "").strip()
        and (
            (os.environ.get("GEE_PRIVATE_KEY") or "").strip()
            or (os.environ.get("GEE_PRIVATE_KEY_FILE") or "").strip()
        )
    ) or _env_truthy("GEE_USE_DEFAULT_AUTH", default=False)

    return {
        "configured": configured,
        "initialized": _initialized,
        "project": (os.environ.get("GEE_PROJECT") or "").strip() or None,
        "auth_mode": "service_account" if (os.environ.get("GEE_SERVICE_ACCOUNT") or "").strip() else "default",
        "last_error": _init_error,
    }


def compute_ndvi_snapshot(
    *,
    lat: float,
    lon: float,
    start_date: str,
    end_date: str,
    buffer_m: int = 250,
    max_cloud_pct: float = 20.0,
    scale: int = 10,
) -> Dict[str, Any]:
    if not (-90.0 <= lat <= 90.0):
        raise ValueError("invalid_lat")
    if not (-180.0 <= lon <= 180.0):
        raise ValueError("invalid_lon")
    if buffer_m < 10 or buffer_m > 50000:
        raise ValueError("invalid_buffer_m")
    if max_cloud_pct < 0 or max_cloud_pct > 100:
        raise ValueError("invalid_max_cloud_pct")
    if scale < 10 or scale > 500:
        raise ValueError("invalid_scale")

    _initialize()
    ee = _import_ee()

    point = ee.Geometry.Point([lon, lat])
    geometry = point.buffer(buffer_m)

    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(geometry)
        .filterDate(start_date, end_date)
        .filter(ee.Filter.lte("CLOUDY_PIXEL_PERCENTAGE", max_cloud_pct))
        .sort("CLOUDY_PIXEL_PERCENTAGE")
    )

    count = int(collection.size().getInfo() or 0)
    if count == 0:
        return _wrap_sovereign_payload({
            "ok": True,
            "lat": lat,
            "lon": lon,
            "start_date": start_date,
            "end_date": end_date,
            "image_count": 0,
            "message": "no_imagery_for_filters",
        }, objective="gee ndvi snapshot", channel="gee-engine")

    image = ee.Image(collection.first())
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")

    mean_ndvi = ndvi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=geometry,
        scale=scale,
        bestEffort=True,
        maxPixels=1_000_000_000,
    ).get("NDVI").getInfo()

    date_ms = image.get("system:time_start").getInfo()
    cloud_pct = image.get("CLOUDY_PIXEL_PERCENTAGE").getInfo()

    acquired_at = None
    if date_ms is not None:
        acquired_at = datetime.fromtimestamp(float(date_ms) / 1000, tz=timezone.utc).strftime("%Y-%m-%d")

    return _wrap_sovereign_payload({
        "ok": True,
        "lat": lat,
        "lon": lon,
        "start_date": start_date,
        "end_date": end_date,
        "image_count": count,
        "acquired_at": acquired_at,
        "cloudy_pixel_percentage": cloud_pct,
        "ndvi_mean": mean_ndvi,
        "dataset": "COPERNICUS/S2_SR_HARMONIZED",
        "band_math": "(B8 - B4) / (B8 + B4)",
        "buffer_m": buffer_m,
        "scale_m": scale,
    }, objective="gee ndvi snapshot", channel="gee-engine")


def default_date_window(days: int = 45) -> tuple[str, str]:
    now = datetime.now(timezone.utc).date()
    start = now - timedelta(days=days)
    return start.isoformat(), now.isoformat()


def get_district_presets(country: str = "Pakistan") -> Dict[str, Any]:
    selected_country = (country or "Pakistan").strip() or "Pakistan"
    if selected_country.lower() != "pakistan":
        return _wrap_sovereign_payload({
            "ok": True,
            "country": selected_country,
            "presets": {},
            "message": "no_presets_configured_for_country",
        }, objective="gee district presets", channel="gee-engine")
    return _wrap_sovereign_payload({
        "ok": True,
        "country": "Pakistan",
        "presets": DISTRICT_PRESETS_PAKISTAN,
    }, objective="gee district presets", channel="gee-engine")


def get_dataset_catalog() -> Dict[str, Any]:
    return _wrap_sovereign_payload({
        "ok": True,
        "catalog": GEE_DATASET_CATALOG,
    }, objective="gee dataset catalog", channel="gee-engine")


def evaluate_anomaly_thresholds(
    *,
    water_trend_slope_cm_per_year: float | None = None,
    ndvi_mean: float | None = None,
    thresholds: Dict[str, Dict[str, float]] | None = None,
) -> Dict[str, Any]:
    """
    Placeholder alert lane for resonance warning states.
    442 Hz indicates a warning/critical anomaly pulse.
    """
    cfg = thresholds or ANOMALY_THRESHOLDS_DEFAULT
    alerts = []

    wt = cfg.get("water_table_decline_cm_per_year", {})
    if water_trend_slope_cm_per_year is not None:
        if water_trend_slope_cm_per_year <= wt.get("critical", -1.5):
            alerts.append({
                "metric": "water_table_decline_cm_per_year",
                "severity": "critical",
                "value": water_trend_slope_cm_per_year,
            })
        elif water_trend_slope_cm_per_year <= wt.get("warning", -0.5):
            alerts.append({
                "metric": "water_table_decline_cm_per_year",
                "severity": "warning",
                "value": water_trend_slope_cm_per_year,
            })

    ndvi_cfg = cfg.get("ndvi_mean", {})
    if ndvi_mean is not None:
        if ndvi_mean <= ndvi_cfg.get("critical_low", 0.15):
            alerts.append({"metric": "ndvi_mean", "severity": "critical", "value": ndvi_mean})
        elif ndvi_mean <= ndvi_cfg.get("warning_low", 0.22) or ndvi_mean >= ndvi_cfg.get("warning_high", 0.85):
            alerts.append({"metric": "ndvi_mean", "severity": "warning", "value": ndvi_mean})

    severity = "normal"
    if any(a["severity"] == "critical" for a in alerts):
        severity = "critical"
    elif alerts:
        severity = "warning"

    return _wrap_sovereign_payload({
        "ok": True,
        "severity": severity,
        "alerts": alerts,
        "resonance_alert_hz": 442 if severity in {"warning", "critical"} else 432,
        "thresholds": cfg,
    }, objective="gee anomaly thresholds", channel="gee-engine")


def calculate_grace_correlation_proxy(*, water_trend_slope_cm_per_year: float | None) -> float | None:
    """
    Build a bounded proxy in [0, 0.99] from GRACE slope magnitude when true
    correlation is unavailable in the current data lane.
    """
    if water_trend_slope_cm_per_year is None:
        return None
    magnitude = abs(float(water_trend_slope_cm_per_year))
    return round(min(0.99, magnitude / 2.0), 4)


def trigger_rfq_on_melt(
    *,
    district_key: str,
    grace_correlation: float | None = None,
    water_trend_slope_cm_per_year: float | None = None,
    dry_period: bool = False,
    policy: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    cfg = policy or RFQ_POLICY_DEFAULT
    target_district = str(cfg.get("target_district_key") or "soan_valley")
    threshold = float(cfg.get("moisture_correlation_trigger", 0.85))

    should_trigger = (
        district_key == target_district
        and grace_correlation is not None
        and grace_correlation >= threshold
    )

    active_ratio = cfg.get("high_humidity_silk_to_zinc_ratio", "66:34")
    if dry_period:
        active_ratio = cfg.get("dry_period_silk_to_zinc_ratio", "74:26")

    profile = cfg.get("triggered_profile", "heavy_weave") if should_trigger else cfg.get("baseline_profile", "baseline")

    return _wrap_sovereign_payload({
        "ok": True,
        "district_key": district_key,
        "grace_correlation": grace_correlation,
        "water_trend_slope_cm_per_year": water_trend_slope_cm_per_year,
        "dry_period": dry_period,
        "rfq_triggered": should_trigger,
        "rfq_profile": profile,
        "recommended_silk_to_zinc_ratio": active_ratio,
        "policy": {
            "target_district_key": target_district,
            "moisture_correlation_trigger": threshold,
        },
        "rule": "if soan_valley correlation >= threshold then trigger heavy weave RFQ",
    }, objective="gee silk rfq trigger", channel="gee-engine")


def compute_water_table_trend(
    *,
    start_date: str,
    end_date: str,
    country: str = "Pakistan",
    lat: float | None = None,
    lon: float | None = None,
    buffer_m: int = 25_000,
    scale: int = 30_000,
) -> Dict[str, Any]:
    """
    Compute water storage trend using GRACE liquid water equivalent thickness.
    This is a groundwater-adjacent proxy (total terrestrial water storage anomaly),
    useful for regional water-table trend direction.
    """
    if buffer_m < 1000 or buffer_m > 300000:
        raise ValueError("invalid_buffer_m")
    if scale < 5000 or scale > 100000:
        raise ValueError("invalid_scale")

    _initialize()
    ee = _import_ee()

    geometry = None
    area_label = ""
    if lat is not None and lon is not None:
        if not (-90.0 <= lat <= 90.0):
            raise ValueError("invalid_lat")
        if not (-180.0 <= lon <= 180.0):
            raise ValueError("invalid_lon")
        geometry = ee.Geometry.Point([lon, lat]).buffer(buffer_m)
        area_label = f"point:{lat},{lon}"
    else:
        country_name = (country or "Pakistan").strip() or "Pakistan"
        fc = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017")
        country_geom = fc.filter(ee.Filter.eq("country_na", country_name)).geometry()
        geometry = country_geom
        area_label = f"country:{country_name}"

    collection = (
        ee.ImageCollection("NASA/GRACE/MASS_GRIDS/LAND")
        .filterDate(start_date, end_date)
        .filterBounds(geometry)
        .select("lwe_thickness_csr")
    )

    count = int(collection.size().getInfo() or 0)
    if count == 0:
        return _wrap_sovereign_payload({
            "ok": True,
            "area": area_label,
            "start_date": start_date,
            "end_date": end_date,
            "sample_count": 0,
            "message": "no_grace_samples_for_filters",
        }, objective="gee water table trend", channel="gee-engine")

    def _sample_to_feature(img):
        stat = img.reduceRegion(
            reducer=ee.Reducer.mean(),
            geometry=geometry,
            scale=scale,
            bestEffort=True,
            maxPixels=1_000_000_000,
        )
        return ee.Feature(None, {
            "time_start": img.get("system:time_start"),
            "lwe": stat.get("lwe_thickness_csr"),
        })

    features = collection.map(_sample_to_feature).filter(ee.Filter.notNull(["lwe"]))
    rows = features.getInfo().get("features", [])

    if not rows:
        return _wrap_sovereign_payload({
            "ok": True,
            "area": area_label,
            "start_date": start_date,
            "end_date": end_date,
            "sample_count": 0,
            "message": "no_valid_grace_samples",
        }, objective="gee water table trend", channel="gee-engine")

    times = []
    values = []
    samples = []

    for row in rows:
        props = row.get("properties", {})
        ts = props.get("time_start")
        val = props.get("lwe")
        if ts is None or val is None:
            continue
        t = datetime.fromtimestamp(float(ts) / 1000, tz=timezone.utc)
        times.append(t)
        values.append(float(val))
        samples.append({"date": t.strftime("%Y-%m-%d"), "lwe_cm": float(val)})

    if len(values) < 2:
        return _wrap_sovereign_payload({
            "ok": True,
            "area": area_label,
            "start_date": start_date,
            "end_date": end_date,
            "sample_count": len(values),
            "message": "insufficient_samples_for_trend",
            "samples": samples,
        }, objective="gee water table trend", channel="gee-engine")

    x_years = np.array([(t - times[0]).total_seconds() / (365.25 * 24 * 3600) for t in times], dtype=float)
    y = np.array(values, dtype=float)
    slope, intercept = np.polyfit(x_years, y, 1)

    if slope > 0.05:
        trend_direction = "rising"
    elif slope < -0.05:
        trend_direction = "declining"
    else:
        trend_direction = "stable"

    return _wrap_sovereign_payload({
        "ok": True,
        "area": area_label,
        "start_date": start_date,
        "end_date": end_date,
        "sample_count": len(values),
        "dataset": "NASA/GRACE/MASS_GRIDS/LAND",
        "metric": "lwe_thickness_csr_cm",
        "trend_slope_cm_per_year": float(slope),
        "trend_intercept_cm": float(intercept),
        "trend_direction": trend_direction,
        "samples": samples,
    }, objective="gee water table trend", channel="gee-engine")


def run_gee_exploration_orchestration(
    *,
    start_date: str,
    end_date: str,
    district_keys: list[str] | None = None,
    include_ndvi: bool = True,
    include_water_trend: bool = True,
) -> Dict[str, Any]:
    presets = DISTRICT_PRESETS_PAKISTAN
    selected_keys = district_keys or list(presets.keys())
    selected = {k: presets[k] for k in selected_keys if k in presets}

    if not selected:
        return _wrap_sovereign_payload({
            "ok": False,
            "error": "no_valid_district_keys",
            "available_keys": list(presets.keys()),
        }, objective="gee orchestration invalid district keys", channel="gee-engine")

    def _explore_one(item: tuple[str, Dict[str, Any]]) -> Dict[str, Any]:
        key, preset = item
        lat = float(preset["center"]["lat"])
        lon = float(preset["center"]["lon"])
        buffer_m = int(preset.get("buffer_m", 30000))

        result: Dict[str, Any] = {
            "district_key": key,
            "label": preset.get("label", key),
            "country": preset.get("country", "Pakistan"),
            "center": {"lat": lat, "lon": lon},
        }

        if include_ndvi:
            try:
                result["ndvi"] = compute_ndvi_snapshot(
                    lat=lat,
                    lon=lon,
                    start_date=start_date,
                    end_date=end_date,
                    buffer_m=buffer_m,
                    max_cloud_pct=20.0,
                    scale=10,
                )
            except Exception as exc:  # noqa: BLE001
                result["ndvi"] = {"ok": False, "error": str(exc)}

        if include_water_trend:
            try:
                result["water_trend"] = compute_water_table_trend(
                    start_date=start_date,
                    end_date=end_date,
                    lat=lat,
                    lon=lon,
                    buffer_m=max(buffer_m, 25000),
                    scale=30000,
                )
            except Exception as exc:  # noqa: BLE001
                result["water_trend"] = {"ok": False, "error": str(exc)}

        slope = None
        ndvi_mean = None
        if isinstance(result.get("water_trend"), dict):
            slope = result["water_trend"].get("trend_slope_cm_per_year")
        if isinstance(result.get("ndvi"), dict):
            ndvi_mean = result["ndvi"].get("ndvi_mean")

        result["anomaly"] = evaluate_anomaly_thresholds(
            water_trend_slope_cm_per_year=slope,
            ndvi_mean=ndvi_mean,
        )
        grace_corr_proxy = calculate_grace_correlation_proxy(
            water_trend_slope_cm_per_year=slope,
        )
        result["rfq_signal"] = trigger_rfq_on_melt(
            district_key=key,
            grace_correlation=grace_corr_proxy,
            water_trend_slope_cm_per_year=slope,
            dry_period=bool(slope is not None and slope > 0.05),
        )
        return result

    district_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, len(selected))) as pool:
        futures = [pool.submit(_explore_one, item) for item in selected.items()]
        for f in futures:
            district_results.append(f.result())

    severe = [r for r in district_results if r.get("anomaly", {}).get("severity") in {"warning", "critical"}]
    rfq_triggered = [r for r in district_results if r.get("rfq_signal", {}).get("rfq_triggered")]

    return _wrap_sovereign_payload({
        "ok": True,
        "start_date": start_date,
        "end_date": end_date,
        "district_count": len(district_results),
        "district_results": district_results,
        "warning_or_critical_count": len(severe),
        "rfq_trigger_count": len(rfq_triggered),
        "catalog": GEE_DATASET_CATALOG,
    }, objective="gee orchestration engine exploration", channel="gee-engine")
