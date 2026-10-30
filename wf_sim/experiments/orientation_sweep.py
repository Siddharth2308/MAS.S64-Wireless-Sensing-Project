"""Task 4 (Proposal B): visible-area coverage vs object orientation.

Yaw 0-345 deg (step 15) x tilt -30..+30 deg (step 10), uniform metal.
"""
import os

# one BLAS thread per worker process; parallelism comes from the pool
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache

import numpy as np
import pandas as pd

from sim import objects, style
from sim.partial import simulate_partial
from sim.style import plt

YAWS = np.arange(0, 360, 15)
TILTS = np.arange(-30, 31, 10)
EXT_YAWS = np.arange(0, 180, 45)      # extended sweep: tilt up to lying on the side
EXT_TILTS = np.arange(0, 91, 10)
N_POINTS = 20000
MATERIAL = "metal"


@lru_cache(maxsize=None)
def _object(name):
    return objects.get_object(name)


def _scan(args):
    name, yaw, tilt = args
    res = simulate_partial(_object(name), pose=(yaw, tilt), materials=MATERIAL,
                           n_points=N_POINTS, seed=0)
    return res["visible_mask"]


def sweep_masks(names, yaws=YAWS, tilts=TILTS):
    """Visibility masks {name: bool array (n_tilt, n_yaw, N_POINTS)}.
    Sample i is the same object-frame surface point in every pose."""
    jobs = [(n, float(y), float(t)) for n in names for t in tilts for y in yaws]
    with ProcessPoolExecutor(max_workers=os.cpu_count()) as ex:
        masks = list(ex.map(_scan, jobs, chunksize=4))
    out, k = {}, 0
    for n in names:
        block = masks[k:k + len(tilts) * len(yaws)]
        out[n] = np.array(block).reshape(len(tilts), len(yaws), -1)
        k += len(block)
    return out


def overlap_with_upright(m):
    """Jaccard overlap (object frame) between each pose's visible set and the
    upright pose's visible set. m: (n_tilt, n_yaw, N) bool."""
    ref = m[list(TILTS).index(0), list(YAWS).index(0)]
    inter = (m & ref).sum(axis=2)
    union = (m | ref).sum(axis=2)
    return inter / np.maximum(union, 1)


def _heat(fig, ax, data, label, title, mark_min):
    im = ax.imshow(data, origin="lower", aspect="auto", cmap="viridis",
                   extent=(YAWS[0] - 7.5, YAWS[-1] + 7.5, TILTS[0] - 5, TILTS[-1] + 5))
    if mark_min:
        ti, yi = np.unravel_index(data.argmin(), data.shape)
        ax.plot(YAWS[yi], TILTS[ti], marker="x", color="white", ms=5, mew=1.2)
    ax.set(ylabel="Tilt (deg)", xticks=np.arange(0, 360, 45), yticks=TILTS[::2])
    for sp in ax.spines.values():
        sp.set_visible(False)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label(label)
    cb.outline.set_visible(False)
    ax.set_title(title, loc="left")


def plot_heatmap(name, cov, overlap):
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(style.HALF_WIDTH, 3.0), sharex=True)
    _heat(fig, a1, 100 * cov, "Visible area (%)",
          f"{name}: (a) coverage vs pose, metal (× = worst)", mark_min=True)
    _heat(fig, a2, 100 * overlap, "Overlap (%)",
          "(b) overlap of visible surface with upright pose (Jaccard)", mark_min=False)
    a2.set_xlabel("Yaw (deg)")
    fig.tight_layout()
    return style.save(fig, f"orientation_heatmap_{name}.png")


