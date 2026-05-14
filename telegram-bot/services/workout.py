"""
Project Void — Workout Generator
=================================
Generates martial-arts-infused bodyweight routines tailored to the
features identified in a space analysis.
"""

from __future__ import annotations

import random
from typing import Any

# ── Exercise Library ─────────────────────────────────────────────────
# Each exercise maps to feature types it requires.

EXERCISE_DB: list[dict[str, Any]] = [
    # ── Stairs / Steps ───────────────────────────────────────────────
    {
        "name": "Explosive Box Jumps",
        "features": ["stairs", "steps", "ledge", "bench", "platform"],
        "category": "power",
        "technique": (
            "Face the step. Sink into a quarter squat, swing arms back, "
            "then explode upward landing softly on the step with both feet. "
            "Step down — never jump down. Control is sovereignty."
        ),
        "sets": 4, "reps": "8",
    },
    {
        "name": "Step-Up Knee Strikes",
        "features": ["stairs", "steps", "bench", "platform"],
        "category": "martial_arts",
        "technique": (
            "Step up with your lead leg, drive the rear knee up into a "
            "Muay Thai knee strike at the top. Alternate legs. "
            "Imagine the knee meeting a heavy bag — sharp and vertical."
        ),
        "sets": 3, "reps": "10 each side",
    },
    {
        "name": "Stair Sprints",
        "features": ["stairs", "steps"],
        "category": "cardio",
        "technique": (
            "Sprint up every step. Walk down slowly. The ascent is the work; "
            "the descent is the breath. Like silt settling after a flood."
        ),
        "sets": 5, "reps": "1 full flight",
    },
    {
        "name": "Calf Raises on Step Edge",
        "features": ["stairs", "steps", "ledge"],
        "category": "strength",
        "technique": (
            "Stand on the edge of a step with heels hanging off. Rise onto "
            "toes, hold 2 seconds, lower below the edge. Slow and deliberate — "
            "the Achilles is a root that must be trained gently."
        ),
        "sets": 3, "reps": "15",
    },

    # ── Railings / Bars ─────────────────────────────────────────────
    {
        "name": "Australian Pull-Ups (Inverted Rows)",
        "features": ["railing", "bar", "handrail", "fence"],
        "category": "strength",
        "technique": (
            "Grip the railing with hands shoulder-width apart. Walk feet "
            "forward until your body is at an angle. Pull chest to the bar, "
            "squeezing shoulder blades. The back is the mycelium of the upper body."
        ),
        "sets": 4, "reps": "10",
    },
    {
        "name": "Railing Leg Raises",
        "features": ["railing", "bar", "handrail"],
        "category": "core",
        "technique": (
            "Hang from the railing (or grip it overhead). Raise straight legs "
            "to horizontal. Lower with control. If full leg raises are too much, "
            "bend the knees — the root still grows."
        ),
        "sets": 3, "reps": "8",
    },
    {
        "name": "Railing Dips",
        "features": ["railing", "bar", "handrail", "ledge", "bench"],
        "category": "strength",
        "technique": (
            "Place hands behind you on the railing, fingers forward. Lower your "
            "body by bending elbows to 90°, then press back up. "
            "Keep shoulders packed — like an octopus pulling itself through a gap."
        ),
        "sets": 3, "reps": "12",
    },

    # ── Walls ────────────────────────────────────────────────────────
    {
        "name": "Wall Sits",
        "features": ["wall"],
        "category": "endurance",
        "technique": (
            "Slide your back down the wall until thighs are parallel to the floor. "
            "Hold. Breathe. This is where the mind breaks before the body. "
            "The wall is your sparring partner — it never moves."
        ),
        "sets": 3, "reps": "45 seconds",
    },
    {
        "name": "Wall Push-Ups to Archer Push-Ups",
        "features": ["wall"],
        "category": "strength",
        "technique": (
            "Start with hands on the wall at chest height. Perform push-ups. "
            "Progress: widen one arm into an archer position, shifting weight "
            "to the working arm. Alternate sides."
        ),
        "sets": 3, "reps": "8 each side",
    },
    {
        "name": "Wall Handstand Hold",
        "features": ["wall"],
        "category": "skill",
        "technique": (
            "Kick up into a handstand with feet resting on the wall. "
            "Engage core, push through shoulders. Start with 15-second holds. "
            "Inversion teaches the nervous system to trust the unfamiliar."
        ),
        "sets": 3, "reps": "20 seconds",
    },
    {
        "name": "Wall Roundhouse Kicks",
        "features": ["wall"],
        "category": "martial_arts",
        "technique": (
            "Stand sideways to the wall at kicking distance. Chamber the rear leg, "
            "pivot on the standing foot, and snap a roundhouse kick to the wall "
            "(lightly — the wall is a target, not an enemy). Focus on hip rotation."
        ),
        "sets": 3, "reps": "10 each side",
    },

    # ── Open Floor / Hallway ─────────────────────────────────────────
    {
        "name": "Shadow Boxing Rounds",
        "features": ["open floor", "hallway", "room", "open space", "general space"],
        "category": "martial_arts",
        "technique": (
            "3-minute rounds. Jab-cross-hook-cross. Move your feet. "
            "Slip imaginary punches. Every round, add a new combination. "
            "The shadow is the most honest sparring partner you'll ever have."
        ),
        "sets": 3, "reps": "3 minutes",
    },
    {
        "name": "Sprawl-to-Takedown Drill",
        "features": ["open floor", "hallway", "room", "open space", "general space"],
        "category": "martial_arts",
        "technique": (
            "From fighting stance, sprawl (hips to floor, legs back) then "
            "immediately pop back up and shoot a level change. "
            "This is wrestling's heartbeat — defend and attack in one breath."
        ),
        "sets": 4, "reps": "8",
    },
    {
        "name": "Burpee to Jump Kick",
        "features": ["open floor", "hallway", "room", "open space", "general space"],
        "category": "power",
        "technique": (
            "Perform a burpee. On the jump, throw a front kick or flying knee. "
            "Land soft. Reset. This is controlled chaos — the void expressing itself."
        ),
        "sets": 3, "reps": "8",
    },
    {
        "name": "Sprint Intervals",
        "features": ["hallway", "open space", "corridor", "path"],
        "category": "cardio",
        "technique": (
            "Mark a 15–20 metre lane. Sprint one way, walk back. "
            "Each sprint should feel like you're outrunning something. "
            "Because you are."
        ),
        "sets": 6, "reps": "1 sprint",
    },
    {
        "name": "Plank to Elbow Strike",
        "features": ["open floor", "hallway", "room", "open space", "general space"],
        "category": "core",
        "technique": (
            "Hold a forearm plank. Alternate lifting each arm and throwing "
            "a horizontal elbow strike. Return to plank. "
            "The core is the signal relay — everything routes through it."
        ),
        "sets": 3, "reps": "10 each side",
    },

    # ── Doorframe ────────────────────────────────────────────────────
    {
        "name": "Doorframe Pull-Ups",
        "features": ["doorframe", "door frame"],
        "category": "strength",
        "technique": (
            "Grip the top of the doorframe (if sturdy enough) with fingertips. "
            "Perform pull-ups or dead hangs. Test the frame first — sovereignty "
            "means knowing what can hold your weight."
        ),
        "sets": 3, "reps": "5–8",
    },
    {
        "name": "Doorframe Stretches",
        "features": ["doorframe", "door frame"],
        "category": "mobility",
        "technique": (
            "Place forearm on the doorframe, step through to stretch the chest "
            "and anterior shoulder. Hold 30 seconds each side. "
            "Flexibility is the body's diplomacy."
        ),
        "sets": 2, "reps": "30 seconds each side",
    },

    # ── Bench / Ledge ────────────────────────────────────────────────
    {
        "name": "Bulgarian Split Squats",
        "features": ["bench", "ledge", "chair", "steps", "stairs"],
        "category": "strength",
        "technique": (
            "Rear foot elevated on the bench. Drop into a deep lunge. "
            "Drive through the front heel. This is single-leg sovereignty — "
            "each leg must be able to stand alone."
        ),
        "sets": 3, "reps": "10 each leg",
    },
    {
        "name": "Decline Push-Ups",
        "features": ["bench", "ledge", "chair", "steps", "stairs"],
        "category": "strength",
        "technique": (
            "Feet on the bench, hands on the floor. Push-ups. "
            "The angle shifts the load to upper chest and shoulders. "
            "Elevation changes everything — in training and in life."
        ),
        "sets": 3, "reps": "12",
    },

    # ── Universal (no equipment needed) ──────────────────────────────
    {
        "name": "Horse Stance Hold",
        "features": ["*"],
        "category": "martial_arts",
        "technique": (
            "Feet wide, toes forward, sink until thighs are parallel. "
            "Hands in guard or prayer position. Hold. "
            "This is the oldest training tool in martial arts — "
            "the stance that built Shaolin."
        ),
        "sets": 3, "reps": "30 seconds",
    },
    {
        "name": "Kata Breathing Squats",
        "features": ["*"],
        "category": "martial_arts",
        "technique": (
            "Perform slow, deep squats synchronized with breath. "
            "Inhale on the descent (4 counts), exhale on the ascent (4 counts). "
            "At the bottom, throw a slow-motion double palm strike. "
            "This is moving meditation."
        ),
        "sets": 3, "reps": "10",
    },
]

