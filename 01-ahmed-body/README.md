# Project 01 — Ahmed Body: 25° Slant, External Aerodynamics

## Status
**Case frozen at commit `72af160`.** The 25° slant / 60 m/s condition is
complete: mesh validated, steady and transient CFD results obtained,
wake dynamics cross-validated against an independent probe measurement.
No further changes will be made to this case. Work is proceeding to
additional slant angles in the case matrix.

---

## 1. Engineering Objective

Investigate the aerodynamic behavior of the Ahmed body at a 25° rear
slant angle — the angle most studied in the literature and the one
with the most reliable published reference data (Ahmed et al. 1984;
Lienhart & Becker 2003) — using RANS CFD, with explicit verification
and validation at every stage.

**Reference configuration**
- Geometry: standard Ahmed body, length L = 1.044 m, width W = 0.389 m,
  height H = 0.288 m, 25° rear slant, 50 mm ground clearance, 100 mm
  front-nose fillet radius (approximation of the real, digitized nose
  profile — see Section 8)
- Freestream velocity: U∞ = 60 m/s (Ahmed 1984 convention)
- Reynolds number: Re_L = U∞L/ν = 4.18×10⁶ (ν = 1.5×10⁻⁵ m²/s)
- Turbulence model: k-ω SST (RAS)

**Research question**: can steady and transient RANS reproduce the
known separation and wake-unsteadiness behavior of the Ahmed body at
this slant angle, and what does the resulting drag/wake signal show
about the applicability of a steady-state assumption to this flow?

---

## 2. Geometry and Domain

- Parametric geometry generated in CadQuery (`geometry/generate_ahmed_body.py`),
  matching Ahmed (1984) dimensions exactly, with the front nose modeled
  as a tangent-fillet approximation (R = 100 mm, corroborated by two
  independent literature sources) rather than the raw digitized scan
  data (see Section 8, Limitations).
- Computational domain: half-domain with a symmetry plane at the
  vehicle centerline (y = 0), exploiting the zero-yaw symmetry of the
  mean flow. Domain extent: 2L upstream, 6L downstream, 1L half-width,
  2L height (x ∈ [−2.088, 6.264] m, y ∈ [0, 1.044] m, z ∈ [0, 2.088] m).
- Ground: stationary no-slip wall (matching the actual Ahmed 1984 and
  Lienhart & Becker 2003 wind-tunnel setups — neither used a moving
  belt).
- Top and outer (far-field) boundaries: slip walls.

---

## 3. Mesh Strategy and Validation

### 3.1 Wall treatment decision
The project initially targeted a **wall-resolved** (y+ ≈ 1) near-wall
strategy with an 18-layer boundary-layer stack, the standard choice
for maximizing separation-prediction accuracy in RANS. This was
**abandoned** after extensive investigation (see Section 9) found a
geometric incompatibility between automated boundary-layer extrusion
and the Ahmed body's rear trihedral corners (where the slant edge,
side edge, and rear vertical face converge), independent of layer
count, domain size, or available hardware.

The project pivoted to a **high-Re wall-function** strategy:
`nutkWallFunction` / `kqRWallFunction` / `omegaWallFunction`, targeting
y+ = 30–300 (the documented valid range for these OpenFOAM 11 boundary
condition implementations, verified against the source code and a
matching external-vehicle-aerodynamics tutorial, not assumed). No
boundary-layer/prism cells are used; near-wall resolution is provided
entirely by isotropic surface refinement.

### 3.2 Mesh generation and verification
- Generated with `snappyHexMesh`, surface refinement level (6,7) on
  the body (steady case): **2,725,204 cells**.
- `checkMesh`: **Mesh OK** — max non-orthogonality 32.9°, max skewness
  0.95, max aspect ratio 3.42, zero illegal faces in every category.
- Independent y+ verification (`scripts/compute_yplus_layer.py --wallfunction`):
  the chosen refinement level places wall-adjacent cells at y+ ≈ 97–194
  for this Re/velocity, within the intended 30–300 wall-function range
  — confirmed analytically before the mesh was trusted, not assumed
  from the refinement level alone.

---

## 4. Steady RANS Baseline (SIMPLEC)

Solved with `foamRun -solver incompressibleFluid`, k-ω SST, SIMPLEC
(`consistent yes`), `residualControl` at 1×10⁻⁴ for p, U, k, ω.

