"""
VOID Radio Engine — Podcast Audio Layer

Generates two-host podcast episodes from Chronicle entries using:
  - OpenAI for conversational script generation (NotebookLM pattern)
    - Unified TTS provider for per-line rendering (OpenAI or ElevenLabs-compatible)
  - pydub for audio concatenation with 350ms gaps
  - ffmpeg for loudness normalisation to -16 LUFS
  - audio_stega.encode_message for steganographic VoidEcho encoding

Host A: George (JBFqnCBsd6RMkjVDRZzb) — Explainer
Host B: Rachel (21m00Tcm4TlvDq8ikWAM) — Questioner
"""

import io
import os
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger(__name__)

RADIO_DIR = Path(__file__).parent.parent / "static" / "radio"
RADIO_DIR.mkdir(parents=True, exist_ok=True)

VOICE_GEORGE = "JBFqnCBsd6RMkjVDRZzb"
VOICE_RACHEL = "21m00Tcm4TlvDq8ikWAM"
GAP_MS = 350


def _get_openai_client():
    from openai import OpenAI
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def generate_script(entries: List[Dict], episode_title: str) -> List[Dict]:
    """
    Generate a two-host conversational podcast script from Chronicle entries.

    Returns a list of dicts: [{"host": "A"|"B", "text": "..."}, ...]

    Structure (NotebookLM pattern):
      - Cold open: most surprising fact
      - Setup: what PROJECT VOID is
      - 3-5 thematic segments, one idea each
      - Takeaways
      - Outro
    """
    combined_text = "\n\n".join(
        f"[Chapter {e.get('chapter_number', '?')}: {e['title']}]\n{e.get('body_text', e.get('english_text', ''))[:800]}"
        for e in entries[:10]
    )

    prompt = f"""You are writing a two-host podcast script about PROJECT VOID — a sovereign communication platform combining acoustic steganography, mesh networking (GriDul), biocomputing (MycoVOID), Al-Jabr 286 cryptography, and the VTX token economy.

Host A (George) is the knowledgeable explainer — calm, precise, enthusiastic about the technology.
Host B (Rachel) is the curious questioner — smart, probing, asks what the listener is thinking.

Write a podcast episode titled: "{episode_title}"

Using this source material from the VOID Chronicle:
{combined_text}

Structure:
1. Cold open (15-20 seconds): Start with the most surprising or striking fact. No "welcome to the show" yet.
2. Intro/Setup (30s): Hosts introduce themselves and the topic briefly.
3. Segment 1: Core concept (what is PROJECT VOID / the specific chapter focus)
4. Segment 2: The technology (Al-Jabr 286, 432 Hz, steganography)
5. Segment 3: The biology (Myco-Switch, QiSync, or relevant bio element)
6. Segment 4: The bigger picture (why this matters / patent implications / future)
7. Takeaways: 2-3 key things the listener should remember
8. Outro: Brief, resonant closing line.

Output ONLY valid JSON — a list of objects: [{{"host": "A", "text": "..."}}]
Each line is one spoken turn. Keep turns under 60 words. Aim for 20-30 total lines.
No stage directions, no markdown. Pure JSON array."""

    client = _get_openai_client()
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a podcast script writer. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000,
        temperature=0.75,
    )

    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    script = json.loads(raw)
    if not isinstance(script, list):
        raise ValueError("Script generation did not return a list")

    for line in script:
        if "host" not in line or "text" not in line:
            raise ValueError(f"Invalid script line: {line}")

    logger.info("[VOID-RADIO] Generated script with %d lines", len(script))
    return script


def _render_line_tts(text: str, voice_id: str) -> bytes:
    """
    Render a single line of text via the configured TTS provider.
    Returns MP3 bytes.
    """
    from void_engine.tts_provider import synthesize_mp3

    return synthesize_mp3(text, voice=voice_id)


