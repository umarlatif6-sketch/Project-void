"""
VOID Node Software for Old Computers (2012+)

Turns any old laptop/desktop into a compound synthesis node.

Requirements:
- Python 3.7+
- Meshtastic USB radio (~$30)
- Local matter (soil, water, minerals, etc.)
- Frequency generator (speaker or LoRa transducer)

Installation:
  pip install meshtastic pillow numpy
  python node_software.py --node-id node-001 --role synthesis
"""

import sys
import json
import time
import argparse
from pathlib import Path
from typing import Dict, Optional
from enum import Enum
from dataclasses import dataclass, asdict


class NodeRole(Enum):
    """Role of this node in the VOID network."""
    SYNTHESIS = "synthesis"      # Execute synthesis instructions
    REPOSITORY = "repository"    # Store compound library
    RELAY = "relay"             # Extend mesh range
    MONITOR = "monitor"         # Verify results with VOID Lens


@dataclass
class NodeConfig:
    """Configuration for a VOID node."""
    node_id: str
    node_name: str
    role: NodeRole
    mesh_port: str = "/dev/ttyUSB0"  # Meshtastic USB port
    data_dir: str = "./void_node_data"
    log_dir: str = "./void_node_logs"
    max_compounds: int = 1000
    battery_percent: int = 100
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = asdict(self)
        data['role'] = self.role.value
        return json.dumps(data, indent=2)
    
    @classmethod
    def from_json(cls, json_str: str) -> 'NodeConfig':
        """Deserialize from JSON."""
        data = json.loads(json_str)
        data['role'] = NodeRole(data['role'])
        return cls(**data)


