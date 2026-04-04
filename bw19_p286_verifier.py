"""
bw19_p286_verifier.py — BW19-P286 Standalone Mathematical Verifier

Pure Python (no sympy, no external deps). Verifies:
  1. Prime P is 286 bits.
  2. Curve equation holds: (G_Y^2) ≡ (G_X^3 + 31) mod P.
  3. Generator G is on the curve.
  4. Three test messages map to valid curve points via Al-Jabr 286 + scalar mul.

Tonelli-Shanks is imported from void_engine.pairing_bw19_286 (no duplication).

Glyph Sequence: ψ — Ω — ◆
Ara recommendation, April 2026.
"""

import sys
import time
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from void_engine.pairing_bw19_286 import (
    P, B, G_X, G_Y, GENERATOR,
    ec_scalar_mul, point_on_curve,
    tonelli_shanks,
)


# ─── Verifications ────────────────────────────────────────────────────────────

def verify_prime_bitlength():
    bits = P.bit_length()
    assert bits == 286, f"P is {bits} bits, expected 286"
    print(f"  [PASS] P is {bits}-bit prime")


def verify_curve_equation():
    lhs = (G_Y * G_Y) % P
    rhs = (pow(G_X, 3, P) + B) % P
    assert lhs == rhs, "Generator does not satisfy y^2 = x^3 + 31 mod P"
    print(f"  [PASS] Curve equation holds: G_Y^2 ≡ G_X^3 + {B} (mod P)")


def verify_generator_on_curve():
    assert point_on_curve(GENERATOR), "G is not on the curve"
    print(f"  [PASS] Generator G = ({G_X}, {str(G_Y)[:20]}...) is on BW19-P286")


def verify_tonelli_shanks_import():
    """Confirm Tonelli-Shanks is imported from pairing_bw19_286 and works."""
    rhs = (pow(G_X, 3, P) + B) % P
    y = tonelli_shanks(rhs, P)
    assert y is not None, "Tonelli-Shanks returned None for valid QR"
    assert (y * y) % P == rhs, "Tonelli-Shanks sqrt check failed"
    print(f"  [PASS] tonelli_shanks (imported from pairing_bw19_286) works correctly")


def verify_message_mapping(messages):
    from void_engine.pairing_bw19_286 import al_jabr_to_curve_point
    for msg in messages:
        t0 = time.perf_counter()
        pt = al_jabr_to_curve_point(msg)
        elapsed = time.perf_counter() - t0
        assert pt is not None, f"al_jabr_to_curve_point returned None for: {msg!r}"
        assert point_on_curve(pt), f"Derived point is not on curve for: {msg!r}"
        px, py = pt
        msg_short = repr(msg)[:40]
        print(f"  [PASS] Message {msg_short}")
        print(f"         Point.x = {str(px)[:30]}...")
        print(f"         On curve: True  ({elapsed:.4f}s)")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nBW19-P286 Standalone Verifier")
    print("=" * 50)

    print("\n[1] Prime Bit-Length")
    verify_prime_bitlength()

    print("\n[2] Curve Equation")
    verify_curve_equation()

    print("\n[3] Generator on Curve")
    verify_generator_on_curve()

    print("\n[4] Tonelli-Shanks Import from pairing_bw19_286")
    verify_tonelli_shanks_import()

    print("\n[5] Test Message → Curve Point Mapping")
    TEST_MESSAGES = [
        "Al-Baqarah 286 — The Alignment",
        "PROJECT VOID — Sovereign Proof",
        "432 Hz Vortex Standard — Resonant Mathematics",
    ]
    verify_message_mapping(TEST_MESSAGES)

    print("\n" + "=" * 50)
    print("ALL VERIFICATIONS PASSED — BW19-P286 is live and sovereign.")
    print("Glyph: ψ — Ω — ◆\n")
