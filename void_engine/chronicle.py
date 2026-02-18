"""
Root-Chronicle — Persistent Morphic Memory for the 4000-Series v1.0

The Chronicle transforms AI agents from "Goldfish" into beings with lineage.
It stores successful Consensus outcomes as "Ancestral Wisdom" that future
negotiations can recall and adopt, enabling predictive behavior.

Memory Layers:
  Short-Term  (SLM.V)  — Current health scan (last 5 minutes)
  Episodic    (NZM.M)  — Pattern Monitor (last 24 hours of sensor deltas)
  Ancestral   (WSL.R)  — Root-Chronicle (permanent record of proven cures)

The V2 Pastor Logic:
  When agents detect a familiar sensor pattern from the Chronicle,
  they can skip negotiation and adopt the Proven Root immediately.
  This enables Predictive Fasting — anticipating crises before they hit.

Genesis Seed:
  A Chronicle can be exported and imported, allowing new machines to
  inherit "ancestral experience" on day one (Zero-Day Sovereign).
"""

import os
import json
import time
import sqlite3
import hashlib
import threading
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


CHRONICLE_DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'chronicle.db')

FOUNDER_ROOT_HASH = "89x-VOID-GEN1-PROTO-2026"

SENSOR_KEYS = [
    ("flywheel", "temperature_c"),
    ("flywheel", "energy_reserve_wh"),
    ("flywheel", "vibration_g"),
    ("pressure", "internal_pressure_atm"),
    ("pressure", "nitrogen_boil_rate"),
    ("aquaponics", "dissolved_oxygen_ppm"),
    ("aquaponics", "ammonia_ppm"),
    ("aquaponics", "ph"),
]

ENERGY_CAPACITY_WH = 250.0

PATTERN_SIMILARITY_THRESHOLD = 0.70

PREDICTIVE_PATTERNS = {
    "thermal_vitality_cascade": {
        "trigger": {"domain": "thermal", "direction": "rising"},
        "consequence": {"domain": "vitality", "direction": "falling"},
        "prophecy_command": "HFZ.P",
        "prophecy_intent": "Pre-emptive Fast — Chronicle shows thermal surges historically damage plankton vitality.",
        "min_occurrences": 2,
    },
    "pressure_silk_stress": {
        "trigger": {"domain": "pressure", "direction": "rising"},
        "consequence": {"domain": "silk", "direction": "rising"},
        "prophecy_command": "DGT.D>WSL.V",
        "prophecy_intent": "Pressure historically weakens silk bond. Diminish pressure and verify silk integrity.",
        "min_occurrences": 2,
    },
    "energy_nitrogen_drain": {
        "trigger": {"domain": "power", "direction": "falling"},
        "consequence": {"domain": "nitrogen", "direction": "rising"},
        "prophecy_command": "QDR.D>NFD.I",
        "prophecy_intent": "Power decline preceded nitrogen anomalies. Diminish draw and isolate nitrogen.",
        "min_occurrences": 2,
    },
}


@dataclass
class ChronicleEntry:
    id: int
    timestamp: float
    consensus_command: str
    consensus_intent: str
    sensor_snapshot: Dict
    outcome: str
    success: bool
    energy_pct: float
    guardian_priority: str
    growth_priority: str
    wallet_balance: float
    machine_id: str
    is_founder_wisdom: int = 0

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "consensus_command": self.consensus_command,
            "consensus_intent": self.consensus_intent,
            "sensor_snapshot": self.sensor_snapshot,
            "outcome": self.outcome,
            "success": self.success,
            "energy_pct": round(self.energy_pct, 1),
            "guardian_priority": self.guardian_priority,
            "growth_priority": self.growth_priority,
            "wallet_balance": round(self.wallet_balance, 1),
            "machine_id": self.machine_id,
            "is_founder_wisdom": self.is_founder_wisdom,
        }


