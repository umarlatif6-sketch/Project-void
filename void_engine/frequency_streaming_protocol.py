"""
Frequency-Streaming Protocol for Project VOID

Like Colibri streams model weights from SSD to RAM, this streams compound
frequency signatures from a central repository to distributed nodes over
Meshtastic LoRa mesh networks.

Protocol: VOID-FSP (VOID Frequency Streaming Protocol)
Transport: Meshtastic LoRa (long-range, low-power, mesh-native)
Payload: 8-byte substrate-agnostic instructions
"""

import hashlib
import time
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from enum import Enum


class PacketType(Enum):
    """VOID-FSP packet types."""
    MANIFEST = 0x01      # List of available compounds
    SIGNATURE = 0x02     # Frequency signature (multi-packet)
    INSTRUCTION = 0x03   # Single instruction
    VERIFY = 0x04        # Verification request
    ACK = 0x05           # Acknowledgment
    ERROR = 0x06         # Error/retry
    HEARTBEAT = 0x07     # Keep-alive


@dataclass
class VoidFSPPacket:
    """A single VOID-FSP packet for mesh transmission."""
    packet_type: PacketType
    sequence_number: int        # For reassembly
    total_packets: int          # For multi-packet signatures
    compound_id: str            # Which compound
    payload: bytes              # 8-255 bytes
    checksum: int               # CRC32 for verification
    timestamp: int              # Unix timestamp
    
    def to_bytes(self) -> bytes:
        """Serialize to bytes for LoRa transmission."""
        packet = bytearray()
        packet.append(self.packet_type.value)
        packet.extend(self.sequence_number.to_bytes(2, 'big'))
        packet.extend(self.total_packets.to_bytes(2, 'big'))
        packet.extend(self.compound_id.encode()[:16])  # Max 16 bytes
        packet.extend(len(self.payload).to_bytes(1, 'big'))
        packet.extend(self.payload)
        packet.extend(self.checksum.to_bytes(4, 'big'))
        packet.extend(self.timestamp.to_bytes(4, 'big'))
        return bytes(packet)
    
    @classmethod
    def from_bytes(cls, data: bytes) -> 'VoidFSPPacket':
        """Deserialize from bytes."""
        offset = 0
        packet_type = PacketType(data[offset])
        offset += 1
        sequence_number = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2
        total_packets = int.from_bytes(data[offset:offset+2], 'big')
        offset += 2
        compound_id = data[offset:offset+16].decode().rstrip('\x00')
        offset += 16
        payload_len = data[offset]
        offset += 1
        payload = data[offset:offset+payload_len]
        offset += payload_len
        checksum = int.from_bytes(data[offset:offset+4], 'big')
        offset += 4
        timestamp = int.from_bytes(data[offset:offset+4], 'big')
        
        return cls(
            packet_type=packet_type,
            sequence_number=sequence_number,
            total_packets=total_packets,
            compound_id=compound_id,
            payload=payload,
            checksum=checksum,
            timestamp=timestamp
        )


