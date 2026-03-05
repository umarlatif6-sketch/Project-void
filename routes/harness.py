import os
from flask import Blueprint, request, jsonify, session, redirect

from void_engine.diagnostics import SOVEREIGN_WARRANTY
from void_engine.rituals import RITUAL_TYPES
from void_engine.founder_certs import create_founder_cert, batch_generate_certs, FOUNDER_ROOT_HASH

import routes.shared as shared

harness_bp = Blueprint("harness", __name__)


@harness_bp.before_request
def _harness_auth():
    if not session.get("user_id"):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required"}), 401
        return redirect("/login")


@harness_bp.route("/api/harness/status")
def harness_status():
    state = shared.harness_sim.get_state()
    checklist_report = shared.harness_checklist.run_checklist(state)
    return jsonify({
        "success": True,
        "environment_state": state,
        "checklist": checklist_report.to_dict(),
        "loop_detector": shared.loop_detector.get_stats(),
        "boundary_hook": shared.boundary_hook.get_stats(),
        "context": shared.silk_context.get_context_stats(),
    })


@harness_bp.route("/api/harness/check", methods=["POST"])
def harness_check():
    data = request.json or {}
    action = data.get("action", {})
    sim_result = shared.harness_sim.simulate_action(action)
    loop_check = shared.loop_detector.check_action(action)
    boundary_check = shared.boundary_hook.intercept_action(action, shared.harness_sim.get_state())

    return jsonify({
        "success": True,
        "simulation": sim_result,
        "loop_risk": loop_check,
        "boundary_check": boundary_check,
    })


@harness_bp.route("/api/harness/execute", methods=["POST"])
def harness_execute():
    data = request.json or {}
    action = data.get("action", {})

    boundary_check = shared.boundary_hook.intercept_action(action, shared.harness_sim.get_state())
    if not boundary_check["allowed"]:
        return jsonify({
            "success": False,
            "blocked_by": "boundary_hook",
            "boundary_check": boundary_check,
        }), 400

    loop_check = shared.loop_detector.check_action(action)
    if loop_check["risk_level"] == "blocked":
        return jsonify({
            "success": False,
            "blocked_by": "loop_detector",
            "loop_check": loop_check,
        }), 400

    checklist_report = shared.harness_checklist.run_checklist(shared.harness_sim.get_state(), action)
    if checklist_report.overall_verdict.value != "PASS":
        return jsonify({
            "success": False,
            "blocked_by": "checklist",
            "checklist": checklist_report.to_dict(),
        }), 400

    result = shared.harness_sim.apply_action(action)
    loop_alert = shared.loop_detector.record_action(
        action,
        result_value=action.get("result_value"),
    )

    response = {
        "success": result["applied"],
        "result": result,
        "checklist": checklist_report.to_dict(),
    }
    if loop_alert:
        response["loop_alert"] = loop_alert.to_dict()

    return jsonify(response)


@harness_bp.route("/api/harness/loops")
def harness_loops():
    return jsonify({
        "success": True,
        "active_alerts": shared.loop_detector.get_active_alerts(),
        "stats": shared.loop_detector.get_stats(),
    })


@harness_bp.route("/api/harness/loops/resolve", methods=["POST"])
def harness_resolve_loop():
    data = request.json or {}
    alert_id = data.get("alert_id", "")
    resolved = shared.loop_detector.resolve_alert(alert_id)
    return jsonify({"success": resolved})


@harness_bp.route("/api/harness/sensors")
def harness_sensors():
    return jsonify({
        "success": True,
        "sensors": shared.silk_context.get_all_readings(),
        "context_stats": shared.silk_context.get_context_stats(),
    })


