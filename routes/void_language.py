"""
VOID Language & Site Translation Routes

Handles:
  - /void-language          — VOID Language glossary page
  - /api/void-language/glossary — JSON glossary endpoint
  - /translate              — Translate page content to a target language
  - /speak                  — Text-to-speech endpoint
  - /api/set-language       — Set preferred language in session
"""

import os
import json
import hashlib
import logging
from flask import Blueprint, render_template, request, jsonify, session, Response

logger = logging.getLogger(__name__)

void_language_bp = Blueprint("void_language", __name__)

_TRANSLATION_CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "void_engine", "translation_cache")

_VALID_LANG_CODES = frozenset(["en", "ur", "ar", "es", "fr", "zh", "ru", "ja"])
_SAFE_LANG_CODE_RE = None


def _validate_lang_code(lang_code: str) -> str:
    """Return the lang_code only if it is an allowed language code, else raise ValueError."""
    import re
    code = lang_code.strip().lower()
    if not re.match(r'^[a-z]{2,5}$', code):
        raise ValueError(f"Invalid lang_code format: {lang_code!r}")
    if code not in _VALID_LANG_CODES:
        raise ValueError(f"Unsupported lang_code: {lang_code!r}")
    return code


def _get_translation_cache_path(slug: str, lang_code: str) -> str:
    os.makedirs(_TRANSLATION_CACHE_DIR, exist_ok=True)
    safe_slug = slug.strip("/").replace("/", "_").replace("..", "") or "root"
    safe_slug = os.path.basename(safe_slug) or "root"
    safe_lang = _validate_lang_code(lang_code)
    filename = f"{safe_slug}__{safe_lang}.json"
    full_path = os.path.realpath(os.path.join(_TRANSLATION_CACHE_DIR, filename))
    cache_real = os.path.realpath(_TRANSLATION_CACHE_DIR)
    if not full_path.startswith(cache_real + os.sep) and full_path != cache_real:
        raise ValueError("Path traversal detected in translation cache path")
    return full_path


def _load_translation_cache(slug: str, lang_code: str):
    path = _get_translation_cache_path(slug, lang_code)
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _save_translation_cache(slug: str, lang_code: str, content_hash: str, translated: str):
    path = _get_translation_cache_path(slug, lang_code)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"slug": slug, "lang": lang_code, "hash": content_hash, "translated": translated}, f, ensure_ascii=False)
    except Exception as e:
        logger.warning("Failed to save translation cache for %s/%s: %s", slug, lang_code, e)

SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "flag": "🇬🇧", "dir": "ltr"},
    {"code": "ur", "name": "Urdu", "flag": "🇵🇰", "dir": "rtl"},
    {"code": "ar", "name": "Arabic", "flag": "🇸🇦", "dir": "rtl"},
    {"code": "es", "name": "Spanish", "flag": "🇪🇸", "dir": "ltr"},
    {"code": "fr", "name": "French", "flag": "🇫🇷", "dir": "ltr"},
    {"code": "zh", "name": "Mandarin", "flag": "🇨🇳", "dir": "ltr"},
    {"code": "ru", "name": "Russian", "flag": "🇷🇺", "dir": "ltr"},
    {"code": "ja", "name": "Japanese", "flag": "🇯🇵", "dir": "ltr"},
    {"code": "void", "name": "VOID", "flag": "◆", "dir": "ltr"},
]

LANG_CODE_TO_NAME = {lang["code"]: lang["name"] for lang in SUPPORTED_LANGUAGES}


@void_language_bp.route("/void-language")
def void_language_page():
    from void_engine.void_language import get_glossary
    try:
        glossary = get_glossary()
    except Exception as e:
        logger.error("Failed to load VOID glossary: %s", e)
        glossary = []

    current_lang = session.get("site_language", "en")
    return render_template(
        "void_language.html",
        glossary=glossary,
        supported_languages=SUPPORTED_LANGUAGES,
        current_language=current_lang,
    )


