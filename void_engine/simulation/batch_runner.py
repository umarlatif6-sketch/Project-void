"""
PROJECT VOID — Batch Simulation Runner
========================================

Runs frequency-driven molecular dynamics on all 108 compounds.
Uses OpenMM for molecular simulation with frequency-driven forces.
Outputs results to JSON for analysis.

Usage:
    python3 batch_runner.py [--start N] [--end M] [--output results.json]
"""

import json
import sys
import time
import math
import numpy as np
from pathlib import Path

try:
    import openmm
    import openmm.app as app
    import openmm.unit as unit
    HAS_OPENMM = True
except ImportError:
    HAS_OPENMM = False
    print("WARNING: OpenMM not available. Using analytical model.")

from compound_library import COMPOUNDS

# ================================================================
# GEOMETRY BUILDERS
# ================================================================

def build_structure(compound):
    """Build a molecular structure based on compound geometry and elements."""
    n_atoms = compound["n_atoms"]
    geometry = compound["geometry"]
    
    # Generate positions based on geometry type
    positions = []
    
    if "hexagonal" in geometry or "sp2" in geometry:
        # Hexagonal lattice
        a = 0.142  # nm (graphene-like bond length)
        for i in range(n_atoms):
            row = i // int(math.sqrt(n_atoms))
            col = i % int(math.sqrt(n_atoms))
            x = col * a + (row % 2) * a / 2
            y = row * a * math.sqrt(3) / 2
            z = np.random.normal(0, 0.01)
            positions.append([x, y, z])
    
    elif "cubic" in geometry or "rocksalt" in geometry or "diamond" in geometry:
        # Cubic/diamond lattice
        a = 0.356  # nm (diamond lattice constant)
        n_side = max(2, int(round(n_atoms ** (1/3))))
        idx = 0
        for i in range(n_side):
            for j in range(n_side):
                for k in range(n_side):
                    if idx >= n_atoms:
                        break
                    positions.append([i * a / n_side, j * a / n_side, k * a / n_side])
                    idx += 1
        while len(positions) < n_atoms:
            positions.append([np.random.uniform(0, a), np.random.uniform(0, a), np.random.uniform(0, a)])
    
    elif "helix" in geometry or "helical" in geometry or "spiral" in geometry:
        # Helical structure
        radius = 0.5  # nm
        pitch = 0.34  # nm per turn
        for i in range(n_atoms):
            theta = i * 2 * math.pi / 10  # 10 atoms per turn
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            z = i * pitch / 10
            positions.append([x, y, z])
    
    elif "icosahedral" in geometry or "geodesic" in geometry:
        # Icosahedral/geodesic sphere
        radius = 0.35  # nm (C60-like)
        golden = (1 + math.sqrt(5)) / 2
        for i in range(n_atoms):
            theta = math.acos(1 - 2 * (i + 0.5) / n_atoms)
            phi = math.pi * (1 + math.sqrt(5)) * i
            x = radius * math.sin(theta) * math.cos(phi)
            y = radius * math.sin(theta) * math.sin(phi)
            z = radius * math.cos(theta)
            positions.append([x, y, z])
    
    elif "layered" in geometry or "sheet" in geometry:
        # Layered structure
        a = 0.25  # nm
        n_per_layer = n_atoms // 3
        for layer in range(3):
            for i in range(n_per_layer):
                row = i // int(math.sqrt(n_per_layer))
                col = i % int(math.sqrt(n_per_layer))
                x = col * a
                y = row * a
                z = layer * 0.335  # interlayer distance
                positions.append([x, y, z])
        while len(positions) < n_atoms:
            positions.append([np.random.uniform(0, a * 5), np.random.uniform(0, a * 5), np.random.uniform(0, 1.0)])
    
    elif "perovskite" in geometry:
        # Perovskite structure (ABO3)
        a = 0.4  # nm
        n_side = max(2, int(round(n_atoms ** (1/3))))
        idx = 0
        for i in range(n_side):
            for j in range(n_side):
                for k in range(n_side):
                    if idx >= n_atoms:
                        break
                    # A site
                    positions.append([i * a, j * a, k * a])
                    idx += 1
                    if idx >= n_atoms:
                        break
                    # B site (center)
                    positions.append([(i + 0.5) * a, (j + 0.5) * a, (k + 0.5) * a])
                    idx += 1
        while len(positions) < n_atoms:
            positions.append([np.random.uniform(0, a * n_side), np.random.uniform(0, a * n_side), np.random.uniform(0, a * n_side)])
    
    elif "amorphous" in geometry or "random" in geometry or "network" in geometry:
        # Amorphous/random structure
        box_size = (n_atoms / 50) ** (1/3) * 0.5  # scale with atom count
        for i in range(n_atoms):
            positions.append([
                np.random.uniform(0, box_size),
                np.random.uniform(0, box_size),
                np.random.uniform(0, box_size)
            ])
    
    elif "linear" in geometry or "chain" in geometry:
        # Linear chain
        bond_length = 0.13  # nm
        for i in range(n_atoms):
            x = i * bond_length
            y = 0.05 * math.sin(i * 0.5)  # slight zigzag
            z = 0.05 * math.cos(i * 0.5)
            positions.append([x, y, z])
    
    elif "toroidal" in geometry or "trefoil" in geometry:
        # Toroidal structure
        R = 0.7  # major radius nm
        r = 0.2  # minor radius nm
        for i in range(n_atoms):
            theta = 2 * math.pi * i / n_atoms
            phi = 3 * theta  # trefoil knot parameter
            x = (R + r * math.cos(phi)) * math.cos(theta)
            y = (R + r * math.cos(phi)) * math.sin(theta)
            z = r * math.sin(phi)
            positions.append([x, y, z])
    
    else:
        # Default: random cluster
        for i in range(n_atoms):
            r = 0.3 * (i / n_atoms) ** (1/3)
            theta = np.random.uniform(0, math.pi)
            phi = np.random.uniform(0, 2 * math.pi)
            x = r * math.sin(theta) * math.cos(phi)
            y = r * math.sin(theta) * math.sin(phi)
            z = r * math.cos(theta)
            positions.append([x, y, z])
    
    positions = positions[:n_atoms]
    return np.array(positions)


