"""VOID Codex routes: markdown <-> E·C·A encoding bridge."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, render_template, request

from void_engine.codex_codec import (
    decode_codex_to_markdown,
    encode_markdown_to_codex,
    markdown_structure_preview,
)
from void_engine.resonance_packet import (
    build_markdown_door,
    build_packet_manifest,
    parse_markdown_doors,
    resolve_packet_paths,
)

logger = logging.getLogger(__name__)

void_codex_bp = Blueprint("void_codex", __name__)


@void_codex_bp.route("/codex")
def codex_page():
    return render_template("void_codex.html")


@void_codex_bp.route("/api/codex/encode", methods=["POST"])
def codex_encode():
    data = request.get_json(silent=True) or {}
    markdown = (data.get("markdown") or "").strip()
    if not markdown:
        return jsonify({"ok": False, "error": "Provide markdown text"}), 400

    try:
        encoded = encode_markdown_to_codex(markdown)
        preview = markdown_structure_preview(markdown)
        return jsonify({
            "ok": True,
            "encoded": encoded,
            "structure_preview": preview,
        })
    except Exception as exc:
        logger.error("Codex encode failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@void_codex_bp.route("/api/codex/decode", methods=["POST"])
def codex_decode():
    data = request.get_json(silent=True) or {}
    codex_text = (data.get("codex") or "").strip()
    if not codex_text:
        return jsonify({"ok": False, "error": "Provide codex text"}), 400

    try:
        decoded = decode_codex_to_markdown(codex_text)
        preview = markdown_structure_preview(decoded["markdown"])
        return jsonify({
            "ok": True,
            "decoded": decoded,
            "structure_preview": preview,
        })
    except Exception as exc:
        logger.error("Codex decode failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 400


@void_codex_bp.route("/api/codex/packet/build", methods=["POST"])
def codex_packet_build():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "VOID Packet").strip()
    markdown = data.get("markdown") or ""
    payloads = data.get("payloads") or []
    resonance = data.get("resonance") or {}

    if not isinstance(payloads, list) or not payloads:
        return jsonify({"ok": False, "error": "Provide payloads[] with kind/path or kind/hex"}), 400

    try:
        manifest = build_packet_manifest(
            title=title,
            markdown=markdown,
            payloads=payloads,
            resonance=resonance,
        )
        door = build_markdown_door(manifest, heading=title)
        return jsonify({
            "ok": True,
            "manifest": manifest,
            "door_markdown": door,
        })
    except Exception as exc:
        logger.error("Codex packet build failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500


@void_codex_bp.route("/api/codex/packet/parse-door", methods=["POST"])
def codex_packet_parse_door():
    data = request.get_json(silent=True) or {}
    markdown = (data.get("markdown") or "").strip()
    if not markdown:
        return jsonify({"ok": False, "error": "Provide markdown text"}), 400

    doors = parse_markdown_doors(markdown)
    return jsonify({"ok": True, "doors": doors, "count": len(doors)})


@void_codex_bp.route("/api/codex/packet/resolve", methods=["POST"])
def codex_packet_resolve():
    data = request.get_json(silent=True) or {}
    manifest = data.get("manifest") or {}
    if not isinstance(manifest, dict) or not manifest:
        return jsonify({"ok": False, "error": "Provide packet manifest object"}), 400

    try:
        resolved = resolve_packet_paths(manifest)
        return jsonify({"ok": True, "resolved": resolved, "count": len(resolved)})
    except Exception as exc:
        logger.error("Codex packet resolve failed: %s", exc)
        return jsonify({"ok": False, "error": str(exc)}), 500
