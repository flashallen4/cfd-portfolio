#!/usr/bin/env python3
"""
Extract Cd (and other forceCoeffs) time-history from foamRun log files
by parsing 'Time = Ns' markers and the subsequent 'Cd = X' line from
forceCoeffs console output.
"""

import argparse
import re
import numpy as np


def parse_cd_history(log_paths):
    """
    Parse one or more log files in order, returning a dict of
    {iteration: Cd} merged across files (later files override earlier
    ones for duplicate iterations, e.g. if a resumed run re-prints the
    same starting iteration).
    """
    time_re = re.compile(r"^Time\s*=\s*(\d+)s?")
    cd_re = re.compile(r"^\s*Cd\s*=\s*([-\d.eE+]+)")

    history = {}
    for path in log_paths:
        current_time = None
        with open(path) as f:
            for line in f:
                tmatch = time_re.match(line.strip())
                if tmatch:
                    current_time = int(tmatch.group(1))
                    continue
                cmatch = cd_re.match(line.strip())
                if cmatch and current_time is not None:
                    history[current_time] = float(cmatch.group(1))

    return history


def main():
    parser = argparse.ArgumentParser(description="Extract and quantify Cd history from foamRun logs.")
    parser.add_argument("logs", nargs="+", help="Log file(s) in chronological order")
    parser.add_argument("--start", type=int, default=1000, help="Start iteration for analysis window")
    parser.add_argument("--end", type=int, default=2000, help="End iteration for analysis window")
    args = parser.parse_args()

    history = parse_cd_history(args.logs)
    iterations = sorted(history.keys())
    print(f"Total Cd data points parsed: {len(iterations)}")
    print(f"Iteration range found: {iterations[0]} to {iterations[-1]}")

    window_iters = [i for i in iterations if args.start <= i <= args.end]
    window_cd = np.array([history[i] for i in window_iters])
    print(f"\n--- Full window [{args.start}, {args.end}]: {len(window_cd)} points ---")
    print(f"Mean: {window_cd.mean():.6f}")
    print(f"Min:  {window_cd.min():.6f}")
    print(f"Max:  {window_cd.max():.6f}")
    print(f"Std:  {window_cd.std():.6f}")

    for last_n in [100, 200]:
        cutoff = args.end - last_n
        sub_iters = [i for i in window_iters if i > cutoff]
        sub_cd = np.array([history[i] for i in sub_iters])
        if len(sub_cd) > 0:
            print(f"\n--- Final {last_n} iterations ({cutoff}-{args.end}): {len(sub_cd)} points ---")
            print(f"Mean:  {sub_cd.mean():.6f}")
            print(f"Range: {sub_cd.max() - sub_cd.min():.6f} (min={sub_cd.min():.6f}, max={sub_cd.max():.6f})")

    mean_100 = np.array([history[i] for i in window_iters if i > args.end - 100]).mean()
    mean_200 = np.array([history[i] for i in window_iters if i > args.end - 200]).mean()
    pct_diff = 100 * abs(mean_100 - mean_200) / mean_200
    print(f"\nPercent difference between final-100 and final-200 means: {pct_diff:.3f}%")

    # Sub-window breakdown
    print(f"\n--- Sub-window breakdown ---")
    bounds = list(range(args.start, args.end + 1, 200))
    for i in range(len(bounds) - 1):
        lo, hi = bounds[i], bounds[i+1]
        sub_iters = [it for it in window_iters if lo <= it < hi] if hi < args.end else [it for it in window_iters if lo <= it <= hi]
        if sub_iters:
            sub_cd = np.array([history[it] for it in sub_iters])
            print(f"{lo}-{hi}: mean={sub_cd.mean():.6f}, min={sub_cd.min():.6f}, max={sub_cd.max():.6f}, n={len(sub_cd)}")

    # Save full series for potential plotting/FFT later
    np.savez('cd_history.npz', iterations=np.array(window_iters), cd=window_cd)
    print(f"\nSaved full windowed series to cd_history.npz")


if __name__ == "__main__":
    main()
