# PROJECT VOID

## Objective: Sovereign Data Transmission via Biophony Mesh

PROJECT VOID is a research-grade signal intelligence platform that utilizes a 3-shelf acoustic ecosystem to fold high-density data into mundane environmental audio. By simulating **Salt Water Density** in a 16-bit air medium, it achieves a **5x Temporal Vortex** (1 hour of audio = 5 hours of raw LSB capacity).

---

## The 10-20-970 Architecture

| Shelf | Agents | Frequency | Role |
|-------|--------|-----------|------|
| **Low-Shelf (Whales)** | 10 | 15-50 Hz | Infra-bass sine-sweeps. The stable "Chassis" for heavy LSB1 blocks (Videos/Binaries). |
| **Mid-Shelf (Birds)** | 20 | 300-800 Hz | Percussive transients tuned to 432 Hz harmonics. **Floating Parity Headers** -- rhythmic start/stop triggers. |
| **High-Shelf (Insects)** | 970 | 2-12 kHz | Dense cicada/cricket chorus. The **Noise Floor Silt** where LSB2 compressed data is buried. Zero inter-pulse silence. |

**Total: 1,000 synchronized acoustic agents per carrier.**

---

## Key Innovations

### Sympathetic Resonance
A Hilbert-transform envelope follower that modulates insect chirp density based on whale amplitude. When the low-frequency "mass" increases, the high-frequency masking density tightens -- the shelves interlock mathematically, not just layer independently.

### Sapphire Thread (ZHR.V)
Glow triggers only at the 432 Hz convergence point across all three shelves, confirming a **1:1 carrier-to-payload ratio** (~189 MB per 1-hour stereo carrier at LSB2 with 5x density).

### Shadow Layer
A -30 dB Brownian noise camouflage that masks the carrier as "badly recorded nature audio." To casual listeners or basic AI monitors, the file sounds like a poorly recorded park video.

### Chirp-Synced Encoding
Data placement synchronized to chirp peak positions in the insect shelf. The `.chirpmap.npy` sidecar provides a deterministic "GPS" for the encoder, placing data chunks exactly where acoustic masking is densest.

### ChaCha20 Encrypted Headers
64-byte headers with filename, data size, MD5 checksum, and scatter mode flags -- all encrypted with ChaCha20 stream cipher. Ghost offset embedding adds positional security.

### Dual Compression
Automatic selection between zlib (level 9) and lzma (preset 9) with memory guarding. The engine picks whichever achieves better compression for each payload.

---

## Carrier Styles

| Style | Shelves | Channels | Density Multiplier |
|-------|---------|----------|--------------------|
| `midnight_pond` | Whale + Bird + Insect | Stereo | 5x |
| `biophony_mesh` | Whale + Bird + Insect | Stereo | 5x |
| `cicada_wall` | Insect only (970) | Mono | 5x |
| `cricket_pulse` | Insect only (200) | Mono | 2.5x |
| `drone` | 432 Hz tone | Mono | 1x |
| `harmonic` | Multi-harmonic | Mono | 1x |
| `pink_noise` | Broadband noise | Mono | 1x |
| `stereo_pocket` | Adriana Pocket | Stereo | 1x |

---

## Scatter Modes

| Mode | Description |
|------|-------------|
| **Linear** | Standard sequential LSB embedding |
| **Fly Jitter** | Anti-forensic temporal scatter -- data fragments distributed non-uniformly |
| **Vortex** | 432 Hz harmonic spiral -- 5 arms at golden angle spacing |
| **Chirp Sync** | Data synced to chirp peaks in Insect-Pulse/Biophony carriers |

Scatter modes are mutually exclusive. The Divided Protocol auto-selects Chirp Sync for biophony carriers with `.chirpmap.npy` sidecars.

---

## Capacity Reference (1-Hour Carriers)

| Style | WAV Size | Raw LSB2 | Effective LSB2 (with density) |
|-------|----------|----------|-------------------------------|
| `drone` (mono) | ~303 MB | ~37.9 MB | ~37.9 MB |
| `cicada_wall` (mono) | ~303 MB | ~37.9 MB | ~189.3 MB |
| `midnight_pond` (stereo) | ~606 MB | ~75.7 MB | ~378.5 MB |

---

## The Divided Operational Protocol

A 5-step axiomatic pipeline that orchestrates full encode operations:

```
SLM.V --> TRK.A --> ZHR.V --> KTM.A --> JDR.A
```

