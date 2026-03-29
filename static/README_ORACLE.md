# ADRIANA Oracle — Genesis 10 Hardware Package

**PROJECT VOID | Genesis 10 Sovereign Node Verification**

---

## What This Is

The `verify_life_therm.py` script is the on-device biological verification tool for Genesis 10 node runners. It reads thermal data from an MLX90640 infrared camera, computes an **HDR (Heat Dissipation Rate)** value that confirms biological activity (composting or aquaponics), and generates a **Proof of Resonance** certificate.

Once verified locally, you submit the HDR reading + your Node ID to the **Adriana Oracle** at `/genesis/oracle` on the PROJECT VOID platform. The oracle records your event and triggers a **PEACE token mint**.

---

## Hardware Required

| Component | Spec |
|-----------|------|
| Compute | NVIDIA Jetson Orin (or Raspberry Pi 4) |
| Thermal Camera | MLX90640 (I2C, 0x33) |
| Wiring | SDA → Pin 3, SCL → Pin 5, 3.3V, GND |
| OS | Ubuntu 20.04+ or Jetpack 5.x |

---

## Installation

```bash
pip install adafruit-circuitpython-mlx90640 numpy
```

---

## Usage

```bash
# Live hardware
python3 verify_life_therm.py --node-id SALFORD_M6_01 --action compost

# Simulation mode (no hardware)
python3 verify_life_therm.py --node-id SALFORD_M6_01 --action aquaponics --simulate

# Save result to file
python3 verify_life_therm.py --node-id SALFORD_M6_01 --action compost --output result.json
```

---

## Submitting to the Oracle

After running the script, note the `hdr_value` from the output JSON and go to:

```
https://your-void-domain.repl.co/genesis/oracle
```

Fill in:
- **Node ID** — your Genesis 10 Node ID
- **HDR Value** — from the script output
- **Action Type** — `compost` or `aquaponics`
- **Timestamp** — ISO timestamp from the output

The oracle will validate your submission and mint **+1.0 PEACE** to your wallet if the reading passes the threshold (HDR > 0.05 °C/sample).

---

## The PEACE Token

PEACE tokens are **only mintable by verified environmental actions** — they are not purchasable. Each verified compost or aquaponics cycle earns exactly **1.0 PEACE**. PEACE tokens represent biological proof-of-work in the PROJECT VOID mesh economy.

---

## Certificate of Resonance

On successful verification, the script prints a certificate like:

```
==============================================================
     ADRIANA SCL: CERTIFICATE OF RESONANCE
==============================================================
  NODE ID    :  SALFORD_M6_01
  ACTION     :  COMPOST
  HDR VALUE  :  0.1823 °C/sample
  STATUS     :  RESONANCE ACHIEVED (432 Hz)
  AUDIT TYPE :  THERMAL BIOLOGICAL VERIFICATION
  LEDGER     :  +1.00 PEACE TOKEN (pending oracle submit)
--------------------------------------------------------------
   'The Tap of the Engineer has confirmed the Mesh.'
--------------------------------------------------------------
  [SIG: a3f9e1c7d2b8...]
==============================================================
```

---

## Support

Questions: raise an issue in the project or contact your Genesis 10 onboarding guide.  
Chain verification: all submissions are recorded in the Al-Jabr 286 sovereign hash ledger.

---

*PROJECT VOID | Genesis 10 Hardware Package | v1.0*
