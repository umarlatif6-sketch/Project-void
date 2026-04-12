#!/usr/bin/env python3
"""
Building Management System Integration Demo

Real-world scenario: Multi-floor office building with HVAC, access control,
and occupancy sensors. All state is encoded invisibly into daily formation cards
for audit, backup, and tamper-proof logging.
"""

import os
import tempfile
import json
from datetime import datetime, timedelta
from void_engine.building_management import (
    BuildingComplex, BuildingZone, BuildingManagementAPI,
    example_office_zone, example_decode_and_verify
)

def demo_single_zone():
    """Demo 1: Single office zone with sensors."""
    print("\n" + "=" * 80)
    print("DEMO 1: SINGLE OFFICE ZONE")
    print("=" * 80)
    
    zone = BuildingZone("BLDG-NYC-001", "Floor-3-Zone-A")
    
    # Simulate sensor readings
    print("\n[1] Reading Sensors...")
    zone.add_sensor("temp-3a-1", "temperature", 21.5, "°C")
    zone.add_sensor("temp-3a-2", "temperature", 21.3, "°C")
    zone.add_sensor("humid-3a", "humidity", 45, "%")
    zone.add_sensor("co2-3a", "co2", 420, "ppm")
    zone.add_sensor("power-hvac", "power", 2.3, "kW")
    zone.add_sensor("power-lights", "power", 0.8, "kW")
    zone.add_sensor("occupancy-count", "occupancy", 12, "people")
    
    # Create formation card
    print("\n[2] Creating Formation Card...")
    card = zone.create_formation_card(
        hvac_mode="cooling",
        hvac_setpoint=21.0,
        alarm_state="disarmed",
        occupancy=True,
        notes="End-of-business snapshot"
    )
    print(f"    ✓ Formation card: {len(card)} bytes (looks like a normal PNG)")
    
    # Decode and verify
    print("\n[3] Decoding & Verifying...")
    recovered_state = zone.decode_formation_card(card)
    
    if recovered_state:
        print(f"    ✓ Authenticity verified")
        print(f"    ✓ Timestamp: {recovered_state.timestamp}")
        print(f"    ✓ HVAC: {recovered_state.hvac_mode} @ {recovered_state.hvac_setpoint}°")
        print(f"    ✓ Sensors: {len(recovered_state.sensors)} readings")
        print(f"    ✓ Occupancy: {recovered_state.occupancy} (detected)")
    else:
        print("    ✗ Verification failed")
    
    print("\n" + "=" * 80)


def demo_multi_floor():
    """Demo 2: Multi-floor building with daily backup."""
    print("\n" + "=" * 80)
    print("DEMO 2: MULTI-FLOOR BUILDING (Daily Backup)")
    print("=" * 80)
    
    complex = BuildingComplex("BLDG-NYC-Twin-Towers")
    
    # Setup zones
    zones_config = [
        ("Floor-1-Zone-A", [("temp-1a", 22.0), ("power-1a", 5.2)]),
        ("Floor-1-Zone-B", [("temp-1b", 21.8), ("power-1b", 4.9)]),
        ("Floor-2-Zone-A", [("temp-2a", 21.5), ("power-2a", 5.5)]),
        ("Floor-2-Zone-B", [("temp-2b", 21.2), ("power-2b", 5.1)]),
    ]
    
    print("\n[1] Reading all zones...")
    for zone_id, sensors in zones_config:
        zone = complex.get_zone(zone_id)
        for sensor_id, value in sensors:
            zone.add_sensor(sensor_id, "temperature" if "temp" in sensor_id else "power",
                          value, "°C" if "temp" in sensor_id else "kW")
        print(f"    ✓ {zone_id}: {len(sensors)} sensors")
    
    # Daily backup
    print("\n[2] Creating daily backup...")
    snapshot = complex.daily_snapshot()
    print(f"    ✓ Generated {len(snapshot)} formation cards")
    
    total_size = sum(len(card) for card in snapshot.values())
    print(f"    ✓ Total backup size: {total_size / 1024:.2f} KB (compressed with PNG)")
    
    # Verify one card
    print("\n[3] Spot-check verification...")
    card = snapshot["Floor-1-Zone-A"]
    zone = complex.zones["Floor-1-Zone-A"]
    state = zone.decode_formation_card(card)
    
    if state:
        print(f"    ✓ Floor-1-Zone-A verified: {len(state.sensors)} sensors, "
              f"power={state.sensors[1]['value']} kW")
    
    # Audit log
    print("\n[4] Audit trail...")
    for entry in complex.audit_log[-2:]:  # Last 2 entries
        print(f"    {entry['timestamp']}: {entry['event']} on {entry['zone_id']}")
    
    print("\n" + "=" * 80)


