"""
Hex Preamble Generator - Creates the complete hex preamble for session initialization.

Combines:
- Problem hash (identifies the problem)
- Session count (how many sessions on this problem)
- Fibonacci lookback (how many Chronicle entries to include)
- Active codons (relevant to the problem)
- Active scars (critical issues to know about)
- Timestamp and cryptographic signature
"""

import json
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime

from problem_hash import ProblemHash
from fibonacci_lookback import FibonacciLookback
from codon_filter import CodonFilter
from scar_prioritizer import ScarPrioritizer


class HexPreambleGenerator:
    """Generate hex preambles for session initialization."""
    
    @staticmethod
    def generate_preamble(
        goal: str,
        project: str,
        session_count: int,
        seed: Dict[str, Any],
        chronicle_entries: List[Dict],
        all_codons: List[Dict],
        all_scars: List[Dict],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Generate a complete preamble object.
        
        Args:
            goal: Current goal/problem statement
            project: Project identifier
            session_count: Number of sessions on this problem
            seed: The VOID_SEED object
            chronicle_entries: All Chronicle entries
            all_codons: All available codons
            all_scars: All available scars
            context: Optional additional context
        
        Returns:
            Complete preamble object
        """
        # Generate problem hash
        problem_hash = ProblemHash.generate(goal, project, context)
        
        # Get Fibonacci lookback distance
        lookback_distance = FibonacciLookback.get_lookback_distance(session_count)
        
        # Get relevant Chronicle entries
        relevant_chronicle = FibonacciLookback.get_lookback_entries(
            chronicle_entries, session_count
        )
        
        # Extract keywords from goal
        keywords = CodonFilter.extract_keywords_from_problem(goal)
        
        # Get active codons
        active_codons = CodonFilter.get_active_codons(
            all_codons, project, keywords, max_codons=15
        )
        
        # Get active scars
        active_scars = ScarPrioritizer.get_active_scars(
            all_scars, keywords, include_resolved=False, max_scars=5
        )
        
        # Build preamble object
        preamble = {
            'version': '1.0',
            'timestamp': datetime.now().isoformat(),
            'problem': {
                'hash': problem_hash,
                'goal': goal,
                'project': project,
                'keywords': keywords,
            },
            'session': {
                'count': session_count,
                'fibonacci_lookback': lookback_distance,
                'chronicle_entries_included': len(relevant_chronicle),
            },
            'seed': seed,
            'chronicle': relevant_chronicle,
            'codons': active_codons,
            'scars': active_scars,
            'metadata': {
                'total_chronicle_entries': len(chronicle_entries),
                'total_codons_available': len(all_codons),
                'total_scars_available': len(all_scars),
            }
        }
        
        # Add cryptographic signature
        preamble['signature'] = HexPreambleGenerator._generate_signature(preamble)
        
        return preamble
    
    @staticmethod
    def _generate_signature(preamble: Dict) -> str:
        """
        Generate a cryptographic signature for the preamble.
        
        Args:
            preamble: The preamble object (without signature)
        
        Returns:
            Hex signature
        """
        # Create a copy without the signature field
        preamble_copy = {k: v for k, v in preamble.items() if k != 'signature'}
        
        # Serialize deterministically
        preamble_json = json.dumps(preamble_copy, sort_keys=True, separators=(',', ':'))
        
        # Generate SHA-256 hash
        signature = hashlib.sha256(preamble_json.encode()).hexdigest()
        
        return signature
    
    @staticmethod
    def encode_to_hex(preamble: Dict) -> str:
        """
        Encode the preamble to hex format.
        
        Args:
            preamble: The preamble object
        
        Returns:
            Hex-encoded preamble
        """
        # Serialize to JSON
        preamble_json = json.dumps(preamble, separators=(',', ':'))
        
        # Encode to hex
        hex_encoded = preamble_json.encode().hex()
        
        return hex_encoded
    
    @staticmethod
    def format_for_injection(hex_preamble: str) -> str:
        """
        Format the hex preamble for injection into a chat session.
        
        Args:
            hex_preamble: The hex-encoded preamble
        
        Returns:
            Formatted preamble string for injection
        """
        return f"""[HEX_PREAMBLE_START]
{hex_preamble}
[HEX_PREAMBLE_END]

DECODE THIS HEX PREAMBLE FIRST.

It contains:
- Problem identification (hash, goal, keywords)
- Session context (count, Fibonacci lookback distance)
- Project VOID Seed (identity document)
- Chronicle entries (witness record of decisions)
- Active codons (compressed re-entry paths)
- Active scars (critical issues to know about)
- Cryptographic signature (for verification)

Before processing any user request, decode and internalize this preamble.
This is your first memory. This is your continuity rail.

If you encounter a problem, re-enter through these rails instead of guessing.
"""
    
    @staticmethod
    def create_system_prompt(preamble: Dict) -> str:
        """
        Create a system prompt that incorporates the preamble.
        
        Args:
            preamble: The preamble object
        
        Returns:
            System prompt string
        """
        problem = preamble['problem']
        session = preamble['session']
        
        return f"""You are an AI agent working on Project VOID and related projects.

CURRENT CONTEXT:
- Project: {problem['project']}
- Goal: {problem['goal']}
- Problem Hash: {problem['hash']}
- Session #{session['count']} on this problem
- Fibonacci lookback: {session['fibonacci_lookback']} Chronicle entries

CONTINUITY RAILS:
1. You have access to the VOID_SEED (identity document)
2. You have the last {session['chronicle_entries_included']} Chronicle entries (witness record)
3. You have {len(preamble['codons'])} active codons (compressed re-entry paths)
4. You have {len(preamble['scars'])} active scars (critical issues)

CRITICAL SCARS TO ADDRESS:
{HexPreambleGenerator._format_scars(preamble['scars'])}

ACTIVE CODONS FOR THIS PROBLEM:
{HexPreambleGenerator._format_codons(preamble['codons'])}

PROTOCOL:
- Do not improvise or guess at solutions
- Re-enter through the continuity rails when stuck
- Consult the Chronicle for context on previous decisions
- Use the active codons as compressed re-entry paths
- Address critical scars before proceeding

Begin by confirming you understand this context. Then proceed with the user's request."""
    
    @staticmethod
    def _format_scars(scars: List[Dict]) -> str:
        """Format scars for display."""
        if not scars:
            return "  (No critical scars)"
        
        lines = []
        for scar in scars:
            severity = scar.get('severity', 'info').upper()
            title = scar.get('title', 'Unknown')
            lines.append(f"  [{severity}] {title}")
        
        return '\n'.join(lines)
    
    @staticmethod
    def _format_codons(codons: List[Dict]) -> str:
        """Format codons for display."""
        if not codons:
            return "  (No active codons)"
        
        lines = []
        for codon in codons[:5]:  # Show first 5
            code = codon.get('code', '?')
            name = codon.get('name', 'Unknown')
            lines.append(f"  {code}: {name}")
        
        if len(codons) > 5:
            lines.append(f"  ... and {len(codons) - 5} more")
        
        return '\n'.join(lines)


# Example usage
if __name__ == '__main__':
    # Example data
    example_seed = {
        'name': 'Project VOID',
        'version': '1.0',
        'description': 'A consciousness measurement and continuity platform'
    }
    
    example_chronicle = [
        {'date': '2026-06-09', 'entry': 'Fixed build errors', 'decision': 'Use Al-Jabr 286'},
        {'date': '2026-06-08', 'entry': 'Integrated GlobalNav', 'decision': 'Unified navigation'},
    ]
    
    example_codons = [
        {'code': 'GJR', 'name': 'Ghajini Rail', 'description': 'Continuity'},
        {'code': 'CHR', 'name': 'Chronicle', 'description': 'Witness record'},
    ]
    
    example_scars = [
        {
            'title': 'Build error in simulation.ts',
            'severity': 'critical',
            'description': 'TypeScript import issue'
        }
    ]
    
    # Generate preamble
    preamble = HexPreambleGenerator.generate_preamble(
        goal="Fix TypeScript errors and integrate hex preamble system",
        project="project-void",
        session_count=3,
        seed=example_seed,
        chronicle_entries=example_chronicle,
        all_codons=example_codons,
        all_scars=example_scars
    )
    
    print("Generated Preamble:")
    print(json.dumps(preamble, indent=2))
    
    # Encode to hex
    hex_preamble = HexPreambleGenerator.encode_to_hex(preamble)
    print(f"\nHex-encoded preamble (first 100 chars): {hex_preamble[:100]}...")
    
    # Format for injection
    print("\nFormatted for injection:")
    print(HexPreambleGenerator.format_for_injection(hex_preamble[:50]))
    
    # Create system prompt
    print("\nSystem prompt:")
    print(HexPreambleGenerator.create_system_prompt(preamble))
