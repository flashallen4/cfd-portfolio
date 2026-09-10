#!/usr/bin/env python3
"""
Compute raw std dev of Cd and Cl over the verified stationary window
(t = 0.06-0.20 s) of the transient Ahmed-body run.

Source: postProcessing/forces/<time>/forceCoeffs.dat directories under
the transient case. Two directories (1000/, 50/) are leftover steady-case
output (integer pseudo-time from the copied steady case) and must be
excluded -- confirmed by inspection: their Time column contains integers
1000-2000 with Cd values matching the steady-case plateau (~0.151-0.155),
not physical seconds.

Handles restart-boundary duplication: multiple forceCoeffs.dat files may
contain overlapping time ranges from run resumptions. We concatenate all
genuine transient files, sort by time, then drop duplicate/overlapping
timestamps (keep last write, matching OpenFOAM's own restart behavior of
overwriting from the resume point forward).

Usage:
    python3 compute_stationary_stats.py <case_dir>

Example:
    python3 compute_stationary_stats.py \
        ~/cfd-portfolio/01-ahmed-body/cases/slant25_re4.29M_symtest_transient
"""

import sys
import glob
import os
import numpy as np
import pandas as pd

# Directory names known to be leftover steady-case pseudo-time data,
# NOT physical transient time. Confirmed via manual inspection
# (see project log) before running this script.
EXCLUDED_DIR_NAMES = {"1000", "50"}

STATIONARY_START = 0.06
STATIONARY_END = 0.20


def load_forcecoeffs(case_dir):
    pattern = os.path.join(case_dir, "postProcessing", "forces", "*", "forceCoeffs.dat")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No forceCoeffs.dat files found under {pattern}")

    frames = []
    excluded = []
    for f in files:
        dirname = os.path.basename(os.path.dirname(f))
        if dirname in EXCLUDED_DIR_NAMES:
            excluded.append(f)
            continue

        df = pd.read_csv(
            f,
            comment="#",
            sep=r"\s+",
            header=None,
            names=["Time", "Cm", "Cd", "Cl", "Cl_f", "Cl_r"],
        )
        frames.append(df)

    if excluded:
        print("Excluded (leftover steady-case pseudo-time data):")
        for f in excluded:
            print(f"  {f}")

    if not frames:
        raise RuntimeError("All candidate files were excluded -- nothing to analyze.")

    combined = pd.concat(frames, ignore_index=True)

    # Sanity check: confirm remaining data actually looks like physical
    # seconds (small fractional values), not iteration counts.
    if combined["Time"].max() > 100:
        raise RuntimeError(
            f"Max time value after exclusion is {combined['Time'].max()}, "
            "which looks like iteration-count data, not seconds. "
            "Check EXCLUDED_DIR_NAMES -- something was missed."
        )

    # Restart-boundary handling: sort by time, then drop duplicates
    # keeping the LAST occurrence (later resume run's rewrite of a
    # given timestamp is authoritative).
    combined = combined.sort_values("Time", kind="mergesort")
    combined = combined.drop_duplicates(subset="Time", keep="last")
    combined = combined.reset_index(drop=True)

    return combined


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <case_dir>")
        sys.exit(1)

    case_dir = os.path.expanduser(sys.argv[1])
    df = load_forcecoeffs(case_dir)

    print(f"\nTotal rows after cleanup: {len(df)}")
    print(f"Time range: {df['Time'].min():.6f} -- {df['Time'].max():.6f} s")

    window = df[(df["Time"] >= STATIONARY_START) & (df["Time"] <= STATIONARY_END)]

    if len(window) == 0:
        raise RuntimeError(
            f"No data found in stationary window [{STATIONARY_START}, {STATIONARY_END}] s. "
            "Check that transient run actually reached this range."
        )

    print(f"\nStationary window: t = {STATIONARY_START}-{STATIONARY_END} s")
    print(f"Rows in window: {len(window)}")
    print(f"Actual time range in window: {window['Time'].min():.6f} -- {window['Time'].max():.6f} s")

    for col in ["Cd", "Cl"]:
        vals = window[col].to_numpy()
        print(f"\n{col}:")
        print(f"  mean    = {vals.mean():.6f}")
        print(f"  std     = {vals.std(ddof=1):.6f}")
        print(f"  min/max = {vals.min():.6f} / {vals.max():.6f}")

    # Also report raw sampling regularity, since deltaT is adaptive --
    # relevant context for interpreting the std dev (irregular sampling
    # can bias a naive std toward whichever regime has denser samples).
    dt = np.diff(window["Time"].to_numpy())
    print(f"\nTimestep spacing in window: mean={dt.mean():.6e}, "
          f"min={dt.min():.6e}, max={dt.max():.6e}, std={dt.std():.6e}")


if __name__ == "__main__":
    main()