**Result**: residuals decreased substantially over the first 1000
iterations, then **plateaued** between iterations 1000–2000 (only ω
ever converged below the 1×10⁻⁴ threshold). Drag coefficient did not
converge to a fixed point — instead:

| Quantity | Value |
|---|---|
| Cd mean (iterations 1000–2000) | 0.152808 |
| Cd standard deviation | 0.001670 |
| Dominant oscillation period (FFT) | 17.26 iterations |
| Peak/background spectral power ratio | 167,354× |

This is an extremely clean, unambiguous **limit cycle** in the
solver's iteration history — residuals and Cd oscillate around a
stable mean rather than converging to a point. Because iteration count
in a steady SIMPLEC solve is a pseudo-time relaxation parameter, not a
physical timestep, this period has **no direct physical-time or
frequency interpretation** on its own — but its existence motivated
the transient investigation below.

![Steady Cd history and FFT](results/slant25_re4.29M/steady_cd_fft.png)

---

## 5. Transition to Transient (PIMPLE)

Converted the case to transient PIMPLE to determine whether the
observed limit cycle reflects genuine flow unsteadiness. Turbulence
model, wall treatment, and boundary conditions were kept unchanged;
only the time-integration approach changed (see Section 9 for the two
non-trivial bugs found and fixed during this conversion).

**Mesh resolution trade-off**: the full 2.7M-cell mesh, even
parallelized across 8 MPI ranks, required an impractical wall-clock
time to reach a statistically useful physical duration given
hardware/thermal constraints on the development machine. The mesh was
coarsened in two documented steps for the transient run only (the
steady-case mesh above is unaffected):

| Stage | Refinement level | Cells | Notes |
|---|---|---|---|
| Steady baseline | (6,7) | 2,725,204 | Fully validated, used for Section 4 |
| Transient, step 1 | (5,6) | 1,264,455 | `Mesh OK`, verified stable |
| **Transient, final** | **(4,5)** | **872,391** | `Mesh OK`, used for all transient results below |

**Final transient configuration**: 872,391 cells, 8 MPI ranks
(hierarchical decomposition, balanced to <0.1% cell-count deviation),
`maxCo = 0.5` (`adjustTimeStep` active), initial `deltaT` computed
from actual mesh/velocity data (not guessed).

Measured performance: **~2.4 s/timestep** (mean), pressure (GAMG) the
dominant per-timestep cost (mean 6.4 iterations, up to 22), consistent
with standard incompressible-PIMPLE cost distribution.

---

## 6. Transient Results

### 6.1 Stationarity
Starting from uniform initial conditions (not the steady-state result
— see Section 9.2), the flow was run to t = 0.20 s. Windowed-mean
analysis (0.02 s windows) showed the initial startup transient
resolving by t ≈ 0.045–0.06 s, after which windowed Cd means agreed
within ~1–2% of each other with no systematic drift. **The flow reaches
statistical stationarity by t ≈ 0.06 s** (≈3.4 body-length
flow-through times).

Selected stationary analysis window: **t = 0.06–0.20 s**.

![Stationarity assessment](results/slant25_re4.29M/stationarity_assessment.png)
![Full transient Cd trajectory](results/slant25_re4.29M/transient_cd_trajectory.png)

### 6.2 Statistics (stationary window, t = 0.06–0.20 s)

Computed directly from the concatenated `forceCoeffs.dat` output
(`scripts/compute_stationary_stats.py`), n = 7281 samples, restricted
to t = 0.06–0.20 s, with leftover steady-case pseudo-time directories
excluded (see script header for details).

| Quantity | Cd | Cl |
|---|---|---|
| Mean | 0.1619 | 0.1204 |
| Std. dev. (raw, stationary window) | 0.0039 | 0.0500 |
| Min / max | 0.1563 / 0.1698 | 0.0492 / 0.1936 |
| Sub-window mean range (4 equal sub-windows) | 0.1606–0.1628 | — |

**Caveat, stated explicitly**: Cl showed measurably more residual
linear drift within the stationary window (~9.7% over the full
window) than Cd (~0.9%) — Cd statistics are more trustworthy than Cl
statistics from this run. The raw Cl std dev above (0.0500) is ~41%
of the Cl mean, a large relative spread that is consistent with —
not a resolution of — this drift concern: it should be read as
further evidence that Cl has not reached a stationary state in this
window, not as a validated fluctuation amplitude. Cd's std dev
(0.0039, ~2.4% of its mean) does not show this problem.

