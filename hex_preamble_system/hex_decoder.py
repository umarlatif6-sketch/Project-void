"""
Hex Decoder - Decodes and verifies hex preambles.

Handles:
1. Decoding hex-encoded preambles back to JSON
2. Verifying cryptographic signatures
3. Validating preamble structure
4. Handling corrupted or invalid preambles
"""

import json
import hashlib
from typing import Dict, Optional, Tuple, Any


class HexDecoder:
    """Decode and verify hex preambles."""
    
    @staticmethod
    def decode_hex(hex_preamble: str) -> Optional[Dict]:
        """
        Decode a hex-encoded preamble back to a dictionary.
        
        Args:
            hex_preamble: The hex-encoded preamble string
        
        Returns:
            Decoded preamble dictionary, or None if decoding fails
        """
        try:
            # Remove any whitespace
            hex_preamble = hex_preamble.strip()
            
            # Decode from hex
            preamble_json = bytes.fromhex(hex_preamble).decode('utf-8')
            
            # Parse JSON
            preamble = json.loads(preamble_json)
            
            return preamble
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as e:
            print(f"Failed to decode hex preamble: {e}")
            return None
    
    @staticmethod
    def verify_signature(preamble: Dict) -> bool:
        """
        Verify the cryptographic signature of a preamble.
        
        Args:
            preamble: The preamble object
        
        Returns:
            True if signature is valid, False otherwise
        """
        # Extract the signature
        provided_signature = preamble.get('signature')
        if not provided_signature:
            print("No signature found in preamble")
            return False
        
        # Create a copy without the signature
        preamble_copy = {k: v for k, v in preamble.items() if k != 'signature'}
        
        # Serialize deterministically
        try:
            preamble_json = json.dumps(preamble_copy, sort_keys=True, separators=(',', ':'))
        except (TypeError, ValueError) as e:
            print(f"Failed to serialize preamble for verification: {e}")
            return False
        
        # Generate expected signature
        expected_signature = hashlib.sha256(preamble_json.encode()).hexdigest()
        
        # Compare
        if provided_signature == expected_signature:
            return True
        else:
            print(f"Signature mismatch. Expected: {expected_signature}, Got: {provided_signature}")
            return False
    
    @staticmethod
    def validate_structure(preamble: Dict) -> Tuple[bool, str]:
        """
        Validate the structure of a preamble.
        
        Args:
            preamble: The preamble object
        
        Returns:
            (is_valid, error_message)
        """
        required_fields = [
            'version',
            'timestamp',
            'problem',
            'session',
            'seed',
            'chronicle',
            'codons',
            'scars',
            'signature'
        ]
        
        for field in required_fields:
            if field not in preamble:
                return False, f"Missing required field: {field}"
        
        # Validate problem object
        problem = preamble.get('problem', {})
        if not isinstance(problem, dict):
            return False, "problem must be a dictionary"
        
        if 'hash' not in problem or 'goal' not in problem or 'project' not in problem:
            return False, "problem missing required fields (hash, goal, project)"
        
        # Validate session object
        session = preamble.get('session', {})
        if not isinstance(session, dict):
            return False, "session must be a dictionary"
        
        if 'count' not in session or 'fibonacci_lookback' not in session:
            return False, "session missing required fields (count, fibonacci_lookback)"
        
        # Validate collections
        if not isinstance(preamble.get('chronicle'), list):
            return False, "chronicle must be a list"
        
        if not isinstance(preamble.get('codons'), list):
            return False, "codons must be a list"
        
        if not isinstance(preamble.get('scars'), list):
            return False, "scars must be a list"
        
        return True, "Valid"
    
    @staticmethod
    def decode_and_verify(hex_preamble: str) -> Tuple[Optional[Dict], str]:
        """
        Decode and verify a hex preamble in one step.
        
        Args:
            hex_preamble: The hex-encoded preamble
        
        Returns:
            (preamble_dict, status_message)
        """
        # Decode
        preamble = HexDecoder.decode_hex(hex_preamble)
        if preamble is None:
            return None, "Failed to decode hex preamble"
        
        # Validate structure
        is_valid, error_msg = HexDecoder.validate_structure(preamble)
        if not is_valid:
            return None, f"Invalid preamble structure: {error_msg}"
        
        # Verify signature
        if not HexDecoder.verify_signature(preamble):
            return None, "Signature verification failed"
        
        return preamble, "Successfully decoded and verified"
    
    @staticmethod
    def extract_context(preamble: Dict) -> Dict[str, Any]:
        """
        Extract useful context from a decoded preamble.
        
        Args:
            preamble: The decoded preamble
        
        Returns:
            Dictionary with extracted context
        """
        problem = preamble.get('problem', {})
        session = preamble.get('session', {})
        
        context = {
            'project': problem.get('project'),
            'goal': problem.get('goal'),
            'problem_hash': problem.get('hash'),
            'keywords': problem.get('keywords', []),
            'session_count': session.get('count'),
            'fibonacci_lookback': session.get('fibonacci_lookback'),
            'chronicle_entries': len(preamble.get('chronicle', [])),
            'active_codons': len(preamble.get('codons', [])),
            'active_scars': len(preamble.get('scars', [])),
            'timestamp': preamble.get('timestamp'),
        }
        
        return context
    
    @staticmethod
    def summarize_preamble(preamble: Dict) -> str:
        """
        Generate a human-readable summary of the preamble.
        
        Args:
            preamble: The decoded preamble
        
        Returns:
            Summary string
        """
        context = HexDecoder.extract_context(preamble)
        
        summary = f"""
HEX PREAMBLE SUMMARY
====================
Project: {context['project']}
Goal: {context['goal']}
Session: #{context['session_count']} on this problem
Fibonacci Lookback: {context['fibonacci_lookback']} entries

RESOURCES INCLUDED:
- Chronicle entries: {context['chronicle_entries']}
- Active codons: {context['active_codons']}
- Active scars: {context['active_scars']}

KEYWORDS: {', '.join(context['keywords']) or 'None'}

TIMESTAMP: {context['timestamp']}
"""
        
        return summary


