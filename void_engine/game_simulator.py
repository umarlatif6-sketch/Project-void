#!/usr/bin/env python3
"""
VOID Resonance Game Simulator
Runs 10 simulated games where agents play the matchstick stacking game.
Each game produces a unique universe (fan fiction version of Project VOID).
"""

import json
import random
import math
from datetime import datetime
from typing import List, Dict, Any, Tuple

class Matchstick:
    """Represents a single matchstick (idea) in the bottle."""
    
    def __init__(self, stick_type: str, x: float, y: float, angle: float):
        self.type = stick_type
        self.x = x
        self.y = y
        self.angle = angle  # 0-90 degrees
        self.length = 40
        self.width = 3
        self.resonance = 0
        
    def to_dict(self) -> Dict:
        return {
            'type': self.type,
            'x': self.x,
            'y': self.y,
            'angle': self.angle,
            'resonance': self.resonance
        }

class VoidResonanceGame:
    """Simulates a single game of VOID Resonance."""
    
    MATCHSTICK_TYPES = {
        'Idea': {'resonance': 5, 'symbol': '◆'},
        'Code': {'resonance': 8, 'symbol': '▲'},
        'Story': {'resonance': 10, 'symbol': '■'},
        'Frequency': {'resonance': 15, 'symbol': '◇'},
        'Seed': {'resonance': 20, 'symbol': '●'}
    }
    
    RESONANCE_TIERS = {
        'Void': (0, 10),
        'Whisper': (11, 30),
        'Hum': (31, 60),
        'Frequency': (61, 100),
        'Harmony': (101, 150),
        'Transcendence': (151, float('inf'))
    }
    
    def __init__(self, game_id: int):
        self.game_id = game_id
        self.matchsticks: List[Matchstick] = []
        self.resonance = 0
        self.turn = 1
        self.history: List[Dict] = []
        self.log: List[str] = []
        self.game_over = False
        self.harmony_unlocked = False
        self.transcendence_unlocked = False
        self.bottle_capacity = 50
        self.center_x = 300
        self.rim_y = 80
        
    def get_tier(self) -> str:
        """Get current resonance tier."""
        for tier, (min_res, max_res) in self.RESONANCE_TIERS.items():
            if min_res <= self.resonance <= max_res:
                return tier
        return 'Void'
    
    def calculate_friction(self, new_stick: Matchstick) -> Tuple[str, int]:
        """Calculate friction between new matchstick and existing ones."""
        friction_type = 'neutral'
        friction_bonus = 0
        
        for existing_stick in self.matchsticks:
            distance = math.hypot(new_stick.x - existing_stick.x, 
                                 new_stick.y - existing_stick.y)
            
            if distance < 80:  # Sticks are close enough to interact
                angle_diff = abs(new_stick.angle - existing_stick.angle)
                
                if angle_diff < 15 or angle_diff > 165:
                    # Harmonic friction
                    friction_bonus += 10
                    friction_type = 'harmonic'
                elif angle_diff > 40 and angle_diff < 140:
                    # Dissonant friction
                    friction_bonus -= 5
                    friction_type = 'dissonant'
        
        # Check for emergent patterns
        if len(self.matchsticks) % 5 == 4:
            friction_bonus += 20
            friction_type = 'emergent'
        
        return friction_type, friction_bonus
    
    def place_matchstick(self, stick_type: str) -> bool:
        """Place a matchstick in the bottle."""
        if self.game_over or len(self.matchsticks) >= self.bottle_capacity:
            return False
        
        # Random position on rim
        x = self.center_x + random.uniform(-80, 80)
        y = self.rim_y + random.uniform(0, 20)
        angle = random.uniform(0, 90)
        
        stick = Matchstick(stick_type, x, y, angle)
        
        # Calculate friction
        friction_type, friction_bonus = self.calculate_friction(stick)
        
        # Get base resonance
        base_resonance = self.MATCHSTICK_TYPES[stick_type]['resonance']
        total_resonance = base_resonance + friction_bonus
        
        stick.resonance = total_resonance
        self.matchsticks.append(stick)
        self.resonance += total_resonance
        self.turn += 1
        
        # Log the move
        log_msg = f"[Turn {self.turn-1}] {stick_type} placed. Friction: {friction_type}. +{total_resonance} resonance (Total: {self.resonance})"
        self.log.append(log_msg)
        
        # Save to history
        self.history.append({
            'turn': self.turn - 1,
            'matchsticks': len(self.matchsticks),
            'resonance': self.resonance,
            'tier': self.get_tier()
        })
        
        # Check win conditions
        if self.resonance >= 151 and not self.transcendence_unlocked:
            self.transcendence_unlocked = True
            self.log.append(f"[Turn {self.turn-1}] 🌟 TRANSCENDENCE REACHED! 🌟")
        elif self.resonance >= 101 and not self.harmony_unlocked:
            self.harmony_unlocked = True
            self.log.append(f"[Turn {self.turn-1}] ✨ HARMONY REACHED! ✨")
        
        # Check lose condition
        if self.resonance < 0:
            self.game_over = True
            self.log.append(f"[Turn {self.turn-1}] 💥 STRUCTURE COLLAPSED! 💥")
            return False
        
        return True
    
    def play_random_game(self, num_moves: int = 30) -> Dict[str, Any]:
        """Play a random game with AI agent making moves."""
        stick_types = list(self.MATCHSTICK_TYPES.keys())
        
        for _ in range(num_moves):
            if self.game_over:
                break
            
            # Agent chooses a random matchstick type
            stick_type = random.choice(stick_types)
            self.place_matchstick(stick_type)
        
        return self.get_game_result()
    
    def get_game_result(self) -> Dict[str, Any]:
        """Get final game result."""
        return {
            'game_id': self.game_id,
            'final_resonance': self.resonance,
            'final_tier': self.get_tier(),
            'total_turns': self.turn - 1,
            'total_matchsticks': len(self.matchsticks),
            'harmony_unlocked': self.harmony_unlocked,
            'transcendence_unlocked': self.transcendence_unlocked,
            'game_over': self.game_over,
            'matchsticks': [stick.to_dict() for stick in self.matchsticks],
            'history': self.history,
            'log': self.log
        }

