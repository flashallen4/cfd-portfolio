#!/usr/bin/env python3
"""
Compute the required first-cell (near-wall) height for a target y+ value,
using a flat-plate turbulent boundary layer estimate. This is a standard
pre-meshing sizing calculation -- actual y+ achieved must be verified
post-solve (via checkMesh / yPlus function object), since this is an
estimate, not an exact result.

Two modes:
  1. Layer sizing (default): computes first-layer height and resulting
     layer-stack thickness for a WALL-RESOLVED (low-Re) near-wall
     treatment, targeting y+ ~ 1 at the first cell, with prism/inflation
     layers extruded from the wall.
  2. Wall-function sizing (--wallfunction): computes the required
     wall-adjacent cell size for a WALL-FUNCTION (high-Re) near-wall
     treatment, targeting y+ in a specified range (default 30-300).
     No prism/layer extrusion is implied -- this is simply the size an
     ordinary bulk/surface-refined cell touching the wall needs to be.

Method (layer sizing):
    Re_L = U * L / nu
    C_f  = 0.058 * Re_L^(-0.2)              (flat-plate turbulent correlation)
    tau_w = 0.5 * rho * U^2 * C_f
    u_tau = sqrt(tau_w / rho)
    y_1   = y_plus_target * nu / u_tau

Method (wall-function sizing): identical u_tau derivation, then solves
the same y+ relation for the cell size range corresponding to
yplus_min and yplus_max.
"""

import argparse
import math


def compute_first_layer_height(
    U: float,
    L: float,
    nu: float = 1.5e-5,
    rho: float = 1.225,
    y_plus_target: float = 1.0,
) -> dict:
    """
    Compute first-cell wall-normal height for a target y+ (wall-resolved,
    low-Re treatment).

    Parameters
    ----------
    U : float
        Free-stream velocity [m/s].
    L : float
        Reference length [m] (body length, used for Re_L and C_f).
    nu : float
        Kinematic viscosity [m^2/s]. Default: air at ~20C, matches
        ERCOFTAC Ahmed body reference data and OpenFOAM tutorials.
    rho : float
        Fluid density [kg/m^3]. Default: air at standard conditions.
    y_plus_target : float
        Desired y+ value at the first cell center.

    Returns
    -------
    dict with Re_L, C_f, tau_w, u_tau, and first_layer_height (all SI units).
    """
    Re_L = U * L / nu
    C_f = 0.058 * Re_L ** (-0.2)
    tau_w = 0.5 * rho * U ** 2 * C_f
    u_tau = math.sqrt(tau_w / rho)
    y_1 = y_plus_target * nu / u_tau

    return {
        "U": U,
        "L": L,
        "nu": nu,
        "rho": rho,
        "Re_L": Re_L,
        "C_f": C_f,
        "tau_w": tau_w,
        "u_tau": u_tau,
        "y_plus_target": y_plus_target,
        "first_layer_height_m": y_1,
        "first_layer_height_mm": y_1 * 1000,
    }


def suggest_layer_stack(
    first_layer_height_m: float,
    expansion_ratio: float = 1.2,
    n_layers: int = 18,
    u_tau: float = None,
    nu: float = 1.5e-5,
) -> dict:
    """
    Given a first-layer height, compute the resulting total boundary-layer
    stack thickness for a given expansion ratio and layer count.

    If u_tau is provided, also computes the y+ value reached at the
    outer edge of the stack -- this is the actual metric that
    determines whether the stack extends into the log-law region
    (y+ > 30, ideally), not just the raw thickness in mm.
    """
    total = 0.0
    h = first_layer_height_m
    for _ in range(n_layers):
        total += h
        h *= expansion_ratio

    result = {
        "n_layers": n_layers,
        "expansion_ratio": expansion_ratio,
        "first_layer_height_m": first_layer_height_m,
        "final_layer_height_m": h / expansion_ratio,
        "total_stack_thickness_m": total,
        "total_stack_thickness_mm": total * 1000,
    }

    if u_tau is not None:
        yplus_at_edge = total * u_tau / nu
        result["yplus_at_stack_edge"] = yplus_at_edge

    return result