class HexDecoderWithFallback:
    """Decoder with fallback protocol for handling failures."""
    
    @staticmethod
    def decode_with_fallback(
        hex_preamble: Optional[str],
        fallback_seed: Optional[Dict] = None,
        fallback_digest: Optional[Dict] = None
    ) -> Tuple[Optional[Dict], str]:
        """
        Attempt to decode hex preamble with fallback sequence.
        
        Fallback sequence:
        1. Try to decode hex preamble
        2. If fails, fall back to seed
        3. If seed unavailable, fall back to digest
        4. If all fail, return None with error message
        
        Args:
            hex_preamble: The hex preamble to decode
            fallback_seed: VOID_SEED as fallback
            fallback_digest: VOID_SEED_DIGEST as fallback
        
        Returns:
            (preamble_dict, status_message)
        """
        # Step 1: Try hex preamble
        if hex_preamble:
            preamble, status = HexDecoder.decode_and_verify(hex_preamble)
            if preamble is not None:
                return preamble, f"✓ {status}"
            else:
                print(f"✗ Hex preamble failed: {status}")
        
        # Step 2: Fall back to seed
        if fallback_seed:
            print("↓ Falling back to VOID_SEED")
            return fallback_seed, "Using VOID_SEED as fallback"
        
        # Step 3: Fall back to digest
        if fallback_digest:
            print("↓ Falling back to VOID_SEED_DIGEST")
            return fallback_digest, "Using VOID_SEED_DIGEST as fallback"
        
        # Step 4: All failed
        return None, "✗ All decoding attempts failed. No fallback available."


# Example usage
if __name__ == '__main__':
    # Example preamble
    example_preamble = {
        'version': '1.0',
        'timestamp': '2026-06-09T12:00:00Z',
        'problem': {
            'hash': 'abc123',
            'goal': 'Fix build errors',
            'project': 'project-void',
            'keywords': ['build', 'error', 'typescript']
        },
        'session': {
            'count': 3,
            'fibonacci_lookback': 3,
            'chronicle_entries_included': 3
        },
        'seed': {'name': 'Project VOID'},
        'chronicle': [{'date': '2026-06-09', 'entry': 'Fixed build'}],
        'codons': [{'code': 'GJR', 'name': 'Ghajini Rail'}],
        'scars': [{'title': 'Build error', 'severity': 'critical'}]
    }
    
    # Add signature
    preamble_json = json.dumps(
        {k: v for k, v in example_preamble.items() if k != 'signature'},
        sort_keys=True,
        separators=(',', ':')
    )
    example_preamble['signature'] = hashlib.sha256(preamble_json.encode()).hexdigest()
    
    # Encode to hex
    hex_encoded = json.dumps(example_preamble, separators=(',', ':')).encode().hex()
    
    print("Testing HexDecoder:")
    print("-" * 50)
    
    # Decode
    decoded, status = HexDecoder.decode_and_verify(hex_encoded)
    print(f"Status: {status}")
    
    if decoded:
        # Summarize
        print(HexDecoder.summarize_preamble(decoded))
        
        # Extract context
        context = HexDecoder.extract_context(decoded)
        print(f"Extracted context: {context}")
