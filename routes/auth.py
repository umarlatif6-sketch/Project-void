import os
import functools
from flask import Blueprint, request, jsonify, session, redirect, render_template, url_for

from void_engine.messenger_auth import create_user, authenticate_user, _get_db

auth_bp = Blueprint("auth", __name__)

FOUNDER_USERNAME = os.environ.get("FOUNDER_USERNAME", "").lower().strip()

TIER_LEVELS = {"ghost": 0, "journalist": 1, "sovereign": 2}
TIER_LIMITS = {
    "ghost": {"upload_mb": 1, "scatter_modes": ["jitter"], "mesh": False, "journalism": False, "custom_salts": False},
    "journalist": {"upload_mb": 50, "scatter_modes": ["jitter", "vortex", "chirp_sync"], "mesh": False, "journalism": True, "custom_salts": False},
    "sovereign": {"upload_mb": 0, "scatter_modes": ["jitter", "vortex", "chirp_sync"], "mesh": True, "journalism": True, "custom_salts": True},
}


def _ensure_column(cur, table, column, definition):
    cur.execute(
        "SELECT 1 FROM information_schema.columns WHERE table_name = %s AND column_name = %s",
        (table, column),
    )
    if not cur.fetchone():
        cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def _ensure_columns():
    conn = _get_db()
    try:
        cur = conn.cursor()
        _ensure_column(cur, "users", "role", "VARCHAR(20) DEFAULT 'user'")
        _ensure_column(cur, "users", "tier", "VARCHAR(20) DEFAULT 'ghost'")
        _ensure_column(cur, "users", "tier_expires_at", "TIMESTAMP")
        _ensure_column(cur, "users", "stripe_customer_id", "VARCHAR(100)")
        _ensure_column(cur, "users", "stripe_subscription_id", "VARCHAR(100)")
        _ensure_column(cur, "users", "vortex_balance", "DECIMAL(18,4) DEFAULT 0")

        _ensure_column(cur, "messages", "attachment_filename", "VARCHAR(255)")
        _ensure_column(cur, "messages", "attachment_path", "VARCHAR(500)")
        _ensure_column(cur, "messages", "attachment_size", "BIGINT")
        _ensure_column(cur, "messages", "attachment_type", "VARCHAR(50)")
        _ensure_column(cur, "messages", "silt_hash_key", "TEXT")
        _ensure_column(cur, "messages", "silt_carrier_style", "VARCHAR(50)")
        _ensure_column(cur, "messages", "vtx_earned", "DECIMAL(18,4) DEFAULT 0")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vortex_ledger (
                id SERIAL PRIMARY KEY,
                block_index INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT NOW(),
                previous_hash VARCHAR(72) NOT NULL,
                tx_type VARCHAR(30) NOT NULL,
                from_user_id INTEGER REFERENCES users(id),
                to_user_id INTEGER REFERENCES users(id),
                amount DECIMAL(18,4) NOT NULL,
                payload_hash VARCHAR(72),
                payload_size_bytes BIGINT,
                block_hash VARCHAR(72) NOT NULL,
                phase_key_signature VARCHAR(16),
                node_id VARCHAR(72)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vigilance_reports (
                id SERIAL PRIMARY KEY,
                reporter_id INTEGER REFERENCES users(id) NOT NULL,
                title VARCHAR(200) NOT NULL,
                description TEXT NOT NULL,
                severity VARCHAR(20) NOT NULL,
                category VARCHAR(40),
                steps_to_reproduce TEXT,
                status VARCHAR(20) DEFAULT 'pending',
                admin_notes TEXT,
                vtx_reward DECIMAL(18,4) DEFAULT 0,
                created_at TIMESTAMP DEFAULT NOW(),
                reviewed_at TIMESTAMP,
                reviewed_by INTEGER REFERENCES users(id)
            )
        """)

        conn.commit()

        _init_vortex_genesis(conn)
    except Exception:
        conn.rollback()
    finally:
        conn.close()


def _init_vortex_genesis(conn):
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM vortex_ledger WHERE block_index = 0")
        if cur.fetchone():
            return
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated
        cur.execute("SELECT id FROM users ORDER BY id LIMIT 1")
        row = cur.fetchone()
        genesis_user = row[0] if row else None
        prev_hash = "0" * 72
        genesis_data = f"0|{prev_hash}|VORTEX_GENESIS|mint_resonance|0"
        block_hash = fatiha_286_hexdigest_from_str(genesis_data)
        phase_sig = fatiha_286_truncated(genesis_data.encode("utf-8"), 16)
        cur.execute(
            """INSERT INTO vortex_ledger (block_index, previous_hash, tx_type, to_user_id, amount, payload_hash, block_hash, phase_key_signature, node_id)
               VALUES (0, %s, 'mint_resonance', %s, 0, 'VORTEX_GENESIS', %s, %s, 'genesis')""",
            (prev_hash, genesis_user, block_hash, phase_sig),
        )
        conn.commit()
    except Exception:
        conn.rollback()


def _get_user_role(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return row[0] if row and row[0] else "user"
    finally:
        conn.close()


def _get_user_tier(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT tier, tier_expires_at FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            return "ghost"
        tier = row[0]
        expires = row[1]
        if tier != "ghost" and expires:
            from datetime import datetime, timezone
            if expires.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                _set_user_tier(user_id, "ghost")
                return "ghost"
        return tier
    finally:
        conn.close()


def _set_user_tier(user_id, tier, expires_at=None):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET tier = %s, tier_expires_at = %s WHERE id = %s", (tier, expires_at, user_id))
        conn.commit()
    finally:
        conn.close()


def _set_user_role(user_id, role):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE users SET role = %s WHERE id = %s", (role, user_id))
        conn.commit()
    finally:
        conn.close()


def _set_stripe_ids(user_id, customer_id=None, subscription_id=None):
    conn = _get_db()
    try:
        cur = conn.cursor()
        if customer_id and subscription_id:
            cur.execute("UPDATE users SET stripe_customer_id = %s, stripe_subscription_id = %s WHERE id = %s",
                        (customer_id, subscription_id, user_id))
        elif customer_id:
            cur.execute("UPDATE users SET stripe_customer_id = %s WHERE id = %s", (customer_id, user_id))
        elif subscription_id:
            cur.execute("UPDATE users SET stripe_subscription_id = %s WHERE id = %s", (subscription_id, user_id))
        conn.commit()
    finally:
        conn.close()


def _get_stripe_customer_id(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT stripe_customer_id FROM users WHERE id = %s", (user_id,))
        row = cur.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def _get_user_by_stripe_customer(customer_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE stripe_customer_id = %s", (customer_id,))
        row = cur.fetchone()
        return {"id": row[0], "username": row[1]} if row else None
    finally:
        conn.close()


def _get_user_by_stripe_subscription(subscription_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id, username FROM users WHERE stripe_subscription_id = %s", (subscription_id,))
        row = cur.fetchone()
        return {"id": row[0], "username": row[1]} if row else None
    finally:
        conn.close()


def login_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("user_id"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect("/login")
        role = session.get("role", "user")
        if role not in ("admin", "founder"):
            if request.is_json or request.path.startswith("/api/"):
                return jsonify({"error": "Admin access required"}), 403
            return redirect("/")
        return f(*args, **kwargs)
    return decorated


def tier_required(min_tier):
    def decorator(f):
        @functools.wraps(f)
        def decorated(*args, **kwargs):
            if not session.get("user_id"):
                if request.is_json or request.path.startswith("/api/"):
                    return jsonify({"error": "Authentication required"}), 401
                return redirect("/login")
            user_tier = _get_user_tier(session["user_id"])
            session["tier"] = user_tier
            if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get(min_tier, 0):
                tier_names = {"journalist": "Journalist", "sovereign": "Sovereign"}
                name = tier_names.get(min_tier, min_tier)
                return jsonify({"error": f"Upgrade to {name} tier to access this feature", "upgrade": True, "required_tier": min_tier}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


def _setup_session(user, role=None):
    if role is None:
        role = _get_user_role(user["id"])
    if FOUNDER_USERNAME and user.get("username", "").lower() == FOUNDER_USERNAME and role != "founder":
        role = "founder"
        _set_user_role(user["id"], "founder")
    is_founder = role == "founder"
    tier = _get_user_tier(user["id"])
    if is_founder and tier != "sovereign":
        tier = "sovereign"
        _set_user_tier(user["id"], "sovereign")
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["display_name"] = user.get("display_name", user["username"])
    session["role"] = role
    session["is_founder"] = is_founder
    session["tier"] = tier
    session["messenger_user_id"] = user["id"]
    os.makedirs(f"data/vaults/{user['username']}/input_files", exist_ok=True)
    os.makedirs(f"data/vaults/{user['username']}/output_audio", exist_ok=True)


@auth_bp.route("/login")
def login_page():
    if session.get("user_id"):
        return redirect("/")
    return render_template("login.html")


@auth_bp.route("/api/auth/register", methods=["POST"])
def auth_register():
    data = request.json or {}
    username = (data.get("username") or "").strip().lower()
    display_name = (data.get("display_name") or "").strip()
    password = data.get("password") or ""
    confirm = data.get("confirm_password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400
    if len(username) < 3 or len(username) > 50:
        return jsonify({"error": "Username must be 3-50 characters"}), 400
    if not all(c.isalnum() or c in "_-" for c in username):
        return jsonify({"error": "Username can only contain letters, numbers, hyphens, and underscores"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    if confirm and password != confirm:
        return jsonify({"error": "Passwords do not match"}), 400

    if not display_name:
        display_name = username

    user = create_user(username, display_name, password)
    if not user:
        return jsonify({"error": "Username already taken"}), 409

    _setup_session(user)

    return jsonify({"success": True, "user": user, "role": session.get("role", "user"), "tier": session.get("tier", "ghost")}), 201


@auth_bp.route("/api/auth/login", methods=["POST"])
def auth_login():
    data = request.json or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user = authenticate_user(username, password)
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401

    _setup_session(user)

    return jsonify({
        "success": True,
        "user": user,
        "role": session.get("role", "user"),
        "is_founder": session.get("is_founder", False),
        "tier": session.get("tier", "ghost"),
    })


@auth_bp.route("/api/auth/logout")
def auth_logout():
    session.clear()
    return redirect("/login")


@auth_bp.route("/api/auth/me")
def auth_me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False}), 401
    return jsonify({
        "authenticated": True,
        "user_id": user_id,
        "username": session.get("username"),
        "display_name": session.get("display_name"),
        "role": session.get("role", "user"),
        "is_founder": session.get("is_founder", False),
        "tier": session.get("tier", "ghost"),
    })
