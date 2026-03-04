import json
import time
import threading
from typing import Dict, List, Optional
from void_engine.al_jabr_286 import fatiha_286_hexdigest_from_str, fatiha_286_truncated

FOUNDER_ROOT_HASH = "89x-VOID-GEN1-PROTO-2026"
MIN_RELAY_HONOR = 0.3


def _compute_block_hash(block_index: int, timestamp: float,
                        previous_hash: str, payload: str,
                        node_id: str) -> str:
    raw = f"{block_index}{timestamp}{previous_hash}{payload}{node_id}"
    return fatiha_286_hexdigest_from_str(raw)


def _phase_key_signature(node_id: str, payload: str) -> str:
    raw = f"PHASE-KEY:{node_id}:{payload}"
    return fatiha_286_truncated(raw.encode("utf-8"), 16)


def _verify_phase_key_signature(node_id: str, payload: str,
                                signature: str) -> bool:
    expected = _phase_key_signature(node_id, payload)
    return expected == signature


class SiltBlock:
    def __init__(self, block_index: int, timestamp: float,
                 previous_hash: str, payload: dict, node_id: str,
                 kinetic_weight: float = 0.0,
                 biological_weight: float = 0.0,
                 signature: str = ""):
        self.block_index = block_index
        self.timestamp = timestamp
        self.previous_hash = previous_hash
        self.payload = payload
        self.node_id = node_id
        self.kinetic_weight = kinetic_weight
        self.biological_weight = biological_weight
        payload_str = json.dumps(payload, sort_keys=True)
        self.block_hash = _compute_block_hash(
            block_index, timestamp, previous_hash, payload_str, node_id
        )
        self.signature = signature or _phase_key_signature(node_id, payload_str)

    def to_dict(self) -> dict:
        return {
            "block_index": self.block_index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "block_hash": self.block_hash,
            "payload": self.payload,
            "node_id": self.node_id,
            "kinetic_weight": self.kinetic_weight,
            "biological_weight": self.biological_weight,
            "signature": self.signature,
        }