### 6.3 Frequency and Strouhal number

Both Cd and Cl gave **identical** dominant frequency in every window
tested. Time-domain peak-to-peak measurement (more reliable than the
FFT bin estimate, given the limited number of cycles available) across
two independent 0.07 s sub-windows agreed to within ~1%:

| Metric | Value |
|---|---|
| Time-domain period (sub-window 1) | 0.01523 s (CoV 0.81%) |
| Time-domain period (sub-window 2) | 0.01538 s (CoV 0.06%) |
| Corresponding frequency | ≈ 65.4 Hz |

**Independent wake-probe cross-check**: sampled velocity at a fixed
near-wake point (x = 1.15, y = 0.10, z = 0.15 m) using the already-saved
transient field data (no re-solving). All three velocity components
independently gave the same dominant frequency, in close agreement
with the force signal:

| Signal | Frequency |
|---|---|
| Integrated force (Cd/Cl) | 65.36 Hz |
| Near-wake velocity probe | 65.57 Hz |
| **Agreement** | **0.33%** |

**Strouhal number — characteristic length verified against
literature, not assumed**: Ahmed-body wake-shedding studies
(Thacker et al. 2010, on this same 25° geometry; aspect-ratio wake
studies) define St using body **height H**, not length L (L is the
correct convention for Re in this project, but a different quantity):

St = f·H/U∞, H = 0.288 m → **St ≈ 0.31–0.34**

Published values for comparable Ahmed-body slant/wake shedding modes:
Thacker et al. (2010), 0.18–0.21 (slant-surface shedding); aspect-ratio
studies, 0.24 (C-pillar contraction/expansion mode). Our result is the
same order of magnitude but on the higher end of published values —
most plausibly attributable to the coarsened transient mesh (Section 6
mesh table), not re-verified via a transient mesh-independence study.

### 6.4 Wake visualization

Velocity contours on a longitudinal slice through the near wake,
across 7 timesteps spanning ~2 shedding cycles, show a reverse-flow
recirculation bubble immediately behind the slant surface with
**visibly changing size and shape** cycle-to-cycle — elongating and
contracting rather than static. This is consistent with the
**"bubble pumping"** mechanism specifically documented in the
literature for this geometry (cyclic contraction/expansion of the
near-wake recirculation bubble), rather than confirmed classical
alternating vortex shedding, which was not distinguished with
certainty from this evidence alone.

![Wake recirculation sequence](results/slant25_re4.29M/wake_recirculation_sequence.png)

---

## 7. Engineering Conclusions

1. **A genuinely steady RANS solution does not exist for this flow at
   this slant angle** — the persistent, high-quality limit cycle in
   the steady solve, combined with the transient run's sustained
   periodic wake oscillation, is strong, convergent evidence of real
   flow unsteadiness that a steady formulation cannot resolve to a
   fixed point.
2. **The observed ~65 Hz oscillation is a physically real wake
   phenomenon**, not a numerical artifact — supported by three
   independent lines of evidence: (a) internal consistency between Cd
   and Cl (identical frequency, 0% difference), (b) cross-validation
   against an independent wake-velocity probe (0.33% agreement), and
   (c) visual confirmation of an evolving recirculation structure
   consistent with a literature-documented mechanism.
3. The corrected Strouhal number (St ≈ 0.31–0.34, using the
   literature-verified height-based convention) is in the right order
   of magnitude relative to published values, though higher than the
   most directly comparable literature figures — a limitation
   attributed to mesh coarsening, not treated as a validated match.

---

## 8. Limitations — What Should Not Be Concluded

- **The transient mesh (872,391 cells, level 4,5) is coarsened ~3.1×**
  from the mesh validated for the steady case. No mesh-independence
  study was performed at this transient resolution. The frequency and
  Strouhal number above should be read as a genuine, cross-validated
  qualitative finding, not a quantitatively converged result.
