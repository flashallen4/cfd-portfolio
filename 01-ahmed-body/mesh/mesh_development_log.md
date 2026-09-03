# Mesh Development Log — slant25_re4.29M

## Iteration 1 — FAILED (zero boundary layers)
- refinementSurfaces: ahmedBody level (4 6)
- resolveFeatureAngle: 30
- features: ahmedBody.eMesh level 6 (all 142 extracted edges)
- addLayers: 18 layers, firstLayerThickness 6.742e-6 m, expansionRatio 1.2
- Result: snappyHexMesh completed "without errors" per its own quality
  checks, but layer table showed 0 layers added to ahmedBody patch.
  checkMesh showed min cell volume 4.38e-10 m^3 (~0.76mm edge length),
  comparable to total layer-stack thickness (0.864mm) -- background
  cells too coarse near the wall for the layer stack to fit without
  becoming degenerate. 1,981,869 cells reported with determinant < 0.001
  during layer-addition attempt (severe cell inversion).

## Iteration 2 — FAILED (non-converging refinement loop)
- Change from iteration 1: refinementSurfaces level (4 6) -> (6 8)
- All other parameters unchanged from iteration 1
- Result: castellation phase did not converge. By shell refinement
  iteration 58, cell count had exceeded maxGlobalCells (6,000,000),
  reaching 7.1M+ cells and continuing to climb by ~200 cells/iteration
  through iteration 72 (manually terminated -- no sign of convergence).
  Refinement-level breakdown showed level 8 cells specifically climbing
  every iteration (395,638 -> 418,014 over 15 iterations) while all
  other levels remained flat -- isolates the non-convergence to the
  maximum refinement level, likely at a specific tight geometric
  feature (fillet-to-flat tangency or a convex feature point), not a
  global density problem.
- Suspected contributing factors (not yet isolated):
  1. resolveFeatureAngle 30 (tight) -- may be forcing excessive
     max-level refinement at moderately sharp transitions.
  2. Feature-edge level 6 applied uniformly to all 142 extracted edges,
     including edges along the smoothly-curved fillet (not just the
     genuinely sharp slant/roof edge) -- may be requesting refinement
     the geometry doesn't structurally support converging to.

## Iteration 3 — IN PROGRESS
- Change from iteration 2: resolveFeatureAngle 30 -> 60
- All other parameters unchanged from iteration 2 (refinementSurfaces
  still level (6 8), feature-edge level 6 on all edges, same layer
  settings)
- Purpose: isolate whether resolveFeatureAngle alone explains the
  non-convergence, before considering feature-edge scope as a separate
  variable.

## Iteration 3 — FAILED (same non-convergence as iteration 2)
- Change from iteration 2: resolveFeatureAngle 30 -> 60
- All other parameters unchanged from iteration 2
- Result: identical failure signature. Shell refinement selected-cell
  counts: 2019 -> 388 -> 213 -> ~210/iteration, flatlined for 9+
  iterations with total cells climbing past 7,000,000+, no convergence.
  resolveFeatureAngle ruled out as the cause.

## Root cause analysis (geometric investigation, not a mesh run)
Directly inspected ahmedBody.stl facet-adjacency angles (trimesh):
- 142 edges flagged as "features" by surfaceFeatures (includedAngle 150)
- 132 of 142 (93%) have midpoints in the front-fillet region (x<0.15m)
- Only 10 edges represent genuine sharp geometry (slant/roof transition,
  box corners)
- Fillet-region facet angles span 0-89.99 degrees, fully overlapping
  the angle range of genuine sharp edges (also up to 90 degrees) --
  no includedAngle threshold can separate "fillet tessellation noise"
  from "real sharp edges" by angle alone.
- Conclusion: the fillet's discretized curvature is being misclassified
  as sharp-feature geometry. The explicit `features` block was forcing
  level-6 refinement along the entire curved fillet surface as if it
  were a discrete sharp line, which cannot converge since there is no
  true edge there -- only an ever-finer polygonal approximation of a
  smooth curve.

## Iteration 4 — IN PROGRESS
- Change from iteration 3: removed the explicit `features` block
  entirely (no feature-edge refinement via surfaceFeatures/.eMesh)
- refinementSurfaces: ahmedBody level (6 8) -- unchanged
- resolveFeatureAngle: 60 -- unchanged
- Layer settings: unchanged (18 layers, firstLayerThickness 6.742e-6 m,
  expansionRatio 1.2)
