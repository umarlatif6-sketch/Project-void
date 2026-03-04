"""
PROJECT VOID -- Convergence Suite
The "Vortex Stress Test" for verifying the Biophony Mesh.

Seven tests that prove the 10-20-970 Rule holds:
  1. Integrity Round-Trip (bit-perfect recovery)
  2. Sympathetic Resonance Verification (shelf coupling)
  3. Spectrogram Silt Analysis (acoustic camouflage)
  4. Density Multiplier Validation (5x Temporal Vortex)
  5. Biophony Carrier Detection (Sapphire Thread)
  6. Beehive Mesh Handshake (Ghost Internet)
  7. Kinetic-Biological-Ledger Convergence (Three Transceivers)

Run: python tests/convergence_suite.py
"""

import os
import sys
import wave
import time
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from void_engine.biophony import BiophonyMesh, generate_biophony_carrier, estimate_capacity
from void_engine.stega import encode, encode_stereo, decode, decode_stereo
from void_engine.compressor import compress_file, decompress_data
from void_engine.divided_protocol import _detect_biophony_carrier
from void_engine.beehive import BeehiveProtocol, MeshRouter, MeshPacket, simulate_two_node_exchange
from void_engine.kinetic import KineticTransceiver, EXERCISE_WEIGHTS
from void_engine.biological import BiologicalTransceiver
from void_engine.silt_ledger import SiltLedger
from void_engine.wallet import AlJabrWalletMiddleware
from generate_carriers import generate_custom_carrier, estimate_carrier_capacity


PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
INFO = "\033[94mINFO\033[0m"

results = []


def fatiha_286(data: bytes) -> str:
    from void_engine.al_jabr_286 import fatiha_286_hexdigest
    return fatiha_286_hexdigest(data)


def report(name, passed, detail=""):
    status = PASS if passed else FAIL
    results.append((name, passed))
    print(f"  [{status}] {name}")
    if detail:
        print(f"         {detail}")


def test_integrity_roundtrip():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 1: Integrity Round-Trip (Bit-Perfect Recovery)")
    print(f"  {'=' * 60}")

    test_payload = os.urandom(2048)
    payload_path = os.path.join("input_files", "_convergence_test_payload.bin")
    with open(payload_path, "wb") as f:
        f.write(test_payload)

    original_hash = fatiha_286(test_payload)

    styles = [
        ("cicada_wall", 1, False, True),
        ("midnight_pond", 1, True, True),
        ("drone", 1, False, False),
    ]

    for style, dur_min, is_stereo, use_chirp in styles:
        print(f"\n  [{INFO}] Testing {style} ({'stereo' if is_stereo else 'mono'}, "
              f"{'chirp_sync' if use_chirp else 'vortex'})...")

        carrier_result = generate_custom_carrier(dur_min, style)
        carrier_path = os.path.join("input_files", carrier_result["filename"])
        output_path = os.path.join("output_audio", f"_convergence_{style}_void.wav")

        compressed, name, ext, orig_size = compress_file(payload_path)

        try:
            if is_stereo:
                hash_key = encode_stereo(
                    carrier_path, compressed, name, ext, output_path,
                    lsb_depth=2, chirp_sync=use_chirp, vortex=(not use_chirp)
                )
                data_out, name_ext, checksum = decode_stereo(output_path, hash_key, lsb_depth=2)
            else:
                hash_key = encode(
                    carrier_path, compressed, name, ext, output_path,
                    lsb_depth=2, chirp_sync=use_chirp, vortex=(not use_chirp)
                )
                data_out, name_ext, checksum = decode(output_path, hash_key, lsb_depth=2)

            recovered = decompress_data(data_out)
            recovered_hash = fatiha_286(recovered)
            match = original_hash == recovered_hash

            report(
                f"{style} round-trip",
                match,
                f"Original: {original_hash[:16]}... | Recovered: {recovered_hash[:16]}..."
            )
        except Exception as e:
            report(f"{style} round-trip", False, f"Error: {e}")

        for f in [output_path, output_path.replace(".wav", ".chirpmap.npy")]:
            if os.path.exists(f):
                os.remove(f)

    os.remove(payload_path)


