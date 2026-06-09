# Hex Preamble Protocol

## Overview

The Hex Preamble Protocol is a continuity system that enables AI agents to maintain context across session resets. Instead of starting each new chat session with zero memory, the system encodes the essential context (goal, problem, Chronicle entries, active codons, critical scars) into a cryptographically-signed hex string that serves as the first input to every new session.

**Key Innovation:** Uses the **Fibonacci sequence** to determine how many Chronicle entries to include, allowing the lookback distance to grow naturally as sessions on the same problem accumulate.

---

## Architecture

### Components

1. **Problem Hash** (`problem_hash.py`)
   - Generates deterministic hash of the current problem
   - Tracks session count per problem (resets when problem changes)
   - Enables continuity across multiple sessions on the same issue

2. **Fibonacci Lookback** (`fibonacci_lookback.py`)
   - Calculates lookback distance based on session count
   - Session 1-2: 1 entry (fast cold start)
   - Session 3-5: 2-5 entries (expanding context)
   - Session 6+: 8+ entries (exponential growth, capped at 144)

3. **Codon Filter** (`codon_filter.py`)
   - Extracts active codons relevant to the current problem
   - Filters by project and problem keywords
   - Returns top 15-20 most relevant codons

4. **Scar Prioritizer** (`scar_prioritizer.py`)
   - Identifies critical issues that need to be addressed
   - Tags scars as critical, warning, resolved, or info
   - Prioritizes by severity and recency

5. **Hex Preamble Generator** (`hex_preamble_generator.py`)
   - Combines all components into a single preamble object
   - Encodes to hex format
   - Generates cryptographic signature
   - Creates system prompt for the session

6. **Hex Decoder** (`hex_decoder.py`)
   - Decodes hex preambles back to JSON
   - Verifies cryptographic signatures
   - Validates preamble structure
   - Handles corrupted or invalid preambles

7. **Integration Layer** (`hex_preamble_system.py`)
   - Main entry point for all operations
   - Manages session history and problem tracking
   - Provides high-level API for creating and loading sessions

---

## Data Flow

### Session Creation

```
1. User starts a new chat session
   ↓
2. System generates problem hash from goal + project
   ↓
3. System checks if this is a new problem or continuation
   ↓
4. If continuation, increment session count
   ↓
5. Calculate Fibonacci lookback distance
   ↓
6. Extract relevant Chronicle entries (last N based on Fibonacci)
   ↓
7. Filter active codons for this problem
   ↓
8. Get active scars (critical issues)
   ↓
9. Combine into preamble object
   ↓
10. Generate cryptographic signature
    ↓
11. Encode to hex
    ↓
12. Inject as first input to session
```

### Session Decoding

```
1. AI receives hex preamble as first input
   ↓
2. Decode hex to JSON
   ↓
3. Verify cryptographic signature
   ↓
4. Validate preamble structure
   ↓
5. Extract context (problem, session count, keywords)
   ↓
6. Load Chronicle entries
   ↓
7. Load active codons
   ↓
8. Load active scars
   ↓
9. Internalize as first memory
   ↓
10. Proceed with user request
```

---

## Fibonacci Lookback Sequence

The system uses Fibonacci numbers to determine how many Chronicle entries to include:

| Session | Lookback | Reason |
|---------|----------|--------|
| 1 | 1 | Fast cold start, minimal overhead |
| 2 | 1 | Still early, keep it light |
| 3 | 2 | Starting to expand context |
| 4 | 3 | Problem complexity growing |
| 5 | 5 | Significant history needed |
| 6 | 8 | Extended session, need more context |
| 7 | 13 | Long session, exponential growth |
| 8 | 21 | Very long session, substantial history |
| 9 | 34 | Extended problem, deep context |
| 10 | 55 | Stuck on same problem, max context |
| 11+ | 89-144 | Capped at 144 entries (Fibonacci 12) |

**Why Fibonacci?**
- Grows exponentially but naturally
- Matches how problem complexity grows
- Prevents token explosion (capped at 144)
- Intuitive: more sessions = more lookback

---

## Preamble Structure

```json
{
  "version": "1.0",
  "timestamp": "2026-06-09T12:00:00Z",
  "problem": {
    "hash": "abc123def456...",
    "goal": "Fix TypeScript errors in StateOfSystem",
    "project": "the-living-fabric",
    "keywords": ["typescript", "error", "stateofystem"]
  },
  "session": {
    "count": 3,
    "fibonacci_lookback": 3,
    "chronicle_entries_included": 3
  },
  "seed": { /* VOID_SEED object */ },
  "chronicle": [ /* Last N entries based on Fibonacci */ ],
  "codons": [ /* 15-20 active codons relevant to problem */ ],
  "scars": [ /* 5 most critical scars */ ],
  "metadata": {
    "total_chronicle_entries": 247,
    "total_codons_available": 203,
    "total_scars_available": 18
  },
  "signature": "sha256_hex_hash_of_preamble_without_signature"
}
```

---

## Usage

### Creating a Session

```python
from hex_preamble_system import HexPreambleManager

# Initialize with Project VOID data
manager = HexPreambleManager(
    seed=VOID_SEED,
    chronicle=VOID_CHRONICLE,
    codons=VOID_CODONS,
    scars=VOID_SCARS
)

# Create a session
session = manager.create_session(
    goal="Fix build errors in simulation.ts",
    project="project-void"
)

# Get hex preamble for injection
hex_preamble = session['hex_preamble']

# Get system prompt
system_prompt = session['system_prompt']
```

### Injecting into Chat

```
[HEX_PREAMBLE_START]
7b2276657273696f6e223a20...
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
```

### Decoding a Preamble

