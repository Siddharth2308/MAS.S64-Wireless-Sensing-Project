"""IWR1443BOOST measurements vs material models (hardware/MEASUREMENT_LOG.md,
sessions 4 and 5): reflectivity relative to aluminium, and two-way
transmission through each sheet.

Models: the simulator's thick-material (half-space) values, and the
thin-sheet model with a small loss tangent. Whiskers on the thin-sheet bars
span plausible permittivities.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from sim import materials as mat, style
from sim.style import plt

DATA = Path(__file__).resolve().parent.parent / "hardware" / "data"
REFLECT_SESSION = "session_20261030_185358"    # session 4, config bo18
TRANSMIT_SESSION = "session_20261030_191359"   # session 5, config bo18
GLASS_GOOD_FRAMES = slice(0, 141)              # glass sheet fell at frame 141

# sheet, model material, thickness (mm), plausible eps range, loss tangent for the nominal thin-sheet bar
SHEETS = [("plastic", "acrylic", 3.0, (2.3, 3.2), 0.02),
          ("glass", "glass", 4.0, (5.5, 6.5), 0.025)]


def _level(session, label, bin_m, frames=slice(None)):
    z = np.load(DATA / session / f"{label}.npz")
    k = int(np.argmin(np.abs(z["range_m"] - bin_m)))
    return float(np.median(z["range_profile_db"][frames, k]))


def measurements():
    """dB relative to metal: reflectivity at 0° and two-way transmission."""
    ref = [_level(REFLECT_SESSION, n, 0.45) for n in ("alu_40", "alu_40_end")]
    plate = [_level(TRANSMIT_SESSION, n, 0.654) for n in ("t_alu_only", "t_alu_only_end")]
    out = {}
    for sheet, *_ in SHEETS:
        frames = GLASS_GOOD_FRAMES if sheet == "glass" else slice(None)
        r = _level(REFLECT_SESSION, f"{sheet}_40", 0.45)
        t = _level(TRANSMIT_SESSION, f"t_{sheet}", 0.654, frames)
        out[sheet] = dict(reflect=float(r - np.mean(ref)), reflect_err=abs(ref[1] - ref[0]) / 2,
                          transmit=float(t - np.mean(plate)), transmit_err=abs(plate[1] - plate[0]) / 2)
    return out


def _thin(material, d_mm, eps, td):
    saved = mat.MATERIALS[material]
    mat.MATERIALS[material] = eps
    try:
        return mat.sheet_prediction(material, d_mm, td)
    finally:
        mat.MATERIALS[material] = saved


def models():
    out = {}
    for sheet, m, d, (lo, hi), td in SHEETS:
        eps0 = mat.MATERIALS[m]
        nominal = _thin(m, d, eps0, td)
        span = [_thin(m, d, e, t) for e in np.linspace(lo, hi, 9) for t in (0.0, td)]
        out[sheet] = dict(
            thick_reflect=float(mat.r0_db(m)),
            thick_transmit=float(2 * mat.transmission_loss_db(m)),   # two faces, no absorption
            thin_reflect=nominal["sheet_R_dB"],
            thin_reflect_range=(min(s["sheet_R_dB"] for s in span), max(s["sheet_R_dB"] for s in span)),
            thin_transmit=nominal["sheet_two_way_transmission_dB"],
            thin_transmit_range=(min(s["sheet_two_way_transmission_dB"] for s in span),
                                 max(s["sheet_two_way_transmission_dB"] for s in span)),
            eps=eps0, tan_delta=td, thickness_mm=d)
    return out


def plot(meas, mod):
    fig, axes = plt.subplots(1, 2, figsize=(style.HALF_WIDTH, 2.3), sharey=False)
    x = np.arange(len(SHEETS))
    w = 0.26
    series = [("measured (IWR1443)", style.INK), ("simulator: thick material", style.ORANGE),
              ("thin-sheet model + loss (line: ε range)", style.BLUE)]
    for ax, kind, title, ymin in [(axes[0], "reflect", "(a) reflectivity vs aluminium", -16),
                                  (axes[1], "transmit", "(b) two-way transmission", -9)]:
        pad = 0.03 * -ymin
        for i, (sheet, *_rest) in enumerate(SHEETS):
            vals = [meas[sheet][kind], mod[sheet][f"thick_{kind}"], mod[sheet][f"thin_{kind}"]]
            err = meas[sheet][f"{kind}_err"]
            for j, (v, (_, c)) in enumerate(zip(vals, series)):
                xp = x[i] + (j - 1) * w
                ax.bar(xp, v, w * 0.9, color=c)
                ax.text(xp, v - (err if j == 0 else 0) - pad, f"{v:.1f}", ha="center", va="top",
                        fontsize=4.5)
            # thin-sheet range over plausible permittivity, drawn beside its bar
            lo, hi = mod[sheet][f"thin_{kind}_range"]
            ax.plot([x[i] + 1.5 * w] * 2, [lo, hi], color=style.BLUE, lw=0.8)
            ax.errorbar(x[i] - w, meas[sheet][kind], yerr=err,
                        fmt="none", ecolor=style.MUTED, lw=0.8, capsize=1.5)
        ax.set_ylim(ymin, 0)
        ax.axhline(0, color=style.MUTED, lw=0.6)
        ax.set_xticks(x, [f"{s} {d:g} mm" for s, _, d, _, _ in SHEETS], fontsize=5.5)
        ax.set_title(title, fontsize=6, loc="left")
        ax.grid(axis="y")
        ax.set_axisbelow(True)
    axes[0].set_ylabel("dB (0 = aluminium plate)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=c) for _, c in series]
    fig.legend(handles, [s for s, _ in series], loc="upper center", ncol=3,
               bbox_to_anchor=(0.5, 1.08), fontsize=5)
    fig.tight_layout()
    return style.save(fig, "iwr_validation.png")


def run():
    if not (DATA / REFLECT_SESSION).exists():
        print("IWR data not found, skipping")
        return {}
    style.setup()
    meas, mod = measurements(), models()
    rows = [dict(sheet=s, **{f"measured_{k}": v for k, v in meas[s].items()},
                 **{k: v for k, v in mod[s].items()}) for s, *_ in SHEETS]
    pd.DataFrame(rows).to_csv(style.RESULTS / "iwr_validation.csv", index=False)
    plot(meas, mod)
    for r in rows:
        print({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    return {"iwr_validation": rows}


if __name__ == "__main__":
    run()
