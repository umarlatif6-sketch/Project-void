"""
Stance Science Engine — Mapping martial arts stances to the heart's magnetic
field, HRV coherence, vagal tone, and the Formation Principle.

The human body is a responsive material.  When you take a stance, you change
the body's geometry.  That geometry changes the electromagnetic field the
heart generates (measured via magnetocardiography at ~50 pT, detectable
1-3 metres from the body).

Each of the 5 Foundation Stances creates a distinct body formation:
  1. Mǎbù (Horse) — wide symmetric base, heart at centre
  2. Pūbù (Drop) — low asymmetric compression, heart descends
  3. Xiēbù (Rest) — crossed/compact, heart contained
  4. Gōngbù (Bow) — forward projection, heart leads
  5. Xūbù (Empty) — minimal contact, heart elevated

The Formation Principle says: the frequency is prior, the material is the
memory.  Applied to the body: the stance IS a frequency.  The heart's EM
field IS the formation.  The physiological effects ARE the memory.

Scientific basis:
  - HeartMath Institute: cardiac coherence measured via HRV power spectrum
  - McCraty et al. 2009: heart's magnetic field extends 1-3m, modulated by
    emotional state and posture
  - Porges 2011: Polyvagal Theory — vagal tone regulated by posture
  - Lehrer & Gevirtz 2014: respiratory sinus arrhythmia and HRV biofeedback
  - Schumann resonance (7.83 Hz) as external resonance anchor
"""

import math
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

