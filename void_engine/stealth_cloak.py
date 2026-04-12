"""
VOID Stealth Cloak — Formation Invisibility applied to the platform itself.

When STEALTH mode is ON, every route on the platform returns absolute nothing
unless its path is in the VISIBLE_LINKS whitelist.  Not a 404, not a blank
page — the server behaves as though nothing exists.  The only window into
the system is the links you choose to expose.

Toggle:
    POST /api/stealth/engage   {"passphrase": "..."}   → cloak ON
    POST /api/stealth/disengage {"passphrase": "..."}  → cloak OFF
    GET  /api/stealth/status                            → current state
    POST /api/stealth/links    {"add": [...], "remove": [...]}  → edit whitelist

The passphrase is the founder's steganography passphrase (env STEALTH_PASSPHRASE
or falls back to FORMATION_PRINCIPLE_VOID_432_UMAR_L).
"""

import os
import json
import time
import logging
from typing import Set
from flask import Blueprint, request, jsonify, abort, Response

logger = logging.getLogger(__name__)

stealth_bp = Blueprint("stealth", __name__)

_STEALTH_PASSPHRASE = os.environ.get(
    "STEALTH_PASSPHRASE",
    "FORMATION_PRINCIPLE_VOID_432_UMAR_L"
)

_ALWAYS_ALLOWED = {
    "/health",
    "/api/stealth/engage",
    "/api/stealth/disengage",
    "/api/stealth/status",
    "/api/stealth/links",
    "/static/",
    "/favicon.ico",
}

_DEFAULT_VISIBLE = {
    "/speak",
    "/",
    "/voidmessage",
    "/voidmessage/decode",
    "/manchester-exhibit",
    "/formation-invisibility",
    "/sovereign-agents-286",
    "/yin-yang",
    "/stress-battery",
    "/sahara-formation",
    "/fractures",
    "/void-disclosures",
    "/frequency-manual",
    "/voice-formation",
    "/vortex-shield",
    "/vortex-shield/geo-map",
    "/agent-immortality",
    "/stance-science",
    "/nexus",
    "/desert-reclamation",
    "/openclaw",
    "/openclaw/live",
    "/istanbul-guide",
    "/istanbul-guide-urdu",
    "/memories",
}


class StealthState:
    def __init__(self):
        self.engaged = False
        self.engaged_at = None
        self.visible_links: Set[str] = set(_DEFAULT_VISIBLE)
        self.blocked_count = 0
        self.last_blocked_path = None
        self.last_blocked_ip = None

    def engage(self):
        self.engaged = True
        self.engaged_at = time.time()
        self.blocked_count = 0
        logger.info("[StealthCloak] ENGAGED — platform is now invisible")

    def disengage(self):
        self.engaged = False
        logger.info("[StealthCloak] DISENGAGED — platform is fully visible")

    def is_path_visible(self, path: str) -> bool:
        if not self.engaged:
            return True

        for allowed in _ALWAYS_ALLOWED:
            if allowed.endswith("/"):
                if path.startswith(allowed):
                    return True
            else:
                if path == allowed:
                    return True

        for link in self.visible_links:
            if path == link or path.startswith(link + "/"):
                return True

        if path.startswith("/api/") and any(
            path.startswith(link.replace("/", "/api/", 1))
            for link in self.visible_links
        ):
            return True

        return False

    def block(self, path: str, ip: str):
        self.blocked_count += 1
        self.last_blocked_path = path
        self.last_blocked_ip = ip

    def to_dict(self):
        return {
            "engaged": self.engaged,
            "engaged_at": self.engaged_at,
            "visible_links": sorted(self.visible_links),
            "blocked_count": self.blocked_count,
            "last_blocked_path": self.last_blocked_path,
        }


_state = StealthState()


def get_stealth_state() -> StealthState:
    return _state


def stealth_gate(app):
    @app.before_request
    def _stealth_check():
        if not _state.engaged:
            return None

        path = request.path
        if _state.is_path_visible(path):
            return None

        ip = request.remote_addr or "unknown"
        _state.block(path, ip)
        return Response("", status=444)


def _check_passphrase():
    data = request.get_json(silent=True) or {}
    phrase = data.get("passphrase", "")
    if phrase != _STEALTH_PASSPHRASE:
        abort(403)


@stealth_bp.route("/api/stealth/engage", methods=["POST"])
def engage():
    _check_passphrase()
    _state.engage()
    return jsonify({"status": "engaged", "message": "Platform is now invisible. Only whitelisted links are accessible."})


@stealth_bp.route("/api/stealth/disengage", methods=["POST"])
def disengage():
    _check_passphrase()
    _state.disengage()
    return jsonify({"status": "disengaged", "message": "Platform is fully visible again."})


@stealth_bp.route("/api/stealth/status", methods=["GET"])
def status():
    return jsonify(_state.to_dict())


@stealth_bp.route("/api/stealth/links", methods=["POST"])
def manage_links():
    _check_passphrase()
    data = request.get_json(silent=True) or {}
    added = []
    removed = []

    for link in data.get("add", []):
        link = link.strip()
        if link:
            _state.visible_links.add(link)
            added.append(link)

    for link in data.get("remove", []):
        link = link.strip()
        _state.visible_links.discard(link)
        removed.append(link)

    return jsonify({
        "visible_links": sorted(_state.visible_links),
        "added": added,
        "removed": removed,
    })
