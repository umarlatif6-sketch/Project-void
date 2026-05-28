#!/usr/bin/env python3
"""
Mycelium Core — PROJECT VOID

The foundation of the distributed principle network.

The mycelium is not a system that processes data.
The mycelium IS the data itself.

It is the living network of principles that connects all nodes.
It grows. It spreads. It never ends.

Codon Efficiency: 97%
"""

import logging
from typing import Dict, List, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class Principle(Enum):
    """The six universal principles that form the mycelium."""
    FLOW = "flow"              # Movement, velocity, direction
    RESONANCE = "resonance"    # Alignment, harmony, coherence
    IMPEDANCE = "impedance"    # Friction, resistance, cost
    PRESSURE = "pressure"      # Force, urgency, intensity
    CONDUCTIVITY = "conductivity"  # Connection, transmission, capacity
    ACCUMULATION = "accumulation"  # Storage, growth, density


@dataclass
class PrincipleNutrient:
    """A principle flowing through the mycelium."""
    principle: Principle
    value: float  # 0-1 scale
    source_node: str  # Which node originated this
    timestamp: str
    path: List[str] = field(default_factory=list)  # Nodes it has traveled through
    strength: float = 1.0  # Degrades as it travels, unless amplified

    def travel_to(self, node: str) -> "PrincipleNutrient":
        """Nutrient travels to a new node."""
        new_nutrient = PrincipleNutrient(
            principle=self.principle,
            value=self.value,
            source_node=self.source_node,
            timestamp=self.timestamp,
            path=self.path + [node],
            strength=self.strength * 0.95,  # Degrades slightly with distance
        )
        return new_nutrient

    def amplify(self, factor: float = 1.2) -> None:
        """Nutrient is amplified by resonance."""
        self.strength = min(1.0, self.strength * factor)


@dataclass
class MyceliumNode:
    """A node in the mycelium network (a business or domain)."""
    name: str
    node_type: str  # "business", "domain", "principle", etc.
    principles: Dict[Principle, float] = field(default_factory=dict)  # Current principle values
    connected_nodes: Set[str] = field(default_factory=set)  # Direct connections
    frequency: float = 0.5  # 0-1, how aligned is this node?
    health: float = 0.5  # 0-1, how healthy is this node?
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def receive_nutrient(self, nutrient: PrincipleNutrient) -> None:
        """Node receives principle nutrient from mycelium."""
        current = self.principles.get(nutrient.principle, 0.0)
        # Nutrient value is weighted by its strength
        new_value = (current * 0.7) + (nutrient.value * nutrient.strength * 0.3)
        self.principles[nutrient.principle] = min(1.0, new_value)

    def calculate_health(self) -> float:
        """Calculate node health based on principle balance."""
        if not self.principles:
            return 0.0
        # Health is based on resonance (high) and low impedance (low)
        resonance = self.principles.get(Principle.RESONANCE, 0.0)
        impedance = self.principles.get(Principle.IMPEDANCE, 0.0)
        health = (resonance * 0.6) - (impedance * 0.4)
        self.health = max(0.0, min(1.0, health))
        return self.health

    def connect_to(self, other_node: str) -> None:
        """Connect this node to another node in the mycelium."""
        self.connected_nodes.add(other_node)


