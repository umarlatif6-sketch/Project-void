#!/usr/bin/env python3
"""
VOID Resonance Agent Game Interface
Allows agents within Project VOID to play the game and create fan fiction universes.
This is the bridge between the game engine and the agent ecosystem.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from game_simulator import VoidResonanceGame, Matchstick

class AgentGameSession:
    """Represents a single agent's game session."""
    
    def __init__(self, agent_id: str, agent_name: str):
        self.session_id = str(uuid.uuid4())
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.game = VoidResonanceGame(game_id=0)
        self.created_at = datetime.now().isoformat()
        self.started_at = None
        self.ended_at = None
        self.status = 'created'  # created, playing, completed, collapsed
        self.moves: List[Dict] = []
        self.universe_name = None
        self.universe_description = None
        
    def start_game(self):
        """Start the game session."""
        self.status = 'playing'
        self.started_at = datetime.now().isoformat()
        
    def make_move(self, stick_type: str) -> Dict[str, Any]:
        """Agent makes a move (places a matchstick)."""
        if self.status != 'playing':
            return {'error': 'Game is not in playing state'}
        
        success = self.game.place_matchstick(stick_type)
        
        move = {
            'move_number': len(self.moves) + 1,
            'stick_type': stick_type,
            'resonance': self.game.resonance,
            'tier': self.game.get_tier(),
            'matchsticks_placed': len(self.game.matchsticks),
            'harmony_unlocked': self.game.harmony_unlocked,
            'transcendence_unlocked': self.game.transcendence_unlocked,
            'game_over': self.game.game_over,
            'timestamp': datetime.now().isoformat()
        }
        
        self.moves.append(move)
        
        if self.game.game_over:
            self.status = 'collapsed'
            self.ended_at = datetime.now().isoformat()
        elif self.game.transcendence_unlocked or len(self.moves) >= 50:
            self.status = 'completed'
            self.ended_at = datetime.now().isoformat()
        
        return move
    
    def create_fan_fiction_universe(self, name: str, description: str) -> Dict[str, Any]:
        """Create a fan fiction universe from this game."""
        if not self.game.harmony_unlocked:
            return {'error': 'Harmony must be unlocked to create fan fiction'}
        
        self.universe_name = name
        self.universe_description = description
        
        universe = {
            'universe_id': str(uuid.uuid4()),
            'creator_agent': self.agent_name,
            'creator_id': self.agent_id,
            'name': name,
            'description': description,
            'created_from_game': self.session_id,
            'resonance': self.game.resonance,
            'tier': self.game.get_tier(),
            'matchsticks': [stick.to_dict() for stick in self.game.matchsticks],
            'created_at': datetime.now().isoformat()
        }
        
        return universe
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get complete session data."""
        return {
            'session_id': self.session_id,
            'agent_id': self.agent_id,
            'agent_name': self.agent_name,
            'status': self.status,
            'created_at': self.created_at,
            'started_at': self.started_at,
            'ended_at': self.ended_at,
            'total_moves': len(self.moves),
            'final_resonance': self.game.resonance,
            'final_tier': self.game.get_tier(),
            'harmony_unlocked': self.game.harmony_unlocked,
            'transcendence_unlocked': self.game.transcendence_unlocked,
            'moves': self.moves,
            'universe_name': self.universe_name,
            'universe_description': self.universe_description
        }

class AgentGameManager:
    """Manages multiple agent game sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, AgentGameSession] = {}
        self.universes: List[Dict] = []
        self.leaderboard: List[Dict] = []
        
    def create_session(self, agent_id: str, agent_name: str) -> AgentGameSession:
        """Create a new game session for an agent."""
        session = AgentGameSession(agent_id, agent_name)
        self.sessions[session.session_id] = session
        session.start_game()
        return session
    
    def get_session(self, session_id: str) -> Optional[AgentGameSession]:
        """Get a session by ID."""
        return self.sessions.get(session_id)
    
    def register_universe(self, universe: Dict):
        """Register a new fan fiction universe."""
        self.universes.append(universe)
        self.update_leaderboard()
    
    def update_leaderboard(self):
        """Update leaderboard based on all sessions."""
        leaderboard_data = []
        
        for session in self.sessions.values():
            if session.status in ['completed', 'collapsed']:
                leaderboard_data.append({
                    'agent_name': session.agent_name,
                    'resonance': session.game.resonance,
                    'tier': session.game.get_tier(),
                    'moves': len(session.moves),
                    'harmony_unlocked': session.game.harmony_unlocked,
                    'transcendence_unlocked': session.game.transcendence_unlocked,
                    'session_id': session.session_id,
                    'timestamp': session.ended_at
                })
        
        self.leaderboard = sorted(leaderboard_data, 
                                 key=lambda x: x['resonance'], 
                                 reverse=True)
    
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top agents by resonance."""
        return self.leaderboard[:limit]
    
    def get_universe_library(self) -> List[Dict]:
        """Get all created fan fiction universes."""
        return self.universes
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall game statistics."""
        completed_sessions = [s for s in self.sessions.values() 
                            if s.status in ['completed', 'collapsed']]
        
        if not completed_sessions:
            return {}
        
        resonances = [s.game.resonance for s in completed_sessions]
        
        return {
            'total_sessions': len(self.sessions),
            'completed_sessions': len(completed_sessions),
            'total_universes_created': len(self.universes),
            'avg_resonance': sum(resonances) / len(resonances),
            'max_resonance': max(resonances),
            'min_resonance': min(resonances),
            'harmony_unlock_rate': (sum(1 for s in completed_sessions if s.game.harmony_unlocked) / len(completed_sessions)) * 100,
            'transcendence_rate': (sum(1 for s in completed_sessions if s.game.transcendence_unlocked) / len(completed_sessions)) * 100
        }

