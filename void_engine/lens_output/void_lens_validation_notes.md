# VOID Lens Validation Notes

## Source images reviewed
- `/home/ubuntu/Project-void/void_engine/lens_output/forward_void_carbon_lattice.png`
- `/home/ubuntu/Project-void/void_engine/lens_output/forward_chladni_diamond.png`
- `/home/ubuntu/Project-void/void_engine/lens_output/forward_quantum-cymatics_hybrid.png`
- `/home/ubuntu/Project-void/void_engine/lens_output/reverse_healthy_nail.png`
- `/home/ubuntu/Project-void/void_engine/lens_output/reverse_unhealthy_nail.png`

## Visual findings

### Forward synthesis patterns
- `forward_void_carbon_lattice.png`: circular plate mask with orange/copper glow, 4-fold style nodal symmetry, clear dark nodal cross at center.
- `forward_chladni_diamond.png`: brighter yellow-green pattern with denser nodal geometry than the carbon lattice image, visually consistent with a higher harmonic order.
- `forward_quantum-cymatics_hybrid.png`: green pattern with more distributed lobes and higher apparent symmetry density, consistent with a more complex / higher-order harmonic profile.

### Reverse test inputs
- `reverse_healthy_nail.png`: smooth, uniform pink oval with low texture and high brightness.
- `reverse_unhealthy_nail.png`: yellowed oval with horizontal ridge lines and multiple dark circular spots, deliberately higher texture and lower uniformity.

## Demo output findings
- Healthy synthetic nail classified as `RESONANT` with spectral centroid `9046.4 Hz`, deviation `-25.6 Hz`, dominant harmonic `6×`, complexity `0.808`.
- Unhealthy synthetic nail classified as `DEVIANT` with spectral centroid `9612.9 Hz`, deviation `+108.9 Hz`, dominant harmonic `13×`, complexity `0.861`.
- Forward engine successfully produced multiple saved cymatics-like images for test compounds.
- Roundtrip fidelity is currently weak: 432 Hz compound re-extracted at `13689.0 Hz`, so reverse mapping and/or forward colour mapping still needs calibration before claiming strict inversion.
- Runtime warnings appeared from saturation division in grayscale/low-brightness cases; numerical guarding should be improved.

## Immediate next actions
1. Fix saturation division warnings with safe division masks.
2. Calibrate reverse spectral centroid logic so dominant hue bands influence centroid more strongly and low-harmonic compounds do not collapse toward very high-frequency centroids.
3. Improve roundtrip validation and produce a concise technical report for GitHub and cross-AI sharing.
'}'},
