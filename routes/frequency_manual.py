"""
What Is Pushing The Sand — A Frequency Manual
================================================
Route: GET /frequency-manual              — The 12-step demonstration document
Route: GET /frequency-manual/narration/manifest — JSON segment list
Route: GET /frequency-manual/narration/<int:index> — LSB-encoded narration WAV

Each segment: TTS (fable voice) → 16-bit WAV → LSB encode the spoken text
into the carrier at 432 Hz. The audio that explains steganography contains its
own text, hidden inside itself. The Formation Principle is the carrier.
"""

import os
import subprocess
import tempfile
import logging
from flask import Blueprint, render_template, jsonify, send_file, abort

frequency_manual_bp = Blueprint("frequency_manual", __name__)
logger = logging.getLogger(__name__)

AUDIO_DIR = os.path.join("static", "audio", "frequency_manual")

NARRATION_SEGMENTS = [
    (
        "introduction",
        """What Is Pushing The Sand.

A twelve-step manual for demonstrating the Formation Principle.
No claims. Only instructions. Total cost of all experiments: under one hundred pounds.

This document does not ask you to believe anything.
It asks you to do twelve things.
After the twelfth, you will have the answer — not because this document gave it to you,
but because the experiment gave it to you.

The experiment cannot be argued with.
It can only be done or not done."""
    ),
    (
        "step_01_02",
        """Step One: What You Need.

Every experiment in this document uses only materials available online or in a hardware store.
None of them require a laboratory. None require a degree. None require anyone's permission.

You need: a Bluetooth speaker or phone speaker, any size.
A metal plate or tray — flat, rigid, any size.
Fine sand, salt, or flour.
A four hundred and thirty two hertz tone — free, downloadable, generatable online.
Ferrofluid — optional, for later steps.
And a phone camera, to record what you see.

That is the full equipment list. What you are about to observe with these materials
was first recorded in seventeen eighty seven and has been sitting in physics textbooks ever since.
The experiment has never been hidden. Only the next question was missing.

Step Two: The First Experiment.

Place your metal plate flat on a surface. Sprinkle a thin, even layer of sand across the entire plate.
Connect your speaker directly beneath the plate, or rest the plate on the speaker.

Play a four hundred and thirty two hertz tone through the speaker.
Start at low volume and gradually increase until the sand begins to move.

Watch the plate. Watch the sand. Do not look away.

The sand will move. It will not scatter randomly. It will organise itself
into a precise geometric pattern — lines, curves, symmetrical forms —
depending on the frequency and the size of your plate.
The pattern will hold as long as the tone holds.

This phenomenon was first documented by Ernst Chladni in seventeen eighty seven.
He called the patterns Chladni figures. They appear at every frequency.
Every frequency produces a different pattern.
The pattern is a direct expression of the frequency.
Stop the tone — the pattern dissolves. Start it again — the same pattern returns. Exactly."""
    ),
    (
        "step_03_04",
        """Step Three: What Everyone Saw.

For two hundred and thirty eight years, since seventeen eighty seven,
every physicist, every student, every curious person who has done this experiment
has seen the same thing: the sand moves to specific lines.

These lines are called nodal lines.
They are the points on the plate where the vibration is zero.
The plate vibrates everywhere except at the nodal lines.
The sand migrates away from where the plate moves most,
and collects at the lines where the plate is still.

This is the accepted explanation. It is correct as far as it goes.

But it does not go far enough.
It tells you where the sand goes.
It does not tell you what is pushing it there.

For two hundred and thirty eight years, that question was not asked.
Not because it was forbidden.
Because the accepted explanation felt complete.
The sand goes to the nodal lines because that is where the plate is still.
The explanation stops there.

This document does not stop there.

Step Four: The Question No One Asked.

The plate vibrates. The sand moves.
The accepted explanation says: the sand moves because the plate vibrates.

But the plate does not touch every grain of sand equally.
There is a space between the plate and the sand.
There is a space between the grains of sand themselves.

What is in that space?
What is between the plate and the sand?
What is between the grains?
What is actually pushing them?

Now go back to the experiment. Look not at where the sand collects.
Look at the sand that is moving toward the nodal line.
Watch a single grain. It does not slide smoothly along the plate. It climbs.
At the edge of the collection point, the sand is pushing upward —
as though trying to go higher than the plate surface.
The sand at the mound is pressing against itself.
The grains at the top pushing outward and upward.

The plate is flat. The plate is not pushing the sand upward. Something else is."""
    ),
    (
        "step_05_06",
        """Step Five: What Is Between The Sand.

When the plate vibrates at four hundred and thirty two hertz,
it does not only move the plate. It moves the air.
The plate pushes the air above it in rhythmic compressions and expansions —
four hundred and thirty two times per second.
This creates a standing wave in the air above the plate.

A standing wave is not a wave that travels. It is a wave that stays.
It has fixed points of maximum compression — antinodes —
and fixed points of zero compression — nodes.
The geometry of these points is determined entirely by the frequency.
Not by the plate. Not by the sand. By the frequency.

The standing wave in the air above the plate is a pressure field.
It exists between the plate and the sand.
It exists between the grains of sand themselves.

The answer is this:
The sand does not respond to the plate.
The sand responds to what the plate wrote into the air.
The pressure field is what is pushing the sand.

This pressure field — acoustic radiation pressure —
was first described mathematically by Lord Rayleigh in nineteen oh two.
The mathematics exists.
But the mathematics was never used to ask the next question:
if the frequency writes itself into the space before it reaches the material —
what does the material carry after the frequency has passed?

Step Six: Why The Sand Climbs.

The pressure field does not only have a horizontal component.
It has a vertical component.
The standing wave in the air above the plate has nodes
not just across the surface but upward through the air column.
The pressure at the nodal line pushes inward from all horizontal directions —
which is why the sand collects there.
But it also pushes upward from below.

The sand climbs because the frequency is trying to lift it.

Increase the volume gradually while watching the sand mounds at the nodal lines.
At higher amplitude, the mounds will grow taller before the sand spills back.
At sufficient amplitude — far beyond a phone speaker —
sand particles levitate briefly above the plate surface before falling back.
This is acoustic levitation at micro scale.
It is the same phenomenon used in laboratories to levitate water droplets,
polystyrene beads, and small biological specimens in mid-air using only sound.

What is holding the sand down at normal volume is gravity.
What is pushing it up is the pressure field.
The mound is the negotiation between them.
Gravity pulls down. Frequency pushes up. The mound is the compromise.

Remove gravity — or increase frequency intensity until the frequency overcomes gravity —
and the sand does not form mounds. It levitates.
In the exact three-dimensional geometry of the nodal field. Hanging in mid-air.
In the shape of the frequency.

This is not theoretical. This is in laboratories today."""
    ),
    (
        "step_07_08",
        """Step Seven: What The Material Carries.

Stop the tone. The sand pattern dissolves.
The sand is still there. The plate is still there.
But the pattern is gone.

Now: UV-curable resin.
Pour a thin layer of UV resin mixed with a small amount of surfactant onto the plate.
Play the four hundred and thirty two hertz tone.
Watch the surface of the resin — a bubble will form and inflate in the sound,
taking the geometry of the Faraday membrane resonance —
the same standing wave, now expressed on a liquid surface.

At the moment of peak resonance — when the surface pattern is most defined —
shine a UV torch on the resin. The resin cures.
The frequency stops. The pattern remains. Permanently.
Frozen into the material at the moment the frequency was present.

What you now hold:
A solid object that carries the formation record of a frequency.
The frequency is no longer present.
The material is the memory of it.
The geometry of four hundred and thirty two hertz, frozen into matter.
Permanent. Photographable. Measurable.

The edge geometry of this cured object is unique.
It is a physical key — a cryptographic signature produced not by computation
but by frequency and matter.
No two cures produce identical geometry. Every sphere is a unique formation record.

This is Physical Key Cryptography. A new discipline. Founded eighth of April, twenty twenty six.

Step Eight: Where The Mathematics Stops.

The mathematics of resonance is not wrong.
Wave equations, boundary conditions, acoustic radiation pressure —
all of it is correct. All of it is in the textbooks.
All of it describes exactly what you have just observed.

The mathematics stops at the right answer to the wrong question.

Standard question: Where does the sand go?
Standard answer: To the nodal lines. Correct.

Standard question: What is the force on the sand?
Standard answer: Acoustic radiation pressure. Correct.

Missing question: What does the material carry after the frequency stops?
Answer: Formation record. No standard framework exists.

Missing question: What is the formation record of material formed at a node?
Answer: The geometry of the frequency — inherited. Permanent.

The mathematics is not wrong. The questions being asked of it are incomplete.
Every experiment in this document is described correctly by existing mathematics.
The formation record is not described.
Not because it cannot be. Because it has not yet been written."""
    ),
    (
        "step_09_10",
        """Step Nine: The Same Principle Everywhere.

Everything you have observed so far is acoustic — sound-based.
The principle is not limited to sound.

Fourth experiment — ferrofluid.
Place a shallow dish of ferrofluid on the speaker. Play four hundred and thirty two hertz.
The ferrofluid surface will form spike patterns — the Rosensweig instability —
organised by the resonance field.
The same geometry. Different material. Liquid, not solid. Magnetic, not acoustic.
Same frequency. Same pattern.

Fifth experiment — water.
Fill a bowl to the brim with water. Place it on or beside the speaker.
Play four hundred and thirty two hertz.
The water surface will form standing wave geometry —
concentric rings and interference patterns at the nodal points.
The same principle. Different material. Fluid.

Seven materials. One frequency. One geometric principle expressed differently in each.
Sound. Sand. Liquid. Solid resin. Plasma. Earth. Living mycelium.

Each substrate responds to the same frequency with the same geometric family of patterns.
The frequency is prior. The material is what expresses it. The material is the memory.

Step Ten: The Nodes The Ancients Found.

The earth has a resonance field.
The planet vibrates at a fundamental frequency — seven point eight three hertz —
the Schumann resonance.
The cavity between the earth's surface and the ionosphere acts as a standing wave chamber.
It has nodal geometry, as every standing wave system does.

The nodal points of the earth's resonance field are locations on the surface
where the field is most defined.
Where the conditions inside the field boundary are measurably different from the surrounding space.
Where the pressure field — the formation field — is strongest.

Every major tradition in human history — independently, across every continent —
recorded specific locations as places of unusual encounter.
Caves. Mountain peaks. River confluences. Desert formations.
They described them with the language they had:
holy ground, thin places, dimensional access, the seat of visions.

They were not describing magic. They were describing nodes.
Places where the earth's formation field creates a distinct boundary.
Where any responsive material formed inside the boundary inherits a different geometry.

The sand mound climbs because the frequency field above it has an upward component.
A person standing at a planetary node is inside a formation field.
Their body — a responsive material — is forming in the presence of a frequency
they cannot name but their nervous system can detect.
The shiver. The clarity. The sense of encounter with something prior to thought.

This is not metaphor. The experiment in step two is the same phenomenon at a different scale."""
    ),
    (
        "step_11_12",
        """Step Eleven: What You Now Know.

You have now done — or read the instructions for — five experiments.
Any of them can be done in a kitchen, in an hour, for under one hundred pounds.

What the experiments demonstrate, taken together:

First: Frequency creates geometry in the space around it before it reaches any material.
The pressure field is prior to the sand. The field is prior to the material.

Second: Material formed in the presence of a frequency inherits that frequency's geometry.
The resin sphere carries the formation record of four hundred and thirty two hertz. Permanently.

Third: The same frequency produces the same geometric family across different materials.
The frequency is the constant. The material is the variable.

Fourth: The formation record is permanent and unique.
No two cures are identical. The geometry is a physical key.
Unrepeatable by computation, reproducible only by the same frequency
acting on the same material under the same conditions.

Fifth: The principle scales.
From a kitchen speaker to the earth's electromagnetic cavity.
From sand on a plate to a person standing on ground
where the planetary formation field is most defined.

The Formation Principle:

Any responsive material, at the moment of formation,
inherits the geometry of the frequency present.
The frequency is prior.
The material is the memory.

Named eighth of April, twenty twenty six. PROJECT VOID.

This is not a claim. This is what the experiments show.
Anyone who has done steps two through seven has the evidence in their hands.

Step Twelve: Where To Go From Here.

This document ends here. The experiment does not.

The Formation Principle is a foundation, not a conclusion.
It opens seven directions, each requiring its own document, its own experiments, its own time.

Physical Key Cryptography — using formation records as cryptographic keys.
Every frequency-cured object is a unique, non-computable physical key.
The geometry is the passphrase.
The key cannot be duplicated by software. It can only be formed.

Resonance Node Portal — a rotating magnetic field device
that creates a nodal boundary in the electromagnetic domain.
The portal is not a door. It is a frequency writing itself into space clearly enough
that the boundary between inside and outside becomes observable and measurable.

Biostance Tracking — if the body is a responsive material,
its formation record changes in the presence of different frequencies.
Tracking which frequencies produce which formation states in a given body
is the beginning of frequency medicine.

Living Keys — mycelium grown in the presence of acoustic resonance at specific frequencies.
The mycelium grows toward the nodal lines, its structure shaped by the formation field.
A living organism that carries a frequency's geometry in its physical structure.

Every direction is buildable. Every direction is demonstrable. Every direction costs less than a car.
None of this requires a laboratory. None requires permission. None requires belief.
It only requires doing the experiment.

Author: Umar L.
Founder, PROJECT VOID.
Ninth of April, twenty twenty six. Manchester, England.
Document zero zero two. Open access. No rights reserved.

I do not ask you to accept this.
I ask you to get a speaker and some sand.
The sand will answer the question.
It has been answering it since seventeen eighty seven.
We just forgot to ask what was pushing it."""
    ),
]


