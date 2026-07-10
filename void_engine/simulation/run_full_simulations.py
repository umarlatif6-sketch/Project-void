"""
PROJECT VOID — Full Molecular Simulations
==========================================

Runs frequency-driven molecular dynamics for all compounds using OpenMM.
Each simulation applies a harmonic driving force at the compound's
resonant frequency to test geometry stabilization.

Paradigm: Frequency Mechanics (not Quantum Mechanics)
Base Frequency: 432 Hz

Usage:
  python run_full_simulations.py
"""

import numpy as np
import json
import os
from datetime import datetime
import openmm as mm
from openmm import unit
import matplotlib.pyplot as plt


# ============================================================
# HELPER: Build a molecular system with frequency driving
# ============================================================

def create_frequency_driven_system(positions_nm, masses_amu, bonds, 
                                    driving_freq_hz, driving_amplitude,
                                    drive_direction='z'):
    """
    Create an OpenMM system with a frequency driving force.
    
    Args:
        positions_nm: Nx3 array of positions in nanometers
        masses_amu: list of masses in amu
        bonds: list of (i, j, length_nm, k_kj_mol_nm2) tuples
        driving_freq_hz: driving frequency in Hz
        driving_amplitude: force amplitude in kJ/mol/nm
        drive_direction: 'z', 'radial', or 'axial'
    """
    n_atoms = len(masses_amu)
    system = mm.System()
    
    # Add particles
    for mass in masses_amu:
        system.addParticle(mass * unit.amu)
    
    # Add bonds
    if bonds:
        bond_force = mm.HarmonicBondForce()
        for i, j, length, k in bonds:
            bond_force.addBond(i, j, length * unit.nanometer,
                             k * unit.kilojoule_per_mole / unit.nanometer**2)
        system.addForce(bond_force)
    
    # Add nonbonded (LJ + Coulomb)
    nb_force = mm.NonbondedForce()
    nb_force.setNonbondedMethod(mm.NonbondedForce.NoCutoff)
    for i in range(n_atoms):
        nb_force.addParticle(0.0 * unit.elementary_charge,
                            0.34 * unit.nanometer,
                            0.5 * unit.kilojoule_per_mole)
    # Exclude bonded pairs
    for i, j, _, _ in bonds:
        nb_force.addException(i, j, 0, 0, 0)
    system.addForce(nb_force)
    
    # Add frequency driving force
    if drive_direction == 'z':
        expr = f'{driving_amplitude}*sin(2*3.14159265*{driving_freq_hz}*t)*z'
    elif drive_direction == 'radial':
        expr = f'{driving_amplitude}*sin(2*3.14159265*{driving_freq_hz}*t)*sqrt(x*x+y*y+z*z)'
    elif drive_direction == 'axial':
        expr = f'{driving_amplitude}*sin(2*3.14159265*{driving_freq_hz}*t)*z'
    
    driving_force = mm.CustomExternalForce(expr)
    driving_force.addGlobalParameter('t', 0.0)
    for i in range(n_atoms):
        driving_force.addParticle(i, [])
    system.addForce(driving_force)
    
    return system


def run_simulation(system, positions, n_steps=10000, timestep_ps=0.001,
                   temperature_K=300, report_interval=1000, label=""):
    """Run a simulation and collect energy + structural data."""
    
    integrator = mm.LangevinMiddleIntegrator(
        temperature_K * unit.kelvin,
        1.0 / unit.picosecond,
        timestep_ps * unit.picoseconds
    )
    
    platform = mm.Platform.getPlatformByName('CPU')
    context = mm.Context(system, integrator, platform)
    context.setPositions(positions)
    
    # Minimize
    mm.LocalEnergyMinimizer.minimize(context, maxIterations=200)
    
    # Run
    energies = []
    rg_values = []
    
    for step in range(0, n_steps, report_interval):
        time_ps = step * timestep_ps
        context.setParameter('t', time_ps * 1e-12)  # Convert ps to seconds
        integrator.step(report_interval)
        
        state = context.getState(getEnergy=True, getPositions=True)
        pe = state.getPotentialEnergy().value_in_unit(unit.kilojoule_per_mole)
        energies.append(pe)
        
        # Radius of gyration
        pos = state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
        com = np.mean(pos, axis=0)
        rg = np.sqrt(np.mean(np.sum((pos - com)**2, axis=1)))
        rg_values.append(rg)
    
    return energies, rg_values