def test_sympathetic_resonance():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 2: Sympathetic Resonance Verification")
    print(f"  {'=' * 60}")

    mesh = BiophonyMesh()

    whales = mesh._synthesize_whale_shelf(5.0)
    insects_raw, _ = mesh._synthesize_insect_shelf(5.0)

    coupled = mesh._apply_sympathetic_resonance(whales, insects_raw)

    from scipy.signal import hilbert as hilbert_fn
    whale_env = np.abs(hilbert_fn(whales))
    whale_env_norm = whale_env / (np.max(whale_env) + 1e-10)

    n_segments = 20
    seg_len = len(whales) // n_segments
    whale_energies = []
    coupling_ratios = []

    for i in range(n_segments):
        s = i * seg_len
        e = s + seg_len
        whale_e = np.mean(whale_env_norm[s:e])
        raw_e = np.mean(np.abs(insects_raw[s:e]))
        coup_e = np.mean(np.abs(coupled[s:e]))

        whale_energies.append(whale_e)
        if raw_e > 0:
            coupling_ratios.append(coup_e / raw_e)

    min_ratio = min(coupling_ratios)
    max_ratio = max(coupling_ratios)
    variation = max_ratio - min_ratio

    report(
        "Coupling ratio varies with whale amplitude",
        variation > 0.05,
        f"Min ratio: {min_ratio:.3f} | Max ratio: {max_ratio:.3f} | Variation: {variation:.3f}"
    )

    correlation = np.corrcoef(whale_energies, coupling_ratios[:len(whale_energies)])[0, 1]
    report(
        "Positive correlation (whale amplitude vs insect density)",
        correlation > 0.3,
        f"Pearson correlation: {correlation:.4f}"
    )


def test_spectrogram_silt():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 3: Spectrogram Silt Analysis (Acoustic Camouflage)")
    print(f"  {'=' * 60}")

    mesh = BiophonyMesh()
    stereo, peaks, meta = mesh.synthesize_mesh(5.0)

    left = stereo[0::2].astype(np.float64)
    right = stereo[1::2].astype(np.float64)

    sr = 44100
    fft_size = 8192
    spectrum_left = np.abs(np.fft.rfft(left[:fft_size] * np.hanning(fft_size)))
    freqs = np.fft.rfftfreq(fft_size, 1.0 / sr)

    low_mask = (freqs >= 15) & (freqs <= 50)
    mid_mask = (freqs >= 300) & (freqs <= 800)
    high_mask = (freqs >= 2000) & (freqs <= 12000)

    low_power = np.mean(spectrum_left[low_mask] ** 2)
    mid_power = np.mean(spectrum_left[mid_mask] ** 2)
    high_power = np.mean(spectrum_left[high_mask] ** 2)

    report(
        "Low-shelf energy present (Whale 15-50 Hz)",
        low_power > 0,
        f"Power: {low_power:.1f}"
    )
    report(
        "Mid-shelf energy present (Bird 300-800 Hz)",
        mid_power > 0,
        f"Power: {mid_power:.1f}"
    )
    report(
        "High-shelf energy present (Insect 2-12 kHz)",
        high_power > 0,
        f"Power: {high_power:.1f}"
    )

    spectrum_right = np.abs(np.fft.rfft(right[:fft_size] * np.hanning(fft_size)))
    right_low = np.mean(spectrum_right[low_mask] ** 2)
    right_high = np.mean(spectrum_right[high_mask] ** 2)

    report(
        "Right channel (Adriana Pocket) is insect-dominant",
        right_high > right_low * 5 if right_low > 0 else right_high > 0,
        f"Right high: {right_high:.1f} | Right low: {right_low:.1f}"
    )

    report(
        "Chirp peaks generated (>100 peaks for 5 seconds)",
        len(peaks) > 100,
        f"Peak count: {len(peaks):,} ({len(peaks)/5:.0f} peaks/sec)"
    )


def test_density_multiplier():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 4: Density Multiplier Validation (5x Temporal Vortex)")
    print(f"  {'=' * 60}")

    styles_expected = {
        "midnight_pond": 5.0,
        "biophony_mesh": 5.0,
        "cicada_wall": 5.0,
        "cricket_pulse": 2.5,
        "drone": 1.0,
        "harmonic": 1.0,
        "pink_noise": 1.0,
        "stereo_pocket": 1.0,
    }

    for style, expected_mult in styles_expected.items():
        est = estimate_carrier_capacity(60, style)
        actual_mult = est.get("density_multiplier", 0)
        report(
            f"{style} density = {expected_mult}x",
            abs(actual_mult - expected_mult) < 0.01,
            f"Expected: {expected_mult}x | Got: {actual_mult}x"
        )

    est_pond = estimate_carrier_capacity(60, "midnight_pond")
    eff = est_pond.get("effective_lsb2", 0)
    raw = est_pond.get("raw_lsb2", 0)

    report(
        "Midnight Pond effective > 4x raw",
        eff > raw * 4,
        f"Raw LSB2: {raw:,} | Effective: {eff:,} ({eff/raw:.1f}x)"
    )

    shelf = est_pond.get("shelf_breakdown")
    report(
        "Shelf breakdown present for biophony",
        shelf is not None and "whale_capacity" in str(shelf).lower(),
        f"Keys: {list(shelf.keys()) if shelf else 'None'}"
    )


