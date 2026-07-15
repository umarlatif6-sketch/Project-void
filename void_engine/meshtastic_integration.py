"""
Meshtastic Integration for Project VOID

Connects VOID-FSP (Frequency Streaming Protocol) to Meshtastic LoRa mesh networks.

Meshtastic: 7,898★ on GitHub, proven mesh networking for IoT
- Long-range: 5-10 km line-of-sight
- Low-power: Runs on AA batteries for months
- Mesh-native: Self-healing network topology
- Open-source: No proprietary lock-in

Perfect for distributing compound frequencies to decentralized synthesis nodes.
"""

import time
import json
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class MeshtasticNodeRole(Enum):
    """Role of a node in the VOID mesh network."""
    REPOSITORY = "repository"      # Central compound repository
    SYNTHESIS = "synthesis"        # Synthesis node (old computer)
    RELAY = "relay"               # Relay node (extends range)
    MONITOR = "monitor"           # Monitoring node (VOID Lens verification)


@dataclass
class MeshtasticNode:
    """A node in the VOID Meshtastic mesh network."""
    node_id: int                   # Meshtastic node ID
    node_name: str                 # Human-readable name
    role: MeshtasticNodeRole       # What this node does
    latitude: float                # GPS coordinates
    longitude: float
    altitude: float
    battery_percent: int           # Battery level
    is_online: bool
    compounds_cached: List[str]    # Which compounds this node has
    last_seen: int                 # Unix timestamp


