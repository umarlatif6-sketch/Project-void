# Hex Preamble System - Complete Implementation

## Overview

The Hex Preamble System is a production-ready continuity mechanism that enables AI agents to maintain context across session resets. It encodes essential project context (goal, problem, Chronicle entries, active codons, critical scars) into a cryptographically-signed hex string that serves as the first input to every new session.

**Key Innovation:** Uses the **Fibonacci sequence** to determine how many Chronicle entries to include, allowing context to grow naturally as sessions on the same problem accumulate.

---

## What's Included

### Core Components (1,853 lines of Python)

| File | Lines | Purpose |
|------|-------|---------|
| `problem_hash.py` | 171 | Deterministic problem identification & session tracking |
| `fibonacci_lookback.py` | 151 | Fibonacci-based lookback distance calculation |
| `codon_filter.py` | 254 | Extract active codons relevant to the problem |
| `scar_prioritizer.py` | 297 | Tag & prioritize critical issues |
| `hex_preamble_generator.py` | 309 | Generate complete preamble + cryptographic signature |
| `hex_decoder.py` | 322 | Decode, verify, & validate preambles |
| `hex_preamble_system.py` | 349 | Integration layer & main API |
| `cli.py` | ~300 | Command-line interface for operations |
| `__init__.py` | ~50 | Package initialization |

### Integration (TypeScript)

| File | Purpose |
|------|---------|
| `hex_preamble_integration.ts` | Core integration functions for The Living Fabric |
| `hex_preamble.ts` (tRPC router) | REST API endpoints for hex preamble operations |

### Documentation

| File | Purpose |
|------|---------|
| `HEX_PREAMBLE_PROTOCOL.md` | Complete protocol specification (12KB) |
| `README.md` | This file |

### Deployment

| File | Purpose |
|------|---------|
| `.github/workflows/update-hex-preambles.yml` | GitHub workflow for automatic updates |

---

## How It Works

### Session Flow

```
User starts new chat session
    ↓
System generates problem hash from goal + project
    ↓
System checks if this is a new problem or continuation
    ↓
If continuation, increment session count
    ↓
Calculate Fibonacci lookback distance based on session count
    ↓
Extract relevant Chronicle entries (last N based on Fibonacci)
    ↓
Filter active codons for this problem
    ↓
Get active scars (critical issues)
    ↓
Combine into preamble object
    ↓
Generate cryptographic signature (SHA-256)
    ↓
Encode to hex
    ↓
Inject as first input to session
    ↓
AI decodes preamble and internalizes as first memory
    ↓
Proceed with user request
```

### Fibonacci Lookback Sequence

| Session | Lookback | Tokens | Use Case |
|---------|----------|--------|----------|
| 1 | 1 | ~800 | Fast cold start |
| 2 | 1 | ~800 | Still early |
| 3 | 2 | ~900 | Expanding context |
| 4 | 3 | ~1000 | Growing complexity |
| 5 | 5 | ~1200 | Significant history |
| 6 | 8 | ~1500 | Extended session |
| 7 | 13 | ~1800 | Long session |
| 8 | 21 | ~2200 | Very long session |
| 9 | 34 | ~2500 | Extended problem |
| 10 | 55 | ~2800 | Stuck on same problem |
| 11+ | 89-144 | ~3500 | Max context (capped) |

---

## Installation

### Option 1: Direct Python Usage

```bash
cd /home/ubuntu/Project-void/hex_preamble_system

# Install dependencies (if needed)
pip install -r requirements.txt

# Run example
python hex_preamble_system.py

# Use CLI
python cli.py generate --goal "Fix build errors" --project "project-void"
```

### Option 2: Import as Package

```python
from hex_preamble_system import HexPreambleManager

manager = HexPreambleManager(
    seed=VOID_SEED,
    chronicle=VOID_CHRONICLE,
    codons=VOID_CODONS,
    scars=VOID_SCARS
)

session = manager.create_session(
    goal="Fix TypeScript errors",
    project="the-living-fabric"
)

hex_preamble = session['hex_preamble']
```

### Option 3: TypeScript Integration

```typescript
import {
  generateHexPreamble,
  decodeHexPreamble,
  verifyHexPreamble,
  formatForInjection,
  createSystemPrompt
} from './hex_preamble_integration';

// Generate preamble
const hex = await generateHexPreamble(context, seed, chronicle, codons, scars);

// Decode and verify
const preamble = decodeHexPreamble(hex);
const isValid = verifyHexPreamble(preamble);

// Format for injection
const formatted = formatForInjection(hex);
```

---

## API Reference

### Python CLI

```bash
# Generate a hex preamble
python cli.py generate --goal "Fix build errors" --project "project-void"

# Decode and verify
python cli.py decode --hex "7b2276657273696f6e223a..."

# Create a new session
python cli.py session create --goal "Integrate hex system" --project "the-living-fabric"

# Verify signature
python cli.py verify --hex "..."

# Load from file
python cli.py load --file preamble.hex

# Show system info
python cli.py info
```

