# Project 01 — Ahmed Body

## Status
**Active.** Project definition and computational plan finalized. Geometry, meshing, and simulation not yet started.

## Overview
The Ahmed body is a simplified ground-vehicle bluff-body geometry used to study three-dimensional separated flow. Its rear slant angle controls the transition between two distinct wake topologies, producing a well-documented non-monotonic drag-vs-angle curve that makes it a standard benchmark for external-aerodynamics CFD.

## Engineering Problem
Automotive-type bluff bodies generate drag primarily through pressure losses associated with flow separation, not skin friction. The Ahmed body isolates this behavior in a geometry simple enough to mesh and validate confidently, while still exhibiting genuine RANS-modelling difficulty at specific slant angles.

## Research Question
How does rear slant angle affect drag coefficient and wake topology in the Ahmed body, and can RANS turbulence modelling (k-ω SST) capture the critical-angle separation behavior reported in experimental reference data?

## Objective
Quantitatively reproduce reference C_D trends across slant angle using RANS CFD, characterize the associated separation and wake vortex structure, and identify where RANS agrees or disagrees with reference data.

## Hypothesis
C_D will rise with slant angle up to a critical angle near 30°, then drop sharply as the flow transitions from attached trailing vortices to full separation off the slant surface. k-ω SST is expected to reproduce this trend qualitatively but to show the largest quantitative disagreement with reference data at/near the critical angle.

## Relevant Theory
- Bluff-body separated flow and pressure-drag dominance
- 3D trailing vortex formation (C-pillar vortices) vs 2D-type separation
- RANS turbulence closure (k-ω SST) and its known limitations for separated, curvature-driven flow

## Assumptions / Simplifications
- Support struts (used in the physical wind-tunnel model) are omitted. This is a standard simplification in published Ahmed body CFD and introduces a small, known drag discrepancy versus experiment.
- Ground plane modelled as a stationary no-slip wall, matching the actual experimental setups of Ahmed (1984) and Lienhart & Becker (2003), neither of which used a moving belt.
- Steady RANS (not scale-resolving) for the baseline study. A DES comparison on the 25° case is a possible future extension, not part of the baseline.
- Incompressible flow (M < 0.15 at all tested velocities).

## Case Matrix

| Slant angle | Velocity | Reynolds number (length-based) | Validation target |
|---|---|---|---|
| 0°  | 60 m/s | 4.29×10⁶ | Ahmed (1984) C_D |
| 10° | 60 m/s | 4.29×10⁶ | Ahmed (1984) C_D |
| 20° | 60 m/s | 4.29×10⁶ | Ahmed (1984) C_D |
| 25° | 60 m/s | 4.29×10⁶ | Ahmed (1984) C_D |
| 25° | 40 m/s | 2.78×10⁶ | Lienhart & Becker (2003) wake PIV |
| 30° | 60 m/s | 4.29×10⁶ | Ahmed (1984) C_D |
| 35° | 60 m/s | 4.29×10⁶ | Ahmed (1984) C_D |

The 25° case is run at two Reynolds numbers because Ahmed (1984) and Lienhart & Becker (2003) used different tunnel velocities (60 m/s and 40 m/s respectively). Running both avoids conflating turbulence-model disagreement with Reynolds-number mismatch when comparing against the two different reference datasets.

## Computational Approach
- **Solver**: `simpleFoam` (steady-state incompressible RANS)
- **Turbulence model**: k-ω SST
- **Geometry**: parametric generation (slant angle as input parameter), exported to STL
- **Meshing**: `blockMesh` background domain + `snappyHexMesh` for body surface conformance and boundary-layer resolution
- **Boundary conditions**: velocity inlet, pressure outlet, no-slip ground and body, symmetry/slip far-field

## Verification Strategy
Mesh-independence study (minimum 3 densities) on the 25°/60 m/s case before trusting results from the full sweep. C_D convergence with mesh refinement will be documented before any parametric results are treated as final.

## Validation Strategy
- C_D vs slant angle compared against Ahmed et al. (1984) experimental data across all 6 angles.
- Detailed wake velocity/topology at 25° compared against Lienhart & Becker (2003) LDA/PIV data.
- Verification (mesh independence) and validation (comparison to experiment) are treated as distinct and will be documented separately.

## Limitations (to be expanded as work progresses)
- No support struts modelled.
- Steady RANS only; no scale-resolving baseline.
- Single turbulence model in the baseline study.

## Reproducibility
All geometry generation, meshing, case setup, and post-processing are scripted (Python/Bash) under `scripts/` and `geometry/`. No manually-edited case files outside of version-controlled dictionaries.

## References
- Ahmed, S.R., Ramm, G., Faltin, G. (1984). *Some Salient Features of the Time-Averaged Ground Vehicle Wake.* SAE Technical Paper 840300.
- Lienhart, H., Becker, S. (2003). *Flow and Turbulence Structure in the Wake of a Simplified Car Model.* SAE Technical Paper 2003-01-0656.
