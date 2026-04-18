from pathlib import Path
from datetime import UTC, datetime
from threading import Lock
from time import sleep

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit, join_room, leave_room

from oryx_engine import OryxEngine
from oryx_engine.auth_store import AuthStore, FEATURE_KEYS, audit_repair_state_for_action


socketio = SocketIO(cors_allowed_origins="*", async_mode="threading")


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)
    socketio.init_app(app)

    engine = OryxEngine(Path(__file__).resolve().parent / "data")
    auth = AuthStore(Path(__file__).resolve().parent / "data" / "oryx.db")
    stream_controls: dict[str, dict[str, int | bool]] = {}
    stream_lock = Lock()

    def _base_url() -> str:
        return request.host_url.rstrip("/")

    def _require_user_id() -> int:
        token = (request.headers.get("Authorization", "").replace("Bearer", "")).strip()
        user = auth.get_user_by_token(token)
        if user is None:
            raise PermissionError("Unauthorized")
        return int(user["id"])

    def _is_world_owner(user_id: int, world_id: str) -> bool:
        owner_id = auth.owner_for_world(world_id)
        return owner_id == user_id

    def _world_role(user_id: int, world_id: str) -> str | None:
        return auth.role_for_world(user_id=user_id, world_id=world_id)

    def _has_permission(user_id: int, world_id: str, feature: str) -> bool:
        return auth.get_effective_permissions(user_id=user_id, world_id=world_id).get(feature, False)

    def _safe_world_state(world_id: str):
        try:
            return engine.load_world(world_id)
        except KeyError:
            return None

    def _emit_world_state(world_id: str) -> None:
        state = _safe_world_state(world_id)
        if state is None:
            socketio.emit("stream_error", {"error": "World not found.", "world_id": world_id}, room=f"world:{world_id}")
            return
        socketio.emit("world_state", state, room=f"world:{world_id}")

    def _log(
        world_id: str,
        action: str,
        target_type: str,
        *,
        target_id: str | None = None,
        actor_user_id: int | None = None,
        repair_state: str | None = None,
        details: dict | None = None,
    ) -> None:
        auth.log_event(
            world_id=world_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            actor_user_id=actor_user_id,
            repair_state=repair_state or audit_repair_state_for_action(action),
            details=details,
        )

    def _safe_parse_iso_datetime(value: str | None):
        if not value:
            return None
        candidate = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(candidate)
        except ValueError:
            return None

    def _world_repair_status(world_id: str, world: dict, collaborators: list[dict], recent_audit: list[dict]) -> dict:
        issues: list[dict] = []
        invites = auth.list_invites(world_id)
        now = datetime.now(UTC)
        owner_present = any(item.get("role") == "owner" for item in collaborators)
        if not owner_present:
            issues.append({
                "code": "owner_missing",
                "repair_state": "quarantined",
                "message": "World has no visible owner record.",
            })

        expired_pending_invites = [
            item for item in invites
            if not item.get("revoked_at")
            and not item.get("used_at")
            and (_safe_parse_iso_datetime(item.get("expires_at")) or now) < now
        ]
        if expired_pending_invites:
            issues.append({
                "code": "expired_pending_invites",
                "repair_state": "recoverable",
                "message": "World has expired invites that should be reviewed or revoked.",
                "count": len(expired_pending_invites),
            })

        recent_repair_events = [item for item in recent_audit if item.get("repair_state") == "recoverable"]
        if recent_repair_events:
            issues.append({
                "code": "recent_repair_events",
                "repair_state": "recoverable",
                "message": "Recent collaboration or invite changes indicate an active repair surface.",
                "count": len(recent_repair_events),
            })

        repair_state = "aligned"
        if any(item["repair_state"] == "quarantined" for item in issues):
            repair_state = "quarantined"
        elif any(item["repair_state"] == "recoverable" for item in issues):
            repair_state = "recoverable"

        return {"repair_state": repair_state, "issues": issues}

    def _stream_loop(world_id: str) -> None:
        room = f"world:{world_id}"
        while True:
            with stream_lock:
                control = stream_controls.get(world_id)
                if control is None or not bool(control.get("active")):
                    break
                interval_ms = max(100, int(control.get("interval_ms", 1000)))
                steps = max(1, int(control.get("steps", 1)))
                actor_user_id = int(control.get("actor_user_id", 0)) or None

            try:
                engine.step_world(world_id, steps=steps)
                _log(world_id, "stream_tick", "world", actor_user_id=actor_user_id, details={"steps": steps, "interval_ms": interval_ms})
                _emit_world_state(world_id)
            except KeyError:
                socketio.emit("stream_error", {"error": "World no longer exists.", "world_id": world_id}, room=room)
                with stream_lock:
                    stream_controls.pop(world_id, None)
                break

            sleep(interval_ms / 1000)

    @app.route("/")
    def index():
        return jsonify({"name": "ORYX Creator Engine", "status": "online", "worlds": engine.list_worlds()})

    @app.route("/api/health")
    def health():
        return jsonify({"ok": True, "service": "oryx-backend"})

    @app.route("/api/auth/register", methods=["POST"])
    def register():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        if not email or len(password) < 8:
            return jsonify({"error": "Email required and password must be at least 8 characters."}), 400
        try:
            user_id = auth.create_user(email=email, password=password)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 409
        return jsonify({"ok": True, "user_id": user_id})

    @app.route("/api/auth/login", methods=["POST"])
    def login():
        payload = request.get_json(silent=True) or {}
        email = (payload.get("email") or "").strip().lower()
        password = payload.get("password") or ""
        token = auth.authenticate_and_issue_token(email=email, password=password)
        if token is None:
            return jsonify({"error": "Invalid credentials."}), 401
        return jsonify({"token": token})

    @app.route("/api/templates")
    def templates():
        return jsonify(engine.templates())

    @app.route("/api/worlds", methods=["GET", "POST"])
    def worlds():
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401

        if request.method == "GET":
            return jsonify(auth.list_worlds_for_user(user_id))

        payload = request.get_json(silent=True) or {}
        world = engine.create_world(
            name=payload.get("name", "Untitled ORYX World"),
            template_key=payload.get("template", "sunsteel_frontier"),
            company_name=payload.get("company_name", "ORYX Studios"),
            integration_mode=payload.get("integration_mode", "optional"),
        )
        world_id = world["world"]["id"]
        auth.assign_world_to_user(user_id=user_id, world_id=world_id)
        _log(world_id, "world_created", "world", actor_user_id=user_id, details={"template": payload.get("template", "sunsteel_frontier")})
        return jsonify(world), 201

    @app.route("/api/worlds/<world_id>")
    def world_detail(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _has_permission(user_id, world_id, "can_view_world"):
            return jsonify({"error": "Forbidden"}), 403
        return jsonify(engine.load_world(world_id))

    @app.route("/api/worlds/<world_id>/summary")
    def world_summary(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _has_permission(user_id, world_id, "can_view_world"):
            return jsonify({"error": "Forbidden"}), 403

        world = engine.load_world(world_id)
        collaborators = auth.list_collaborators(world_id)
        recent_audit = auth.list_audit_log(world_id, limit=5)
        active_stream = bool(stream_controls.get(world_id, {}).get("active"))
        repair_status = _world_repair_status(world_id, world, collaborators, recent_audit)
        summary = {
            "world": world["world"],
            "counts": {
                "agents": len(world.get("agents", [])),
                "enemies": len(world.get("enemies", [])),
                "resources": len(world.get("resources", [])),
                "quests": len(world.get("quests", [])),
                "open_quests": sum(1 for item in world.get("quests", []) if item.get("status") == "open"),
                "collaborators": len(collaborators),
            },
            "stream": stream_controls.get(world_id, {"active": False}),
            "active_stream": active_stream,
            "recent_audit": recent_audit,
            "role": _world_role(user_id, world_id),
            "permissions": auth.get_effective_permissions(user_id=user_id, world_id=world_id),
            "repair_state": repair_status["repair_state"],
            "issues": repair_status["issues"],
        }
        return jsonify(summary)

    @app.route("/api/worlds/<world_id>/step", methods=["POST"])
    def world_step(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _has_permission(user_id, world_id, "can_step_world"):
            return jsonify({"error": "Forbidden"}), 403
        payload = request.get_json(silent=True) or {}
        stepped = engine.step_world(world_id, steps=int(payload.get("steps", 1)))
        _log(world_id, "world_step", "world", actor_user_id=user_id, details={"steps": int(payload.get("steps", 1))})
        socketio.emit("world_state", stepped, room=f"world:{world_id}")
        return jsonify(stepped)

    @app.route("/api/worlds/<world_id>/agents", methods=["POST"])
    def add_agent(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _has_permission(user_id, world_id, "can_manage_agents"):
            return jsonify({"error": "Forbidden"}), 403
        payload = request.get_json(silent=True) or {}
        updated = engine.add_agent(world_id, agent_name=payload.get("name", "Creator Agent"), behavior=payload.get("behavior", "explore"))
        _log(world_id, "agent_added", "agent", actor_user_id=user_id, details={"name": payload.get("name", "Creator Agent"), "behavior": payload.get("behavior", "explore")})
        socketio.emit("world_state", updated, room=f"world:{world_id}")
        return jsonify(updated)

    @app.route("/api/worlds/<world_id>/quests", methods=["POST"])
    def inject_quest(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _has_permission(user_id, world_id, "can_manage_quests"):
            return jsonify({"error": "Forbidden"}), 403
        payload = request.get_json(silent=True) or {}
        updated = engine.inject_quest(world_id, quest_text=payload.get("text", "New creator quest"))
        _log(world_id, "quest_added", "quest", actor_user_id=user_id, details={"text": payload.get("text", "New creator quest")})
        socketio.emit("world_state", updated, room=f"world:{world_id}")
        return jsonify(updated)

    @app.route("/api/worlds/<world_id>/collaborators", methods=["GET", "POST"])
    def collaborators(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401

        if request.method == "GET":
            if not _has_permission(user_id, world_id, "can_view_world"):
                return jsonify({"error": "Forbidden"}), 403
            return jsonify(auth.list_collaborators(world_id))

        if not _is_world_owner(user_id, world_id):
            return jsonify({"error": "Only owner can manage collaborators."}), 403

        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip().lower()
        role = str(payload.get("role", "viewer")).strip().lower()
        if not email:
            return jsonify({"error": "Collaborator email is required."}), 400

        try:
            added = auth.add_collaborator(world_id=world_id, email=email, role=role)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        _log(world_id, "collaborator_added", "collaborator", actor_user_id=user_id, target_id=email, details={"role": role})
        return jsonify(added), 201

    @app.route("/api/worlds/<world_id>/collaborators/remove", methods=["POST"])
    def remove_collaborator(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _is_world_owner(user_id, world_id):
            return jsonify({"error": "Only owner can manage collaborators."}), 403

        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip().lower()
        if not email:
            return jsonify({"error": "Collaborator email is required."}), 400

        removed = auth.remove_collaborator(world_id=world_id, email=email)
        if not removed:
            return jsonify({"error": "Collaborator not found."}), 404
        _log(world_id, "collaborator_removed", "collaborator", actor_user_id=user_id, target_id=email)
        return jsonify({"ok": True, "email": email})

    @app.route("/api/worlds/<world_id>/permissions", methods=["GET", "POST"])
    def permissions(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401

        if request.method == "GET":
            if not _has_permission(user_id, world_id, "can_view_world"):
                return jsonify({"error": "Forbidden"}), 403
            return jsonify(auth.list_collaborators(world_id))

        if not _is_world_owner(user_id, world_id):
            return jsonify({"error": "Only owner can manage feature permissions."}), 403

        payload = request.get_json(silent=True) or {}
        email = str(payload.get("email", "")).strip().lower()
        if not email:
            return jsonify({"error": "Collaborator email is required."}), 400
        permissions_payload = {key: payload.get(key) for key in FEATURE_KEYS}
        try:
            updated = auth.set_feature_permissions(world_id=world_id, email=email, permissions=permissions_payload)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        _log(world_id, "permissions_updated", "collaborator", actor_user_id=user_id, target_id=email, details=permissions_payload)
        return jsonify(updated)

    @app.route("/api/worlds/<world_id>/invites", methods=["GET", "POST"])
    def invites(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _is_world_owner(user_id, world_id):
            return jsonify({"error": "Only owner can manage invites."}), 403

        if request.method == "GET":
            return jsonify(auth.list_invites(world_id, base_url=_base_url()))

        payload = request.get_json(silent=True) or {}
        role = str(payload.get("role", "viewer")).strip().lower()
        expires_in_hours = int(payload.get("expires_in_hours", 72))
        try:
            invite = auth.create_invite(world_id=world_id, role=role, created_by_user_id=user_id, expires_in_hours=expires_in_hours, base_url=_base_url())
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        _log(world_id, "invite_created", "invite", actor_user_id=user_id, target_id=invite["token"], details={"role": role, "expires_in_hours": expires_in_hours})
        return jsonify(invite), 201

    @app.route("/api/worlds/<world_id>/invites/revoke", methods=["POST"])
    def revoke_invite(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _is_world_owner(user_id, world_id):
            return jsonify({"error": "Only owner can manage invites."}), 403

        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()
        if not token:
            return jsonify({"error": "Invite token is required."}), 400

        revoked = auth.revoke_invite(token=token)
        if not revoked:
            return jsonify({"error": "Invite not found or already inactive."}), 404
        _log(world_id, "invite_revoked", "invite", actor_user_id=user_id, target_id=token)
        return jsonify({"ok": True, "token": token})

    @app.route("/api/invites/accept", methods=["POST"])
    def accept_invite():
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401

        payload = request.get_json(silent=True) or {}
        token = str(payload.get("token", "")).strip()
        if not token:
            return jsonify({"error": "Invite token is required."}), 400

        try:
            accepted = auth.accept_invite(token=token, user_id=user_id)
        except ValueError as exc:
            return jsonify({"error": str(exc)}), 400
        _log(accepted["world_id"], "invite_accepted", "invite", actor_user_id=user_id, target_id=token, details={"role": accepted["role"]})
        return jsonify(accepted)

    @app.route("/api/worlds/<world_id>/audit")
    def audit(world_id: str):
        try:
            user_id = _require_user_id()
        except PermissionError:
            return jsonify({"error": "Unauthorized"}), 401
        if not _has_permission(user_id, world_id, "can_view_world"):
            return jsonify({"error": "Forbidden"}), 403
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        action = (request.args.get("action") or "").strip() or None
        actor_email = (request.args.get("actor_email") or "").strip().lower() or None
        repair_state = (request.args.get("repair_state") or "").strip().lower() or None
        safe_limit = max(1, min(500, limit))
        safe_offset = max(0, offset)
        items = auth.list_audit_log(
            world_id,
            limit=safe_limit,
            offset=safe_offset,
            action=action,
            actor_email=actor_email,
            repair_state=repair_state,
        )
        total = auth.count_audit_log(world_id, action=action, actor_email=actor_email, repair_state=repair_state)
        return jsonify({"items": items, "total": total, "limit": safe_limit, "offset": safe_offset})

    @socketio.on("join_world")
    def on_join_world(payload):
        payload = payload or {}
        world_id = str(payload.get("world_id", "")).strip()
        token = str(payload.get("token", "")).strip()
        user = auth.get_user_by_token(token)
        if user is None:
            emit("stream_error", {"error": "Unauthorized."})
            return
        user_id = int(user["id"])
        if not _has_permission(user_id, world_id, "can_view_world"):
            emit("stream_error", {"error": "Forbidden for this world."})
            return
        room = f"world:{world_id}"
        join_room(room)
        emit("joined_world", {"room": room, "world_id": world_id, "role": _world_role(user_id, world_id)})
        _emit_world_state(world_id)

    @socketio.on("leave_world")
    def on_leave_world(payload):
        payload = payload or {}
        world_id = str(payload.get("world_id", "")).strip()
        leave_room(f"world:{world_id}")
        emit("left_world", {"world_id": world_id})

    @socketio.on("tick_once")
    def on_tick_once(payload):
        payload = payload or {}
        world_id = str(payload.get("world_id", "")).strip()
        token = str(payload.get("token", "")).strip()
        steps = int(payload.get("steps", 1))
        user = auth.get_user_by_token(token)
        if user is None:
            emit("stream_error", {"error": "Unauthorized."})
            return
        user_id = int(user["id"])
        if not _has_permission(user_id, world_id, "can_step_world"):
            emit("stream_error", {"error": "Forbidden for this world."})
            return
        engine.step_world(world_id, steps=max(1, steps))
        _log(world_id, "socket_tick", "world", actor_user_id=user_id, details={"steps": max(1, steps)})
        _emit_world_state(world_id)

    @socketio.on("start_stream")
    def on_start_stream(payload):
        payload = payload or {}
        world_id = str(payload.get("world_id", "")).strip()
        token = str(payload.get("token", "")).strip()
        interval_ms = int(payload.get("interval_ms", 1000))
        steps = int(payload.get("steps", 1))
        user = auth.get_user_by_token(token)
        if user is None:
            emit("stream_error", {"error": "Unauthorized."})
            return
        user_id = int(user["id"])
        if not _has_permission(user_id, world_id, "can_manage_stream"):
            emit("stream_error", {"error": "Forbidden for this world."})
            return
        with stream_lock:
            already_active = world_id in stream_controls and bool(stream_controls[world_id].get("active"))
            stream_controls[world_id] = {
                "active": True,
                "interval_ms": max(100, interval_ms),
                "steps": max(1, steps),
                "actor_user_id": user_id,
            }
        if not already_active:
            socketio.start_background_task(_stream_loop, world_id)
        _log(world_id, "stream_started", "world", actor_user_id=user_id, details={"interval_ms": interval_ms, "steps": steps})
        emit("stream_status", {"world_id": world_id, "active": True})

    @socketio.on("stop_stream")
    def on_stop_stream(payload):
        payload = payload or {}
        world_id = str(payload.get("world_id", "")).strip()
        token = str(payload.get("token", "")).strip()
        user = auth.get_user_by_token(token)
        if user is None:
            emit("stream_error", {"error": "Unauthorized."})
            return
        user_id = int(user["id"])
        if not _has_permission(user_id, world_id, "can_manage_stream"):
            emit("stream_error", {"error": "Forbidden for this world."})
            return
        with stream_lock:
            if world_id in stream_controls:
                stream_controls[world_id]["active"] = False
        _log(world_id, "stream_stopped", "world", actor_user_id=user_id)
        emit("stream_status", {"world_id": world_id, "active": False})

    @app.route("/editor")
    def editor():
        frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/editor/<path:asset>")
    def editor_assets(asset: str):
        frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
        return send_from_directory(frontend_dir, asset)

    return app


app = create_app()


if __name__ == "__main__":
    socketio.run(app, debug=True)
