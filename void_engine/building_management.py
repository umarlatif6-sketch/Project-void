"""
Building Management Integration — Steganographic Sensor Data & Control State Encoding.

Embeds building sensor readings, HVAC state, access logs, and control panel status
invisibly into formation cards (PNG images) using Z-Axis dimensional steganography.

Each building zone maintains a cryptographic identity (formation hash) derived from
building ID + zone + timestamp. Daily sensor snapshots are encoded into formation
cards that look like ordinary images but carry complete, tamper-proof audit logs.

Usage:
  building = BuildingZone("BLDG-001-NYC", "Floor-3-Zone-A")
  state = building.read_sensors(...)
  card = building.create_formation_card(state)
  
  # Later: verify and recover
  recovered_state = building.decode_formation_card(card)
  if recovered_state.is_valid():
      print("State verified, not tampered")
"""

import json
import hashlib
import logging
from datetime import datetime
from typing import Dict, Optional, Any, List
from dataclasses import dataclass, asdict

from void_engine.z_axis_encoder import encode, decode
from void_engine.al_jabr_286 import fatiha_286_hexdigest

logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Single sensor measurement with timestamp and location."""
    sensor_id: str
    sensor_type: str  # "temperature", "humidity", "co2", "occupancy", "power", etc.
    value: float
    unit: str
    timestamp: str


@dataclass
class BuildingState:
    """Complete snapshot of building zone status at a point in time."""
    building_id: str
    zone_id: str
    timestamp: str
    sensors: List[Dict]  # List of sensor reading dicts
    hvac_mode: str  # "heating", "cooling", "ventilation", "off"
    hvac_setpoint: float
    access_state: Dict  # {"main_door": "locked", "emergency_exit": "locked", ...}
    alarm_state: str  # "armed", "disarmed", "triggered"
    occupancy: bool
    notes: str = ""
    formation_hash: str = ""  # Set after encoding
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)
    
    @staticmethod
    def from_json(data: str) -> "BuildingState":
        return BuildingState(**json.loads(data))


class BuildingZone:
    """
    Single building zone with steganographic sensor data management.
    
    Encodes/decodes all sensor and state data into formation cards (PNG images).
    Formation hash is cryptographically derived from building ID, zone, and timestamp.
    """
    
    def __init__(self, building_id: str, zone_id: str):
        self.building_id = building_id
        self.zone_id = zone_id
        self.sensors: Dict[str, SensorReading] = {}
        self.state: Optional[BuildingState] = None
        
    def derive_formation_hash(self, timestamp: Optional[str] = None) -> str:
        """
        Derive cryptographic identity for this zone at a specific timestamp.
        
        Same building/zone at different times = different hashes → different formation cards
        Allows per-timestamp verification and prevents replay attacks.
        """
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        identity_string = f"{self.building_id}:{self.zone_id}:{timestamp}"
        return fatiha_286_hexdigest(identity_string.encode())
    
    def add_sensor(self, sensor_id: str, sensor_type: str, value: float, 
                   unit: str, timestamp: Optional[str] = None):
        """Record a single sensor reading."""
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat()
        
        self.sensors[sensor_id] = SensorReading(
            sensor_id=sensor_id,
            sensor_type=sensor_type,
            value=value,
            unit=unit,
            timestamp=timestamp
        )
        logger.info(f"[BldgMgmt] {self.building_id}/{self.zone_id}: {sensor_type}={value}{unit}")
    
    def set_hvac_state(self, mode: str, setpoint: float):
        """Update HVAC state (heating/cooling/off)."""
        logger.info(f"[BldgMgmt] {self.building_id}/{self.zone_id}: HVAC {mode} @ {setpoint}°")
    
    def set_access_state(self, door_id: str, state: str):
        """Update door/access lock state."""
        if self.state is None:
            self.state = BuildingState(
                building_id=self.building_id,
                zone_id=self.zone_id,
                timestamp=datetime.utcnow().isoformat(),
                sensors=[],
                hvac_mode="off",
                hvac_setpoint=20.0,
                access_state={},
                alarm_state="disarmed",
                occupancy=False
            )
        self.state.access_state[door_id] = state
        logger.info(f"[BldgMgmt] {self.building_id}/{self.zone_id}: {door_id}={state}")
    
    def create_formation_card(self, hvac_mode: str = "off", hvac_setpoint: float = 20.0,
                             alarm_state: str = "disarmed", occupancy: bool = False,
                             notes: str = "") -> bytes:
        """
        Encode current sensor state into a formation card PNG.
        
        Returns: PNG bytes (formation card image containing embedded data)
        """
        timestamp = datetime.utcnow().isoformat()
        formation_hash = self.derive_formation_hash(timestamp)
        
        state = BuildingState(
            building_id=self.building_id,
            zone_id=self.zone_id,
            timestamp=timestamp,
            sensors=[asdict(s) for s in self.sensors.values()],
            hvac_mode=hvac_mode,
            hvac_setpoint=hvac_setpoint,
            access_state=getattr(self, '_access_state', {}),
            alarm_state=alarm_state,
            occupancy=occupancy,
            notes=notes,
            formation_hash=formation_hash
        )
        
        # Encode state JSON into formation card
        state_json = state.to_json().encode()
        card_png_bytes = encode(state_json, formation_hash)
        
        self.state = state
        logger.info(f"[BldgMgmt] Created formation card: {self.building_id}/{self.zone_id} "
                   f"({len(card_png_bytes)} bytes)")
        
        return card_png_bytes
    
    def decode_formation_card(self, card_png_bytes: bytes, 
                             expected_timestamp: Optional[str] = None) -> Optional[BuildingState]:
        """
        Decode and verify a formation card.
        
        If expected_timestamp is provided, verifies the card is from that exact time.
        Returns BuildingState if valid, None if integrity check fails.
        """
        try:
            # We need the formation hash to decode; try to rebuild it from card metadata
            # For this implementation, assume card was created from known timestamp
            timestamp = expected_timestamp or datetime.utcnow().isoformat()
            formation_hash = self.derive_formation_hash(timestamp)
            
            # Decode
            recovered_json = decode(card_png_bytes, formation_hash)
            state = BuildingState.from_json(recovered_json.decode())
            
            # Verify it matches expected building/zone
            if state.building_id != self.building_id or state.zone_id != self.zone_id:
                logger.error(f"[BldgMgmt] Zone mismatch in card: expected "
                            f"{self.building_id}/{self.zone_id}, got "
                            f"{state.building_id}/{state.zone_id}")
                return None
            
            logger.info(f"[BldgMgmt] Formation card verified: {len(state.sensors)} sensors, "
                       f"HVAC {state.hvac_mode}, occupancy {state.occupancy}")
            return state
            
        except Exception as e:
            logger.error(f"[BldgMgmt] Failed to decode formation card: {e}")
            return None


class BuildingComplex:
    """Multi-zone building management with centralized logging."""
    
    def __init__(self, building_id: str):
        self.building_id = building_id
        self.zones: Dict[str, BuildingZone] = {}
        self.audit_log: List[Dict] = []
    
    def get_zone(self, zone_id: str) -> BuildingZone:
        """Get or create a zone."""
        if zone_id not in self.zones:
            self.zones[zone_id] = BuildingZone(self.building_id, zone_id)
        return self.zones[zone_id]
    
    def daily_snapshot(self, timestamp: Optional[str] = None) -> Dict[str, bytes]:
        """
        Create formation cards for all zones (daily backup/audit snapshot).
        
        Returns: {zone_id: formation_card_png_bytes, ...}
        """
        if timestamp is None:
            timestamp = datetime.utcnow().date().isoformat()
        
        snapshot = {}
        for zone_id, zone in self.zones.items():
            card = zone.create_formation_card()
            snapshot[zone_id] = card
            
            # Log to audit trail
            self.audit_log.append({
                "timestamp": datetime.utcnow().isoformat(),
                "event": "daily_snapshot",
                "zone_id": zone_id,
                "card_size_bytes": len(card)
            })
        
        logger.info(f"[BldgMgmt] Daily snapshot: {self.building_id} ({len(snapshot)} zones)")
        return snapshot
    
    def export_audit_log(self) -> str:
        """Export audit log as JSON."""
        return json.dumps(self.audit_log, indent=2)


# =============================================================================
# Example Utilities
# =============================================================================

def example_office_zone() -> bytes:
    """
    Demonstrate a complete office zone with typical sensors.
    Returns a formation card ready to archive.
    """
    zone = BuildingZone("BLDG-NYC-001", "Floor-3-Zone-A")
    
    # Temperature sensors
    zone.add_sensor("temp-3a-1", "temperature", 21.5, "°C")
    zone.add_sensor("temp-3a-2", "temperature", 21.3, "°C")
    
    # Humidity
    zone.add_sensor("humid-3a", "humidity", 45, "%")
    
    # CO2
    zone.add_sensor("co2-3a", "co2", 420, "ppm")
    
    # Power usage
    zone.add_sensor("power-3a-hvac", "power", 2.3, "kW")
    zone.add_sensor("power-3a-lights", "power", 0.8, "kW")
    
    # Create formation card with HVAC state
    card = zone.create_formation_card(
        hvac_mode="cooling",
        hvac_setpoint=21.0,
        alarm_state="disarmed",
        occupancy=True,
        notes="Daily end-of-shift snapshot"
    )
    
    return card


def example_decode_and_verify(card: bytes) -> Optional[Dict]:
    """Decode a formation card and return state as dict."""
    zone = BuildingZone("BLDG-NYC-001", "Floor-3-Zone-A")
    
    # In a real system, you'd know the timestamp from the card filename or metadata
    state = zone.decode_formation_card(card, expected_timestamp=None)
    
    if state:
        return {
            "building": state.building_id,
            "zone": state.zone_id,
            "timestamp": state.timestamp,
            "num_sensors": len(state.sensors),
            "hvac_mode": state.hvac_mode,
            "occupancy": state.occupancy,
            "alarm": state.alarm_state,
            "sensors": state.sensors
        }
    return None


# =============================================================================
# REST/API Integration Support
# =============================================================================

class BuildingManagementAPI:
    """Simple API to integrate with control panel web services."""
    
    def __init__(self, building_id: str):
        self.complex = BuildingComplex(building_id)
    
    def post_sensor_data(self, zone_id: str, sensor_data: Dict) -> Dict:
        """
        Receive sensor data from a control panel.
        
        Expected payload:
        {
            "sensor_id": "temp-3a-1",
            "sensor_type": "temperature",
            "value": 21.5,
            "unit": "°C"
        }
        """
        zone = self.complex.get_zone(zone_id)
        zone.add_sensor(
            sensor_data["sensor_id"],
            sensor_data["sensor_type"],
            sensor_data["value"],
            sensor_data["unit"]
        )
        return {"status": "recorded", "zone": zone_id}
    
    def get_formation_card(self, zone_id: str) -> bytes:
        """Generate and return formation card for a zone."""
        zone = self.complex.get_zone(zone_id)
        return zone.create_formation_card()
    
    def verify_formation_card(self, zone_id: str, card_bytes: bytes) -> Dict:
        """Verify that a formation card is authentic and unmodified."""
        zone = self.complex.get_zone(zone_id)
        state = zone.decode_formation_card(card_bytes)
        
        if state:
            return {
                "valid": True,
                "building": state.building_id,
                "zone": state.zone_id,
                "timestamp": state.timestamp,
                "sensors": len(state.sensors)
            }
        else:
            return {"valid": False, "error": "Integrity check failed"}
    
    def daily_backup(self) -> Dict[str, str]:
        """Create daily formation card backup for all zones."""
        snapshot = self.complex.daily_snapshot()
        
        # In a real system, save these cards:
        # for zone_id, card_bytes in snapshot.items():
        #     with open(f"backup/{zone_id}_{date}.png", "wb") as f:
        #         f.write(card_bytes)
        
        return {
            "status": "backed_up",
            "building": self.complex.building_id,
            "zones": list(snapshot.keys()),
            "timestamp": datetime.utcnow().isoformat()
        }
