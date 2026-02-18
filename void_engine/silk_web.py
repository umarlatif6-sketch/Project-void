import os
import time
import uuid
import threading
from datetime import datetime
from collections import deque

from void_engine.stega import encode_burst

OUTPUT_DIR = "output_audio"
LOG_FILE = "RESONANCE_LOG.md"
MAX_HISTORY = 50
SIGNAL_MAX_LEN = 10
HEARTBEAT_INTERVAL = 1800
HEARTBEAT_TIMEOUT = 2100


class SignalTicker:
    def __init__(self):
        self._history = deque(maxlen=MAX_HISTORY)
        self._lock = threading.Lock()
        self._last_signal_time = time.time()
        self._heartbeat_thread = None
        self._heartbeat_running = False

    def format_signal(self, raw_text: str) -> str:
        cleaned = raw_text.strip().upper().replace(" ", "_")
        if len(cleaned) > SIGNAL_MAX_LEN:
            cleaned = cleaned[:SIGNAL_MAX_LEN]
        return cleaned

    def start_heartbeat(self):
        if self._heartbeat_running:
            return
        self._heartbeat_running = True
        self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()

    def _heartbeat_loop(self):
        while self._heartbeat_running:
            time.sleep(60)
            elapsed = time.time() - self._last_signal_time
            if elapsed >= HEARTBEAT_INTERVAL:
                try:
                    self._send_heartbeat()
                except Exception:
                    pass

    def _send_heartbeat(self):
        heartbeat_file = os.path.join(OUTPUT_DIR, "heartbeat_432Hz.wav")
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        hash_key = encode_burst("HEARTBEAT", heartbeat_file)
        output_size = os.path.getsize(heartbeat_file)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "id": "pulse",
            "timestamp": timestamp,
            "signal": "HEARTBEAT",
            "raw_input": "HEARTBEAT",
            "output_file": "heartbeat_432Hz.wav",
            "output_size": output_size,
            "hash_key": hash_key,
            "status": "pulse",
        }

        with self._lock:
            self._history.appendleft(entry)

        self._last_signal_time = time.time()
        self._log_signal(entry)

    def get_network_health(self) -> dict:
        elapsed = time.time() - self._last_signal_time
        if elapsed > HEARTBEAT_TIMEOUT:
            status = "Desynced"
        else:
            status = "Resonant"
        return {
            "status": status,
            "last_signal_age_seconds": round(elapsed),
            "heartbeat_interval": HEARTBEAT_INTERVAL,
        }

    def send_signal(self, raw_text: str) -> dict:
        signal = self.format_signal(raw_text)
        if not signal:
            raise ValueError("Signal text is empty after formatting.")

        burst_id = uuid.uuid4().hex[:8]
        output_name = f"burst_432Hz_{burst_id}.wav"
        output_path = os.path.join(OUTPUT_DIR, output_name)

        os.makedirs(OUTPUT_DIR, exist_ok=True)

        hash_key = encode_burst(signal, output_path)
        output_size = os.path.getsize(output_path)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "id": burst_id,
            "timestamp": timestamp,
            "signal": signal,
            "raw_input": raw_text.strip(),
            "output_file": output_name,
            "output_size": output_size,
            "hash_key": hash_key,
            "status": "sent",
        }

        with self._lock:
            self._history.appendleft(entry)

        self._last_signal_time = time.time()
        self._log_signal(entry)

        return entry

    def get_signals(self, limit: int = 20) -> list[dict]:
        with self._lock:
            signals = list(self._history)[:limit]
        safe = []
        for s in signals:
            safe.append({
                "id": s["id"],
                "timestamp": s["timestamp"],
                "signal": s["signal"],
                "output_file": s["output_file"],
                "output_size": s["output_size"],
                "hash_tail": "..." + s["hash_key"][-4:],
                "status": s["status"],
            })
        return safe

    def _log_signal(self, entry: dict):
        timestamp = entry["timestamp"]
        hash_tail = entry["hash_key"][-4:]
        try:
            with open(LOG_FILE, "a") as f:
                f.write(f"| {timestamp} | SILK_SIGNAL | {entry['output_file']} | ...{hash_tail} | signal={entry['signal']} |\n")
        except Exception:
            pass