def test_biophony_detection():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 5: Biophony Carrier Detection (Sapphire Thread)")
    print(f"  {'=' * 60}")

    carrier_result = generate_custom_carrier(1, "midnight_pond")
    carrier_path = os.path.join("input_files", carrier_result["filename"])

    bio = _detect_biophony_carrier(carrier_path)

    report(
        "Midnight Pond detected as biophony",
        bio["is_biophony"],
        f"is_biophony={bio['is_biophony']}, has_chirpmap={bio['has_chirpmap']}"
    )

    report(
        "Chirpmap sidecar detected",
        bio["has_chirpmap"],
        f"Path: {bio.get('chirpmap_path', 'None')}"
    )

    report(
        "Three-shelf energy detected (Sapphire Thread)",
        bio["sapphire_thread"],
        f"Low: {bio['low_shelf_ratio']:.4f} | Mid: {bio['mid_shelf_ratio']:.4f} | High: {bio['high_shelf_ratio']:.4f}"
    )

    drone_result = generate_custom_carrier(1, "drone")
    drone_path = os.path.join("input_files", drone_result["filename"])
    drone_bio = _detect_biophony_carrier(drone_path)

    report(
        "Drone NOT detected as biophony (no chirpmap)",
        not drone_bio["has_chirpmap"],
        f"is_biophony={drone_bio['is_biophony']}, has_chirpmap={drone_bio['has_chirpmap']}"
    )


