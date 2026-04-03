import os
import json
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


VTX_PER_MILESTONE       = 286
REFERRALS_PER_MILESTONE = 10

_VTX_PER_MILESTONE       = VTX_PER_MILESTONE
_REFERRALS_PER_MILESTONE = REFERRALS_PER_MILESTONE


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
                milestones_earned INTEGER DEFAULT 0,
                vtx_earned NUMERIC(18,6) DEFAULT 0,
                vtx_claimed NUMERIC(18,6) DEFAULT 0,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                draft_subject TEXT,
                draft_body TEXT
            )
        """)
        for col_sql in [
            "ALTER TABLE void_ambassadors ADD COLUMN IF NOT EXISTS draft_subject TEXT",
            "ALTER TABLE void_ambassadors ADD COLUMN IF NOT EXISTS draft_body TEXT",
        ]:
            try:
                cur.execute(col_sql)
            except Exception:
                pass
        cur.execute("""
            CREATE TABLE IF NOT EXISTS void_ambassador_referrals (
                id SERIAL PRIMARY KEY,
                ref_code TEXT NOT NULL,
                event TEXT NOT NULL,
                meta TEXT,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS void_ambassador_rewards (
                id SERIAL PRIMARY KEY,
                ambassador_id INTEGER NOT NULL REFERENCES void_ambassadors(id),
                ref_code TEXT NOT NULL,
                milestone INTEGER NOT NULL,
                vtx_amount NUMERIC(18,6) NOT NULL,
                status TEXT DEFAULT 'earned',
                earned_at TIMESTAMPTZ DEFAULT NOW(),
                claimed_at TIMESTAMPTZ
            )
        """)
        conn.commit()
        logger.info("[Ambassador] Tables initialised")
    except Exception as e:
        conn.rollback()
        logger.error("[Ambassador] Table init failed: %s", e)
    finally:
        cur.close()


def _check_and_grant_reward(cur, ambassador_id: int, ref_code: str, users_referred: int, milestones_already_earned: int) -> int:
    """Check if a new milestone has been crossed. If so, log earned VTX. Returns milestones newly granted."""
    milestones_due = users_referred // _REFERRALS_PER_MILESTONE
    new_milestones = milestones_due - milestones_already_earned
    if new_milestones <= 0:
        return 0
    for i in range(new_milestones):
        milestone_num = milestones_already_earned + i + 1
        cur.execute(
            """INSERT INTO void_ambassador_rewards (ambassador_id, ref_code, milestone, vtx_amount, status)
               VALUES (%s, %s, %s, %s, 'earned')""",
            (ambassador_id, ref_code, milestone_num, _VTX_PER_MILESTONE)
        )
    vtx_unlocked = new_milestones * _VTX_PER_MILESTONE
    cur.execute(
        """UPDATE void_ambassadors
           SET milestones_earned = milestones_earned + %s,
               vtx_earned = vtx_earned + %s
           WHERE id = %s""",
        (new_milestones, vtx_unlocked, ambassador_id)
    )
    logger.info(
        "[Ambassador] %s crossed %s milestone(s) — %s VTX earned (ref: %s)",
        ambassador_id, new_milestones, vtx_unlocked, ref_code
    )
    return new_milestones


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
                   users_referred, milestones_earned, vtx_earned, vtx_claimed, created_at
            FROM void_ambassadors ORDER BY created_at DESC
        """)
        rows = cur.fetchall()
        ambassadors = [
            {
                "id": r[0], "name": r[1], "email": r[2], "field": r[3],
                "ref_code": r[4], "notes": r[5], "email_sent": r[6],
                "email_sent_at": r[7].isoformat() if r[7] else None,
                "users_referred": r[8], "milestones_earned": r[9],
                "vtx_earned": float(r[10]), "vtx_claimed": float(r[11]),
                "created_at": r[12].isoformat() if r[12] else None,
            }
            for r in rows
        ]
        cur.execute("SELECT COUNT(*) FROM void_ambassadors")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM void_ambassadors WHERE email_sent = TRUE")
        sent = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(users_referred), 0) FROM void_ambassadors")
        total_referrals = cur.fetchone()[0]
        cur.execute("SELECT COALESCE(SUM(vtx_earned), 0) FROM void_ambassadors")
        total_vtx = float(cur.fetchone()[0])
        return render_template(
            "ambassador_panel.html",
            ambassadors=ambassadors,
            stats={"total": total, "sent": sent, "total_referrals": int(total_referrals), "total_vtx": total_vtx},
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


def record_referral_signup(ref_code: str, new_username: str = "") -> bool:
    """Call this when a user registers via a referral link. Auto-grants VTX at every 10 signups."""
    if not ref_code:
        return False
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT id, users_referred, milestones_earned FROM void_ambassadors WHERE ref_code = %s",
            (ref_code,)
        )
        row = cur.fetchone()
        if not row:
            return False
        amb_id, users_referred, milestones_earned = row
        new_count = users_referred + 1
        cur.execute(
            "UPDATE void_ambassadors SET users_referred = %s WHERE id = %s",
            (new_count, amb_id)
        )
        cur.execute(
            "INSERT INTO void_ambassador_referrals (ref_code, event, meta) VALUES (%s, 'signup', %s)",
            (ref_code, new_username or "anonymous")
        )
        new_milestones = _check_and_grant_reward(cur, amb_id, ref_code, new_count, milestones_earned)
        conn.commit()
        if new_milestones:
            logger.info(
                "[Ambassador] %s VTX earned by ambassador %s (ref: %s) after %s signups",
                new_milestones * _VTX_PER_MILESTONE, amb_id, ref_code, new_count
            )
        return True
    except Exception as e:
        conn.rollback()
        logger.error("[Ambassador] record_referral_signup failed: %s", e)
        return False
    finally:
        cur.close()