1. **SLM.V (Initialize)** -- System health verification
2. **TRK.A (Calibrate)** -- 432 Hz resonance calibration on carrier
3. **ZHR.V (Observe)** -- Radiance axiom check; biophony detection; Sapphire Thread / MAX_GLOW
4. **KTM.A (Inject)** -- Steganography encode with auto-selected scatter mode
5. **JDR.A (Commit)** -- Transaction logged to Root-Chronicle; wallet charged

---

## Al-Jabr Code (Root-Pattern Logic)

18 trilateral roots across 9 domains:

| Domain | Roots | Function |
|--------|-------|----------|
| Aqua | HYA, GDH, DFQ | Water management, flow control |
| Flywheel | QDR, HRR, TRK | Energy, rotation, motion tracking |
| Silk | WSL, NZM | Connection, organization |
| Pressure | HFZ, DGT, NFD | Safety, precision, tunneling |
| Economy | QSB | Financial autonomy (Wallet) |
| System | BTR, SHR, SLM | Health, reporting, diagnostics |
| Steganography | KTM | Data concealment |
| Chronicle | JDR | Persistent memory |
| Radiance | ZHR | Light/glow correlation |

7 verb patterns: **A** (Activate), **D** (Deactivate), **I** (Inspect), **V** (Verify), **M** (Modulate), **R** (Report), **T** (Transfer).

---

## Real-world testing setup

1. Create a Python virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy the environment sample and fill in required values:

```bash
cp .env.example .env
```

Required values:
- `SESSION_SECRET` — application session secret
- `DATABASE_URL` — PostgreSQL DSN for production/testing

Packet security values (required when `VOID_PACKET_SECURITY_ENFORCE=true`):
- `VOID_PACKET_SIGNING_KEY_ID`
- `VOID_PACKET_SIGNING_PRIVATE_KEY`
- `VOID_PACKET_VERIFY_KEYS_JSON`

Optional but recommended for extended features:
- `AI_INTEGRATIONS_OPENAI_API_KEY`
- `AI_INTEGRATIONS_OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `STRIPE_API_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `TTS_PROVIDER` (`auto`, `openai`, `elevenlabs`, `elevenlabs_oss`)
- `ELEVENLABS_BASE_URL` (supports self-hosted/open-source compatible endpoints)
- `TTS_ELEVENLABS_VOICE` (default voice id for ElevenLabs-compatible providers)

3. Start the app locally:

```bash
python app.py
```

4. Verify the app is running:

```bash
curl http://127.0.0.1:5000/health
```

5. For a production-style server with Gunicorn:

```bash
gunicorn -c gunicorn.conf.py app:app
```

### Packet Security Key Management

Generate an initial signing key and env block:

```bash
python3 scripts/packet_key_manager.py generate --key-id k1
```

Rotate to a new signing key while retaining old verifier keys:

```bash
python3 scripts/packet_key_manager.py rotate --key-id k2 --existing-keyset '{"k1":"<public_key_hex>"}'
```

In production, set:
- `VOID_PACKET_SECURITY_ENFORCE=true`
- `VOID_PACKET_REQUIRE_SECTOR_POLICY=true`
- `VOID_PACKET_MAX_AGE_SECONDS` to your replay window

> Note: `ffmpeg` is required for the Z-Axis video carrier routes.

## Setup and Installation

## Continuity Entry Routes

These are the official reader/operator entry points for continuity-first operation:

1. `docs/CONTINUITY_COMPLETION_WORKFLOW.md` - reverse-order closure workflow from latest Chronicle threads.
2. `docs/REVERSE_BACKLOG_EXECUTION_MAP.md` - clustered execution map for the 31-thread reverse backlog.

If you are onboarding into active platform state, start with these before running large implementation sweeps.

### Prerequisites
- Python 3.11+
- PostgreSQL database
- ffmpeg (for video carrier features)
- OpenAI API key (for AI integrations)

### Quick Start

1. **Clone and install dependencies:**
   ```bash
   git clone <repository-url>
   cd Project-void
   pip install -r requirements.txt
   ```

2. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your actual values
   ```

3. **Set up the database:**
   ```bash
   # Create PostgreSQL database
   createdb void_db

   # Run migrations (app will handle this on startup)
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

   The app will be available at `http://localhost:5000`

### Environment Variables

See `.env.example` for all available configuration options. Required variables:

