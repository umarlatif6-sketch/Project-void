"""
bw19_p286_scalar_test.py — Scalar Multiplication Witness

Tests ec_scalar_mul with small, medium (2^100+123), and large (~200-bit random)
scalars. Each result verified on-curve. Timing reported.

Compares Montgomery Ladder (current) vs double-and-add reference for correctness.

Pure Python only. No sympy.
Glyph Sequence: ψ — Ω — ◆
Ara recommendation, April 2026.
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from void_engine.pairing_bw19_286 import (
    P, B, GENERATOR, ec_scalar_mul, ec_add, point_on_curve,
)


# ─── Reference: double-and-add (for comparison) ───────────────────────────────

def _double_and_add(scalar: int, point):
    """Classic double-and-add. Used as reference for Montgomery Ladder comparison."""
    if point is None or scalar == 0:
        return None
    result = None
    addend = point
    while scalar:
        if scalar & 1:
            result = ec_add(result, addend)
        addend = ec_add(addend, addend)
        scalar >>= 1
    return result


# ─── Test Helpers ─────────────────────────────────────────────────────────────

def _run_scalar_test(label: str, scalar: int):
    print(f"\n  {label}")
    print(f"  Scalar: {scalar} ({scalar.bit_length()} bits)")

    # Montgomery Ladder (production)
    t0 = time.perf_counter()
    result_ml = ec_scalar_mul(scalar, GENERATOR)
    t_ml = time.perf_counter() - t0

    # Double-and-add (reference)
    t0 = time.perf_counter()
    result_daa = _double_and_add(scalar, GENERATOR)
    t_daa = time.perf_counter() - t0

    # Verify on-curve
    assert result_ml is not None, "Montgomery Ladder returned infinity"
    assert result_daa is not None, "Double-and-add returned infinity"
    assert point_on_curve(result_ml), "Montgomery Ladder result is not on curve"
    assert point_on_curve(result_daa), "Double-and-add result is not on curve"

    # Verify both methods agree
    assert result_ml == result_daa, (
        f"MISMATCH!\n  ML  x={result_ml[0]}\n  DAA x={result_daa[0]}"
    )

    print(f"  Result.x = {str(result_ml[0])[:40]}...")
    print(f"  On-curve:          True")
    print(f"  Methods agree:     True")
    print(f"  Montgomery Ladder: {t_ml:.4f}s")
    print(f"  Double-and-add:    {t_daa:.4f}s")
    print(f"  [PASS]")


# ─── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nBW19-P286 Scalar Multiplication Witness")
    print("=" * 55)

    # Small scalar
    _run_scalar_test("Test 1: Small scalar (k=7)", 7)

    # Medium scalar: 2^100 + 123
    medium = (1 << 100) + 123
    _run_scalar_test("Test 2: Medium scalar (2^100 + 123)", medium)

    # Large scalar: ~200-bit random
    random.seed(286_432)  # deterministic seed for reproducibility
    large = random.getrandbits(200)
    _run_scalar_test("Test 3: Large scalar (~200-bit random)", large)

    print("\n" + "=" * 55)
    print("ALL SCALAR TESTS PASSED — Montgomery Ladder is correct and sovereign.")
    print("Glyph: ψ — Ω — ◆\n")