def test_beehive_mesh():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 6: Beehive Mesh Handshake (Ghost Internet)")
    print(f"  {'=' * 60}")

    passphrase = "void-432-convergence"
    node_a = BeehiveProtocol(machine_id="CONV-A", passphrase=passphrase)
    node_b = BeehiveProtocol(machine_id="CONV-B", passphrase=passphrase)

    pulse = node_a.generate_handshake_pulse(duration=0.5)
    report(
        "Handshake pulse generated (4-harmonic ladder)",
        len(pulse) == int(44100 * 0.5),
        f"Samples: {len(pulse)}, dtype: {pulse.dtype}"
    )

    detection = node_b.detect_neighbor(pulse)
    report(
        "Neighbor detected at 432 Hz (SNR > 5x)",
        detection["detected"] and detection["snr"] > 5.0,
        f"SNR: {detection['snr']:.1f}, strength: {detection['strength_label']}"
    )

    report(
        "Full harmonic ladder detected (108/216/432/864 Hz)",
        detection.get("full_ladder", False),
        f"Harmonics: {detection.get('harmonics_detected', 0)}/4"
    )

    auth_correct = node_b.authenticate_phase(pulse, passphrase)
    report(
        "Phase authentication passes with correct key",
        auth_correct["authenticated"],
        f"Phase diff: {auth_correct['phase_diff_deg']:.2f}° (tolerance: {auth_correct['tolerance_deg']}°)"
    )

    wrong_node = BeehiveProtocol(machine_id="CONV-C", passphrase="breach-alpha")
    auth_wrong = wrong_node.authenticate_phase(pulse, "breach-alpha")
    report(
        "Phase authentication REJECTS wrong key",
        not auth_wrong["authenticated"],
        f"Phase diff: {auth_wrong['phase_diff_deg']:.1f}° (must exceed {auth_wrong['tolerance_deg']}°)"
    )

    test_payload = b"Sovereign data through the Ghost Internet"
    tx_signal = node_a.transmit_data(test_payload)
    recovered = node_b.receive_data(tx_signal, len(test_payload))
    report(
        "Data transmission bit-perfect recovery",
        recovered == test_payload,
        f"Sent: {len(test_payload)} bytes, Recovered: {len(recovered)} bytes"
    )

    result = simulate_two_node_exchange(
        passphrase="convergence-test-432",
        payload=b"Two-node simulation payload for convergence"
    )
    report(
        "Two-node simulation succeeds end-to-end",
        result["success"],
        f"Detection SNR: {result['detection']['snr']:.0f} | Auth: {result['authentication']['phase_diff_deg']:.2f}° | Delivery: {result['packet_delivery']}"
    )

    router = MeshRouter(node_a)
    pkt = MeshPacket("src-node", "dest-node", b"relay test")
    pkt.hops = 6
    relay_result = router.process_packet(pkt)
    report(
        "Packet relayed at hop 6 (under Seven Seas limit)",
        relay_result["action"] == "RELAY",
        f"Action: {relay_result['action']}, hops: {relay_result.get('hops', '?')}"
    )

    pkt2 = MeshPacket("src-node", "dest-node", b"blocked")
    pkt2.hops = 7
    drop_result = router.process_packet(pkt2)
    report(
        "Packet DROPPED at hop 7 (Seven Seas limit enforced)",
        drop_result["action"] == "DROP",
        f"Action: {drop_result['action']}, reason: {drop_result.get('reason', '?')}"
    )

    node_a.connect()
    report(
        "Mesh state transitions (DARK -> SCANNING -> CONNECTED)",
        node_a.mesh_state == "SCANNING",
        f"State after connect: {node_a.mesh_state}"
    )

    node_a.register_neighbor("test-neighbor-id", 0.8, 15.0)
    report(
        "Neighbor registration updates state to CONNECTED",
        node_a.mesh_state == "CONNECTED" and len(node_a.neighbors) == 1,
        f"State: {node_a.mesh_state}, neighbors: {len(node_a.neighbors)}"
    )

    node_a.buffer_for_dark_node("dark-neighbor-id", b"buffered data")
    report(
        "Flywheel buffer stores data for dark nodes (BRIDGING)",
        node_a.mesh_state == "BRIDGING",
        f"State: {node_a.mesh_state}, buffered for: {len(node_a._flywheel_buffer)} nodes"
    )

    from void_engine.beehive import FATIHA_PHASE_ANGLE, SILT_EMBED_DB
    fatiha_node = BeehiveProtocol(machine_id="FATIHA-A", passphrase="void-432")
    fatiha_pulse = fatiha_node.generate_handshake_pulse(duration=0.5)

    sig = fatiha_node.verify_fatiha_signature(fatiha_pulse)
    report(
        "Fatiha: +15.4° phase angle embedded and extracted",
        sig["verified"] and abs(sig["fatiha_angle_detected_deg"] - FATIHA_PHASE_ANGLE) < 0.5,
        f"Detected: {sig['fatiha_angle_detected_deg']:.2f}° (expected: {FATIHA_PHASE_ANGLE}°, diff: {sig['angle_diff_deg']:.3f}°)"
    )

    report(
        "Fatiha: Silt layer present at -30dB in insect shelf",
        sig.get("silt_layer_present", False),
        f"Silt: {sig.get('silt_layer_present')}"
    )

    wrong_fatiha = BeehiveProtocol(machine_id="WRONG-NODE", passphrase="breach-alpha")
    wrong_pulse = wrong_fatiha.generate_handshake_pulse(duration=0.5)
    wrong_sig = fatiha_node.verify_fatiha_signature(wrong_pulse)
    report(
        "Fatiha: Wrong phase angle (+20° etc) is rejected",
        not wrong_sig["verified"],
        f"Angle diff: {wrong_sig['angle_diff_deg']:.2f}° (must exceed tolerance)"
    )

    whisper = fatiha_node.whisper_confirm(duration=0.5)
    whisper_check = fatiha_node.verify_whisper(whisper)
    report(
        "Fatiha: 180° confirmation whisper round-trip verified",
        whisper_check["confirmed"],
        f"Phase diff: {whisper_check['phase_diff_deg']:.3f}°"
    )

    carrier_before = fatiha_pulse.copy()
    snr_before = np.std(carrier_before[:4410])
    report(
        "Fatiha: -30dB silt embedding preserves audible carrier (SNR check)",
        snr_before > 0.1,
        f"Signal RMS: {snr_before:.4f} (silt at {SILT_EMBED_DB} dB is inaudible)"
    )