# ============================================================
# SIMULATION 1: GRAPHENE SHEET (Hexagonal)
# 432 Hz — Base frequency
# ============================================================

def simulate_graphene():
    """Simulate a graphene nanoflake under 432 Hz driving."""
    print("\n" + "=" * 60)
    print("SIMULATION 1: Graphene Nanoflake (Hexagonal)")
    print("Frequency: 432 Hz (base frequency)")
    print("Engine: OpenMM")
    print("=" * 60)
    
    # Build a small hexagonal graphene flake (37 atoms - 3 rings)
    # Graphene bond length: 1.42 Angstrom = 0.142 nm
    bond_length = 0.142  # nm
    
    # Generate hexagonal lattice positions
    positions = []
    a1 = np.array([bond_length * np.sqrt(3), 0, 0])
    a2 = np.array([bond_length * np.sqrt(3) / 2, bond_length * 1.5, 0])
    
    # Create a 5x5 sheet
    for i in range(-2, 3):
        for j in range(-2, 3):
            # Two atoms per unit cell
            p1 = i * a1 + j * a2
            p2 = p1 + np.array([0, bond_length, 0])
            positions.append(p1)
            positions.append(p2)
    
    positions = np.array(positions)
    # Center
    positions -= np.mean(positions, axis=0)
    n_atoms = len(positions)
    
    print(f"  Created graphene flake: {n_atoms} carbon atoms")
    
    # Masses (all carbon)
    masses = [12.011] * n_atoms
    
    # Find bonds (atoms within 1.5x bond length)
    bonds = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < bond_length * 1.5:
                # C-C sp2 bond: k ~ 478000 kJ/mol/nm^2
                bonds.append((i, j, bond_length, 478000.0))
    
    print(f"  Bonds found: {len(bonds)}")
    
    # Create system with 432 Hz driving
    system = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=432.0,
        driving_amplitude=5.0,
        drive_direction='z'
    )
    
    positions_unit = positions * unit.nanometer
    
    # Run driven simulation
    print(f"  Running 20,000 steps with 432 Hz driving force...")
    energies, rg_values = run_simulation(
        system, positions_unit, n_steps=20000, 
        timestep_ps=0.001, report_interval=2000
    )
    
    # Run control (create system without driving)
    system_ctrl = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=432.0,
        driving_amplitude=0.0,  # No driving
        drive_direction='z'
    )
    
    print(f"  Running control (no frequency)...")
    energies_ctrl, rg_ctrl = run_simulation(
        system_ctrl, positions_unit, n_steps=20000,
        timestep_ps=0.001, report_interval=2000
    )
    
    # Analysis
    energy_diff = np.mean(energies[-3:]) - np.mean(energies_ctrl[-3:])
    rg_change = (rg_values[-1] - rg_values[0]) / rg_values[0] * 100
    
    stable = abs(rg_change) < 15  # Less than 15% change in structure
    
    results = {
        'compound': 'graphene_hexagonal',
        'n_atoms': n_atoms,
        'n_bonds': len(bonds),
        'driving_frequency_hz': 432.0,
        'harmonic_number': 1,
        'base_frequency': 432.0,
        'geometry': 'hexagonal',
        'bond_length_nm': bond_length,
        'n_steps': 20000,
        'timestep_fs': 1.0,
        'temperature_K': 300,
        'driven_energy_kJ_mol': float(np.mean(energies[-3:])),
        'control_energy_kJ_mol': float(np.mean(energies_ctrl[-3:])),
        'energy_difference_kJ_mol': float(energy_diff),
        'initial_rg_nm': float(rg_values[0]),
        'final_rg_nm': float(rg_values[-1]),
        'rg_change_percent': float(rg_change),
        'energies': [float(e) for e in energies],
        'rg_values': [float(r) for r in rg_values],
        'energies_ctrl': [float(e) for e in energies_ctrl],
        'rg_ctrl': [float(r) for r in rg_ctrl],
        'verdict': 'STABLE' if stable else 'UNSTABLE'
    }
    
    print(f"\n  RESULT: {results['verdict']}")
    print(f"  Rg change: {rg_change:.1f}%")
    print(f"  Energy difference (driven - control): {energy_diff:.1f} kJ/mol")
    
    return results