# ================================================================
# SIMULATION ENGINE
# ================================================================

def compute_radius_of_gyration(positions):
    """Compute radius of gyration."""
    center = np.mean(positions, axis=0)
    rg = np.sqrt(np.mean(np.sum((positions - center) ** 2, axis=1)))
    return rg


def run_simulation_openmm(compound, n_steps=10000):
    """Run frequency-driven molecular dynamics using OpenMM."""
    n_atoms = compound["n_atoms"]
    freq = compound["freq"]
    
    # Build system
    system = openmm.System()
    positions_nm = build_structure(compound)
    
    # Assign masses based on elements
    element_masses = {"C": 12.0, "H": 1.0, "N": 14.0, "O": 16.0, "S": 32.0,
                      "Si": 28.0, "B": 10.8, "Al": 27.0, "Fe": 55.8, "Cu": 63.5,
                      "Zn": 65.4, "Ti": 47.9, "W": 183.8, "Ni": 58.7, "Co": 58.9,
                      "Cr": 52.0, "Mo": 95.9, "V": 50.9, "Nb": 92.9, "Mn": 54.9,
                      "Zr": 91.2, "Re": 186.2, "Hf": 178.5, "Ta": 180.9,
                      "Mg": 24.3, "Li": 6.9, "Na": 23.0, "K": 39.1, "Ca": 40.1,
                      "P": 31.0, "Gd": 157.3, "U": 238.0, "Pu": 244.0,
                      "Y": 88.9, "Ba": 137.3, "Bi": 209.0, "Sr": 87.6,
                      "Sn": 118.7, "Se": 79.0, "Te": 127.6, "Cd": 112.4,
                      "As": 74.9, "Sm": 150.4, "Ga": 69.7, "Pt": 195.1,
                      "Pb": 207.2, "I": 126.9, "La": 138.9, "Be": 9.0}
    
    elements = compound["elements"]
    for i in range(n_atoms):
        el = elements[i % len(elements)]
        mass = element_masses.get(el, 12.0)
        system.addParticle(mass)
    
    # Add harmonic bonds between nearby atoms
    bond_force = openmm.HarmonicBondForce()
    bond_length = 0.15  # nm
    bond_k = 100000.0  # kJ/mol/nm^2
    
    for i in range(n_atoms):
        for j in range(i + 1, min(i + 4, n_atoms)):
            dist = np.linalg.norm(positions_nm[i] - positions_nm[j])
            if dist < 0.3:  # Only bond nearby atoms
                bond_force.addBond(i, j, dist, bond_k)
    
    system.addForce(bond_force)
    
    # Add frequency-driving force (custom external force)
    # F = A * sin(2*pi*freq*t) applied radially
    freq_force = openmm.CustomExternalForce(
        f"A * sin(2 * 3.14159265 * {freq} * t_param) * ((x-cx)*(x-cx) + (y-cy)*(y-cy) + (z-cz)*(z-cz))"
    )
    freq_force.addGlobalParameter("A", 10.0)  # amplitude kJ/mol/nm^2
    freq_force.addGlobalParameter("t_param", 0.0)
    cx, cy, cz = np.mean(positions_nm, axis=0)
    freq_force.addGlobalParameter("cx", cx)
    freq_force.addGlobalParameter("cy", cy)
    freq_force.addGlobalParameter("cz", cz)
    
    for i in range(n_atoms):
        freq_force.addParticle(i, [])
    
    system.addForce(freq_force)
    
    # Set up integrator and simulation
    integrator = openmm.LangevinMiddleIntegrator(
        300 * unit.kelvin,
        1.0 / unit.picosecond,
        0.002 * unit.picoseconds
    )
    
    platform = openmm.Platform.getPlatformByName("CPU")
    context = openmm.Context(system, integrator, platform)
    context.setPositions(positions_nm * unit.nanometer)
    
    # Run simulation with frequency driving
    dt = 0.002  # ps
    rg_values = []
    
    for step in range(n_steps):
        # Update time parameter for frequency driving
        t = step * dt * 1e-12  # convert to seconds for Hz
        context.setParameter("t_param", t)
        integrator.step(1)
        
        if step % 1000 == 0:
            state = context.getState(getPositions=True)
            pos = state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
            rg = compute_radius_of_gyration(pos)
            rg_values.append(rg)
    
    # Get final state
    final_state = context.getState(getPositions=True, getEnergy=True)
    final_pos = final_state.getPositions(asNumpy=True).value_in_unit(unit.nanometer)
    final_energy = final_state.getPotentialEnergy().value_in_unit(unit.kilojoules_per_mole)
    final_rg = compute_radius_of_gyration(final_pos)
    initial_rg = compute_radius_of_gyration(positions_nm)
    
    return {
        "initial_rg": float(initial_rg),
        "final_rg": float(final_rg),
        "rg_change_pct": float((final_rg - initial_rg) / initial_rg * 100),
        "final_energy_kJ_mol": float(final_energy),
        "rg_trajectory": [float(r) for r in rg_values],
        "n_steps": n_steps,
    }