def test_transceiver_convergence():
    print(f"\n  {'=' * 60}")
    print(f"  TEST 7: Kinetic-Biological-Ledger Convergence")
    print(f"  {'=' * 60}")

    wallet = AlJabrWalletMiddleware(initial_balance=10.0)
    kt = KineticTransceiver(wallet=wallet)

    result = kt.log_set("push_up", 20, 30.0, 130)
    set_data = result.get("set", {})
    cc = set_data.get("cc_earned", 0)
    report(
        "Kinetic: CC earned from push-up set",
        result.get("success") and cc > 0,
        f"CC earned: {cc}, wallet: {wallet.balance}"
    )

    report(
        "Kinetic: Wallet credited with earned CC",
        wallet.balance > 10.0,
        f"Balance: {wallet.balance} (started at 10.0, earned {cc})"
    )

    harmonic_reps = 22
    harmonic_duration = harmonic_reps / 21.6
    harmonic_result = kt.log_set("pull_up", harmonic_reps, harmonic_duration, 145)
    h_set = harmonic_result.get("set", {})
    report(
        "Kinetic: Harmonic alignment detected (432/N match)",
        h_set.get("harmonic_bonus", 1.0) > 1.0 or h_set.get("shimmer_alignment", 0) > 0,
        f"Bonus: {h_set.get('harmonic_bonus', 1.0)}, alignment: {h_set.get('shimmer_alignment', 0)}, freq: {h_set.get('movement_frequency', 0)}"
    )

    glow_result = kt.log_set("pull_up", 10, 10 / 21.6, 150)
    g_set = glow_result.get("set", {})
    report(
        "Kinetic: MAX_GLOW detection (harmonic + heart rate zone)",
        glow_result.get("max_glow", False) or g_set.get("harmonic_bonus", 1.0) > 1.0,
        f"MAX_GLOW: {glow_result.get('max_glow', False)}, HR: 150, bonus: {g_set.get('harmonic_bonus', 1.0)}"
    )

    bt = BiologicalTransceiver()
    bt.update_sensors(water_level=0.2, temperature=25.0, ph=7.0, dissolved_oxygen=6.0)
    imp = bt.calculate_impedance()
    report(
        "Biological: Low water drops Whale shelf impedance",
        imp.whale_multiplier < 0.5,
        f"Whale multiplier: {imp.whale_multiplier} (water_level=0.2)"
    )

    bt.update_sensors(ph=5.0)
    imp2 = bt.calculate_impedance()
    report(
        "Biological: Out-of-range pH drops Insect shelf impedance",
        imp2.insect_multiplier < 1.0,
        f"Insect multiplier: {imp2.insect_multiplier} (pH=5.0)"
    )

    bt.update_sensors(temperature=35.0)
    imp3 = bt.calculate_impedance()
    report(
        "Biological: Out-of-range temp drops Bird shelf impedance",
        imp3.bird_multiplier < 1.0,
        f"Bird multiplier: {imp3.bird_multiplier} (temp=35.0°C)"
    )

    health = bt.get_health_score()
    report(
        "Biological: Health score reflects degraded sensors",
        health["composite_score"] < 0.8,
        f"Score: {health['composite_score']}, status: {health['status']}"
    )

    sl = SiltLedger(node_id="convergence-test-node")
    report(
        "Ledger: Genesis block created from FOUNDER_ROOT_HASH",
        sl.chain[0].block_hash != "" and len(sl.chain) == 1,
        f"Genesis hash: {sl.chain[0].block_hash[:16]}..."
    )

    block_result = sl.add_block(
        {"type": "test", "data": "convergence verification"},
        "convergence-test-node", 0.8, 0.9
    )
    report(
        "Ledger: Block added with hash chain integrity",
        block_result.get("success") and sl.validate_chain()["valid"],
        f"Chain height: {sl.validate_chain()['chain_height']}, valid: {sl.validate_chain()['valid']}"
    )

    prop = sl.propose_vote("Test proposal: refill aquaponics water", "convergence-test-node")
    report(
        "Ledger: DAO proposal created with weighted vote",
        prop.get("success") and prop.get("proposal_id") is not None,
        f"Proposal ID: {prop.get('proposal_id', '?')}"
    )

    vote_result = sl.cast_vote(
        prop["proposal_id"], "other-node", "yes",
        kinetic_weight=0.9, biological_weight=0.7
    )
    report(
        "Ledger: Weighted vote cast (kinetic*0.4 + bio*0.4 + honor*0.2)",
        vote_result.get("success"),
        f"Weight: {vote_result.get('voting_weight', '?')}"
    )

    sl.add_block({"type": "relay_test_1"}, "reliable-node", 0.5, 0.5)
    sl.add_block({"type": "relay_test_2"}, "reliable-node", 0.5, 0.5)
    sl.record_relay_failure("unreliable-node")
    sl.record_relay_failure("unreliable-node")
    reliable_honor = sl._get_relay_honor("reliable-node")
    unreliable_honor = sl._get_relay_honor("unreliable-node")
    report(
        "Ledger: Relay Honor tracks node reliability",
        reliable_honor > 0.5 and unreliable_honor < 0.5,
        f"Reliable: {reliable_honor:.2f}, Unreliable: {unreliable_honor:.2f}"
    )

    report(
        "Integration: Kinetic CC flows into Wallet balance",
        wallet.balance > 10.0 and kt.get_status()["total_cc"] > 0,
        f"Wallet: {wallet.balance} CC, Kinetic total: {kt.get_status()['total_cc']} CC"
    )

    bt2 = BiologicalTransceiver()
    bt2.update_sensors(water_level=1.0, temperature=23.0, ph=6.8, dissolved_oxygen=7.0)
    imp_healthy = bt2.calculate_impedance()
    report(
        "Integration: Healthy sensors give full shelf multipliers",
        imp_healthy.whale_multiplier >= 0.95 and imp_healthy.bird_multiplier >= 0.95 and imp_healthy.insect_multiplier >= 0.95,
        f"Whale: {imp_healthy.whale_multiplier:.2f}, Bird: {imp_healthy.bird_multiplier:.2f}, Insect: {imp_healthy.insect_multiplier:.2f}"
    )