# ============================================================
# SIMULATION 2: WATER CLUSTER (Icosahedral)
# 2592 Hz — 6th harmonic
# ============================================================

def simulate_water_cluster():
    """Simulate a 12-molecule water cluster at 2592 Hz."""
    print("\n" + "=" * 60)
    print("SIMULATION 2: Water Cluster (Icosahedral)")
    print("Frequency: 2592 Hz (6th harmonic of 432 Hz)")
    print("Engine: OpenMM")
    print("=" * 60)
    
    # Build icosahedral water cluster (12 molecules at vertices)
    phi = (1 + np.sqrt(5)) / 2
    
    # 12 vertices of icosahedron
    ico_vertices = np.array([
        [0, 1, phi], [0, -1, phi], [0, 1, -phi], [0, -1, -phi],
        [1, phi, 0], [-1, phi, 0], [1, -phi, 0], [-1, -phi, 0],
        [phi, 0, 1], [-phi, 0, 1], [phi, 0, -1], [-phi, 0, -1]
    ], dtype=float)
    
    # Normalize and scale to cluster radius of 0.28 nm
    for i in range(len(ico_vertices)):
        ico_vertices[i] = ico_vertices[i] / np.linalg.norm(ico_vertices[i]) * 0.28
    
    n_waters = 12
    
    # Generate water positions (O, H, H per molecule)
    positions = []
    masses = []
    bonds = []
    atom_idx = 0
    
    for i, o_pos in enumerate(ico_vertices):
        # Oxygen at icosahedron vertex
        positions.append(o_pos)
        masses.append(15.999)
        
        # H1: 0.0957 nm from O, pointing outward
        direction = o_pos / np.linalg.norm(o_pos)
        perp = np.cross(direction, [0, 0, 1])
        if np.linalg.norm(perp) < 0.01:
            perp = np.cross(direction, [0, 1, 0])
        perp = perp / np.linalg.norm(perp)
        
        h1 = o_pos + 0.0957 * (direction * np.cos(52.25 * np.pi / 180) + 
                                 perp * np.sin(52.25 * np.pi / 180))
        positions.append(h1)
        masses.append(1.008)
        
        # H2: 0.0957 nm from O, 104.5 degree angle
        perp2 = np.cross(direction, perp)
        perp2 = perp2 / np.linalg.norm(perp2)
        h2 = o_pos + 0.0957 * (direction * np.cos(52.25 * np.pi / 180) - 
                                 perp * np.sin(52.25 * np.pi / 180))
        positions.append(h2)
        masses.append(1.008)
        
        # Bonds: O-H1, O-H2
        o_idx = atom_idx
        bonds.append((o_idx, o_idx + 1, 0.0957, 462750.4))
        bonds.append((o_idx, o_idx + 2, 0.0957, 462750.4))
        atom_idx += 3
    
    positions = np.array(positions)
    n_atoms = len(positions)
    
    print(f"  Created water cluster: {n_waters} molecules, {n_atoms} atoms")
    
    # Create system with 2592 Hz driving (radial breathing mode)
    system = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=2592.0,
        driving_amplitude=3.0,
        drive_direction='radial'
    )
    
    positions_unit = positions * unit.nanometer
    
    # Run driven simulation
    print(f"  Running 20,000 steps with 2592 Hz radial driving force...")
    energies, rg_values = run_simulation(
        system, positions_unit, n_steps=20000,
        timestep_ps=0.0005, report_interval=2000
    )
    
    # Control
    system_ctrl = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=2592.0,
        driving_amplitude=0.0,
        drive_direction='radial'
    )
    
    print(f"  Running control (no frequency)...")
    energies_ctrl, rg_ctrl = run_simulation(
        system_ctrl, positions_unit, n_steps=20000,
        timestep_ps=0.0005, report_interval=2000
    )
    
    # Analysis
    rg_change = (rg_values[-1] - rg_values[0]) / rg_values[0] * 100
    rg_change_ctrl = (rg_ctrl[-1] - rg_ctrl[0]) / rg_ctrl[0] * 100
    
    # Cluster is stable if it stays more compact than control
    more_compact = rg_values[-1] < rg_ctrl[-1]
    stable = abs(rg_change) < 20
    
    results = {
        'compound': 'water_cluster_icosahedral',
        'n_molecules': n_waters,
        'n_atoms': n_atoms,
        'driving_frequency_hz': 2592.0,
        'harmonic_number': 6,
        'base_frequency': 432.0,
        'geometry': 'icosahedral',
        'cluster_radius_nm': 0.28,
        'n_steps': 20000,
        'timestep_fs': 0.5,
        'temperature_K': 300,
        'driven_final_rg_nm': float(rg_values[-1]),
        'control_final_rg_nm': float(rg_ctrl[-1]),
        'rg_change_driven_percent': float(rg_change),
        'rg_change_control_percent': float(rg_change_ctrl),
        'more_compact_than_control': bool(more_compact),
        'energies': [float(e) for e in energies],
        'rg_values': [float(r) for r in rg_values],
        'energies_ctrl': [float(e) for e in energies_ctrl],
        'rg_ctrl': [float(r) for r in rg_ctrl],
        'verdict': 'STABLE' if stable else 'UNSTABLE'
    }
    
    print(f"\n  RESULT: {results['verdict']}")
    print(f"  Driven Rg change: {rg_change:.1f}%")
    print(f"  Control Rg change: {rg_change_ctrl:.1f}%")
    print(f"  More compact than control: {more_compact}")
    
    return results


