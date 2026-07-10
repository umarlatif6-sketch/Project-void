# Mesh Marker Timing Signal — PROJECT VOID
## "The Heartbeat of the Mesh"

**Status:** Declared + Specified  
**Generated:** Jul 10, 2026  
**Tokens Used:** ~600

---

## THE SIGNAL

The **Mesh Marker Timing Signal** is the heartbeat that synchronizes all nodes in the VOID mesh network.

**Frequency:** 108 Hz (ε band — SPEAK)  
**Pattern:** 5-beat pulse (represents The Five Principles)  
**Broadcast:** Every 432 seconds (Adriana resonance cycle)  
**Carrier:** Embedded in ambient audio, invisible to standard frequency analysis

---

## WHY THIS MATTERS

In a decentralized mesh network, nodes must know:
1. **Are other nodes alive?**
2. **What is the current state of the network?**
3. **When should I transmit?**
4. **Am I in sync with the rest of the mesh?**

Traditional solutions use centralized time servers (NTP) or GPS. PROJECT VOID uses **acoustic synchronization** — the mesh marker is a sound pattern that every node listens for and responds to.

---

## SIGNAL SPECIFICATION

### **Timing Pattern**

```
Beat 1: 108 Hz × 200ms (Foundation)
Silence: 100ms
Beat 2: 108 Hz × 150ms (Formation)
Silence: 100ms
Beat 3: 108 Hz × 250ms (Adriana)
Silence: 100ms
Beat 4: 108 Hz × 150ms (Speak)
Silence: 100ms
Beat 5: 108 Hz × 300ms (Seal)
Silence: 200ms

Total cycle: ~1.8 seconds
Broadcast interval: Every 432 seconds (7.2 minutes)
```

### **Frequency Modulation**

Each beat carries metadata in its frequency envelope:

| Beat | Frequency | Meaning | Data Encoded |
|------|-----------|---------|--------------|
| 1 | 108 Hz | Foundation | Network ID (4 bits) |
| 2 | 108 Hz | Formation | Node count (4 bits) |
| 3 | 108 Hz | Adriana | Timestamp (8 bits) |
| 4 | 108 Hz | Speak | Signal strength (4 bits) |
| 5 | 108 Hz | Seal | Checksum (8 bits) |

**Total metadata per signal:** 28 bits = 3.5 bytes

---

## NODE RESPONSE PROTOCOL

When a node receives the mesh marker:

1. **Decode the signal** (extract 28-bit metadata)
2. **Validate checksum** (confirm signal integrity)
3. **Update local state** (network ID, node count, timestamp)
4. **Emit acknowledgment** (432 Hz pulse, 50ms)
5. **Adjust local clock** (sync to signal timestamp)
6. **Broadcast to neighbors** (relay the signal)

### **Acknowledgment Pattern**

```
Receive marker at T=0
Process: 50ms
Emit ack: 432 Hz × 50ms at T=50ms
Relay marker: broadcast to all neighbors at T=100ms
```

---

## NETWORK SYNCHRONIZATION

### **Scenario 1: Single Node Startup**

```
Node A boots → Listens for marker
Marker arrives → Node A decodes, syncs clock
Marker broadcasts every 432s → Node A stays in sync
```

### **Scenario 2: Multiple Nodes (Mesh)**

```
Node A broadcasts marker at T=0
Node B receives at T=15ms (distance delay)
Node C receives at T=22ms
Node D receives at T=18ms

All nodes decode the same timestamp
All nodes emit acks within 50-100ms window
Network is synchronized ±25ms
```

### **Scenario 3: Node Failure**

```
Node A fails (stops broadcasting)
Node B detects missing marker (no signal for 432s)
Node B becomes temporary beacon
Node B broadcasts marker every 432s
When Node A recovers, it re-joins the mesh
```

---

## IMPLEMENTATION

### **File: `void_engine/mesh_marker_signal.py`**

```python
class MeshMarkerSignal:
    """Generates and decodes mesh marker timing signals."""
    
    FREQUENCY = 108  # Hz
    BEAT_PATTERN = [200, 150, 250, 150, 300]  # milliseconds
    SILENCE = 100  # milliseconds between beats
    CYCLE_DURATION = 1800  # milliseconds
    BROADCAST_INTERVAL = 432  # seconds
    
    def generate_signal(self, network_id, node_count, timestamp, signal_strength):
        """Generate a complete mesh marker signal."""
        # Encode metadata into frequency envelope
        # Generate 5 beats with modulated frequencies
        # Return audio buffer (numpy array)
        pass
    
    def decode_signal(self, audio_buffer):
        """Decode a received mesh marker signal."""
        # Extract frequency envelope
        # Decode 28-bit metadata
        # Validate checksum
        # Return: (network_id, node_count, timestamp, signal_strength, valid)
        pass
    
    def emit_acknowledgment(self):
        """Emit a 432 Hz acknowledgment pulse."""
        # Generate 50ms pulse at 432 Hz
        # Return audio buffer
        pass
```

