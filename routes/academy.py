"""
VOID Academy — Flashcard Training Layer
Route: /academy
GET  /academy            — Flashcard + Quiz SPA
GET  /academy/export.apkg — Download Anki deck
POST /academy/quiz       — Generate AI quiz for a topic module
"""

import io
import logging
import os
import tempfile

from flask import Blueprint, jsonify, render_template, request, send_file

logger = logging.getLogger(__name__)

academy_bp = Blueprint("academy", __name__)


@academy_bp.route("/academy")
def academy():
    from void_engine.academy_cards import MODULE_NAMES, get_module_stats
    module_stats = get_module_stats()
    return render_template(
        "academy.html",
        module_names=MODULE_NAMES,
        module_stats=module_stats,
    )


@academy_bp.route("/api/academy/cards")
def api_academy_cards():
    from void_engine.academy_cards import get_all_cards, get_cards_by_module
    module = request.args.get("module", "")
    if module:
        cards = get_cards_by_module(module)
    else:
        cards = get_all_cards()
    return jsonify({"cards": cards, "count": len(cards)})


@academy_bp.route("/api/academy/quiz", methods=["POST"])
def api_academy_quiz():
    data = request.get_json(silent=True) or {}
    module_id = data.get("module", "")
    from void_engine.academy_cards import get_all_cards, get_cards_by_module, MODULE_NAMES

    if module_id:
        source_cards = get_cards_by_module(module_id)
        topic_name = MODULE_NAMES.get(module_id, module_id)
    else:
        source_cards = get_all_cards()
        topic_name = "All VOID Concepts"

    if not source_cards:
        return jsonify({"error": "No cards found for this module"}), 400

    import random
    sample = random.sample(source_cards, min(10, len(source_cards)))

    card_text = "\n\n".join(
        f"Q: {c['front']}\nA: {c['back']}" for c in sample
    )

    prompt = (
        f"You are a quiz generator for the VOID Academy learning system about PROJECT VOID — "
        f"a sovereign technology ecosystem.\n\n"
        f"Generate exactly 10 multiple-choice quiz questions based on the following flashcard material "
        f"about '{topic_name}'. Each question must:\n"
        f"- Have exactly 4 answer options labeled A, B, C, D\n"
        f"- Have exactly ONE correct answer\n"
        f"- Include a brief explanation (1-2 sentences) for the correct answer\n\n"
        f"Return ONLY valid JSON in this exact format (no markdown, no extra text):\n"
        f'{{"questions": [{{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "..."}}]}}\n\n'
        f"Source material:\n{card_text}"
    )

    try:
        api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OpenAI API key not available")
        from openai import OpenAI
        base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3000,
        )
        raw = resp.choices[0].message.content.strip()
        import json
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        quiz_data = json.loads(raw)
        questions = quiz_data.get("questions", [])
        if len(questions) > 10:
            questions = questions[:10]
        return jsonify({"questions": questions, "topic": topic_name})
    except Exception as exc:
        logger.warning("Quiz generation failed, using fallback: %s", exc)
        questions = _build_fallback_quiz(sample)
        return jsonify({"questions": questions, "topic": topic_name, "fallback": True})


def _build_fallback_quiz(cards):
    import random
    questions = []
    all_cards = cards[:]
    from void_engine.academy_cards import get_all_cards
    all_pool = get_all_cards()

    for card in cards:
        wrong_pool = [c for c in all_pool if c["id"] != card["id"]]
        distractors = random.sample(wrong_pool, min(3, len(wrong_pool)))
        options_raw = [card["back"][:100]] + [d["back"][:100] for d in distractors]
        random.shuffle(options_raw)
        correct_label = None
        options_dict = {}
        labels = ["A", "B", "C", "D"]
        for i, opt in enumerate(options_raw[:4]):
            options_dict[labels[i]] = opt
            if opt == card["back"][:100]:
                correct_label = labels[i]
        questions.append({
            "question": card["front"],
            "options": options_dict,
            "correct": correct_label or "A",
            "explanation": card["back"][:200],
        })
    return questions