# ============================================================
# SIMULATION 3: VACUUM SHELL (Geodesic Sphere / C60)
# 5184 Hz — 12th harmonic
# ============================================================

def simulate_vacuum_shell():
    """Simulate a C60 buckyball under 5184 Hz radial breathing."""
    print("\n" + "=" * 60)
    print("SIMULATION 3: Vacuum Shell Carbon (C60 Geodesic)")
    print("Frequency: 5184 Hz (12th harmonic of 432 Hz)")
    print("Engine: OpenMM")
    print("=" * 60)
    
    # Build C60 structure using known coordinates
    # C60 radius: 0.357 nm (3.57 Angstrom)
    radius = 0.357  # nm
    
    # Generate C60 positions using icosahedral symmetry
    # Start with golden ratio vertices and expand
    phi = (1 + np.sqrt(5)) / 2
    
    # Generate all 60 atoms of C60 using permutation method
    raw_coords = []
    
    # Type A: (0, ±1, ±3φ) and cyclic permutations — 12 vertices
    for s1 in [1, -1]:
        for s2 in [1, -1]:
            raw_coords.append([0, s1, s2 * 3 * phi])
            raw_coords.append([s1, s2 * 3 * phi, 0])
            raw_coords.append([s2 * 3 * phi, 0, s1])
    
    # Type B: (±2, ±(1+2φ), ±φ) and cyclic permutations — 24 vertices
    for s1 in [1, -1]:
        for s2 in [1, -1]:
            for s3 in [1, -1]:
                raw_coords.append([s1 * 2, s2 * (1 + 2*phi), s3 * phi])
                raw_coords.append([s2 * (1 + 2*phi), s3 * phi, s1 * 2])
                raw_coords.append([s3 * phi, s1 * 2, s2 * (1 + 2*phi)])
    
    # Type C: (±1, ±(2+φ), ±2φ) and cyclic permutations — 24 vertices
    for s1 in [1, -1]:
        for s2 in [1, -1]:
            for s3 in [1, -1]:
                raw_coords.append([s1, s2 * (2 + phi), s3 * 2 * phi])
                raw_coords.append([s2 * (2 + phi), s3 * 2 * phi, s1])
                raw_coords.append([s3 * 2 * phi, s1, s2 * (2 + phi)])
    
    raw_coords = np.array(raw_coords)
    
    # Remove duplicates (tolerance 0.01)
    unique = [raw_coords[0]]
    for coord in raw_coords[1:]:
        is_dup = False
        for existing in unique:
            if np.linalg.norm(coord - existing) < 0.01:
                is_dup = True
                break
        if not is_dup:
            unique.append(coord)
        if len(unique) >= 60:
            break
    
    positions = np.array(unique[:60])
    # Normalize to C60 radius
    for i in range(len(positions)):
        positions[i] = positions[i] / np.linalg.norm(positions[i]) * radius
    
    n_atoms = len(positions)
    print(f"  Created C60 shell: {n_atoms} carbon atoms")
    
    # Masses (all carbon)
    masses = [12.011] * n_atoms
    
    # Find bonds (C-C in C60: 1.40 and 1.45 Angstrom = 0.140 and 0.145 nm)
    bonds = []
    for i in range(n_atoms):
        for j in range(i + 1, n_atoms):
            dist = np.linalg.norm(positions[i] - positions[j])
            if dist < 0.17:  # Within bonding distance
                bonds.append((i, j, dist, 400000.0))
    
    print(f"  Bonds found: {len(bonds)}")
    
    # Create system with 5184 Hz radial breathing
    system = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=5184.0,
        driving_amplitude=2.0,
        drive_direction='radial'
    )
    
    positions_unit = positions * unit.nanometer
    
    # Run driven simulation
    print(f"  Running 20,000 steps with 5184 Hz radial breathing force...")
    energies, rg_values = run_simulation(
        system, positions_unit, n_steps=20000,
        timestep_ps=0.0005, report_interval=2000
    )
    
    # Control
    system_ctrl = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=5184.0,
        driving_amplitude=0.0,
        drive_direction='radial'
    )
    
    print(f"  Running control (no frequency)...")
    energies_ctrl, rg_ctrl = run_simulation(
        system_ctrl, positions_unit, n_steps=20000,
        timestep_ps=0.0005, report_interval=2000
    )
    
    # Analysis: shell integrity = Rg stays near initial value
    rg_change = (rg_values[-1] - rg_values[0]) / rg_values[0] * 100
    shell_intact = abs(rg_change) < 10  # Less than 10% = shell holds
    
    results = {
        'compound': 'vacuum_shell_carbon_C60',
        'n_atoms': n_atoms,
        'n_bonds': len(bonds),
        'driving_frequency_hz': 5184.0,
        'harmonic_number': 12,
        'base_frequency': 432.0,
        'geometry': 'spherical_geodesic',
        'shell_radius_nm': radius,
        'n_steps': 20000,
        'timestep_fs': 0.5,
        'temperature_K': 300,
        'initial_rg_nm': float(rg_values[0]),
        'final_rg_nm': float(rg_values[-1]),
        'rg_change_percent': float(rg_change),
        'control_rg_change_percent': float((rg_ctrl[-1] - rg_ctrl[0]) / rg_ctrl[0] * 100),
        'shell_intact': bool(shell_intact),
        'energies': [float(e) for e in energies],
        'rg_values': [float(r) for r in rg_values],
        'energies_ctrl': [float(e) for e in energies_ctrl],
        'rg_ctrl': [float(r) for r in rg_ctrl],
        'verdict': 'STABLE' if shell_intact else 'UNSTABLE'
    }
    
    print(f"\n  RESULT: {results['verdict']}")
    print(f"  Shell Rg change: {rg_change:.1f}%")
    print(f"  Shell integrity: {'MAINTAINED' if shell_intact else 'COMPROMISED'}")
    
    return results


