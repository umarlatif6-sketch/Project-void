"""
Codon Distillation Engine — Routes
====================================
Blueprint at /codon-distil

Routes:
  GET  /codon-distil                  — upload/paste interface
  POST /api/codon-distil/process      — start background processing job
  GET  /codon-distil/stream/<job_id>  — SSE progress stream
  POST /api/codon-distil/seal         — founder seals a codon into the Chronicle
"""

import json
import logging
import os
import threading
import time
import uuid

from flask import Blueprint, Response, jsonify, redirect, render_template, request, session

from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
from void_engine.codon_distil import (
    chunk_text,
    extract_moments,
    init_codon_distil_tables,
    map_to_glyphs,
    score_codon,
    seal_to_chronicle,
)
from void_engine.db_pool import get_db

logger = logging.getLogger(__name__)

codon_distil_bp = Blueprint("codon_distil", __name__)

MAX_TEXT_BYTES = 10 * 1024 * 1024

_jobs: dict[str, dict] = {}
_jobs_lock = threading.Lock()
_JOB_TTL_SECONDS = 3600


def _evict_stale_jobs():
    """Remove completed/errored jobs older than TTL from in-memory store."""
    cutoff = time.time() - _JOB_TTL_SECONDS
    with _jobs_lock:
        stale = [
            jid for jid, j in _jobs.items()
            if j.get("status") in ("complete", "error", "cancelled")
            and j.get("_finished_at", 0) < cutoff
        ]
        for jid in stale:
            del _jobs[jid]


def _init_tables():
    try:
        conn = get_db()
        init_codon_distil_tables(conn)
        conn.close()
    except Exception as e:
        logger.warning("Codon distil table init deferred: %s", e)


try:
    _init_tables()
except Exception:
    pass


def _get_openai_client():
    api_key = (
        os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
    )
    base_url = (
        os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        or os.environ.get("OPENAI_API_BASE")
        or os.environ.get("OPENAI_BASE_URL")
    )
    from openai import OpenAI
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _create_job(job_id: str, total_chunks: int):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO codon_distil_jobs (job_id, status, total_chunks, done_chunks)
                   VALUES (%s, 'running', %s, 0)
                   ON CONFLICT (job_id) DO UPDATE SET status='running', total_chunks=%s, done_chunks=0""",
                (job_id, total_chunks, total_chunks),
            )
        conn.commit()
    except Exception as e:
        logger.error("_create_job error: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _update_job(job_id: str, done_chunks: int, status: str = "running"):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE codon_distil_jobs SET done_chunks=%s, status=%s WHERE job_id=%s",
                (done_chunks, status, job_id),
            )
        conn.commit()
    except Exception as e:
        logger.error("_update_job error: %s", e)
        conn.rollback()
    finally:
        conn.close()


def _save_codon(job_id: str, codon: dict):
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO codon_distil_results
                   (job_id, entity, condition, action, glyph_seq, story_excerpt,
                    resonance, clarity, story_score, total_score, al_jabr_hash)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (
                    job_id,
                    codon["entity"],
                    codon["condition"],
                    codon["action"],
                    codon["glyph_seq"],
                    codon["story_excerpt"],
                    codon["resonance"],
                    codon["clarity"],
                    codon["story_score"],
                    codon["total_score"],
                    codon["al_jabr_hash"],
                ),
            )
            row_id = cur.fetchone()[0]
        conn.commit()
        return row_id
    except Exception as e:
        logger.error("_save_codon error: %s", e)
        conn.rollback()
        return None
    finally:
        conn.close()


def _get_codons(job_id: str) -> list[dict]:
    conn = get_db()
    rows = []
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, entity, condition, action, glyph_seq, story_excerpt,
                          resonance, clarity, story_score, total_score, sealed, al_jabr_hash
                   FROM codon_distil_results
                   WHERE job_id = %s
                   ORDER BY total_score DESC""",
                (job_id,),
            )
            rows = cur.fetchall()
    except Exception as e:
        logger.error("_get_codons error: %s", e)
    finally:
        conn.close()
    return [
        {
            "id": r[0],
            "entity": r[1],
            "condition": r[2],
            "action": r[3],
            "glyph_seq": r[4],
            "story_excerpt": r[5],
            "resonance": r[6],
            "clarity": r[7],
            "story_score": r[8],
            "total_score": r[9],
            "sealed": r[10],
            "al_jabr_hash": r[11],
        }
        for r in rows
    ]


