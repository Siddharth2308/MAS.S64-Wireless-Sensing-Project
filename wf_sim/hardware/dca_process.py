"""Process raw DCA1000 captures (IWR1443BOOST, 4 LVDS lanes, complex, 16 bit).

  python -m hardware.dca_process summary <adc_data.bin> --label E1_plate_40
  python -m hardware.dca_process shift <before.bin> <after.bin> --moved-mm 1
  python -m hardware.dca_process materials <capture_dir>

Chirp settings come from a demo .cfg (default iwr1443_txbo18.cfg) and must match
what was set in mmWave Studio. Each summary appends a row to
hardware/logs/dca_summary.csv and saves hardware/logs/dca_<label>.png.

`materials` reads <capture_dir>/E5_r_<sample>_<n>/adc_data.bin (reflection,
reference sample "alu") and E5_t_<sample>_<n>/adc_data.bin (transmission,
reference sample "none"). Sample names must not contain underscores. It writes
hardware/logs/dca_materials.csv, dca_material_pairs.csv and dca_materials.png.
"""
import argparse
import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

from sim import style
from sim.style import plt

HERE = Path(__file__).resolve().parent
DEFAULT_CFG = HERE / "iwr1443_txbo18.cfg"
SUMMARY_CSV = HERE / "logs" / "dca_summary.csv"
C = 299_792_458.0
N_FFT = 256                 # same bins as the on-chip range profile
N_RX = 4
CLIP_LEVEL = 32000          # |I| or |Q| at or above this counts as clipped


def parse_cfg(text):
    """Chirp parameters from profileCfg, chirpCfg and frameCfg lines."""
    p = dict(n_tx=0)
    for line in text.splitlines():
        tok = line.split()
        if not tok:
            continue
        if tok[0] == "profileCfg":
            start_hz, adc_start_s = float(tok[2]) * 1e9, float(tok[4]) * 1e-6
            slope = float(tok[8]) * 1e12            # Hz/s
            n_samples, fs = int(tok[10]), float(tok[11]) * 1e3
            f0 = start_hz + slope * adc_start_s
            f_center = f0 + slope * (n_samples - 1) / fs / 2
            p.update(n_samples=n_samples, fs=fs, slope=slope, f_center=f_center)
        elif tok[0] == "chirpCfg":
            p["n_tx"] += 1
        elif tok[0] == "frameCfg":
            p["chirps_per_frame"] = (int(tok[2]) - int(tok[1]) + 1) * int(tok[3])
            p["frame_period_s"] = float(tok[5]) * 1e-3
    p["bin_m"] = C * p["fs"] / (2 * p["slope"] * N_FFT)
    p["lambda_m"] = C / p["f_center"]
    return p


def load_bin(path, n_samples):
    """Return (chirps x rx x samples) complex data and leftover int16 count.
    Layout per sample: I1 I2 I3 I4 Q1 Q2 Q3 Q4 (little-endian int16)."""
    raw = np.fromfile(path, dtype="<i2")
    per_chirp = n_samples * N_RX * 2
    n_chirps = raw.size // per_chirp
    leftover = raw.size - n_chirps * per_chirp
    x = raw[:n_chirps * per_chirp].reshape(n_chirps, n_samples, 2 * N_RX).astype(np.float32)
    data = x[:, :, :N_RX] + 1j * x[:, :, N_RX:]
    return data.transpose(0, 2, 1), leftover


def range_fft(data):
    """Windowed range FFT along samples, scaled so a tone of amplitude A peaks at A."""
    w = np.hanning(data.shape[-1])
    return np.fft.fft(data * w, N_FFT, axis=-1) / w.sum()


def db(power):
    return 10 * np.log10(np.maximum(power, 1e-12))


def _peak_bin(profile_db, cfg, rmin, rmax):
    r = np.arange(N_FFT) * cfg["bin_m"]
    sel = np.flatnonzero((r >= rmin) & (r <= rmax))
    return int(sel[np.argmax(profile_db[sel])])