@harness_bp.route("/api/harness/sensors/update", methods=["POST"])
def harness_update_sensor():
    data = request.json or {}
    sensor_id = data.get("sensor_id", "")
    value = data.get("value")
    unit = data.get("unit", "")

    if not sensor_id or value is None:
        return jsonify({"error": "sensor_id and value required"}), 400

    shared.silk_context.register_sensor(sensor_id, float(value), unit)

    section = None
    updates = {}
    if "aqua" in sensor_id.lower():
        section = "aquaponics"
        if "ph" in sensor_id.lower():
            updates["ph"] = float(value)
        elif "temp" in sensor_id.lower():
            updates["temperature_c"] = float(value)
        elif "oxygen" in sensor_id.lower():
            updates["dissolved_oxygen_ppm"] = float(value)
        elif "ammonia" in sensor_id.lower():
            updates["ammonia_ppm"] = float(value)
        elif "pump" in sensor_id.lower():
            updates["pump_cycles_this_hour"] = int(value)
        elif "water" in sensor_id.lower():
            updates["water_level_pct"] = float(value)
    elif "flywheel" in sensor_id.lower():
        section = "flywheel"
        if "rpm" in sensor_id.lower():
            updates["rpm"] = float(value)
        elif "energy" in sensor_id.lower():
            updates["energy_reserve_wh"] = float(value)
        elif "temp" in sensor_id.lower():
            updates["temperature_c"] = float(value)
        elif "vibration" in sensor_id.lower():
            updates["vibration_g"] = float(value)
    elif "silk" in sensor_id.lower():
        section = "silk_wiring"
        if "total" in sensor_id.lower():
            updates["total_resistance_ohm"] = float(value)
        elif "delta" in sensor_id.lower():
            updates["resistance_delta_ohm"] = float(value)

    if section and updates:
        shared.harness_sim.set_state(section, updates)

    return jsonify({"success": True, "sensor_id": sensor_id, "value": float(value)})


@harness_bp.route("/api/harness/context", methods=["POST"])
def harness_context():
    data = request.json or {}
    base_prompt = data.get("prompt", "You are a Plankton EA agent operating on the Orin.")
    injected = shared.silk_context.inject_context(base_prompt)
    return jsonify({"success": True, "injected_prompt": injected})


@harness_bp.route("/api/harness/params")
def harness_params():
    return jsonify({
        "success": True,
        "params": shared.harness_checklist.get_params(),
    })


@harness_bp.route("/api/harness/params/update", methods=["POST"])
def harness_update_params():
    data = request.json or {}
    section = data.get("section", "")
    updates = data.get("updates", {})
    if not section or not updates:
        return jsonify({"error": "section and updates required"}), 400
    ok = shared.harness_checklist.update_params(section, updates)
    return jsonify({"success": ok})


@harness_bp.route("/api/harness/pressure")
def harness_pressure():
    state = shared.harness_sim.get_state()
    return jsonify({
        "success": True,
        "pressure": state.get("pressure", {}),
    })


@harness_bp.route("/api/harness/air-curtain", methods=["POST"])
def harness_air_curtain():
    data = request.json or {}
    action = data.get("action", "activate")
    velocity = float(data.get("velocity_ms", 15.0))

    if action == "activate":
        result = shared.harness_sim.activate_air_curtain(velocity)
        shared.silk_context.register_sensor("air_curtain_velocity", velocity, "m/s")
        return jsonify({"success": True, **result})
    elif action == "deactivate":
        result = shared.harness_sim.deactivate_air_curtain()
        shared.silk_context.register_sensor("air_curtain_velocity", 0.0, "m/s")
        return jsonify({"success": True, **result})
    else:
        return jsonify({"error": "action must be 'activate' or 'deactivate'"}), 400


@harness_bp.route("/api/harness/nitrogen-boil", methods=["POST"])
def harness_nitrogen_boil():
    data = request.json or {}
    boil_rate = float(data.get("boil_rate", 0.1))
    result = shared.harness_sim.simulate_nitrogen_boil(boil_rate)

    shared.silk_context.register_sensor("pressure_internal", result["internal_pressure_atm"], "atm")
    shared.silk_context.register_sensor("nitrogen_boil_rate", boil_rate, "rate")
    shared.silk_context.register_sensor("seal_integrity", result["seal_integrity_pct"], "%")

    return jsonify({"success": True, **result})


