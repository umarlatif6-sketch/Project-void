import os
import logging
import secrets
import string
from datetime import datetime, timezone

from flask import Blueprint, request, jsonify, render_template, session
from routes.auth import admin_required, login_required
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)

ambassador_bp = Blueprint("ambassador", __name__)


def _get_db():
    return get_db()


def init_ambassador_tables():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS void_ambassadors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                field TEXT,
                ref_code TEXT NOT NULL UNIQUE,
                notes TEXT,
                email_sent BOOLEAN DEFAULT FALSE,
                email_sent_at TIMESTAMPTZ,
                users_referred INTEGER DEFAULT 0,
                reward_triggered INTEGER DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS void_ambassador_referrals (
                id SERIAL PRIMARY KEY,
                ref_code TEXT NOT NULL,
                event TEXT NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        conn.commit()
        logger.info("[Ambassador] Tables initialised")
    except Exception as e:
        conn.rollback()
        logger.error("[Ambassador] Table init failed: %s", e)
    finally:
        cur.close()


def _generate_ref_code(name: str) -> str:
    initials = "".join(w[0].upper() for w in name.split() if w)[:3]
    suffix = "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(5))
    return f"VOID-{initials}-{suffix}"


def _build_ambassador_email_html(name: str, ref_code: str, field: str) -> str:
    base_url = os.environ.get("VOID_PUBLIC_URL", "https://projectvoid.io")
    signup_url = f"{base_url}/voidecho?ref={ref_code}"
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 0; }}
  .container {{ max-width: 600px; margin: 0 auto; padding: 40px 24px; }}
  .header {{ border-bottom: 1px solid #333; padding-bottom: 24px; margin-bottom: 32px; }}
  .logo {{ font-size: 22px; letter-spacing: 6px; color: #fff; }}
  .sub {{ font-size: 11px; color: #666; letter-spacing: 3px; margin-top: 6px; }}
  h2 {{ font-size: 18px; color: #fff; font-weight: normal; margin-bottom: 16px; }}
  p {{ line-height: 1.8; color: #bbb; font-size: 14px; }}
  .ref-block {{ background: #111; border: 1px solid #333; padding: 20px 24px; margin: 28px 0; border-radius: 4px; }}
  .ref-label {{ font-size: 11px; color: #666; letter-spacing: 2px; margin-bottom: 8px; }}
  .ref-code {{ font-size: 22px; letter-spacing: 4px; color: #fff; }}
  .cta {{ display: inline-block; margin-top: 20px; padding: 12px 28px; background: #fff; color: #0a0a0a;
          text-decoration: none; font-size: 13px; letter-spacing: 2px; font-weight: bold; }}
  .footer {{ margin-top: 48px; padding-top: 24px; border-top: 1px solid #222; font-size: 11px; color: #444; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">PROJECT VOID</div>
    <div class="sub">A SOVEREIGN COMMUNICATION PLATFORM</div>
  </div>
  <h2>Hello {name},</h2>
  <p>
    You are being invited into an early layer of something that has been building quietly since 2012.
  </p>
  <p>
    Project VOID is a sovereign communication platform — combining acoustic steganography, mesh networking,
    and AI that receives rather than responds. Its first public entry point is <strong>VoidEcho</strong>:
    a tool that hides documents inside sound. Files carried invisibly in music. Memory anchors. Secure carriers.
  </p>
  <p>
    We are reaching out to a small number of people in {field or 'relevant fields'} who understand why
    this matters — not to pitch, but to introduce.
  </p>
  <p>
    Your unique referral code below gives you a personal link to share. Every person who discovers VOID
    through you is recorded in our ledger.
  </p>
  <div class="ref-block">
    <div class="ref-label">YOUR AMBASSADOR CODE</div>
    <div class="ref-code">{ref_code}</div>
  </div>
  <p>Your personal entry link:</p>
  <p><a href="{signup_url}" style="color:#aaa;">{signup_url}</a></p>
  <a href="{signup_url}" class="cta">ENTER THE VOID</a>
  <div class="footer">
    <p>This email was sent because you were identified as someone whose work aligns with what VOID is building.
    You will not be contacted again unless you choose to respond.</p>
    <p>Project VOID &mdash; Est. 2012 &mdash; Rebuilt 2026</p>
  </div>
</div>
</body>
</html>"""


def _build_ambassador_email_text(name: str, ref_code: str, field: str) -> str:
    base_url = os.environ.get("VOID_PUBLIC_URL", "https://projectvoid.io")
    signup_url = f"{base_url}/voidecho?ref={ref_code}"
    return f"""PROJECT VOID — A SOVEREIGN COMMUNICATION PLATFORM

Hello {name},

You are being invited into an early layer of something that has been building quietly since 2012.

Project VOID is a sovereign communication platform — combining acoustic steganography, mesh networking, and AI that receives rather than responds. Its first public entry point is VoidEcho: a tool that hides documents inside sound. Files carried invisibly in music. Memory anchors. Secure carriers.

We are reaching out to a small number of people in {field or 'relevant fields'} who understand why this matters — not to pitch, but to introduce.

YOUR AMBASSADOR CODE: {ref_code}

Your personal entry link:
{signup_url}

This email was sent because you were identified as someone whose work aligns with what VOID is building. You will not be contacted again unless you choose to respond.

Project VOID — Est. 2012 — Rebuilt 2026
"""


@ambassador_bp.route("/admin/ambassadors", methods=["GET"])
@admin_required
def ambassador_panel():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, email, field, ref_code, notes, email_sent, email_sent_at,
                   users_referred, reward_triggered, created_at
            FROM void_ambassadors ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        ambassadors = [
            {
                "id": r[0], "name": r[1], "email": r[2], "field": r[3],
                "ref_code": r[4], "notes": r[5], "email_sent": r[6],
                "email_sent_at": r[7].isoformat() if r[7] else None,
                "users_referred": r[8], "reward_triggered": r[9],
                "created_at": r[10].isoformat() if r[10] else None,
            }
            for r in rows
        ]
        cur.execute("SELECT COUNT(*) FROM void_ambassadors")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM void_ambassadors WHERE email_sent = TRUE")
        sent = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(users_referred), 0) FROM void_ambassadors")
        total_referrals = cur.fetchone()[0]
        return render_template(
            "ambassador_panel.html",
            ambassadors=ambassadors,
            stats={"total": total, "sent": sent, "total_referrals": total_referrals},
        )
    except Exception as e:
        logger.error("[Ambassador] Panel load failed: %s", e)
        return f"Error loading ambassador panel: {e}", 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/add", methods=["POST"])
@admin_required
def add_ambassador():
    data = request.get_json() or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    field = (data.get("field") or "").strip()
    notes = (data.get("notes") or "").strip()

    if not name or not email:
        return jsonify({"error": "Name and email are required"}), 400

    ref_code = _generate_ref_code(name)
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO void_ambassadors (name, email, field, ref_code, notes)
               VALUES (%s, %s, %s, %s, %s) RETURNING id, ref_code""",
            (name, email, field, ref_code, notes)
        )
        row = cur.fetchone()
        conn.commit()
        return jsonify({"success": True, "id": row[0], "ref_code": row[1]})
    except Exception as e:
        conn.rollback()
        if "unique" in str(e).lower():
            return jsonify({"error": "An ambassador with that email already exists"}), 409
        logger.error("[Ambassador] Add failed: %s", e)
        return jsonify({"error": "Failed to add ambassador"}), 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/send/<int:ambassador_id>", methods=["POST"])
@admin_required
def send_ambassador_email(ambassador_id: int):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, email, field, ref_code, email_sent FROM void_ambassadors WHERE id = %s",
            (ambassador_id,)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Ambassador not found"}), 404

        name, email, field, ref_code, already_sent = row

        from void_engine.gmail_client import send_email
        html = _build_ambassador_email_html(name, ref_code, field)
        text = _build_ambassador_email_text(name, ref_code, field)
        sent = send_email(email, "An Invitation into Project VOID", html, text)

        if sent:
            cur.execute(
                "UPDATE void_ambassadors SET email_sent = TRUE, email_sent_at = NOW() WHERE id = %s",
                (ambassador_id,)
            )
            conn.commit()
            return jsonify({"success": True, "message": f"Email sent to {email}"})
        else:
            return jsonify({"error": "Email failed to send — check logs"}), 500

    except Exception as e:
        conn.rollback()
        logger.error("[Ambassador] Send failed: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/send-all", methods=["POST"])
@admin_required
def send_all_ambassador_emails():
    conn = _get_db()
    results = {"sent": 0, "failed": 0, "skipped": 0}
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, name, email, field, ref_code FROM void_ambassadors WHERE email_sent = FALSE"
        )
        rows = cur.fetchall()

        from void_engine.gmail_client import send_email

        for row in rows:
            amb_id, name, email, field, ref_code = row
            try:
                html = _build_ambassador_email_html(name, ref_code, field)
                text = _build_ambassador_email_text(name, ref_code, field)
                sent = send_email(email, "An Invitation into Project VOID", html, text)
                if sent:
                    cur.execute(
                        "UPDATE void_ambassadors SET email_sent = TRUE, email_sent_at = NOW() WHERE id = %s",
                        (amb_id,)
                    )
                    conn.commit()
                    results["sent"] += 1
                else:
                    results["failed"] += 1
            except Exception as e:
                logger.error("[Ambassador] Bulk send failed for %s: %s", email, e)
                results["failed"] += 1

        return jsonify({"success": True, **results})
    except Exception as e:
        logger.error("[Ambassador] Send-all failed: %s", e)
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/delete/<int:ambassador_id>", methods=["DELETE"])
@admin_required
def delete_ambassador(ambassador_id: int):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM void_ambassadors WHERE id = %s", (ambassador_id,))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


@ambassador_bp.route("/ref/<ref_code>")
def ref_landing(ref_code: str):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM void_ambassadors WHERE ref_code = %s", (ref_code,))
        row = cur.fetchone()
        if row:
            cur.execute(
                "INSERT INTO void_ambassador_referrals (ref_code, event) VALUES (%s, 'visit')",
                (ref_code,)
            )
            conn.commit()
        from flask import redirect, url_for
        return redirect(f"/voidecho?ref={ref_code}")
    except Exception as e:
        logger.error("[Ambassador] Ref landing failed: %s", e)
        from flask import redirect
        return redirect("/voidecho")
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/stats", methods=["GET"])
@admin_required
def ambassador_stats():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM void_ambassadors")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM void_ambassadors WHERE email_sent = TRUE")
        sent = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(users_referred), 0) FROM void_ambassadors")
        referrals = cur.fetchone()[0]
        return jsonify({"total": total, "sent": sent, "total_referrals": int(referrals)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()