def compute_wallfunction_cell_size(
    U: float,
    L: float,
    nu: float = 1.5e-5,
    rho: float = 1.225,
    yplus_min: float = 30.0,
    yplus_max: float = 300.0,
) -> dict:
    """
    Compute the required wall-adjacent cell size for a wall-function
    (high-Re) near-wall treatment, given a target y+ range. Unlike
    compute_first_layer_height, this does NOT imply any prism/layer
    stack -- the returned cell size is simply the size the bulk mesh
    cell touching the wall needs to be, achieved through ordinary
    surface/volume refinement, not layer extrusion.

    Parameters
    ----------
    U, L, nu, rho : see compute_first_layer_height.
    yplus_min, yplus_max : float
        Target y+ range for the wall-function treatment. Default
        30-300, the standard range for nutkWallFunction/kOmegaSST
        high-Re wall treatment in OpenFOAM.

    Returns
    -------
    dict with Re_L, u_tau, and the cell size range (SI units + mm).
    """
    Re_L = U * L / nu
    C_f = 0.058 * Re_L ** (-0.2)
    tau_w = 0.5 * rho * U ** 2 * C_f
    u_tau = math.sqrt(tau_w / rho)

    y_min = yplus_min * nu / u_tau
    y_max = yplus_max * nu / u_tau

    return {
        "U": U,
        "L": L,
        "Re_L": Re_L,
        "C_f": C_f,
        "tau_w": tau_w,
        "u_tau": u_tau,
        "yplus_min": yplus_min,
        "yplus_max": yplus_max,
        "cell_size_min_m": y_min,
        "cell_size_max_m": y_max,
        "cell_size_min_mm": y_min * 1000,
        "cell_size_max_mm": y_max * 1000,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compute near-wall cell sizing for either a wall-resolved "
                    "(layer-based) or wall-function (high-Re) near-wall treatment."
    )
    parser.add_argument("--U", type=float, required=True, help="Free-stream velocity [m/s]")
    parser.add_argument("--L", type=float, default=1.044, help="Reference length [m] (default: Ahmed body length)")
    parser.add_argument("--nu", type=float, default=1.5e-5, help="Kinematic viscosity [m^2/s]")
    parser.add_argument("--rho", type=float, default=1.225, help="Fluid density [kg/m^3]")
    parser.add_argument("--yplus", type=float, default=1.0, help="Target y+ value (layer-sizing mode)")
    parser.add_argument("--expansion-ratio", type=float, default=1.2)
    parser.add_argument("--n-layers", type=int, default=18)
    parser.add_argument("--wallfunction", action="store_true",
                         help="Compute wall-function cell size range (y+ 30-300) "
                              "instead of wall-resolved layer sizing.")
    parser.add_argument("--yplus-min", type=float, default=30.0,
                         help="Lower y+ bound for wall-function mode")
    parser.add_argument("--yplus-max", type=float, default=300.0,
                         help="Upper y+ bound for wall-function mode")
    args = parser.parse_args()

    if args.wallfunction:
        wf = compute_wallfunction_cell_size(
            args.U, args.L, args.nu, args.rho, args.yplus_min, args.yplus_max
        )
        print(f"--- Wall-function cell sizing for U={args.U} m/s, L={args.L} m ---")
        print(f"  Re_L    = {wf['Re_L']:.4e}")
        print(f"  C_f (flat-plate est) = {wf['C_f']:.5f}")
        print(f"  tau_w   = {wf['tau_w']:.4f} Pa")
        print(f"  u_tau   = {wf['u_tau']:.4f} m/s")
        print(f"  Required wall-adjacent cell size for y+={wf['yplus_min']:.0f}  : "
              f"{wf['cell_size_min_mm']:.4f} mm ({wf['cell_size_min_m']:.4e} m)")
        print(f"  Required wall-adjacent cell size for y+={wf['yplus_max']:.0f} : "
              f"{wf['cell_size_max_mm']:.4f} mm ({wf['cell_size_max_m']:.4e} m)")
        return

    result = compute_first_layer_height(args.U, args.L, args.nu, args.rho, args.yplus)

    print(f"--- y+ sizing for U={args.U} m/s, L={args.L} m ---")
    print(f"  Re_L                 = {result['Re_L']:.4e}")
    print(f"  C_f (flat-plate est) = {result['C_f']:.5f}")
    print(f"  tau_w                = {result['tau_w']:.4f} Pa")
    print(f"  u_tau                = {result['u_tau']:.4f} m/s")
    print(f"  First layer height   = {result['first_layer_height_mm']:.6f} mm "
          f"({result['first_layer_height_m']:.4e} m)")

    stack = suggest_layer_stack(
        result["first_layer_height_m"], args.expansion_ratio, args.n_layers,
        u_tau=result["u_tau"], nu=args.nu
    )
    print(f"\n--- Layer stack (n={stack['n_layers']}, ratio={stack['expansion_ratio']}) ---")
    print(f"  Final layer height       = {stack['final_layer_height_m']*1000:.4f} mm")
    print(f"  Total stack thickness    = {stack['total_stack_thickness_mm']:.3f} mm")
    print(f"  y+ at stack edge         = {stack['yplus_at_stack_edge']:.2f}")


if __name__ == "__main__":
    main()