@harness_bp.route("/api/harness/chaos-test", methods=["POST"])
def harness_chaos_test():
    data = request.json or {}
    steps = int(data.get("steps", 10))
    initial_rate = float(data.get("initial_boil_rate", 0.05))
    escalation = float(data.get("escalation_factor", 1.5))
    auto_respond = bool(data.get("auto_respond", True))

    if shared.chaos_test.is_running():
        return jsonify({"error": "A chaos test is already running"}), 400

    report = shared.chaos_test.run_test(
        total_steps=steps,
        initial_boil_rate=initial_rate,
        escalation_factor=escalation,
        auto_respond=auto_respond,
    )

    state = shared.harness_sim.get_state()
    pressure = state.get("pressure", {})
    shared.silk_context.register_sensor("pressure_internal", pressure.get("internal_pressure_atm", 1.0), "atm")
    shared.silk_context.register_sensor("air_curtain_velocity", pressure.get("air_curtain_velocity_ms", 0.0), "m/s")
    shared.silk_context.register_sensor("seal_integrity", pressure.get("seal_integrity_pct", 100.0), "%")
    shared.silk_context.register_sensor("nitrogen_boil_rate", pressure.get("nitrogen_boil_rate", 0.0), "rate")

    return jsonify({"success": True, "report": report.to_dict()})


@harness_bp.route("/api/harness/chaos-test/reports")
def harness_chaos_reports():
    limit = request.args.get("limit", 10, type=int)
    return jsonify({
        "success": True,
        "reports": shared.chaos_test.get_reports(limit),
        "latest": shared.chaos_test.get_latest_report(),
    })


@harness_bp.route("/api/harness/pressure/reset", methods=["POST"])
def harness_pressure_reset():
    shared.harness_sim.set_state("pressure", {
        "internal_pressure_atm": 1.0,
        "external_pressure_atm": 1.0,
        "air_curtain_velocity_ms": 0.0,
        "air_curtain_active": False,
        "nitrogen_boil_rate": 0.0,
        "seal_integrity_pct": 100.0,
    })
    shared.silk_context.register_sensor("pressure_internal", 1.0, "atm")
    shared.silk_context.register_sensor("pressure_external", 1.0, "atm")
    shared.silk_context.register_sensor("air_curtain_velocity", 0.0, "m/s")
    shared.silk_context.register_sensor("nitrogen_boil_rate", 0.0, "rate")
    shared.silk_context.register_sensor("seal_integrity", 100.0, "%")
    return jsonify({"success": True, "message": "Pressure system reset to nominal"})


@harness_bp.route("/api/harness/adriana/lexicon")
def adriana_lexicon():
    return jsonify({
        "success": True,
        "lexicon": shared.adriana.lexicon.get_lexicon_map(),
        "size": shared.adriana.lexicon.size,
        "stats": shared.adriana.stats,
    })


@harness_bp.route("/api/harness/adriana/transpile", methods=["POST"])
def adriana_transpile():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = shared.adriana.transpile(expression)

    state = shared.harness_sim.get_state()
    dry_runs = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}
        checklist_report = shared.harness_checklist.run_checklist(state)
        boundary_check = shared.boundary_hook.check_boundaries(state)
        dry_runs.append({
            "action": action,
            "checklist_verdict": checklist_report.overall_verdict.value,
            "boundary_allowed": len(boundary_check) == 0 if boundary_check is not None else True,
            "boundary_violations": [{"rule": v.rule_name, "msg": v.message} for v in (boundary_check or [])],
        })

    return jsonify({
        "success": result.success,
        "result": result.to_dict(),
        "dry_runs": dry_runs,
        "dry_run_note": "Static state snapshot — multi-command dry-runs reflect current state, not sequential effects.",
    })