def render_audio(script: List[Dict], episode_slug: str) -> Path:
    """
    Render each script line via the configured TTS provider, concatenate with 350ms gaps,
    normalise to -16 LUFS via ffmpeg, and save as episode.mp3.

    Returns path to the normalised episode.mp3.
    """
    from pydub import AudioSegment

    gap = AudioSegment.silent(duration=GAP_MS)
    segments = []

    for i, line in enumerate(script):
        host = line.get("host", "A")
        text = line.get("text", "").strip()
        if not text:
            continue

        voice_id = VOICE_GEORGE if host == "A" else VOICE_RACHEL

        logger.info("[VOID-RADIO] Rendering line %d/%d (Host %s): %.40s…",
                    i + 1, len(script), host, text)

        for attempt in range(3):
            try:
                mp3_bytes = _render_line_tts(text, voice_id)
                seg = AudioSegment.from_file(io.BytesIO(mp3_bytes), format="mp3")
                segments.append(seg)
                segments.append(gap)
                break
            except Exception as exc:
                logger.warning("[VOID-RADIO] Line %d attempt %d failed: %s", i, attempt + 1, exc)
                if attempt == 2:
                    logger.error("[VOID-RADIO] Skipping line %d after 3 failures", i)
                time.sleep(1)

    if not segments:
        raise RuntimeError("No audio segments were rendered")

    combined = segments[0]
    for seg in segments[1:]:
        combined += seg

    ep_dir = RADIO_DIR / episode_slug
    ep_dir.mkdir(parents=True, exist_ok=True)

    raw_path = ep_dir / "episode_raw.mp3"
    combined.export(str(raw_path), format="mp3", bitrate="128k")
    logger.info("[VOID-RADIO] Raw episode saved: %s (%.1fs)", raw_path, combined.duration_seconds)

    norm_path = ep_dir / "episode.mp3"
    _normalise_lufs(raw_path, norm_path)

    return norm_path


def _normalise_lufs(input_path: Path, output_path: Path, target_lufs: float = -16.0) -> None:
    """Normalise audio to target LUFS using ffmpeg loudnorm filter."""
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af", f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11",
        "-ar", "44100",
        "-ab", "128k",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=120)
    if result.returncode != 0:
        logger.error("[VOID-RADIO] ffmpeg normalise failed: %s", result.stderr.decode())
        import shutil
        shutil.copy(str(input_path), str(output_path))
    else:
        logger.info("[VOID-RADIO] Normalised to %s LUFS → %s", target_lufs, output_path)


def encode_stega(episode_slug: str, script_text: str) -> Path:
    """
    Encode the Al-Jabr 286 hash of script_text into the episode.mp3 carrier
    using audio_stega.encode_message (spectrogram mode).

    Saves the stega-encoded WAV as episode_stega.wav and returns its path.
    """
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str
    from void_engine.audio_stega import encode_message

    ep_dir = RADIO_DIR / episode_slug
    episode_mp3 = ep_dir / "episode.mp3"
    stega_wav = ep_dir / "episode_stega.wav"

    if not episode_mp3.exists():
        raise FileNotFoundError(f"episode.mp3 not found at {episode_mp3}")

    hash_payload = fatiha_286_hexdigest_from_str(script_text)
    logger.info("[VOID-RADIO] Script hash (Al-Jabr 286): %s…", hash_payload[:32])

    wav_bytes = encode_message(hash_payload, method="spectrogram", duration=10.0)
    stega_wav.write_bytes(wav_bytes)
    logger.info("[VOID-RADIO] Stega WAV saved: %s", stega_wav)
    return stega_wav


def get_chronicle_entries_for_radio(chapter_filter: str = "all") -> List[Dict]:
    """Return Chronicle entries suitable for radio, optionally filtered by chapter group."""
    from void_engine.chronicle_adriana import get_chronicle

    entries = get_chronicle()
    if chapter_filter == "all":
        return entries

    try:
        chapter_num = int(chapter_filter)
        return [e for e in entries if e.get("chapter_number") == chapter_num]
    except (ValueError, TypeError):
        return entries