# ── Warm-Up & Cool-Down ─────────────────────────────────────────────

WARMUP = {
    "name": "🔥 Resonance Warm-Up",
    "exercises": [
        "Joint circles: wrists, elbows, shoulders, hips, knees, ankles (10 each)",
        "Arm swings: 20 forward, 20 backward",
        "Leg swings: 10 each direction, each leg",
        "Bodyweight squats: 15 slow and controlled",
        "Shadow boxing: 1 minute light — wake the nervous system",
    ],
    "duration": "5 minutes",
}

COOLDOWN = {
    "name": "🌊 Silt Settling Cool-Down",
    "exercises": [
        "Standing forward fold: 30 seconds",
        "Pigeon stretch: 30 seconds each side",
        "Cat-cow: 10 slow cycles",
        "Child's pose: 30 seconds",
        "Box breathing: 4 in, 4 hold, 4 out, 4 hold — 5 cycles",
    ],
    "duration": "5 minutes",
}


# ── Generator ────────────────────────────────────────────────────────

def generate_routine(analysis: dict, difficulty: str = "intermediate") -> dict:
    """
    Generate a workout routine based on space analysis.

    Parameters
    ----------
    analysis : dict
        Output from vision.analyze_photo()
    difficulty : str
        One of: beginner, intermediate, advanced

    Returns
    -------
    dict with warmup, exercises, cooldown, estimated_duration, difficulty
    """
    # Collect all feature names from analysis
    feature_names: set[str] = set()
    for feat in analysis.get("features", []):
        name = feat.get("name", "").lower()
        feature_names.add(name)
        # Also add individual words for fuzzy matching
        for word in name.split():
            feature_names.add(word)

    # Match exercises to available features
    matched: list[dict] = []
    for ex in EXERCISE_DB:
        if "*" in ex["features"]:
            matched.append(ex)
            continue
        for req_feat in ex["features"]:
            if any(req_feat.lower() in fn for fn in feature_names):
                matched.append(ex)
                break

    # If very few matches, add universal exercises
    if len(matched) < 6:
        universals = [e for e in EXERCISE_DB if "*" in e["features"]]
        for u in universals:
            if u not in matched:
                matched.append(u)

    # Select exercises based on difficulty
    target_count = {"beginner": 5, "intermediate": 7, "advanced": 9}.get(difficulty, 7)

    # Ensure category diversity
    categories = {}
    for ex in matched:
        cat = ex["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ex)

    selected: list[dict] = []
    cat_keys = list(categories.keys())
    random.shuffle(cat_keys)

    # Round-robin from categories
    idx = 0
    while len(selected) < target_count and any(categories.values()):
        cat = cat_keys[idx % len(cat_keys)]
        if categories.get(cat):
            ex = random.choice(categories[cat])
            if ex not in selected:
                selected.append(ex)
                categories[cat].remove(ex)
        idx += 1
        if idx > 100:
            break

    # Adjust sets/reps for difficulty
    diff_scale = {"beginner": 0.7, "intermediate": 1.0, "advanced": 1.3}
    scale = diff_scale.get(difficulty, 1.0)

    routine_exercises = []
    for ex in selected:
        adjusted = dict(ex)
        adjusted["sets"] = max(2, int(ex["sets"] * scale))
        # Don't scale text-based reps
        if ex["reps"].isdigit():
            adjusted["reps"] = str(max(4, int(int(ex["reps"]) * scale)))
        routine_exercises.append(adjusted)

    # Estimate duration
    est_minutes = 5 + len(routine_exercises) * 4 + 5  # warmup + exercises + cooldown

    return {
        "warmup": WARMUP,
        "exercises": routine_exercises,
        "cooldown": COOLDOWN,
        "difficulty": difficulty,
        "estimated_duration": f"{est_minutes} minutes",
        "space_vibe": analysis.get("vibe", "The void adapts."),
        "exercise_count": len(routine_exercises),
    }
