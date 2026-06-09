"""
Problem Hash Function - Identifies if two sessions are working on the same problem.

This allows the system to track session count per problem, not globally.
If the problem changes, the Fibonacci counter resets.
"""

import hashlib
import json
from typing import Dict, Any, Optional


class ProblemHash:
    """Generate and manage problem identifiers across sessions."""
    
    @staticmethod
    def generate(goal: str, project: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a deterministic hash for a problem/goal.
        
        Args:
            goal: The current goal or problem statement
            project: Project identifier (e.g., "the-living-fabric", "project-void")
            context: Optional additional context (features, components, etc.)
        
        Returns:
            Hex hash of the problem
        """
        problem_data = {
            'goal': goal.strip().lower(),
            'project': project.strip().lower(),
            'context': context or {}
        }
        
        # Serialize deterministically (sorted keys for consistency)
        problem_json = json.dumps(problem_data, sort_keys=True, separators=(',', ':'))
        
        # Create SHA-256 hash
        problem_hash = hashlib.sha256(problem_json.encode()).hexdigest()
        
        return problem_hash
    
    @staticmethod
    def normalize_goal(goal: str) -> str:
        """
        Normalize goal text to reduce false negatives.
        
        Examples:
            "Fix the build error" -> "fix build error"
            "Build the hex preamble system" -> "build hex preamble system"
        """
        # Remove common filler words
        filler = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for']
        words = goal.lower().split()
        words = [w for w in words if w not in filler]
        return ' '.join(words).strip()
    
    @staticmethod
    def compare(hash1: str, hash2: str, tolerance: float = 1.0) -> bool:
        """
        Compare two problem hashes.
        
        Args:
            hash1: First problem hash
            hash2: Second problem hash
            tolerance: Similarity threshold (1.0 = exact match only)
        
        Returns:
            True if hashes match (same problem)
        """
        return hash1 == hash2
    
    @staticmethod
    def extract_problem_from_goal(goal: str) -> Dict[str, str]:
        """
        Extract structured problem information from a goal string.
        
        Example:
            "Fix TypeScript errors in StateOfSystem component"
            -> {
                'action': 'fix',
                'problem': 'typescript errors',
                'location': 'stateofystem component'
            }
        """
        normalized = ProblemHash.normalize_goal(goal)
        words = normalized.split()
        
        # Simple extraction (can be enhanced with NLP)
        action = words[0] if words else 'unknown'
        problem = ' '.join(words[1:-1]) if len(words) > 2 else 'unknown'
        location = words[-1] if len(words) > 1 else 'unknown'
        
        return {
            'action': action,
            'problem': problem,
            'location': location
        }


class ProblemTracker:
    """Track session counts per problem."""
    
    def __init__(self):
        self.problem_sessions: Dict[str, int] = {}
        self.current_problem_hash: Optional[str] = None
    
    def track_session(self, goal: str, project: str, context: Optional[Dict] = None) -> tuple:
        """
        Track a new session and return (problem_hash, session_count).
        
        Args:
            goal: Current goal
            project: Project identifier
            context: Optional context
        
        Returns:
            (problem_hash, session_count_for_this_problem)
        """
        problem_hash = ProblemHash.generate(goal, project, context)
        
        # If this is a new problem, reset counter
        if problem_hash != self.current_problem_hash:
            self.current_problem_hash = problem_hash
            self.problem_sessions[problem_hash] = 1
        else:
            # Same problem, increment counter
            self.problem_sessions[problem_hash] = self.problem_sessions.get(problem_hash, 0) + 1
        
        session_count = self.problem_sessions[problem_hash]
        return problem_hash, session_count
    
    def get_session_count(self, problem_hash: str) -> int:
        """Get the current session count for a problem."""
        return self.problem_sessions.get(problem_hash, 0)
    
    def reset_problem(self) -> None:
        """Reset the current problem tracker."""
        self.current_problem_hash = None


# Example usage
if __name__ == '__main__':
    # Test problem hash generation
    goal1 = "Fix TypeScript errors in StateOfSystem component"
    goal2 = "Fix TypeScript errors in StateOfSystem component"
    goal3 = "Build the hex preamble system"
    
    hash1 = ProblemHash.generate(goal1, "the-living-fabric")
    hash2 = ProblemHash.generate(goal2, "the-living-fabric")
    hash3 = ProblemHash.generate(goal3, "project-void")
    
    print(f"Goal 1 hash: {hash1}")
    print(f"Goal 2 hash: {hash2}")
    print(f"Goal 3 hash: {hash3}")
    print(f"Hash 1 == Hash 2: {hash1 == hash2}")  # Should be True
    print(f"Hash 1 == Hash 3: {hash1 == hash3}")  # Should be False
    
    # Test problem extraction
    extracted = ProblemHash.extract_problem_from_goal(goal1)
    print(f"\nExtracted problem: {extracted}")
    
    # Test tracker
    tracker = ProblemTracker()
    hash_a, count_a = tracker.track_session(goal1, "the-living-fabric")
    hash_b, count_b = tracker.track_session(goal1, "the-living-fabric")
    hash_c, count_c = tracker.track_session(goal3, "project-void")
    
    print(f"\nSession 1: {count_a}")  # Should be 1
    print(f"Session 2 (same problem): {count_b}")  # Should be 2
    print(f"Session 3 (new problem): {count_c}")  # Should be 1
