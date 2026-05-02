import logging
from flask import Blueprint, jsonify, request

from routes.auth import login_required
from void_engine.google_earth_engine import (
    compute_water_table_trend,
    compute_ndvi_snapshot,
    default_date_window,
    get_gee_status,
)

logger = logging.getLogger(__name__)
gee_bp = Blueprint("google_earth_engine", __name__)


@gee_bp.route("/api/gee/status", methods=["GET"])
def gee_status():
    return jsonify(get_gee_status())


@gee_bp.route("/api/gee/ndvi", methods=["POST"])
@login_required
def gee_ndvi():
    data = request.get_json(silent=True) or {}

    try:
        lat = float(data.get("lat"))
        lon = float(data.get("lon"))
    except Exception:  # noqa: BLE001
        return jsonify({"ok": False, "error": "lat_lon_required"}), 400

    start_date = (data.get("start_date") or "").strip()
    end_date = (data.get("end_date") or "").strip()
    if not start_date or not end_date:
        start_date, end_date = default_date_window(45)

    try:
        buffer_m = int(data.get("buffer_m", 250) or 250)
        max_cloud_pct = float(data.get("max_cloud_pct", 20.0) or 20.0)
        scale = int(data.get("scale", 10) or 10)
    except Exception:  # noqa: BLE001
        return jsonify({"ok": False, "error": "invalid_numeric_params"}), 400

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
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.error("GEE NDVI route failed: %s", exc)
        return jsonify({"ok": False, "error": "gee_execution_failed", "detail": str(exc)}), 502


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
            return jsonify({"ok": False, "error": "invalid_lat_lon"}), 400
    else:
        lat = None
        lon = None

    try:
        buffer_m = int(data.get("buffer_m", 25_000) or 25_000)
        scale = int(data.get("scale", 30_000) or 30_000)
    except Exception:  # noqa: BLE001
        return jsonify({"ok": False, "error": "invalid_numeric_params"}), 400

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
        return jsonify(result)
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except Exception as exc:  # noqa: BLE001
        logger.error("GEE water-table route failed: %s", exc)
        return jsonify({"ok": False, "error": "gee_execution_failed", "detail": str(exc)}), 502