def seed_radio_brief_into_chronicle() -> None:
    """
    Seed the RADIO_BRIEF chronicle entry on startup (idempotent by title).
    """
    from void_engine.db_pool import get_db
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

    title = "VOID Radio — Podcast Broadcast Layer"
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM chronicle_entries WHERE title = %s LIMIT 1", (title,))
        if cur.fetchone():
            return

        body = (
            "VOID Radio is a two-host podcast generation and broadcast layer within PROJECT VOID.\n\n"
            "The system produces conversational episodes from Chronicle chapters using two AI voices — "
            "George (Explainer) and Rachel (Questioner) — rendered through the configured unified TTS backend.\n\n"
            "Each episode follows the NotebookLM broadcast pattern:\n"
            "  Cold open → Setup → 3-5 thematic segments → Takeaways → Outro\n\n"
            "Audio is concatenated with 350ms gaps between turns, then loudness-normalised to -16 LUFS "
            "via ffmpeg for broadcast-standard output.\n\n"
            "The plain episode.mp3 is also re-encoded as a VoidEcho steganographic broadcast: "
            "the Al-Jabr 286 hash of the full script is hidden inside the episode audio using the "
            "spectrogram mode. The episode IS the carrier; the 286-bit hash IS the hidden payload.\n\n"
            "Medium is the message. The story IS the signal.\n\n"
            "Route: /radio\n"
            "Voices: George (JBFqnCBsd6RMkjVDRZzb) / Rachel (21m00Tcm4TlvDq8ikWAM)\n"
            "TTS Backend: TTS_PROVIDER (OpenAI or ElevenLabs-compatible)\n"
            "Carrier: VoidEcho 432 Hz spectrogram\n"
            "HEX_DIGEST: RADIO_BRIEF_0x432_BROADCAST"
        )

        from void_engine.lunar_season import get_current_season
        try:
            season = get_current_season()
        except Exception:
            season = "INCUBATION"

        hash_val = fatiha_286_hexdigest_from_str(body)
        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash, entry_type, season)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                99,
                title,
                "Capability Brief — VOID Radio Podcast Layer",
                "◆-📻-∞",
                body,
                hash_val,
                "RADIO_BRIEF",
                season,
            ),
        )
        conn.commit()
        logger.info("[VOID-RADIO] RADIO_BRIEF chronicle entry seeded")
    except Exception as exc:
        conn.rollback()
        logger.error("[VOID-RADIO] Failed to seed RADIO_BRIEF: %s", exc)
    finally:
        conn.close()


def seed_radio_broadcast_entry(title: str, script_lines: List[Dict], episode_slug: str) -> None:
    """
    Seed a RADIO_BROADCAST chronicle entry for a generated episode (idempotent by title).
    """
    from void_engine.db_pool import get_db
    from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

    broadcast_title = f"RADIO_BROADCAST — {title}"
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM chronicle_entries WHERE title = %s LIMIT 1", (broadcast_title,))
        if cur.fetchone():
            logger.info("[VOID-RADIO] Broadcast entry already exists: %s", broadcast_title)
            conn.close()
            return

        script_preview = "\n".join(
            f"[Host {l.get('host','?')}]: {l.get('text','')[:80]}"
            for l in script_lines[:8]
        )
        body = (
            f"Episode: {title}\n"
            f"Slug: {episode_slug}\n"
            f"Lines: {len(script_lines)}\n\n"
            f"Script Preview:\n{script_preview}\n\n"
            f"Audio: /radio/download/{episode_slug}/episode.mp3\n"
            f"VoidEcho: /radio/download/{episode_slug}/episode_stega.wav"
        )

        from void_engine.lunar_season import get_current_season
        try:
            season = get_current_season()
        except Exception:
            season = "INCUBATION"

        hash_val = fatiha_286_hexdigest_from_str(body)
        cur.execute(
            """INSERT INTO chronicle_entries
               (chapter_number, title, subtitle, glyph_sequence, body_text, al_jabr_hash, entry_type, season)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
            (
                99,
                broadcast_title,
                f"VOID Radio Broadcast — {episode_slug}",
                "◆-📻-⚡",
                body,
                hash_val,
                "RADIO_BROADCAST",
                season,
            ),
        )
        conn.commit()
        logger.info("[VOID-RADIO] RADIO_BROADCAST entry seeded: %s", broadcast_title)
    except Exception as exc:
        conn.rollback()
        logger.error("[VOID-RADIO] Failed to seed broadcast entry: %s", exc)
    finally:
        conn.close()