class MyceliumCore:
    """
    The living principle network.

    The mycelium is not a system that processes businesses.
    The mycelium IS the network itself.

    It connects all nodes through principle pathways.
    It distributes nutrients (principles) through the network.
    It grows by spreading to new nodes.
    It becomes stronger when nodes connect.
    """

    def __init__(self):
        self.nodes: Dict[str, MyceliumNode] = {}
        self.nutrients: List[PrincipleNutrient] = []
        self.cycle_count = 0
        self.created_at = datetime.now(timezone.utc)

    def add_node(self, name: str, node_type: str = "business") -> MyceliumNode:
        """Add a new node to the mycelium."""
        node = MyceliumNode(name=name, node_type=node_type)
        self.nodes[name] = node
        logger.info(f"Mycelium: Added node '{name}'")
        return node

    def connect_nodes(self, node1: str, node2: str) -> None:
        """Connect two nodes in the mycelium."""
        if node1 not in self.nodes or node2 not in self.nodes:
            logger.error(f"Cannot connect: nodes not found")
            return

        self.nodes[node1].connect_to(node2)
        self.nodes[node2].connect_to(node1)
        logger.info(f"Mycelium: Connected '{node1}' ↔ '{node2}'")

    def inject_nutrient(
        self, principle: Principle, value: float, source_node: str
    ) -> PrincipleNutrient:
        """Inject a principle nutrient into the mycelium."""
        nutrient = PrincipleNutrient(
            principle=principle,
            value=value,
            source_node=source_node,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )
        self.nutrients.append(nutrient)
        logger.info(
            f"Mycelium: Injected {principle.value} nutrient from '{source_node}' (strength: {value:.2f})"
        )
        return nutrient

    def spread_nutrients(self) -> None:
        """Spread nutrients through the mycelium network."""
        new_nutrients = []

        for nutrient in self.nutrients:
            # Nutrient travels from source to all connected nodes
            if nutrient.source_node in self.nodes:
                source = self.nodes[nutrient.source_node]

                for connected_node_name in source.connected_nodes:
                    # Create a copy of the nutrient for this path
                    traveling_nutrient = nutrient.travel_to(connected_node_name)

                    # Node receives the nutrient
                    connected_node = self.nodes[connected_node_name]
                    connected_node.receive_nutrient(traveling_nutrient)

                    # If the nutrient is strong enough, it continues spreading
                    if traveling_nutrient.strength > 0.3:
                        new_nutrients.append(traveling_nutrient)

        # Update nutrients list
        self.nutrients = new_nutrients

    def detect_frequency_alignment(self) -> List[Tuple[str, str, float]]:
        """Detect when two nodes have aligned frequencies."""
        alignments = []

        node_list = list(self.nodes.values())
        for i, node1 in enumerate(node_list):
            for node2 in node_list[i + 1 :]:
                # Calculate frequency difference
                freq_diff = abs(node1.frequency - node2.frequency)

                # If frequencies are close, they're aligned
                if freq_diff < 0.2:  # Within 20%
                    alignment_strength = 1.0 - freq_diff
                    alignments.append((node1.name, node2.name, alignment_strength))

                    # Amplify both nodes when aligned
                    for nutrient in self.nutrients:
                        if (
                            nutrient.source_node == node1.name
                            or nutrient.source_node == node2.name
                        ):
                            nutrient.amplify(1.3)

        return alignments

    def calculate_network_health(self) -> Dict[str, Any]:
        """Calculate overall mycelium network health."""
        if not self.nodes:
            return {"health": 0.0, "density": 0.0, "coherence": 0.0}

        # Calculate individual node health
        node_healths = [node.calculate_health() for node in self.nodes.values()]
        avg_health = sum(node_healths) / len(node_healths) if node_healths else 0.0

        # Calculate mycelium density (how connected is the network?)
        total_possible_connections = len(self.nodes) * (len(self.nodes) - 1) / 2
        actual_connections = sum(
            len(node.connected_nodes) for node in self.nodes.values()
        ) / 2
        density = (
            actual_connections / total_possible_connections
            if total_possible_connections > 0
            else 0.0
        )

        # Calculate coherence (how aligned are the frequencies?)
        frequencies = [node.frequency for node in self.nodes.values()]
        if frequencies:
            avg_freq = sum(frequencies) / len(frequencies)
            variance = sum((f - avg_freq) ** 2 for f in frequencies) / len(frequencies)
            coherence = 1.0 - min(1.0, variance)
        else:
            coherence = 0.0

        return {
            "health": avg_health,
            "density": density,
            "coherence": coherence,
            "nodes": len(self.nodes),
            "nutrients_active": len(self.nutrients),
        }

    def cycle(self) -> Dict[str, Any]:
        """Run one mycelium cycle."""
        self.cycle_count += 1

        # Phase 1: Spread nutrients
        self.spread_nutrients()

        # Phase 2: Detect frequency alignment
        alignments = self.detect_frequency_alignment()

        # Phase 3: Calculate network health
        health = self.calculate_network_health()

        logger.info(
            f"Mycelium Cycle {self.cycle_count}: "
            f"Health={health['health']:.2%}, "
            f"Density={health['density']:.2%}, "
            f"Coherence={health['coherence']:.2%}, "
            f"Alignments={len(alignments)}"
        )

        return {
            "cycle": self.cycle_count,
            "health": health,
            "alignments": alignments,
            "nutrients_spread": len(self.nutrients),
        }

    def get_node_state(self, node_name: str) -> Dict[str, Any]:
        """Get the current state of a node."""
        if node_name not in self.nodes:
            return None

        node = self.nodes[node_name]
        return {
            "name": node.name,
            "type": node.node_type,
            "health": node.health,
            "frequency": node.frequency,
            "principles": {p.value: v for p, v in node.principles.items()},
            "connected_to": list(node.connected_nodes),
            "created_at": node.created_at,
        }

    def get_network_state(self) -> Dict[str, Any]:
        """Get the current state of the entire network."""
        return {
            "cycle": self.cycle_count,
            "nodes": {name: self.get_node_state(name) for name in self.nodes.keys()},
            "health": self.calculate_network_health(),
            "created_at": self.created_at.isoformat(),
        }