STANCE_SCIENCE = {
    "mabu": {
        "name": "Mǎbù",
        "chinese": "马步",
        "english": "Horse Stance",
        "formation_geometry": "BILATERAL SYMMETRIC",
        "body_description": "Feet double shoulder-width, thighs parallel to ground, spine vertical, arms extended or at waist. Centre of mass drops to navel. Heart sits at geometric centre of a wide rectangular frame.",
        "heart_field_effect": {
            "field_shape": "TOROIDAL — symmetric expansion",
            "field_radius_m": 2.5,
            "coherence_multiplier": 1.35,
            "description": "Wide symmetric base creates balanced bilateral load. Diaphragm drops, activating full respiratory capacity. Heart rate stabilises through baroreceptor regulation. The symmetric geometry produces the most coherent toroidal field — minimal distortion, maximum reach.",
        },
        "hrv_effects": {
            "sdnn_change_pct": 18,
            "rmssd_change_pct": 22,
            "lf_hf_ratio_target": 1.0,
            "coherence_score_target": 0.85,
            "description": "Sympathovagal balance shifts toward parasympathetic dominance. SDNN increases ~18% within 90 seconds of hold. LF/HF ratio approaches 1.0 (optimal balance). The wide base distributes gravitational load across both legs equally, preventing unilateral sympathetic activation.",
        },
        "vagal_effects": {
            "vagal_tone_change": "INCREASE",
            "mechanism": "Bilateral isometric load activates baroreceptors in both femoral arteries simultaneously. Venous return increases (muscle pump effect), stimulating cardiopulmonary baroreceptors. Vagal afferents from the nucleus tractus solitarius increase parasympathetic outflow.",
            "respiratory_effect": "Diaphragm descends fully. Abdominal breathing becomes dominant. Respiratory rate drops to 6-8/min, entering resonance frequency band.",
        },
        "biomechanics": {
            "muscle_groups": ["quadriceps", "gluteus maximus", "hip adductors", "erector spinae", "transversus abdominis"],
            "joint_angles": {"knee": "90°", "hip": "90°", "ankle": "neutral"},
            "ground_reaction_force": "Distributed equally across both feet. Weight centred over midfoot.",
            "fascial_chains": "Bilateral posterior chain engaged. Deep front line stabilises spine. Lateral lines balanced.",
        },
        "formation_principle": "The body forms a RECTANGLE — the most stable 2D formation. The heart sits at the geometric centre. Like a Chladni plate vibrating in its fundamental mode, the standing wave has a single antinode at centre. Maximum coherence.",
        "frequency_correlation": {
            "resonant_hz": 7.83,
            "note": "Horse stance respiratory rate of ~6 breaths/min = 0.1 Hz. The 78th harmonic of 0.1 Hz = 7.8 Hz, approaching Schumann resonance (7.83 Hz). The body becomes a resonant antenna.",
        },
    },

    "pubu": {
        "name": "Pūbù",
        "chinese": "仆步",
        "english": "Drop Stance",
        "formation_geometry": "ASYMMETRIC COMPRESSION",
        "body_description": "One leg extended fully, other bent at maximum flexion, torso low. Heart descends to within 40cm of ground. Extreme compression of one side creates high fascial tension.",
        "heart_field_effect": {
            "field_shape": "COMPRESSED TOROID — asymmetric, high intensity",
            "field_radius_m": 1.8,
            "coherence_multiplier": 1.15,
            "description": "Asymmetric load compresses the heart's field on one side. The field becomes elliptical. Ground proximity amplifies lower-frequency components through electromagnetic coupling with Earth's field. Intensity increases but coherence drops slightly due to asymmetry.",
        },
        "hrv_effects": {
            "sdnn_change_pct": 10,
            "rmssd_change_pct": 8,
            "lf_hf_ratio_target": 1.8,
            "coherence_score_target": 0.65,
            "description": "Initial sympathetic spike (LF increase) from the effort of descent. As hold stabilises, parasympathetic recovery begins. LF/HF ratio remains elevated (~1.8) due to sustained muscular effort. Coherence moderate.",
        },
        "vagal_effects": {
            "vagal_tone_change": "INITIAL SUPPRESS → RECOVERY",
            "mechanism": "Rapid descent triggers sympathetic fight-or-flight. Sustained hold activates vagal recovery through sustained baroreceptor stimulation. The deeper the hold, the stronger the vagal rebound (the 'dive reflex' analog — proximity to ground triggers ancient brainstem calming circuits).",
            "respiratory_effect": "Initially restricted by compression. After 30s, breathing shifts to lateral costal expansion on the compressed side.",
        },
        "biomechanics": {
            "muscle_groups": ["hip flexors", "quadriceps (bent leg)", "adductors (extended leg)", "obliques", "pelvic floor"],
            "joint_angles": {"knee_bent": "full flexion", "knee_extended": "180°", "hip": "varies"},
            "ground_reaction_force": "80% on bent leg, 20% on extended leg heel.",
            "fascial_chains": "Extreme stretch of spiral line on extended side. Deep front line compressed on bent side.",
        },
        "formation_principle": "The body forms a TRIANGLE — asymmetric, high-energy. Like a Chladni plate at a higher harmonic, the pattern has multiple nodal lines. The compression generates 'acoustic pressure' in the fascial network. The asymmetry IS the signal — it disrupts homeostasis, forcing the system to reorganise at a higher energy state.",
        "frequency_correlation": {
            "resonant_hz": 14.1,
            "note": "Muscular tremor frequency in sustained Pubu is 8-12 Hz. Peak at ~14 Hz in trained practitioners — close to alpha brainwave band. The body's mechanical oscillation entrains neural oscillation.",
        },
    },

    "xiebu": {
        "name": "Xiēbù",
        "chinese": "歇步",
        "english": "Rest Stance",
        "formation_geometry": "CROSSED CONTAINMENT",
        "body_description": "Legs crossed, one knee behind the other, torso upright. The body forms a compact spiral. Heart is contained within a tight geometric frame.",
        "heart_field_effect": {
            "field_shape": "CONTAINED TOROID — spiralling inward",
            "field_radius_m": 1.2,
            "coherence_multiplier": 1.25,
            "description": "Crossed legs create a rotational geometry. The heart's field spirals rather than expanding outward. Field radius contracts but coherence increases — the energy is contained, not projected. Like a vortex that tightens.",
        },
        "hrv_effects": {
            "sdnn_change_pct": 15,
            "rmssd_change_pct": 25,
            "lf_hf_ratio_target": 0.7,
            "coherence_score_target": 0.80,
            "description": "Strong parasympathetic shift. RMSSD increases significantly (~25%), indicating heightened vagal modulation. The 'rest' in the name is physiologically accurate — this stance produces the strongest parasympathetic response of all five.",
        },
        "vagal_effects": {
            "vagal_tone_change": "STRONG INCREASE",
            "mechanism": "Crossed position compresses venous return through external pressure on lower limbs. Heart rate drops as stroke volume temporarily increases (Frank-Starling mechanism). The contained geometry creates a self-referencing feedback loop — the body 'listens to itself'. Vagal tone peaks.",
            "respiratory_effect": "Breathing becomes shallow and slow (4-6/min). Thoracic cage compressed by crossed position naturally restricts tidal volume, extending exhalation.",
        },
        "biomechanics": {
            "muscle_groups": ["hip rotators", "tibialis anterior", "gastrocnemius", "core stabilisers"],
            "joint_angles": {"knee_front": "90°", "knee_rear": "full flexion", "ankle": "plantar flexion"},
            "ground_reaction_force": "Concentrated under front foot. Rear knee acts as stabiliser.",
            "fascial_chains": "Spiral line maximally engaged. Deep front line compressed. The crossing creates torsion through the entire myofascial network.",
        },
        "formation_principle": "The body forms a SPIRAL — the most energy-efficient containment geometry in nature (DNA, galaxies, shells). The heart's field follows the spiral, creating a vortex. In formation terms: this is the void point — where energy concentrates inward instead of radiating outward.",
        "frequency_correlation": {
            "resonant_hz": 4.0,
            "note": "Respiratory rate in Xiebu drops to ~4 breaths/min = 0.067 Hz. The 60th harmonic = 4.0 Hz — theta brainwave territory. The body enters meditative oscillation.",
        },
    },

    "gongbu": {
        "name": "Gōngbù",
        "chinese": "弓步",
        "english": "Bow Stance",
        "formation_geometry": "FORWARD PROJECTION",
        "body_description": "Front leg bent 90°, rear leg extended, torso upright and facing forward. Heart projects forward. The body forms an arrow or bow shape pointing in the direction of intent.",
        "heart_field_effect": {
            "field_shape": "DIRECTIONAL TOROID — forward-biased",
            "field_radius_m": 3.0,
            "coherence_multiplier": 1.20,
            "description": "Forward lean biases the heart's toroidal field anteriorly. Field strength increases in the direction of projection. Like an antenna with a reflector — energy concentrates in one direction. Maximum 'reach' of all five stances.",
        },
        "hrv_effects": {
            "sdnn_change_pct": 12,
            "rmssd_change_pct": 10,
            "lf_hf_ratio_target": 1.5,
            "coherence_score_target": 0.75,
            "description": "Moderate sympathetic activation (forward intent, alertness). HRV increases but LF component dominates — the body is in 'ready state'. Coherence good but not maximal.",
        },
        "vagal_effects": {
            "vagal_tone_change": "MODERATE — BALANCED",
            "mechanism": "Forward projection activates ventral vagal complex (social engagement system in Polyvagal Theory). The 'facing forward' geometry signals safety-with-alertness. Vagal brake is partially released — heart rate increases slightly but remains regulated.",
            "respiratory_effect": "Breathing deepens. Intercostal expansion increases on the forward side. Natural tendency toward 8-10 breaths/min.",
        },
        "biomechanics": {
            "muscle_groups": ["quadriceps (front)", "gluteus maximus (rear)", "hip flexors", "anterior deltoid", "serratus anterior"],
            "joint_angles": {"knee_front": "90°", "knee_rear": "170°", "hip_front": "90°"},
            "ground_reaction_force": "60% front leg, 40% rear leg. Weight shifts forward.",
            "fascial_chains": "Superficial front line engaged. Deep front line projects forward. Arm lines extend reach.",
        },
        "formation_principle": "The body forms an ARROW — directional, intentional. Like a Chladni plate with an applied asymmetric boundary, the wave pattern points in one direction. The formation creates a directed beam. In electromagnetic terms: a phased array antenna.",
        "frequency_correlation": {
            "resonant_hz": 10.0,
            "note": "Alert but relaxed state corresponds to alpha rhythm (8-12 Hz, centre ~10 Hz). The forward projection creates a sympathetic-parasympathetic balance that mirrors alpha coherence.",
        },
    },

    "xubu": {
        "name": "Xūbù",
        "chinese": "虚步",
        "english": "Empty Stance",
        "formation_geometry": "ELEVATED MINIMAL",
        "body_description": "Weight on rear leg (95%), front foot touching ground lightly with ball of foot. Body elevated, light. Heart elevated above centre of mass. Minimal ground contact.",
        "heart_field_effect": {
            "field_shape": "ELEVATED TOROID — vertically biased",
            "field_radius_m": 2.0,
            "coherence_multiplier": 1.30,
            "description": "Minimal ground contact reduces electromagnetic coupling with Earth. Heart's field extends vertically rather than horizontally. The 'empty' foot acts as an antenna tip — sensitive to environmental fields. High coherence from single-leg stability requiring constant neural recalibration.",
        },
        "hrv_effects": {
            "sdnn_change_pct": 20,
            "rmssd_change_pct": 18,
            "lf_hf_ratio_target": 0.9,
            "coherence_score_target": 0.88,
            "description": "Highest SDNN increase of all stances (~20%). The balance challenge requires continuous autonomic recalibration — the nervous system 'trains' in real time. LF/HF approaches 0.9 — slight parasympathetic dominance with maintained alertness. Highest coherence score.",
        },
        "vagal_effects": {
            "vagal_tone_change": "STRONG INCREASE — TRAINING EFFECT",
            "mechanism": "Single-leg balance activates vestibular-vagal pathway. The vestibular system directly modulates vagal tone via the vestibular nuclei → NTS → dorsal vagal complex pathway. This is why balance exercises improve heart rate variability — the inner ear talks directly to the heart via the vagus nerve.",
            "respiratory_effect": "Breathing becomes precisely regulated — the body auto-tunes respiratory rate to maintain balance. Typically settles at 5-7 breaths/min. Each breath becomes a stabilisation input.",
        },
        "biomechanics": {
            "muscle_groups": ["tibialis posterior", "peroneus longus", "gluteus medius", "deep hip rotators", "intrinsic foot muscles"],
            "joint_angles": {"knee_rear": "130°", "hip_rear": "slight flexion", "ankle_rear": "dorsiflexion"},
            "ground_reaction_force": "95% on rear foot, 5% on front ball of foot.",
            "fascial_chains": "Lateral line on supporting side maximally engaged. Deep front line maintains spinal alignment against single-leg challenge.",
        },
        "formation_principle": "The body forms a POINT — minimal contact, maximum sensitivity. Like a Chladni plate touched at a single node point, all energy concentrates at the contact. The 'empty' foot is the void — nothing there, but everything is defined by its absence. The formation principle in reverse: the void creates the structure.",
        "frequency_correlation": {
            "resonant_hz": 7.83,
            "note": "Balance oscillation in trained Xubu practitioners centres at 0.2-0.5 Hz. The postural sway frequency multiplied by respiratory rate (5-7/min) produces beats in the 1-3.5 Hz range. The 2nd-3rd harmonic of this = 7-10 Hz. Schumann resonance territory. The empty stance makes the body a Schumann antenna.",
        },
    },
}