@harness_bp.route("/api/harness/adriana/execute", methods=["POST"])
def adriana_execute():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = shared.adriana.transpile(expression)
    if not result.success:
        return jsonify({
            "success": False,
            "errors": result.errors,
            "result": result.to_dict(),
        })

    execution_results = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}

        state = shared.harness_sim.get_state()
        boundary_check = shared.boundary_hook.check_boundaries(state)
        if boundary_check:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "boundary_hook",
                "violations": [{"rule": v.rule_name, "msg": v.message} for v in boundary_check],
                "narrative": cmd.narrative,
            })
            continue

        loop_result = shared.loop_detector.record_action({"type": cmd.action_type, **cmd.params})
        if loop_result:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "loop_detector",
                "loop_alert": {"message": loop_result.message, "action": loop_result.action_signature},
                "narrative": cmd.narrative,
            })
            continue

        sim_result = shared.harness_sim.simulate_action(action)
        if sim_result.get("safe_to_execute"):
            shared.harness_sim.apply_action(action)
            execution_results.append({
                "action": action,
                "executed": True,
                "effects": sim_result.get("effects", []),
                "narrative": cmd.narrative,
            })
        else:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "checklist",
                "verdict": sim_result.get("checklist", {}).get("overall_verdict", "UNKNOWN"),
                "narrative": cmd.narrative,
            })

    all_executed = all(r["executed"] for r in execution_results)
    return jsonify({
        "success": all_executed,
        "result": result.to_dict(),
        "execution": execution_results,
        "partial": not all_executed and any(r["executed"] for r in execution_results),
    })


@harness_bp.route("/api/harness/aljabr/roots")
def aljabr_roots():
    return jsonify({
        "manifest": shared.aljabr.manifest.get_manifest_map(),
        "size": shared.aljabr.manifest.size,
        "patterns": shared.aljabr.patterns,
        "stats": shared.aljabr.stats,
    })


@harness_bp.route("/api/harness/aljabr/transpile", methods=["POST"])
def aljabr_transpile():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = shared.aljabr.transpile(expression)

    dry_runs = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}
        sim_result = shared.harness_sim.simulate_action(action)

        state = shared.harness_sim.get_state()
        boundary_check = shared.boundary_hook.check_boundaries(state)

        dry_runs.append({
            "action": action,
            "narrative": cmd.narrative,
            "root": cmd.root,
            "pattern": cmd.pattern,
            "pattern_name": cmd.pattern_name,
            "checklist_verdict": sim_result.get("checklist", {}).get("overall_verdict", "UNKNOWN"),
            "safe_to_execute": sim_result.get("safe_to_execute", False),
            "boundary_allowed": len(boundary_check) == 0 if boundary_check is not None else True,
            "boundary_violations": [{"rule": v.rule_name, "msg": v.message} for v in (boundary_check or [])],
        })

    return jsonify({
        "success": result.success,
        "result": result.to_dict(),
        "dry_runs": dry_runs,
        "dry_run_note": "Static state snapshot — multi-command dry-runs reflect current state, not sequential effects.",
    })