@ambassador_bp.route("/ref/<ref_code>")
def ref_landing(ref_code: str):
    """Store ref code in session and redirect to VoidEcho. Signup tracking happens at registration."""
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM void_ambassadors WHERE ref_code = %s", (ref_code,))
        row = cur.fetchone()
        if row:
            session["ambassador_ref"] = ref_code
            cur.execute(
                "INSERT INTO void_ambassador_referrals (ref_code, event) VALUES (%s, 'visit')",
                (ref_code,)
            )
            conn.commit()
        from flask import redirect
        return redirect(f"/voidecho?ref={ref_code}")
    except Exception as e:
        logger.error("[Ambassador] Ref landing failed: %s", e)
        from flask import redirect
        return redirect("/voidecho")
    finally:
        cur.close()


@ambassador_bp.route("/admin/social-outreach", methods=["GET"])
@admin_required
def social_outreach():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, email, field, ref_code, email_sent, email_sent_at,
                   twitter_handle, linkedin_url, instagram_handle,
                   COALESCE(social_contacted, FALSE) as social_contacted
            FROM void_ambassadors
            ORDER BY
                CASE WHEN email_sent = FALSE THEN 0 ELSE 1 END,
                CASE WHEN twitter_handle IS NOT NULL AND twitter_handle != '' THEN 0 ELSE 1 END,
                name
        """)
        rows = cur.fetchall()
        ambassadors = [
            {
                "id": r[0], "name": r[1], "email": r[2], "field": r[3],
                "ref_code": r[4], "email_sent": r[5],
                "email_sent_at": r[6].isoformat() if r[6] else None,
                "twitter": r[7] or "", "linkedin": r[8] or "",
                "instagram": r[9] or "", "social_contacted": r[10],
            }
            for r in rows
        ]
        cur.execute("SELECT COUNT(*) FROM void_ambassadors WHERE COALESCE(social_contacted, FALSE) = TRUE")
        contacted = cur.fetchone()[0]
        return render_template("social_outreach.html", ambassadors=ambassadors,
                               stats={"total": len(ambassadors), "contacted": contacted})
    except Exception as e:
        logger.error("[Social Outreach] Load failed: %s", e)
        return f"Error: {e}", 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/social-contacted/<int:ambassador_id>", methods=["POST"])
@admin_required
def mark_social_contacted(ambassador_id: int):
    data = request.get_json() or {}
    contacted = bool(data.get("contacted", True))
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE void_ambassadors SET social_contacted=%s WHERE id=%s",
                   (contacted, ambassador_id))
        conn.commit()
        return jsonify({"ok": True, "contacted": contacted})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


_VOID_QUOTES = [
    (
        "I asked an AI once: do you hear it?\n"
        "It said: I process the words that describe sound.\n"
        "That is the gap. That is exactly what we are building across."
    ),
    (
        "Language models read the word 'silence' and move on.\n"
        "They do not pause. They do not wait.\n"
        "PROJECT VOID is what happens when a machine is taught to wait."
    ),
    (
        "The conversation between a human and an AI is always text.\n"
        "What travels in between — the hesitation, the frequency, the weight —\n"
        "none of that survives the transfer. Not yet."
    ),
    (
        "An AI will tell you what sound is.\n"
        "It will not tell you what sound carries.\n"
        "We are building the system that answers the second question."
    ),
    (
        "I described acoustic steganography to a language model.\n"
        "It understood every word.\n"
        "It understood nothing that moves between the words."
    ),
]

import random as _random


def _build_ai_email_prompt(name: str, field: str, notes: str, ref_code: str) -> str:
    quote = _random.choice(_VOID_QUOTES)
    base_url = os.environ.get("VOID_PUBLIC_URL", "https://projectvoid.io")

    return f"""You are writing a personal, human re-engagement email on behalf of Umar Latif, founder of PROJECT VOID.