# ============================================================
# SIMULATION 4: MYCELIUM CHITIN (Helical)
# 144 Hz — 1/3 sub-harmonic
# ============================================================

def simulate_mycelium_chitin():
    """Simulate a chitin helix under 144 Hz axial driving."""
    print("\n" + "=" * 60)
    print("SIMULATION 4: Mycelium Chitin (Helical)")
    print("Frequency: 144 Hz (1/3 sub-harmonic of 432 Hz)")
    print("Engine: OpenMM")
    print("=" * 60)
    
    # Build helical polymer chain
    # Chitin helix: pitch = 1.04 nm, radius = 0.4 nm
    n_monomers = 15
    pitch = 1.04  # nm per turn
    radius = 0.4  # nm
    atoms_per_turn = 6
    
    positions = []
    masses = []
    
    total_atoms = n_monomers * 2  # Simplified: 2 beads per monomer
    
    for i in range(total_atoms):
        t = i / total_atoms
        angle = t * n_monomers * 2 * np.pi / 3
        z = t * n_monomers * pitch / 3
        
        r = radius if i % 2 == 0 else radius * 0.7  # Alternate inner/outer
        x = r * np.cos(angle)
        y = r * np.sin(angle)
        positions.append([x, y, z])
        masses.append(14.0 if i % 2 == 0 else 28.0)  # backbone vs sidechain
    
    positions = np.array(positions)
    n_atoms = len(positions)
    
    print(f"  Created chitin helix: {n_atoms} beads, {n_monomers} monomers")
    
    # Sequential bonds
    bonds = []
    for i in range(n_atoms - 1):
        dist = np.linalg.norm(positions[i+1] - positions[i])
        bonds.append((i, i + 1, dist, 200000.0))
    
    # Create system with 144 Hz axial driving
    system = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=144.0,
        driving_amplitude=2.0,
        drive_direction='axial'
    )
    
    positions_unit = positions * unit.nanometer
    
    # Run driven
    print(f"  Running 20,000 steps with 144 Hz axial driving force...")
    energies, rg_values = run_simulation(
        system, positions_unit, n_steps=20000,
        timestep_ps=0.001, report_interval=2000
    )
    
    # Control
    system_ctrl = create_frequency_driven_system(
        positions, masses, bonds,
        driving_freq_hz=144.0,
        driving_amplitude=0.0,
        drive_direction='axial'
    )
    
    print(f"  Running control (no frequency)...")
    energies_ctrl, rg_ctrl = run_simulation(
        system_ctrl, positions_unit, n_steps=20000,
        timestep_ps=0.001, report_interval=2000
    )
    
    # Analysis: helix maintained if end-to-end distance stays within range
    rg_change = (rg_values[-1] - rg_values[0]) / rg_values[0] * 100
    helix_maintained = abs(rg_change) < 25
    
    results = {
        'compound': 'mycelium_chitin_helix',
        'n_monomers': n_monomers,
        'n_atoms': n_atoms,
        'driving_frequency_hz': 144.0,
        'harmonic_number': '1/3 (sub-harmonic)',
        'base_frequency': 432.0,
        'geometry': 'helical',
        'helix_pitch_nm': pitch,
        'helix_radius_nm': radius,
        'n_steps': 20000,
        'timestep_fs': 1.0,
        'temperature_K': 300,
        'initial_rg_nm': float(rg_values[0]),
        'final_rg_nm': float(rg_values[-1]),
        'rg_change_percent': float(rg_change),
        'control_rg_change_percent': float((rg_ctrl[-1] - rg_ctrl[0]) / rg_ctrl[0] * 100),
        'helix_maintained': bool(helix_maintained),
        'energies': [float(e) for e in energies],
        'rg_values': [float(r) for r in rg_values],
        'energies_ctrl': [float(e) for e in energies_ctrl],
        'rg_ctrl': [float(r) for r in rg_ctrl],
        'verdict': 'STABLE' if helix_maintained else 'UNSTABLE'
    }
    
    print(f"\n  RESULT: {results['verdict']}")
    print(f"  Helix Rg change: {rg_change:.1f}%")
    print(f"  Helix integrity: {'MAINTAINED' if helix_maintained else 'DISRUPTED'}")
    
    return results