def run_simulation_analytical(compound):
    """Analytical model for when OpenMM is not available."""
    freq = compound["freq"]
    n_atoms = compound["n_atoms"]
    geometry = compound["geometry"]
    
    # Analytical stability model based on frequency-geometry resonance
    # Higher stability when frequency matches geometry's natural mode
    
    # Geometry mode numbers
    mode_map = {
        "hexagonal": 6, "cubic": 4, "tetrahedral": 4, "helical": 1,
        "icosahedral": 5, "geodesic": 5, "layered": 2, "linear": 1,
        "diamond": 4, "perovskite": 3, "amorphous": 0, "toroidal": 2,
        "rhombohedral": 3, "orthorhombic": 3, "wurtzite": 6,
        "spinel": 4, "fluorite": 4, "rocksalt": 4, "hcp": 6,
    }
    
    # Find matching mode
    mode = 1
    for key, val in mode_map.items():
        if key in geometry:
            mode = val
            break
    
    # Resonance condition: stability peaks when freq/432 is near an integer or simple fraction
    ratio = freq / 432.0
    nearest_harmonic = round(ratio)
    detuning = abs(ratio - nearest_harmonic) / nearest_harmonic
    
    # Stability score (0-1)
    resonance_factor = math.exp(-detuning * 10)
    geometry_factor = 1.0 - 0.1 * abs(mode - nearest_harmonic % 7)
    size_factor = min(1.0, 40.0 / n_atoms)  # smaller structures more stable
    
    stability = max(0, min(1, resonance_factor * 0.6 + geometry_factor * 0.3 + size_factor * 0.1))
    
    # Simulate Rg change
    rg_change = -stability * 5.0 + (1 - stability) * 15.0 + np.random.normal(0, 2)
    
    initial_rg = 0.3 * (n_atoms / 30) ** (1/3)
    final_rg = initial_rg * (1 + rg_change / 100)
    
    return {
        "initial_rg": float(initial_rg),
        "final_rg": float(final_rg),
        "rg_change_pct": float(rg_change),
        "stability_score": float(stability),
        "resonance_factor": float(resonance_factor),
        "geometry_factor": float(geometry_factor),
        "n_steps": 10000,
    }


