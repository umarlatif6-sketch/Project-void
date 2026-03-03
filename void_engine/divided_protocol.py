"""
Divided Operational Protocol — The Axiomatic Sequence

Five-step pipeline that bridges raw steganography to Al-Jabr logic:
  1. Initialize (SLM.V)  — System health check
  2. Calibrate  (TRK.A)  — Verify 432 Hz resonance on carrier
  3. Observe    (ZHR.V)   — Motion→light axiom check
  4. Inject     (KTM.A)   — Steganography encode with vortex scatter
  5. Commit     (JDR.A)   — Log transaction to Root-Chronicle

Each step returns a status. The protocol short-circuits on failure.
"""

import os
import time
import wave
import numpy as np
from typing import Dict, Optional

from void_engine.stega import encode, encode_stereo, check_resonance_purity, VILLAGE_STANDARD_HZ
from void_engine.calculator import analyze_carrier
from void_engine.compressor import compress_file

PROTOCOL_VERSION = "1.1"
RESONANCE_THRESHOLD = 5.0
RADIANCE_MOTION_THRESHOLD = 3000


def _detect_biophony_carrier(carrier_path: str) -> Dict:
    chirpmap_path = carrier_path.replace(".wav", ".chirpmap.npy")
    has_chirpmap = os.path.exists(chirpmap_path)

    with wave.open(carrier_path, "rb") as wf:
        sr = wf.getframerate()
        n_frames = wf.getnframes()
        n_ch = wf.getnchannels()
        raw = wf.readframes(min(n_frames, sr * 5))

    samples = np.frombuffer(raw, dtype=np.int16).astype(np.float64)
    if n_ch > 1:
        samples = samples[::n_ch]

    window_size = min(len(samples), 16384)
    segment = samples[:window_size]
    windowed = segment * np.hanning(len(segment))
    spectrum = np.abs(np.fft.rfft(windowed))
    freqs = np.fft.rfftfreq(len(segment), 1.0 / sr)

    low_mask = (freqs >= 15) & (freqs <= 50)
    mid_mask = (freqs >= 300) & (freqs <= 800)
    high_mask = (freqs >= 2000) & (freqs <= 12000)

    total_power = np.mean(spectrum ** 2) + 1e-10
    low_power = np.mean(spectrum[low_mask] ** 2) if np.any(low_mask) else 0
    mid_power = np.mean(spectrum[mid_mask] ** 2) if np.any(mid_mask) else 0
    high_power = np.mean(spectrum[high_mask] ** 2) if np.any(high_mask) else 0

    low_ratio = low_power / total_power
    mid_ratio = mid_power / total_power
    high_ratio = high_power / total_power

    biophony_active = has_chirpmap or (high_ratio > 0.05)
    sapphire_thread = (low_ratio > 0.01 and mid_ratio > 0.01 and high_ratio > 0.05)

    return {
        "is_biophony": biophony_active,
        "has_chirpmap": has_chirpmap,
        "sapphire_thread": sapphire_thread,
        "low_shelf_ratio": round(float(low_ratio), 4),
        "mid_shelf_ratio": round(float(mid_ratio), 4),
        "high_shelf_ratio": round(float(high_ratio), 4),
        "chirpmap_path": chirpmap_path if has_chirpmap else None,
    }


class ProtocolStep:
    def __init__(self, index: int, name: str, root_code: str, description: str):
        self.index = index
        self.name = name
        self.root_code = root_code
        self.description = description
        self.status = "pending"
        self.result = None
        self.duration_ms = 0.0
        self.error = None

    def to_dict(self):
        return {
            "index": self.index,
            "name": self.name,
            "root_code": self.root_code,
            "description": self.description,
            "status": self.status,
            "result": self.result,
            "duration_ms": round(self.duration_ms, 2),
            "error": self.error,
        }