def analyze(path, cfg, rmin=0.25, rmax=1.5):
    data, leftover = load_bin(path, cfg["n_samples"])
    clip = float(np.mean((np.abs(data.real) >= CLIP_LEVEL) | (np.abs(data.imag) >= CLIP_LEVEL)))
    max_adc = int(max(np.abs(data.real).max(), np.abs(data.imag).max()))
    spec = range_fft(data[::cfg["n_tx"]])            # first TX only: (chirps, rx, bins)
    profile = db(np.mean(np.abs(spec) ** 2, axis=(0, 1)))
    k = _peak_bin(profile, cfg, rmin, rmax)
    rx_bins = [_peak_bin(db(np.mean(np.abs(spec[:, i]) ** 2, axis=0)), cfg, rmin, rmax)
               for i in range(N_RX)]

    # one phasor per frame at the peak bin, first RX
    per_frame = cfg["chirps_per_frame"] // cfg["n_tx"]
    n_frames = spec.shape[0] // per_frame
    phasors = spec[:n_frames * per_frame, 0, k].reshape(n_frames, per_frame).mean(axis=1)
    phase = np.degrees(np.unwrap(np.angle(phasors))) if n_frames else np.zeros(0)
    level = db(np.abs(phasors) ** 2) if n_frames else np.zeros(0)
    deg_to_um = cfg["lambda_m"] / 720 * 1e6          # two-way path

    return dict(
        frames=n_frames,
        complete=bool(leftover == 0 and data.shape[0] % cfg["chirps_per_frame"] == 0),
        max_adc=max_adc,
        clip_pct=round(100 * clip, 3),
        peak_db=round(float(profile[k]), 2),
        peak_cm=round(100 * k * cfg["bin_m"], 1),
        peak_bin=k,
        floor_db=round(float(np.median(profile[N_FFT // 2:])), 2),
        rx_peak_bins=" ".join(map(str, rx_bins)),
        level_std_db=round(float(level.std()), 3) if n_frames else None,
        phase_std_deg=round(float(phase.std()), 2) if n_frames else None,
        phase_std_um=round(float(phase.std() * deg_to_um), 1) if n_frames else None,
        phase_range_deg=round(float(np.ptp(phase)), 2) if n_frames else None,
    ), profile, phase


def phase_shift(before, after, cfg, rmin=0.25, rmax=1.5):
    """Phase change at the plate's bin between two recordings, per RX (degrees, wrapped)."""
    a, _ = load_bin(before, cfg["n_samples"])
    b, _ = load_bin(after, cfg["n_samples"])
    sa, sb = range_fft(a[::cfg["n_tx"]]), range_fft(b[::cfg["n_tx"]])
    k = _peak_bin(db(np.mean(np.abs(sa) ** 2, axis=(0, 1))), cfg, rmin, rmax)
    delta = sb[:, :, k].mean(axis=0) * np.conj(sa[:, :, k].mean(axis=0))
    return np.degrees(np.angle(delta)), k


def expected_shift_deg(moved_mm, cfg):
    """Two-way phase change for a target moved by moved_mm (degrees, unwrapped)."""
    return 720 * (moved_mm * 1e-3) / cfg["lambda_m"]


def gated_response(path, cfg, rmin, rmax, k=None, half_width=2):
    """Response of one target across the sweep: (rx, samples) complex.

    Averages the first TX's chirps, keeps the range bins around the target and
    transforms back, so the result is that target's echo versus frequency."""
    data, _ = load_bin(path, cfg["n_samples"])
    w = np.hanning(cfg["n_samples"])
    spec = np.fft.fft(data[::cfg["n_tx"]].mean(axis=0) * w, axis=-1)
    if k is None:
        r = np.arange(cfg["n_samples"]) * cfg["fs"] * C / (2 * cfg["slope"] * cfg["n_samples"])
        sel = np.flatnonzero((r >= rmin) & (r <= rmax))
        k = int(sel[np.argmax(np.sum(np.abs(spec[:, sel]) ** 2, axis=0))])
    gate = np.zeros(cfg["n_samples"])
    gate[k - half_width:k + half_width + 1] = np.hanning(2 * half_width + 3)[1:-1]
    return np.fft.ifft(spec * gate, axis=-1), k


def _band(cfg, trim=0.15):
    """Sample indices to keep (the window weakens the band edges) and their frequencies."""
    n = cfg["n_samples"]
    idx = np.arange(int(trim * n), int((1 - trim) * n))
    f = cfg["f_center"] + cfg["slope"] * (idx - (n - 1) / 2) / cfg["fs"]
    return idx, f


def separation(a, b):
    """Difference between two groups of repeats, in units of their larger spread."""
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    spread = max(np.std(a, ddof=1), np.std(b, ddof=1), 1e-3)
    return float(abs(np.mean(a) - np.mean(b)) / spread)


def curve_separation(a, b):
    """Same for curves versus frequency: RMS difference of the means / larger RMS spread."""
    a, b = np.asarray(a), np.asarray(b)
    if len(a) < 2 or len(b) < 2:
        return float("nan")
    spread = max(np.sqrt(np.mean(np.var(g, axis=0, ddof=1))) for g in (a, b))
    return float(np.sqrt(np.mean((a.mean(axis=0) - b.mean(axis=0)) ** 2)) / max(spread, 1e-3))


def _group_captures(root, mode):
    groups = defaultdict(list)
    for d in sorted(Path(root).glob(f"E5_{mode}_*_*")):
        parts = d.name.split("_")
        if len(parts) == 4 and (d / "adc_data.bin").exists():
            groups[parts[2]].append(d / "adc_data.bin")
    return groups


def analyze_reflection(groups, cfg, rmin=0.25, rmax=0.6, reference="alu"):
    """Level versus frequency relative to the metal reference. Only magnitude is
    used: re-placing a sheet moves it by more than a wavelength's fraction."""
    k = None
    refs = []
    for path in groups[reference]:
        y, k = gated_response(path, cfg, rmin, rmax, k)
        refs.append(np.abs(y) ** 2)
    ref = np.mean(refs, axis=0)
    idx, f = _band(cfg)
    out = {}
    for name, paths in groups.items():
        curves = []
        for path in paths:
            y, _ = gated_response(path, cfg, rmin, rmax, k)
            curves.append(db(np.mean(np.abs(y[:, idx]) ** 2 / ref[:, idx], axis=0)))
        out[name] = dict(curves=np.array(curves),
                         level_db=np.array([db(np.mean(10 ** (c / 10))) for c in curves]),
                         paths=paths)
    return out, f


def analyze_transmission(groups, cfg, rmin=0.55, rmax=0.85, reference="none"):
    """Complex change of the plate's echo caused by each sheet. The plate must
    stay fixed, so phase is usable: its slope gives the extra path (n-1)d."""
    k = None
    refs = []
    for path in groups[reference]:
        y, k = gated_response(path, cfg, rmin, rmax, k)
        refs.append(y)
    ref = np.mean(refs, axis=0)
    idx, f = _band(cfg)
    out = {}
    for name, paths in groups.items():
        curves, paths_mm = [], []
        for path in paths:
            y, _ = gated_response(path, cfg, rmin, rmax, k)
            ratio = (y[:, idx] / ref[:, idx]).mean(axis=0)
            curves.append(db(np.abs(ratio) ** 2))
            slope = np.polyfit(f, np.unwrap(np.angle(ratio)), 1)[0]      # rad per Hz
            paths_mm.append(abs(slope) / (2 * np.pi) * C / 2 * 1e3)      # two-way delay -> (n-1)d
        out[name] = dict(curves=np.array(curves),
                         level_db=np.array([db(np.mean(10 ** (c / 10))) for c in curves]),
                         path_mm=np.array(paths_mm), paths=paths)
    return out, f


def _plot_materials(reflect, transmit, f_r, f_t):
    style.setup()
    fig, axes = plt.subplots(1, 2, figsize=(2 * style.HALF_WIDTH, 2.6))
    for ax, res, f, title in [(axes[0], reflect, f_r, "Reflection vs metal"),
                              (axes[1], transmit, f_t, "Two-way transmission")]:
        for i, (name, g) in enumerate((res or {}).items()):
            c = style.CATEGORICAL[i % len(style.CATEGORICAL)]
            m, s = g["curves"].mean(axis=0), g["curves"].std(axis=0)
            ax.plot(f / 1e9, m, color=c, lw=1.2, label=name)
            ax.fill_between(f / 1e9, m - s, m + s, color=c, alpha=0.2, lw=0)
        ax.set(xlabel="Frequency (GHz)", ylabel="dB", title=title)
        ax.grid(axis="y")
        ax.legend()
    fig.tight_layout()
    out = HERE / "logs" / "dca_materials.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def cmd_materials(args, cfg):
    reflect, transmit, f_r, f_t = {}, {}, None, None
    groups = _group_captures(args.dir, "r")
    if groups:
        reflect, f_r = analyze_reflection(groups, cfg)
    groups = _group_captures(args.dir, "t")
    if groups:
        transmit, f_t = analyze_transmission(groups, cfg)
    if not reflect and not transmit:
        raise SystemExit(f"no E5_r_* or E5_t_* captures found in {args.dir}")

    rows, pairs = [], []
    for mode, res in (("reflection", reflect), ("transmission", transmit)):
        names = list(res)
        for name in names:
            g = res[name]
            print(f"{mode:12s} {name:12s} n={len(g['paths'])}  level {g['level_db'].mean():7.2f} "
                  f"+/- {g['level_db'].std(ddof=1) if len(g['paths']) > 1 else float('nan'):.2f} dB"
                  + (f"  (n-1)d {g['path_mm'].mean():.2f} +/- "
                     f"{g['path_mm'].std(ddof=1) if len(g['paths']) > 1 else float('nan'):.2f} mm"
                     if "path_mm" in g else ""))
            for i, path in enumerate(g["paths"]):
                rows.append(dict(mode=mode, sample=name, file=str(path), level_db=round(float(g["level_db"][i]), 3),
                                 path_mm=round(float(g["path_mm"][i]), 3) if "path_mm" in g else ""))
        for i, a in enumerate(names):
            for b in names[i + 1:]:
                seps = dict(level=separation(res[a]["level_db"], res[b]["level_db"]),
                            curve=curve_separation(res[a]["curves"], res[b]["curves"]))
                if "path_mm" in res[a]:
                    seps["path"] = separation(res[a]["path_mm"], res[b]["path_mm"])
                for metric, s in seps.items():
                    pairs.append(dict(mode=mode, a=a, b=b, metric=metric, separation=round(s, 2),
                                      separable=bool(s >= 3)))

    print("\nseparation = difference / larger repeat spread (3 or more counts as separable)")
    for p in pairs:
        print(f"{p['mode']:12s} {p['a']:>12s} vs {p['b']:<12s} {p['metric']:6s} {p['separation']:8.2f}"
              f"  {'yes' if p['separable'] else 'no'}")
    (HERE / "logs").mkdir(parents=True, exist_ok=True)
    for name, table in (("dca_materials.csv", rows), ("dca_material_pairs.csv", pairs)):
        with open(HERE / "logs" / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(table[0]))
            w.writeheader()
            w.writerows(table)
    print(f"saved {_plot_materials(reflect, transmit, f_r, f_t)}")


def _plot(label, profile, phase, cfg, res):
    style.setup()
    r = 100 * np.arange(N_FFT) * cfg["bin_m"]
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(style.HALF_WIDTH, 3.4))
    a1.plot(r, profile, color=style.BLUE, lw=1)
    a1.set(xlim=(0, 200), xlabel="Range (cm)", ylabel="Level (dB re 1 ADC count)",
           title=f"{label}: peak {res['peak_db']} dB at {res['peak_cm']} cm")
    a2.plot(np.arange(phase.size) * cfg["frame_period_s"], phase - (phase[0] if phase.size else 0),
            color=style.BLUE, lw=1)
    a2.set(xlabel="Time (s)", ylabel="Phase change (deg)",
           title=f"phase std {res['phase_std_deg']} deg ({res['phase_std_um']} um)")
    fig.tight_layout()
    out = HERE / "logs" / f"dca_{label}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    return out


def cmd_summary(args, cfg):
    res, profile, phase = analyze(args.bin, cfg, args.rmin, args.rmax)
    row = dict(time=datetime.now().isoformat(timespec="seconds"), label=args.label,
               file=str(args.bin), **res)
    SUMMARY_CSV.parent.mkdir(parents=True, exist_ok=True)
    new = not SUMMARY_CSV.exists()
    with open(SUMMARY_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
    for k, v in res.items():
        print(f"{k:16s} {v}")
    print(f"saved {_plot(args.label, profile, phase, cfg, res)}")
    if res["clip_pct"] > 0:
        print("WARNING: samples are clipping; reduce RX gain or raise TX back-off")
    if not res["complete"]:
        print("WARNING: incomplete frames; check Studio settings match the cfg, or lost packets")
    if len(set(res["rx_peak_bins"].split())) > 1:
        print("WARNING: RX channels disagree on the peak bin; check the sample settings")


def cmd_shift(args, cfg):
    delta, k = phase_shift(args.before, args.after, cfg, args.rmin, args.rmax)
    exp = expected_shift_deg(args.moved_mm, cfg)
    wrapped = (exp + 180) % 360 - 180
    print(f"peak bin {k} ({100 * k * cfg['bin_m']:.1f} cm), wavelength {1e3 * cfg['lambda_m']:.3f} mm")
    print("measured change per RX (deg):", np.round(delta, 1))
    print(f"expected for {args.moved_mm} mm: {exp:.1f} deg, wraps to +/-{abs(wrapped):.1f} deg "
          "(sign depends on direction)")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cfg", default=str(DEFAULT_CFG))
    ap.add_argument("--rmin", type=float, default=0.25, help="peak search window (m)")
    ap.add_argument("--rmax", type=float, default=1.5)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("summary", help="checks, range profile and phase stability of one capture")
    s.add_argument("bin", type=Path)
    s.add_argument("--label", required=True)
    s.set_defaults(func=cmd_summary)
    d = sub.add_parser("shift", help="phase change between two captures")
    d.add_argument("before", type=Path)
    d.add_argument("after", type=Path)
    d.add_argument("--moved-mm", type=float, required=True)
    d.set_defaults(func=cmd_shift)
    m = sub.add_parser("materials", help="compare repeated captures of each material (E5)")
    m.add_argument("dir", type=Path)
    m.set_defaults(func=cmd_materials)
    args = ap.parse_args()
    args.func(args, parse_cfg(Path(args.cfg).read_text(encoding="utf-8")))


if __name__ == "__main__":
    main()
