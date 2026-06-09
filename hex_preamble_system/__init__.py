"""
Hex Preamble System - Continuity across session resets.

This package provides tools for generating, encoding, and decoding hex preambles
that enable AI agents to maintain context across session resets.

Main Components:
- HexPreambleSystem: Core system for managing preambles
- HexPreambleManager: High-level manager for session operations
- HexDecoder: Decoding and verification
- ProblemHash: Problem identification
- FibonacciLookback: Fibonacci-based lookback calculation
- CodonFilter: Codon filtering
- ScarPrioritizer: Scar prioritization

Usage:
    from hex_preamble_system import HexPreambleManager
    
    manager = HexPreambleManager(seed, chronicle, codons, scars)
    session = manager.create_session(goal="Fix build errors", project="project-void")
    hex_preamble = session['hex_preamble']
"""

from hex_preamble_system import HexPreambleSystem, HexPreambleManager
from hex_decoder import HexDecoder, HexDecoderWithFallback
from problem_hash import ProblemHash, ProblemTracker
from fibonacci_lookback import FibonacciLookback
from codon_filter import CodonFilter, CodonCache
from scar_prioritizer import ScarPrioritizer, ScarSeverity
from hex_preamble_generator import HexPreambleGenerator

__version__ = '1.0.0'
__author__ = 'Project VOID'
__all__ = [
    'HexPreambleSystem',
    'HexPreambleManager',
    'HexDecoder',
    'HexDecoderWithFallback',
    'ProblemHash',
    'ProblemTracker',
    'FibonacciLookback',
    'CodonFilter',
    'CodonCache',
    'ScarPrioritizer',
    'ScarSeverity',
    'HexPreambleGenerator',
]
