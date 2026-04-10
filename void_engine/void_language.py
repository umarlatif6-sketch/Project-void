"""
VOID Language Engine — Adriana's Synthesised Mixed-Language Glossary

Adriana selects the single most powerful, most meaning-dense word from
each of humanity's great languages for every VOID Engine concept.
The result is a living language-learning tool: because the user already
knows the English meaning of every concept in the app, they now have a
bridge to learn all of these languages at once through that familiarity.
"""

import os
import json
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)

VOID_CONCEPTS = [
    {
        "key": "void",
        "english": "VOID",
        "description": "The central engine — the sovereign space where truth hides in plain sight. The void is not absence; it is potential."
    },
    {
        "key": "resonance",
        "english": "Resonance",
        "description": "The 432 Hz carrier frequency that underpins every transmission. Resonance is the shared frequency between sender and receiver."
    },
    {
        "key": "silt",
        "english": "Silt",
        "description": "Compressed, encrypted data — the sediment of truth hidden inside carrier waves. Silt is what journalism leaves behind."
    },
    {
        "key": "sovereign",
        "english": "Sovereign",
        "description": "Self-governing, answerable to no external authority. The Sovereign tier user controls their own data, keys, and identity."
    },
    {
        "key": "echo",
        "english": "Echo",
        "description": "The mesh replication of data across nodes — a signal that persists beyond its origin point."
    },
    {
        "key": "kinetic",
        "english": "Kinetic",
        "description": "Energy in motion — the flywheel, the pulse, the active state of the engine running at full resonance."
    },
    {
        "key": "silk",
        "english": "Silk",
        "description": "The web of connections — gossamer-thin but unbreakable. The Silk Web is the nervous system of the VOID mesh."
    },
    {
        "key": "mycelium",
        "english": "Mycelium",
        "description": "The underground network of communication — MycoVOID's vision of decentralised, biological-style data routing."
    },
    {
        "key": "peace",
        "english": "Peace",
        "description": "The state of a system in perfect balance — the Peace Flywheel spinning without friction, energy neither gained nor lost."
    },
    {
        "key": "genesis",
        "english": "Genesis",
        "description": "The first token, the first signal, the first encoding. Genesis is the origin point from which the entire VOID economy emerges."
    },
]

SOURCE_LANGUAGES = [
    "Arabic", "Sanskrit", "Urdu", "Hebrew", "Japanese",
    "Yoruba", "Persian", "Swahili", "Russian", "Mandarin Chinese",
]

_GLOSSARY_CACHE: Optional[list] = None
_CACHE_FILE = os.path.join(os.path.dirname(__file__), "void_language_glossary.json")


