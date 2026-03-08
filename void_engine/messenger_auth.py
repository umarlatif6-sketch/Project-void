import os
import base64
import psycopg2
from datetime import datetime
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from void_engine.al_jabr_286 import fatiha_286_hexdigest, fatiha_286_derive_key


def _get_db():
    return psycopg2.connect(os.environ["DATABASE_URL"])


def _generate_salt():
    return os.urandom(16).hex()


def hash_password(password, username, salt):
    salted = f"VOID-286-{salt}-{username.lower()}-{password}"
    return fatiha_286_hexdigest(salted.encode("utf-8"))


def verify_password(password, stored_hash, username, salt):
    return hash_password(password, username, salt) == stored_hash


def create_user(username, display_name, password):
    salt = _generate_salt()
    pw_hash = hash_password(password, username, salt)
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (username, display_name, password_hash, password_salt) VALUES (%s, %s, %s, %s) RETURNING id, username, display_name, created_at",
            (username.lower().strip(), display_name.strip(), pw_hash, salt),
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "username": row[1],
            "display_name": row[2],
            "created_at": row[3].isoformat(),
        }
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return None
    finally:
        conn.close()


def authenticate_user(username, password):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, display_name, password_hash, created_at, password_salt FROM users WHERE username = %s",
            (username.lower().strip(),),
        )
        row = cur.fetchone()
        if not row:
            return None
        salt = row[5] or ""
        if not verify_password(password, row[3], row[1], salt):
            return None
        cur.execute("UPDATE users SET last_seen = NOW() WHERE id = %s", (row[0],))
        conn.commit()
        return {
            "id": row[0],
            "username": row[1],
            "display_name": row[2],
            "created_at": row[4].isoformat(),
        }
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, username, display_name, created_at, last_seen, role, tier FROM users WHERE id = %s",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "username": row[1],
            "display_name": row[2],
            "created_at": row[3].isoformat() if row[3] else None,
            "last_seen": row[4].isoformat() if row[4] else None,
            "role": row[5] or "user",
            "tier": row[6] or "ghost",
        }
    finally:
        conn.close()


def search_users(query, exclude_user_id=None, limit=20):
    conn = _get_db()
    try:
        cur = conn.cursor()
        pattern = f"{query.lower().strip()}%"
        if exclude_user_id:
            cur.execute(
                "SELECT id, username, display_name FROM users WHERE username LIKE %s AND id != %s ORDER BY username LIMIT %s",
                (pattern, exclude_user_id, limit),
            )
        else:
            cur.execute(
                "SELECT id, username, display_name FROM users WHERE username LIKE %s ORDER BY username LIMIT %s",
                (pattern, limit),
            )
        return [{"id": r[0], "username": r[1], "display_name": r[2]} for r in cur.fetchall()]
    finally:
        conn.close()