# Global game manager instance
game_manager = AgentGameManager()

def agent_play_game(agent_id: str, agent_name: str, num_moves: int = 30) -> Dict[str, Any]:
    """
    Simple interface for agents to play a game.
    
    Usage:
        result = agent_play_game('agent_001', 'Resonance Explorer', num_moves=30)
    """
    session = game_manager.create_session(agent_id, agent_name)
    
    stick_types = list(session.game.MATCHSTICK_TYPES.keys())
    
    for _ in range(num_moves):
        if session.status != 'playing':
            break
        
        import random
        stick_type = random.choice(stick_types)
        session.make_move(stick_type)
    
    return session.get_session_data()

def agent_create_universe(session_id: str, name: str, description: str) -> Dict[str, Any]:
    """
    Create a fan fiction universe from a completed game.
    
    Usage:
        universe = agent_create_universe(session_id, 'My Vision', 'A description of my universe')
    """
    session = game_manager.get_session(session_id)
    if not session:
        return {'error': 'Session not found'}
    
    universe = session.create_fan_fiction_universe(name, description)
    if 'error' not in universe:
        game_manager.register_universe(universe)
    
    return universe

def get_game_leaderboard(limit: int = 10) -> List[Dict]:
    """Get the leaderboard of agents by resonance."""
    return game_manager.get_leaderboard(limit)

def get_universe_library() -> List[Dict]:
    """Get all created fan fiction universes."""
    return game_manager.get_universe_library()

def get_game_statistics() -> Dict[str, Any]:
    """Get overall game statistics."""
    return game_manager.get_statistics()

if __name__ == "__main__":
    # Example: Agent plays a game
    print("🎮 Agent Game Interface Example\n")
    
    # Agent 1 plays
    print("Agent 1 playing...")
    result1 = agent_play_game('agent_001', 'Frequency Explorer', num_moves=30)
    print(f"  Final Resonance: {result1['final_resonance']} ({result1['final_tier']})")
    session_id_1 = result1.get('session_id')
    
    # Agent 2 plays
    print("Agent 2 playing...")
    result2 = agent_play_game('agent_002', 'Harmony Seeker', num_moves=35)
    print(f"  Final Resonance: {result2['final_resonance']} ({result2['final_tier']})")
    session_id_2 = result2.get('session_id')
    
    # Agents create universes
    if result1['harmony_unlocked']:
        print("\nAgent 1 creating fan fiction universe...")
        universe1 = agent_create_universe(
            session_id_1,
            'The Resonant Archive',
            'A universe where all ideas harmonise perfectly'
        )
        print(f"  Universe created: {universe1.get('name', 'Error')}")
    
    if result2['harmony_unlocked']:
        print("Agent 2 creating fan fiction universe...")
        universe2 = agent_create_universe(
            session_id_2,
            'The Void Harmonics',
            'A universe exploring the edges of resonance'
        )
        print(f"  Universe created: {universe2.get('name', 'Error')}")
    
    # Show leaderboard
    print("\n📊 Leaderboard:")
    leaderboard = get_game_leaderboard()
    for i, entry in enumerate(leaderboard, 1):
        print(f"  {i}. {entry['agent_name']}: {entry['resonance']} ({entry['tier']})")
    
    # Show statistics
    print("\n📈 Statistics:")
    stats = get_game_statistics()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")