STEGO_PASSPHRASE = "FORMATION_PRINCIPLE_VOID_432_UMAR_L"


def _get_openai_client():
    from openai import OpenAI
    return OpenAI()


def _ensure_audio_dir():
    os.makedirs(AUDIO_DIR, exist_ok=True)


def _get_segment_path(slug: str) -> str:
    return os.path.join(AUDIO_DIR, f"{slug}.wav")


def _tts_to_mp3_bytes(text: str) -> bytes:
    from openai import OpenAI
    client = OpenAI()
    words = text.split()
    chunks = []
    current = []
    current_len = 0
    for word in words:
        word_len = len(word) + 1
        if current_len + word_len > 4000:
            chunks.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len += word_len
    if current:
        chunks.append(" ".join(current))
    audio_bytes = b""
    for chunk in chunks:
        response = client.audio.speech.create(
            model="tts-1",
            voice="fable",
            input=chunk,
            response_format="mp3",
        )
        audio_bytes += response.content
    return audio_bytes


def _mp3_to_wav_16bit(mp3_bytes: bytes, wav_path: str):
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        tmp.write(mp3_bytes)
        tmp_mp3 = tmp.name
    try:
        subprocess.run(
            [
                "ffmpeg", "-y", "-i", tmp_mp3,
                "-ar", "44100",
                "-ac", "1",
                "-sample_fmt", "s16",
                wav_path
            ],
            check=True,
            capture_output=True,
        )
    finally:
        os.unlink(tmp_mp3)