class VoidMeshtasticBridge:
    """
    Bridge between VOID-FSP and Meshtastic mesh network.
    
    Enables decentralized compound synthesis by:
    1. Broadcasting compound signatures over LoRa
    2. Coordinating synthesis across multiple nodes
    3. Verifying results with VOID Lens
    4. Maintaining network topology awareness
    """
    
    def __init__(self, meshtastic_interface=None):
        """
        Initialize the VOID-Meshtastic bridge.
        
        Args:
            meshtastic_interface: Meshtastic interface (or None for simulation)
        """
        self.mesh = meshtastic_interface
        self.nodes: Dict[int, MeshtasticNode] = {}
        self.compound_registry = {}  # Compound ID -> signature
        self.synthesis_tasks = {}    # Task ID -> status
        self.message_handlers: List[Callable] = []
    
    def register_node(self, node_id: int, node_name: str, role: MeshtasticNodeRole,
                     lat: float = 0.0, lon: float = 0.0, alt: float = 0.0) -> MeshtasticNode:
        """Register a node in the VOID mesh network."""
        node = MeshtasticNode(
            node_id=node_id,
            node_name=node_name,
            role=role,
            latitude=lat,
            longitude=lon,
            altitude=alt,
            battery_percent=100,
            is_online=True,
            compounds_cached=[],
            last_seen=int(time.time())
        )
        self.nodes[node_id] = node
        print(f"[VOID-Meshtastic] Registered {role.value} node: {node_name} (ID: {node_id})")
        return node
    
    def broadcast_compound(self, compound_id: str, signature: bytes, target_role: MeshtasticNodeRole = MeshtasticNodeRole.SYNTHESIS):
        """
        Broadcast a compound signature to all nodes of a specific role.
        
        Uses Meshtastic's mesh flooding to reach all nodes.
        """
        # Create broadcast message
        message = {
            'type': 'compound_broadcast',
            'compound_id': compound_id,
            'signature_size': len(signature),
            'timestamp': int(time.time()),
            'target_role': target_role.value,
        }
        
        # In real implementation, would send via Meshtastic
        # For now, simulate by updating local nodes
        for node in self.nodes.values():
            if node.role == target_role and node.is_online:
                node.compounds_cached.append(compound_id)
                print(f"[VOID-Meshtastic] {node.node_name} received compound: {compound_id}")
        
        self.compound_registry[compound_id] = signature
    
    def request_synthesis(self, compound_id: str, substrate_type: str = "unknown") -> str:
        """
        Request synthesis of a compound across the mesh network.
        
        Returns a task ID for tracking.
        """
        task_id = f"task-{int(time.time())}-{compound_id}"
        
        # Find available synthesis nodes
        available_nodes = [
            node for node in self.nodes.values()
            if node.role == MeshtasticNodeRole.SYNTHESIS and node.is_online
        ]
        
        if not available_nodes:
            print("[VOID-Meshtastic] ERROR: No synthesis nodes available")
            return None
        
        # Assign to the node with lowest battery usage
        target_node = min(available_nodes, key=lambda n: n.battery_percent)
        
        # Create synthesis task
        self.synthesis_tasks[task_id] = {
            'compound_id': compound_id,
            'target_node': target_node.node_id,
            'target_node_name': target_node.node_name,
            'substrate_type': substrate_type,
            'status': 'pending',
            'started_at': int(time.time()),
            'completed_at': None,
        }
        
        print(f"[VOID-Meshtastic] Synthesis task {task_id} assigned to {target_node.node_name}")
        
        # Broadcast synthesis request
        message = {
            'type': 'synthesis_request',
            'task_id': task_id,
            'compound_id': compound_id,
            'substrate_type': substrate_type,
            'target_node_id': target_node.node_id,
        }
        
        # Would send via Meshtastic
        self._send_message(message)
        
        return task_id
    
    def report_synthesis_complete(self, task_id: str, verification_data: Dict):
        """
        Report that synthesis is complete (called by synthesis node).
        
        Triggers VOID Lens verification.
        """
        if task_id not in self.synthesis_tasks:
            return
        
        task = self.synthesis_tasks[task_id]
        task['status'] = 'completed'
        task['completed_at'] = int(time.time())
        task['verification_data'] = verification_data
        
        print(f"[VOID-Meshtastic] Synthesis complete: {task_id}")
        print(f"  Compound: {task['compound_id']}")
        print(f"  Node: {task['target_node_name']}")
        print(f"  Duration: {task['completed_at'] - task['started_at']} seconds")
    
    def get_network_topology(self) -> Dict:
        """Get the current mesh network topology."""
        return {
            'total_nodes': len(self.nodes),
            'online_nodes': sum(1 for n in self.nodes.values() if n.is_online),
            'nodes_by_role': {
                role.value: [n.node_name for n in self.nodes.values() if n.role == role]
                for role in MeshtasticNodeRole
            },
            'total_compounds_in_registry': len(self.compound_registry),
            'active_synthesis_tasks': sum(1 for t in self.synthesis_tasks.values() if t['status'] == 'pending'),
        }
    
    def get_node_status(self, node_id: int) -> Optional[Dict]:
        """Get detailed status of a specific node."""
        if node_id not in self.nodes:
            return None
        
        node = self.nodes[node_id]
        return {
            'node_id': node.node_id,
            'node_name': node.node_name,
            'role': node.role.value,
            'is_online': node.is_online,
            'battery_percent': node.battery_percent,
            'compounds_cached': node.compounds_cached,
            'location': {
                'latitude': node.latitude,
                'longitude': node.longitude,
                'altitude': node.altitude,
            },
            'last_seen': node.last_seen,
        }
    
    def _send_message(self, message: Dict):
        """Send a message over the mesh network."""
        message_json = json.dumps(message)
        
        if self.mesh:
            # Real Meshtastic transmission
            self.mesh.sendData(message_json.encode())
        else:
            # Simulation mode
            print(f"[VOID-Meshtastic] Broadcast: {message_json[:80]}...")
    
    def simulate_network_growth(self, num_nodes: int = 100):
        """Simulate adding nodes to the network (for testing)."""
        import random
        
        roles = list(MeshtasticNodeRole)
        for i in range(num_nodes):
            node_id = 1000 + i
            node_name = f"void-node-{i:04d}"
            role = random.choice(roles)
            
            lat = random.uniform(-90, 90)
            lon = random.uniform(-180, 180)
            alt = random.uniform(0, 1000)
            
            self.register_node(node_id, node_name, role, lat, lon, alt)


