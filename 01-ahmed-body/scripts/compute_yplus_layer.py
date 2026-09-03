#!/usr/bin/env python3
"""
Compute the required first-cell (near-wall) height for a target y+ value,
using a flat-plate turbulent boundary layer estimate. This is a standard
pre-meshing sizing calculation -- actual y+ achieved must be verified
post-solve (via checkMesh / yPlus function object), since this is an
estimate, not an exact result.

Method:
    Re_L = U * L / nu
    C_f  = 0.058 * Re_L^(-0.2)              (flat-plate turbulent correlation)
    tau_w = 0.5 * rho * U^2 * C_f
    u_tau = sqrt(tau_w / rho)
    y_1   = y_plus_target * nu / u_tau
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
    Compute first-cell wall-normal height for a target y+.

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
) -> dict:
    """
    Given a first-layer height, compute the resulting total boundary-layer
    stack thickness for a given expansion ratio and layer count.
    """
    total = 0.0
    h = first_layer_height_m
    for _ in range(n_layers):
        total += h
        h *= expansion_ratio

    return {
        "n_layers": n_layers,
        "expansion_ratio": expansion_ratio,
        "first_layer_height_m": first_layer_height_m,
        "final_layer_height_m": h / expansion_ratio,
        "total_stack_thickness_m": total,
        "total_stack_thickness_mm": total * 1000,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Compute near-wall first-layer height for target y+."
    )
    parser.add_argument("--U", type=float, required=True, help="Free-stream velocity [m/s]")
    parser.add_argument("--L", type=float, default=1.044, help="Reference length [m] (default: Ahmed body length)")
    parser.add_argument("--nu", type=float, default=1.5e-5, help="Kinematic viscosity [m^2/s]")
    parser.add_argument("--rho", type=float, default=1.225, help="Fluid density [kg/m^3]")
    parser.add_argument("--yplus", type=float, default=1.0, help="Target y+ value")
    parser.add_argument("--expansion-ratio", type=float, default=1.2)
    parser.add_argument("--n-layers", type=int, default=18)
    args = parser.parse_args()

    result = compute_first_layer_height(args.U, args.L, args.nu, args.rho, args.yplus)

    print(f"--- y+ sizing for U={args.U} m/s, L={args.L} m ---")
    print(f"  Re_L                 = {result['Re_L']:.4e}")
    print(f"  C_f (flat-plate est) = {result['C_f']:.5f}")
    print(f"  tau_w                = {result['tau_w']:.4f} Pa")
    print(f"  u_tau                = {result['u_tau']:.4f} m/s")
    print(f"  First layer height   = {result['first_layer_height_mm']:.6f} mm "
          f"({result['first_layer_height_m']:.4e} m)")

    stack = suggest_layer_stack(
        result["first_layer_height_m"], args.expansion_ratio, args.n_layers
    )
    print(f"\n--- Layer stack (n={stack['n_layers']}, ratio={stack['expansion_ratio']}) ---")
    print(f"  Final layer height       = {stack['final_layer_height_m']*1000:.4f} mm")
    print(f"  Total stack thickness    = {stack['total_stack_thickness_mm']:.3f} mm")


if __name__ == "__main__":
    main()