def _encode_text_into_wav(wav_path: str, text: str, output_path: str):
    from void_engine.stega import encode
    from void_engine.compressor import compress_bytes
    payload = compress_bytes(text.encode("utf-8"))
    encode(
        carrier_path=wav_path,
        payload=payload,
        file_name="formation_principle",
        extension=".txt",
        output_path=output_path,
        lsb_depth=1,
        passphrase=STEGO_PASSPHRASE,
    )


def _generate_segment(slug: str, text: str) -> str:
    final_path = _get_segment_path(slug)
    if os.path.exists(final_path):
        return final_path

    logger.info("[FrequencyManual] Generating TTS + stego segment: %s", slug)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
        tmp_wav_path = tmp_wav.name

    try:
        mp3_bytes = _tts_to_mp3_bytes(text)
        logger.info("[FrequencyManual] TTS done for %s (%d bytes MP3)", slug, len(mp3_bytes))

        _mp3_to_wav_16bit(mp3_bytes, tmp_wav_path)
        logger.info("[FrequencyManual] WAV conversion done: %s", tmp_wav_path)

        _encode_text_into_wav(tmp_wav_path, text, final_path)
        logger.info("[FrequencyManual] Stego encoded: %s", final_path)

    except Exception:
        if os.path.exists(tmp_wav_path):
            os.unlink(tmp_wav_path)
        raise
    finally:
        if os.path.exists(tmp_wav_path):
            try:
                os.unlink(tmp_wav_path)
            except Exception:
                pass

    return final_path


@frequency_manual_bp.route("/frequency-manual")
def frequency_manual():
    return render_template("frequency_manual.html")


@frequency_manual_bp.route("/frequency-manual/narration/manifest")
def narration_manifest():
    segments = []
    for i, (slug, _text) in enumerate(NARRATION_SEGMENTS):
        segments.append({
            "index": i,
            "slug": slug,
            "url": f"/frequency-manual/narration/{i}"
        })
    return jsonify({"segments": segments, "total": len(NARRATION_SEGMENTS)})


@frequency_manual_bp.route("/frequency-manual/narration/<int:index>")
def narration_segment(index):
    if index < 0 or index >= len(NARRATION_SEGMENTS):
        abort(404)
    _ensure_audio_dir()
    slug, text = NARRATION_SEGMENTS[index]
    try:
        path = _generate_segment(slug, text)
        return send_file(path, mimetype="audio/wav", conditional=True)
    except Exception as e:
        logger.error("[FrequencyManual] Segment generation failed %d (%s): %s", index, slug, e)
        abort(500)
