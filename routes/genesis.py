"""
Genesis 10 — Sovereign Node Blueprint NFT Launch & Oracle
=========================================================
Routes:
  GET  /genesis              — Landing page with pitch + purchase flow
  GET  /genesis/oracle       — Oracle submission interface (auth required)
  POST /api/genesis/purchase — Buy a Genesis 10 NFT (VTX or Stripe)
  POST /api/genesis/oracle   — Submit an oracle verification event
  GET  /api/genesis/listings — Get Genesis 10 token availability
  GET  /api/genesis/oracle-history — Get user's oracle submissions
"""

import logging
import os
from datetime import datetime, timezone

from flask import Blueprint, render_template, jsonify, session, request, send_from_directory

logger = logging.getLogger(__name__)
genesis_bp = Blueprint("genesis", __name__)


def _get_genesis_listings():
    from void_engine.blueprint_nft import get_genesis_10_listings
    return get_genesis_10_listings()


def _is_genesis_holder(user_id):
    from void_engine.db_pool import get_db
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT 1 FROM token_ownership tow
               JOIN blueprint_tokens bt ON bt.id = tow.token_id
               WHERE tow.owner_id = %s AND bt.collection = 'genesis_10'
               LIMIT 1""",
            (user_id,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


@genesis_bp.route("/genesis")
def genesis_page():
    user_id = session.get("user_id")
    listings = {}
    try:
        listings = _get_genesis_listings()
    except Exception as e:
        logger.error("Failed to load genesis listings: %s", e)
        listings = {"tokens": [], "total": 10, "available": 10, "sold": 0}

    is_holder = False
    peace_balance = 0.0
    if user_id:
        try:
            is_holder = _is_genesis_holder(user_id)
        except Exception:
            pass
        try:
            from void_engine.vortex_wallet import get_peace_balance
            peace_balance = get_peace_balance(user_id)
        except Exception:
            pass

    return render_template(
        "genesis.html",
        listings=listings,
        user_id=user_id,
        username=session.get("username", ""),
        user_tier=session.get("tier", "ghost"),
        is_holder=is_holder,
        peace_balance=peace_balance,
    )


@genesis_bp.route("/genesis/oracle")
def genesis_oracle_page():
    user_id = session.get("user_id")
    if not user_id:
        from flask import redirect
        return redirect("/")

    is_holder = False
    try:
        is_holder = _is_genesis_holder(user_id)
    except Exception:
        pass

    if not is_holder:
        from flask import redirect
        return redirect("/genesis")

    history = []
    peace_balance = 0.0
    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT node_id, action_type, hdr_value, timestamp, verified, peace_minted
                   FROM genesis_oracle_events
                   WHERE user_id = %s
                   ORDER BY submitted_at DESC LIMIT 20""",
                (user_id,),
            )
            for r in cur.fetchall():
                history.append({
                    "node_id": r[0],
                    "action_type": r[1],
                    "hdr_value": float(r[2]) if r[2] else 0.0,
                    "timestamp": r[3].isoformat() if r[3] else None,
                    "verified": r[4],
                    "peace_minted": float(r[5]) if r[5] else 0.0,
                })
        finally:
            conn.close()
    except Exception as e:
        logger.error("Failed to load oracle history: %s", e)

    try:
        from void_engine.vortex_wallet import get_peace_balance
        peace_balance = get_peace_balance(user_id)
    except Exception:
        pass

    return render_template(
        "genesis_oracle.html",
        user_id=user_id,
        username=session.get("username", ""),
        is_holder=is_holder,
        history=history,
        peace_balance=peace_balance,
    )


@genesis_bp.route("/api/genesis/listings")
def api_genesis_listings():
    try:
        data = _get_genesis_listings()
        return jsonify({"ok": True, **data})
    except Exception as e:
        logger.error("Genesis listings error: %s", e)
        return jsonify({"ok": False, "error": str(e)}), 500


@genesis_bp.route("/api/genesis/purchase", methods=["POST"])
def api_genesis_purchase():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    data = request.get_json(silent=True) or {}
    token_id = data.get("token_id")
    method = data.get("method", "vtx")

    if not token_id:
        return jsonify({"error": "token_id required"}), 400

    try:
        from void_engine.blueprint_nft import purchase_token_vtx
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                "SELECT id FROM blueprint_tokens WHERE id = %s AND collection = 'genesis_10'",
                (int(token_id),),
            )
            if not cur.fetchone():
                return jsonify({"error": "Token not found in Genesis 10 collection"}), 404
        finally:
            conn.close()

        if method == "vtx":
            result = purchase_token_vtx(int(token_id), user_id)
            if result.get("success"):
                _after_purchase(int(token_id), user_id)
            return jsonify(result)
        elif method == "stripe":
            return jsonify({"error": "Stripe flow: initiate via /api/marketplace/checkout"}), 400
        else:
            return jsonify({"error": "Invalid method"}), 400
    except Exception as e:
        logger.error("Genesis purchase failed: %s", e)
        return jsonify({"error": str(e)}), 500


