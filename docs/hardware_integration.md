# Hardware Integration: Solar Harvester & WiFi CSI Mycelium Monitor

*Written for the InteRussia Fellowship Application — PROJECT VOID, Novosibirsk Node (Gridul-286)*

---

## Overview

PROJECT VOID's Sovereign Node is designed to operate indefinitely without dependence on the grid, institutional infrastructure, or external compute resources. Two complementary hardware layers make this possible: a dual-mode solar harvester that converts sunlight into either electrical power or building heat depending on the season, and an ESP32-based WiFi sensing system that reads the biological health of the machine's wooden enclosure by measuring how living mycelium disturbs radio signals passing through the wood.

Together these systems turn a physical machine into something genuinely novel: a computation node that is powered by the sun, monitored by fungi, and capable of running autonomously through a Siberian winter.

---

## 1. Dual-Mode Solar Harvester

### What it does

A standard solar panel converts sunlight into electricity. A solar thermal panel converts sunlight into heat. The harvester described here does both — but not at the same time. It switches automatically between the two modes depending on ambient temperature.

When outdoor temperatures are above 15 °C (the "crossover point"), the harvester operates its thin-film photovoltaic layer and feeds electricity directly to the node's internal flywheel energy reserve. The panels achieve approximately 18% efficiency under these conditions, producing a peak output of around 367 W from a 2.4 m² aperture — enough to run the node indefinitely during Siberian summer daylight hours.

When outdoor temperatures drop below 15 °C, running photovoltaics becomes less efficient than simply using the sunlight as heat. At that point the harvester switches to its selective absorber coating, which captures up to 90% of incident solar energy as thermal energy. This heat is directed into the machine enclosure, keeping the biological substrate (the mycelium bed, the aquaponics water, and the silk wiring contacts) within their optimal temperature ranges without drawing any electricity from the flywheel reserve.

### Why it matters

Most off-grid compute nodes either run on batteries that need replacing or rely on diesel generators. The dual-mode harvester eliminates both dependencies. In summer it generates more electricity than the node consumes at idle. In winter it drastically reduces the heating energy budget, which is typically the dominant power cost in cold climates. The 15 °C crossover was calculated from the efficiency curves of CIGS thin-film panels and selective absorber coatings: below that temperature, thermal collection outperforms electrical generation in terms of useful energy delivered to the system.

### How it connects to PROJECT VOID

The harvester's operational status — current mode, estimated output, and grid-independence flag — is exposed through the `hardware/solar_profile.py` module and displayed on the Sovereign Node dashboard. When the node is in electricity mode and generating enough power for its full-compute workload, it is declared grid-independent. This status feeds into the Sovereign Node's proof-of-infrastructure metadata and is factored into the VTX yield calculations that reward node operators.

---

## 2. ESP32 WiFi CSI Mycelium Monitor

### What it does

WiFi signals carry more information than just data packets. Every transmission also produces Channel State Information (CSI): a detailed measurement of how the radio signal was distorted as it travelled from transmitter to receiver. Most routers discard this information, but an ESP32-S3 microcontroller running modified firmware can capture it in full, producing amplitude and phase measurements across 64 frequency sub-channels dozens of times per second.

When mycelium — the underground network of fungal threads — grows through a wooden substrate, it changes the material's dielectric properties. Water, chitin (the structural material in fungal cell walls), and the physical structure of growing hyphae all interact with radio waves differently from dry, uninhabited wood. These changes are small but consistent, and they produce a measurable signature in the CSI data.

The ESP32 nodes mounted in PROJECT VOID's wooden machine enclosure continuously broadcast WiFi probe packets and capture the resulting CSI. The `void_engine/csi_bio_monitor.py` module receives this data over a local UDP connection, analyses the amplitude variance (which correlates with substrate moisture and mycelium density) and the phase shift magnitude (which correlates with the physical structure of the growing network), and translates these measurements into the same sensor readings the engine has always used: water level, temperature, and biological health scores.

### Why it matters

No existing biological monitoring system for fungal substrates uses radio signals as its primary sensing modality. Conventional approaches rely on resistive moisture sensors, CO₂ probes, or visual inspection — all of which either require physical contact with the substrate, periodic calibration, or human attention. CSI sensing is passive (the WiFi signals are already present), non-invasive (the sensor never touches the mycelium), and continuous (readings arrive many times per second with no moving parts).

For a machine that is designed to run without human intervention, this is significant. The mycelium bed is not a decoration — it is part of the machine's environmental regulation and biological processing layer. Knowing its health in real time, through radio waves, without opening the enclosure, is what makes the "biological transceiver" concept literal rather than metaphorical.

### Fallback and simulation

When no ESP32 hardware is present, the monitor falls back automatically to a simulation mode that generates realistic values with a gentle random walk. This means the rest of the engine — the impedance calculations, governance proposals, and health scoring — continues to function identically whether or not physical hardware is attached. Connecting real hardware is a drop-in replacement: set the `USE_REAL_CSI=1` environment variable and the live UDP stream takes over.

### How it connects to PROJECT VOID

The CSI monitor feeds directly into the `BiologicalTransceiver` class — the same class that has always managed aquaponics sensor state, impedance calculations, and the three-shelf mesh signal multipliers (Whale, Bird, Insect). The biological data from the mycelium is now a first-class input to these calculations, not a simulated stand-in. The CSI source (hardware or simulation) is displayed on the Sovereign Node dashboard so operators always know the provenance of their biological readings.

---

## 3. The Combination: Why It Is Novel

A solar-powered machine that monitors its own biological state through radio waves represents a genuinely new category of autonomous infrastructure. Each technology reinforces the other:

- The solar harvester provides the low-power, grid-independent energy supply that makes long-term autonomous operation possible.
- The CSI monitor provides real-time biological feedback without any human intervention or physical sensor contact.
- Together they close the loop: the machine knows its own energy state and its own biological health, and it can adjust its governance proposals and operational mode accordingly.

For the InteRussia fellowship specifically, this combination demonstrates that advanced computational infrastructure can be built, operated, and maintained entirely within local material and energy constraints — no imported components need replacing, no grid connection needs maintaining, and no biological sensor needs calibrating. The machine tends itself.

---

## Technical Appendix

| Parameter | Value |
|---|---|
| Harvester panel area | 2.4 m² |
| Crossover temperature | 15 °C |
| Electricity mode efficiency | 18% (CIGS thin-film) |
| Electricity mode peak output | ~367 W |
| Heating mode efficiency | 90% (selective absorber) |
| Heating mode peak thermal output | ~1836 W |
| Estimated daily electrical yield (summer) | ~2.0 kWh |
| Node idle power draw | 18 W |
| CSI sub-channels monitored | 64 |
| CSI sensing modality | UDP stream from ESP32-S3 mesh |
| Fallback mode | SimulatedCSIBioMonitor (software) |
| Environment flag for real hardware | `USE_REAL_CSI=1` |
| UDP port | 5286 |
