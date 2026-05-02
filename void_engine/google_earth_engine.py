import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import numpy as np

logger = logging.getLogger(__name__)

_init_lock = threading.Lock()
_initialized = False
_init_error: str | None = None


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
        return {
            "ok": True,
            "lat": lat,
            "lon": lon,
            "start_date": start_date,
            "end_date": end_date,
            "image_count": 0,
            "message": "no_imagery_for_filters",
        }

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

    return {
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
    }


def default_date_window(days: int = 45) -> tuple[str, str]:
    now = datetime.now(timezone.utc).date()
    start = now - timedelta(days=days)
    return start.isoformat(), now.isoformat()


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
        return {
            "ok": True,
            "area": area_label,
            "start_date": start_date,
            "end_date": end_date,
            "sample_count": 0,
            "message": "no_grace_samples_for_filters",
        }

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
        return {
            "ok": True,
            "area": area_label,
            "start_date": start_date,
            "end_date": end_date,
            "sample_count": 0,
            "message": "no_valid_grace_samples",
        }

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
        return {
            "ok": True,
            "area": area_label,
            "start_date": start_date,
            "end_date": end_date,
            "sample_count": len(values),
            "message": "insufficient_samples_for_trend",
            "samples": samples,
        }

    x_years = np.array([(t - times[0]).total_seconds() / (365.25 * 24 * 3600) for t in times], dtype=float)
    y = np.array(values, dtype=float)
    slope, intercept = np.polyfit(x_years, y, 1)

    if slope > 0.05:
        trend_direction = "rising"
    elif slope < -0.05:
        trend_direction = "declining"
    else:
        trend_direction = "stable"

    return {
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
    }
