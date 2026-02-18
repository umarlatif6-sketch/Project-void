import os
import uuid
import threading
from datetime import datetime
from collections import deque

from void_engine.stega import encode_burst

OUTPUT_DIR = "output_audio"
LOG_FILE = "RESONANCE_LOG.md"
MAX_HISTORY = 50
SIGNAL_MAX_LEN = 10


class SignalTicker:
    def __init__(self):
        self._history = deque(maxlen=MAX_HISTORY)
        self._lock = threading.Lock()

    def format_signal(self, raw_text: str) -> str:
        cleaned = raw_text.strip().upper().replace(" ", "_")
        if len(cleaned) > SIGNAL_MAX_LEN:
            cleaned = cleaned[:SIGNAL_MAX_LEN]
        return cleaned

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