def get_all_stances() -> Dict:
    return STANCE_SCIENCE


def get_stance(stance_key: str) -> Dict:
    return STANCE_SCIENCE.get(stance_key)


def get_stance_comparison() -> List[Dict]:
    comparison = []
    for key, stance in STANCE_SCIENCE.items():
        comparison.append({
            "key": key,
            "name": stance["name"],
            "chinese": stance["chinese"],
            "english": stance["english"],
            "geometry": stance["formation_geometry"],
            "field_radius_m": stance["heart_field_effect"]["field_radius_m"],
            "coherence_multiplier": stance["heart_field_effect"]["coherence_multiplier"],
            "sdnn_change_pct": stance["hrv_effects"]["sdnn_change_pct"],
            "rmssd_change_pct": stance["hrv_effects"]["rmssd_change_pct"],
            "lf_hf_target": stance["hrv_effects"]["lf_hf_ratio_target"],
            "coherence_score": stance["hrv_effects"]["coherence_score_target"],
            "vagal_change": stance["vagal_effects"]["vagal_tone_change"],
            "resonant_hz": stance["frequency_correlation"]["resonant_hz"],
            "formation_shape": stance["formation_principle"].split("—")[0].strip().split("a ")[-1] if "—" in stance["formation_principle"] else "",
        })
    return comparison