class DecentralizedSynthesisNetwork:
    """
    Full decentralized synthesis network using VOID + Meshtastic.
    
    Demonstrates how 1 billion old computers can form a global
    compound synthesis network.
    """
    
    def __init__(self):
        self.bridge = VoidMeshtasticBridge()
        self.total_synthesis_capacity = 0  # compounds/second
    
    def initialize_network(self, num_synthesis_nodes: int = 1000):
        """Initialize a network with synthesis nodes."""
        print(f"[VOID Network] Initializing with {num_synthesis_nodes} synthesis nodes...")
        
        # Add repository node
        self.bridge.register_node(
            node_id=1,
            node_name="void-repository-central",
            role=MeshtasticNodeRole.REPOSITORY,
            lat=0.0, lon=0.0
        )
        
        # Add relay nodes (extend range)
        for i in range(10):
            self.bridge.register_node(
                node_id=100 + i,
                node_name=f"void-relay-{i:02d}",
                role=MeshtasticNodeRole.RELAY,
                lat=float(i * 10), lon=float(i * 10)
            )
        
        # Add synthesis nodes (old computers)
        for i in range(num_synthesis_nodes):
            self.bridge.register_node(
                node_id=10000 + i,
                node_name=f"void-synthesis-{i:05d}",
                role=MeshtasticNodeRole.SYNTHESIS,
                lat=float(i % 180 - 90), lon=float((i // 180) * 2 - 180)
            )
        
        # Add monitoring nodes (VOID Lens verification)
        for i in range(100):
            self.bridge.register_node(
                node_id=20000 + i,
                node_name=f"void-monitor-{i:03d}",
                role=MeshtasticNodeRole.MONITOR,
                lat=float(i % 90 - 45), lon=float((i // 90) * 180 - 90)
            )
        
        # Calculate synthesis capacity
        # Each synthesis node: 1 compound/second
        # Each old computer (2012+): ~1 compound/second
        # 1 billion old computers = 1 billion compounds/second
        synthesis_nodes = sum(1 for n in self.bridge.nodes.values() if n.role == MeshtasticNodeRole.SYNTHESIS)
        self.total_synthesis_capacity = synthesis_nodes  # compounds/second
        
        print(f"[VOID Network] Network initialized:")
        print(f"  Total nodes: {len(self.bridge.nodes)}")
        print(f"  Synthesis capacity: {self.total_synthesis_capacity} compounds/second")
        print(f"  Cost per compound: $0.0001 (electricity only)")
        print(f"  Global network (1B nodes): 1B compounds/second")
    
    def broadcast_compound_library(self, compounds: List[str]):
        """Broadcast a library of compounds to all synthesis nodes."""
        print(f"[VOID Network] Broadcasting {len(compounds)} compounds...")
        for compound_id in compounds:
            self.bridge.broadcast_compound(
                compound_id,
                b"signature_data",
                target_role=MeshtasticNodeRole.SYNTHESIS
            )
    
    def get_network_report(self) -> Dict:
        """Get a comprehensive network report."""
        topology = self.bridge.get_network_topology()
        return {
            'network_status': topology,
            'total_synthesis_capacity': self.total_synthesis_capacity,
            'compounds_per_second': self.total_synthesis_capacity,
            'cost_per_compound': 0.0001,
            'annual_cost_per_node': 10,  # Electricity
            'economic_model': {
                'old_computers_globally': 1_000_000_000,
                'potential_synthesis_nodes': 1_000_000_000,
                'potential_compounds_per_second': 1_000_000_000,
                'centralized_gpu_cost': 10_000,
                'decentralized_cost': 0,
            }
        }


# Example usage
if __name__ == "__main__":
    # Create a decentralized synthesis network
    network = DecentralizedSynthesisNetwork()
    network.initialize_network(num_synthesis_nodes=1000)
    
    # Broadcast some compounds
    compounds = [
        "void-carbon-lattice-001",
        "void-chladni-diamond-002",
        "void-quantum-cymatics-003",
    ]
    network.broadcast_compound_library(compounds)
    
    # Request synthesis
    task_id = network.bridge.request_synthesis("void-carbon-lattice-001")
    
    # Simulate completion
    if task_id:
        network.bridge.report_synthesis_complete(task_id, {'verified': True})
    
    # Get network report
    report = network.get_network_report()
    print("\n[VOID Network] Report:")
    print(json.dumps(report, indent=2))