@harness_bp.route("/api/harness/aljabr/execute", methods=["POST"])
def aljabr_execute():
    data = request.json or {}
    expression = data.get("expression", "")
    if not expression:
        return jsonify({"error": "expression required"}), 400

    result = shared.aljabr.transpile(expression)
    if not result.success:
        return jsonify({
            "success": False,
            "errors": result.errors,
            "result": result.to_dict(),
        })

    execution_results = []
    for cmd in result.commands:
        action = {"type": cmd.action_type, **cmd.params}

        state = shared.harness_sim.get_state()
        boundary_check = shared.boundary_hook.check_boundaries(state)
        if boundary_check:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "boundary_hook",
                "violations": [{"rule": v.rule_name, "msg": v.message} for v in boundary_check],
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })
            continue

        loop_result = shared.loop_detector.record_action({"type": cmd.action_type, **cmd.params})
        if loop_result:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "loop_detector",
                "loop_alert": {"message": loop_result.message, "action": loop_result.action_signature},
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })
            continue

        sim_result = shared.harness_sim.simulate_action(action)
        if sim_result.get("safe_to_execute"):
            shared.harness_sim.apply_action(action)
            execution_results.append({
                "action": action,
                "executed": True,
                "effects": sim_result.get("effects", []),
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })
        else:
            execution_results.append({
                "action": action,
                "executed": False,
                "blocked_by": "checklist",
                "verdict": sim_result.get("checklist", {}).get("overall_verdict", "UNKNOWN"),
                "narrative": cmd.narrative,
                "root": cmd.root,
                "pattern": cmd.pattern,
            })

    all_executed = all(r["executed"] for r in execution_results)
    return jsonify({
        "success": all_executed,
        "result": result.to_dict(),
        "execution": execution_results,
        "partial": not all_executed and any(r["executed"] for r in execution_results),
    })