class FrequencyStreamingProtocol:
    """
    VOID-FSP: Frequency Streaming Protocol
    
    Enables decentralized compound synthesis by streaming frequency signatures
    over Meshtastic LoRa mesh networks to old computers acting as synthesis nodes.
    
    Key principle: Like Colibri streams model weights on-demand, VOID-FSP
    streams compound signatures on-demand to any node that requests them.
    """
    
    def __init__(self, node_id: str, mesh_interface=None):
        """
        Initialize a VOID-FSP node.
        
        Args:
            node_id: Unique identifier for this node (e.g., "node-2012-laptop-001")
            mesh_interface: Meshtastic interface (optional, for testing)
        """
        self.node_id = node_id
        self.mesh = mesh_interface
        self.compound_cache = {}  # Local cache of signatures
        self.pending_packets = {}  # Reassembly buffer for multi-packet signatures
        self.statistics = {
            'packets_sent': 0,
            'packets_received': 0,
            'packets_lost': 0,
            'compounds_synthesized': 0,
            'total_bytes_transmitted': 0,
        }
    
    def request_compound(self, compound_id: str) -> Optional[bytes]:
        """
        Request a compound signature from the mesh network.
        
        Returns the full signature once all packets are received.
        """
        # Check local cache first
        if compound_id in self.compound_cache:
            return self.compound_cache[compound_id]
        
        # Send request packet
        request = VoidFSPPacket(
            packet_type=PacketType.MANIFEST,
            sequence_number=0,
            total_packets=1,
            compound_id=compound_id,
            payload=b"REQUEST",
            checksum=self._calculate_checksum(b"REQUEST"),
            timestamp=int(time.time())
        )
        
        self._send_packet(request)
        
        # Wait for response (in real implementation, this would be async)
        # For now, return None (would be filled by receive_packet)
        return None
    
    def stream_compound(self, compound_id: str, signature_bytes: bytes) -> List[VoidFSPPacket]:
        """
        Stream a compound signature to the mesh network.
        
        Breaks large signatures into 255-byte chunks for LoRa transmission.
        """
        packets = []
        chunk_size = 255
        total_chunks = (len(signature_bytes) + chunk_size - 1) // chunk_size
        
        for i in range(total_chunks):
            chunk = signature_bytes[i*chunk_size:(i+1)*chunk_size]
            packet = VoidFSPPacket(
                packet_type=PacketType.SIGNATURE,
                sequence_number=i,
                total_packets=total_chunks,
                compound_id=compound_id,
                payload=chunk,
                checksum=self._calculate_checksum(chunk),
                timestamp=int(time.time())
            )
            packets.append(packet)
            self._send_packet(packet)
        
        return packets
    
    def receive_packet(self, packet: VoidFSPPacket) -> Optional[bytes]:
        """
        Receive and process a packet from the mesh network.
        
        Returns complete signature when all packets of a multi-packet
        transmission are received.
        """
        self.statistics['packets_received'] += 1
        
        # Verify checksum
        if not self._verify_checksum(packet):
            self.statistics['packets_lost'] += 1
            return None
        
        # Handle different packet types
        if packet.packet_type == PacketType.SIGNATURE:
            # Multi-packet reassembly
            if packet.compound_id not in self.pending_packets:
                self.pending_packets[packet.compound_id] = {}
            
            self.pending_packets[packet.compound_id][packet.sequence_number] = packet.payload
            
            # Check if all packets received
            if len(self.pending_packets[packet.compound_id]) == packet.total_packets:
                # Reassemble
                full_signature = b''
                for i in range(packet.total_packets):
                    full_signature += self.pending_packets[packet.compound_id][i]
                
                # Cache it
                self.compound_cache[packet.compound_id] = full_signature
                
                # Clean up
                del self.pending_packets[packet.compound_id]
                
                # Send ACK
                ack = VoidFSPPacket(
                    packet_type=PacketType.ACK,
                    sequence_number=0,
                    total_packets=1,
                    compound_id=packet.compound_id,
                    payload=b"OK",
                    checksum=0,
                    timestamp=int(time.time())
                )
                self._send_packet(ack)
                
                return full_signature
        
        return None
    
    def _send_packet(self, packet: VoidFSPPacket):
        """Send a packet over the mesh network."""
        packet_bytes = packet.to_bytes()
        self.statistics['packets_sent'] += 1
        self.statistics['total_bytes_transmitted'] += len(packet_bytes)
        
        if self.mesh:
            # Real Meshtastic transmission
            self.mesh.sendData(packet_bytes, wantAck=True)
        else:
            # Simulation mode
            print(f"[{self.node_id}] Sent {len(packet_bytes)} bytes: {packet.compound_id}")
    
    def _calculate_checksum(self, data: bytes) -> int:
        """Calculate CRC32 checksum."""
        return int(hashlib.md5(data).hexdigest()[:8], 16)
    
    def _verify_checksum(self, packet: VoidFSPPacket) -> bool:
        """Verify packet checksum."""
        expected = self._calculate_checksum(packet.payload)
        return expected == packet.checksum
    
    def get_statistics(self) -> Dict:
        """Get protocol statistics."""
        return {
            **self.statistics,
            'node_id': self.node_id,
            'cached_compounds': len(self.compound_cache),
            'pending_reassemblies': len(self.pending_packets),
            'efficiency': (self.statistics['packets_received'] - self.statistics['packets_lost']) / max(1, self.statistics['packets_received']),
        }


class MeshNetworkSimulator:
    """
    Simulate a mesh network of VOID-FSP nodes for testing.
    
    Demonstrates how old computers (2012+ laptops) can form a decentralized
    network for compound synthesis.
    """
    
    def __init__(self):
        self.nodes: Dict[str, FrequencyStreamingProtocol] = {}
        self.compound_repository = {}  # Central repository
    
    def add_node(self, node_id: str) -> FrequencyStreamingProtocol:
        """Add a node to the mesh network."""
        node = FrequencyStreamingProtocol(node_id)
        self.nodes[node_id] = node
        return node
    
    def register_compound(self, compound_id: str, signature: bytes):
        """Register a compound in the central repository."""
        self.compound_repository[compound_id] = signature
    
    def broadcast_compound(self, compound_id: str):
        """Broadcast a compound to all nodes in the network."""
        if compound_id not in self.compound_repository:
            return
        
        signature = self.compound_repository[compound_id]
        
        # Simulate broadcasting to all nodes
        for node in self.nodes.values():
            # In real implementation, this would go through Meshtastic
            node.compound_cache[compound_id] = signature
    
    def get_network_status(self) -> Dict:
        """Get status of all nodes in the network."""
        return {
            'total_nodes': len(self.nodes),
            'nodes': {
                node_id: node.get_statistics()
                for node_id, node in self.nodes.items()
            },
            'total_compounds': len(self.compound_repository),
        }


# Example usage
if __name__ == "__main__":
    # Create a mesh network simulator
    network = MeshNetworkSimulator()
    
    # Add nodes (simulating old computers)
    nodes = [
        network.add_node("node-2012-laptop-001"),
        network.add_node("node-2013-desktop-002"),
        network.add_node("node-2014-laptop-003"),
    ]
    
    # Register a compound
    compound_id = "void-carbon-lattice-001"
    signature = b"432Hz_1x2x3x4_harmonics_stable_94percent"
    network.register_compound(compound_id, signature)
    
    # Broadcast to all nodes
    network.broadcast_compound(compound_id)
    
    # Check network status
    status = network.get_network_status()
    print(f"Network Status:")
    print(f"  Total nodes: {status['total_nodes']}")
    print(f"  Total compounds: {status['total_compounds']}")
    print(f"  Nodes: {list(status['nodes'].keys())}")
    
    # Each node now has the compound cached
    for node_id, node in network.nodes.items():
        print(f"  {node_id}: {len(node.compound_cache)} compounds cached")