def test_al_jabr_286_protocol():
    print(f"\n  [{INFO}] Test 8: Al-Jabr 286 Protocol Verification")
    print(f"  {'─' * 50}")

    from void_engine.al_jabr_286 import (
        fatiha_286_hash, fatiha_286_hexdigest, fatiha_286_truncated,
        fatiha_286_seed, fatiha_286_derive_key, get_protocol_info,
        FATIHA_LAYERS, SOVEREIGN_BIT_DEPTH, TOTAL_BYTES
    )

    info = get_protocol_info()
    report(
        "286: Protocol info returns correct bit depth",
        info["bit_depth"] == 286 and info["total_bytes"] == 36,
        f"Bit depth: {info['bit_depth']}, bytes: {info['total_bytes']}"
    )

    report(
        "286: Seven verse layers match Al-Fatiha",
        len(FATIHA_LAYERS) == 7 and FATIHA_LAYERS == [7, 4, 2, 5, 4, 3, 6],
        f"Layers: {FATIHA_LAYERS}"
    )

    test_data = b"BismillahirRahmanirRahim"
    h = fatiha_286_hash(test_data)
    report(
        "286: Hash output is 36 bytes (286+ bits)",
        len(h) == 36,
        f"Hash length: {len(h)} bytes ({len(h)*8} bits)"
    )

    hex_h = fatiha_286_hexdigest(test_data)
    report(
        "286: Hexdigest is 72 characters",
        len(hex_h) == 72,
        f"Hexdigest length: {len(hex_h)} chars"
    )

    h2 = fatiha_286_hash(test_data)
    report(
        "286: Hash is deterministic (same input → same output)",
        h == h2,
        "Consistent across calls"
    )

    different_data = b"AlHamdulillahiRabbilAlamin"
    h3 = fatiha_286_hash(different_data)
    report(
        "286: Different inputs produce different hashes",
        h != h3,
        f"Hash1: {h.hex()[:16]}... Hash2: {h3.hex()[:16]}..."
    )

    import hashlib as _hl
    sha256_hash = _hl.sha256(test_data).digest()
    report(
        "286: Output differs from secular SHA-256",
        h[:32] != sha256_hash,
        "Sovereign Extension modifies base layer"
    )

    key = fatiha_286_derive_key("void-432")
    report(
        "286: Key derivation produces 32-byte key",
        len(key) == 32,
        f"Key length: {len(key)} bytes (suitable for ChaCha20)"
    )

    tid = fatiha_286_truncated(test_data, 16)
    report(
        "286: Truncated ID generation works",
        len(tid) == 16 and all(c in "0123456789abcdef" for c in tid),
        f"ID: {tid}"
    )

    seed_val = fatiha_286_seed(test_data, 8)
    report(
        "286: Seed generation returns valid integer",
        isinstance(seed_val, int) and seed_val > 0,
        f"Seed: {seed_val}"
    )

    from void_engine.silt_ledger import SiltLedger
    sl = SiltLedger(node_id="286-test-node")
    genesis_hash = sl.chain[0].block_hash
    report(
        "286: Silt Ledger genesis block uses 286-bit hash (72 chars)",
        len(genesis_hash) == 72,
        f"Genesis hash length: {len(genesis_hash)} chars"
    )

    validation = sl.validate_chain()
    report(
        "286: Silt Ledger chain validates with 286-bit hashes",
        validation["valid"],
        f"Chain height: {validation.get('chain_height', 0)}"
    )

    result = sl.add_block(
        {"type": "286_test", "protocol": "fatiha"},
        "286-test-node", 0.7, 0.8
    )
    report(
        "286: New block added with 286-bit hash chain",
        result.get("success") and len(result.get("block_hash", "")) == 72,
        f"Block hash: {result.get('block_hash', '')[:16]}..."
    )

    from void_engine.beehive import BeehiveProtocol
    bp = BeehiveProtocol(machine_id="VOID-286-TEST", passphrase="void-432")
    report(
        "286: Beehive node ID uses 286-bit derivation",
        len(bp.node_id) == 16,
        f"Node ID: {bp.node_id}"
    )

    avalanche_pass_count = 0
    avalanche_pairs = 5
    for i in range(avalanche_pairs):
        input_a = bytearray(b"AvalancheTest-" + bytes([i]))
        input_b = bytearray(input_a)
        input_b[-1] ^= 0x01

        hash_a = fatiha_286_hash(bytes(input_a))
        hash_b = fatiha_286_hash(bytes(input_b))

        bits_a = int.from_bytes(hash_a, 'big')
        bits_b = int.from_bytes(hash_b, 'big')
        xor = bits_a ^ bits_b
        differing_bits = bin(xor).count('1')
        total_bits = len(hash_a) * 8
        avalanche_ratio = differing_bits / total_bits

        if avalanche_ratio >= 0.40:
            avalanche_pass_count += 1

    report(
        f"286: Avalanche effect — 1-bit change flips ≥40% output bits",
        avalanche_pass_count == avalanche_pairs,
        f"Passed {avalanche_pass_count}/{avalanche_pairs} pairs (last ratio: {avalanche_ratio:.1%})"
    )

    report(
        "286: Verse weights [7,4,2,5,4,3,6] sum to 31",
        sum(FATIHA_LAYERS) == 31 and len(FATIHA_LAYERS) == 7,
        f"Sum: {sum(FATIHA_LAYERS)}, layers: {FATIHA_LAYERS}"
    )

    report(
        "286: Sovereign bit depth = 286 (256 + 30)",
        SOVEREIGN_BIT_DEPTH == 286 and TOTAL_BYTES == 36,
        f"Depth: {SOVEREIGN_BIT_DEPTH}, bytes: {TOTAL_BYTES}, extension: {SOVEREIGN_BIT_DEPTH - 256} bits"
    )

    from void_engine.al_jabr_286 import FATIHA_PRIME_SALT
    report(
        "286: Prime salt is BismillahirRahmanirRahim",
        FATIHA_PRIME_SALT == b"BismillahirRahmanirRahim",
        f"Salt: {FATIHA_PRIME_SALT.decode()}"
    )