def _after_purchase(token_id, user_id):
    try:
        from void_engine.blueprint_nft import regenerate_leaders_md
        regenerate_leaders_md()
    except Exception as e:
        logger.error("Failed to regenerate GENESIS_LEADERS.md: %s", e)


@genesis_bp.route("/api/genesis/oracle", methods=["POST"])
def api_genesis_oracle_submit():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    try:
        if not _is_genesis_holder(user_id):
            return jsonify({"error": "Genesis 10 holder status required"}), 403
    except Exception as e:
        logger.error("Holder check failed: %s", e)
        return jsonify({"error": "Could not verify holder status"}), 500

    data = request.get_json(silent=True) or {}
    node_id = (data.get("node_id") or "").strip()
    action_type = data.get("action_type", "compost")
    hdr_value = data.get("hdr_value")
    timestamp_str = data.get("timestamp")

    if not node_id:
        return jsonify({"error": "node_id is required"}), 400
    if action_type not in ("compost", "aquaponics"):
        return jsonify({"error": "action_type must be compost or aquaponics"}), 400

    try:
        hdr_value = float(hdr_value)
    except (TypeError, ValueError):
        return jsonify({"error": "hdr_value must be a number"}), 400

    if hdr_value < 0:
        return jsonify({"error": "hdr_value must be non-negative"}), 400

    try:
        if timestamp_str:
            event_ts = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            event_ts = datetime.now(timezone.utc)
    except ValueError:
        event_ts = datetime.now(timezone.utc)

    verified = hdr_value >= 0.05
    peace_earned = 0.0
    ledger_block = None

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO genesis_oracle_events
                   (node_id, user_id, action_type, hdr_value, timestamp, verified, peace_minted, ledger_block_index)
                   VALUES (%s, %s, %s, %s, %s, %s, 0, NULL)
                   RETURNING id""",
                (node_id, user_id, action_type, hdr_value, event_ts, verified),
            )
            event_db_id = cur.fetchone()[0]
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error("Oracle event insert failed: %s", e)
        return jsonify({"error": "Failed to record oracle event"}), 500

    if verified:
        try:
            import uuid as _uuid
            event_id = f"oracle_{user_id}_{event_db_id}_{_uuid.uuid4().hex[:8]}"
            from void_engine.vortex_wallet import mint_peace
            result = mint_peace(user_id, action_type, event_id)
            if result.get("peace_earned"):
                peace_earned = result["peace_earned"]
                ledger_block = result.get("block_index")
                try:
                    conn2 = get_db()
                    try:
                        cur2 = conn2.cursor()
                        cur2.execute(
                            "UPDATE genesis_oracle_events SET peace_minted=%s, ledger_block_index=%s WHERE id=%s",
                            (peace_earned, ledger_block, event_db_id),
                        )
                        conn2.commit()
                    finally:
                        conn2.close()
                except Exception as upd_err:
                    logger.error("Oracle event peace_minted update failed (event %s): %s", event_db_id, upd_err)
        except Exception as e:
            logger.error("PEACE mint failed for oracle event %s: %s", event_db_id, e)

    try:
        from void_engine.blueprint_nft import regenerate_leaders_md
        regenerate_leaders_md()
    except Exception as regen_err:
        logger.warning("Leaders MD regeneration after oracle submission failed: %s", regen_err)

    return jsonify({
        "ok": True,
        "event_id": event_db_id,
        "verified": verified,
        "peace_minted": peace_earned,
        "hdr_value": hdr_value,
        "action_type": action_type,
        "node_id": node_id,
        "message": (
            f"+{peace_earned:.1f} PEACE minted to your wallet" if peace_earned
            else ("Submission recorded — HDR below verification threshold (0.05 required)" if not verified
                  else "Submission recorded")
        ),
    })


@genesis_bp.route("/api/genesis/oracle-history")
def api_oracle_history():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "authentication required"}), 401

    try:
        from void_engine.db_pool import get_db
        conn = get_db()
        try:
            cur = conn.cursor()
            cur.execute(
                """SELECT id, node_id, action_type, hdr_value, timestamp, verified, peace_minted
                   FROM genesis_oracle_events
                   WHERE user_id = %s
                   ORDER BY submitted_at DESC LIMIT 50""",
                (user_id,),
            )
            events = []
            for r in cur.fetchall():
                events.append({
                    "id": r[0],
                    "node_id": r[1],
                    "action_type": r[2],
                    "hdr_value": float(r[3]) if r[3] else 0.0,
                    "timestamp": r[4].isoformat() if r[4] else None,
                    "verified": r[5],
                    "peace_minted": float(r[6]) if r[6] else 0.0,
                })
            return jsonify({"ok": True, "events": events})
        finally:
            conn.close()
    except Exception as e:
        logger.error("Oracle history error: %s", e)
        return jsonify({"ok": False, "events": []}), 500


@genesis_bp.route("/genesis/download/<filename>")
def genesis_download(filename):
    allowed = {"verify_life_therm.py", "README_ORACLE.md"}
    if filename not in allowed:
        return jsonify({"error": "File not found"}), 404
    return send_from_directory("static", filename, as_attachment=True)