def _get_job_status(job_id: str) -> dict | None:
    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT status, total_chunks, done_chunks FROM codon_distil_jobs WHERE job_id=%s",
                (job_id,),
            )
            row = cur.fetchone()
        return {"status": row[0], "total_chunks": row[1], "done_chunks": row[2]} if row else None
    except Exception as e:
        logger.error("_get_job_status error: %s", e)
        return None
    finally:
        conn.close()


def _process_job(job_id: str, chunks: list[str]):
    """Background worker: iterate chunks, extract moments, score, store."""
    with _jobs_lock:
        _jobs[job_id] = {
            "status": "running",
            "total": len(chunks),
            "done": 0,
            "codons": [],
            "events": [],
        }

    _create_job(job_id, len(chunks))

    try:
        client = _get_openai_client()
    except Exception as e:
        with _jobs_lock:
            _jobs[job_id]["status"] = "error"
            _jobs[job_id]["error"] = str(e)
            _jobs[job_id]["_finished_at"] = time.time()
        _update_job(job_id, 0, "error")
        return

    codons_found = 0

    for idx, chunk in enumerate(chunks):
        with _jobs_lock:
            if _jobs[job_id].get("status") == "cancelled":
                break

        try:
            moment = extract_moments(chunk, client)
        except Exception as e:
            logger.warning("Chunk %d extraction failed: %s", idx, e)
            moment = None

        codon = None
        if moment:
            total_score = score_codon(moment)
            glyph_seq = map_to_glyphs(moment["entity"], moment["condition"], moment["action"])
            seal_data = f"{moment['entity']}|{moment['condition']}|{moment['action']}|{glyph_seq}"
            al_jabr_hash = fatiha_286_hexdigest_from_str(seal_data)

            codon = {
                "entity": moment["entity"],
                "condition": moment["condition"],
                "action": moment["action"],
                "glyph_seq": glyph_seq,
                "story_excerpt": moment["story_excerpt"],
                "resonance": round(moment["resonance"], 2),
                "clarity": round(moment["clarity"], 2),
                "story_score": round(moment["story"], 2),
                "total_score": total_score,
                "al_jabr_hash": al_jabr_hash,
            }
            row_id = _save_codon(job_id, codon)
            codon["id"] = row_id
            codons_found += 1

        with _jobs_lock:
            _jobs[job_id]["done"] = idx + 1
            event = {
                "type": "progress",
                "done": idx + 1,
                "total": len(chunks),
                "chunk_num": idx + 1,
            }
            if codon:
                event["codon"] = {
                    "glyph_seq": codon["glyph_seq"],
                    "entity": codon["entity"],
                    "condition": codon["condition"],
                    "action": codon["action"],
                    "total_score": codon["total_score"],
                }
            _jobs[job_id]["events"].append(event)

        _update_job(job_id, idx + 1, "running")

    final_status = "complete"
    with _jobs_lock:
        _jobs[job_id]["status"] = final_status
        _jobs[job_id]["_finished_at"] = time.time()
        _jobs[job_id]["events"].append({
            "type": "complete",
            "total_codons": codons_found,
            "total_chunks": len(chunks),
        })

    _update_job(job_id, len(chunks), final_status)
    logger.info("Job %s complete: %d codons from %d chunks", job_id, codons_found, len(chunks))
    _evict_stale_jobs()


@codon_distil_bp.route("/codon-distil")
def codon_distil_page():
    if not session.get("user_id"):
        return redirect("/login")
    role = session.get("role", "user")
    if role not in ("admin", "founder"):
        return redirect("/")
    is_founder = session.get("is_founder", False)
    return render_template("codon_distil.html", is_founder=is_founder)


@codon_distil_bp.route("/api/codon-distil/process", methods=["POST"])
def api_process():
    if not session.get("user_id"):
        return jsonify({"error": "auth required"}), 401
    role = session.get("role", "user")
    if role not in ("admin", "founder"):
        return jsonify({"error": "admin/founder required"}), 403

    text = None
    if request.content_type and "multipart" in request.content_type:
        f = request.files.get("file")
        if f:
            raw = f.read(MAX_TEXT_BYTES + 1)
            if len(raw) > MAX_TEXT_BYTES:
                return jsonify({"error": f"File exceeds {MAX_TEXT_BYTES // (1024*1024)} MB limit"}), 413
            text = raw.decode("utf-8", errors="replace")
    else:
        data = request.get_json(silent=True) or {}
        text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "text is required"}), 400

    encoded = text.encode("utf-8")
    if len(encoded) > MAX_TEXT_BYTES:
        return jsonify({"error": f"Text exceeds {MAX_TEXT_BYTES // (1024*1024)} MB limit. Upload as a file for large archives."}), 413

    chunks = chunk_text(text, max_words=800)
    if not chunks:
        return jsonify({"error": "no processable text found"}), 400

    job_id = str(uuid.uuid4())

    thread = threading.Thread(
        target=_process_job,
        args=(job_id, chunks),
        daemon=True,
    )
    thread.start()

    return jsonify({
        "job_id": job_id,
        "total_chunks": len(chunks),
        "status": "running",
    })