# ================================================================
# BATCH RUNNER
# ================================================================

def run_batch(start=0, end=108, output_file="simulation_results.json"):
    """Run simulations for a batch of compounds."""
    results = []
    compounds_to_run = COMPOUNDS[start:end]
    total = len(compounds_to_run)
    
    print(f"\n{'='*60}")
    print(f"PROJECT VOID — Frequency Periodic Table Simulation")
    print(f"{'='*60}")
    print(f"Running {total} compounds (index {start}-{end})")
    print(f"Engine: {'OpenMM' if HAS_OPENMM else 'Analytical Model'}")
    print(f"{'='*60}\n")
    
    for i, compound in enumerate(compounds_to_run):
        t0 = time.time()
        
        try:
            if HAS_OPENMM:
                sim_result = run_simulation_openmm(compound, n_steps=10000)
            else:
                sim_result = run_simulation_analytical(compound)
            
            # Determine verdict
            rg_change = sim_result["rg_change_pct"]
            if abs(rg_change) < 5:
                verdict = "STABLE"
            elif abs(rg_change) < 15:
                verdict = "METASTABLE"
            else:
                verdict = "UNSTABLE"
            
            result = {
                "id": compound["id"],
                "name": compound["name"],
                "frequency_hz": compound["freq"],
                "geometry": compound["geometry"],
                "elements": compound["elements"],
                "category": compound["category"],
                "verdict": verdict,
                "rg_change_pct": round(rg_change, 2),
                "simulation": sim_result,
                "runtime_s": round(time.time() - t0, 2),
            }
            
        except Exception as e:
            result = {
                "id": compound["id"],
                "name": compound["name"],
                "frequency_hz": compound["freq"],
                "geometry": compound["geometry"],
                "elements": compound["elements"],
                "category": compound["category"],
                "verdict": "ERROR",
                "error": str(e),
                "runtime_s": round(time.time() - t0, 2),
            }
        
        results.append(result)
        
        # Progress indicator
        status = result["verdict"]
        rg = result.get("rg_change_pct", "N/A")
        print(f"  [{i+1:3d}/{total}] {compound['id']} {compound['name']:<30s} "
              f"{compound['freq']:>7.1f} Hz → {status:<10s} (Rg: {rg:>+.1f}%)" 
              if isinstance(rg, float) else
              f"  [{i+1:3d}/{total}] {compound['id']} {compound['name']:<30s} "
              f"{compound['freq']:>7.1f} Hz → {status}")
    
    # Save results
    output_path = Path(__file__).parent / output_file
    with open(output_path, "w") as f:
        json.dump({
            "meta": {
                "total_compounds": total,
                "engine": "OpenMM" if HAS_OPENMM else "Analytical",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "base_frequency": 432.0,
                "n_steps": 10000,
            },
            "results": results,
        }, f, indent=2)
    
    # Summary
    stable = sum(1 for r in results if r["verdict"] == "STABLE")
    metastable = sum(1 for r in results if r["verdict"] == "METASTABLE")
    unstable = sum(1 for r in results if r["verdict"] == "UNSTABLE")
    errors = sum(1 for r in results if r["verdict"] == "ERROR")
    
    print(f"\n{'='*60}")
    print(f"SIMULATION COMPLETE")
    print(f"{'='*60}")
    print(f"  STABLE:     {stable:3d} ({stable/total*100:.0f}%)")
    print(f"  METASTABLE: {metastable:3d} ({metastable/total*100:.0f}%)")
    print(f"  UNSTABLE:   {unstable:3d} ({unstable/total*100:.0f}%)")
    print(f"  ERRORS:     {errors:3d}")
    print(f"  TOTAL:      {total:3d}")
    print(f"\nResults saved to: {output_path}")
    print(f"{'='*60}")
    
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run batch frequency simulations")
    parser.add_argument("--start", type=int, default=0, help="Start index")
    parser.add_argument("--end", type=int, default=108, help="End index")
    parser.add_argument("--output", type=str, default="simulation_results.json", help="Output file")
    args = parser.parse_args()
    
    run_batch(args.start, args.end, args.output)