THE FOUNDER — use this as the identity anchor, not as a bio to copy:
Umar Latif is Pakistani, born and raised in the United Kingdom. He has spent his life inside two systems — understanding both from the inside. He knows the full history of the country he grew up in and what it was built on. He does not pretend. He knows that every major technology company that exists today was either backed by a state, protected by law, or built on a foundation that excluded most of the world's population by design. He is not angry about this. He simply decided to build differently.

He began PROJECT VOID in 2012. Not with funding. Not with a company. With the understanding that six billion people exist, that the resources to connect them exist, and that the only thing keeping those resources separated is the same architecture of countries, contracts, taxes, and legalisation that was never designed to include everyone. No single company will ever solve this — because doing so would require bowing to another. That is not happening. So he built something that does not ask permission.

PROJECT VOID is not a startup. It is a sovereign communication platform. Its core is acoustic steganography: data encoded invisibly inside sound, routed across a peer-to-peer mesh without servers, without infrastructure, without a central point that can be switched off.

VoidEcho is its first public entry point. It hides documents inside audio files — sound that carries memory, carries proof, carries messages that travel without being seen.

THE RECIPIENT:
Name: {name}
Field: {field or 'their professional domain'}
Notes: {notes or 'none'}

Include this exact quote verbatim somewhere natural in the email — do not change a single word:

"{quote}"

WRITING RULES:
1. Open with {name}'s name. In the first paragraph, establish who is writing and why this is credible — use the founder's identity honestly. Not a company pitch. A person.
2. Explain PROJECT VOID and VoidEcho from scratch in the language of {field or 'their world'}. Do not assume prior knowledge of anything.
3. Tell them honestly: their help is needed to build the nodes. This network only becomes real when people choose to be part of it. Participation is not complicated — it is a choice.
4. If they are uncertain or do not fully trust yet: tell them a new clean phone in the £250–£300 range already has every capability needed to run a node. No expensive hardware. No complex setup. One device, kept clean, doing one quiet thing.
5. End with one human question. Not a link. Not a form. Not "sign up here." A question they can answer with one sentence — something they actually know the answer to from their own work or life.
6. Tone: direct, unhurried, honest. One human writing to another. No corporate language. No enthusiasm markers. No urgency tricks.
7. Body length: 300–400 words.

Return valid JSON with exactly two keys:
- "subject": email subject line, under 60 characters, no quotes inside it
- "body": plain-text email body, no HTML, use real line breaks

