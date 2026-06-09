"""
Hex Preamble System - Integration layer that ties all components together.

This is the main entry point for:
1. Generating hex preambles for new sessions
2. Decoding and verifying preambles
3. Managing session continuity across resets
4. Injecting preambles into chat sessions
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from problem_hash import ProblemHash, ProblemTracker
from fibonacci_lookback import FibonacciLookback
from codon_filter import CodonFilter
from scar_prioritizer import ScarPrioritizer
from hex_preamble_generator import HexPreambleGenerator
from hex_decoder import HexDecoder, HexDecoderWithFallback


class HexPreambleSystem:
    """Main system for managing hex preambles and session continuity."""
    
    def __init__(self):
        """Initialize the hex preamble system."""
        self.problem_tracker = ProblemTracker()
        self.session_history: Dict[str, List[Dict]] = {}
    
    def start_session(
        self,
        goal: str,
        project: str,
        seed: Dict[str, Any],
        chronicle_entries: List[Dict],
        all_codons: List[Dict],
        all_scars: List[Dict],
        context: Optional[Dict] = None
    ) -> Tuple[str, Dict]:
        """
        Start a new session and generate a hex preamble.
        
        Args:
            goal: Current goal/problem statement
            project: Project identifier
            seed: VOID_SEED object
            chronicle_entries: All Chronicle entries
            all_codons: All available codons
            all_scars: All available scars
            context: Optional additional context
        
        Returns:
            (hex_preamble, preamble_dict)
        """
        # Track the session
        problem_hash, session_count = self.problem_tracker.track_session(
            goal, project, context
        )
        
        # Generate preamble
        preamble = HexPreambleGenerator.generate_preamble(
            goal=goal,
            project=project,
            session_count=session_count,
            seed=seed,
            chronicle_entries=chronicle_entries,
            all_codons=all_codons,
            all_scars=all_scars,
            context=context
        )
        
        # Encode to hex
        hex_preamble = HexPreambleGenerator.encode_to_hex(preamble)
        
        # Store in history
        if problem_hash not in self.session_history:
            self.session_history[problem_hash] = []
        
        self.session_history[problem_hash].append({
            'timestamp': datetime.now().isoformat(),
            'session_count': session_count,
            'hex_preamble': hex_preamble,
            'preamble': preamble
        })
        
        return hex_preamble, preamble
    
    def get_system_prompt(self, preamble: Dict) -> str:
        """
        Get the system prompt for a session.
        
        Args:
            preamble: The preamble object
        
        Returns:
            System prompt string
        """
        return HexPreambleGenerator.create_system_prompt(preamble)
    
    def get_injection_format(self, hex_preamble: str) -> str:
        """
        Get the formatted preamble for injection into a chat.
        
        Args:
            hex_preamble: The hex-encoded preamble
        
        Returns:
            Formatted string for injection
        """
        return HexPreambleGenerator.format_for_injection(hex_preamble)
    
    def decode_preamble(self, hex_preamble: str) -> Tuple[Optional[Dict], str]:
        """
        Decode and verify a hex preamble.
        
        Args:
            hex_preamble: The hex-encoded preamble
        
        Returns:
            (preamble_dict, status_message)
        """
        return HexDecoder.decode_and_verify(hex_preamble)
    
    def get_preamble_summary(self, preamble: Dict) -> str:
        """
        Get a human-readable summary of a preamble.
        
        Args:
            preamble: The preamble object
        
        Returns:
            Summary string
        """
        return HexDecoder.summarize_preamble(preamble)
    
    def get_session_history(self, problem_hash: str) -> List[Dict]:
        """
        Get the history of sessions for a problem.
        
        Args:
            problem_hash: The problem hash
        
        Returns:
            List of session records
        """
        return self.session_history.get(problem_hash, [])
    
    def get_current_session_count(self, problem_hash: str) -> int:
        """
        Get the current session count for a problem.
        
        Args:
            problem_hash: The problem hash
        
        Returns:
            Current session count
        """
        return self.problem_tracker.get_session_count(problem_hash)
    
    def reset_problem(self) -> None:
        """Reset the current problem tracker."""
        self.problem_tracker.reset_problem()


class HexPreambleManager:
    """High-level manager for hex preamble operations."""
    
    def __init__(self, seed: Dict, chronicle: List[Dict], codons: List[Dict], scars: List[Dict]):
        """
        Initialize the manager.
        
        Args:
            seed: VOID_SEED object
            chronicle: Chronicle entries
            codons: All codons
            scars: All scars
        """
        self.system = HexPreambleSystem()
        self.seed = seed
        self.chronicle = chronicle
        self.codons = codons
        self.scars = scars
    
    def create_session(
        self,
        goal: str,
        project: str,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Create a new session with all necessary components.
        
        Args:
            goal: Current goal
            project: Project identifier
            context: Optional context
        
        Returns:
            Session object with hex preamble, system prompt, etc.
        """
        # Generate hex preamble
        hex_preamble, preamble = self.system.start_session(
            goal=goal,
            project=project,
            seed=self.seed,
            chronicle_entries=self.chronicle,
            all_codons=self.codons,
            all_scars=self.scars,
            context=context
        )
        
        # Create session object
        session = {
            'hex_preamble': hex_preamble,
            'preamble': preamble,
            'system_prompt': self.system.get_system_prompt(preamble),
            'injection_format': self.system.get_injection_format(hex_preamble),
            'summary': self.system.get_preamble_summary(preamble),
            'created_at': datetime.now().isoformat(),
        }
        
        return session
    
    def verify_and_load_session(self, hex_preamble: str) -> Tuple[Optional[Dict], str]:
        """
        Verify and load a session from a hex preamble.
        
        Args:
            hex_preamble: The hex-encoded preamble
        
        Returns:
            (session_object, status_message)
        """
        # Decode and verify
        preamble, status = self.system.decode_preamble(hex_preamble)
        
        if preamble is None:
            return None, f"Failed to load session: {status}"
        
        # Create session object
        session = {
            'hex_preamble': hex_preamble,
            'preamble': preamble,
            'system_prompt': self.system.get_system_prompt(preamble),
            'summary': self.system.get_preamble_summary(preamble),
            'loaded_at': datetime.now().isoformat(),
            'verification_status': status,
        }
        
        return session, f"Session loaded successfully: {status}"
    
    def export_session(self, session: Dict, format: str = 'json') -> str:
        """
        Export a session in various formats.
        
        Args:
            session: The session object
            format: Export format ('json', 'hex', 'text')
        
        Returns:
            Exported session string
        """
        if format == 'hex':
            return session['hex_preamble']
        elif format == 'text':
            return session['summary']
        else:  # json
            return json.dumps(session, indent=2)