def plot_examples(name, best, worst):
    """Partial cloud at best and worst pose: top view and side view (cm)."""
    obj = _object(name)
    fig, axes = plt.subplots(2, 2, figsize=(style.HALF_WIDTH, 3.6))
    for row, (label, (yaw, tilt, c)) in enumerate([("Best", best), ("Worst", worst)]):
        res = simulate_partial(obj, pose=(yaw, tilt), materials=MATERIAL,
                               n_points=N_POINTS, seed=0)
        P, V = 100 * res["points"][::4], 100 * res["partial"]
        side = 0 if np.ptp(P[:, 0]) >= np.ptp(P[:, 1]) else 1   # wider horizontal axis
        for col, (i, j, view) in enumerate([(0, 1, "top"), (side, 2, "side")]):
            ax = axes[row, col]
            ax.scatter(P[:, i], P[:, j], s=0.3, c=style.GRAY, lw=0, rasterized=True)
            ax.scatter(V[:, i], V[:, j], s=0.8, c=style.BLUE, lw=0, rasterized=True)
            ax.set_aspect("equal", adjustable="datalim")
            ax.set_xlabel(f"{'xyz'[i]} (cm)")
            ax.set_ylabel(f"{'xyz'[j]} (cm)")
            ax.locator_params(nbins=4)
            ax.set_title(f"{label} {view}: yaw {yaw:g}°, tilt {tilt:g}° ({100 * c:.1f}%)",
                         loc="left", fontsize=5.5)
    axes[0, 0].scatter([], [], c=style.GRAY, s=6, label="full surface")
    axes[0, 0].scatter([], [], c=style.BLUE, s=6, label="simulated partial (visible)")
    fig.legend(*axes[0, 0].get_legend_handles_labels(), loc="upper center",
               ncol=2, bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout()
    return style.save(fig, f"orientation_examples_{name}.png")


def plot_extended(names, ext):
    """Coverage vs tilt 0-90 deg (mean over yaw, band = min-max), small multiples."""
    ncol = 3
    nrow = int(np.ceil(len(names) / ncol))
    fig, axes = plt.subplots(nrow, ncol, figsize=(style.HALF_WIDTH, 1.05 * nrow + 0.5),
                             sharex=True)
    for ax, n in zip(axes.flat, names):
        cov = 100 * ext[n].mean(axis=2)                       # (tilt, yaw)
        ax.axvspan(0, 30, color="#eeede9", lw=0)
        ax.fill_between(EXT_TILTS, cov.min(axis=1), cov.max(axis=1), color=style.BLUE,
                        alpha=0.25, lw=0)
        ax.plot(EXT_TILTS, cov.mean(axis=1), color=style.BLUE, lw=1.2)
        ax.set_title(n, loc="left", fontsize=5.5)
        ax.set_ylim(bottom=0)
        ax.set_xticks([0, 30, 60, 90])
        ax.locator_params(axis="y", nbins=3)
    for ax in axes.flat[len(names):]:
        ax.set_visible(False)
    fig.supxlabel("Tilt (deg)  — shaded: range of main sweep", fontsize=6)
    fig.supylabel("Visible area (%)", fontsize=6)
    fig.tight_layout()
    return style.save(fig, "orientation_extended_tilt.png")


def plot_summary(stats):
    """Min-max range per object, mean dot, canonical-pose marker."""
    stats = sorted(stats, key=lambda s: s["mean"])
    fig, ax = plt.subplots(figsize=(style.HALF_WIDTH, 0.25 * len(stats) + 0.7))
    y = np.arange(len(stats))
    for k, s in enumerate(stats):
        ax.plot([100 * s["min"], 100 * s["max"]], [k, k], color=style.BLUE, lw=2,
                solid_capstyle="round")
    ax.plot([100 * s["mean"] for s in stats], y, "o", ms=4,
            color=style.INK, label="mean over poses")
    ax.plot([100 * s["canonical"] for s in stats], y, "|", color=style.ORANGE, ms=9,
            mew=2, label="upright (yaw 0°, tilt 0°)")
    ax.set_yticks(y, [s["object"] for s in stats])
    ax.set_xlabel("Visible surface area (%) — bar = min to max over 168 poses")
    ax.set_xlim(left=0)
    ax.grid(axis="x")
    ax.legend(loc="lower right")
    return style.save(fig, "orientation_summary.png")


def summarize(name, cov, overlap):
    flat = [(float(YAWS[j]), float(TILTS[i]), float(cov[i, j]))
            for i in range(len(TILTS)) for j in range(len(YAWS))]
    by_cov = sorted(flat, key=lambda r: r[2])
    canonical = cov[list(TILTS).index(0), list(YAWS).index(0)]
    tilt_mean = {int(t): float(cov[i].mean()) for i, t in enumerate(TILTS)}
    ov_tilt = {int(t): float(overlap[i].mean()) for i, t in enumerate(TILTS)}
    return dict(object=name, min=float(cov.min()), mean=float(cov.mean()),
                max=float(cov.max()), canonical=float(canonical),
                worst=by_cov[:3], best=by_cov[-1], tilt_mean=tilt_mean,
                overlap_min=float(overlap.min()), overlap_mean=float(overlap.mean()),
                overlap_by_abs_tilt={t: float(np.mean([ov_tilt[t], ov_tilt[-t]]))
                                     for t in (0, 10, 20, 30)})


def run(names=None, masks=None):
    style.setup()
    names = names or objects.all_object_names()
    masks = masks or sweep_masks(names)
    ext = sweep_masks(names, EXT_YAWS, EXT_TILTS)
    stats, ext_rows = [], []
    for n in names:
        cov = masks[n].mean(axis=2)
        overlap = overlap_with_upright(masks[n])
        pd.DataFrame([dict(yaw_deg=YAWS[j], tilt_deg=TILTS[i], coverage=cov[i, j],
                           overlap_with_upright=overlap[i, j])
                      for i in range(len(TILTS)) for j in range(len(YAWS))]
                     ).to_csv(style.RESULTS / f"orientation_{n}.csv", index=False)
        s = summarize(n, cov, overlap)
        ecov = ext[n].mean(axis=2)
        s["ext_tilt_mean"] = {int(t): float(ecov[i].mean()) for i, t in enumerate(EXT_TILTS)}
        ext_rows += [dict(object=n, yaw_deg=EXT_YAWS[j], tilt_deg=EXT_TILTS[i],
                          coverage=ecov[i, j])
                     for i in range(len(EXT_TILTS)) for j in range(len(EXT_YAWS))]
        stats.append(s)
        plot_heatmap(n, cov, overlap)
        plot_examples(n, s["best"], s["worst"][0])
        print(f"{n:22s} cov min {s['min']:.3f} mean {s['mean']:.3f} max {s['max']:.3f} "
              f"upright {s['canonical']:.3f} | overlap@|tilt| "
              f"{ {t: round(v, 2) for t, v in s['overlap_by_abs_tilt'].items()} } "
              f"| ext {[round(v, 3) for v in s['ext_tilt_mean'].values()]}")
    plot_summary(stats)
    plot_extended(names, ext)
    pd.DataFrame(ext_rows).to_csv(style.RESULTS / "orientation_extended.csv", index=False)
    pd.DataFrame([{k: v for k, v in s.items()
                   if k in ("object", "min", "mean", "max", "canonical",
                            "overlap_min", "overlap_mean")}
                  for s in stats]).to_csv(style.RESULTS / "orientation_summary.csv", index=False)
    return {"orientation": stats}, masks


if __name__ == "__main__":
    run()
