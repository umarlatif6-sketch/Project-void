#!/usr/bin/env python3
"""
Beehive Live Audio Demo — PROJECT VOID

A command-line tool for demonstrating the Beehive acoustic mesh protocol
with real microphone and speaker I/O.

Usage:
    python scripts/beehive_demo.py --listen
        Record 2 seconds from the microphone, run detect_neighbor and
        Fatiha verification, print results.

    python scripts/beehive_demo.py --transmit
        Generate and play the 432 Hz handshake pulse through the speaker.

    python scripts/beehive_demo.py --loopback
        Full loopback self-test: transmit + record + verify (works without
        a second device when speaker output is captured by the same mic).

    python scripts/beehive_demo.py --simulate
        Run a purely in-memory two-node exchange (no audio hardware required).

Options:
    --duration SECONDS   Recording / pulse duration (default: 2.0)
    --passphrase TEXT     Beehive passphrase (default: void-432)
    --machine-id TEXT     Node machine ID (default: VOID-AUDIO-DEMO)
"""

import sys
import os
import argparse
import textwrap

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from void_engine.beehive import BeehiveProtocol, simulate_two_node_exchange
from void_engine.beehive_audio import BeehiveAudio, AUDIO_BACKEND


def _bar(value: float, width: int = 20, max_val: float = 1.0) -> str:
    filled = int(min(value / max_val, 1.0) * width)
    return "[" + "#" * filled + "-" * (width - filled) + "]"


def _header(title: str):
    print()
    print("=" * 60)
    print(f"  {title}")
    print("=" * 60)


def _print_detection(result: dict):
    print(f"  Node ID        : {result.get('node_id', 'N/A')}")
    print(f"  Mesh State     : {result.get('mesh_state', 'DARK')}")
    print(f"  Backend        : {result.get('backend', 'unknown')}")
    print()
    detected = result.get("detected", False)
    print(f"  Signal Detected: {'YES ✓' if detected else 'NO ✗'}")
    snr = result.get("snr", 0.0)
    strength = result.get("signal_strength", 0.0)
    print(f"  SNR            : {snr:.2f}  {_bar(snr, max_val=20.0)}")
    print(f"  Signal Strength: {strength:.3f}  {_bar(strength)}")
    print(f"  Strength Label : {result.get('strength_label', 'none')}")
    print(f"  Harmonics Found: {result.get('harmonics_detected', 0)}/4")
    print(f"  Est. Distance  : {result.get('estimated_distance_m', 0.0):.1f} m")
    print()
    verified = result.get("fatiha_verified", False)
    print(f"  Fatiha Verified: {'YES ✓' if verified else 'NO ✗'}")
    print(f"  Angle Detected : {result.get('fatiha_angle_detected_deg', 0.0):.3f}°")
    print(f"  Angle Expected : {result.get('fatiha_angle_expected_deg', 0.0):.3f}°")
    diff = result.get("angle_diff_deg", 0.0)
    tol = result.get("tolerance_deg", 0.5)
    print(f"  Angle Diff     : {diff:.4f}°  (tolerance: ±{tol}°)")
    print(f"  Silt Layer     : {'PRESENT' if result.get('silt_layer_present') else 'NOT DETECTED'}")


def cmd_listen(args):
    _header("BEEHIVE LISTEN MODE — Recording from Microphone")
    protocol = BeehiveProtocol(machine_id=args.machine_id, passphrase=args.passphrase)
    audio = BeehiveAudio(protocol=protocol, sample_rate=44100)

    if audio.backend == "simulation":
        print("  WARNING: No audio backend found — cannot record real audio.")
        print("  Install sounddevice: pip install sounddevice")
        print("  Or pyaudio:          pip install pyaudio")
        print("  Use --simulate for in-memory demo.")
        return 1

    print(f"  Recording {args.duration}s from microphone ({audio.backend}) ...")
    print("  [Listening...]")
    result = audio.listen(duration=args.duration)

    _print_detection(result)

    print()
    if result.get("fatiha_verified") and result.get("detected"):
        print("  RESULT: Beehive handshake DETECTED and VERIFIED")
    elif result.get("detected"):
        print("  RESULT: 432 Hz signal detected — Fatiha signature NOT verified")
    else:
        print("  RESULT: No Beehive signal detected in this audio window")
    print()
    return 0


def cmd_transmit(args):
    _header("BEEHIVE TRANSMIT MODE — Playing Handshake Pulse")
    protocol = BeehiveProtocol(machine_id=args.machine_id, passphrase=args.passphrase)
    audio = BeehiveAudio(protocol=protocol, sample_rate=44100)

    if audio.backend == "simulation":
        print("  WARNING: No audio backend found — cannot play real audio.")
        print("  Install sounddevice: pip install sounddevice")
        print("  Or pyaudio:          pip install pyaudio")
        print("  Use --simulate for in-memory demo.")
        return 1

    print(f"  Node ID    : {protocol.node_id}")
    print(f"  Passphrase : {args.passphrase}")
    print(f"  Duration   : {args.duration}s")
    print(f"  Backend    : {audio.backend}")
    print()
    print("  Transmitting 432 Hz Fatiha handshake pulse ...")
    result = audio.transmit(duration=args.duration)
    print()
    print(f"  Node ID        : {result['node_id']}")
    print(f"  Mesh State     : {result['mesh_state']}")
    print(f"  Peak Amplitude : {result['peak_amplitude']:.4f}")
    print(f"  Samples Sent   : {result['samples']:,}")
    print(f"  SNR            : N/A (transmit-only mode)")
    print(f"  Angle Diff     : N/A (transmit-only mode)")
    print(f"  Fatiha Verify  : N/A (transmit-only mode — use --loopback to capture + verify)")
    print()
    print("  RESULT: Handshake pulse transmitted")
    print()
    return 0