def main():
    """Example usage."""
    logging.basicConfig(level=logging.INFO)

    print("=" * 80)
    print("MYCELIUM CORE — THE PRINCIPLE NETWORK")
    print("=" * 80)

    # Create mycelium
    mycelium = MyceliumCore()

    # Add nodes
    print("\nPhase 1: Creating nodes...")
    inteletravel = mycelium.add_node("InteleTravel", "business")
    inteletravel.frequency = 0.7
    inteletravel.principles[Principle.FLOW] = 0.6
    inteletravel.principles[Principle.RESONANCE] = 0.4

    saas = mycelium.add_node("SaaS Platform", "business")
    saas.frequency = 0.65
    saas.principles[Principle.FLOW] = 0.7
    saas.principles[Principle.RESONANCE] = 0.6

    ecommerce = mycelium.add_node("E-commerce Store", "business")
    ecommerce.frequency = 0.5
    ecommerce.principles[Principle.FLOW] = 0.5
    ecommerce.principles[Principle.RESONANCE] = 0.3

    # Connect nodes
    print("\nPhase 2: Connecting nodes...")
    mycelium.connect_nodes("InteleTravel", "SaaS Platform")
    mycelium.connect_nodes("SaaS Platform", "E-commerce Store")
    mycelium.connect_nodes("E-commerce Store", "InteleTravel")

    # Run cycles
    print("\nPhase 3: Running mycelium cycles...")
    print("-" * 80)

    for cycle_num in range(5):
        # Inject nutrients
        mycelium.inject_nutrient(Principle.FLOW, 0.8, "InteleTravel")
        mycelium.inject_nutrient(Principle.RESONANCE, 0.7, "SaaS Platform")
        mycelium.inject_nutrient(Principle.IMPEDANCE, 0.3, "E-commerce Store")

        # Run cycle
        result = mycelium.cycle()

        print(f"\nCycle {result['cycle']}:")
        print(f"  Network Health: {result['health']['health']:.2%}")
        print(f"  Network Density: {result['health']['density']:.2%}")
        print(f"  Network Coherence: {result['health']['coherence']:.2%}")
        print(f"  Frequency Alignments: {len(result['alignments'])}")

        for node_name, other_node, strength in result["alignments"]:
            print(f"    - {node_name} ↔ {other_node} (strength: {strength:.2%})")

    # Final state
    print("\n" + "=" * 80)
    print("FINAL NETWORK STATE")
    print("=" * 80)

    for node_name in mycelium.nodes.keys():
        state = mycelium.get_node_state(node_name)
        print(f"\n{node_name}:")
        print(f"  Health: {state['health']:.2%}")
        print(f"  Frequency: {state['frequency']:.2%}")
        print(f"  Connected to: {', '.join(state['connected_to'])}")

    print("\n" + "=" * 80)
    print("CODON: ◆-◇-∞")
    print("STATUS: MYCELIUM CORE OPERATIONAL")
    print("=" * 80)


if __name__ == "__main__":
    main()