- Geometry and background mesh: unchanged
- Purpose: isolate whether the standalone features block (as opposed
  to refinementSurfaces' own curvature-aware refinement) was the cause
  of non-convergence.

## Iteration 4 — FAILED (identical signature, features block ruled out)
- Change from iteration 3: removed explicit features block entirely
- refinementSurfaces: ahmedBody level (6 8) -- unchanged
- resolveFeatureAngle: 60 -- unchanged
- Result: identical non-convergence signature a third time. Selected-
  cell counts: 201765 -> 108031 -> 12288 -> 1969 -> 332 -> flatlined
  at 140-155 cells/iteration for 10+ iterations, total cells past
  6,241,601 and climbing, no sign of convergence. Manually killed.
- CONCLUSION: the explicit features block was NOT the cause. The
  standalone `features` hypothesis is ruled out.
- Remaining hypothesis: refinementSurfaces itself has independent
  curvature-based refinement logic (distinct from the explicit
  features block), which may be responding to the same fillet
  facet-angle noise (0-90 deg, measured directly on the STL, fully
  overlapping genuine sharp-edge angles) that caused the features
  block to fail to converge. If so, level (6 8) on refinementSurfaces
  is attempting to resolve fillet tessellation noise as if it were
  a real sharp feature, independent of any explicit feature file.
- Next diagnostic step (not yet a fix): identify which specific cells
  are being repeatedly selected for refinement each iteration, to
  confirm or rule out the fillet region as the actual spatial source
  of the stuck refinement loop.

## Iteration 5 — IN PROGRESS
- Hypothesis: tangent-line ambiguity at the fillet-to-flat-face
  transition (G1 but not G2 continuous) causes a small, bounded set of
  cells near that boundary to perpetually re-trigger surface-driven
  refinement, which is NOT subject to maxGlobalCells (that cap only
  applies to bulk/internal refinement) -- explaining the persistent
  ~150 cells/iteration regardless of global cell count.
- Change from iteration 4: refinementSurfaces level (6 8) -> (6 7)
  (reducing max level by one, to test whether fewer refinement
  generations at the ambiguous tangent region allows convergence)
- All other settings unchanged: no features block, resolveFeatureAngle
  60, same layer parameters, same geometry/background mesh.
- Purpose: single-variable test of the tangent-line ambiguity
  hypothesis. If this converges, confirms the theory and establishes
  a practical refinement ceiling for this geometry. If it still fails,
  theory is likely wrong; will need to directly inspect spatial
  refinement pattern (e.g., via foamToVTK on a capped/partial mesh)
  rather than continue guessing at levels.

## Rear-corner root cause investigation (spatial analysis, not a mesh run)
Used cellLevel data (parsed directly from constant/polyMesh/cellLevel)
cross-referenced with cell centers (PyVista OpenFOAM reader) to
spatially locate level-7 (max level) cells from the iteration-5
diagnostic capture:
- Level-7 cells NOT confined to front fillet as originally hypothesized
- Length-wise (x) histogram: flat baseline (~7040 cells/bin) across
  mid-body, but spikes at rear (x=0.835-1.044m), peaking at 4.9x
  baseline in the final bin (x=0.992-1.044m)
- Width-wise (y) histogram of rear region: sharp concentration at
  |y|~0.195 (side edges/corners), ~6x baseline; middle of rear face
  flat at baseline
- CONCLUSION: dominant refinement anomaly is at the two rear side
  edges/corners (where slant edge meets side edge meets rear vertical
  face), not the front fillet. Front fillet shows a real but secondary
  elevation.

## Wake refinement box isolation test
Repeated the same castellation-only diagnostic (level (6,7), features
removed, resolveFeatureAngle 60, minRefinementCells 500, snap/layers
off) with wakeRefinementBox entirely removed from geometry and
refinementRegions.
- Result: level-7 cell count identical to the run WITH the wake box
  present (229,604 cells, exact match). Total cell count dropped
  (4,234,692 vs 5,501,797) due to fewer level 3-6 cells elsewhere, but
  level-7 count unchanged.
- CONCLUSION: wake refinement box is NOT a contributing factor. Rear-
  corner refinement anomaly is purely a body-geometry effect.
- Restored to pre-test baseline after this diagnostic.

## Option C investigation (rear corner fillet) -- REJECTED, not attempted
Researched literature on Ahmed body rear-corner geometry before
considering a corner radius as a fix. Findings:
- Standard Ahmed body (Ahmed 1984, and the Lienhart & Becker 2003
  configuration this project validates against) has genuinely sharp
  rear edges/corners; rounded-edge variants exist in the literature
  (e.g. Thacker et al. 2012) but are explicitly a separate flow-control
  research modification, not the baseline geometry.
- Keogh et al. (cited via literature search) found that adding a
  corner radius at the rear (and front) measurably changes drag
  coefficient -- rear corner sharpness is a drag-sensitive parameter,
  not a negligible meshing convenience.
- CONCLUSION: rear corner fillet REJECTED. No literature precedent
  supports this as a legitimate simplification for the baseline
  validation case (unlike the front-nose fillet, which had two
  independent supporting sources for the specific R=100mm value).
  Geometry must remain sharp at the rear corners.

## resolveFeatureAngle sensitivity investigation
Since the rear corners must stay geometrically sharp, investigated
resolveFeatureAngle as a meshing-level (not geometry-level) lever.

Castellation-only diagnostics (level (6,7), minRefinementCells 500,
snap/layers off) at various resolveFeatureAngle values:
- 60 (iteration 3 baseline): plateaus at ~90-220 cells/iteration
  indefinitely (established failure signature)
- 90: converges naturally (no plateau) but with 205,832 level-7 cells
  remaining (down from 229,604 at angle 60, but far from zero)
- 120: converges naturally with ZERO level-7 cells
- 170: converges naturally with ZERO level-7 cells, IDENTICAL final
  mesh to 120 (5,250,171 cells, identical level-by-level breakdown,
  confirmed via diff of full logs -- only timestamps/PIDs/microsecond
  timings differ). Confirms 120 already saturates whatever angle-based
  discrimination is happening; no benefit from being more permissive
  than 120.

Spatial check on rear-corner cells (from iteration-5 level7_centers.npy):
y-distribution of rear (x>0.95) level-7 cells shows sharp concentration
at |y|=0.156-0.195 (~13,506 cells per edge bin) vs flat baseline
(~2,260 cells) across the rest of the width. This coincides with the
side edges, which per literature (Krajnovic 2014, cited via search)
carry REAL physical significance -- streamwise counter-rotating
vortices form here, one of three named physical mechanisms at the
Ahmed body rear. This is NOT a safe-to-ignore point singularity;
capping resolution here risks under-resolving genuine flow physics
central to this project's research question. Local-refinement-cap
approach (Option A) therefore de-prioritized in favor of continuing
to find a global resolveFeatureAngle value that resolves the mesh
issue without sacrificing edge resolution.

## Full candidate test: resolveFeatureAngle 90, full snap+layers
Ran the actual production configuration (snap true, addLayers true,
minRefinementCells 10) at resolveFeatureAngle 90, level (6,7) -- not
just the fast castellation-only diagnostic -- to test whether the
real target mesh (not a proxy metric) succeeds.
- Result: FAILED. Selected-for-refinement count dropped from initial
  153 to a tight oscillation between 30-40 cells/iteration, sustained
  across 19+ consecutive iterations with no downward trend. This is
  the same non-convergence signature as the original failure, just at
  reduced magnitude. Manually terminated.
- CONCLUSION: resolveFeatureAngle 90 is insufficient for the full
  production mesh, despite showing improvement over 60 in the
  castellation-only diagnostic. The castellation-only diagnostic (fast,
  informative) does not necessarily predict success under full
  snap+layers settings -- this is an important methodological finding:
  proxy-metric diagnostics (level-7 cell count from a truncated run)
  are directional but not sufficient evidence of a working mesh on
  their own.

## Iteration 6 (candidate) -- IN PROGRESS
- Configuration: level (6,7), resolveFeatureAngle 120 (the only value
  tested so far achieving TRUE castellation convergence), full
  production settings (snap true, addLayers true, minRefinementCells 10)
- Purpose: test whether 120 -- which converged cleanly in the
  castellation-only diagnostic -- also succeeds under full snap+layers,
  unlike 90 which regressed under the same test.

## Full candidate result: resolveFeatureAngle 120, full production settings
Ran the full candidate configuration (level (6,7), resolveFeatureAngle
120, snap true, addLayers true, minRefinementCells 10, 18 layers,
firstLayerThickness 6.742e-6m) -- the only resolveFeatureAngle value
that achieved TRUE castellation convergence in prior diagnostics.

- Castellation: CONVERGED CLEANLY. Selected-for-refinement count
  dropped 432 -> 109 -> 7 (below minRefinementCells 10), reaching
  ~6.2M cells. This is the first configuration where castellation
  itself converged rather than plateauing.
- Layer addition: reached the layer summary table BEFORE crashing:
      patch     faces    layers avg thickness[m]
      ahmedBody 882518   18     6.74e-06  0.000864
  This shows 18/18 requested layers matched, with near-wall and
  overall thickness exactly matching our y+ calculation. This is
  the most promising result obtained across all iterations.
- CRASH: the WSL2 VM itself crashed (not just the snappyHexMesh
  process) immediately after "Setting up information for layer
  truncation", with no OpenFOAM-level error message. Reproduced
  IDENTICALLY on a second run at the same configuration -- same
  exact point of failure both times, confirmed via explicit "Terminated"
  message from the shell (external signal, not an internal error).
- dmesg showed no explicit OOM-kill message, but WSL2's memory
  ceiling (12GB, confirmed via .wslconfig) against total system RAM
  of only ~15.85GB physical (TotalPhysicalMemory = 17,011,683,328
  bytes) leaves very little headroom -- raising the WSL2 memory
  ceiling further was assessed as unsafe (would leave Windows host
  with ~2GB, risking host-level instability instead of fixing the
  WSL crash).
- CONCLUSION: this configuration is very likely the CORRECT numerical
  configuration (18/18 layers achieved, correct thickness, clean
  castellation convergence) but is NOT currently executable on this
  hardware due to a genuine physical RAM constraint, not a meshing-
  logic error. This result is preserved as evidence that the
  meshing STRATEGY (level (6,7), resolveFeatureAngle 120, full
  domain, 18 layers) is sound; execution is blocked by hardware,
  not by an unresolved technical/numerical problem.

## Decision 9 reconsidered: half-domain symmetry feasibility test
Given the hardware constraint above, investigated whether a symmetry-
plane half-domain (superseding the original full-domain choice) could
reduce memory footprint enough to retain the 18-layer/y+~=1 strategy.

Physical justification: Ahmed body wake bistability is a documented,
real phenomenon (literature: Krajnovic 2014 and others) but is
inherently TIME-DEPENDENT. The project's baseline is STEADY RANS,
which cannot capture time-dependent switching regardless of whether
symmetry is imposed. Imposing symmetry for the steady baseline was
assessed as not discarding capturable physics -- it removes a
spurious degree of freedom a steady solver could not resolve
correctly either way. Explicit caveat: this does NOT extend to any
future DES extension on the 25 deg case, which would need the full
domain restored to capture genuine unsteady asymmetric switching.

Half-domain test (slant25_re4.29M_symtest, y in [0, 1.044], symmetry
plane at y=0, identical (6,7)/resolveFeatureAngle 120/18-layer
settings, background cell size preserved via 13 cells in y instead of
reusing 25):
- blockMesh: verified correct (32,500 cells, exactly half of the
  full-domain's 62,500; bounding box and patches correct; insidePoint
  verified valid via direct coordinate check)
- snappyHexMesh: WSL2 CRASHED AGAIN, at roughly half the pre-layer
  cell count (~3.1M vs ~6.2M).
- CONCLUSION: the crash is NOT simply proportional to total mesh
  size. Halving cell count did not avoid it. This weakens (but does
  not disprove) a pure "insufficient RAM for this many cells"
  explanation and raises the alternative hypothesis that the 18-layer
  displacementMedialAxis calculation itself has a memory-scaling
  problem specific to this geometry's sharp rear-corner features,
  independent of overall mesh size.

## Layer-addition isolation diagnostic (attempt 1) -- INCONCLUSIVE
Attempted to isolate the layer-addition crash from overall mesh size
by drastically coarsening refinementSurfaces level from (6,7) to
(2,3) (with a hard maxGlobalCells safety cap of 300,000), while
explicitly preserving resolveFeatureAngle 120, nSurfaceLayers 18,
firstLayerThickness 6.742e-6m, and all addLayersControls settings
unchanged.
- Result: completed WITHOUT crashing, but with ZERO layers added
  (ahmedBody 2125 0 0 0) -- not 18.
- INTERPRETATION: this does not answer the diagnostic question. At
  level (2,3), background/surface cells are far too large relative
  to the fixed 6.742e-6m firstLayerThickness -- reproducing the
  ORIGINAL iteration-1 failure mode (cell-size/layer-thickness
  mismatch), not testing whether the algorithm crashes independent
  of size. Coarsening refinement level breaks the diagnostic's
  premise, since it simultaneously changes local near-wall cell size,
  which is a second confounding variable.
- CONCLUSION: this diagnostic design is inadequate. A valid isolation
  test requires shrinking total mesh extent (e.g. a tight bounding
  domain around just the body) while preserving LOCAL near-wall
  refinement density equivalent to the working (6,7) configuration,
  rather than globally coarsening refinement level.

## Layer-addition isolation diagnostic (attempt 2) -- PLANNED
Redesigned approach: construct a deliberately small background domain
(tight box around the body only, e.g. ~1.2L x 0.3L x 0.5L instead of
8L x 2L x 2L) while keeping refinementSurfaces level (6,7),
resolveFeatureAngle 120, and all layer settings identical to the
working candidate. This should produce a much smaller total cell
count while preserving near-wall cell size comparable to the
candidate that reached 18/18 layers, properly isolating the layer-
addition mechanism as the single tested variable.
