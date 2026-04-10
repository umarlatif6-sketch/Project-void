"""
THE 99 NAMES — AL-JABR 286 | Route
PROJECT VOID | Umar Latif
"""

from flask import Blueprint, render_template, jsonify, request
from void_engine.names_286 import (
    all_profiles, full_profile, dominant_name_from_frequency,
    name_sovereign_score, LAMBDA, BASE_FREQ, N_NAMES,
    LATIF_INDEX, LATIF_FREQ, LATIF_MODE, LATIF_CODON,
    FORMATION_RATIO, SCALING_RATIO
)

names_286_bp = Blueprint('names_286', __name__)


@names_286_bp.route('/names-286')
def names_286_page():
    profiles = all_profiles()
    stats = {
        "lambda": LAMBDA,
        "base_freq": BASE_FREQ,
        "n_names": N_NAMES,
        "formation_ratio": round(FORMATION_RATIO, 4),
        "scaling_ratio": round(SCALING_RATIO, 4),
        "latif_index": LATIF_INDEX,
        "latif_freq": LATIF_FREQ,
        "latif_mode": LATIF_MODE,
        "latif_codon": LATIF_CODON,
    }
    return render_template('names_286.html', profiles=profiles, stats=stats)


@names_286_bp.route('/api/names-286/all')
def api_all_names():
    return jsonify(all_profiles())


@names_286_bp.route('/api/names-286/<int:index>')
def api_name_by_index(index):
    if not 1 <= index <= N_NAMES:
        return jsonify({"error": "Index must be 1–99"}), 400
    return jsonify(full_profile(index))


@names_286_bp.route('/api/names-286/from-frequency')
def api_from_frequency():
    freq = request.args.get('hz', type=float)
    if freq is None:
        return jsonify({"error": "Provide ?hz=<frequency>"}), 400
    profile = dominant_name_from_frequency(freq)
    return jsonify(profile)


@names_286_bp.route('/api/names-286/sovereign-score')
def api_sovereign_score():
    raw = request.args.get('raw', type=float)
    idx = request.args.get('index', type=int, default=1)
    if raw is None:
        return jsonify({"error": "Provide ?raw=<0-100>"}), 400
    score = name_sovereign_score(raw, idx)
    return jsonify({"raw": raw, "sovereign_score": score, "lambda": LAMBDA})
