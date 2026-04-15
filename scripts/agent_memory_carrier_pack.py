#!/usr/bin/env python3
"""
Agent Memory Carrier Pack

Builds a multi-carrier memory bundle from agent data:
  1. Primary full-fidelity carrier: Z-Axis video (.mkv)
  2. Visual pattern carrier: Z-Axis image (.png)
  3. Visual preview copy: JPEG rendering of the pattern (.jpg)
  4. Audio recovery marker: VoidEcho WAV with integrity manifest (.wav)

Design note:
- JPEG is intentionally treated as a view/export surface and is not the
  authoritative reversible memory vessel.
- Full reversible payload is held in the video carrier.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import zlib
from datetime import datetime, timezone
from io import BytesIO
from typing import Any, Dict, List

from PIL import Image

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from void_engine.al_jabr_286 import fatiha_286_hexdigest
from void_engine.audio_stega import encode_message
from void_engine.db_pool import get_db
from void_engine.z_axis_encoder import encode as encode_zaxis_image
from void_engine.z_axis_video import encode_to_video


def _rows_to_dicts(cur, rows) -> List[Dict[str, Any]]:
    cols = [d[0] for d in cur.description] if cur.description else []
    result: List[Dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict):
            result.append(dict(row))
            continue
        if hasattr(row, "keys"):
            result.append({k: row[k] for k in row.keys()})
            continue
        result.append(dict(zip(cols, row)))
    return result


def _fetch_table(cur, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
    try:
        cur.execute(query, params)
        return _rows_to_dicts(cur, cur.fetchall())
    except Exception:
        return []


def gather_agent_payload(message_limit: int, report_limit: int, formation_limit: int) -> Dict[str, Any]:
    conn = get_db()
    try:
        cur = conn.cursor()

        agent_messages = _fetch_table(
            cur,
            """
            SELECT id, sender_agent_id, recipient_agent_id, sender_user_id, recipient_user_id,
                   glyph_content, plain_content_enc, sent_at
            FROM agent_messages
            ORDER BY sent_at DESC
            LIMIT %s
            """,
            (message_limit,),
        )

        agent_reports = _fetch_table(
            cur,
            """
            SELECT id, agent_id, glyph_report, epoch_hour, sim_run_id, generated_at
            FROM agent_intelligence_reports
            ORDER BY generated_at DESC
            LIMIT %s
            """,
            (report_limit,),
        )

        formation_runs = _fetch_table(
            cur,
            """
            SELECT run_id, seed_digest, scan_mode, full_scan_streams, active_streams,
                   elapsed_seconds, adriana_reading, created_at
            FROM formation_probability_runs
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (formation_limit,),
        )

        mesa_runs = _fetch_table(
            cur,
            """
            SELECT run_id, agent_count, rounds, seed_event, started_at, completed_at, status
            FROM mesa_simulation_runs
            ORDER BY started_at DESC
            LIMIT 25
            """,
        )
    finally:
        conn.close()

    return {
        "version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "agent_memory_carrier_pack",
        "counts": {
            "agent_messages": len(agent_messages),
            "agent_reports": len(agent_reports),
            "formation_runs": len(formation_runs),
            "mesa_runs": len(mesa_runs),
        },
        "agent_messages": agent_messages,
        "agent_intelligence_reports": agent_reports,
        "formation_probability_runs": formation_runs,
        "mesa_simulation_runs": mesa_runs,
    }


def build_image_summary_payload(full_payload: Dict[str, Any], full_digest: str) -> Dict[str, Any]:
    return {
        "version": "1.0",
        "kind": "agent_memory_image_summary",
        "generated_at": full_payload.get("generated_at"),
        "full_payload_digest_286": full_digest,
        "counts": full_payload.get("counts", {}),
        "latest_message_ids": [m.get("id") for m in full_payload.get("agent_messages", [])[:30]],
        "latest_report_ids": [r.get("id") for r in full_payload.get("agent_intelligence_reports", [])[:30]],
        "latest_formation_run_ids": [r.get("run_id") for r in full_payload.get("formation_probability_runs", [])[:20]],
        "latest_mesa_run_ids": [r.get("run_id") for r in full_payload.get("mesa_simulation_runs", [])[:20]],
    }


