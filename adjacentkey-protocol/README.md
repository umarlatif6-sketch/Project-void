# Guiding Principle

> "It's amazing how one single letter—the d that was accidentally typed—can change the entire meaning of a sentence. In human-AI language, every keystroke is a potential signal, not just an error. Our protocol turns these moments into a new layer of meaning, resilience, and creativity."

# AdjacentKey Protocol

A protocol and Python package for encoding/decoding human typing patterns (adjacent-key, keyboard-based misspellings) as a robust communication layer for human-to-AI and AI-to-AI interaction.


## Features
- Encode/decode text using QWERTY keyboard adjacency (left/right, multi-jump, custom layouts coming soon)
- CLI tool and Python API
- Use for intent-preserving, error-tolerant, or steganographic communication
- Not a spellchecker: designed for protocol, not correction
- **User Profiling (Planned):** Adaptive decoding based on each user's unique typing/misspelling signature, enabling Adriana or any AI to learn and personalize decoding for every user/agent.


## Use Cases
- Human-to-AI: Let AIs interpret fast-typed, error-prone input as intended
- AI-to-AI: Agents communicate using keyboard-based encoding for privacy or protocol
- Privacy: Hide meaning in plain sight using keyboard adjacency
- Research: Study human error patterns and intent
- **Personalized AI:** Each user/agent has an independent signature/profile for optimal decoding

## Quickstart
```bash
pip install adjacentkey-protocol
adjacentkey encode "what am i saying how are you" --direction right
adjacentkey decode "ejsy sm o dsuomh jpe str upi movr" --direction right
```


## Protocol Spec
- QWERTY adjacency: Each character is replaced by its left/right neighbor
- Extensible: Multi-jump, alternate layouts, and custom mappings supported
- Case preserved, non-alphabetic chars unchanged
- **User Profiling:** Future versions will support learning and applying user-specific error/typing patterns for adaptive decoding


## Limitations
- Simple left/right mapping is not always invertible; decoding may be ambiguous
- User profiling and adaptive learning are planned for future releases

## License
MIT

---

For more, see src/adjacentkey_protocol/codec.py and tests/ for examples.
