"""
PROJECT VOID — Beehive Audio I/O Layer

Wraps sounddevice (with pyaudio fallback) to provide real microphone
recording and speaker playback for the Beehive acoustic mesh protocol.

Includes a loopback self-test that transmits a handshake pulse through
the speaker and immediately captures it from the microphone to verify
the full acoustic pipeline.

Mode: HARDWARE — requires sounddevice or pyaudio. Falls back to
      simulation mode if no audio library is available.
"""

import time
import threading
import numpy as np
from void_engine.beehive import BeehiveProtocol, SAMPLE_RATE

AUDIO_BACKEND = None
_sd = None
_pa = None


def _detect_backend():
    global AUDIO_BACKEND, _sd, _pa
    try:
        import sounddevice as sd
        _sd = sd
        AUDIO_BACKEND = "sounddevice"
        return "sounddevice"
    except (ImportError, OSError):
        pass
    try:
        import pyaudio
        _pa = pyaudio
        AUDIO_BACKEND = "pyaudio"
        return "pyaudio"
    except (ImportError, OSError):
        pass
    AUDIO_BACKEND = "simulation"
    return "simulation"


_detect_backend()


class BeehiveAudio:
    """
    Audio I/O wrapper for the Beehive acoustic mesh protocol.

    Provides:
      - record(duration): capture audio from the default microphone
      - play(signal): play a numpy float32 array through the speaker
      - loopback_self_test(): transmit handshake + immediately record + verify
    """

    def __init__(self, protocol: BeehiveProtocol = None, sample_rate: int = SAMPLE_RATE):
        self.sr = sample_rate
        self.protocol = protocol or BeehiveProtocol(machine_id="VOID-AUDIO-NODE")
        self.backend = AUDIO_BACKEND
        self._last_record_snr = None

    def record(self, duration: float = 2.0) -> np.ndarray:
        """
        Record audio from the default microphone for `duration` seconds.
        Returns a float32 numpy array normalised to [-1.0, 1.0].

        Raises RuntimeError if no audio backend is available.
        """
        if self.backend == "sounddevice":
            audio = _sd.rec(
                int(self.sr * duration),
                samplerate=self.sr,
                channels=1,
                dtype="float32",
            )
            _sd.wait()
            return audio.flatten()

        if self.backend == "pyaudio":
            pa = _pa.PyAudio()
            chunk = 1024
            n_frames = int(self.sr / chunk * duration)
            stream = pa.open(
                format=_pa.paFloat32,
                channels=1,
                rate=self.sr,
                input=True,
                frames_per_buffer=chunk,
            )
            frames = []
            for _ in range(n_frames):
                data = stream.read(chunk, exception_on_overflow=False)
                frames.append(np.frombuffer(data, dtype=np.float32))
            stream.stop_stream()
            stream.close()
            pa.terminate()
            return np.concatenate(frames)

        raise RuntimeError(
            "No audio backend available. "
            "Install sounddevice: pip install sounddevice\n"
            "Or pyaudio: pip install pyaudio"
        )

    def play(self, signal: np.ndarray) -> None:
        """
        Play a float32 numpy array through the default speaker.

        Raises RuntimeError if no audio backend is available.
        """
        audio = signal.astype(np.float32)

        if self.backend == "sounddevice":
            _sd.play(audio, samplerate=self.sr)
            _sd.wait()
            return

        if self.backend == "pyaudio":
            pa = _pa.PyAudio()
            stream = pa.open(
                format=_pa.paFloat32,
                channels=1,
                rate=self.sr,
                output=True,
            )
            stream.write(audio.tobytes())
            stream.stop_stream()
            stream.close()
            pa.terminate()
            return

        raise RuntimeError(
            "No audio backend available. "
            "Install sounddevice: pip install sounddevice\n"
            "Or pyaudio: pip install pyaudio"
        )

    def listen(self, duration: float = 2.0) -> dict:
        """
        Record audio, run detect_neighbor and verify_fatiha_signature.
        Returns a summary dict with SNR, detection, and verification results.
        """
        audio = self.record(duration)
        detection = self.protocol.detect_neighbor(audio)
        fatiha = self.protocol.verify_fatiha_signature(audio)

        snr = detection.get("snr", 0.0)
        self._last_record_snr = snr

        return {
            "node_id": self.protocol.node_id,
            "mesh_state": self.protocol.mesh_state,
            "duration_s": duration,
            "samples": len(audio),
            "detected": detection.get("detected", False),
            "snr": snr,
            "signal_strength": detection.get("signal_strength", 0.0),
            "strength_label": detection.get("strength_label", "none"),
            "estimated_distance_m": detection.get("estimated_distance_m", 0.0),
            "harmonics_detected": detection.get("harmonics_detected", 0),
            "fatiha_verified": fatiha.get("verified", False),
            "fatiha_angle_detected_deg": fatiha.get("fatiha_angle_detected_deg", 0.0),
            "fatiha_angle_expected_deg": fatiha.get("fatiha_angle_expected_deg", 0.0),
            "angle_diff_deg": fatiha.get("angle_diff_deg", 0.0),
            "silt_layer_present": fatiha.get("silt_layer_present", False),
            "backend": self.backend,
        }

    def transmit(self, duration: float = 1.0) -> dict:
        """
        Generate and play the Beehive handshake pulse.
        Returns a summary dict.
        """
        pulse = self.protocol.generate_handshake_pulse(duration=duration)
        self.play(pulse)
        return {
            "node_id": self.protocol.node_id,
            "mesh_state": self.protocol.mesh_state,
            "duration_s": duration,
            "samples": len(pulse),
            "peak_amplitude": float(np.max(np.abs(pulse))),
            "backend": self.backend,
            "status": "transmitted",
        }

    def loopback_self_test(self, pulse_duration: float = 1.0,
                            record_duration: float = 2.0,
                            gap_s: float = 0.05) -> dict:
        """
        Loopback self-test — full-duplex capture during playback:
          1. Generate the handshake pulse
          2. Play it through the speaker AND simultaneously record from the mic
             (sounddevice: sd.playrec for true full-duplex)
             (pyaudio: starts recording thread before playback begins)
          3. Run detect_neighbor + verify_fatiha_signature on the capture

        Works without a second device if the machine's speaker output
        is captured by its own microphone (loopback / monitor source).

        Returns a full result dict.
        """
        pulse = self.protocol.generate_handshake_pulse(duration=pulse_duration)

        if self.backend == "simulation":
            noise = np.random.normal(0, 0.01, len(pulse)).astype(np.float32)
            recorded = pulse + noise
            loopback_note = "SIMULATION — no real audio hardware used"

        elif self.backend == "sounddevice":
            n_record = int(self.sr * record_duration)
            n_pulse = len(pulse)
            playback = np.zeros(n_record, dtype=np.float32)
            playback[:n_pulse] = pulse
            recorded_2d = _sd.playrec(
                playback,
                samplerate=self.sr,
                channels=1,
                dtype="float32",
                blocking=True,
            )
            recorded = recorded_2d.flatten()
            loopback_note = "LOOPBACK via sounddevice (full-duplex playrec)"

        elif self.backend == "pyaudio":
            pa = _pa.PyAudio()
            chunk = 1024
            capture_frames = []
            capture_done = threading.Event()

            def _capture():
                stream = pa.open(
                    format=_pa.paFloat32,
                    channels=1,
                    rate=self.sr,
                    input=True,
                    frames_per_buffer=chunk,
                )
                n_frames = int(self.sr / chunk * record_duration)
                for _ in range(n_frames):
                    data = stream.read(chunk, exception_on_overflow=False)
                    capture_frames.append(np.frombuffer(data, dtype=np.float32))
                stream.stop_stream()
                stream.close()
                capture_done.set()

            capture_thread = threading.Thread(target=_capture, daemon=True)
            capture_thread.start()

            time.sleep(0.02)
            out_stream = pa.open(
                format=_pa.paFloat32,
                channels=1,
                rate=self.sr,
                output=True,
            )
            out_stream.write(pulse.tobytes())
            out_stream.stop_stream()
            out_stream.close()

            capture_done.wait(timeout=record_duration + 2.0)
            pa.terminate()

            recorded = np.concatenate(capture_frames) if capture_frames else np.zeros(
                int(self.sr * record_duration), dtype=np.float32
            )
            loopback_note = "LOOPBACK via pyaudio (concurrent record+play)"

        else:
            raise RuntimeError("No audio backend available for loopback self-test")

        detection = self.protocol.detect_neighbor(recorded)
        fatiha = self.protocol.verify_fatiha_signature(recorded)

        return {
            "node_id": self.protocol.node_id,
            "mesh_state": self.protocol.mesh_state,
            "backend": self.backend,
            "loopback_note": loopback_note,
            "pulse_duration_s": pulse_duration,
            "record_duration_s": record_duration if self.backend != "simulation" else pulse_duration,
            "samples_transmitted": len(pulse),
            "samples_recorded": len(recorded),
            "detected": detection.get("detected", False),
            "snr": detection.get("snr", 0.0),
            "signal_strength": detection.get("signal_strength", 0.0),
            "strength_label": detection.get("strength_label", "none"),
            "harmonics_detected": detection.get("harmonics_detected", 0),
            "fatiha_verified": fatiha.get("verified", False),
            "fatiha_angle_detected_deg": fatiha.get("fatiha_angle_detected_deg", 0.0),
            "fatiha_angle_expected_deg": fatiha.get("fatiha_angle_expected_deg", 0.0),
            "angle_diff_deg": fatiha.get("angle_diff_deg", 0.0),
            "tolerance_deg": fatiha.get("tolerance_deg", 0.0),
            "silt_layer_present": fatiha.get("silt_layer_present", False),
            "self_test_passed": bool(detection.get("detected", False) and fatiha.get("verified", False)),
        }