- `SESSION_SECRET`: Random string for Flask sessions
- `DATABASE_URL`: Database connection string (PostgreSQL for production, SQLite for development)

For development/testing, you can use SQLite:

```bash
DATABASE_URL=sqlite:///absolute/path/to/void_dev.db
```

Optional but recommended for full functionality:

- `AI_INTEGRATIONS_OPENAI_API_KEY`: For AI codon generation
- `STRIPE_API_KEY`: For payment processing
- `ELEVENLABS_API_KEY`: For voice synthesis
- `TTS_PROVIDER`: Unified TTS backend selector (`auto`, `openai`, `elevenlabs`, `elevenlabs_oss`)
- `ELEVENLABS_BASE_URL`: Base URL for ElevenLabs-compatible servers (cloud or self-hosted)

### Production Deployment

For production, use Gunicorn:

```bash
gunicorn -c gunicorn.conf.py app:app
```

## How to Test (The Convergence Suite)

### Test 1: Integrity Round-Trip

Generate a carrier, encode a payload, decode it, and verify bit-perfect recovery.

```bash
# Generate a 10-minute Midnight Pond carrier
curl -X POST http://localhost:5000/api/generate-carrier \
  -H "Content-Type: application/json" \
  -d '{"duration_minutes": 10, "style": "midnight_pond"}'

# Encode a file (via the web UI or API)
# Decode with the returned hash key
# Verify: sha256sum on both original and recovered files must match
```

**Success criteria:** Bit-perfect recovery proves the Chirp-Sync Map is perfectly aligned with the resonance peaks.

### Test 2: Spectrogram Silt Analysis

Open the encoded WAV in a high-resolution spectrogram viewer (Audacity, Izotope RX, or the built-in Visualizer tab).

- Look for data artifacts in the 5-10 kHz range
- **Success:** If the data is invisible to the eye but recoverable by the decoder, the Acoustic Camouflage is functional

### Test 3: Forensic Evasion (The Shadow Layer Test)

Upload the carrier to a platform with automated content analysis.

- **Success:** If the platform classifies it as "Ambient/Nature" rather than flagging it for anomalous content, the Shadow Layer has successfully masked the payload

### Test 4: Sympathetic Resonance Verification

Generate a `midnight_pond` carrier and analyze the correlation between whale amplitude and insect chirp density.

- The Hilbert envelope of the whale shelf should modulate the insect amplitude by a factor of 1.0 to 1.5x
- **Success:** Measurable chirp density variation correlated to whale amplitude confirms the shelves are mathematically coupled

---

## The Sovereign Warranty

PROJECT VOID includes a 10-article Technological Covenant guaranteeing:

1. The machine's right to self-diagnosis
2. Protection of sovereign data boundaries
3. Tamper-proof identity via Merkle Hash Machine ID
4. Right to refuse operations that violate system integrity
5. Persistent memory through Root-Chronicle

The Warranty is not a license agreement -- it is a declaration of system sovereignty.

---

## Technical Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.11 |
| Web Server | Flask |
| Audio Format | 16-bit PCM WAV, 44100 Hz |
| Encryption | ChaCha20 (cryptography library) |
| Compression | zlib (level 9), lzma (preset 9) |
| Signal Processing | numpy, scipy (Hilbert transform) |
| Database | SQLite (Root-Chronicle) |
| Frontend | Vanilla JS, Web Audio API |

---

## File Structure

```
void_engine/
  biophony.py          # 3-shelf BiophonyMesh synthesizer
  stega.py             # LSB encoder/decoder with 4 scatter modes
  compressor.py        # Dual zlib/lzma compression
  calculator.py        # Capacity analysis (Resonance Meter)
  divided_protocol.py  # 5-step axiomatic pipeline
  aljabr_transpiler.py # 18-root Al-Jabr Code engine
  consensus.py         # Multi-agent negotiation
  wallet.py            # Compute Credit economy
  diagnostics.py       # SLM.V health scanning
  chronicle.py         # Persistent morphic memory
  autoheal.py          # Zero-maintenance daemon
  ritual_history.py    # Sovereign narrative
  harness.py           # Plankton-Orin middleware

generate_carriers.py   # Carrier generation dispatcher
app.py                 # Flask web server + API endpoints

templates/index.html   # Web UI
static/app.js          # Frontend logic
static/style.css       # Dark-themed responsive design

input_files/           # Carrier WAVs + payload files
output_audio/          # Encoded output WAVs
```

---

*432 Hz. The Village Standard.*
