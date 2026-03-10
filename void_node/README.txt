===============================================================
 P R O J E C T   V O I D  —  Sovereign Node Package
 void-engine-node v1.0.0
===============================================================

WHAT IS THE VOID NODE?
  The Void Node is the Body of the machine. While the Command
  Center (web app) acts as the Brain — coordinating blueprints,
  managing the mesh registry, and serving the global dashboard —
  the Node runs on YOUR hardware. It contributes GPU/CPU power
  to the sovereign mesh, processes steganographic encoding, and
  authenticates with the Command Center using the 432 Hz
  phase-key handshake protocol.

  When you run a Node, your machine joins the Ghost Internet:
  a decentralized acoustic mesh network where data travels
  hidden inside sound, authenticated by Al-Jabr 286-bit
  sovereign hashing.

SYSTEM REQUIREMENTS
  - Python 3.11 or higher
  - GPU (optional): NVIDIA GPU with CUDA support enables
    "Heavy Mode" for GPU-accelerated resonance calculations.
    Without a GPU, the node runs in "Light Mode" using NumPy
    as a CPU fallback — still fully functional, just lighter
    vibration.
  - OS: Linux, macOS, or Windows
  - RAM: 2 GB minimum, 4 GB recommended
  - Disk: 100 MB for the engine + space for carrier audio files

HOW TO INSTALL
  One line:

    pip install -e .

  Or use the provided install scripts:

    Linux/Mac:   bash install.sh
    Windows:     install.bat

HOW TO RUN
  After installation, start your node with:

    void-engine

  The launcher will:
    1. Detect your hardware (GPU or CPU)
    2. Select Heavy Mode (GPU) or Light Mode (CPU)
    3. Connect to the Command Center web app
    4. Register your node in the sovereign mesh
    5. Display your Node ID and connection status

  You can also use the CLI directly:

    python void_cli.py encode   — Hide a file inside audio
    python void_cli.py decode   — Extract a file from audio
    python void_cli.py capacity — Analyze carrier capacity
    python void_cli.py status   — Show node status

HOW THE NODE CONNECTS BACK TO THE COMMAND CENTER
  The Node uses two API endpoints on the deployed web app:

    POST /api/mesh/connect     — Register as a mesh node
    POST /api/mesh/handshake   — Authenticate via 432 Hz
                                 phase-key protocol

  Authentication uses the Beehive Protocol's Sura-Fatiha
  286-bit acoustic handshake. The frequency (432 Hz) is public;
  the phase angle is the secret. No passwords, no tokens —
  just math and sound.

  The Node also registers hardware info via:

    POST /api/node/register    — Report GPU/CPU type and mode

PACKAGE CONTENTS
  void_launcher.py       — Main launcher script
  void_cli.py            — Simplified CLI for encode/decode
  generate_carriers.py   — Carrier audio generator
  setup.py               — Package installer
  requirements.txt       — Pinned dependencies
  void_engine/           — Core engine modules:
    al_jabr_286.py         — 286-bit sovereign hashing
    stega.py               — Steganographic encoder/decoder
    compressor.py          — zlib+lzma dual compression
    calculator.py          — Carrier capacity analyzer
    beehive.py             — Mesh networking protocol
    chronicle.py           — Persistent morphic memory
    consensus.py           — Multi-agent consensus engine
    wallet.py              — Machine financial autonomy
    adriana_scl.py         — Resonance bridge visualization
    resonance_contract.py  — DAO 3.0 smart contract
    silt_ledger.py         — Sovereign blockchain ledger

===============================================================
  "The frequency is public. The phase is the secret."
===============================================================