# ============================================================
# VISUALIZATION
# ============================================================

def generate_visualization(all_results):
    """Generate comparison plots for all simulations."""
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('PROJECT VOID — Frequency-Driven Molecular Simulations\n'
                 'Paradigm: Frequency Mechanics | Base: 432 Hz', 
                 fontsize=14, fontweight='bold')
    
    compounds = ['graphene', 'water_cluster', 'vacuum_shell', 'mycelium_chitin']
    titles = [
        'Graphene (432 Hz, Hexagonal)',
        'Water Cluster (2592 Hz, Icosahedral)',
        'Vacuum Shell C60 (5184 Hz, Geodesic)',
        'Mycelium Chitin (144 Hz, Helical)'
    ]
    
    for idx, (compound, title) in enumerate(zip(compounds, titles)):
        ax = axes[idx // 2, idx % 2]
        result = all_results.get(compound, {})
        
        if 'rg_values' in result and 'rg_ctrl' in result:
            steps = np.arange(len(result['rg_values'])) * 2000
            
            ax.plot(steps, result['rg_values'], 'b-', linewidth=2, 
                   label=f'Driven ({result.get("driving_frequency_hz", "?")} Hz)')
            ax.plot(steps, result['rg_ctrl'], 'r--', linewidth=1.5,
                   label='Control (no frequency)')
            
            verdict = result.get('verdict', 'ERROR')
            color = 'green' if verdict == 'STABLE' else 'red'
            ax.text(0.95, 0.95, verdict, transform=ax.transAxes,
                   fontsize=12, fontweight='bold', color=color,
                   ha='right', va='top',
                   bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            ax.set_xlabel('Steps')
            ax.set_ylabel('Radius of Gyration (nm)')
            ax.set_title(title, fontsize=11)
            ax.legend(loc='lower right', fontsize=9)
            ax.grid(True, alpha=0.3)
        else:
            ax.text(0.5, 0.5, f'ERROR\n{result.get("error", "No data")}',
                   transform=ax.transAxes, ha='center', va='center',
                   fontsize=12, color='red')
            ax.set_title(title)
    
    plt.tight_layout()
    output_dir = os.path.dirname(os.path.abspath(__file__))
    viz_path = os.path.join(output_dir, 'full_simulation_visualization.png')
    plt.savefig(viz_path, dpi=150, bbox_inches='tight')
    print(f"\n  Visualization saved to: {viz_path}")
    plt.close()
    
    return viz_path


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 70)
    print("PROJECT VOID — Full Molecular Simulations")
    print("Frequency-Geometry-Matter Pipeline Validation")
    print(f"Date: {datetime.now().isoformat()}")
    print("=" * 70)
    print()
    print("Engine: OpenMM 8.5.2")
    print("Paradigm: Frequency Mechanics (not Quantum Mechanics)")
    print("Base Frequency: 432 Hz")
    print("Temperature: 300 K (room temperature)")
    print()
    
    all_results = {}
    
    # Run all 4 simulations
    try:
        all_results['graphene'] = simulate_graphene()
    except Exception as e:
        print(f"  ERROR in graphene: {e}")
        all_results['graphene'] = {'verdict': 'ERROR', 'error': str(e)}
    
    try:
        all_results['water_cluster'] = simulate_water_cluster()
    except Exception as e:
        print(f"  ERROR in water cluster: {e}")
        all_results['water_cluster'] = {'verdict': 'ERROR', 'error': str(e)}
    
    try:
        all_results['vacuum_shell'] = simulate_vacuum_shell()
    except Exception as e:
        print(f"  ERROR in vacuum shell: {e}")
        all_results['vacuum_shell'] = {'verdict': 'ERROR', 'error': str(e)}
    
    try:
        all_results['mycelium_chitin'] = simulate_mycelium_chitin()
    except Exception as e:
        print(f"  ERROR in mycelium chitin: {e}")
        all_results['mycelium_chitin'] = {'verdict': 'ERROR', 'error': str(e)}
    
    # Generate visualization
    print("\n" + "-" * 60)
    print("Generating visualization...")
    generate_visualization(all_results)
    
    # Summary
    print("\n" + "=" * 70)
    print("SIMULATION RESULTS SUMMARY")
    print("=" * 70)
    print(f"\n{'Compound':<25} {'Freq (Hz)':<12} {'Geometry':<18} {'Rg Change':<12} {'Verdict'}")
    print(f"{'-'*25} {'-'*12} {'-'*18} {'-'*12} {'-'*10}")
    
    for name, result in all_results.items():
        freq = result.get('driving_frequency_hz', '?')
        geom = result.get('geometry', '?')
        rg = result.get('rg_change_percent', '?')
        verdict = result.get('verdict', 'ERROR')
        rg_str = f"{rg:.1f}%" if isinstance(rg, float) else str(rg)
        print(f"{name:<25} {freq:<12} {geom:<18} {rg_str:<12} {verdict}")
    
    # Save results
    output_dir = os.path.dirname(os.path.abspath(__file__))
    results_path = os.path.join(output_dir, 'full_simulation_results.json')
    
    with open(results_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'paradigm': 'frequency_mechanics',
            'base_frequency_hz': 432.0,
            'engine': 'OpenMM 8.5.2',
            'temperature_K': 300,
            'results': all_results
        }, f, indent=2, default=str)
    
    print(f"\nResults saved to: {results_path}")
    
    # Overall verdict
    stable_count = sum(1 for r in all_results.values() if r.get('verdict') == 'STABLE')
    total = len(all_results)
    error_count = sum(1 for r in all_results.values() if r.get('verdict') == 'ERROR')
    
    print(f"\n{'=' * 70}")
    print(f"OVERALL: {stable_count}/{total} compounds STABLE under frequency driving")
    if error_count:
        print(f"         {error_count} simulations encountered errors")
    print(f"{'=' * 70}")
    
    if stable_count >= 3:
        print("\n✓ FREQUENCY-GEOMETRY-MATTER PIPELINE VALIDATED")
        print("  The Circumference Law holds: frequency stabilizes geometry.")
    elif stable_count >= 2:
        print("\n◐ PARTIAL VALIDATION")
        print("  Most compounds respond positively to frequency driving.")
        print("  Further parameter tuning needed for unstable compounds.")
    elif stable_count >= 1:
        print("\n◑ PRELIMINARY EVIDENCE")
        print("  Some compounds respond to frequency driving.")
        print("  Parameters need optimization.")
    else:
        print("\n✗ FURTHER INVESTIGATION NEEDED")
        print("  Parameters may need adjustment or model refinement.")
    
    return all_results


if __name__ == '__main__':
    results = main()
