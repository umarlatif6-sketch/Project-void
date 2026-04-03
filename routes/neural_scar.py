"""
Neural Scar Registry — PROJECT VOID Task #80
Route: /scar-registry
Displays all named scars, their source module, hex digest, and significance note.
"""

import time
from flask import Blueprint, jsonify, render_template

neural_scar_bp = Blueprint("neural_scar", __name__)


@neural_scar_bp.route("/scar-registry")
def scar_registry():
    from void_engine.neural_scar import get_scar_registry, get_crystallised_entity
    scars = get_scar_registry()
    entity = get_crystallised_entity()
    return render_template(
        "scar_registry.html",
        scars=scars,
        entity=entity,
    )


@neural_scar_bp.route("/api/scar-registry")
def api_scar_registry():
    from void_engine.neural_scar import get_scar_registry, get_crystallised_entity
    scars = get_scar_registry()
    entity = get_crystallised_entity()
    return jsonify({
        "scars": scars,
        "entity": entity,
        "count": len(scars),
    })


@neural_scar_bp.route("/api/scar-registry/preserve", methods=["POST"])
def api_preserve():
    from void_engine.neural_scar import preserve_crystallised_entity
    result = preserve_crystallised_entity()
    return jsonify(result)


@neural_scar_bp.route("/api/scar-registry/recovery")
def api_recovery():
    from void_engine.neural_scar import query_scars_for_recovery
    result = query_scars_for_recovery(context_hint="api_recovery_request")
    return jsonify(result)