@codon_distil_bp.route("/codon-distil/stream/<job_id>")
def stream_job(job_id: str):
    if not session.get("user_id"):
        return jsonify({"error": "auth required"}), 401
    role = session.get("role", "user")
    if role not in ("admin", "founder"):
        return jsonify({"error": "admin/founder required"}), 403

    def event_generator():
        cursor = 0
        while True:
            with _jobs_lock:
                job = _jobs.get(job_id)

            if job is None:
                db_status = _get_job_status(job_id)
                if db_status is None:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'job not found'})}\n\n"
                    return
                yield f"data: {json.dumps({'type': 'status', **db_status})}\n\n"
                return

            with _jobs_lock:
                events = job["events"][cursor:]
                cursor += len(events)
                status = job["status"]

            for evt in events:
                yield f"data: {json.dumps(evt)}\n\n"

            if status in ("complete", "error", "cancelled"):
                if status == "complete":
                    codons = _get_codons(job_id)
                    yield f"data: {json.dumps({'type': 'results', 'codons': codons})}\n\n"
                return

            yield ": ping\n\n"
            time.sleep(1)

    return Response(
        event_generator(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@codon_distil_bp.route("/api/codon-distil/results/<job_id>")
def api_results(job_id: str):
    if not session.get("user_id"):
        return jsonify({"error": "auth required"}), 401
    role = session.get("role", "user")
    if role not in ("admin", "founder"):
        return jsonify({"error": "admin/founder required"}), 403
    codons = _get_codons(job_id)
    status = _get_job_status(job_id)
    return jsonify({
        "job_id": job_id,
        "status": status,
        "codons": codons,
        "total": len(codons),
    })


@codon_distil_bp.route("/api/codon-distil/seal", methods=["POST"])
def api_seal():
    if not session.get("user_id"):
        return jsonify({"error": "auth required"}), 401
    if not session.get("is_founder"):
        return jsonify({"error": "founder auth required"}), 403

    data = request.get_json(silent=True) or {}
    codon_id = data.get("codon_id")
    if not codon_id:
        return jsonify({"error": "codon_id is required"}), 400

    conn = get_db()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT id, job_id, entity, condition, action, glyph_seq,
                          story_excerpt, resonance, clarity, story_score, total_score, sealed
                   FROM codon_distil_results WHERE id=%s""",
                (codon_id,),
            )
            row = cur.fetchone()

        if not row:
            return jsonify({"error": "codon not found"}), 404

        codon = {
            "id": row[0],
            "job_id": row[1],
            "entity": row[2],
            "condition": row[3],
            "action": row[4],
            "glyph_seq": row[5],
            "story_excerpt": row[6],
            "resonance": row[7],
            "clarity": row[8],
            "story_score": row[9],
            "total_score": row[10],
            "sealed": row[11],
        }

        if codon["sealed"]:
            return jsonify({"error": "already sealed", "codon_id": codon_id}), 409

        chronicle_id = seal_to_chronicle(codon, conn)

        with conn.cursor() as cur:
            al_jabr_hash = fatiha_286_hexdigest_from_str(
                f"{codon['entity']}|{codon['condition']}|{codon['action']}|{codon['glyph_seq']}"
            )
            cur.execute(
                "UPDATE codon_distil_results SET sealed=TRUE, al_jabr_hash=%s WHERE id=%s",
                (al_jabr_hash, codon_id),
            )
        conn.commit()

        return jsonify({
            "success": True,
            "codon_id": codon_id,
            "chronicle_id": chronicle_id,
            "glyph_seq": codon["glyph_seq"],
            "al_jabr_hash": al_jabr_hash[:32],
        })

    except Exception as e:
        logger.error("seal error: %s", e)
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify({"error": "seal failed", "detail": str(e)}), 500
    finally:
        conn.close()
