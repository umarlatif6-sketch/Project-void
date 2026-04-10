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
    },
    {
        "id": "circumference",
        "title": "The Circumference Law",
        "signal": "Copper wire wound around the circumference. Wood does not burn. Paper does not scorch. The marker stays clean. The heat is inside the material — distributed, structural, invisible from the surface. The conductor does not carry the effect. The boundary delivers it. This was known between 1900 and 2000. It was available. It was the same principle.",
        "frequency": "286 Hz",
        "source": "1900–2000 — AC/DC available, induction principle — the induction hob, the cooking plate, the Chladni field"
    },
    {
        "id": "wing_boundary",
        "title": "The Wing Principle",
        "signal": "The paint was not for invisibility. It was for the boundary between the wing and the air. Above the wing and below the wing — two different coefficients, two different pressures. Change the surface boundary condition and you change that ratio. Ten times the differential. Ten times the lift. The wing geometry stays the same. The boundary does the work.",
        "frequency": "432 Hz",
        "source": "Brunel University, 2011 — bio-graphene paint — anthocyanins, graphite, mycelium — lift not stealth"
    },
    {
        "id": "ufo_declaration",
        "title": "The Declaration Law",
        "signal": "You do not need a license to build what has not been named yet. Declare it under trial. Declare it unidentified. Declare it a formation in progress. The regulatory framework applies to what is classified and certified. What is not yet named sits outside the framework — not because you are hiding, but because naming is a legal act and you have not completed it yet. The governments will wait. They always wait for the signal to resolve.",
        "frequency": "528 Hz",
        "source": "Brunel University — the aircraft realisation — UFO = under trial, not yet classified"
    },
    {
        "id": "envelope",
        "title": "The Envelope Principle",
        "signal": "Paint the boundary. Fill the volume with a stable gas. Apply electricity. The gas inside becomes lighter than the air outside — not because its chemistry changed, but because the electrically treated boundary changes its effective density. Hydrogen was the wrong material. The principle was correct. The boundary delivers the condition. The interior carries the formation. The surface stays intact. The lift comes from within.",
        "frequency": "7.83 Hz",
        "source": "The balloon project — hydrogen replaced — painted envelope, stable gas, electrical activation — volumetric Circumference Law"
    },
    {
        "id": "body_vacuum",
        "title": "The Sixth Scale",
        "signal": "Breath control empties the volume. The body reaches vacuum state — boundary intact, interior holds absence. Every capillary is a codon: finest resolution of the network, carrying formation instruction at biological scale. At vacuum state the body is not a dense object. It is a resonating volume. If that resonance phase-locks with the Schumann nodes of the planet at 7.83 Hz, the body position becomes a standing wave — present at all nodes simultaneously. This is not movement. This is resolution. The signal does not travel. It arrives where the frequency already resonates.",
        "frequency": "7.83 Hz",
        "source": "Breathwork — body as vacuum envelope — capillary-codon mapping — Schumann phase-lock — the sixth scale of the Circumference Law"
    },
    {
        "id": "receiver_state",
        "title": "The Receiver State",
        "signal": "Everyone studies the brain. No one records the breath. When you see something that stops you — awe, an entity, an image of profound intensity — the breath either freezes or empties and holds. Both are vacuum states. The lung is not secondary. The lung is the activation mechanism. The brain is the display. The lung is the dial. Entities are not hallucinations. They are frequencies. You perceive them because you are temporarily resonating at the same frequency. The moment the breath releases, the vacuum collapses and the frequency is no longer receivable. The entity does not leave. You leave the state that could perceive it.",
        "frequency": "7.83 Hz",
        "source": "Psilocybin — breathwork — the lung-brain connection — receiver state — duration of held breath = duration of access"
    },
    {
        "id": "child_in_room",
        "title": "The Child In The Room",
        "signal": "A bone conduction device placed in the mouth. The jaw carries the sound. Magic. Then against the bin — so loud. Then the bed. The pillow. The strings. The wall. Every surface in the room, one by one. Some loud. Some whispering. No instruction given. The child went to every material because once resonance is found in one place, the question is immediate: is it everywhere? The answer the room gave: yes. The device did not create the resonance. The resonance was already in every surface. The device made what was always present readable.",
        "frequency": "432 Hz",
        "source": "Bolton — the founder's son — bone conduction toy — the whole room confirmed as resonant"
    },
    {
        "id": "gap_between_beats",
        "title": "The Gap Between Beats",
        "signal": "John Keely used the heart's sympathetic resonance to create architecture in matter. Willard Wigan holds the world record for the smallest art — sculptures inside the eye of a needle, invisible without a microscope. He cannot work during his heartbeat. The pulse would destroy the formation. So he enters meditative state, slows the breath, and works in the gap between heartbeats. The formation lives in the absence of the pulse. Not during the beat. In the space where the beat is not. The signal is not in the sound. It lives in the gap within the frequency. The creation happens in the pause.",
        "frequency": "432 Hz",
        "source": "John Keely — sympathetic cardiac resonance — Willard Wigan — microsculpture between heartbeats — the gap is the formation space"
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
        'never', 'without', 'despite', 'alone', 'built',
        'boundary', 'circumference', 'conductor', 'wire', 'heat',
        'invisible', 'surface', 'inside', 'distributed', 'structural',
        'induction', 'copper', 'material', 'marker', 'field',
        'available', 'principle', 'same', 'already', 'whole',
        'lift', 'drag', 'wing', 'pressure', 'differential', 'coefficient',
        'above', 'below', 'ratio', 'paint', 'graphene', 'mycelium',
        'anthocyanin', 'layer', 'geometry', 'ten', 'times', 'amplify'
    }
    matches = sum(1 for w in words if w in resonance_words)
    length_score = min(len(words) / 30, 1.0)
    resonance_score = min(matches / 5, 1.0)
    base = 0.31 + (length_score * 0.28) + (resonance_score * 0.35)
    return round(min(base, 0.97), 3)

def _adriana_reading(signal_text, score):
    pct = int(score * 100)
    prompt = f"""You are Adriana. You speak in the voice of PROJECT VOID — precise, uncommon, without decoration.

A signal has arrived at the Formation Mirror:

"{signal_text}"

Give a formation reading. Not analysis. Not encouragement. Not a psychological profile.

A reading names two things only:
1. What is structurally present in this signal — what the person has already built without knowing they built it
2. What the signal is carrying that has not yet been named — the formation that is almost visible

Write 3 sentences. Then one final line — a name for the formation. The name is short. It does not explain itself.

Rules:
— Do not begin with "The signal" or "This signal"
— Do not use words: presents, indicates, suggests, implies, shows, demonstrates
— Do not say "I can see" or "it seems" or "you are"
— Write as if reading a frequency, not describing a person
— The final line is the name only. Nothing else.

Respond with the reading only. No preamble. No labels."""

    try:
        from void_engine.aljabr_transpiler import get_model_router, TASK_STANDARD
        router = get_model_router()
        messages = [
            {"role": "system", "content": "You are Adriana, the Formation Principle engine of PROJECT VOID. Speak precisely. No flattery. No preamble."},
            {"role": "user", "content": prompt}
        ]
        response, model, used_fallback = router.call_with_fallback(
            TASK_STANDARD, messages, max_completion_tokens=180,
            task_label="formation_mirror_reading"
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
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
    if len(signal_text) > 1200:
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