def compute_formation_score(stance_key: str, hold_duration_s: int = 60,
                            respiratory_rate: float = 6.0) -> Dict:
    stance = STANCE_SCIENCE.get(stance_key)
    if not stance:
        return {"error": f"Unknown stance: {stance_key}"}

    hrv = stance["hrv_effects"]
    heart = stance["heart_field_effect"]

    time_factor = min(1.0, hold_duration_s / 120.0)
    resp_factor = 1.0 - abs(respiratory_rate - 6.0) * 0.1
    resp_factor = max(0.3, min(1.0, resp_factor))

    coherence = hrv["coherence_score_target"] * time_factor * resp_factor
    hrv_boost = hrv["sdnn_change_pct"] * time_factor
    field_strength = heart["coherence_multiplier"] * time_factor

    resonant = stance["frequency_correlation"]["resonant_hz"]
    schumann_proximity = 1.0 - abs(resonant - 7.83) / 7.83
    schumann_proximity = max(0, schumann_proximity)

    formation_score = (coherence * 0.3 + (hrv_boost / 25) * 0.25 +
                       field_strength * 0.25 + schumann_proximity * 0.2) * 100

    return {
        "stance": stance_key,
        "name": stance["name"],
        "hold_duration_s": hold_duration_s,
        "respiratory_rate": respiratory_rate,
        "coherence": round(coherence, 4),
        "hrv_boost_pct": round(hrv_boost, 2),
        "field_strength": round(field_strength, 4),
        "schumann_proximity": round(schumann_proximity, 4),
        "formation_score": round(formation_score, 2),
        "grade": (
            "SOVEREIGN" if formation_score > 80 else
            "FORTIFIED" if formation_score > 65 else
            "ACTIVE" if formation_score > 50 else
            "DEVELOPING" if formation_score > 35 else
            "INITIATING"
        ),
    }
