import os
import wave
import uuid
from flask import Blueprint, request, jsonify, session, render_template, redirect, send_file
from werkzeug.utils import secure_filename
from void_engine.messenger_auth import (
    create_user,
    authenticate_user,
    get_user_by_id,
    search_users,
    find_or_create_conversation,
    get_conversations,
    send_message,
    get_messages,
    decrypt_message,
    _get_db,
)
from routes.auth import _setup_session, login_required, tier_required, TIER_LEVELS, _get_user_tier, _check_rate_limit

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
    user_id = session.get("user_id")
    if not user_id:
        return None
    return user_id


@messenger_bp.route("/messenger")
def messenger_page():
    return render_template("messenger.html")


@messenger_bp.route("/api/messenger/register", methods=["POST"])
def messenger_register():
    if not _check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait and try again."}), 429
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
    if not _check_rate_limit():
        return jsonify({"error": "Too many requests. Please wait and try again."}), 429
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


def _silt_drops_dir(username):
    d = f"data/vaults/{username}/silt_drops"
    os.makedirs(d, exist_ok=True)
    return d


def _check_conversation_member(conv_id, user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s", (conv_id, user_id))
        return bool(cur.fetchone())
    finally:
        conn.close()


@messenger_bp.route("/api/messenger/silt-drop", methods=["POST"])
def messenger_silt_drop():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user_tier = _get_user_tier(user_id)
    session["tier"] = user_tier
    if TIER_LEVELS.get(user_tier, 0) < TIER_LEVELS.get("journalist", 1):
        return jsonify({
            "error": "Silt Drops require Journalist tier or higher. Upgrade at /pricing",
            "upgrade": True,
        }), 403

    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"error": "No filename"}), 400

    conv_id = request.form.get("conversation_id", type=int)
    if not conv_id:
        return jsonify({"error": "Conversation ID is required"}), 400

    if not _check_conversation_member(conv_id, user_id):
        return jsonify({"error": "Not a member of this conversation"}), 403

    carrier_style = request.form.get("carrier_style", "midnight_pond")

    f.seek(0, 2)
    file_size = f.tell()
    f.seek(0)
    if file_size > 50 * 1024 * 1024:
        return jsonify({"error": "File exceeds 50MB limit"}), 413

    username = session.get("username", "unknown")
    drops_dir = _silt_drops_dir(username)
    safe_name = secure_filename(f.filename)
    input_path = os.path.join(drops_dir, f"input_{safe_name}")
    f.save(input_path)

    try:
        from void_engine.compressor import compress_file
        from void_engine.stega import encode, encode_stereo
        from generate_carriers import generate_custom_carrier

        compressed, name, ext, orig_size = compress_file(input_path, low_power=False)

        carrier_samples = len(compressed) * 8 // 2 + 44100 * 2
        duration_s = max(carrier_samples / 44100, 3.0)

        carrier_path = os.path.join(drops_dir, f"carrier_{uuid.uuid4().hex[:8]}.wav")
        generate_custom_carrier(
            style=carrier_style,
            duration_seconds=duration_s,
            output_path=carrier_path,
        )

        drop_id = uuid.uuid4().hex[:12]
        output_name = f"silt_drop_{drop_id}.wav"
        output_path = os.path.join(drops_dir, output_name)

        with wave.open(carrier_path, "rb") as wf:
            n_channels = wf.getnchannels()

        if n_channels == 2:
            hash_key = encode_stereo(carrier_path, compressed, name, ext, output_path, lsb_depth=2, vortex=True)
        else:
            hash_key = encode(carrier_path, compressed, name, ext, output_path, lsb_depth=2, vortex=True)

        try:
            os.remove(input_path)
            os.remove(carrier_path)
        except OSError:
            pass

        from void_engine.vortex_wallet import mint_resonance
        mint_result = mint_resonance(user_id, len(compressed), hash_key)
        vtx_earned = mint_result.get("vtx_earned", 0)

        text_content = request.form.get("message", "") or f"Silt Drop: {safe_name}"
        msg = send_message(
            conv_id, user_id, text_content,
            message_type="silt_drop",
            attachment_filename=safe_name,
            attachment_path=output_path,
            attachment_size=orig_size,
            attachment_type="silt_drop",
            silt_hash_key=hash_key,
            silt_carrier_style=carrier_style,
            vtx_earned=vtx_earned,
        )

        if msg is None:
            return jsonify({"error": "Failed to send message"}), 500

        return jsonify({
            "success": True,
            "message": msg,
            "hash_key": hash_key,
            "vtx_earned": vtx_earned,
            "carrier_style": carrier_style,
            "original_size": orig_size,
            "compressed_size": len(compressed),
            "output_file": output_name,
        }), 201

    except Exception as e:
        try:
            os.remove(input_path)
        except OSError:
            pass
        return jsonify({"error": str(e)}), 500