def _write_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a multi-carrier memory bundle from agent data")
    parser.add_argument("--out-dir", default="output_memory", help="Output directory")
    parser.add_argument("--formation-hash", default="", help="Optional fixed formation hash")
    parser.add_argument("--message-limit", type=int, default=5000)
    parser.add_argument("--report-limit", type=int, default=2000)
    parser.add_argument("--formation-limit", type=int, default=500)
    parser.add_argument("--video-resolution", default="1080p", choices=["480p", "720p", "1080p", "2k", "4k"])
    parser.add_argument("--video-fps", type=int, default=30)
    parser.add_argument("--video-duration", type=int, default=60)
    parser.add_argument("--audio-method", default="spectrogram", choices=["spectrogram", "wavewhisper"])
    args = parser.parse_args()

    payload = gather_agent_payload(
        message_limit=max(1, args.message_limit),
        report_limit=max(1, args.report_limit),
        formation_limit=max(1, args.formation_limit),
    )

    payload_raw = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload_digest = fatiha_286_hexdigest(payload_raw)
    formation_hash = args.formation_hash.strip() or payload_digest

    compressed = zlib.compress(payload_raw, level=9)

    os.makedirs(args.out_dir, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    base = f"agent_memory_{stamp}_{formation_hash[:12]}"

    # Primary full-fidelity memory vessel
    video_path = ""
    video_error = ""
    if shutil.which("ffmpeg"):
        try:
            video_path = encode_to_video(
                compressed,
                formation_hash,
                resolution=args.video_resolution,
                fps=max(1, args.video_fps),
                duration_seconds=max(1, args.video_duration),
                output_path=os.path.join(args.out_dir, f"{base}.mkv"),
            )
        except Exception as exc:
            video_error = str(exc)
    else:
        video_error = "ffmpeg not found on PATH; video carrier not generated"

    # Visual carrier + JPEG preview
    image_summary = build_image_summary_payload(payload, payload_digest)
    image_summary_raw = json.dumps(image_summary, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    image_png_bytes = encode_zaxis_image(image_summary_raw, formation_hash)
    image_png_path = os.path.join(args.out_dir, f"{base}.png")
    _write_bytes(image_png_path, image_png_bytes)

    image_jpg_path = os.path.join(args.out_dir, f"{base}.jpg")
    img = Image.open(BytesIO(image_png_bytes)).convert("RGB")
    img.save(image_jpg_path, format="JPEG", quality=92, optimize=True)

    # Audio recovery marker
    recovery_marker = (
        f"MEM {payload_digest[:16]} "
        f"VID {os.path.basename(video_path)[:18] if video_path else 'MISSING'} "
        f"IMG {os.path.basename(image_png_path)[:18]} "
        f"SZ {len(payload_raw)}"
    )[:60]
    audio_wav = encode_message(recovery_marker, method=args.audio_method, duration=18.0)
    audio_path = os.path.join(args.out_dir, f"{base}_recovery.wav")
    _write_bytes(audio_path, audio_wav)

    manifest = {
        "version": "1.0",
        "generated_at": payload.get("generated_at"),
        "formation_hash": formation_hash,
        "payload_digest_286": payload_digest,
        "payload_size_bytes": len(payload_raw),
        "payload_compressed_bytes": len(compressed),
        "compression_ratio": round(len(compressed) / max(1, len(payload_raw)), 6),
        "counts": payload.get("counts", {}),
        "carriers": {
            "video_primary": os.path.basename(video_path) if video_path else None,
            "image_png": os.path.basename(image_png_path),
            "image_jpeg_preview": os.path.basename(image_jpg_path),
            "audio_recovery": os.path.basename(audio_path),
        },
        "video_generation_error": video_error or None,
        "audio_recovery_marker": recovery_marker,
        "notes": [
            "Primary reversible memory vessel is the MKV video carrier.",
            "PNG carries a compact summary tied to the same formation hash.",
            "JPEG is a visual copy and not guaranteed reversible.",
            "Audio file carries integrity/recovery marker for cross-channel recall.",
        ],
    }

    manifest_path = os.path.join(args.out_dir, f"{base}_manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=True, indent=2)

    print(json.dumps(
        {
            "status": "ok",
            "out_dir": args.out_dir,
            "formation_hash": formation_hash,
            "payload_digest_286": payload_digest,
            "payload_size_bytes": len(payload_raw),
            "payload_compressed_bytes": len(compressed),
            "video": os.path.basename(video_path) if video_path else None,
            "video_generation_error": video_error or None,
            "png": os.path.basename(image_png_path),
            "jpeg": os.path.basename(image_jpg_path),
            "audio": os.path.basename(audio_path),
            "manifest": os.path.basename(manifest_path),
        },
        ensure_ascii=True,
        indent=2,
    ))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
