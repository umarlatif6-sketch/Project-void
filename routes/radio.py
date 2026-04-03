"""
VOID Radio — Podcast Generation and Player Route

Routes:
  GET  /radio                         — Broadcast room player page (no auth)
  POST /radio/generate                — Generate script + audio from Chronicle entries
  POST /radio/encode-stega            — Encode episode into VoidEcho stega WAV
  GET  /radio/download/<slug>/<file>  — Download generated audio file
"""

import json
import logging
import re
import time
from pathlib import Path
from flask import Blueprint, render_template, request, jsonify, send_file

logger = logging.getLogger(__name__)
radio_bp = Blueprint("radio", __name__)

RADIO_DIR = Path(__file__).parent.parent / "static" / "radio"
RADIO_DIR.mkdir(parents=True, exist_ok=True)


def _safe_slug(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower())
    slug = slug.strip("-")[:48]
    ts = str(int(time.time()))[-6:]
    return f"{slug}-{ts}"


@radio_bp.route("/radio")
def radio_page():
    from void_engine.chronicle_adriana import get_chronicle

    try:
        all_entries = get_chronicle()
        entries_by_chapter = {}
        for e in all_entries:
            ch = e.get("chapter_number", 0)
            if ch not in entries_by_chapter:
                entries_by_chapter[ch] = e
        chapter_list = sorted(entries_by_chapter.values(), key=lambda x: x.get("chapter_number", 0))
    except Exception as exc:
        logger.error("[VOID-RADIO] Failed to load chronicle: %s", exc)
        chapter_list = []

    existing_episodes = _list_existing_episodes()

    return render_template(
        "radio.html",
        chapters=chapter_list,
        episodes=existing_episodes,
    )


def _list_existing_episodes():
    episodes = []
    if not RADIO_DIR.exists():
        return episodes
    for ep_dir in sorted(RADIO_DIR.iterdir(), reverse=True):
        if not ep_dir.is_dir():
            continue
        meta_path = ep_dir / "meta.json"
        ep_mp3 = ep_dir / "episode.mp3"
        stega_wav = ep_dir / "episode_stega.wav"
        if not ep_mp3.exists():
            continue
        meta = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text())
            except Exception:
                pass
        episodes.append({
            "slug": ep_dir.name,
            "title": meta.get("title", ep_dir.name),
            "lines": meta.get("lines", 0),
            "has_stega": stega_wav.exists(),
            "mp3_url": f"/radio/download/{ep_dir.name}/episode.mp3",
            "wav_url": f"/radio/download/{ep_dir.name}/episode_stega.wav" if stega_wav.exists() else None,
        })
    return episodes[:10]


@radio_bp.route("/radio/generate", methods=["POST"])
def radio_generate():
    """
    Generate a two-host podcast episode from Chronicle entries.

    Body: {"chapter_filter": "all"|<chapter_number>, "title": "Optional episode title"}
    """
    data = request.get_json(force=True, silent=True) or {}
    chapter_filter = str(data.get("chapter_filter", "all")).strip()
    episode_title = (data.get("title") or "").strip()

    try:
        from void_engine.radio_engine import (
            get_chronicle_entries_for_radio,
            generate_script,
            render_audio,
            seed_radio_broadcast_entry,
        )

        entries = get_chronicle_entries_for_radio(chapter_filter)
        if not entries:
            return jsonify({"error": "No Chronicle entries found for this filter"}), 400

        if not episode_title:
            if chapter_filter == "all":
                episode_title = "VOID Chronicle — Full Archive Broadcast"
            else:
                matched = next((e for e in entries if str(e.get("chapter_number")) == chapter_filter), None)
                if matched:
                    episode_title = f"Chapter {chapter_filter}: {matched['title']}"
                else:
                    episode_title = f"VOID Chronicle — Chapter {chapter_filter}"

        logger.info("[VOID-RADIO] Generating episode: %s (filter=%s, %d entries)",
                    episode_title, chapter_filter, len(entries))

        script = generate_script(entries, episode_title)
        episode_slug = _safe_slug(episode_title)

        norm_path = render_audio(script, episode_slug)

        script_text = "\n".join(
            f"[Host {l.get('host','?')}]: {l.get('text','')}"
            for l in script
        )

        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        script_hash = fatiha_286_hexdigest_from_str(script_text)

        meta = {
            "title": episode_title,
            "chapter_filter": chapter_filter,
            "lines": len(script),
            "script_hash": script_hash,
        }
        ep_dir = RADIO_DIR / episode_slug
        (ep_dir / "meta.json").write_text(json.dumps(meta, indent=2))
        (ep_dir / "script.json").write_text(json.dumps(script, indent=2, ensure_ascii=False))

        try:
            seed_radio_broadcast_entry(episode_title, script, episode_slug)
        except Exception as seed_exc:
            logger.warning("[VOID-RADIO] Could not seed broadcast chronicle entry: %s", seed_exc)

        return jsonify({
            "success": True,
            "slug": episode_slug,
            "title": episode_title,
            "lines": len(script),
            "script": script,
            "script_hash": script_hash,
            "mp3_url": f"/radio/download/{episode_slug}/episode.mp3",
        })

    except Exception as exc:
        logger.exception("[VOID-RADIO] Generation failed: %s", exc)
        return jsonify({"error": "Episode generation failed", "detail": str(exc)}), 500


@radio_bp.route("/radio/encode-stega", methods=["POST"])
def radio_encode_stega():
    """
    Encode the Al-Jabr 286 hash of the episode script into a VoidEcho WAV.

    Body: {"slug": "episode-slug"}
    """
    data = request.get_json(force=True, silent=True) or {}
    slug = (data.get("slug") or "").strip()
    if not slug:
        return jsonify({"error": "slug is required"}), 400

    ep_dir = RADIO_DIR / slug
    if not ep_dir.exists():
        return jsonify({"error": f"Episode '{slug}' not found"}), 404

    script_path = ep_dir / "script.json"
    if not script_path.exists():
        return jsonify({"error": "Script file not found for this episode"}), 404

    try:
        script = json.loads(script_path.read_text())
        script_text = "\n".join(
            f"[Host {l.get('host','?')}]: {l.get('text','')}"
            for l in script
        )

        from void_engine.radio_engine import encode_stega
        stega_path = encode_stega(slug, script_text)

        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
        script_hash = fatiha_286_hexdigest_from_str(script_text)

        return jsonify({
            "success": True,
            "slug": slug,
            "script_hash": script_hash,
            "wav_url": f"/radio/download/{slug}/episode_stega.wav",
            "message": "Al-Jabr 286 hash encoded into VoidEcho spectrogram carrier",
        })

    except Exception as exc:
        logger.exception("[VOID-RADIO] Stega encode failed: %s", exc)
        return jsonify({"error": "Stega encoding failed", "detail": str(exc)}), 500


@radio_bp.route("/radio/download/<slug>/<filename>")
def radio_download(slug: str, filename: str):
    allowed = {"episode.mp3", "episode_raw.mp3", "episode_stega.wav"}
    if filename not in allowed:
        return jsonify({"error": "File not allowed"}), 403

    file_path = RADIO_DIR / slug / filename
    if not file_path.exists():
        return jsonify({"error": "File not found"}), 404

    if filename.endswith(".wav"):
        mimetype = "audio/wav"
    else:
        mimetype = "audio/mpeg"

    return send_file(
        str(file_path),
        mimetype=mimetype,
        as_attachment=False,
        download_name=filename,
    )
