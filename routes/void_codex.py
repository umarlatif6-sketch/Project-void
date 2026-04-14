"""VOID Codex routes: markdown <-> E·C·A encoding bridge."""

from __future__ import annotations

import logging

from flask import Blueprint, jsonify, render_template, request

from void_engine.codex_codec import (
    decode_codex_to_markdown,
    encode_markdown_to_codex,
    markdown_structure_preview,
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