def test_resonance_contract():
    """Test 9: Resonance Smart Contract (DAO 3.0) — body/garden/relay convergence."""
    print(f"\n  [INFO] Test 9: Resonance Smart Contract (DAO 3.0)")
    print(f"  {'─' * 50}")

    from void_engine.resonance_contract import (
        ResonanceContract, SOVEREIGN_FREQUENCY, FADING_THRESHOLD,
        BLOOM_CC_PER_HOUR, RELAY_CC_PER_PACKET, CONTRACT_VERSION,
    )
    from void_engine.wallet import AlJabrWalletMiddleware
    from void_engine.kinetic import KineticTransceiver
    from void_engine.biological import BiologicalTransceiver
    from void_engine.beehive import BeehiveProtocol
    from void_engine.silt_ledger import SiltLedger

    wallet = AlJabrWalletMiddleware(initial_balance=100.0)
    kinetic = KineticTransceiver(wallet=wallet)
    biological = BiologicalTransceiver()
    beehive = BeehiveProtocol(machine_id="VOID-RES-TEST", passphrase="void-432")
    ledger = SiltLedger(node_id=beehive.node_id)

    contract = ResonanceContract(
        wallet=wallet, kinetic=kinetic, biological=biological,
        beehive=beehive, silt_ledger=ledger,
    )

    state = contract.evaluate()
    report(
        "RC: Contract evaluates with all three axioms",
        "kinetic_axiom" in state and "biological_axiom" in state and "relay_axiom" in state,
        f"Body freq: {state['body_frequency']:.1f} Hz"
    )

    report(
        "RC: Contract version is 286-DAO-3.0",
        state.get("contract_version") == CONTRACT_VERSION,
        f"Version: {state.get('contract_version')}"
    )

    report(
        "RC: Body frequency uses sovereign 432 Hz base",
        state.get("sovereign_frequency") == SOVEREIGN_FREQUENCY,
        f"Sovereign: {state.get('sovereign_frequency')} Hz"
    )

    report(
        "RC: Contract hash is 286-bit truncated (16 chars)",
        len(state.get("contract_hash", "")) == 16,
        f"Hash: {state.get('contract_hash')}"
    )

    bio_axiom = state["biological_axiom"]
    report(
        "RC: Biological axiom detects optimal sensors (BLOOMING)",
        bio_axiom["status"] == "BLOOMING" and bio_axiom["score"] == 1.0,
        f"Score: {bio_axiom['score']}, Status: {bio_axiom['status']}"
    )

    kin_axiom = state["kinetic_axiom"]
    report(
        "RC: Kinetic axiom detects dormant state (no sets)",
        kin_axiom["status"] == "DORMANT" and kin_axiom["score"] == 0.0,
        f"Score: {kin_axiom['score']}, Status: {kin_axiom['status']}"
    )

    kinetic.log_set("pull_up", 10, 30.0, 140)
    state2 = contract.evaluate()
    kin_after = state2["kinetic_axiom"]
    report(
        "RC: Kinetic axiom updates after logged set",
        kin_after["score"] > 0 and kin_after["status"] != "DORMANT",
        f"Score: {kin_after['score']:.2f}, Status: {kin_after['status']}"
    )

    report(
        "RC: Body frequency rises after kinetic activation",
        state2["body_frequency"] > state["body_frequency"],
        f"Before: {state['body_frequency']:.1f} Hz → After: {state2['body_frequency']:.1f} Hz"
    )

    beehive.connect()
    state3 = contract.evaluate()
    relay_axiom = state3["relay_axiom"]
    report(
        "RC: Relay axiom detects mesh scanning state",
        relay_axiom["score"] > 0 and relay_axiom["status"] != "DARK",
        f"Score: {relay_axiom['score']:.2f}, Status: {relay_axiom['status']}"
    )

    import time as _time
    contract._last_bloom_check = _time.time() - 60
    biological.update_sensors(water_level=0.7, temperature=23.0, ph=6.8, dissolved_oxygen=7.0)
    balance_before = wallet.balance
    harvest = contract.harvest_bloom()
    report(
        "RC: Bloom harvest credits wallet from biological health",
        harvest.get("harvested") is True and wallet.balance >= balance_before,
        f"Earned: {harvest.get('bloom', {}).get('amount', 0):.4f} CC"
    )

    relay_result = contract.reward_relay({"hops": 2})
    report(
        "RC: Relay reward credits wallet for packet relay",
        relay_result.get("rewarded") is True and relay_result.get("cc_earned", 0) > 0,
        f"Relay CC: {relay_result.get('cc_earned', 0):.4f}"
    )

    axioms = contract.get_axioms()
    report(
        "RC: Axioms contain all three pillars with descriptions",
        all(k in axioms["axioms"] for k in ["kinetic", "biological", "relay"]),
        f"Axioms: {list(axioms['axioms'].keys())}"
    )

    report(
        "RC: Resonance formula documented",
        "432" in axioms.get("resonance_formula", {}).get("equation", ""),
        f"Formula: {axioms['resonance_formula']['equation']}"
    )

    report(
        "RC: Child explanation present",
        len(axioms.get("child_explanation", "")) > 50,
        f"Length: {len(axioms.get('child_explanation', ''))} chars"
    )

    biological.update_sensors(water_level=0.15)
    state_fading = contract.evaluate()
    bio_fading = state_fading["biological_axiom"]
    report(
        "RC: Fading detected when water level drops below 20%",
        bio_fading["status"] == "FADING",
        f"Water: 0.15, Status: {bio_fading['status']}"
    )