```python
from hex_preamble_system import HexPreambleManager

manager = HexPreambleManager(...)

# Load a session from hex preamble
session, status = manager.verify_and_load_session(hex_preamble)

if session:
    print(f"✓ Session loaded: {status}")
    print(session['summary'])
else:
    print(f"✗ Failed to load: {status}")
```

---

## Fallback Protocol

If hex preamble decoding fails:

1. **Primary:** Decode hex preamble
2. **Fallback 1:** Load VOID_SEED
3. **Fallback 2:** Load VOID_SEED_DIGEST
4. **Fallback 3:** Start fresh and log failure

```python
from hex_decoder import HexDecoderWithFallback

preamble, status = HexDecoderWithFallback.decode_with_fallback(
    hex_preamble=hex_preamble,
    fallback_seed=VOID_SEED,
    fallback_digest=VOID_SEED_DIGEST
)
```

---

## Integration with Manus

### Option 1: Manus Connector

Create a custom connector that automatically injects the hex preamble into every new chat:

```python
# Manus connector code
def process_message(message):
    if is_first_message(message):
        hex_preamble = generate_hex_preamble()
        message = prepend_hex_preamble(message, hex_preamble)
    return message
```

### Option 2: CLI Tool

```bash
# Generate hex preamble for current session
manus-hex-preamble generate \
  --goal "Fix build errors" \
  --project "project-void" \
  --session-count 3

# Decode and verify a hex preamble
manus-hex-preamble decode \
  --hex "7b2276657273696f6e223a..."

# Create a new session
manus-hex-preamble session create \
  --goal "Integrate hex system" \
  --project "the-living-fabric"
```

### Option 3: GitHub Workflow

Automatically update hex preambles when Chronicle changes:

```yaml
name: Update Hex Preambles
on:
  push:
    paths:
      - 'VOID_CHRONICLE.md'

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - run: python hex_preamble_system.py --update-all
      - run: git commit -am "Update hex preambles"
      - run: git push
```

---

## Security

### Signature Verification

Every preamble is signed with SHA-256. Before using a preamble:

```python
from hex_decoder import HexDecoder

preamble, status = HexDecoder.decode_and_verify(hex_preamble)
# Returns None if signature is invalid
```

### Immutability

Once encoded, a preamble cannot be modified without invalidating the signature. This ensures:
- Problem context cannot be corrupted
- Chronicle entries cannot be altered
- Codons cannot be swapped
- Scars cannot be hidden

---

## Performance

### Token Usage

Typical preamble sizes:

| Component | Size (chars) | Tokens (approx) |
|-----------|--------------|-----------------|
| Problem | 200 | 50 |
| Session | 100 | 25 |
| Seed | 500 | 125 |
| Chronicle (5 entries) | 1000 | 250 |
| Codons (15) | 1500 | 375 |
| Scars (5) | 800 | 200 |
| Metadata | 300 | 75 |
| **Total** | ~4800 | ~1100 |

**Optimization:** Fibonacci lookback prevents token explosion. Session 1 uses ~200 tokens, Session 10 uses ~1100 tokens (still reasonable).

---

## Examples

### Example 1: First Session on a Problem

```
Session 1: "Fix TypeScript errors in StateOfSystem"
- Fibonacci lookback: 1 entry
- Active codons: 15
- Active scars: 3 (critical only)
- Total tokens: ~800
```

### Example 2: Third Session on Same Problem

```
Session 3: "Fix TypeScript errors in StateOfSystem" (continued)
- Fibonacci lookback: 2 entries
- Active codons: 15 (same problem)
- Active scars: 3 (same critical scars)
- Total tokens: ~900
```

### Example 3: Tenth Session on Same Problem

```
Session 10: "Fix TypeScript errors in StateOfSystem" (still stuck)
- Fibonacci lookback: 55 entries (full context)
- Active codons: 15 (all relevant codons)
- Active scars: 5 (all critical + warnings)
- Total tokens: ~2500
```

---

## Troubleshooting

### Hex Preamble Won't Decode

```
Error: Failed to decode hex preamble

Solution:
1. Check if hex string is valid (should be lowercase alphanumeric)
2. Verify no whitespace or special characters
3. Try fallback protocol (load VOID_SEED)
4. Check signature verification
```

### Signature Mismatch

```
Error: Signature verification failed

Solution:
1. Preamble may have been corrupted
2. Preamble may have been tampered with
3. Use fallback protocol
4. Generate new preamble
```

### Session Count Not Incrementing

```
Problem: Same problem hash not being recognized

Solution:
1. Check problem hash generation (goal + project)
2. Verify problem_hash.py is using correct normalization
3. Check if problem keywords changed
4. Reset problem tracker if needed
```

---

## Future Enhancements

1. **Compression:** Gzip compress preamble before hex encoding to reduce size
2. **Encryption:** Encrypt sensitive data in preamble (optional)
3. **Versioning:** Support multiple preamble format versions
4. **Streaming:** Stream large preambles instead of loading all at once
5. **Caching:** Cache decoded preambles to avoid repeated decoding
6. **Metrics:** Track preamble usage and effectiveness

---

## References

- `problem_hash.py` — Problem identification and session tracking
- `fibonacci_lookback.py` — Fibonacci-based lookback calculation
- `codon_filter.py` — Codon filtering and prioritization
- `scar_prioritizer.py` — Scar tagging and prioritization
- `hex_preamble_generator.py` — Preamble generation and encoding
- `hex_decoder.py` — Preamble decoding and verification
- `hex_preamble_system.py` — Integration layer and main API

---

**Version:** 1.0  
**Last Updated:** June 9, 2026  
**Status:** Production Ready