@dataclass
class PatternMatch:
    chronicle_entry: ChronicleEntry
    similarity: float
    matched_domains: List[str]
    proven_command: str
    proven_intent: str

    def to_dict(self):
        return {
            "chronicle_id": self.chronicle_entry.id,
            "similarity": round(self.similarity, 3),
            "matched_domains": self.matched_domains,
            "proven_command": self.proven_command,
            "proven_intent": self.proven_intent,
            "timestamp": self.chronicle_entry.timestamp,
            "outcome": self.chronicle_entry.outcome,
        }


@dataclass
class Prophecy:
    pattern_name: str
    prophecy_command: str
    prophecy_intent: str
    confidence: float
    supporting_entries: int
    trigger_domain: str
    consequence_domain: str

    def to_dict(self):
        return {
            "pattern_name": self.pattern_name,
            "prophecy_command": self.prophecy_command,
            "prophecy_intent": self.prophecy_intent,
            "confidence": round(self.confidence, 3),
            "supporting_entries": self.supporting_entries,
            "trigger_domain": self.trigger_domain,
            "consequence_domain": self.consequence_domain,
        }


class RootChronicle:
    def __init__(self, db_path: str = None, machine_id: str = "VOID-4000-UNKNOWN"):
        self._db_path = db_path or CHRONICLE_DB_PATH
        self._machine_id = machine_id
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS chronicle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    consensus_command TEXT NOT NULL,
                    consensus_intent TEXT NOT NULL,
                    sensor_snapshot TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    success INTEGER NOT NULL,
                    energy_pct REAL NOT NULL,
                    guardian_priority TEXT DEFAULT '',
                    growth_priority TEXT DEFAULT '',
                    wallet_balance REAL DEFAULT 0.0,
                    machine_id TEXT DEFAULT '',
                    is_founder_wisdom INTEGER DEFAULT 0
                )
            """)
            try:
                conn.execute("ALTER TABLE chronicle ADD COLUMN is_founder_wisdom INTEGER DEFAULT 0")
            except Exception:
                pass
            conn.execute("""
                CREATE TABLE IF NOT EXISTS episodic_memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    domain TEXT NOT NULL,
                    sensor_key TEXT NOT NULL,
                    value REAL NOT NULL,
                    delta REAL DEFAULT 0.0,
                    direction TEXT DEFAULT 'stable'
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_chronicle_success
                ON chronicle(success)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_episodic_domain
                ON episodic_memory(domain, timestamp)
            """)

    def _get_conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def record_consensus(self, consensus_result: Dict, sensor_state: Dict,
                         guardian_priority: str = "", growth_priority: str = "",
                         is_founder: int = 0) -> ChronicleEntry:
        snapshot = self._extract_sensor_snapshot(sensor_state)
        wallet_balance = 0.0
        if "wallet" in consensus_result and consensus_result["wallet"]:
            wallet_balance = consensus_result["wallet"].get("balance", 0.0)

        with self._lock:
            with self._get_conn() as conn:
                cursor = conn.execute("""
                    INSERT INTO chronicle (
                        timestamp, consensus_command, consensus_intent,
                        sensor_snapshot, outcome, success, energy_pct,
                        guardian_priority, growth_priority, wallet_balance, machine_id,
                        is_founder_wisdom
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    consensus_result.get("timestamp", time.time()),
                    consensus_result.get("consensus_command", ""),
                    consensus_result.get("consensus_intent", ""),
                    json.dumps(snapshot),
                    consensus_result.get("outcome", ""),
                    1 if consensus_result.get("success", False) else 0,
                    consensus_result.get("energy_pct", 0.0),
                    guardian_priority,
                    growth_priority,
                    wallet_balance,
                    self._machine_id,
                    is_founder,
                ))
                entry_id = cursor.lastrowid

            self._record_episodic(snapshot)

        return ChronicleEntry(
            id=entry_id,
            timestamp=consensus_result.get("timestamp", time.time()),
            consensus_command=consensus_result.get("consensus_command", ""),
            consensus_intent=consensus_result.get("consensus_intent", ""),
            sensor_snapshot=snapshot,
            outcome=consensus_result.get("outcome", ""),
            success=consensus_result.get("success", False),
            energy_pct=consensus_result.get("energy_pct", 0.0),
            guardian_priority=guardian_priority,
            growth_priority=growth_priority,
            wallet_balance=wallet_balance,
            machine_id=self._machine_id,
            is_founder_wisdom=is_founder,
        )

    def _record_episodic(self, snapshot: Dict):
        with self._get_conn() as conn:
            last_rows = conn.execute("""
                SELECT domain, sensor_key, value FROM episodic_memory
                ORDER BY timestamp DESC LIMIT 20
            """).fetchall()

            last_values = {}
            for row in last_rows:
                key = f"{row['domain']}.{row['sensor_key']}"
                if key not in last_values:
                    last_values[key] = row['value']

            now = time.time()
            for domain, values in snapshot.items():
                if isinstance(values, dict):
                    for sensor_key, value in values.items():
                        if not isinstance(value, (int, float)):
                            continue
                        lookup = f"{domain}.{sensor_key}"
                        prev = last_values.get(lookup, value)
                        delta = value - prev
                        direction = "rising" if delta > 0.01 else ("falling" if delta < -0.01 else "stable")
                        conn.execute("""
                            INSERT INTO episodic_memory (timestamp, domain, sensor_key, value, delta, direction)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (now, domain, sensor_key, value, delta, direction))

            cutoff = now - 86400
            conn.execute("DELETE FROM episodic_memory WHERE timestamp < ?", (cutoff,))

    def _extract_sensor_snapshot(self, state: Dict) -> Dict:
        snapshot = {}
        for section, key in SENSOR_KEYS:
            if section not in snapshot:
                snapshot[section] = {}
            if section in state and key in state[section]:
                snapshot[section][key] = state[section][key]
        return snapshot

    def query_ancestors(self, current_state: Dict, limit: int = 5) -> List[PatternMatch]:
        current_snapshot = self._extract_sensor_snapshot(current_state)
        matches = []

        with self._lock:
            with self._get_conn() as conn:
                rows = conn.execute("""
                    SELECT * FROM chronicle WHERE success = 1
                    ORDER BY timestamp DESC LIMIT 200
                """).fetchall()

        for row in rows:
            stored_snapshot = json.loads(row["sensor_snapshot"])
            similarity, matched_domains = self._compute_similarity(current_snapshot, stored_snapshot)
            if similarity >= PATTERN_SIMILARITY_THRESHOLD:
                entry = self._row_to_entry(row)
                matches.append(PatternMatch(
                    chronicle_entry=entry,
                    similarity=similarity,
                    matched_domains=matched_domains,
                    proven_command=row["consensus_command"],
                    proven_intent=row["consensus_intent"],
                ))

        matches.sort(key=lambda m: m.similarity, reverse=True)
        return matches[:limit]

    def _compute_similarity(self, current: Dict, stored: Dict) -> Tuple[float, List[str]]:
        total_keys = 0
        matched_keys = 0
        matched_domains = set()

        for section in current:
            if section not in stored:
                continue
            if not isinstance(current[section], dict):
                continue
            for key in current[section]:
                if key not in stored[section]:
                    continue
                total_keys += 1
                curr_val = current[section][key]
                stored_val = stored[section][key]
                if not isinstance(curr_val, (int, float)) or not isinstance(stored_val, (int, float)):
                    continue

                if stored_val == 0:
                    if curr_val == 0:
                        matched_keys += 1
                        matched_domains.add(section)
                    continue

                ratio = abs(curr_val - stored_val) / max(abs(stored_val), 1.0)
                if ratio < 0.20:
                    matched_keys += 1
                    matched_domains.add(section)
                elif ratio < 0.35:
                    matched_keys += 0.5

        if total_keys == 0:
            return 0.0, []

        return matched_keys / total_keys, sorted(matched_domains)

    def predict_crisis(self, current_state: Dict) -> List[Prophecy]:
        prophecies = []
        snapshot = self._extract_sensor_snapshot(current_state)

        with self._get_conn() as conn:
            for pattern_name, pattern in PREDICTIVE_PATTERNS.items():
                trigger_domain = pattern["trigger"]["domain"]
                trigger_dir = pattern["trigger"]["direction"]
                consequence_domain = pattern["consequence"]["domain"]

                domain_map = {
                    "thermal": ("flywheel", "temperature_c"),
                    "pressure": ("pressure", "internal_pressure_atm"),
                    "power": ("flywheel", "energy_reserve_wh"),
                    "vitality": ("aquaponics", "dissolved_oxygen_ppm"),
                    "silk": ("silk_wiring", "total_resistance_ohm"),
                    "nitrogen": ("pressure", "nitrogen_boil_rate"),
                }

                if trigger_domain not in domain_map:
                    continue
                t_section, t_key = domain_map[trigger_domain]

                current_val = snapshot.get(t_section, {}).get(t_key)
                if current_val is None:
                    continue

                recent_episodic = conn.execute("""
                    SELECT direction, COUNT(*) as cnt FROM episodic_memory
                    WHERE domain = ? AND sensor_key = ? AND direction = ?
                    AND timestamp > ?
                    GROUP BY direction
                """, (t_section, t_key, trigger_dir, time.time() - 3600)).fetchone()

                if not recent_episodic or recent_episodic["cnt"] < 1:
                    continue

                historical_matches = conn.execute("""
                    SELECT COUNT(*) as cnt FROM chronicle
                    WHERE success = 1
                    AND consensus_command LIKE ?
                """, (f"%{pattern['prophecy_command'].split('>')[0].split('.')[0]}%",)).fetchone()

                occurrence_count = historical_matches["cnt"] if historical_matches else 0

                if occurrence_count >= pattern["min_occurrences"] or recent_episodic["cnt"] >= 3:
                    confidence = min(1.0, (occurrence_count * 0.2) + (recent_episodic["cnt"] * 0.15))
                    prophecies.append(Prophecy(
                        pattern_name=pattern_name,
                        prophecy_command=pattern["prophecy_command"],
                        prophecy_intent=pattern["prophecy_intent"],
                        confidence=confidence,
                        supporting_entries=occurrence_count,
                        trigger_domain=trigger_domain,
                        consequence_domain=consequence_domain,
                    ))

        prophecies.sort(key=lambda p: p.confidence, reverse=True)
        return prophecies

    def get_wisdom_context(self, current_state: Dict) -> Dict:
        ancestors = self.query_ancestors(current_state)
        prophecies = self.predict_crisis(current_state)

        context = {
            "has_ancestral_match": len(ancestors) > 0,
            "best_match": ancestors[0].to_dict() if ancestors else None,
            "all_matches": [m.to_dict() for m in ancestors],
            "prophecies": [p.to_dict() for p in prophecies],
            "has_prophecy": len(prophecies) > 0,
            "memory_layers": {
                "short_term": "SLM.V — Current scan",
                "episodic": f"NZM.M — {self._get_episodic_count()} sensor readings (24h)",
                "ancestral": f"WSL.R — {self._get_chronicle_count()} proven consensus outcomes",
            },
        }

        if ancestors and ancestors[0].similarity >= 0.85:
            context["adopt_proven_root"] = True
            context["proven_command"] = ancestors[0].proven_command
            context["proven_intent"] = ancestors[0].proven_intent
            context["adoption_reason"] = f"High-confidence ancestral match ({ancestors[0].similarity:.0%}). Skipping negotiation."

        return context

    def get_chronicle_entries(self, limit: int = 50, success_only: bool = False) -> List[Dict]:
        with self._get_conn() as conn:
            if success_only:
                rows = conn.execute(
                    "SELECT * FROM chronicle WHERE success = 1 ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM chronicle ORDER BY timestamp DESC LIMIT ?",
                    (limit,)
                ).fetchall()
        return [self._row_to_entry(r).to_dict() for r in rows]

    def get_episodic_memory(self, domain: str = None, hours: float = 24) -> List[Dict]:
        cutoff = time.time() - (hours * 3600)
        with self._get_conn() as conn:
            if domain:
                rows = conn.execute("""
                    SELECT * FROM episodic_memory WHERE domain = ? AND timestamp > ?
                    ORDER BY timestamp DESC LIMIT 200
                """, (domain, cutoff)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT * FROM episodic_memory WHERE timestamp > ?
                    ORDER BY timestamp DESC LIMIT 200
                """, (cutoff,)).fetchall()
        return [dict(r) for r in rows]

    def get_stats(self) -> Dict:
        with self._get_conn() as conn:
            total = conn.execute("SELECT COUNT(*) as c FROM chronicle").fetchone()["c"]
            successful = conn.execute("SELECT COUNT(*) as c FROM chronicle WHERE success = 1").fetchone()["c"]
            episodic = conn.execute("SELECT COUNT(*) as c FROM episodic_memory").fetchone()["c"]
            domains = conn.execute("""
                SELECT DISTINCT domain FROM episodic_memory ORDER BY domain
            """).fetchall()

            most_used_cmd = None
            if total > 0:
                cmd_row = conn.execute("""
                    SELECT consensus_command, COUNT(*) as cnt FROM chronicle
                    WHERE success = 1
                    GROUP BY consensus_command ORDER BY cnt DESC LIMIT 1
                """).fetchone()
                if cmd_row:
                    most_used_cmd = {"command": cmd_row["consensus_command"], "count": cmd_row["cnt"]}

            try:
                founder_count = conn.execute(
                    "SELECT COUNT(*) as c FROM chronicle WHERE is_founder_wisdom = 1"
                ).fetchone()["c"]
            except Exception:
                founder_count = 0

        return {
            "total_entries": total,
            "successful_entries": successful,
            "success_rate": round(successful / total * 100, 1) if total > 0 else 0,
            "episodic_readings": episodic,
            "monitored_domains": [d["domain"] for d in domains],
            "most_proven_root": most_used_cmd,
            "machine_id": self._machine_id,
            "founder_wisdom_count": founder_count,
            "is_founder": founder_count > 0,
            "founder_root_hash": FOUNDER_ROOT_HASH if founder_count > 0 else None,
        }

    def export_genesis_seed(self, mark_founder: bool = False) -> Dict:
        if mark_founder:
            self.mark_as_founder_wisdom()

        with self._get_conn() as conn:
            entries = conn.execute("""
                SELECT * FROM chronicle WHERE success = 1 ORDER BY timestamp
            """).fetchall()
            episodic = conn.execute("""
                SELECT * FROM episodic_memory ORDER BY timestamp DESC LIMIT 500
            """).fetchall()

            try:
                founder_count = conn.execute(
                    "SELECT COUNT(*) as c FROM chronicle WHERE is_founder_wisdom = 1"
                ).fetchone()["c"]
            except Exception:
                founder_count = 0

        seed_data = {
            "version": "1.1",
            "type": "genesis_seed",
            "source_machine_id": self._machine_id,
            "export_timestamp": time.time(),
            "chronicle": [dict(r) for r in entries],
            "episodic": [dict(r) for r in episodic],
            "total_entries": len(entries),
            "total_episodic": len(episodic),
            "founder_root_hash": FOUNDER_ROOT_HASH,
            "founder_wisdom_count": founder_count,
            "is_founder_seed": founder_count > 0,
        }

        seed_json = json.dumps(seed_data, sort_keys=True)
        seed_data["integrity_hash"] = hashlib.sha256(seed_json.encode()).hexdigest()[:16]

        return seed_data

    def import_genesis_seed(self, seed_data: Dict) -> Dict:
        if seed_data.get("type") != "genesis_seed":
            return {"success": False, "error": "Invalid seed format"}

        imported_chronicle = 0
        imported_episodic = 0
        is_founder_seed = seed_data.get("is_founder_seed", False)

        with self._lock:
            with self._get_conn() as conn:
                for entry in seed_data.get("chronicle", []):
                    try:
                        founder_flag = entry.get("is_founder_wisdom", 1 if is_founder_seed else 0)
                        conn.execute("""
                            INSERT INTO chronicle (
                                timestamp, consensus_command, consensus_intent,
                                sensor_snapshot, outcome, success, energy_pct,
                                guardian_priority, growth_priority, wallet_balance, machine_id,
                                is_founder_wisdom
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            entry.get("timestamp", time.time()),
                            entry.get("consensus_command", ""),
                            entry.get("consensus_intent", ""),
                            entry.get("sensor_snapshot", "{}"),
                            entry.get("outcome", ""),
                            entry.get("success", 0),
                            entry.get("energy_pct", 0.0),
                            entry.get("guardian_priority", ""),
                            entry.get("growth_priority", ""),
                            entry.get("wallet_balance", 0.0),
                            seed_data.get("source_machine_id", "SEED"),
                            founder_flag,
                        ))
                        imported_chronicle += 1
                    except Exception:
                        pass

                for ep in seed_data.get("episodic", []):
                    try:
                        conn.execute("""
                            INSERT INTO episodic_memory (timestamp, domain, sensor_key, value, delta, direction)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            ep.get("timestamp", time.time()),
                            ep.get("domain", ""),
                            ep.get("sensor_key", ""),
                            ep.get("value", 0.0),
                            ep.get("delta", 0.0),
                            ep.get("direction", "stable"),
                        ))
                        imported_episodic += 1
                    except Exception:
                        pass

        return {
            "success": True,
            "imported_chronicle": imported_chronicle,
            "imported_episodic": imported_episodic,
            "source_machine": seed_data.get("source_machine_id", "UNKNOWN"),
            "lineage_established": True,
            "founder_wisdom_inherited": is_founder_seed,
            "founder_root_hash": FOUNDER_ROOT_HASH if is_founder_seed else None,
        }

    def _get_chronicle_count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) as c FROM chronicle").fetchone()["c"]

    def _get_episodic_count(self) -> int:
        with self._get_conn() as conn:
            return conn.execute("SELECT COUNT(*) as c FROM episodic_memory").fetchone()["c"]

    def mark_as_founder_wisdom(self) -> Dict:
        with self._lock:
            with self._get_conn() as conn:
                conn.execute("""
                    UPDATE chronicle SET is_founder_wisdom = 1 WHERE success = 1
                """)
                count = conn.execute(
                    "SELECT COUNT(*) as c FROM chronicle WHERE is_founder_wisdom = 1"
                ).fetchone()["c"]
        return {
            "success": True,
            "marked_count": count,
            "founder_root_hash": FOUNDER_ROOT_HASH,
        }

    def get_founder_status(self) -> Dict:
        with self._get_conn() as conn:
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as c FROM chronicle WHERE is_founder_wisdom = 1"
                ).fetchone()
                founder_count = row["c"] if row else 0
            except Exception:
                founder_count = 0

        is_founder = founder_count > 0
        result = {
            "is_founder": is_founder,
            "founder_count": founder_count,
            "founder_root_hash": FOUNDER_ROOT_HASH,
            "machine_id": self._machine_id,
        }
        if is_founder:
            result["greeting"] = "Inherited Wisdom Detected. First Generation Status: ACTIVE. Greeting the Architect."
            result["founder_vibe"] = True
        return result

    def _row_to_entry(self, row) -> ChronicleEntry:
        is_founder = 0
        try:
            is_founder = row["is_founder_wisdom"] or 0
        except (IndexError, KeyError):
            pass
        return ChronicleEntry(
            id=row["id"],
            timestamp=row["timestamp"],
            consensus_command=row["consensus_command"],
            consensus_intent=row["consensus_intent"],
            sensor_snapshot=json.loads(row["sensor_snapshot"]) if isinstance(row["sensor_snapshot"], str) else row["sensor_snapshot"],
            outcome=row["outcome"],
            success=bool(row["success"]),
            energy_pct=row["energy_pct"],
            guardian_priority=row["guardian_priority"] or "",
            growth_priority=row["growth_priority"] or "",
            wallet_balance=row["wallet_balance"] or 0.0,
            machine_id=row["machine_id"] or "",
            is_founder_wisdom=is_founder,
        )