def _get_conversation_key(conversation_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT encryption_key_encrypted FROM conversations WHERE id = %s", (conversation_id,))
        row = cur.fetchone()
        if not row or not row[0]:
            raw_key = os.urandom(32)
            _secret = os.environ.get("SESSION_SECRET")
            if not _secret:
                raise RuntimeError("SESSION_SECRET environment variable is required")
            master = fatiha_286_derive_key(_secret)
            master_aead = ChaCha20Poly1305(master)
            nonce = os.urandom(12)
            encrypted_key = master_aead.encrypt(nonce, raw_key, None)
            stored = base64.b64encode(nonce + encrypted_key).decode("ascii")
            cur.execute("UPDATE conversations SET encryption_key_encrypted = %s WHERE id = %s", (stored, conversation_id))
            conn.commit()
            return raw_key
        stored = base64.b64decode(row[0])
        nonce = stored[:12]
        encrypted_key = stored[12:]
        _secret = os.environ.get("SESSION_SECRET")
        if not _secret:
            raise RuntimeError("SESSION_SECRET environment variable is required")
        master = fatiha_286_derive_key(_secret)
        master_aead = ChaCha20Poly1305(master)
        return master_aead.decrypt(nonce, encrypted_key, None)
    finally:
        conn.close()


def encrypt_message(text, conversation_id):
    key = _get_conversation_key(conversation_id)
    aead = ChaCha20Poly1305(key)
    nonce = os.urandom(12)
    ciphertext = aead.encrypt(nonce, text.encode("utf-8"), None)
    return base64.b64encode(ciphertext).decode("ascii"), nonce.hex()


def decrypt_message(ciphertext_b64, nonce_hex, conversation_id):
    key = _get_conversation_key(conversation_id)
    aead = ChaCha20Poly1305(key)
    nonce = bytes.fromhex(nonce_hex)
    ciphertext = base64.b64decode(ciphertext_b64)
    return aead.decrypt(nonce, ciphertext, None).decode("utf-8")


def find_or_create_conversation(user_id, other_user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT cm1.conversation_id FROM conversation_members cm1
               JOIN conversation_members cm2 ON cm1.conversation_id = cm2.conversation_id
               JOIN conversations c ON c.id = cm1.conversation_id
               WHERE cm1.user_id = %s AND cm2.user_id = %s AND c.type = 'direct'""",
            (user_id, other_user_id),
        )
        row = cur.fetchone()
        if row:
            return row[0]

        cur.execute(
            "INSERT INTO conversations (type) VALUES ('direct') RETURNING id",
        )
        conv_id = cur.fetchone()[0]
        cur.execute(
            "INSERT INTO conversation_members (conversation_id, user_id) VALUES (%s, %s), (%s, %s)",
            (conv_id, user_id, conv_id, other_user_id),
        )
        conn.commit()
        return conv_id
    finally:
        conn.close()


def get_conversations(user_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT c.id, c.type, c.name, c.created_at,
                      (SELECT m.created_at FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_msg_time,
                      (SELECT m.content_encrypted FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_encrypted,
                      (SELECT m.content_nonce FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1) as last_nonce
               FROM conversations c
               JOIN conversation_members cm ON cm.conversation_id = c.id
               WHERE cm.user_id = %s
               ORDER BY COALESCE(
                   (SELECT m.created_at FROM messages m WHERE m.conversation_id = c.id ORDER BY m.created_at DESC LIMIT 1),
                   c.created_at
               ) DESC""",
            (user_id,),
        )
        convs = []
        for row in cur.fetchall():
            conv_id = row[0]

            cur.execute(
                """SELECT u.id, u.username, u.display_name, u.last_seen
                   FROM users u
                   JOIN conversation_members cm ON cm.user_id = u.id
                   WHERE cm.conversation_id = %s AND u.id != %s""",
                (conv_id, user_id),
            )
            members = [{"id": m[0], "username": m[1], "display_name": m[2], "last_seen": m[3].isoformat() if m[3] else None} for m in cur.fetchall()]

            last_preview = None
            if row[5] and row[6]:
                try:
                    decrypted = decrypt_message(row[5], row[6], conv_id)
                    last_preview = decrypted[:80] + ("..." if len(decrypted) > 80 else "")
                except Exception:
                    last_preview = "[encrypted]"

            convs.append({
                "id": conv_id,
                "type": row[1],
                "name": row[2],
                "created_at": row[3].isoformat() if row[3] else None,
                "last_message_time": row[4].isoformat() if row[4] else None,
                "last_preview": last_preview,
                "members": members,
            })
        return convs
    finally:
        conn.close()


def send_message(conversation_id, sender_id, content, message_type="text",
                  attachment_filename=None, attachment_path=None, attachment_size=None,
                  attachment_type=None, silt_hash_key=None, silt_carrier_style=None, vtx_earned=0):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s",
            (conversation_id, sender_id),
        )
        if not cur.fetchone():
            return None

        encrypted, nonce = encrypt_message(content, conversation_id)

        encrypted_hash_key = None
        hash_key_nonce = None
        if silt_hash_key:
            encrypted_hash_key, hash_key_nonce = encrypt_message(silt_hash_key, conversation_id)
            encrypted_hash_key = f"{hash_key_nonce}:{encrypted_hash_key}"

        cur.execute(
            """INSERT INTO messages (conversation_id, sender_id, content_encrypted, content_nonce, message_type,
                                     attachment_filename, attachment_path, attachment_size, attachment_type,
                                     silt_hash_key, silt_carrier_style, vtx_earned)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, created_at""",
            (conversation_id, sender_id, encrypted, nonce, message_type,
             attachment_filename, attachment_path, attachment_size, attachment_type,
             encrypted_hash_key, silt_carrier_style, vtx_earned),
        )
        row = cur.fetchone()
        cur.execute("UPDATE users SET last_seen = NOW() WHERE id = %s", (sender_id,))
        conn.commit()
        return {
            "id": row[0],
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "content": content,
            "message_type": message_type,
            "created_at": row[1].isoformat(),
            "attachment_filename": attachment_filename,
            "attachment_size": attachment_size,
            "attachment_type": attachment_type,
            "silt_carrier_style": silt_carrier_style,
            "vtx_earned": float(vtx_earned) if vtx_earned else 0,
        }
    finally:
        conn.close()


def get_messages(conversation_id, user_id, before_id=None, limit=50):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM conversation_members WHERE conversation_id = %s AND user_id = %s",
            (conversation_id, user_id),
        )
        if not cur.fetchone():
            return None

        _fields = """m.id, m.sender_id, m.content_encrypted, m.content_nonce, m.created_at, m.message_type,
                     u.username, u.display_name,
                     m.attachment_filename, m.attachment_size, m.attachment_type,
                     m.silt_carrier_style, m.vtx_earned"""
        if before_id:
            cur.execute(
                f"""SELECT {_fields}
                   FROM messages m JOIN users u ON u.id = m.sender_id
                   WHERE m.conversation_id = %s AND m.id < %s
                   ORDER BY m.created_at DESC LIMIT %s""",
                (conversation_id, before_id, limit),
            )
        else:
            cur.execute(
                f"""SELECT {_fields}
                   FROM messages m JOIN users u ON u.id = m.sender_id
                   WHERE m.conversation_id = %s
                   ORDER BY m.created_at DESC LIMIT %s""",
                (conversation_id, limit),
            )

        msgs = []
        for row in cur.fetchall():
            try:
                content = decrypt_message(row[2], row[3], conversation_id)
            except Exception:
                content = "[decryption failed]"
            msg = {
                "id": row[0],
                "sender_id": row[1],
                "content": content,
                "created_at": row[4].isoformat(),
                "message_type": row[5],
                "sender_username": row[6],
                "sender_display_name": row[7],
            }
            if row[8]:
                msg["attachment_filename"] = row[8]
                msg["attachment_size"] = row[9]
                msg["attachment_type"] = row[10]
                msg["silt_carrier_style"] = row[11]
                msg["vtx_earned"] = float(row[12]) if row[12] else 0
            msgs.append(msg)

        msgs.reverse()
        return msgs
    finally:
        conn.close()
