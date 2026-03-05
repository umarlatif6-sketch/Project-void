import os
import time
from datetime import datetime
from void_engine.harness import PreCompletionChecklistMiddleware, VirtualVoidSimulator
from void_engine.nervous_system import SilkLinkContextMiddleware, AquaponicsBoundaryHook
from void_engine.loop_detector import LoopDetectionMiddleware
from void_engine.chaos_test import NitrogenLeakChaosTest
from void_engine.adriana_transpiler import AdrianaTranspiler
from void_engine.aljabr_transpiler import AlJabrTranspiler
from void_engine.consensus import ConsensusEngine
from void_engine.wallet import AlJabrWalletMiddleware
from void_engine.diagnostics import DiagnosticEngine, SOVEREIGN_WARRANTY
from void_engine.rituals import RitualHistory, AutoHealDaemon, RITUAL_TYPES
from void_engine.chronicle import RootChronicle
from void_engine.founder_certs import create_founder_cert, batch_generate_certs, FOUNDER_ROOT_HASH
from void_engine.technical_brief import generate_technical_brief
from void_engine.divided_protocol import DividedProtocol
from void_engine.silk_web import SignalTicker
from void_engine.beehive import BeehiveProtocol, MeshRouter, MeshPacket, simulate_two_node_exchange, _sanitize_for_json
from void_engine.kinetic import KineticTransceiver, EXERCISE_WEIGHTS
from void_engine.biological import BiologicalTransceiver
from void_engine.silt_ledger import SiltLedger
from void_engine.resonance_contract import ResonanceContract
from generate_carriers import generate_custom_carrier, estimate_carrier_capacity, ALL_STYLES

INPUT_DIR = "input_files"
OUTPUT_DIR = "output_audio"
SILT_DIR = "silt_drops"
INQUIRY_DIR = "inquiries"
LOG_FILE = "RESONANCE_LOG.md"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(SILT_DIR, exist_ok=True)
os.makedirs(INQUIRY_DIR, exist_ok=True)

low_power_mode = False
village_default_key = None
start_time = time.time()


def _log_operation(op_type, filename, hash_key, extra=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    hash_tail = hash_key[-4:] if hash_key else "????"
    with open(LOG_FILE, "a") as f:
        line = f"| {timestamp} | {op_type} | {filename} | ...{hash_tail} |"
        if extra:
            line += f" {extra} |"
        f.write(line + "\n")


silk_ticker = SignalTicker()
silk_ticker.start_heartbeat()

harness_checklist = PreCompletionChecklistMiddleware()
harness_sim = VirtualVoidSimulator()
silk_context = SilkLinkContextMiddleware()
boundary_hook = AquaponicsBoundaryHook()
loop_detector = LoopDetectionMiddleware(max_attempts=5)

chaos_test = NitrogenLeakChaosTest(harness_sim, harness_checklist, boundary_hook, loop_detector)
adriana = AdrianaTranspiler()
aljabr = AlJabrTranspiler()
wallet = AlJabrWalletMiddleware(initial_balance=50.0)
diagnostics = DiagnosticEngine(harness_sim, wallet=wallet)
ritual_history = RitualHistory(harness_sim, wallet=wallet)
chronicle = RootChronicle(machine_id=ritual_history.machine_id)
consensus = ConsensusEngine(harness_sim, aljabr, boundary_hook, loop_detector, wallet=wallet, chronicle=chronicle)
auto_heal = AutoHealDaemon(diagnostics, harness_sim, wallet=wallet, ritual_history=ritual_history)
divided = DividedProtocol(diagnostics, harness_sim, chronicle=chronicle, wallet=wallet)
beehive = BeehiveProtocol(machine_id="VOID-4000-PRIMARY")
mesh_router = MeshRouter(beehive)
kinetic = KineticTransceiver(wallet=wallet, chronicle=chronicle)
biological = BiologicalTransceiver()
silt_ledger = SiltLedger(node_id=beehive.node_id)
resonance_contract = ResonanceContract(
    wallet=wallet,
    kinetic=kinetic,
    biological=biological,
    beehive=beehive,
    silt_ledger=silt_ledger,
)

silk_context.bulk_update({
    "silk_strand_0_resistance": {"value": 3.1, "unit": "ohm"},
    "silk_strand_1_resistance": {"value": 3.2, "unit": "ohm"},
    "silk_strand_2_resistance": {"value": 3.0, "unit": "ohm"},
    "silk_strand_3_resistance": {"value": 3.2, "unit": "ohm"},
    "silk_strand_4_resistance": {"value": 3.4, "unit": "ohm"},
    "silk_strand_5_resistance": {"value": 3.1, "unit": "ohm"},
    "silk_total_resistance": {"value": 12.5, "unit": "ohm"},
    "aqua_ph": {"value": 6.8, "unit": "pH"},
    "aqua_temperature": {"value": 22.0, "unit": "C"},
    "aqua_dissolved_oxygen": {"value": 7.5, "unit": "ppm"},
    "aqua_ammonia": {"value": 0.1, "unit": "ppm"},
    "aqua_pump_cycles": {"value": 0, "unit": "cycles/hr"},
    "aqua_water_level": {"value": 85.0, "unit": "%"},
    "flywheel_rpm": {"value": 3500, "unit": "RPM"},
    "flywheel_energy": {"value": 120.0, "unit": "Wh"},
    "flywheel_temperature": {"value": 38.0, "unit": "C"},
    "flywheel_vibration": {"value": 0.8, "unit": "g"},
    "pressure_internal": {"value": 1.0, "unit": "atm"},
    "pressure_external": {"value": 1.0, "unit": "atm"},
    "air_curtain_velocity": {"value": 0.0, "unit": "m/s"},
    "nitrogen_boil_rate": {"value": 0.0, "unit": "rate"},
    "seal_integrity": {"value": 100.0, "unit": "%"},
})
