"""Regenerate every figure and CSV, and write results/summary.json.

    python run_all.py            # full run (~6-7 min on a 12-thread laptop)
    python run_all.py --quick    # skip the orientation sweep (~10 s)
"""
import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

import argparse  # noqa: E402
import json  # noqa: E402
import time  # noqa: E402

from experiments import (fresnel_plot, iwr_validation, material_jar, orientation_sweep,  # noqa: E402
                         pipeline_diagram)
from sim import style  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true", help="skip the orientation sweep")
    args = ap.parse_args()

    summary = {}
    steps = [("pipeline diagram", pipeline_diagram.run),
             ("Fresnel + material table", fresnel_plot.run),
             ("material jar", material_jar.run),
             ("IWR validation", iwr_validation.run)]
    if not args.quick:
        steps.append(("orientation sweep", lambda: orientation_sweep.run()[0]))
    for name, fn in steps:
        t = time.time()
        print(f"\n=== {name} ===")
        summary.update(fn() or {})
        print(f"--- {name}: {time.time() - t:.0f} s")

    style.RESULTS.mkdir(exist_ok=True)
    (style.RESULTS / "summary.json").write_text(json.dumps(summary, indent=1, default=float))
    print("\nwrote results/summary.json")


if __name__ == "__main__":
    main()