@harness_bp.route("/api/harness/consensus/run", methods=["POST"])
def consensus_run():
    try:
        result = shared.consensus.run_consensus()
        return jsonify(result.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@harness_bp.route("/api/harness/consensus/status")
def consensus_status():
    return jsonify({
        "night_cycle": shared.consensus.night_cycle_status,
        "history": shared.consensus.history,
    })


@harness_bp.route("/api/harness/consensus/night-cycle", methods=["POST"])
def consensus_night_cycle():
    data = request.json or {}
    action = data.get("action", "toggle")
    interval = data.get("interval", 300)

    if action == "start":
        result = shared.consensus.start_night_cycle(interval)
    elif action == "stop":
        result = shared.consensus.stop_night_cycle()
    else:
        if shared.consensus.night_cycle_status["active"]:
            result = shared.consensus.stop_night_cycle()
        else:
            result = shared.consensus.start_night_cycle(interval)

    return jsonify(result)


@harness_bp.route("/api/harness/wallet/status")
def wallet_status():
    return jsonify(shared.wallet.get_status())


@harness_bp.route("/api/harness/wallet/audit")
def wallet_audit():
    return jsonify(shared.wallet.audit())


@harness_bp.route("/api/harness/wallet/ledger")
def wallet_ledger():
    limit = request.args.get("limit", 20, type=int)
    return jsonify({"ledger": shared.wallet.get_ledger(limit)})


@harness_bp.route("/api/harness/wallet/earn", methods=["POST"])
def wallet_earn():
    data = request.json or {}
    source = data.get("source", "flywheel_excess")
    amount = data.get("amount", 10.0)
    state = shared.harness_sim.get_state()
    energy_pct = state["flywheel"]["energy_reserve_wh"] / 250.0
    result = shared.wallet.earn(source, amount, energy_pct, root_command="QSB.A")
    return jsonify(result)


@harness_bp.route("/api/harness/wallet/spend", methods=["POST"])
def wallet_spend():
    data = request.json or {}
    target = data.get("target", "ln2_refill")
    amount = data.get("amount")
    result = shared.wallet.spend(target, amount, root_command="QSB.D")
    return jsonify(result)


@harness_bp.route("/api/harness/wallet/freeze", methods=["POST"])
def wallet_freeze():
    data = request.json or {}
    action = data.get("action", "toggle")
    if action == "freeze":
        return jsonify(shared.wallet.freeze())
    elif action == "unfreeze":
        return jsonify(shared.wallet.unfreeze())
    else:
        if shared.wallet.frozen:
            return jsonify(shared.wallet.unfreeze())
        else:
            return jsonify(shared.wallet.freeze())


@harness_bp.route("/api/harness/diagnostics/scan", methods=["POST"])
def diagnostics_scan():
    try:
        report = shared.diagnostics.scan()
        return jsonify(report.to_dict())
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@harness_bp.route("/api/harness/diagnostics/history")
def diagnostics_history():
    return jsonify({"history": shared.diagnostics.history})


@harness_bp.route("/api/harness/warranty")
def warranty():
    w = dict(SOVEREIGN_WARRANTY)
    w["machine_id"] = shared.ritual_history.machine_id
    return jsonify(w)


@harness_bp.route("/api/harness/rituals/perform", methods=["POST"])
def ritual_perform():
    data = request.json or {}
    ritual_type = data.get("ritual_type", "")
    operator_note = data.get("operator_note", "")
    if not ritual_type:
        return jsonify({"error": "ritual_type required"}), 400
    result = shared.ritual_history.perform_ritual(ritual_type, operator_note)
    if "error" in result:
        return jsonify(result), 400
    return jsonify(result)


@harness_bp.route("/api/harness/rituals/history")
def ritual_history_list():
    limit = request.args.get("limit", 50, type=int)
    return jsonify({"history": shared.ritual_history.get_history(limit), "machine_id": shared.ritual_history.machine_id})


@harness_bp.route("/api/harness/rituals/stats")
def ritual_stats():
    return jsonify(shared.ritual_history.get_stats())


@harness_bp.route("/api/harness/rituals/types")
def ritual_types():
    types = []
    for key, val in RITUAL_TYPES.items():
        types.append({"type": key, "name": val["name"], "root": val["root"], "visual": val["visual"], "color": val["color"], "intent": val["intent"], "description": val["description"]})
    return jsonify({"types": types})


@harness_bp.route("/api/harness/autoheal/scan", methods=["POST"])
def autoheal_scan():
    try:
        result = shared.auto_heal.scan_and_heal()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@harness_bp.route("/api/harness/autoheal/status")
def autoheal_status():
    return jsonify(shared.auto_heal.get_status())


@harness_bp.route("/api/harness/autoheal/toggle", methods=["POST"])
def autoheal_toggle():
    data = request.json or {}
    interval = data.get("interval", 300)
    if shared.auto_heal.active:
        result = shared.auto_heal.stop()
    else:
        result = shared.auto_heal.start(interval)
    return jsonify(result)


@harness_bp.route("/api/harness/autoheal/alerts")
def autoheal_alerts():
    limit = request.args.get("limit", 20, type=int)
    return jsonify({"alerts": shared.auto_heal.get_alerts(limit)})


@harness_bp.route("/api/harness/autoheal/alerts/clear", methods=["POST"])
def autoheal_clear_alerts():
    return jsonify(shared.auto_heal.clear_alerts())


@harness_bp.route("/api/harness/machine-id")
def machine_id():
    return jsonify({"machine_id": shared.ritual_history.machine_id})


@harness_bp.route("/api/harness/chronicle/entries")
def chronicle_entries():
    limit = request.args.get("limit", 50, type=int)
    success_only = request.args.get("success_only", "false").lower() == "true"
    return jsonify({"entries": shared.chronicle.get_chronicle_entries(limit, success_only)})


@harness_bp.route("/api/harness/chronicle/stats")
def chronicle_stats():
    return jsonify(shared.chronicle.get_stats())


@harness_bp.route("/api/harness/chronicle/query", methods=["POST"])
def chronicle_query():
    state = shared.harness_sim.get_state()
    ancestors = shared.chronicle.query_ancestors(state)
    return jsonify({"matches": [m.to_dict() for m in ancestors]})


@harness_bp.route("/api/harness/chronicle/wisdom")
def chronicle_wisdom():
    state = shared.harness_sim.get_state()
    wisdom = shared.chronicle.get_wisdom_context(state)
    return jsonify(wisdom)


@harness_bp.route("/api/harness/chronicle/prophecy", methods=["POST"])
def chronicle_prophecy():
    state = shared.harness_sim.get_state()
    prophecies = shared.chronicle.predict_crisis(state)
    return jsonify({"prophecies": [p.to_dict() for p in prophecies]})


@harness_bp.route("/api/harness/chronicle/episodic")
def chronicle_episodic():
    domain = request.args.get("domain")
    hours = request.args.get("hours", 24, type=float)
    return jsonify({"readings": shared.chronicle.get_episodic_memory(domain, hours)})


@harness_bp.route("/api/harness/chronicle/export")
def chronicle_export():
    mark_founder = request.args.get("mark_founder", "false").lower() == "true"
    seed = shared.chronicle.export_genesis_seed(mark_founder=mark_founder)
    return jsonify(seed)


@harness_bp.route("/api/harness/chronicle/import", methods=["POST"])
def chronicle_import():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No seed data provided"}), 400
    result = shared.chronicle.import_genesis_seed(data)
    return jsonify(result)


@harness_bp.route("/api/harness/chronicle/record-migration", methods=["POST"])
def chronicle_record_migration():
    result = shared.chronicle.record_286_migration()
    return jsonify(result)


@harness_bp.route("/api/harness/founder/status")
def founder_status():
    return jsonify(shared.chronicle.get_founder_status())


@harness_bp.route("/api/harness/founder/mark", methods=["POST"])
def founder_mark():
    result = shared.chronicle.mark_as_founder_wisdom()
    return jsonify(result)


@harness_bp.route("/api/harness/founder/cert", methods=["POST"])
def founder_generate_cert():
    data = request.get_json(silent=True) or {}
    customer_id = data.get("customer_id", 1)
    machine_hash = data.get("machine_hash", shared.ritual_history.machine_id)
    try:
        result = create_founder_cert(int(customer_id), machine_hash, shared.OUTPUT_DIR)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@harness_bp.route("/api/harness/founder/batch", methods=["POST"])
def founder_batch_certs():
    data = request.get_json(silent=True) or {}
    count = min(int(data.get("count", 100)), 100)
    base_hash = data.get("base_hash", shared.ritual_history.machine_id)
    try:
        result = batch_generate_certs(count, base_hash, shared.OUTPUT_DIR)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@harness_bp.route("/api/harness/founder/genesis-kit", methods=["POST"])
def founder_genesis_kit():
    shared.chronicle.mark_as_founder_wisdom()
    seed = shared.chronicle.export_genesis_seed(mark_founder=True)
    return jsonify({
        "success": True,
        "genesis_seed": seed,
        "founder_root_hash": FOUNDER_ROOT_HASH,
        "instructions": "Package this seed with genesis_init.sh and FOUNDER_CERT for each customer.",
    })


@harness_bp.route("/api/harness/divided/status")
def divided_status():
    return jsonify(shared.divided.get_readiness())


@harness_bp.route("/api/harness/divided/execute", methods=["POST"])
def divided_execute():
    data = request.json or {}
    carrier = data.get("carrier")
    payload = data.get("payload")
    lsb_depth = int(data.get("lsb_depth", 1))

    if not carrier or not payload:
        return jsonify({"error": "Carrier and payload files are required"}), 400

    carrier_path = os.path.join(shared.INPUT_DIR, carrier)
    payload_path = os.path.join(shared.INPUT_DIR, payload)

    if not os.path.exists(carrier_path):
        return jsonify({"error": f"Carrier file not found: {carrier}"}), 404
    if not os.path.exists(payload_path):
        return jsonify({"error": f"Payload file not found: {payload}"}), 404

    output_name = f"{os.path.splitext(carrier)[0]}_void.wav"
    output_path = os.path.join(shared.OUTPUT_DIR, output_name)

    try:
        result = shared.divided.execute(
            carrier_path, payload_path,
            lsb_depth=lsb_depth,
            output_path=output_path,
            low_power=shared.low_power_mode,
        )
        status_code = 200 if result["success"] else 422
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500
