#!/usr/bin/env python3
"""
Hex Preamble CLI - Command-line interface for hex preamble operations.

Usage:
    python cli.py generate --goal "Fix build errors" --project "project-void"
    python cli.py decode --hex "7b2276657273696f6e223a..."
    python cli.py session create --goal "..." --project "..."
    python cli.py verify --hex "..."
"""

import argparse
import json
import sys
from typing import Optional
from pathlib import Path

from hex_preamble_system import HexPreambleManager, HexPreambleSystem
from hex_decoder import HexDecoder


class HexPreambleCLI:
    """Command-line interface for hex preamble operations."""
    
    def __init__(self):
        """Initialize CLI."""
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            description='Hex Preamble System - Continuity across session resets',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog='''
Examples:
  # Generate a hex preamble
  python cli.py generate --goal "Fix build errors" --project "project-void"
  
  # Decode and verify a hex preamble
  python cli.py decode --hex "7b2276657273696f6e223a..."
  
  # Create a new session
  python cli.py session create --goal "Integrate hex system" --project "the-living-fabric"
  
  # Verify a hex preamble
  python cli.py verify --hex "..."
  
  # Load from file
  python cli.py load --file preamble.hex
            '''
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Command to run')
        
        # Generate command
        generate_parser = subparsers.add_parser('generate', help='Generate a hex preamble')
        generate_parser.add_argument('--goal', required=True, help='Problem/goal statement')
        generate_parser.add_argument('--project', required=True, help='Project identifier')
        generate_parser.add_argument('--context', help='Optional context (JSON)')
        generate_parser.add_argument('--output', help='Output file (optional)')
        
        # Decode command
        decode_parser = subparsers.add_parser('decode', help='Decode a hex preamble')
        decode_parser.add_argument('--hex', required=True, help='Hex-encoded preamble')
        decode_parser.add_argument('--output', help='Output file (optional)')
        
        # Verify command
        verify_parser = subparsers.add_parser('verify', help='Verify a hex preamble')
        verify_parser.add_argument('--hex', required=True, help='Hex-encoded preamble')
        
        # Session command
        session_parser = subparsers.add_parser('session', help='Session operations')
        session_subparsers = session_parser.add_subparsers(dest='session_command')
        
        create_session = session_subparsers.add_parser('create', help='Create a new session')
        create_session.add_argument('--goal', required=True, help='Problem/goal statement')
        create_session.add_argument('--project', required=True, help='Project identifier')
        create_session.add_argument('--output', help='Output file (optional)')
        
        # Load command
        load_parser = subparsers.add_parser('load', help='Load preamble from file')
        load_parser.add_argument('--file', required=True, help='Preamble file path')
        
        # Info command
        info_parser = subparsers.add_parser('info', help='Show system information')
        
        return parser
    
    def run(self, args: Optional[list] = None) -> int:
        """Run the CLI."""
        parsed_args = self.parser.parse_args(args)
        
        if not parsed_args.command:
            self.parser.print_help()
            return 1
        
        try:
            if parsed_args.command == 'generate':
                return self.cmd_generate(parsed_args)
            elif parsed_args.command == 'decode':
                return self.cmd_decode(parsed_args)
            elif parsed_args.command == 'verify':
                return self.cmd_verify(parsed_args)
            elif parsed_args.command == 'session':
                return self.cmd_session(parsed_args)
            elif parsed_args.command == 'load':
                return self.cmd_load(parsed_args)
            elif parsed_args.command == 'info':
                return self.cmd_info(parsed_args)
            else:
                self.parser.print_help()
                return 1
        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            return 1
    
    def cmd_generate(self, args) -> int:
        """Generate a hex preamble."""
        print(f"Generating hex preamble...")
        print(f"  Goal: {args.goal}")
        print(f"  Project: {args.project}")
        
        # For demo, generate a simple preamble
        preamble = {
            'version': '1.0',
            'goal': args.goal,
            'project': args.project,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }
        
        hex_encoded = json.dumps(preamble).encode().hex()
        
        print(f"\n✓ Generated hex preamble:")
        print(f"  {hex_encoded[:80]}...")
        
        if args.output:
            Path(args.output).write_text(hex_encoded)
            print(f"  Saved to: {args.output}")
        
        return 0
    
    def cmd_decode(self, args) -> int:
        """Decode a hex preamble."""
        print(f"Decoding hex preamble...")
        
        preamble, status = HexDecoder.decode_and_verify(args.hex)
        
        if preamble:
            print(f"✓ {status}")
            print(f"\n{HexDecoder.summarize_preamble(preamble)}")
            
            if args.output:
                Path(args.output).write_text(json.dumps(preamble, indent=2))
                print(f"Saved to: {args.output}")
            
            return 0
        else:
            print(f"✗ {status}")
            return 1
    
    def cmd_verify(self, args) -> int:
        """Verify a hex preamble."""
        print(f"Verifying hex preamble...")
        
        preamble = HexDecoder.decode_hex(args.hex)
        if not preamble:
            print(f"✗ Failed to decode hex preamble")
            return 1
        
        is_valid, error_msg = HexDecoder.validate_structure(preamble)
        if not is_valid:
            print(f"✗ Invalid structure: {error_msg}")
            return 1
        
        is_signed = HexDecoder.verify_signature(preamble)
        if not is_signed:
            print(f"✗ Signature verification failed")
            return 1
        
        print(f"✓ Preamble is valid and signed")
        return 0
    
    def cmd_session(self, args) -> int:
        """Handle session operations."""
        if args.session_command == 'create':
            print(f"Creating new session...")
            print(f"  Goal: {args.goal}")
            print(f"  Project: {args.project}")
            
            # For demo
            session = {
                'goal': args.goal,
                'project': args.project,
                'created_at': __import__('datetime').datetime.now().isoformat()
            }
            
            print(f"\n✓ Session created")
            print(json.dumps(session, indent=2))
            
            if args.output:
                Path(args.output).write_text(json.dumps(session, indent=2))
                print(f"Saved to: {args.output}")
            
            return 0
        
        return 1
    
    def cmd_load(self, args) -> int:
        """Load preamble from file."""
        print(f"Loading preamble from: {args.file}")
        
        try:
            hex_preamble = Path(args.file).read_text().strip()
            preamble, status = HexDecoder.decode_and_verify(hex_preamble)
            
            if preamble:
                print(f"✓ {status}")
                print(f"\n{HexDecoder.summarize_preamble(preamble)}")
                return 0
            else:
                print(f"✗ {status}")
                return 1
        except FileNotFoundError:
            print(f"✗ File not found: {args.file}")
            return 1
    
    def cmd_info(self, args) -> int:
        """Show system information."""
        print("""
HEX PREAMBLE SYSTEM - Information
==================================

Components:
  - problem_hash.py: Problem identification & session tracking
  - fibonacci_lookback.py: Fibonacci-based lookback calculation
  - codon_filter.py: Active codon extraction
  - scar_prioritizer.py: Critical issue prioritization
  - hex_preamble_generator.py: Preamble generation & encoding
  - hex_decoder.py: Preamble decoding & verification
  - hex_preamble_system.py: Integration layer

Features:
  ✓ Deterministic problem hashing
  ✓ Fibonacci-based lookback (1 → 1 → 2 → 3 → 5 → 8 → 13 → 21 → 34 → 55 → 89 → 144)
  ✓ Cryptographic signature verification
  ✓ Fallback protocol for failures
  ✓ Token-optimized context inclusion

Fibonacci Lookback Sequence:
  Session 1: 1 entry (≈800 tokens)
  Session 3: 2 entries (≈900 tokens)
  Session 5: 5 entries (≈1200 tokens)
  Session 10: 55 entries (≈2500 tokens)
  Session 12+: 144 entries (capped)

For more information, see: HEX_PREAMBLE_PROTOCOL.md
        """)
        return 0


def main():
    """Main entry point."""
    cli = HexPreambleCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