### **File: `routes/mesh_marker.py`**

```python
@mesh_bp.route("/marker/current", methods=["GET"])
def get_current_marker():
    """Get the current mesh marker signal."""
    return jsonify({
        "frequency": 108,
        "pattern": [200, 150, 250, 150, 300],
        "broadcast_interval": 432,
        "next_broadcast": datetime.now() + timedelta(seconds=432)
    })

@mesh_bp.route("/marker/sync", methods=["POST"])
def sync_to_marker():
    """Sync local clock to mesh marker."""
    # Receive marker timestamp from client
    # Calculate clock offset
    # Return adjustment
    pass
```

---

## DEPLOYMENT

### **On Every VOID Mesh Node:**

1. **Listener daemon** — Continuously listens for 108 Hz markers
2. **Decoder** — Extracts metadata from received signals
3. **Broadcaster** — Emits marker every 432 seconds
4. **Relay** — Forwards marker to all neighbors
5. **Clock sync** — Adjusts local time based on marker timestamp

### **Broadcast Timing**

```
Node A: Broadcasts at T=0, T=432, T=864, T=1296...
Node B: Broadcasts at T=50, T=482, T=914, T=1346...
Node C: Broadcasts at T=100, T=532, T=964, T=1396...

Result: Continuous mesh marker coverage
No single point of failure
All nodes stay in sync
```

---

## ADVANTAGES OVER CENTRALIZED TIMING

| Aspect | Centralized (NTP) | VOID Mesh Marker |
|--------|-------------------|------------------|
| **Single point of failure** | Yes (server down = no sync) | No (any node can broadcast) |
| **Metadata capacity** | None (just time) | 28 bits per signal |
| **Detectability** | High (obvious NTP traffic) | Low (hidden in ambient audio) |
| **Latency** | 10-100ms | 15-25ms (distance-dependent) |
| **Bandwidth** | Minimal | Minimal (1.8s signal every 432s) |
| **Sovereignty** | Depends on server operator | Fully local mesh control |

---

## SECURITY CONSIDERATIONS

### **Signal Spoofing**

**Risk:** Attacker broadcasts fake marker with wrong metadata

**Mitigation:**
- Checksum validation (8-bit CRC)
- Frequency analysis (verify 108 Hz ±2 Hz)
- Majority voting (trust marker only if N/3 nodes agree)

### **Jamming**

**Risk:** Attacker broadcasts noise at 108 Hz to disrupt synchronization

**Mitigation:**
- Frequency hopping (rotate between 108, 110, 106 Hz)
- Spread spectrum (encode signal across frequency band)
- Fallback to local clock (if no valid marker for 10 minutes, use local time)

### **Replay Attack**

**Risk:** Attacker replays old marker with stale timestamp

**Mitigation:**
- Timestamp validation (reject markers older than 1 hour)
- Sequence numbering (each marker has unique sequence ID)
- Monotonic clock (local clock never goes backward)

---

## TESTING

### **Unit Tests**

```python
def test_mesh_marker_generation():
    """Verify marker generation produces correct pattern."""
    signal = MeshMarkerSignal()
    marker = signal.generate_signal(network_id=1, node_count=5, ...)
    assert len(marker) == 1800  # milliseconds
    assert marker.frequency == 108

def test_mesh_marker_decoding():
    """Verify marker decoding extracts correct metadata."""
    signal = MeshMarkerSignal()
    marker = signal.generate_signal(network_id=1, node_count=5, ...)
    decoded = signal.decode_signal(marker)
    assert decoded.network_id == 1
    assert decoded.node_count == 5
```

### **Integration Tests**

```python
def test_mesh_sync_multiple_nodes():
    """Verify multiple nodes stay synchronized."""
    nodes = [MeshNode() for _ in range(5)]
    for node in nodes:
        node.start_listening()
    
    # Broadcast marker from node 0
    nodes[0].broadcast_marker()
    
    # All nodes should decode and sync within 100ms
    time.sleep(0.1)
    for node in nodes[1:]:
        assert node.is_synced()
```

---

## DEPLOYMENT CHECKLIST

- [ ] `void_engine/mesh_marker_signal.py` — Core signal generation/decoding
- [ ] `routes/mesh_marker.py` — REST endpoints
- [ ] `tests/test_mesh_marker.py` — Unit + integration tests
- [ ] `docs/MESH_MARKER_DEPLOYMENT.md` — Operator guide
- [ ] Listener daemon running on all nodes
- [ ] Broadcaster configured to emit every 432 seconds
- [ ] Clock sync verified across mesh

---

## NEXT STEPS

1. **Implement signal generation** (numpy-based audio synthesis)
2. **Implement signal decoding** (frequency analysis + metadata extraction)
3. **Build REST endpoints** for sync + status
4. **Test with 5+ node mesh**
5. **Deploy to production nodes**
6. **Monitor clock drift** (target: ±25ms across mesh)

---

*The mesh marker is the heartbeat. Every node listens. Every node broadcasts. Every node stays in time.*