- **No mean/RMS Cd or Cl value from this project has been compared to
  Ahmed (1984) or Lienhart & Becker (2003) experimental data.** Doing
  so would require, at minimum, matching the exact experimental
  Reynolds number condition (this project's 40 m/s / Re 2.78×10⁶
  Lienhart & Becker case remains unexecuted) and a mesh-independence
  study — neither of which has been done.
- **The front nose is a tangent-fillet approximation** of the real,
  digitized nose profile (documented and justified in
  `validation/reference_data/README.md`), not the exact experimental
  geometry.
- **Cl statistics carry more uncertainty than Cd** due to observed
  residual drift within the nominally stationary window (Section 6.2).
- **The wake mechanism is identified as consistent with "bubble
  pumping,"** based on visual inspection of 7 timesteps — this is not
  a rigorous mode-decomposition (e.g. POD/DMD) analysis, and classical
  alternating vortex shedding has not been definitively ruled out as a
  contributing or alternative mechanism.
- **All decisions on mesh resolution, run duration, and rank count in
  the transient study were driven partly by hardware/thermal
  constraints** on the development machine, not purely by numerical
  or physical criteria — stated explicitly rather than presented as
  independent scientific choices.

---

## 9. Development & Troubleshooting (summary)

The full, unabridged investigation — every dead end, failed
configuration, and correction — is preserved in
`mesh/mesh_development_log.md`. Summary of the load-bearing findings:

**9.1 — Wall-resolved meshing failure.** Six-plus mesh iterations at
increasing refinement, multiple `resolveFeatureAngle` values, and
layer counts from 18 down to 5 all failed during boundary-layer
extrusion, either crashing the machine or producing zero retained
layers. Root cause, isolated via direct spatial analysis of
`cellLevel` data: severe cell inversion concentrated at the two rear
trihedral corners, independent of mesh size (reproduced on a mesh
6,300× smaller than the full-resolution attempt). A rear-corner fillet
was investigated and rejected on literature grounds (real Ahmed-body
corners are sharp; rounding them measurably changes drag). This
motivated the wall-function pivot (Section 3.1).

**9.2 — Transient conversion bugs.** (a) `ddtSchemes` in `fvSchemes` —
not `controlDict` or `fvSolution` — controls steady vs. transient
solver mode in OpenFOAM 11 (verified directly from source code); a
correctly-configured PIMPLE/timestep setup silently ran in steady mode
until this was found. (b) The steady SIMPLEC solution's `phi` (flux)
field is inconsistent with a PIMPLE/PISO transient restart, producing
Courant numbers wrong by 5 orders of magnitude; resolved by starting
the transient run from uniform initial conditions instead of
attempting flux reconstruction.

**9.3 — Frequency-analysis correction.** An initial FFT on the raw,
non-uniformly-sampled transient Cd(t) signal produced a spurious
"dominant period" equal to the analysis window length — an artifact of
analyzing a still-decaying envelope. Caught by comparing the FFT
result against a direct visual inspection of the signal and a
time-domain peak count, then corrected by resampling to a uniform grid
and restricting to the verified-stationary window (Section 6.1) before
recomputing.

**9.4 — Strouhal characteristic-length error.** An initial calculation
using body length L gave St ≈ 1.14 — implausible for bluff-body wake
shedding. Literature verification found the wake-shedding convention
uses body height H, not L (L remains correct for this project's
Reynolds number definition, a different, unrelated quantity). This is
documented as a genuine error, caught before being reported as final.

---

## 10. Reproducibility

All geometry generation, meshing, case setup, and post-processing
scripts are under `geometry/`, `mesh/`, and `scripts/`. Case
dictionaries for all three case variants (steady wall-resolved
attempts, steady wall-function baseline, transient) are under
`cases/`. Raw solver field/mesh data is excluded from version control
(regenerable from scripts and dictionaries); quantitative results are
preserved as `.npz` arrays and the figures in `results/`.

## 11. References
- Ahmed, S.R., Ramm, G., Faltin, G. (1984). *Some Salient Features of
  the Time-Averaged Ground Vehicle Wake.* SAE Technical Paper 840300.
- Lienhart, H., Becker, S. (2003). *Flow and Turbulence Structure in
  the Wake of a Simplified Car Model.* SAE Technical Paper 2003-01-0656.
- Thacker, A. et al. (2010, as cited in aspect-ratio wake literature).
  Strouhal number for 25° slant Ahmed-body shedding, St = 0.18–0.21.
