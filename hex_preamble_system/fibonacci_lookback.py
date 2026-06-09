"""
Fibonacci Lookback Calculator - Determines how many Chronicle entries to include.

Uses Fibonacci sequence to grow lookback distance naturally:
- Session 1: 1 entry
- Session 2: 1 entry
- Session 3: 2 entries
- Session 4: 3 entries
- Session 5: 5 entries
- Session 6: 8 entries
- Session 7: 13 entries
- Session 8: 21 entries
- Session 9: 34 entries
- Session 10: 55 entries
- Capped at Fibonacci(12) = 144 entries max
"""

from typing import List, Tuple


class FibonacciLookback:
    """Calculate Fibonacci-based lookback distances."""
    
    # Precomputed Fibonacci sequence (up to index 12 for cap)
    FIBONACCI_SEQUENCE = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]
    MAX_FIBONACCI_INDEX = 12
    MAX_LOOKBACK_ENTRIES = 144
    
    @staticmethod
    def generate_fibonacci(n: int) -> int:
        """
        Generate the nth Fibonacci number.
        
        Args:
            n: Position in Fibonacci sequence (1-indexed)
        
        Returns:
            The nth Fibonacci number
        """
        if n <= 0:
            return 0
        if n == 1 or n == 2:
            return 1
        
        a, b = 1, 1
        for _ in range(n - 2):
            a, b = b, a + b
        return b
    
    @staticmethod
    def get_lookback_distance(session_count: int) -> int:
        """
        Get the lookback distance for a given session count.
        
        Args:
            session_count: Number of sessions on the same problem (1-indexed)
        
        Returns:
            Number of Chronicle entries to include (capped at 144)
        """
        # Cap at Fibonacci(12) = 144
        capped_session = min(session_count, FibonacciLookback.MAX_FIBONACCI_INDEX)
        
        # Get Fibonacci number for this position
        if capped_session <= len(FibonacciLookback.FIBONACCI_SEQUENCE):
            return FibonacciLookback.FIBONACCI_SEQUENCE[capped_session - 1]
        
        # Fallback (shouldn't reach here with cap)
        return FibonacciLookback.MAX_LOOKBACK_ENTRIES
    
    @staticmethod
    def get_lookback_entries(
        chronicle_entries: List[dict],
        session_count: int
    ) -> List[dict]:
        """
        Get the appropriate number of Chronicle entries based on session count.
        
        Args:
            chronicle_entries: Full list of Chronicle entries (in chronological order)
            session_count: Number of sessions on the same problem
        
        Returns:
            Sliced list of relevant Chronicle entries
        """
        lookback_distance = FibonacciLookback.get_lookback_distance(session_count)
        
        # Return the last N entries
        if len(chronicle_entries) <= lookback_distance:
            return chronicle_entries
        
        return chronicle_entries[-lookback_distance:]
    
    @staticmethod
    def get_fibonacci_sequence(max_sessions: int = 20) -> List[Tuple[int, int]]:
        """
        Get a mapping of session count to lookback distance.
        
        Args:
            max_sessions: Maximum session count to generate
        
        Returns:
            List of (session_count, lookback_distance) tuples
        """
        result = []
        for session in range(1, max_sessions + 1):
            lookback = FibonacciLookback.get_lookback_distance(session)
            result.append((session, lookback))
        return result
    
    @staticmethod
    def explain_lookback(session_count: int) -> str:
        """
        Generate a human-readable explanation of the lookback.
        
        Args:
            session_count: Number of sessions on the same problem
        
        Returns:
            Explanation string
        """
        lookback_distance = FibonacciLookback.get_lookback_distance(session_count)
        
        if session_count <= 2:
            reason = "Early session - minimal lookback for fast cold start"
        elif session_count <= 5:
            reason = "Mid-session - expanding context as complexity grows"
        elif session_count <= 10:
            reason = "Extended session - exponential lookback to capture problem trajectory"
        else:
            reason = "Long session - maximum lookback (capped at 144 entries)"
        
        return (
            f"Session {session_count}: Including {lookback_distance} Chronicle entries. "
            f"{reason}"
        )


# Example usage
if __name__ == '__main__':
    print("Fibonacci Lookback Sequence:")
    print("-" * 50)
    
    sequence = FibonacciLookback.get_fibonacci_sequence(15)
    for session_count, lookback_distance in sequence:
        explanation = FibonacciLookback.explain_lookback(session_count)
        print(f"{explanation}")
    
    print("\n" + "-" * 50)
    print(f"Maximum lookback distance: {FibonacciLookback.MAX_LOOKBACK_ENTRIES} entries")
    print(f"Fibonacci sequence capped at index: {FibonacciLookback.MAX_FIBONACCI_INDEX}")