@messenger_bp.route("/api/messenger/silt-drop/<int:message_id>/download")
def messenger_silt_download(message_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT m.attachment_path, m.attachment_filename, m.conversation_id
               FROM messages m
               WHERE m.id = %s AND m.attachment_type = 'silt_drop'""",
            (message_id,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Silt drop not found"}), 404

        attachment_path, attachment_filename, conv_id = row
        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s",
            (conv_id, user_id),
        )
        if not cur.fetchone():
            return jsonify({"error": "Not a member of this conversation"}), 403
    finally:
        conn.close()

    if not attachment_path or not os.path.exists(attachment_path):
        return jsonify({"error": "Audio file not found on disk"}), 404

    return send_file(attachment_path, mimetype="audio/wav",
                     as_attachment=False, download_name=f"silt_drop_{attachment_filename}.wav")


@messenger_bp.route("/api/messenger/silt-drop/<int:message_id>/decode", methods=["POST"])
def messenger_silt_decode(message_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT m.attachment_path, m.attachment_filename, m.conversation_id, m.silt_hash_key
               FROM messages m
               WHERE m.id = %s AND m.attachment_type = 'silt_drop'""",
            (message_id,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Silt drop not found"}), 404

        attachment_path, attachment_filename, conv_id, encrypted_key_data = row
        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s",
            (conv_id, user_id),
        )
        if not cur.fetchone():
            return jsonify({"error": "Not a member of this conversation"}), 403
    finally:
        conn.close()

    if not attachment_path or not os.path.exists(attachment_path):
        return jsonify({"error": "Audio file not found on disk"}), 404

    if not encrypted_key_data:
        return jsonify({"error": "No hash key stored for this silt drop"}), 400

    try:
        nonce_hex, ciphertext_b64 = encrypted_key_data.split(":", 1)
        hash_key = decrypt_message(ciphertext_b64, nonce_hex, conv_id)
    except Exception:
        return jsonify({"error": "Failed to decrypt hash key"}), 500

    try:
        from void_engine.stega import decode, decode_stereo
        from void_engine.compressor import decompress_data

        with wave.open(attachment_path, "rb") as wf:
            n_channels = wf.getnchannels()

        if n_channels == 2:
            data, filename, ext = decode_stereo(attachment_path, hash_key)
        else:
            data, filename, ext = decode(attachment_path, hash_key)

        original = decompress_data(data)

        username = session.get("username", "unknown")
        out_dir = f"data/vaults/{username}/silt_drops"
        os.makedirs(out_dir, exist_ok=True)
        out_name = f"{filename}{ext}" if filename else attachment_filename
        out_path = os.path.join(out_dir, f"decoded_{out_name}")
        with open(out_path, "wb") as fp:
            fp.write(original)

        return send_file(out_path, as_attachment=True, download_name=out_name)
    except Exception as e:
        return jsonify({"error": f"Decode failed: {str(e)}"}), 500


@messenger_bp.route("/api/messenger/gift", methods=["POST"])
def messenger_gift():
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    data = request.get_json(silent=True) or {}
    conv_id = data.get("conversation_id")
    message_id = data.get("message_id")
    amount = data.get("amount")

    if not conv_id or not message_id or not amount:
        return jsonify({"error": "conversation_id, message_id, and amount are required"}), 400

    try:
        amount = float(amount)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid amount"}), 400

    if amount <= 0:
        return jsonify({"error": "Amount must be positive"}), 400

    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s",
            (conv_id, user_id),
        )
        if not cur.fetchone():
            return jsonify({"error": "Not a member of this conversation"}), 403

        cur.execute(
            "SELECT sender_id FROM messages WHERE id = %s AND conversation_id = %s",
            (message_id, conv_id),
        )
        msg_row = cur.fetchone()
        if not msg_row:
            return jsonify({"error": "Message not found"}), 404

        recipient_id = msg_row[0]
        if recipient_id == user_id:
            return jsonify({"error": "Cannot gift yourself"}), 400

    finally:
        conn.close()

    from void_engine.vortex_wallet import gift_transfer
    result = gift_transfer(user_id, recipient_id, amount, message_id)

    if "error" in result:
        return jsonify(result), 400

    gift_hash = result.get("gift_hash", result.get("block_hash", ""))

    from void_engine.gift_chime import generate_gift_chime
    try:
        chime_path = generate_gift_chime(amount, gift_hash)
    except Exception as e:
        chime_path = None

    gift_content = f"[VTX Gift] {amount} VTX"
    from void_engine.messenger_auth import send_message as _send_msg
    gift_msg = _send_msg(conv_id, user_id, gift_content)

    conn = _get_db()
    try:
        cur = conn.cursor()

        cur.execute(
            """INSERT INTO vortex_gifts (sender_id, recipient_id, amount, message_id, conversation_id,
                                         al_jabr_286_hash, chime_path, status)
               VALUES (%s, %s, %s, %s, %s, %s, %s, 'settled')""",
            (user_id, recipient_id, amount, message_id, conv_id, gift_hash, chime_path),
        )

        if chime_path and gift_msg:
            gift_msg_id = gift_msg.get("id") if isinstance(gift_msg, dict) else None
            if gift_msg_id:
                cur.execute(
                    """UPDATE messages SET attachment_path = %s, attachment_type = 'gift_chime',
                       attachment_filename = %s WHERE id = %s""",
                    (chime_path, os.path.basename(chime_path), gift_msg_id),
                )

        conn.commit()
    except Exception:
        conn.rollback()
    finally:
        conn.close()

    tier = "sovereign" if amount >= 100 else ("medium" if amount >= 10 else "small")

    return jsonify({
        "success": True,
        "gift_hash": gift_hash,
        "amount": amount,
        "recipient_id": recipient_id,
        "gift_tier": tier,
        "chime_path": chime_path,
        "block": result,
    })


@messenger_bp.route("/api/messenger/silt-drop/<int:message_id>/key")
def messenger_silt_key(message_id):
    user_id = _require_login()
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT m.conversation_id, m.silt_hash_key
               FROM messages m
               WHERE m.id = %s AND m.attachment_type = 'silt_drop'""",
            (message_id,),
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Silt drop not found"}), 404

        conv_id, encrypted_key_data = row
        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s",
            (conv_id, user_id),
        )
        if not cur.fetchone():
            return jsonify({"error": "Not a member of this conversation"}), 403
    finally:
        conn.close()

    if not encrypted_key_data:
        return jsonify({"error": "No hash key stored"}), 400

    try:
        nonce_hex, ciphertext_b64 = encrypted_key_data.split(":", 1)
        hash_key = decrypt_message(ciphertext_b64, nonce_hex, conv_id)
        return jsonify({"hash_key": hash_key})
    except Exception:
        return jsonify({"error": "Failed to decrypt hash key"}), 500
