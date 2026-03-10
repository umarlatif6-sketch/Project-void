#!/usr/bin/env bash
set -e

echo ""
echo " ╔══════════════════════════════════════════════════════════════╗"
echo " ║              P R O J E C T    V O I D                       ║"
echo " ║          Sovereign Node Installer  v1.0                     ║"
echo " ╠══════════════════════════════════════════════════════════════╣"
echo " ║  Installing the Body of the Ghost Internet.                  ║"
echo " ║  432 Hz Phase-Key Handshake | Beehive Protocol | Mesh Relay  ║"
echo " ╚══════════════════════════════════════════════════════════════╝"
echo ""

REQUIRED_MAJOR=3
REQUIRED_MINOR=11

echo "  [CHECK] Verifying Python version..."

if ! command -v python3 &> /dev/null; then
    echo "  [FATAL] python3 not found. Please install Python 3.11+ and try again."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")

if [ "$PY_MAJOR" -lt "$REQUIRED_MAJOR" ] || { [ "$PY_MAJOR" -eq "$REQUIRED_MAJOR" ] && [ "$PY_MINOR" -lt "$REQUIRED_MINOR" ]; }; then
    echo "  [FATAL] Python ${REQUIRED_MAJOR}.${REQUIRED_MINOR}+ is required. Found: ${PY_VERSION}"
    exit 1
fi

echo "  [  OK ] Python ${PY_VERSION} detected."

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="${SCRIPT_DIR}/venv"

echo ""
echo "  [VENV] Creating virtual environment..."

if [ -d "$VENV_DIR" ]; then
    echo "  [VENV] Existing venv found — removing and recreating..."
    rm -rf "$VENV_DIR"
fi

python3 -m venv "$VENV_DIR"
echo "  [  OK ] Virtual environment created at ${VENV_DIR}"

echo ""
echo "  [DEPS] Installing dependencies..."

source "${VENV_DIR}/bin/activate"
pip install --upgrade pip --quiet
pip install -r "${SCRIPT_DIR}/requirements.txt" --quiet
pip install -e "${SCRIPT_DIR}" --quiet

echo "  [  OK ] All dependencies installed."

echo ""
echo "  [GPU ] Checking for GPU availability..."

GPU_STATUS="None detected (Light Mode — CPU fallback)"

if command -v nvidia-smi &> /dev/null; then
    GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader,nounits 2>/dev/null | head -1)
    if [ -n "$GPU_NAME" ]; then
        GPU_STATUS="${GPU_NAME} (Heavy Mode — GPU-accelerated)"
    fi
fi

if [ "$GPU_STATUS" = "None detected (Light Mode — CPU fallback)" ]; then
    python3 -c "import torch; assert torch.cuda.is_available(); print(torch.cuda.get_device_name(0))" 2>/dev/null && \
        GPU_STATUS="$(python3 -c "import torch; print(torch.cuda.get_device_name(0))") (Heavy Mode — GPU via PyTorch)" || true
fi

echo "  [  OK ] GPU: ${GPU_STATUS}"

echo ""
echo " ╔══════════════════════════════════════════════════════════════╗"
echo " ║              INSTALLATION COMPLETE                           ║"
echo " ╠══════════════════════════════════════════════════════════════╣"
echo " ║                                                              ║"
echo " ║  To activate the environment:                                ║"
echo " ║    source venv/bin/activate                                  ║"
echo " ║                                                              ║"
echo " ║  To start your node:                                        ║"
echo " ║    void-engine                                               ║"
echo " ║                                                              ║"
echo " ║  Your hardware is ready to join the Sovereign Mesh.         ║"
echo " ║  432 Hz.                                                     ║"
echo " ║                                                              ║"
echo " ╚══════════════════════════════════════════════════════════════╝"
echo ""