@void_language_bp.route("/api/void-language/glossary")
def glossary_api():
    from void_engine.void_language import get_glossary
    force = request.args.get("regenerate") == "1"

    if force:
        if not session.get("user_id") or session.get("tier") not in ("sovereign", "journalist"):
            return jsonify({"success": False, "error": "Admin access required for regeneration"}), 403

    try:
        glossary = get_glossary(force_regenerate=force)
        return jsonify({"success": True, "glossary": glossary})
    except Exception as e:
        logger.error("Glossary API error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@void_language_bp.route("/translate", methods=["POST"])
def translate_content():
    """
    Translate a block of text/HTML to the target language.

    Body: { "text": "...", "language": "Urdu", "slug": "/guide", "lang_code": "ur" }

    When slug + lang_code are provided, the result is cached server-side by
    slug+language and served from disk on subsequent requests for the same page.
    The content hash is used to detect stale cache (page content changed).
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    language = data.get("language", "English").strip()
    slug = data.get("slug", "").strip() or request.referrer or ""
    lang_code = data.get("lang_code", "").strip()

    if not text:
        return jsonify({"success": False, "error": "No text provided"}), 400

    if language.lower() == "english":
        return jsonify({"success": True, "translated": text, "language": language, "from_cache": False})

    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

    use_cache = bool(slug and lang_code)
    if use_cache:
        try:
            _validate_lang_code(lang_code)
        except ValueError:
            use_cache = False

    if use_cache:
        try:
            cached = _load_translation_cache(slug, lang_code)
            if cached and cached.get("hash") == content_hash:
                return jsonify({
                    "success": True,
                    "translated": cached["translated"],
                    "language": language,
                    "from_cache": True,
                })
        except (ValueError, Exception) as e:
            logger.warning("Translation cache lookup failed: %s", e)
            use_cache = False

    from void_engine.void_language import translate_text
    try:
        translated = translate_text(text, language)
        if use_cache:
            try:
                _save_translation_cache(slug, lang_code, content_hash, translated)
            except (ValueError, Exception) as e:
                logger.warning("Translation cache save failed: %s", e)
        return jsonify({"success": True, "translated": translated, "language": language, "from_cache": False})
    except Exception as e:
        logger.error("Translation endpoint error: %s", e)
        return jsonify({"success": False, "error": str(e)}), 500


@void_language_bp.route("/speak", methods=["POST"])
def speak():
    """
    Text-to-speech endpoint.
    Body: { "text": "...", "language": "Urdu" }
    Returns: audio/mpeg stream
    """
    data = request.get_json(silent=True) or {}
    text = data.get("text", "").strip()
    language = data.get("language", "English").strip()

    if not text:
        return jsonify({"error": "No text provided"}), 400

    from void_engine.void_language import text_to_speech
    try:
        audio_bytes = text_to_speech(text, language)
        return Response(
            audio_bytes,
            mimetype="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=void_speech.mp3",
                "Cache-Control": "no-cache",
            }
        )
    except Exception as e:
        logger.error("TTS endpoint error: %s", e)
        return jsonify({"error": str(e)}), 500


@void_language_bp.route("/api/set-language", methods=["POST"])
def set_language():
    """Persist the user's preferred language in the session."""
    data = request.get_json(silent=True) or {}
    lang_code = data.get("lang", "en")

    valid_codes = [l["code"] for l in SUPPORTED_LANGUAGES]
    if lang_code not in valid_codes:
        return jsonify({"success": False, "error": "Unsupported language"}), 400

    session["site_language"] = lang_code
    session.modified = True

    lang_info = next((l for l in SUPPORTED_LANGUAGES if l["code"] == lang_code), None)
    return jsonify({
        "success": True,
        "lang": lang_code,
        "name": lang_info["name"] if lang_info else lang_code,
        "dir": lang_info["dir"] if lang_info else "ltr",
    })


@void_language_bp.route("/api/languages")
def get_languages():
    """Return list of supported languages."""
    current = session.get("site_language", "en")
    return jsonify({
        "languages": SUPPORTED_LANGUAGES,
        "current": current,
    })