class DividedProtocol:
    def __init__(self, diagnostics, simulator, chronicle=None, wallet=None):
        self._diagnostics = diagnostics
        self._simulator = simulator
        self._chronicle = chronicle
        self._wallet = wallet
        self._last_run = None

    def get_readiness(self) -> Dict:
        state = self._simulator.get_state()
        fw = state.get("flywheel", {})
        rpm = fw.get("rpm", 0)
        energy = fw.get("energy_wh", 0)
        temp = fw.get("temperature_c", 0)

        checks = {
            "system_online": True,
            "flywheel_rpm": rpm,
            "flywheel_energy_wh": energy,
            "temperature_c": temp,
            "chronicle_available": self._chronicle is not None,
            "wallet_available": self._wallet is not None,
            "diagnostics_available": self._diagnostics is not None,
        }

        report = self._diagnostics.scan()
        checks["system_status"] = report.overall_status
        checks["critical_issues"] = report.critical_count
        checks["ready"] = report.overall_status != "CRITICAL"

        return {
            "protocol_version": PROTOCOL_VERSION,
            "checks": checks,
            "ready": checks["ready"],
            "last_run": self._last_run,
        }

    def execute(self, carrier_path: str, payload_path: str,
                lsb_depth: int = 1, output_path: str = None,
                low_power: bool = False) -> Dict:

        steps = [
            ProtocolStep(1, "Initialize", "SLM.V", "System health verification"),
            ProtocolStep(2, "Calibrate", "TRK.A", "432 Hz resonance calibration"),
            ProtocolStep(3, "Observe", "ZHR.V", "Radiance axiom — motion-to-light check"),
            ProtocolStep(4, "Inject", "KTM.A", "Vortex scatter steganography encode"),
            ProtocolStep(5, "Commit", "JDR.A", "Transaction committed to Root-Chronicle"),
        ]

        protocol_start = time.time()
        overall_success = True
        final_result = {}

        for step in steps:
            step_start = time.time()
            step.status = "running"

            try:
                if step.index == 1:
                    step.result = self._step_initialize()
                elif step.index == 2:
                    step.result = self._step_calibrate(carrier_path)
                elif step.index == 3:
                    step.result = self._step_observe(carrier_path)
                elif step.index == 4:
                    step.result = self._step_inject(
                        carrier_path, payload_path, lsb_depth,
                        output_path, low_power
                    )
                    final_result = step.result
                elif step.index == 5:
                    step.result = self._step_commit(final_result)

                step.status = "pass"
                step.duration_ms = (time.time() - step_start) * 1000

            except Exception as e:
                step.status = "fail"
                step.error = str(e)
                step.duration_ms = (time.time() - step_start) * 1000
                overall_success = False
                for remaining in steps[step.index:]:
                    remaining.status = "skipped"
                break

        total_ms = (time.time() - protocol_start) * 1000

        run_result = {
            "success": overall_success,
            "protocol_version": PROTOCOL_VERSION,
            "steps": [s.to_dict() for s in steps],
            "total_duration_ms": round(total_ms, 2),
            "chain": "SLM.V>TRK.A>ZHR.V>KTM.A>JDR.A",
        }

        if overall_success and final_result:
            run_result["hash_key"] = final_result.get("hash_key")
            run_result["output_file"] = final_result.get("output_file")
            run_result["scatter_mode"] = final_result.get("scatter_mode", "vortex")
            run_result["biophony_carrier"] = final_result.get("biophony_carrier", False)

        self._last_run = {
            "timestamp": time.time(),
            "success": overall_success,
            "carrier": os.path.basename(carrier_path),
            "payload": os.path.basename(payload_path),
            "duration_ms": round(total_ms, 2),
        }

        return run_result

    def _step_initialize(self) -> Dict:
        report = self._diagnostics.scan()

        if report.overall_status == "CRITICAL":
            raise RuntimeError(
                f"SLM.V FAIL — {report.critical_count} critical issue(s): {report.summary}"
            )

        return {
            "overall_status": report.overall_status,
            "summary": report.summary,
            "total_checks": report.total_checks,
            "critical": report.critical_count,
            "warnings": report.warning_count,
            "nominal": report.nominal_count,
        }

    def _step_calibrate(self, carrier_path: str) -> Dict:
        if not os.path.exists(carrier_path):
            raise FileNotFoundError(f"Carrier not found: {carrier_path}")

        purity = check_resonance_purity(carrier_path)
        capacity = analyze_carrier(carrier_path)

        snr = purity.get("snr_432hz_db", 0)
        resonance_score = capacity.get("resonance_score", 0)

        state = self._simulator.get_state()
        fw = state.get("flywheel", {})
        rpm = fw.get("rpm", 0)

        calibrated = True
        warnings = []

        if snr < RESONANCE_THRESHOLD:
            warnings.append(f"Low 432 Hz resonance (SNR: {snr:.1f} dB). Carrier may not be optimally tuned.")

        if rpm < RADIANCE_MOTION_THRESHOLD:
            self._simulator.set_state("flywheel", {"rpm": max(rpm, RADIANCE_MOTION_THRESHOLD)})
            warnings.append(f"Flywheel calibrated from {rpm} to {RADIANCE_MOTION_THRESHOLD} RPM")

        return {
            "carrier_snr_db": round(snr, 2),
            "resonance_score": round(resonance_score, 4),
            "flywheel_rpm": rpm,
            "calibrated": calibrated,
            "capacity_1bit": capacity.get("capacity_1bit", 0),
            "capacity_2bit": capacity.get("capacity_2bit", 0),
            "warnings": warnings,
        }

    def _step_observe(self, carrier_path: str) -> Dict:
        state = self._simulator.get_state()
        fw = state.get("flywheel", {})
        rpm = fw.get("rpm", 0)

        motion_active = rpm >= RADIANCE_MOTION_THRESHOLD
        purity = check_resonance_purity(carrier_path)
        has_glow = purity.get("snr_432hz_db", 0) > 0

        biophony = _detect_biophony_carrier(carrier_path)
        biophony_active = biophony["is_biophony"]
        sapphire_thread = biophony["sapphire_thread"]

        if biophony_active:
            glow_level = "MAX_GLOW" if sapphire_thread else "GLOW"
            axiom_result = "PASS"
        elif motion_active:
            glow_level = "GLOW"
            axiom_result = "PASS"
        else:
            glow_level = "DIM"
            axiom_result = "CONDITIONAL"

        if not motion_active and not has_glow and not biophony_active:
            axiom_result = "BLOCKAGE"
            raise RuntimeError(
                f"ZHR.V BLOCKAGE — Motion (TRK: {rpm} RPM) below threshold "
                f"and no glow detected. Mechanical blockage suspected."
            )

        self._biophony_info = biophony

        return {
            "axiom": "if TRK.A > threshold then ZHR.A",
            "motion_rpm": rpm,
            "motion_threshold": RADIANCE_MOTION_THRESHOLD,
            "motion_active": motion_active,
            "glow_detected": has_glow,
            "glow_level": glow_level,
            "glow_snr_db": round(purity.get("snr_432hz_db", 0), 2),
            "axiom_result": axiom_result,
            "biophony_active": biophony_active,
            "sapphire_thread": sapphire_thread,
            "shelf_ratios": {
                "low": biophony["low_shelf_ratio"],
                "mid": biophony["mid_shelf_ratio"],
                "high": biophony["high_shelf_ratio"],
            },
        }

    def _step_inject(self, carrier_path: str, payload_path: str,
                     lsb_depth: int, output_path: str,
                     low_power: bool) -> Dict:
        if not os.path.exists(carrier_path):
            raise FileNotFoundError(f"Carrier not found: {carrier_path}")
        if not os.path.exists(payload_path):
            raise FileNotFoundError(f"Payload not found: {payload_path}")

        compressed, name, ext, orig_size = compress_file(payload_path, low_power=low_power)

        carrier_basename = os.path.splitext(os.path.basename(carrier_path))[0]
        if output_path is None:
            output_dir = os.path.join(os.path.dirname(carrier_path), "..", "output_audio")
            output_dir = os.path.normpath(output_dir)
            os.makedirs(output_dir, exist_ok=True)
            output_path = os.path.join(output_dir, f"{carrier_basename}_void.wav")

        with wave.open(carrier_path, "rb") as wf:
            n_channels = wf.getnchannels()

        biophony = getattr(self, "_biophony_info", None)
        use_chirp_sync = biophony and biophony.get("has_chirpmap", False)
        scatter_mode = "chirp_sync" if use_chirp_sync else "vortex"

        if n_channels == 2:
            hash_key = encode_stereo(
                carrier_path, compressed, name, ext, output_path,
                lsb_depth,
                vortex=(not use_chirp_sync),
                chirp_sync=use_chirp_sync
            )
        else:
            hash_key = encode(
                carrier_path, compressed, name, ext, output_path,
                lsb_depth,
                vortex=(not use_chirp_sync),
                chirp_sync=use_chirp_sync
            )

        output_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0

        return {
            "hash_key": hash_key,
            "output_file": os.path.basename(output_path),
            "output_path": output_path,
            "original_size": orig_size,
            "compressed_size": len(compressed),
            "output_size": output_size,
            "lsb_depth": lsb_depth,
            "scatter_mode": scatter_mode,
            "stereo": n_channels == 2,
            "biophony_carrier": use_chirp_sync,
        }

    def _step_commit(self, inject_result: Dict) -> Dict:
        if self._chronicle is None:
            return {
                "committed": False,
                "reason": "No chronicle available",
            }

        sensor_state = self._simulator.get_state()

        consensus_result = {
            "success": True,
            "consensus_command": "SLM.V>TRK.A>ZHR.V>KTM.A>JDR.A",
            "intent": "Divided Protocol — full encode pipeline",
            "outcome": f"Encoded {inject_result.get('output_file', 'unknown')} via vortex scatter",
            "energy_pct": sensor_state.get("flywheel", {}).get("energy_wh", 0) / 100.0,
        }

        entry = self._chronicle.record_consensus(
            consensus_result, sensor_state,
            guardian_priority="SLM",
            growth_priority="KTM",
        )

        if self._wallet:
            try:
                self._wallet.spend("divided_protocol", 2.0)
            except Exception:
                pass

        return {
            "committed": True,
            "chronicle_id": entry.id if hasattr(entry, "id") else None,
            "command_logged": "SLM.V>TRK.A>ZHR.V>KTM.A>JDR.A",
            "wallet_charged": 2.0 if self._wallet else 0,
        }