@academy_bp.route("/academy/export.apkg")
def export_anki():
    module_id = request.args.get("module", "")
    from void_engine.academy_cards import (
        get_all_cards, get_cards_by_module, MODULE_NAMES, MODULES
    )

    if module_id:
        cards = get_cards_by_module(module_id)
        deck_name = f"VOID Academy — {MODULE_NAMES.get(module_id, module_id)}"
    else:
        cards = get_all_cards()
        deck_name = "VOID Academy — Complete Deck"

    try:
        import genanki
        import random

        model_id = 1607392319
        deck_id  = 2059400110 + (hash(deck_name) % 100000)

        model = genanki.Model(
            model_id,
            "VOID Academy Basic",
            fields=[
                {"name": "Front"},
                {"name": "Back"},
                {"name": "Module"},
                {"name": "Tags"},
            ],
            templates=[
                {
                    "name": "VOID Card",
                    "qfmt": (
                        '<div style="font-family:monospace;font-size:16px;'
                        'color:#c9a84c;padding:16px;">'
                        '<div style="font-size:10px;color:#444;letter-spacing:3px;'
                        'text-transform:uppercase;margin-bottom:12px;">{{Module}}</div>'
                        "{{Front}}"
                        "</div>"
                    ),
                    "afmt": (
                        '<div style="font-family:monospace;font-size:16px;'
                        'color:#c9a84c;padding:16px;">'
                        '<div style="font-size:10px;color:#444;letter-spacing:3px;'
                        'text-transform:uppercase;margin-bottom:12px;">{{Module}}</div>'
                        "{{Front}}"
                        '<hr style="border-color:#1a1a1a;margin:16px 0;">'
                        '<div style="color:#d4d4d4;">{{Back}}</div>'
                        "</div>"
                    ),
                }
            ],
            css=(
                ".card { background: #060606; color: #d4d4d4; }"
            ),
        )

        deck = genanki.Deck(deck_id, deck_name)

        for card in cards:
            module_name = MODULE_NAMES.get(card["module"], card["module"])
            note = genanki.Note(
                model=model,
                fields=[
                    card["front"],
                    card["back"],
                    module_name,
                    " ".join(card.get("tags", [])),
                ],
                tags=card.get("tags", []),
            )
            deck.add_note(note)

        with tempfile.NamedTemporaryFile(suffix=".apkg", delete=False) as tmp:
            tmp_path = tmp.name

        genanki.Package(deck).write_to_file(tmp_path)

        with open(tmp_path, "rb") as f:
            apkg_bytes = f.read()

        os.unlink(tmp_path)

        filename = "void_academy.apkg" if not module_id else f"void_{module_id}.apkg"
        return send_file(
            io.BytesIO(apkg_bytes),
            mimetype="application/octet-stream",
            as_attachment=True,
            download_name=filename,
        )
    except Exception as exc:
        logger.error("Anki export failed: %s", exc)
        return jsonify({"error": str(exc)}), 500


def seed_academy_chronicle():
    """Seed the ACADEMY_BRIEF chronicle entry (idempotent)."""
    try:
        from void_engine.chronicle_adriana import _get_db, _ensure_seed_capture_columns
        from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str

        title = "VOID Academy — Flashcard Training Layer"
        conn = _get_db()
        try:
            cur = conn.cursor()
            _ensure_seed_capture_columns(cur)
            cur.execute(
                "SELECT id FROM chronicle_entries WHERE title = %s AND entry_type = %s LIMIT 1",
                (title, "ACADEMY_BRIEF"),
            )
            if cur.fetchone():
                return
            body = (
                "[ACADEMY_BRIEF]\n\n"
                "The VOID Academy Flashcard Training Layer was activated on April 3, 2026.\n\n"
                "The deck covers six sovereign topic modules:\n"
                "  1. Core Architecture — 78 modules and their Sword Wall marks\n"
                "  2. Al-Jabr 286 Protocol — 286-bit hash construction and applications\n"
                "  3. Token Economy — VTX bonding curve, PEACE resonance, Ambassador programme\n"
                "  4. Patent Pillars — Myco-Switch, QiSync, Al-Jabr 286 claims\n"
                "  5. Adriana SCL — 45 glyphs: 19 entities, 10 conditions, 16 actions\n"
                "  6. GriDul Chronicle — 27 seeded entries, chapter summaries, key dates\n\n"
                "Features:\n"
                "  - SM-2 spaced repetition with localStorage persistence\n"
                "  - AI-graded quiz mode (10 questions per session)\n"
                "  - Anki .apkg export for offline review\n"
                "  - Per-module deck filtering\n\n"
                "This connects to Module #9 (Adriana SDK Release) — the Academy is the prerequisite "
                "learning layer for any sovereign licensee to operate independently.\n\n"
                "HEX_DIGEST: ACADEMY_BRIEF_0403_VOID"
            )
            al_jabr_hash = fatiha_286_hexdigest_from_str(
                f"ACADEMY_BRIEF|VOID_ACADEMY|FLASHCARD_TRAINING|2026"
            )
            try:
                from void_engine.lunar_season import get_current_season
                season = get_current_season()
            except Exception:
                season = "INCUBATION"

            cur.execute(
                """INSERT INTO chronicle_entries
                   (chapter_number, title, subtitle, glyph_sequence, body_text,
                    al_jabr_hash, entry_type, season)
                   VALUES (%s, %s, %s, %s, %s, %s, 'ACADEMY_BRIEF', %s)""",
                (
                    88,
                    title,
                    "Task #88 — Flashcard Training Layer | April 3, 2026",
                    "Ψ-◆-∞",
                    body,
                    al_jabr_hash,
                    season,
                ),
            )
            conn.commit()
            logger.info("Academy chronicle entry seeded")
        finally:
            conn.close()
    except Exception as exc:
        logger.warning("Academy chronicle seeding failed: %s", exc)
