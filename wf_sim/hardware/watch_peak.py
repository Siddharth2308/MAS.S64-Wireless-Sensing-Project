"""Print the peak level each time mmWave Studio writes a new capture (for aligning a plate or sheet).

  python -m hardware.watch_peak C:\\dca\\E1_align

Watches <dir>\\adc_data.bin (or a .bin path). On every new, complete capture it prints the peak level and
range, the change vs the previous capture, and the best so far. Same processing as `dca_process summary`,
but nothing is written to the logs. Ctrl+C to stop.
"""
import argparse
import time
from pathlib import Path

from hardware import dca_process as d


def _stat(path):
    try:
        s = path.stat()
        return s.st_mtime, s.st_size
    except OSError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("path", type=Path, help="capture folder or .bin file")
    ap.add_argument("--cfg", default=str(d.DEFAULT_CFG))
    ap.add_argument("--rmin", type=float, default=0.25, help="peak search window (m)")
    ap.add_argument("--rmax", type=float, default=1.5)
    args = ap.parse_args()

    path = args.path / "adc_data.bin" if args.path.suffix.lower() != ".bin" else args.path
    cfg = d.parse_cfg(Path(args.cfg).read_text(encoding="utf-8"))
    frame_bytes = cfg["chirps_per_frame"] * cfg["n_samples"] * d.N_RX * 4
    print(f"watching {path}  (window {args.rmin}-{args.rmax} m). ARM -> Trigger in Studio; Ctrl+C to stop.")

    seen, prev, best, n = None, None, None, 0
    while True:
        st = _stat(path)
        if st and st != seen and st[1] >= frame_bytes:
            time.sleep(1.0)                          # let Studio finish writing
            if _stat(path) != st:
                continue                             # still growing: check again next loop
            seen = st
            try:
                res, _, _ = d.analyze(path, cfg, args.rmin, args.rmax)
            except Exception as e:                   # half-written or locked file
                print(f"   could not read capture ({e}); waiting for the next one")
                continue
            n += 1
            p = res["peak_db"]
            delta = f"{p - prev:+.1f} vs previous" if prev is not None else "first"
            best = p if best is None else max(best, p)
            flag = "  <- best" if p == best and n > 1 else ""
            warn = "" if res["complete"] and res["clip_pct"] == 0 else \
                f"  [complete={res['complete']} clip={res['clip_pct']}%]"
            print(f"#{n:<3d} peak {p:5.1f} dB at {res['peak_cm']:5.1f} cm   ({delta}, best {best:.1f})"
                  f"   frames {res['frames']}{flag}{warn}")
            prev = p
        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("stopped")