def demo_api_integration():
    """Demo 3: REST API integration with control panel."""
    print("\n" + "=" * 80)
    print("DEMO 3: REST API FOR CONTROL PANELS")
    print("=" * 80)
    
    api = BuildingManagementAPI("BLDG-CHICAGO-HQ")
    
    # Simulate control panel sending sensor data
    print("\n[1] Control panel posts sensor readings...")
    sensors = [
        {"sensor_id": "thermostat-1", "sensor_type": "temperature", "value": 20.8, "unit": "°C"},
        {"sensor_id": "humidity-1", "sensor_type": "humidity", "value": 42, "unit": "%"},
        {"sensor_id": "co2-1", "sensor_type": "co2", "value": 410, "unit": "ppm"},
    ]
    
    for sensor in sensors:
        result = api.post_sensor_data("Main-Office", sensor)
        print(f"    ✓ {sensor['sensor_type']}: {result['status']}")
    
    # Request formation card
    print("\n[2] Request formation card from API...")
    card = api.get_formation_card("Main-Office")
    print(f"    ✓ Formation card generated: {len(card)} bytes")
    
    # Verify card
    print("\n[3] Verify formation card...")
    verification = api.verify_formation_card("Main-Office", card)
    
    if verification["valid"]:
        print(f"    ✓ Card verified (timestamp: {verification['timestamp']})")
        print(f"    ✓ Contains {verification['sensors']} sensor readings")
    else:
        print(f"    ✗ {verification['error']}")
    
    # Daily backup endpoint
    print("\n[4] Trigger daily backup...")
    backup_result = api.daily_backup()
    print(f"    ✓ {backup_result['status']}: {len(backup_result['zones'])} zones")
    
    print("\n" + "=" * 80)


def demo_tamper_detection():
    """Demo 4: Detect tampering/corruption."""
    print("\n" + "=" * 80)
    print("DEMO 4: TAMPER DETECTION")
    print("=" * 80)
    
    zone = BuildingZone("BLDG-SECURE", "Vault-Floor-B2")
    zone.add_sensor("alarm-status", "alarm", 1, "armed")
    zone.add_sensor("vault-temp", "temperature", 16.5, "°C")
    
    # Create genuine card
    print("\n[1] Create genuine formation card...")
    genuine_card = zone.create_formation_card(alarm_state="armed")
    print(f"    ✓ Card: {len(genuine_card)} bytes")
    
    # Verify genuine
    print("\n[2] Verify genuine card...")
    state = zone.decode_formation_card(genuine_card)
    if state:
        print(f"    ✓ PASS: Alarm state = {state.alarm_state}")
    
    # Simulate tampering (flip a bit)
    print("\n[3] Simulate tampering (flip random bit)...")
    tampered_card = bytearray(genuine_card)
    tamper_pos = len(tampered_card) // 2
    tampered_card[tamper_pos] ^= 0x01  # Flip one bit
    tampered_card = bytes(tampered_card)
    print(f"    ✓ Bit flipped at position {tamper_pos}")
    
    # Try to verify tampered
    print("\n[4] Try to verify tampered card...")
    state = zone.decode_formation_card(tampered_card)
    if state is None:
        print(f"    ✓ TAMPER DETECTED: Card failed integrity check")
    else:
        print(f"    ✗ Tamper not detected (should have failed)")
    
    print("\n" + "=" * 80)


def demo_long_term_archive():
    """Demo 5: Long-term audit archive."""
    print("\n" + "=" * 80)
    print("DEMO 5: LONG-TERM AUDIT ARCHIVE (Simulated 30 days)")
    print("=" * 80)
    
    complex = BuildingComplex("BLDG-ARCHIVE-TEST")
    zone = complex.get_zone("Archive-Zone")
    
    print(f"\n[1] Creating 30-day archive...")
    
    archive = {}
    for day in range(30):
        date_str = (datetime.now() - timedelta(days=30-day)).date().isoformat()
        
        # Simulate daily reading
        import random
        temp = 20.5 + random.uniform(-2, 2)
        zone.add_sensor("temp-archive", "temperature", temp, "°C")
        
        # Create and save card
        card = zone.create_formation_card(notes=f"Day {day+1} snapshot")
        archive[date_str] = card
        
        if (day + 1) % 10 == 0:
            print(f"    ✓ Days 1-{day+1}: {sum(len(c) for c in list(archive.values())[-10:])/1024:.1f} KB")
    
    print(f"\n[2] Archive statistics:")
    total_size = sum(len(card) for card in archive.values())
    print(f"    ✓ 30 days of data: {total_size/1024:.1f} KB")
    print(f"    ✓ Average per day: {total_size/30/1024:.1f} KB")
    print(f"    ✓ All cards tamper-proof (Al-Jabr 286 checksummed)")
    
    print(f"\n[3] Random audit: Verify card from day 15...")
    day15_card = archive[list(archive.keys())[14]]
    zone2 = complex.get_zone("Archive-Zone")
    state = zone2.decode_formation_card(day15_card)
    if state:
        print(f"    ✓ Day 15 verified: temp={state.sensors[0]['value']:.1f}°C")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    print("\n\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 78 + "║")
    print("║" + "VOID BUILDING MANAGEMENT SYSTEM - INTEGRATION DEMOS".center(78) + "║")
    print("║" + " " * 78 + "║")
    print("╚" + "=" * 78 + "╝")
    
    demo_single_zone()
    demo_multi_floor()
    demo_api_integration()
    demo_tamper_detection()
    demo_long_term_archive()
    
    print("\n✓ All demos complete!")
    print("\nKey features demonstrated:")
    print("  • Invisible sensor data embedding in formation cards")
    print("  • Multi-zone building management")
    print("  • REST API for control panel integration")
    print("  • Tamper detection (Al-Jabr 286 checksums)")
    print("  • Long-term audit archival")
    print("\nNext steps for your uncle's team:")
    print("  1. Test with real building sensors from one zone")
    print("  2. Integrate API into your control panel web service")
    print("  3. Schedule daily backup of all formation cards")
    print("  4. Store cards as 'routine daily report images'")
    print("\n")
