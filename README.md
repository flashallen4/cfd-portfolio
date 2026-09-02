# CFD Portfolio

A computational fluid dynamics portfolio built to demonstrate applied aerospace engineering competency — from problem formulation through geometry, meshing, solver configuration, verification, validation, and physical interpretation.

## About

I am an aerospace engineering student building this portfolio to demonstrate practical CFD and computational engineering capability. My primary interests are:

- Computational Fluid Dynamics
- Aerodynamics
- Aerospace propulsion
- High-speed and hypersonic flow
- Fluid–structure interaction
- Aerospace structures and computational mechanics

## Purpose

This portfolio is built to demonstrate CFD *competency*, not visual polish. Every project follows the same discipline:

Physics → Geometry → Mesh → Numerical Model → Solver → Convergence
→ Verification → Validation → Parametric Study → Physical Interpretation
→ Engineering Conclusion

Projects are evaluated on whether they answer a real engineering question with defensible evidence — not on mesh size, solver runtime, or how a contour plot looks.

## Technical Stack

| Category | Tools |
|---|---|
| CFD | OpenFOAM (v11) |
| FEA | CalculiX |
| Geometry / CAD | OpenSCAD, STEP/BREP |
| Meshing | Gmsh |
| Programming | Python, Bash |
| Scientific computing | NumPy, SciPy, Pandas, Matplotlib, PyVista |
| Visualization | PyVista (primary), ParaView (exploratory) |
| Version control | Git, GitHub |
| Environment | WSL2 / Ubuntu (terminal-first workflow) |

## Engineering Philosophy

- Verification and validation are treated as distinct and both are required where credible reference data exists.
- Mesh independence is a prerequisite, not a formality.
- A converged solver run is not automatically a correct one.
- Limitations are documented explicitly rather than hidden.
- Negative or inconclusive results are reported honestly rather than adjusted to match expectations.

## Projects

| # | Project | Status | Description |
|---|---|---|---|
| 01 | [Ahmed Body](01-ahmed-body/) | Active | External aerodynamics, separated flow, turbulence modelling, mesh independence, drag validation |
| 02 | [Circular Cylinder VIV](02-circular-cylinder-viv/) | Planned | Vortex shedding, Strouhal number, unsteady CFD, fluid–structure interaction |
| 03 | [Finite Wing / Wingtip Vortex](03-finite-wing/) | Planned | 3D aerodynamics, induced drag, aspect-ratio effects, wingtip vortex formation |
| 04 | [Supersonic Wedge](04-supersonic-wedge/) | Planned | Compressible CFD, oblique shock formation, analytical validation |
| 05 | [RAE2822 Transonic Airfoil](05-rae2822/) | Planned | Transonic flow, shock–boundary-layer interaction, experimental validation |
| 06 | [F1 Front Wing](06-f1-front-wing/) | Planned | Multi-element aerodynamics, ground effect, downforce/drag trade-offs |
| 07 | [Turbulent Channel Flow](07-turbulent-channel/) | Planned | Wall-bounded turbulence, near-wall treatment, y+, turbulence-model comparison |

Status is updated as work progresses. A project is only marked complete once it has been verified, validated where possible, documented, and published with reproducible results.

## Reproducibility

Each project is self-contained and independently reproducible. Project-level READMEs document geometry, mesh methodology, boundary conditions, solver configuration, and steps to reproduce results from scratch.
