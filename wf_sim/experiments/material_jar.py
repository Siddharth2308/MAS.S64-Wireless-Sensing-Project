"""Task 5 (Proposal A): uniform vs per-part materials on the lidded jar.

Conditions: uniform glass; per-part (metal lid, glass body); per-part with
transmission through glass (lossless interfaces, as originally modelled); and
per-part with transmission calibrated to the IWR1443 measurement of a 4 mm
glass sheet (hardware/MEASUREMENT_LOG.md, session 5). Poses: upright, tilt 20 deg, and lying on its
side (tilt 90 deg, added because upright the lid hides the body in every
condition).
"""
import numpy as np
import pandas as pd

from sim import materials as mat, objects, style
from sim.partial import simulate_partial
from sim.style import plt

# measured two-way loss through the 4 mm glass sheet (2 faces), session 5
MEASURED_GLASS_TWO_WAY_DB = -5.55
# extra loss per crossed glass face so a 2-face sheet matches the measurement (~1.1 dB)
GLASS_EXTRA_LOSS_DB = -(MEASURED_GLASS_TWO_WAY_DB / 2 - mat.transmission_loss_db("glass"))

PER_PART = {"lid": "metal", "body": "glass"}
# label, materials, transmission on, extra loss per crossed dielectric face (dB)
CONDITIONS = [
    ("Uniform glass", "glass", False, 0.0),
    ("Per-part", PER_PART, False, 0.0),
    ("Per-part + trans.", PER_PART, True, 0.0),
    ("+ trans., measured loss", PER_PART, True, GLASS_EXTRA_LOSS_DB),
]
TILTS = (0, 20, 90)
POSE_LABEL = {0: "upright", 20: "tilt 20°", 90: "on its side"}
N_POINTS = 20000


def simulate_all():
    jar = objects.get_object("jar_lid")
    return {(t, label): simulate_partial(jar, pose=(0, t), materials=m, transmission=tr,
                                         extra_loss_db=xl, n_points=N_POINTS, seed=0)
            for t in TILTS for label, m, tr, xl in CONDITIONS}, jar


def plot_partials(results, jar):
    """Side view (y-z): grey = full surface, color = visible, by part."""
    fig, axes = plt.subplots(len(TILTS), len(CONDITIONS), figsize=(style.HALF_WIDTH + 0.6, 3.6))
    for r, t in enumerate(TILTS):
        for c, (label, *_) in enumerate(CONDITIONS):
            ax, res = axes[r, c], results[(t, label)]
            P = 100 * res["points"]
            ax.scatter(P[::4, 1], P[::4, 2], s=0.2, c=style.GRAY, lw=0, rasterized=True)
            vis_parts = res["part_ids"][res["visible_mask"]]
            V = 100 * res["partial"]
            for i, part in enumerate(jar.part_names):
                sel = vis_parts == i
                ax.scatter(V[sel, 1], V[sel, 2], s=0.6, c=style.PART_COLOR[part], lw=0,
                           rasterized=True)
            ax.set_aspect("equal", adjustable="datalim")
            ax.locator_params(nbins=3)
            ax.tick_params(labelsize=5)
            if r == 0:
                ax.set_title(label, fontsize=6)
            if c == 0:
                ax.set_ylabel(f"{POSE_LABEL[t]}\nz (cm)", fontsize=6)
            if r == len(TILTS) - 1:
                ax.set_xlabel("y (cm)", fontsize=6)
    handles = [plt.Line2D([], [], ls="", marker="o", ms=3, color=style.PART_COLOR[p],
                          label=f"{p} (visible)") for p in jar.part_names]
    handles.append(plt.Line2D([], [], ls="", marker="o", ms=3, color=style.GRAY,
                              label="full surface"))
    fig.legend(handles=handles, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.03))
    fig.tight_layout()
    return style.save(fig, "material_jar_partials.png")


def plot_coverage(df, jar):
    fig, axes = plt.subplots(1, len(TILTS), figsize=(style.HALF_WIDTH + 0.6, 2.0), sharey=True)
    x = np.arange(len(CONDITIONS))
    w = 0.38
    for ax, t in zip(axes, TILTS):
        for k, part in enumerate(jar.part_names):
            vals = [100 * df[(df.tilt_deg == t) & (df.condition == lab) & (df.part == part)]
                    .visible_fraction.item() for lab, *_ in CONDITIONS]
            pos = x + (k - 0.5) * w
            ax.bar(pos, vals, w * 0.92, color=style.PART_COLOR[part], label=part)
            for p, v in zip(pos, vals):
                ax.text(p, v + 0.8, f"{v:.1f}", ha="center", va="bottom", fontsize=4.5)
        ax.set_xticks(x, ["Uni-\nform", "Per-\npart", "+trans.\nideal", "+trans.\nmeas."], fontsize=4.5)
        ax.set_title(POSE_LABEL[t], fontsize=6)
        ax.grid(axis="y")
        ax.set_axisbelow(True)
    axes[0].set_ylabel("Visible area of part (%)")
    fig.legend(*axes[0].get_legend_handles_labels(), loc="upper center", ncol=2,
               bbox_to_anchor=(0.5, 1.06))
    fig.tight_layout()
    return style.save(fig, "material_jar_coverage.png")


def run():
    style.setup()
    results, jar = simulate_all()
    rows = []
    for (t, label), res in results.items():
        vis_parts = res["part_ids"][res["visible_mask"]]
        for i, part in enumerate(jar.part_names):
            rows.append(dict(tilt_deg=t, condition=label, part=part,
                             visible_fraction=res["coverage_by_part"][part],
                             share_of_partial=float((vis_parts == i).mean())
                             if len(vis_parts) else 0.0,
                             total_coverage=res["coverage_total"],
                             n_partial_points=int(res["visible_mask"].sum())))
    df = pd.DataFrame(rows)
    df.to_csv(style.RESULTS / "material_jar.csv", index=False)
    plot_partials(results, jar)
    plot_coverage(df, jar)
    print(df.round(3).to_string(index=False))
    return {"material_jar": rows}


if __name__ == "__main__":
    run()