def cmd_loopback(args):
    _header("BEEHIVE LOOPBACK SELF-TEST — Transmit + Record + Verify")
    protocol = BeehiveProtocol(machine_id=args.machine_id, passphrase=args.passphrase)
    audio = BeehiveAudio(protocol=protocol, sample_rate=44100)

    if audio.backend == "simulation":
        print("  NOTE: No audio hardware — running in SIMULATION mode.")
        print("  (Handshake pulse fed directly into the detector without DAC/ADC.)")
        print()

    print(f"  Node ID    : {protocol.node_id}")
    print(f"  Passphrase : {args.passphrase}")
    print(f"  Backend    : {audio.backend}")
    print()

    if audio.backend != "simulation":
        print("  Step 1: Playing handshake pulse through speaker ...")
    else:
        print("  Step 1: Generating handshake pulse (simulation) ...")

    result = audio.loopback_self_test(
        pulse_duration=min(args.duration, 1.0),
        record_duration=args.duration,
    )

    print(f"  Loopback   : {result['loopback_note']}")
    print()
    _print_detection(result)

    print()
    passed = result.get("self_test_passed", False)
    if passed:
        print("  SELF-TEST: PASSED ✓ — Full acoustic pipeline verified")
    else:
        print("  SELF-TEST: FAILED ✗ — Check speaker/mic levels and loopback routing")
    print()
    return 0 if passed else 1


def cmd_simulate(args):
    _header("BEEHIVE SIMULATION — In-Memory Two-Node Exchange")
    print("  Running two-node Beehive exchange in memory (no audio hardware) ...")
    print()
    result = simulate_two_node_exchange(passphrase=args.passphrase)

    success = result.get("success", False)
    detection = result.get("detection", {})
    auth = result.get("authentication", {})
    fatiha = result.get("fatiha_handshake", {})

    print(f"  Node A State   : {result.get('node_a_state', 'DARK')}")
    print(f"  Node B State   : {result.get('node_b_state', 'DARK')}")
    print(f"  Neighbors A    : {result.get('node_a_neighbors', 0)}")
    print(f"  Neighbors B    : {result.get('node_b_neighbors', 0)}")
    print()
    detected = detection.get("detected", False)
    print(f"  Signal Detected: {'YES ✓' if detected else 'NO ✗'}")
    snr = detection.get("snr", 0.0)
    print(f"  SNR            : {snr:.2f}  {_bar(snr, max_val=20.0)}")
    print(f"  Harmonics      : {detection.get('harmonics_detected', 0)}/4")
    print()
    authenticated = auth.get("authenticated", False)
    print(f"  Phase Auth     : {'PASS ✓' if authenticated else 'FAIL ✗'}")
    print(f"  Phase Diff     : {auth.get('phase_diff_deg', 0.0):.3f}° (tol ±{auth.get('tolerance_deg', 15.0)}°)")
    print()
    print(f"  Fatiha Verified: {'YES ✓' if fatiha.get('fatiha_verified') else 'NO ✗'}")
    print(f"  Silt Layer     : {'PRESENT' if fatiha.get('silt_layer_present') else 'NOT DETECTED'}")
    print(f"  Whisper Confirm: {'YES ✓' if fatiha.get('whisper_confirmed') else 'NO ✗'}")
    print(f"  Protocol       : {fatiha.get('protocol', '')}")
    print()
    data_tx = result.get("data_transmitted", 0)
    data_rx = result.get("data_recovered", 0)
    bit_perfect = result.get("bit_perfect", False)
    print(f"  Data TX        : {data_tx} bytes")
    print(f"  Data RX        : {data_rx} bytes")
    print(f"  Bit-Perfect    : {'YES ✓' if bit_perfect else 'NO ✗'}")
    print(f"  Packet Delivery: {result.get('packet_delivery', 'UNKNOWN')}")
    print()
    if success:
        print("  RESULT: Two-node exchange SUCCEEDED ✓")
    else:
        print(f"  RESULT: Exchange FAILED at stage: {result.get('stage', 'unknown')}")
        if result.get("error"):
            print(f"  Error  : {result['error']}")
    print()
    return 0 if success else 1


def main():
    parser = argparse.ArgumentParser(
        description=textwrap.dedent(__doc__),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--listen", action="store_true",
                       help="Record from mic, detect + verify Fatiha")
    group.add_argument("--transmit", action="store_true",
                       help="Play the handshake pulse through the speaker")
    group.add_argument("--loopback", action="store_true",
                       help="Full loopback self-test (transmit + record + verify)")
    group.add_argument("--simulate", action="store_true",
                       help="In-memory two-node simulation (no hardware needed)")

    parser.add_argument("--duration", type=float, default=2.0,
                        help="Recording / pulse duration in seconds (default: 2.0)")
    parser.add_argument("--passphrase", type=str, default="void-432",
                        help="Beehive passphrase (default: void-432)")
    parser.add_argument("--machine-id", type=str, default="VOID-AUDIO-DEMO",
                        help="Node machine ID (default: VOID-AUDIO-DEMO)")

    args = parser.parse_args()

    print()
    print("  PROJECT VOID — Beehive Live Audio Demo")
    print(f"  Audio Backend  : {AUDIO_BACKEND}")
    print(f"  Machine ID     : {args.machine_id}")

    if args.listen:
        return cmd_listen(args)
    if args.transmit:
        return cmd_transmit(args)
    if args.loopback:
        return cmd_loopback(args)
    if args.simulate:
        return cmd_simulate(args)


if __name__ == "__main__":
    sys.exit(main() or 0)
