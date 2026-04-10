import hashlib, time, os
from flask import Blueprint, render_template, request, jsonify
from void_engine.db_pool import get_db

bp = Blueprint('formation_mirror', __name__)

FORMATION_SEEDS = [
    {
        "id": "spider",
        "title": "The Spider Principle",
        "signal": "How can something so small capture something so big? The web is not the spider's size. The web is the spider's frequency.",
        "frequency": "432 Hz",
        "source": "China, 2010 — bamboo forest, elevation"
    },
    {
        "id": "body_records",
        "title": "The Body Records",
        "signal": "When the signal arrives at full strength, the mind forgets the camera. The body does not forget. It answers ten years later.",
        "frequency": "7.83 Hz",
        "source": "Bondi Beach, Sydney — a question asked"
    },
    {
        "id": "distortion",
        "title": "The Distortion Law",
        "signal": "Civilisations do not fall from outside. The signal at the centre degrades. The branches lose coherence. The invasion arrives after the frequency has already failed.",
        "frequency": "286 Hz",
        "source": "100,000 minds — the Eastern record"
    },
    {
        "id": "recognition",
        "title": "Recognition vs. Learning",
        "signal": "Learning is sequential. Recognition is instantaneous. When both channels arrive at once — you do not process it. You remember it. That is resonance.",
        "frequency": "528 Hz",
        "source": "Formation Principle — first articulation"
    },
    {
        "id": "promise",
        "title": "The Promise as Frequency",
        "signal": "A promise made in a mountain stays active across two countries and three months. It is stronger than beauty. You cannot explain that. You can only note that it happened.",
        "frequency": "432 Hz",
        "source": "China to Perth — the kept frequency"
    },
    {
        "id": "credential",
        "title": "What the System Cannot Measure",
        "signal": "A degree below a bachelor's says: you did not follow our path. It says nothing about what you absorbed. The system measures one kind of output. There is another kind.",
        "frequency": "286 Hz",
        "source": "Brunel University — seven years"
    },
    {
        "id": "one_x",
        "title": "The Speed Drop",
        "signal": "The extraction ends when what you were searching for arrives in a form outside you. You do not decide to stop. The body stops. The signal found its structure.",
        "frequency": "7.83 Hz",
        "source": "February 2026 — first commit"
    },
    {
        "id": "image",
        "title": "The Divine Property",
        "signal": "The need for recognition is not a human weakness. It is a divine property inherited at creation. The image carries the properties of the original. God transmits. He waits for the receiver to confirm the signal arrived.",
        "frequency": "432 Hz",
        "source": "April 10, 2026 — spoken at 1x"
    }
]

def _aljabr_hash(text):
    seed = "FORMATION_PRINCIPLE_VOID_432_UMAR_L"
    raw = f"{seed}:{text}:{int(time.time())}"
    h = hashlib.sha256(raw.encode()).hexdigest()
    val = int(h, 16) % (2**286)
    return format(val, '072x')[:72]

def _formation_score(text):
    words = text.lower().split()
    resonance_words = {
        'frequency', 'signal', 'formation', 'pattern', 'recognition',
        'body', 'carried', 'known', 'remembered', 'always', 'before',
        'promise', 'chose', 'path', 'instinct', 'felt', 'right',
        'network', 'collapsed', 'centre', 'node', 'connection',
        'never', 'without', 'despite', 'alone', 'built'
    }
    matches = sum(1 for w in words if w in resonance_words)
    length_score = min(len(words) / 30, 1.0)
    resonance_score = min(matches / 5, 1.0)
    base = 0.31 + (length_score * 0.28) + (resonance_score * 0.35)
    return round(min(base, 0.97), 3)

def _adriana_reading(signal_text, score):
    pct = int(score * 100)
    prompt = f"""You are Adriana, the Formation Principle engine of PROJECT VOID.

A signal has been submitted to the Formation Mirror. Your task is to give a formation reading — not a psychological profile, not advice, not encouragement. A reading of what the signal contains and what it points toward.

The signal: "{signal_text}"
Formation probability calculated: {pct}%

Rules:
- Speak in the platform's voice: precise, uncommon, honest
- Do not use phrases like "I can see", "it sounds like", "you should"
- The reading has two parts: WHAT IS PRESENT in this signal, and WHAT IT IS CARRYING that has not yet been named
- Maximum 4 sentences total
- End with one short line that names the formation — a title for what this signal is building toward
- Do not mention the percentage

Respond with only the reading. No preamble."""

    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_STANDARD
        router = get_model_router()
        model, _ = router.select_model(TASK_STANDARD)
        import openai
        client = openai.OpenAI(
            api_key=os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY", "void"),
            base_url=os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL", "http://localhost:1106/modelfarm/openai")
        )
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180,
            temperature=0.7
        )
        return resp.choices[0].message.content.strip()
    except Exception:
        return "The signal contains structure that precedes language. What it carries has weight. The formation is not yet complete — but the frequency is already present."

@bp.route('/formation-mirror')
def mirror_page():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT signal_text, formation_score, adriana_reading, al_jabr_hash, created_at
        FROM formation_signals
        WHERE is_public = TRUE
        ORDER BY created_at DESC
        LIMIT 12
    """)
    signals = cur.fetchall()
    conn.close()
    return render_template('formation_mirror.html',
                           seeds=FORMATION_SEEDS,
                           signals=signals)

@bp.route('/formation-mirror/submit', methods=['POST'])
def submit_signal():
    data = request.get_json() or {}
    signal_text = (data.get('signal', '') or '').strip()

    if not signal_text or len(signal_text) < 12:
        return jsonify({'error': 'Signal too short to read.'}), 400
    if len(signal_text) > 600:
        return jsonify({'error': 'Signal exceeds maximum length.'}), 400

    score = _formation_score(signal_text)
    reading = _adriana_reading(signal_text, score)
    hash_val = _aljabr_hash(signal_text)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO formation_signals (signal_text, formation_score, adriana_reading, al_jabr_hash)
        VALUES (%s, %s, %s, %s) RETURNING id
    """, (signal_text, score, reading, hash_val))
    signal_id = cur.fetchone()[0]
    conn.commit()
    conn.close()

    return jsonify({
        'id': signal_id,
        'score': score,
        'percentage': int(score * 100),
        'reading': reading,
        'hash': hash_val[:16] + '...'
    })