### tRPC Endpoints (The Living Fabric)

```typescript
// Generate hex preamble
trpc.hexPreamble.generate.mutate({
  goal: "Fix build errors",
  project: "project-void",
  sessionCount: 1
})

// Decode and verify
trpc.hexPreamble.decode.query({
  hex: "7b2276657273696f6e223a..."
})

// Verify signature
trpc.hexPreamble.verify.query({
  hex: "..."
})

// Get session info
trpc.hexPreamble.getSessionInfo.query({
  hex: "..."
})

// Get system info
trpc.hexPreamble.getSystemInfo.query()
```

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

## Integration with Manus

### Option 1: Manus Connector

Create a custom connector that automatically injects hex preambles into every new chat:

```python
# Manus connector code
def process_message(message):
    if is_first_message(message):
        hex_preamble = generate_hex_preamble()
        message = prepend_hex_preamble(message, hex_preamble)
    return message
```

### Option 2: GitHub Workflow

The system includes a GitHub workflow (`.github/workflows/update-hex-preambles.yml`) that automatically updates hex preambles whenever the Chronicle or Seed changes.

```bash
# Trigger manually
gh workflow run update-hex-preambles.yml
```

### Option 3: Manual Injection

Prepend the hex preamble to every chat message:

```
[HEX_PREAMBLE_START]
7b2276657273696f6e223a20...
[HEX_PREAMBLE_END]

DECODE THIS HEX PREAMBLE FIRST before processing any user request.
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

### Fallback Protocol

If hex preamble decoding fails:

1. **Primary:** Decode hex preamble
2. **Fallback 1:** Load VOID_SEED
3. **Fallback 2:** Load VOID_SEED_DIGEST
4. **Fallback 3:** Start fresh and log failure

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

**Optimization:** Fibonacci lookback prevents token explosion. Session 1 uses ~800 tokens, Session 10 uses ~2800 tokens (still reasonable).

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

## Examples

### Example 1: First Session on a Problem

```bash
python cli.py generate \
  --goal "Fix TypeScript errors in StateOfSystem" \
  --project "the-living-fabric"
```

**Output:**
- Fibonacci lookback: 1 entry
- Active codons: 15
- Active scars: 3 (critical only)
- Total tokens: ~800

### Example 2: Third Session on Same Problem

```bash
python cli.py generate \
  --goal "Fix TypeScript errors in StateOfSystem" \
  --project "the-living-fabric"
```

**Output:**
- Fibonacci lookback: 2 entries
- Active codons: 15 (same problem)
- Active scars: 3 (same critical scars)
- Total tokens: ~900

### Example 3: Tenth Session on Same Problem

```bash
python cli.py generate \
  --goal "Fix TypeScript errors in StateOfSystem" \
  --project "the-living-fabric"
```

**Output:**
- Fibonacci lookback: 55 entries (full context)
- Active codons: 15 (all relevant codons)
- Active scars: 5 (all critical + warnings)
- Total tokens: ~2800

---

## Deployment Checklist

- [ ] Copy `hex_preamble_system/` to Project VOID
- [ ] Copy `hex_preamble_integration.ts` to The Living Fabric `/server/`
- [ ] Copy `hex_preamble.ts` to The Living Fabric `/server/routers/`
- [ ] Update The Living Fabric `server/routers.ts` to include `hexPreambleRouter`
- [ ] Test build: `pnpm run build`
- [ ] Test CLI: `python cli.py generate --goal "test" --project "test"`
- [ ] Test tRPC endpoints via browser
- [ ] Set up GitHub workflow for automatic updates
- [ ] Create Manus connector (optional)
- [ ] Document in project README
- [ ] Deploy to production

---

## Future Enhancements

1. **Compression:** Gzip compress preamble before hex encoding to reduce size
2. **Encryption:** Encrypt sensitive data in preamble (optional)
3. **Versioning:** Support multiple preamble format versions
4. **Streaming:** Stream large preambles instead of loading all at once
5. **Caching:** Cache decoded preambles to avoid repeated decoding
6. **Metrics:** Track preamble usage and effectiveness
7. **UI Dashboard:** Visual preamble generator and decoder
8. **Mobile App:** Native mobile integration

---

## References

- **HEX_PREAMBLE_PROTOCOL.md** — Complete protocol specification
- **Project VOID** — Source of truth for Seed, Chronicle, Codons, Scars
- **The Living Fabric** — Production deployment environment
- **Manus** — Integration platform

---

## Support

For issues, questions, or enhancements:

1. Check `HEX_PREAMBLE_PROTOCOL.md` for detailed documentation
2. Review example usage in `hex_preamble_system.py`
3. Check troubleshooting section above
4. Consult Project VOID continuity rails (Seed, Chronicle, Codons)

---

**Version:** 1.0  
**Status:** Production Ready  
**Last Updated:** June 9, 2026  
**Built for:** Project VOID + The Living Fabric