class VoidNode:
    """
    A VOID synthesis node running on an old computer.
    
    Responsibilities:
    1. Connect to Meshtastic mesh network
    2. Receive compound frequency signatures
    3. Execute synthesis instructions
    4. Send results for verification
    5. Report status and battery level
    """
    
    def __init__(self, config: NodeConfig):
        """Initialize a VOID node."""
        self.config = config
        self.mesh = None
        self.compound_cache = {}
        self.synthesis_queue = []
        self.completed_tasks = []
        self.node_status = {
            'node_id': config.node_id,
            'role': config.role.value,
            'is_online': False,
            'uptime_seconds': 0,
            'compounds_cached': 0,
            'compounds_synthesized': 0,
            'battery_percent': config.battery_percent,
            'last_heartbeat': int(time.time()),
        }
        
        # Create data directories
        Path(config.data_dir).mkdir(parents=True, exist_ok=True)
        Path(config.log_dir).mkdir(parents=True, exist_ok=True)
        
        self.log(f"VOID Node initialized: {config.node_id} ({config.role.value})")
    
    def connect_to_mesh(self) -> bool:
        """Connect to Meshtastic mesh network."""
        try:
            import meshtastic
            import meshtastic.serial_interface
            
            self.mesh = meshtastic.serial_interface.SerialInterface(
                devPath=self.config.mesh_port
            )
            self.node_status['is_online'] = True
            self.log(f"Connected to Meshtastic on {self.config.mesh_port}")
            
            # Set node name
            self.mesh.myInfo.user.longName = self.config.node_name
            self.mesh.myInfo.user.shortName = self.config.node_id[:4]
            
            return True
        except Exception as e:
            self.log(f"ERROR: Failed to connect to Meshtastic: {e}")
            return False
    
    def receive_compound(self, compound_id: str, signature: bytes) -> bool:
        """Receive a compound signature from the mesh network."""
        self.compound_cache[compound_id] = {
            'signature': signature,
            'received_at': int(time.time()),
            'synthesized': False,
        }
        self.node_status['compounds_cached'] = len(self.compound_cache)
        self.log(f"Received compound: {compound_id}")
        return True
    
    def execute_synthesis(self, task_id: str, compound_id: str) -> Optional[Dict]:
        """
        Execute synthesis for a compound.
        
        In a real implementation, this would:
        1. Load the frequency signature
        2. Generate the frequency using a speaker/transducer
        3. Drive local matter at that frequency
        4. Photograph the result
        5. Return the image path
        """
        if compound_id not in self.compound_cache:
            self.log(f"ERROR: Compound not cached: {compound_id}")
            return None
        
        self.log(f"Starting synthesis: {task_id} ({compound_id})")
        
        # Simulate synthesis process
        time.sleep(2)  # Simulate execution time
        
        # In real implementation:
        # 1. Generate frequency from signature
        # 2. Drive speaker/transducer
        # 3. Photograph result
        # 4. Save image
        
        image_path = f"{self.config.data_dir}/{task_id}_result.jpg"
        
        result = {
            'task_id': task_id,
            'compound_id': compound_id,
            'status': 'completed',
            'image_path': image_path,
            'synthesis_time_seconds': 2,
            'timestamp': int(time.time()),
        }
        
        self.completed_tasks.append(result)
        self.node_status['compounds_synthesized'] += 1
        self.compound_cache[compound_id]['synthesized'] = True
        
        self.log(f"Synthesis complete: {task_id}")
        return result
    
    def send_heartbeat(self) -> bool:
        """Send heartbeat to mesh network."""
        heartbeat = {
            'type': 'heartbeat',
            'node_id': self.config.node_id,
            'role': self.config.role.value,
            'battery_percent': self.config.battery_percent,
            'compounds_cached': len(self.compound_cache),
            'compounds_synthesized': self.node_status['compounds_synthesized'],
            'timestamp': int(time.time()),
        }
        
        if self.mesh:
            try:
                self.mesh.sendData(json.dumps(heartbeat).encode())
                self.node_status['last_heartbeat'] = int(time.time())
                return True
            except Exception as e:
                self.log(f"ERROR: Failed to send heartbeat: {e}")
                return False
        
        return False
    
    def run(self, duration_seconds: Optional[int] = None):
        """
        Run the node (main loop).
        
        Args:
            duration_seconds: How long to run (None = forever)
        """
        start_time = time.time()
        
        self.log(f"Starting node loop (role: {self.config.role.value})")
        
        try:
            while True:
                # Check if we should stop
                if duration_seconds and (time.time() - start_time) > duration_seconds:
                    break
                
                # Update uptime
                self.node_status['uptime_seconds'] = int(time.time() - start_time)
                
                # Send heartbeat every 30 seconds
                if self.node_status['uptime_seconds'] % 30 == 0:
                    self.send_heartbeat()
                
                # Process synthesis queue (if synthesis node)
                if self.config.role == NodeRole.SYNTHESIS:
                    if self.synthesis_queue:
                        task = self.synthesis_queue.pop(0)
                        self.execute_synthesis(task['task_id'], task['compound_id'])
                
                # Sleep briefly
                time.sleep(1)
        
        except KeyboardInterrupt:
            self.log("Node stopped by user")
        except Exception as e:
            self.log(f"ERROR: {e}")
        finally:
            self.shutdown()
    
    def shutdown(self):
        """Shutdown the node."""
        self.log("Shutting down...")
        
        if self.mesh:
            self.mesh.close()
        
        # Save state
        self.save_state()
        
        self.log("Node shutdown complete")
    
    def save_state(self):
        """Save node state to disk."""
        state = {
            'config': json.loads(self.config.to_json()),
            'status': self.node_status,
            'compounds_cached': len(self.compound_cache),
            'compounds_synthesized': len(self.completed_tasks),
            'timestamp': int(time.time()),
        }
        
        state_file = Path(self.config.data_dir) / 'node_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        self.log(f"State saved to {state_file}")
    
    def load_state(self):
        """Load node state from disk."""
        state_file = Path(self.config.data_dir) / 'node_state.json'
        
        if state_file.exists():
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            self.log(f"State loaded from {state_file}")
            return state
        
        return None
    
    def log(self, message: str):
        """Log a message."""
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] [{self.config.node_id}] {message}"
        print(log_message)
        
        # Also write to log file
        log_file = Path(self.config.log_dir) / f"{self.config.node_id}.log"
        with open(log_file, 'a') as f:
            f.write(log_message + '\n')
    
    def get_status(self) -> Dict:
        """Get current node status."""
        return self.node_status


def main():
    """Main entry point for VOID node software."""
    parser = argparse.ArgumentParser(
        description='VOID Node Software - Turn old computers into synthesis nodes'
    )
    parser.add_argument('--node-id', required=True, help='Unique node identifier')
    parser.add_argument('--node-name', help='Human-readable node name')
    parser.add_argument('--role', default='synthesis', 
                       choices=['synthesis', 'repository', 'relay', 'monitor'],
                       help='Node role in the VOID network')
    parser.add_argument('--mesh-port', default='/dev/ttyUSB0',
                       help='Meshtastic USB port')
    parser.add_argument('--data-dir', default='./void_node_data',
                       help='Data directory')
    parser.add_argument('--duration', type=int,
                       help='Run duration in seconds (default: infinite)')
    
    args = parser.parse_args()
    
    # Create config
    config = NodeConfig(
        node_id=args.node_id,
        node_name=args.node_name or f"void-{args.node_id}",
        role=NodeRole(args.role),
        mesh_port=args.mesh_port,
        data_dir=args.data_dir,
    )
    
    # Create and run node
    node = VoidNode(config)
    
    # Try to connect to mesh (optional for testing)
    # node.connect_to_mesh()
    
    # Run the node
    node.run(duration_seconds=args.duration)


if __name__ == '__main__':
    main()