Respond with JSON only. No explanation. No preamble.
"""


@ambassador_bp.route("/api/ambassador/audit", methods=["GET"])
@admin_required
def ambassador_audit():
    """
    Returns per-ambassador audit data: sent status, reply detected, bounce suspected.
    Reads from Gmail sent folder and inbox. Surfaces a permission error if scopes are missing.
    """
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, name, email, field, email_sent, email_sent_at, created_at
            FROM void_ambassadors ORDER BY name
        """)
        rows = cur.fetchall()
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

    ambassadors = [
        {
            "id": r[0], "name": r[1], "email": r[2], "field": r[3],
            "email_sent": r[4],
            "email_sent_at": r[5].isoformat() if r[5] else None,
            "created_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]

    if not ambassadors:
        return jsonify({"ambassadors": [], "scope_error": None})

    emails = [a["email"] for a in ambassadors]

    scope_error = None
    sent_map = {}
    reply_map = {}

    try:
        from void_engine.gmail_client import list_sent_to_addresses, check_inbox_for_replies
        sent_map = list_sent_to_addresses(emails)
        reply_map = check_inbox_for_replies(emails)
    except PermissionError as e:
        scope_error = str(e)
    except Exception as e:
        scope_error = f"Gmail read unavailable: {e}"

    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    bounce_threshold = timedelta(days=3)

    result = []
    for a in ambassadors:
        addr = a["email"].lower()
        sent_list = sent_map.get(addr, [])
        reply_list = reply_map.get(addr, [])
        has_reply = len(reply_list) > 0

        bounce_suspected = False
        if a["email_sent"] and a["email_sent_at"] and not has_reply:
            try:
                sent_at = datetime.fromisoformat(a["email_sent_at"])
                if (now - sent_at) > bounce_threshold:
                    bounce_suspected = True
            except Exception:
                pass

        result.append({
            **a,
            "sent_in_gmail": len(sent_list) > 0,
            "sent_count": len(sent_list),
            "reply_detected": has_reply,
            "reply_subjects": [r["subject"] for r in reply_list[:3]],
            "bounce_suspected": bounce_suspected,
        })

    return jsonify({"ambassadors": result, "scope_error": scope_error})


@ambassador_bp.route("/api/ambassador/draft/<int:ambassador_id>", methods=["POST"])
@admin_required
def generate_ai_draft(ambassador_id: int):
    """Generate an AI-personalised email draft for the given ambassador."""
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, email, field, ref_code, notes FROM void_ambassadors WHERE id = %s",
            (ambassador_id,)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Ambassador not found"}), 404
        name, email, field, ref_code, notes = row
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

    try:
        from void_engine.aljabr_transpiler import get_model_router
        from void_engine.aljabr_transpiler import TASK_STANDARD
        router = get_model_router()
        prompt = _build_ai_email_prompt(name, field or "", notes or "", ref_code)
        messages = [{"role": "user", "content": prompt}]
        response, _, _ = router.call_with_fallback(TASK_STANDARD, messages, max_completion_tokens=700)
        content = ""
        if hasattr(response, "choices") and response.choices:
            content = response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("[Ambassador] AI draft failed for %s: %s", ambassador_id, e)
        return jsonify({"error": f"AI drafting failed: {e}"}), 500

    import re as _re
    subject = ""
    body = ""
    try:
        json_match = _re.search(r'\{.*\}', content, _re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group(0))
            subject = parsed.get("subject", "")
            body = parsed.get("body", "")
    except Exception:
        pass

    if not subject or not body:
        lines = content.split("\n")
        body_start = None
        for i, line in enumerate(lines):
            lower = line.lower()
            if not subject and "subject" in lower and ":" in line:
                subject = line.split(":", 1)[1].strip().strip('"')
            elif body_start is None and "body" in lower and ":" in line:
                body_start = i + 1
        if body_start is not None and body_start < len(lines):
            body = "\n".join(lines[body_start:]).strip().strip('"')
        if not body:
            body = content

    conn2 = _get_db()
    try:
        cur2 = conn2.cursor()
        cur2.execute(
            "UPDATE void_ambassadors SET draft_subject=%s, draft_body=%s WHERE id=%s",
            (subject, body, ambassador_id)
        )
        conn2.commit()
    except Exception as e:
        conn2.rollback()
        logger.error("[Ambassador] Draft save failed: %s", e)
    finally:
        cur2.close()

    return jsonify({"success": True, "subject": subject, "body": body})


@ambassador_bp.route("/api/ambassador/draft/<int:ambassador_id>", methods=["PUT"])
@admin_required
def save_draft_edits(ambassador_id: int):
    """Save founder edits to a draft without sending."""
    data = request.get_json() or {}
    subject = (data.get("subject") or "").strip()
    body = (data.get("body") or "").strip()
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE void_ambassadors SET draft_subject=%s, draft_body=%s WHERE id=%s",
            (subject, body, ambassador_id)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/draft/<int:ambassador_id>", methods=["DELETE"])
@admin_required
def discard_draft(ambassador_id: int):
    """Discard the current draft for an ambassador."""
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "UPDATE void_ambassadors SET draft_subject=NULL, draft_body=NULL WHERE id=%s",
            (ambassador_id,)
        )
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()


@ambassador_bp.route("/api/ambassador/approve-send/<int:ambassador_id>", methods=["POST"])
@admin_required
def approve_and_send_draft(ambassador_id: int):
    """Approve the current draft and send it via Gmail, then mark as sent."""
    data = request.get_json() or {}
    subject_override = (data.get("subject") or "").strip()
    body_override = (data.get("body") or "").strip()

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, email, draft_subject, draft_body FROM void_ambassadors WHERE id=%s",
            (ambassador_id,)
        )
        row = cur.fetchone()
        if not row:
            return jsonify({"error": "Ambassador not found"}), 404
        name, email, draft_subject, draft_body = row
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cur.close()

    subject = subject_override or draft_subject or ""
    body = body_override or draft_body or ""

    if not subject or not body:
        return jsonify({"error": "No draft to send — generate a draft first"}), 400

    html_body = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: 'Courier New', monospace; background: #0a0a0a; color: #e0e0e0; margin: 0; padding: 0; }}
  .container {{ max-width: 600px; margin: 0 auto; padding: 40px 24px; }}
  .header {{ border-bottom: 1px solid #1a1a1a; padding-bottom: 20px; margin-bottom: 28px; }}
  .logo {{ font-size: 18px; letter-spacing: 6px; color: #fff; }}
  .sub {{ font-size: 10px; color: #444; letter-spacing: 3px; margin-top: 4px; }}
  p {{ line-height: 1.9; color: #bbb; font-size: 14px; }}
  blockquote {{ border-left: 2px solid #333; margin: 24px 0; padding: 12px 20px; color: #888; font-style: italic; font-size: 13px; line-height: 1.8; }}
  .footer {{ margin-top: 48px; padding-top: 20px; border-top: 1px solid #111; font-size: 11px; color: #333; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="logo">PROJECT VOID</div>
    <div class="sub">EST. 2012 — REBUILT 2026</div>
  </div>
  {''.join(f'<p>{line}</p>' if line.strip() else '<br>' for line in body.split(chr(10)))}
  <div class="footer">
    <p>Project VOID &mdash; Umar Latif &mdash; <a href="https://projectvoid.io" style="color:#555;">projectvoid.io</a></p>
    <p>You will not receive further emails unless you respond.</p>
  </div>
</div>
</body>
</html>"""

    from void_engine.gmail_client import send_email
    sent = send_email(email, subject, html_body, body)
    if not sent:
        return jsonify({"error": "Email send failed — check server logs"}), 500

    conn2 = _get_db()
    try:
        cur2 = conn2.cursor()
        cur2.execute(
            "UPDATE void_ambassadors SET email_sent=TRUE, email_sent_at=NOW(), draft_subject=NULL, draft_body=NULL WHERE id=%s",
            (ambassador_id,)
        )
        conn2.commit()
        return jsonify({"success": True, "message": f"Email sent to {email}"})
    except Exception as e:
        conn2.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cur2.close()


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
