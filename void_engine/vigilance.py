import os
from decimal import Decimal
from datetime import datetime, timezone
from void_engine.db_pool import get_db


def _get_db():
    return get_db()


BOUNTY_RATES = {
    "critical": Decimal("50"),
    "high": Decimal("25"),
    "medium": Decimal("10"),
    "low": Decimal("5"),
    "cosmetic": Decimal("1"),
}

VALID_SEVERITIES = list(BOUNTY_RATES.keys())
VALID_CATEGORIES = ["security", "crash", "ui", "logic", "performance", "cosmetic"]
VALID_STATUSES = ["pending", "verified", "rewarded", "rejected", "duplicate"]
VALID_ACTIONS = ["verify", "reject", "duplicate"]


def submit_report(reporter_id, title, description, severity, category=None, steps=None):
    if severity not in VALID_SEVERITIES:
        return {"error": f"Invalid severity. Must be one of: {', '.join(VALID_SEVERITIES)}"}
    if category and category not in VALID_CATEGORIES:
        return {"error": f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}"}

    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO vigilance_reports (reporter_id, title, description, severity, category, steps_to_reproduce)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING id, created_at""",
            (reporter_id, title.strip(), description.strip(), severity, category, steps),
        )
        row = cur.fetchone()
        conn.commit()
        return {
            "id": row[0],
            "title": title.strip(),
            "severity": severity,
            "category": category,
            "status": "pending",
            "created_at": row[1].isoformat() if row[1] else None,
            "bounty_potential": float(BOUNTY_RATES.get(severity, 0)),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_reports(status_filter=None, reporter_id=None, limit=50):
    conn = _get_db()
    try:
        cur = conn.cursor()
        query = """SELECT vr.id, vr.title, vr.severity, vr.category, vr.status,
                          vr.vtx_reward, vr.created_at, vr.reviewed_at,
                          u.username as reporter_username, vr.reporter_id,
                          vr.description, vr.steps_to_reproduce, vr.admin_notes
                   FROM vigilance_reports vr
                   JOIN users u ON u.id = vr.reporter_id"""
        params = []
        clauses = []
        if status_filter:
            clauses.append("vr.status = %s")
            params.append(status_filter)
        if reporter_id:
            clauses.append("vr.reporter_id = %s")
            params.append(reporter_id)
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY vr.created_at DESC LIMIT %s"
        params.append(limit)

        cur.execute(query, tuple(params))
        reports = []
        for row in cur.fetchall():
            reports.append({
                "id": row[0],
                "title": row[1],
                "severity": row[2],
                "category": row[3],
                "status": row[4],
                "vtx_reward": float(row[5]) if row[5] else 0,
                "created_at": row[6].isoformat() if row[6] else None,
                "reviewed_at": row[7].isoformat() if row[7] else None,
                "reporter_username": row[8],
                "reporter_id": row[9],
                "description": row[10],
                "steps_to_reproduce": row[11],
                "admin_notes": row[12],
            })
        return reports
    finally:
        conn.close()


def get_report(report_id):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT vr.id, vr.title, vr.description, vr.severity, vr.category,
                      vr.steps_to_reproduce, vr.status, vr.admin_notes, vr.vtx_reward,
                      vr.created_at, vr.reviewed_at, vr.reporter_id, vr.reviewed_by,
                      u.username as reporter_username,
                      ru.username as reviewer_username
               FROM vigilance_reports vr
               JOIN users u ON u.id = vr.reporter_id
               LEFT JOIN users ru ON ru.id = vr.reviewed_by
               WHERE vr.id = %s""",
            (report_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return {
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "severity": row[3],
            "category": row[4],
            "steps_to_reproduce": row[5],
            "status": row[6],
            "admin_notes": row[7],
            "vtx_reward": float(row[8]) if row[8] else 0,
            "created_at": row[9].isoformat() if row[9] else None,
            "reviewed_at": row[10].isoformat() if row[10] else None,
            "reporter_id": row[11],
            "reviewed_by": row[12],
            "reporter_username": row[13],
            "reviewer_username": row[14],
        }
    finally:
        conn.close()


def review_report(report_id, admin_id, action, admin_notes=None):
    if action not in VALID_ACTIONS:
        return {"error": f"Invalid action. Must be one of: {', '.join(VALID_ACTIONS)}"}

    report = get_report(report_id)
    if not report:
        return {"error": "Report not found"}
    if report["status"] in ("rewarded", "rejected", "duplicate"):
        return {"error": f"Report already {report['status']}"}

    conn = _get_db()
    try:
        cur = conn.cursor()
        now = datetime.now(timezone.utc)

        if action == "verify":
            severity = report["severity"]
            reward = BOUNTY_RATES.get(severity, Decimal("1"))

            cur.execute(
                """UPDATE vigilance_reports
                   SET status = 'verified', admin_notes = %s, vtx_reward = %s,
                       reviewed_at = %s, reviewed_by = %s
                   WHERE id = %s""",
                (admin_notes, reward, now, admin_id, report_id),
            )
            conn.commit()

            try:
                from void_engine.vortex_wallet import mint_vigilance
                block = mint_vigilance(report["reporter_id"], reward, report_id)

                cur2 = conn.cursor()
                cur2.execute("UPDATE vigilance_reports SET status = 'rewarded' WHERE id = %s", (report_id,))
                conn.commit()
            except Exception:
                conn.rollback()
                return {
                    "report_id": report_id,
                    "action": "verified",
                    "status": "verified",
                    "vtx_reward": float(reward),
                    "block": None,
                    "mint_error": "VTX minting failed — report verified but reward pending",
                    "reporter_username": report["reporter_username"],
                }

            return {
                "report_id": report_id,
                "action": "verified",
                "status": "rewarded",
                "vtx_reward": float(reward),
                "block": block,
                "reporter_username": report["reporter_username"],
            }

        elif action == "reject":
            cur.execute(
                """UPDATE vigilance_reports
                   SET status = 'rejected', admin_notes = %s,
                       reviewed_at = %s, reviewed_by = %s
                   WHERE id = %s""",
                (admin_notes, now, admin_id, report_id),
            )
            conn.commit()
            return {"report_id": report_id, "action": "rejected", "status": "rejected"}

        elif action == "duplicate":
            cur.execute(
                """UPDATE vigilance_reports
                   SET status = 'duplicate', admin_notes = %s,
                       reviewed_at = %s, reviewed_by = %s
                   WHERE id = %s""",
                (admin_notes, now, admin_id, report_id),
            )
            conn.commit()
            return {"report_id": report_id, "action": "duplicate", "status": "duplicate"}

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_leaderboard(limit=20):
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            """SELECT u.username, u.id,
                      COUNT(vr.id) as report_count,
                      COUNT(CASE WHEN vr.status = 'rewarded' THEN 1 END) as rewarded_count,
                      COALESCE(SUM(CASE WHEN vr.status = 'rewarded' THEN vr.vtx_reward ELSE 0 END), 0) as total_vtx
               FROM vigilance_reports vr
               JOIN users u ON u.id = vr.reporter_id
               GROUP BY u.id, u.username
               ORDER BY total_vtx DESC, rewarded_count DESC
               LIMIT %s""",
            (limit,),
        )
        entries = []
        for i, row in enumerate(cur.fetchall(), 1):
            entries.append({
                "rank": i,
                "username": row[0],
                "user_id": row[1],
                "report_count": row[2],
                "rewarded_count": row[3],
                "total_vtx": float(row[4]),
            })
        return entries
    finally:
        conn.close()


def get_stats():
    conn = _get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM vigilance_reports")
        total = cur.fetchone()[0]
        cur.execute("SELECT status, COUNT(*) FROM vigilance_reports GROUP BY status")
        by_status = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT severity, COUNT(*) FROM vigilance_reports GROUP BY severity")
        by_severity = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT COALESCE(SUM(vtx_reward), 0) FROM vigilance_reports WHERE status = 'rewarded'")
        total_vtx_paid = float(cur.fetchone()[0])
        return {
            "total_reports": total,
            "by_status": by_status,
            "by_severity": by_severity,
            "total_vtx_paid": total_vtx_paid,
            "bounty_rates": {k: float(v) for k, v in BOUNTY_RATES.items()},
        }
    finally:
        conn.close()