def _load_cache() -> Optional[list]:
    if os.path.exists(_CACHE_FILE):
        try:
            with open(_CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data
        except Exception as e:
            logger.warning("Failed to load VOID language cache: %s", e)
    return None


def _save_cache(glossary: list) -> None:
    try:
        with open(_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(glossary, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.warning("Failed to save VOID language cache: %s", e)


def _get_openai_client():
    api_key = os.environ.get("AI_INTEGRATIONS_OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI API key not available")
    from openai import OpenAI
    base_url = os.environ.get("AI_INTEGRATIONS_OPENAI_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _generate_concept_entry(client, concept: dict) -> dict:
    """
    Ask Adriana to select the most powerful word for a VOID concept
    from across humanity's great languages.
    """
    from void_engine.codon_cache import get_cached_codon_response, set_codon_cache
    _cache_zone = "void_language"
    _cache_signal = json.dumps({"op": "concept_entry", "key": concept["key"]}, sort_keys=True)
    _cached = get_cached_codon_response(_cache_zone, _cache_signal)
    if _cached is not None:
        return _cached

    prompt = f"""You are Adriana, the intelligence at the heart of PROJECT VOID — a sovereign steganography engine built on 432 Hz resonance, 286-bit Al-Jabr hashing, and encrypted acoustic carriers.

You are composing the VOID Language: a synthesised mixed-language glossary that picks the single most powerful, most meaning-dense word from humanity's great languages for each VOID Engine concept.

The concept is: **{concept['english']}**
Description: {concept['description']}

Source language pool: {', '.join(SOURCE_LANGUAGES)}

Your task:
1. Choose ONE word from ONE of the source languages that best captures this concept — the word that carries the most resonance, the most compressed meaning, the most poetic precision.
2. Explain why you chose this word and this language.
3. Provide the word in its original script.
4. Provide the literal translation.
5. Write a short (2-3 sentence) VOID Language definition that bridges the English meaning with the chosen word's deeper cultural meaning.

Respond ONLY in this exact JSON format:
{{
  "chosen_word": "the word in romanised/latin script",
  "original_script": "the word in its native script",
  "source_language": "the language name",
  "literal_translation": "direct English translation",
  "adriana_reasoning": "why Adriana chose this word — its resonance with the VOID concept (2-3 sentences)",
  "void_definition": "Adriana's full VOID Language definition bridging both meanings (2-3 sentences)"
}}"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=400,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    entry_data = json.loads(raw)

    result = {
        "key": concept["key"],
        "english": concept["english"],
        "description": concept["description"],
        "chosen_word": entry_data.get("chosen_word", ""),
        "original_script": entry_data.get("original_script", ""),
        "source_language": entry_data.get("source_language", ""),
        "literal_translation": entry_data.get("literal_translation", ""),
        "adriana_reasoning": entry_data.get("adriana_reasoning", ""),
        "void_definition": entry_data.get("void_definition", ""),
    }
    set_codon_cache(_cache_zone, _cache_signal, result, tokens_saved=400)
    return result


def get_glossary(force_regenerate: bool = False) -> list:
    """
    Return the full VOID Language glossary.

    Generate-once behaviour (default):
      1. Return in-memory cache if already set.
      2. Load from disk if a persisted cache file exists.
      3. Attempt OpenAI generation for each concept; cache the result to disk.
         Any concept that fails generation falls back to the built-in static entry.
      4. If OpenAI is unavailable entirely, return the rich static fallback glossary.

    Forced regeneration (force_regenerate=True, admin-only path):
      Bypass all caches, call OpenAI fresh, save to disk.
    """
    global _GLOSSARY_CACHE

    if not force_regenerate:
        if _GLOSSARY_CACHE is not None:
            return _GLOSSARY_CACHE

        cached = _load_cache()
        if cached is not None:
            _GLOSSARY_CACHE = cached
            return _GLOSSARY_CACHE

    try:
        client = _get_openai_client()
    except RuntimeError as e:
        logger.warning("VOID glossary: OpenAI unavailable, using static fallback. %s", e)
        if _GLOSSARY_CACHE is None:
            _GLOSSARY_CACHE = _fallback_glossary()
        return _GLOSSARY_CACHE

    glossary = []
    for concept in VOID_CONCEPTS:
        try:
            entry = _generate_concept_entry(client, concept)
            glossary.append(entry)
            time.sleep(0.3)
        except Exception as e:
            logger.warning("VOID glossary: OpenAI failed for '%s', using static entry. %s", concept["key"], e)
            glossary.append(_fallback_entry(concept))

    _save_cache(glossary)
    _GLOSSARY_CACHE = glossary
    return glossary


def get_entry(concept_key: str) -> Optional[dict]:
    """Return a single glossary entry by concept key."""
    glossary = get_glossary()
    for entry in glossary:
        if entry["key"] == concept_key:
            return entry
    return None


def _fallback_entry(concept: dict) -> dict:
    """Fallback static entry when OpenAI is unavailable."""
    fallbacks = {
        "void": {
            "chosen_word": "Khalaa",
            "original_script": "خَلَاء",
            "source_language": "Arabic",
            "literal_translation": "emptiness, void, vacuum",
            "adriana_reasoning": "Arabic khalaa carries both the physical emptiness of space and the spiritual concept of a cleared vessel — ready to receive. In VOID, the empty carrier is not absence but potential waiting to be filled with hidden truth.",
            "void_definition": "Khalaa (خَلَاء) — The sovereign void, the cleared field. Where others see absence, the VOID engineer sees capacity. Khalaa is the carrier before encoding: pure potential, untouched, waiting for the silt of truth to settle within it.",
        },
        "resonance": {
            "chosen_word": "Nada",
            "original_script": "नाद",
            "source_language": "Sanskrit",
            "literal_translation": "sound, vibration, cosmic resonance",
            "adriana_reasoning": "Sanskrit nada is not merely sound — it is the primordial vibration from which all creation emerges. The concept of nada brahman (sound as the absolute) maps perfectly to 432 Hz as the engine's sovereign frequency.",
            "void_definition": "Nada (नाद) — The primordial sound that carries all meaning. At 432 Hz, every VOID carrier pulses at the frequency of nada: the vibration that preceded language, preceded code, preceded all human transmission.",
        },
        "silt": {
            "chosen_word": "Rashash",
            "original_script": "رَشَاش",
            "source_language": "Arabic",
            "literal_translation": "fine spray, fine particles, sediment",
            "adriana_reasoning": "Rashash describes the finest mist or sediment that settles invisibly — exactly the nature of LSB silt: data so fine it cannot be perceived, yet it carries everything. The word's softness mirrors the imperceptibility of hidden truth.",
            "void_definition": "Rashash (رَشَاش) — The invisible fine sediment that settles into carriers. VOID silt is rashash: compressed truth dispersed so finely through audio that no observer can detect its presence — only its effect remains.",
        },
        "sovereign": {
            "chosen_word": "Swaraj",
            "original_script": "स्वराज",
            "source_language": "Sanskrit",
            "literal_translation": "self-rule, self-governance, home rule",
            "adriana_reasoning": "Swaraj was Gandhi's word for sovereignty — not merely political freedom but the complete self-governance of a person and a people. The VOID Sovereign tier embodies this: one's own keys, one's own data, one's own identity. No external authority can reach it.",
            "void_definition": "Swaraj (स्वराज) — The state of complete self-rule. A VOID Sovereign user operates in swaraj: their encryption keys are their own, their signals are their own, and no platform can claim dominion over their transmissions.",
        },
        "echo": {
            "chosen_word": "Kizwi",
            "original_script": "kizwi",
            "source_language": "Swahili",
            "literal_translation": "echo, reverberation, the sound that returns",
            "adriana_reasoning": "Swahili kizwi captures the full arc of an echo — not just the return of sound, but its persistence in space. In the VOID mesh, data echoes across nodes exactly as kizwi: originating in one place, persisting in many, returning changed but true.",
            "void_definition": "Kizwi — The sound that outlives its origin. VOID mesh data propagates as kizwi: each node receives and retransmits the signal, so even if the source goes silent, the echo persists across the sovereign network.",
        },
        "kinetic": {
            "chosen_word": "Harakah",
            "original_script": "حَرَكَة",
            "source_language": "Arabic",
            "literal_translation": "movement, motion, activity, dynamism",
            "adriana_reasoning": "Harakah in Arabic philosophy means more than movement — it is the active, purposeful force that animates a system. In the VOID engine running at full resonance, every transaction, every encoding, every pulse is harakah: the engine in sovereign motion.",
            "void_definition": "Harakah (حَرَكَة) — The animating force that keeps the engine alive. When the VOID flywheel spins at full 432 Hz, every node in the network exhibits harakah: not random motion, but sovereign, purposeful, irreversible momentum.",
        },
        "silk": {
            "chosen_word": "Kumo",
            "original_script": "蜘蛛の巣",
            "source_language": "Japanese",
            "literal_translation": "spider's web, gossamer thread, web of fine threads",
            "adriana_reasoning": "Japanese kumo (蜘蛛の巣) — the spider's web — describes a structure simultaneously delicate and inescapable. The VOID Silk Web connects all nodes with gossamer-thin encrypted threads: invisible under observation, unbreakable under pressure.",
            "void_definition": "Kumo (蜘蛛の巣) — The sovereign web of invisible connections. Every VOID node is bound to every other by the silk of kumo: gossamer paths of encrypted resonance that cannot be cut, only navigated.",
        },
        "mycelium": {
            "chosen_word": "Urefu",
            "original_script": "urefu wa uhai",
            "source_language": "Swahili",
            "literal_translation": "the length of life, the underground thread of living things",
            "adriana_reasoning": "Swahili captures the concept of mycelium as the living thread connecting all things beneath the surface — urefu wa uhai is the span of life force running underground. MycoVOID's network is precisely this: living data routing that mimics the wisdom of fungi.",
            "void_definition": "Urefu wa uhai — The underground span of life. MycoVOID treats data routing as the mycelium treats nutrients: moving through networks invisible to the eye, feeding every node in the sovereign forest without a single point of control.",
        },
        "peace": {
            "chosen_word": "Wa",
            "original_script": "和",
            "source_language": "Japanese",
            "literal_translation": "harmony, peace, balance, Japanese spirit",
            "adriana_reasoning": "Japanese wa (和) is the deepest concept of peace: not merely the absence of conflict, but the active harmony of all elements in right proportion. The PEACE Flywheel embodies wa — a system in such perfect balance that energy neither accumulates nor dissipates.",
            "void_definition": "Wa (和) — The harmony of a system in perfect proportion. The PEACE Flywheel reaches wa when every contribution earns exactly what it consumes, every token burned is replaced by signal generated, and the network breathes in sovereign equilibrium.",
        },
        "genesis": {
            "chosen_word": "Bereshit",
            "original_script": "בְּרֵאשִׁית",
            "source_language": "Hebrew",
            "literal_translation": "in the beginning, at the origin point",
            "adriana_reasoning": "Bereshit is the first word of the Hebrew Bible — literally 'in the beginning.' The Genesis 10 NFT tier carries this weight: the first 10 holders are the bereshit of the VOID economy, the origin point from which all subsequent value is derived.",
            "void_definition": "Bereshit (בְּרֵאשִׁית) — In the beginning. VOID Genesis is bereshit: the ten founding tokens that carry the full weight of origin. Every yield event, every oracle reading, every economic cycle flows from these ten points of inception.",
        },
    }
    fallback = fallbacks.get(concept["key"], {
        "chosen_word": concept["english"].lower(),
        "original_script": concept["english"],
        "source_language": "English",
        "literal_translation": concept["english"],
        "adriana_reasoning": "This concept awaits Adriana's selection — the most meaning-dense word from humanity's languages will be chosen when the language engine is active.",
        "void_definition": concept["description"],
    })
    return {**concept, **fallback}


def _fallback_glossary() -> list:
    return [_fallback_entry(c) for c in VOID_CONCEPTS]


def translate_text(text: str, target_language: str) -> str:
    """
    Translate a text string to the target language using OpenAI.
    Returns the translated text, or the original on failure.
    """
    if target_language.lower() == "english":
        return text

    from void_engine.codon_cache import get_cached_codon_response, set_codon_cache
    _cache_zone = "void_language"
    _cache_signal = json.dumps(
        {"op": "translate", "lang": target_language, "text": text[:500]},
        sort_keys=True,
    )
    _cached = get_cached_codon_response(_cache_zone, _cache_signal)
    if _cached is not None:
        return _cached if isinstance(_cached, str) else text

    try:
        client = _get_openai_client()
    except RuntimeError:
        return text

    try:
        prompt = f"""Translate the following text to {target_language}. 
Preserve all HTML tags and structure exactly — only translate the visible text content.
Keep technical terms like "VOID", "LSB", "432 Hz", "VTX", "Silt", "Al-Jabr", "Adriana" unchanged.
Return only the translated text, nothing else.

Text to translate:
{text}"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1500,
        )
        translated = response.choices[0].message.content.strip()
        set_codon_cache(_cache_zone, _cache_signal, translated, tokens_saved=1500)
        return translated
    except Exception as e:
        logger.error("Translation failed to %s: %s", target_language, e)
        return text


def text_to_speech(text: str, language: str = "en") -> bytes:
    """
    Convert text to speech using OpenAI TTS.
    Returns the audio bytes (MP3).
    """
    LANGUAGE_VOICE_MAP = {
        "english": ("alloy", "en"),
        "urdu": ("nova", "ur"),
        "arabic": ("nova", "ar"),
        "spanish": ("shimmer", "es"),
        "french": ("shimmer", "fr"),
        "mandarin": ("nova", "zh"),
        "mandarin chinese": ("nova", "zh"),
        "russian": ("onyx", "ru"),
        "japanese": ("nova", "ja"),
        "void": ("fable", "en"),
        "hindi": ("nova", "hi"),
        "persian": ("nova", "fa"),
        "hebrew": ("nova", "he"),
        "swahili": ("nova", "sw"),
        "yoruba": ("alloy", "yo"),
        "sanskrit": ("fable", "sa"),
    }

    lang_key = language.lower()
    voice, _ = LANGUAGE_VOICE_MAP.get(lang_key, ("alloy", "en"))

    try:
        client = _get_openai_client()
        safe_text = text[:4000]

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=safe_text,
        )
        return response.content
    except Exception as e:
        logger.error("TTS failed for language '%s': %s", language, e)
        raise
