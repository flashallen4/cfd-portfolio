#!/usr/bin/env python3
"""
Parametric Ahmed body geometry generator.

Builds the Ahmed reference body (Ahmed et al., 1984) for a given rear
slant angle and exports it as an STL surface mesh for use in CFD meshing
(snappyHexMesh).

Coordinate system (all units mm):
    x : streamwise, x=0 at front tip, x=L at rear
    y : spanwise (width), y=0 at the vertical symmetry plane
    z : vertical (height), z=0 at the bottom of the body

Note: ground clearance (50 mm) is NOT included in this geometry. The body
occupies z in [0, H] only; positioning the body above a ground-plane
boundary condition is handled in the CFD case setup, not in this file.

Fixed dimensions (Ahmed et al. 1984 / Lienhart & Becker 2003):
    L (length)              = 1044 mm
    W (width)               = 389 mm
    H (height)              = 288 mm
    slant_length            = 222 mm (constant, along the slant surface)
    front nose fillet radius = 100 mm

Front-nose fidelity note:
    The real experimental nose is a measured/digitized surface (see
    validation/reference_data/ahmed-front-geo.dat). This script uses a
    standard tangent-fillet approximation (R = 100 mm on all four front
    edges) instead of reconstructing that point cloud. This is documented
    as a limitation in the project README. R = 100 mm is corroborated by
    two independent literature sources (see project README references).

Slant angle convention:
    Measured from the HORIZONTAL roofline. At 0 deg, the slant panel is a
    flat continuation of the roof (near-squareback). Increasing angle
    rotates the panel downward; at higher angles the rear approaches a
    steep fastback-like slope.
"""

import argparse
import math
from pathlib import Path

import cadquery as cq

# --- Fixed Ahmed body dimensions (mm) ---
LENGTH = 1044.0
WIDTH = 389.0
HEIGHT = 288.0
SLANT_LENGTH = 222.0
NOSE_FILLET_RADIUS = 100.0

# Margin used for boolean-cut robustness (avoids coincident/zero-thickness
# faces during the slant cut). Purely a numerical-robustness value, not a
# geometric feature of the body.
CUT_MARGIN = 50.0


def build_ahmed_body(slant_angle_deg: float) -> cq.Workplane:
    """
    Construct the Ahmed body solid for the given slant angle.

    Parameters
    ----------
    slant_angle_deg : float
        Rear slant angle in degrees, measured from horizontal (0-40 deg
        is the physically meaningful range for this geometry).

    Returns
    -------
    cq.Workplane
        A CadQuery Workplane containing the final solid.
    """
    theta = math.radians(slant_angle_deg)

    # --- Step 1: base rectangular box ---
    # x: 0 -> LENGTH, y: -WIDTH/2 -> +WIDTH/2, z: 0 -> HEIGHT
    body = cq.Workplane("XY").box(
        LENGTH, WIDTH, HEIGHT, centered=(False, True, False)
    )

    # --- Step 2: cut the rear slant ---
    # Slant line runs from (x_slant_start, HEIGHT) on the roofline
    # down to (LENGTH, z_slant_end) at the rear.
    slant_dx = SLANT_LENGTH * math.cos(theta)
    slant_dz = SLANT_LENGTH * math.sin(theta)
    x_slant_start = LENGTH - slant_dx
    z_slant_end = HEIGHT - slant_dz

    if z_slant_end < 0:
        raise ValueError(
            f"Slant angle {slant_angle_deg} deg drives the slant below "
            f"the body base (z_slant_end={z_slant_end:.1f} mm). "
            f"Angle out of physically valid range for this geometry."
        )

    z_top = HEIGHT + CUT_MARGIN

    # 2D cutting profile in the X-Z plane (CadQuery's "XZ" named plane:
    # local x -> global X, local y -> global Z), extruded symmetrically
    # across the full width plus margin.
    wedge_points = [
        (x_slant_start, HEIGHT),
        (LENGTH, z_slant_end),
        (LENGTH + CUT_MARGIN, z_slant_end),
        (LENGTH + CUT_MARGIN, z_top),
        (x_slant_start, z_top),
    ]

    wedge = (
        cq.Workplane("XZ")
        .polyline(wedge_points)
        .close()
        .extrude(WIDTH / 2 + CUT_MARGIN, both=True)
    )

    body = body.cut(wedge)

    # --- Step 3: front nose fillet ---
    # Applied to all four edges of the front face (x=0), giving a
    # rounded/bullet-style nose (standard Ahmed body simplification).
    body = body.faces("<X").edges().fillet(NOSE_FILLET_RADIUS)

    return body


def main():
    parser = argparse.ArgumentParser(
        description="Generate Ahmed body STL geometry for one or more slant angles."
    )
    parser.add_argument(
        "--angles",
        type=float,
        nargs="+",
        default=[0, 10, 20, 25, 30, 35],
        help="Slant angle(s) in degrees to generate (default: project case matrix).",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path(__file__).parent / "stl",
        help="Output directory for STL files.",
    )
    args = parser.parse_args()

    args.outdir.mkdir(parents=True, exist_ok=True)

    for angle in args.angles:
        print(f"--- Building Ahmed body: slant angle = {angle} deg ---")
        solid = build_ahmed_body(angle)

        bb = solid.val().BoundingBox()
        volume = solid.val().Volume()
        print(
            f"  Bounding box: "
            f"x=[{bb.xmin:.1f}, {bb.xmax:.1f}] "
            f"y=[{bb.ymin:.1f}, {bb.ymax:.1f}] "
            f"z=[{bb.zmin:.1f}, {bb.zmax:.1f}] mm"
        )
        print(f"  Volume: {volume / 1e6:.3f} L (liters, from mm^3)")

        # Export in meters: internal geometry is built in mm (matches
        # literature dimension conventions), but OpenFOAM/CFD tooling
        # expects meters. Scale here, at the single point of CFD export,
        # rather than converting per-case downstream.
        solid_m = solid.val().scale(0.001)
        outfile = args.outdir / f"ahmed_body_{int(angle):02d}deg.stl"
        cq.exporters.export(cq.Workplane("XY").add(solid_m), str(outfile))
        print(f"  Exported: {outfile}")


if __name__ == "__main__":
    main()