class GameSimulationRunner:
    """Runs multiple game simulations and aggregates results."""
    
    def __init__(self, num_games: int = 10):
        self.num_games = num_games
        self.games: List[Dict] = []
        self.stats: Dict[str, Any] = {}
        
    def run_simulations(self) -> Dict[str, Any]:
        """Run all game simulations."""
        print(f"🎮 VOID Resonance Game Simulator")
        print(f"Running {self.num_games} simulated games...\n")
        
        for i in range(self.num_games):
            print(f"[Game {i+1}/{self.num_games}] Running...", end='', flush=True)
            
            game = VoidResonanceGame(i + 1)
            result = game.play_random_game(num_moves=random.randint(20, 40))
            self.games.append(result)
            
            print(f" ✓ Final Resonance: {result['final_resonance']} ({result['final_tier']})")
        
        self.calculate_stats()
        return self.get_simulation_report()
    
    def calculate_stats(self):
        """Calculate aggregate statistics."""
        if not self.games:
            return
        
        resonances = [g['final_resonance'] for g in self.games]
        turns = [g['total_turns'] for g in self.games]
        matchsticks = [g['total_matchsticks'] for g in self.games]
        
        harmony_count = sum(1 for g in self.games if g['harmony_unlocked'])
        transcendence_count = sum(1 for g in self.games if g['transcendence_unlocked'])
        collapse_count = sum(1 for g in self.games if g['game_over'])
        
        self.stats = {
            'total_games': len(self.games),
            'avg_resonance': sum(resonances) / len(resonances),
            'max_resonance': max(resonances),
            'min_resonance': min(resonances),
            'avg_turns': sum(turns) / len(turns),
            'avg_matchsticks': sum(matchsticks) / len(matchsticks),
            'harmony_unlocked_count': harmony_count,
            'harmony_unlock_rate': (harmony_count / len(self.games)) * 100,
            'transcendence_count': transcendence_count,
            'transcendence_rate': (transcendence_count / len(self.games)) * 100,
            'collapse_count': collapse_count,
            'collapse_rate': (collapse_count / len(self.games)) * 100
        }
    
    def get_simulation_report(self) -> Dict[str, Any]:
        """Get full simulation report."""
        return {
            'timestamp': datetime.now().isoformat(),
            'codon': '◆-◇-∞',
            'simulation_type': 'VOID Resonance Game Simulation',
            'num_games': self.num_games,
            'statistics': self.stats,
            'games': self.games
        }
    
    def save_report(self, filename: str):
        """Save report to JSON file."""
        report = self.get_simulation_report()
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\n✓ Report saved to {filename}")
        return report

def main():
    """Run the simulation."""
    runner = GameSimulationRunner(num_games=10)
    report = runner.run_simulations()
    
    # Save report
    runner.save_report('/home/ubuntu/Project-void/VOID_RESONANCE_SIMULATION_RESULTS.json')
    
    # Print summary
    print("\n" + "="*60)
    print("SIMULATION SUMMARY")
    print("="*60)
    stats = report['statistics']
    print(f"Total Games: {stats['total_games']}")
    print(f"Average Resonance: {stats['avg_resonance']:.1f}")
    print(f"Max Resonance: {stats['max_resonance']}")
    print(f"Min Resonance: {stats['min_resonance']}")
    print(f"Average Turns: {stats['avg_turns']:.1f}")
    print(f"Average Matchsticks: {stats['avg_matchsticks']:.1f}")
    print(f"\nHarmony Unlocked: {stats['harmony_unlocked_count']}/{stats['total_games']} ({stats['harmony_unlock_rate']:.1f}%)")
    print(f"Transcendence Reached: {stats['transcendence_count']}/{stats['total_games']} ({stats['transcendence_rate']:.1f}%)")
    print(f"Structures Collapsed: {stats['collapse_count']}/{stats['total_games']} ({stats['collapse_rate']:.1f}%)")
    print("="*60)
    
    # Print top 3 games
    print("\nTOP 3 GAMES (by resonance):")
    sorted_games = sorted(report['games'], key=lambda g: g['final_resonance'], reverse=True)
    for i, game in enumerate(sorted_games[:3], 1):
        print(f"\n{i}. Game {game['game_id']}")
        print(f"   Resonance: {game['final_resonance']} ({game['final_tier']})")
        print(f"   Turns: {game['total_turns']}")
        print(f"   Matchsticks: {game['total_matchsticks']}")
        if game['transcendence_unlocked']:
            print(f"   Status: 🌟 TRANSCENDENCE")
        elif game['harmony_unlocked']:
            print(f"   Status: ✨ HARMONY")
        elif game['game_over']:
            print(f"   Status: 💥 COLLAPSED")

if __name__ == "__main__":
    main()