class SiltLedger:
    def __init__(self, node_id: str = "VOID-GENESIS"):
        self.node_id = node_id
        self.chain: List[SiltBlock] = []
        self.relay_honor: Dict[str, Dict] = {}
        self.proposals: Dict[str, Dict] = {}
        self._lock = threading.Lock()
        self._create_genesis_block()

    def _create_genesis_block(self):
        genesis_payload = {
            "type": "genesis",
            "founder_root_hash": FOUNDER_ROOT_HASH,
            "message": "In the beginning was the Signal.",
        }
        genesis = SiltBlock(
            block_index=0,
            timestamp=time.time(),
            previous_hash="0" * 72,
            payload=genesis_payload,
            node_id=self.node_id,
            kinetic_weight=0.0,
            biological_weight=0.0,
        )
        self.chain.append(genesis)

    def get_latest_block(self) -> SiltBlock:
        with self._lock:
            return self.chain[-1]

    def add_block(self, payload: dict, node_id: str = "",
                  kinetic_weight: float = 0.0,
                  biological_weight: float = 0.0,
                  signature: str = "") -> dict:
        node = node_id or self.node_id
        payload_str = json.dumps(payload, sort_keys=True)

        if signature:
            if not _verify_phase_key_signature(node, payload_str, signature):
                return {"success": False, "error": "Invalid phase-key signature"}
        else:
            signature = _phase_key_signature(node, payload_str)

        honor = self._get_relay_honor(node)
        if node != self.node_id and honor < MIN_RELAY_HONOR:
            return {
                "success": False,
                "error": f"Relay honor too low ({honor:.2f} < {MIN_RELAY_HONOR})",
            }

        with self._lock:
            latest = self.chain[-1]
            new_block = SiltBlock(
                block_index=latest.block_index + 1,
                timestamp=time.time(),
                previous_hash=latest.block_hash,
                payload=payload,
                node_id=node,
                kinetic_weight=kinetic_weight,
                biological_weight=biological_weight,
                signature=signature,
            )
            self.chain.append(new_block)
            self._record_relay_success(node)

        return {
            "success": True,
            "block_index": new_block.block_index,
            "block_hash": new_block.block_hash,
        }

    def validate_chain(self) -> dict:
        with self._lock:
            if not self.chain:
                return {"valid": False, "error": "Empty chain"}

            if self.chain[0].previous_hash != "0" * 72:
                return {"valid": False, "error": "Invalid genesis block"}

            for i in range(1, len(self.chain)):
                current = self.chain[i]
                previous = self.chain[i - 1]

                if current.previous_hash != previous.block_hash:
                    return {
                        "valid": False,
                        "error": f"Hash chain break at block {i}",
                        "block_index": i,
                    }

                payload_str = json.dumps(current.payload, sort_keys=True)
                expected_hash = _compute_block_hash(
                    current.block_index, current.timestamp,
                    current.previous_hash, payload_str, current.node_id,
                )
                if current.block_hash != expected_hash:
                    return {
                        "valid": False,
                        "error": f"Block hash mismatch at block {i}",
                        "block_index": i,
                    }

            return {
                "valid": True,
                "chain_height": len(self.chain),
                "genesis_hash": self.chain[0].block_hash,
                "latest_hash": self.chain[-1].block_hash,
            }

    def _get_relay_honor(self, node_id: str) -> float:
        if node_id == self.node_id:
            return 1.0
        info = self.relay_honor.get(node_id)
        if not info:
            return 1.0
        total = info.get("total", 0)
        if total == 0:
            return 1.0
        return info.get("success", 0) / total

    def _record_relay_success(self, node_id: str):
        if node_id not in self.relay_honor:
            self.relay_honor[node_id] = {"success": 0, "total": 0}
        self.relay_honor[node_id]["success"] += 1
        self.relay_honor[node_id]["total"] += 1

    def record_relay_failure(self, node_id: str):
        with self._lock:
            if node_id not in self.relay_honor:
                self.relay_honor[node_id] = {"success": 0, "total": 0}
            self.relay_honor[node_id]["total"] += 1

    def propose_vote(self, proposal: str, node_id: str = "",
                     kinetic_weight: float = 0.0,
                     biological_weight: float = 0.0) -> dict:
        node = node_id or self.node_id
        proposal_id = fatiha_286_truncated(
            f"{proposal}{time.time()}{node}".encode(), 12
        )

        honor = self._get_relay_honor(node)
        voting_weight = (
            kinetic_weight * 0.4
            + biological_weight * 0.4
            + honor * 0.2
        )

        with self._lock:
            self.proposals[proposal_id] = {
                "proposal": proposal,
                "proposer": node,
                "timestamp": time.time(),
                "votes": [{
                    "node_id": node,
                    "weight": voting_weight,
                    "kinetic_weight": kinetic_weight,
                    "biological_weight": biological_weight,
                    "relay_honor": honor,
                    "vote": "yes",
                }],
                "status": "active",
                "total_weight_yes": voting_weight,
                "total_weight_no": 0.0,
            }

        return {
            "success": True,
            "proposal_id": proposal_id,
            "voting_weight": round(voting_weight, 4),
        }

    def cast_vote(self, proposal_id: str, node_id: str, vote: str,
                  kinetic_weight: float = 0.0,
                  biological_weight: float = 0.0) -> dict:
        if vote not in ("yes", "no"):
            return {"success": False, "error": "Vote must be 'yes' or 'no'"}

        with self._lock:
            prop = self.proposals.get(proposal_id)
            if not prop:
                return {"success": False, "error": "Proposal not found"}
            if prop["status"] != "active":
                return {"success": False, "error": "Proposal not active"}

            for v in prop["votes"]:
                if v["node_id"] == node_id:
                    return {"success": False, "error": "Node already voted"}

            honor = self._get_relay_honor(node_id)
            voting_weight = (
                kinetic_weight * 0.4
                + biological_weight * 0.4
                + honor * 0.2
            )

            prop["votes"].append({
                "node_id": node_id,
                "weight": voting_weight,
                "kinetic_weight": kinetic_weight,
                "biological_weight": biological_weight,
                "relay_honor": honor,
                "vote": vote,
            })

            if vote == "yes":
                prop["total_weight_yes"] += voting_weight
            else:
                prop["total_weight_no"] += voting_weight

        return {
            "success": True,
            "proposal_id": proposal_id,
            "voting_weight": round(voting_weight, 4),
            "current_yes": round(prop["total_weight_yes"], 4),
            "current_no": round(prop["total_weight_no"], 4),
        }

    def get_proposals(self) -> List[dict]:
        with self._lock:
            result = []
            for pid, prop in self.proposals.items():
                result.append({
                    "proposal_id": pid,
                    "proposal": prop["proposal"],
                    "proposer": prop["proposer"],
                    "timestamp": prop["timestamp"],
                    "status": prop["status"],
                    "total_weight_yes": round(prop["total_weight_yes"], 4),
                    "total_weight_no": round(prop["total_weight_no"], 4),
                    "vote_count": len(prop["votes"]),
                })
            return result

    def get_chain(self, limit: int = 50) -> List[dict]:
        with self._lock:
            blocks = self.chain[-limit:]
            return [b.to_dict() for b in blocks]

    def get_status(self) -> dict:
        validation = self.validate_chain()
        with self._lock:
            honor_scores = {}
            for nid, info in self.relay_honor.items():
                honor_scores[nid] = round(self._get_relay_honor(nid), 4)
            active_proposals = sum(
                1 for p in self.proposals.values() if p["status"] == "active"
            )
        return {
            "chain_height": len(self.chain),
            "integrity": validation,
            "relay_honor_scores": honor_scores,
            "active_proposals": active_proposals,
            "total_proposals": len(self.proposals),
            "node_id": self.node_id,
        }

    def prepare_sync_payload(self, since_index: int = 0) -> dict:
        with self._lock:
            blocks = [
                b.to_dict() for b in self.chain
                if b.block_index >= since_index
            ]
        return {
            "type": "silt_sync",
            "source_node": self.node_id,
            "timestamp": time.time(),
            "blocks": blocks,
            "chain_height": len(self.chain),
        }

    def receive_sync_payload(self, sync_data: dict) -> dict:
        if sync_data.get("type") != "silt_sync":
            return {"success": False, "error": "Invalid sync payload type"}

        blocks = sync_data.get("blocks", [])
        imported = 0
        with self._lock:
            existing_indices = {b.block_index for b in self.chain}
            for block_data in blocks:
                idx = block_data.get("block_index", -1)
                if idx in existing_indices:
                    continue
                imported += 1

        return {
            "success": True,
            "source_node": sync_data.get("source_node", "unknown"),
            "blocks_received": len(blocks),
            "blocks_imported": imported,
        }