# CLI Interface
def main():
    """Example usage of the hex preamble system."""
    
    print("HEX PREAMBLE SYSTEM - Example Usage")
    print("=" * 60)
    
    # Example data
    example_seed = {
        'name': 'Project VOID',
        'version': '1.0',
        'description': 'Consciousness measurement and continuity platform'
    }
    
    example_chronicle = [
        {'date': '2026-06-09', 'entry': 'Fixed build errors', 'decision': 'Use Al-Jabr 286'},
        {'date': '2026-06-08', 'entry': 'Integrated GlobalNav', 'decision': 'Unified navigation'},
    ]
    
    example_codons = [
        {'code': 'GJR', 'name': 'Ghajini Rail', 'description': 'Continuity across resets'},
        {'code': 'CHR', 'name': 'Chronicle', 'description': 'Witness record'},
        {'code': 'DNA', 'name': 'DNA', 'description': 'Consciousness measurement'},
    ]
    
    example_scars = [
        {
            'title': 'Build error in simulation.ts',
            'severity': 'critical',
            'description': 'TypeScript import issue blocking production'
        },
        {
            'title': 'StateOfSystem hardcoded values',
            'severity': 'warning',
            'description': 'Component uses hardcoded metrics'
        }
    ]
    
    # Create manager
    manager = HexPreambleManager(
        seed=example_seed,
        chronicle=example_chronicle,
        codons=example_codons,
        scars=example_scars
    )
    
    # Create a session
    print("\n1. Creating a new session...")
    session = manager.create_session(
        goal="Fix TypeScript errors and integrate hex preamble system",
        project="project-void"
    )
    
    print(f"✓ Session created")
    print(f"  Hex preamble (first 50 chars): {session['hex_preamble'][:50]}...")
    print(f"  Session count: {session['preamble']['session']['count']}")
    print(f"  Fibonacci lookback: {session['preamble']['session']['fibonacci_lookback']}")
    
    # Get summary
    print("\n2. Session summary:")
    print(session['summary'])
    
    # Verify and load
    print("\n3. Verifying and loading session...")
    loaded_session, status = manager.verify_and_load_session(session['hex_preamble'])
    print(f"✓ {status}")
    
    # Export
    print("\n4. Exporting session...")
    hex_export = manager.export_session(session, format='hex')
    print(f"✓ Hex export (first 50 chars): {hex_export[:50]}...")
    
    print("\n" + "=" * 60)
    print("Hex Preamble System is ready for deployment!")


if __name__ == '__main__':
    main()