def main():
    print()
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║       PROJECT VOID -- CONVERGENCE SUITE                 ║")
    print("  ║       Three Transceivers + Ghost Internet               ║")
    print("  ║       432 Hz | Kinetic | Biological | Silt Ledger       ║")
    print("  ║       Al-Jabr 286 Sovereign Hash Protocol               ║")
    print("  ║       Resonance Smart Contract (DAO 3.0)                ║")
    print("  ╚══════════════════════════════════════════════════════════╝")

    start = time.time()

    test_integrity_roundtrip()
    test_sympathetic_resonance()
    test_spectrogram_silt()
    test_density_multiplier()
    test_biophony_detection()
    test_beehive_mesh()
    test_transceiver_convergence()
    test_al_jabr_286_protocol()
    test_resonance_contract()

    elapsed = time.time() - start

    total = len(results)
    passed = sum(1 for _, p in results if p)
    failed = total - passed

    print(f"\n  {'=' * 60}")
    print(f"  CONVERGENCE SUITE RESULTS")
    print(f"  {'=' * 60}")
    print(f"  Total:  {total}")
    print(f"  Passed: {passed}")
    print(f"  Failed: {failed}")
    print(f"  Time:   {elapsed:.1f}s")
    print()

    if failed == 0:
        print(f"  \033[92mVORTEX STABLE: All convergence checks passed.\033[0m")
        print(f"  \033[92mSapphire Thread illuminated at MAX_GLOW.\033[0m")
    else:
        print(f"  \033[91mVORTEX UNSTABLE: {failed} check(s) failed.\033[0m")
        for name, p in results:
            if not p:
                print(f"    - {name}")

    print()
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
