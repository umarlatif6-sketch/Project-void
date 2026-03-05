from flask import Blueprint, request, jsonify, session, render_template, redirect
from void_engine.messenger_auth import (
    create_user,
    authenticate_user,
    get_user_by_id,
    search_users,
    find_or_create_conversation,
    get_conversations,
    send_message,
    get_messages,
)
from routes.auth import _setup_session, login_required

messenger_bp = Blueprint("messenger", __name__)

_MESSENGER_PUBLIC_PATHS = {
    "/api/messenger/register",
    "/api/messenger/login",
}


@messenger_bp.before_request
def _messenger_auth():
    if request.path in _MESSENGER_PUBLIC_PATHS:
        return None
    if not session.get("user_id"):
        if request.is_json or request.path.startswith("/api/"):
            return jsonify({"error": "Authentication required"}), 401
        return redirect("/login")


def _require_login():
    user_id = session.get("messenger_user_id") or session.get("user_id")
    if not user_id:
        return None
    return user_id


@messenger_bp.route("/messenger")
def messenger_page():
    return render_template("messenger.html")


@messenger_bp.route("/api/messenger/register", methods=["POST"])
def messenger_register():
    data = request.json or {}
    username = (data.get("username") or "").strip().lower()
    display_name = (data.get("display_name") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(username) < 3 or len(username) > 50:
        return jsonify({"error": "Username must be 3-50 characters"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if not username.isalnum() and not all(c.isalnum() or c in "_-" for c in username):
        return jsonify({"error": "Username can only contain letters, numbers, hyphens, and underscores"}), 400

    if not display_name:
        display_name = username

    user = create_user(username, display_name, password)
    if not user:
        return jsonify({"error": "Username already taken"}), 409

    _setup_session(user)
    return jsonify({"user": user}), 201


@messenger_bp.route("/api/messenger/login", methods=["POST"])
def messenger_login():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    _setup_session(user)
    return jsonify({"user": user})


@messenger_bp.route("/api/messenger/logout", methods=["POST"])
def messenger_logout():
    session.clear()
    return jsonify({"ok": True})


@messenger_bp.route("/api/messenger/me")
def messenger_me():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    user = get_user_by_id(user_id)
    if not user:
        session.pop("messenger_user_id", None)
        return jsonify({"error": "User not found"}), 401
    return jsonify({"user": user})


@messenger_bp.route("/api/messenger/users/search")
def messenger_user_search():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    q = request.args.get("q", "").strip()
    if len(q) < 1:
        return jsonify({"users": []})

    results = search_users(q, exclude_user_id=user_id)
    return jsonify({"users": results})


@messenger_bp.route("/api/messenger/conversations", methods=["GET"])
def messenger_conversations():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    convs = get_conversations(user_id)
    return jsonify({"conversations": convs})


@messenger_bp.route("/api/messenger/conversations", methods=["POST"])
def messenger_create_conversation():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json or {}
    other_username = (data.get("username") or "").strip().lower()
    if not other_username:
        return jsonify({"error": "Username is required"}), 400

    from void_engine.messenger_auth import _get_db
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE username = %s", (other_username,))
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "User not found"}), 404
        other_id = row[0]
    finally:
        conn.close()

    if other_id == user_id:
        return jsonify({"error": "Cannot message yourself"}), 400

    conv_id = find_or_create_conversation(user_id, other_id)
    return jsonify({"conversation_id": conv_id}), 201


@messenger_bp.route("/api/messenger/conversations/<int:conv_id>/messages", methods=["GET"])
def messenger_get_messages(conv_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    before_id = request.args.get("before", type=int)
    msgs = get_messages(conv_id, user_id, before_id=before_id)
    if msgs is None:
        return jsonify({"error": "Not a member of this conversation"}), 403

    return jsonify({"messages": msgs})


@messenger_bp.route("/api/messenger/conversations/<int:conv_id>/messages", methods=["POST"])
def messenger_send_message(conv_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.json or {}
    content = (data.get("content") or "").strip()
    if not content:
        return jsonify({"error": "Message cannot be empty"}), 400
    if len(content) > 5000:
        return jsonify({"error": "Message too long (max 5000 characters)"}), 400

    msg = send_message(conv_id, user_id, content)
    if msg is None:
        return jsonify({"error": "Not a member of this conversation"}), 403

    return jsonify({"message": msg}), 201
