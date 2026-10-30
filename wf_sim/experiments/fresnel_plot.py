"""Task 6: Fresnel reflectivity vs incidence angle + material/cutoff table."""
import numpy as np
import pandas as pd

from sim import materials as mat, style
from sim.style import plt

THRESHOLDS_DB = (-15.0, -20.0, -25.0)
# the sheets we measure with the IWR (hardware/PROTOCOL.md): material, thickness (mm)
MEASURED_SHEETS = [("glass", 4.0), ("acrylic", 3.0)]
TAN_DELTAS = (0.0, 0.01)   # lossless, and a plausible loss for glass/plastics


def material_table(lobe_deg=mat.DEFAULT_LOBE_DEG):
    rows = []
    for name, eps in mat.MATERIALS.items():
        row = dict(material=name, eps="PEC" if eps is None else eps,
                   R0_linear=round(mat.r0_linear(name), 4),
                   R0_dB=round(mat.r0_db(name), 2),
                   brewster_deg=None if eps is None else round(mat.brewster_deg(name), 1),
                   one_way_interface_loss_dB=round(mat.transmission_loss_db(name) / 2, 2)
                   if eps is not None else None)
        for t in THRESHOLDS_DB:
            row[f"cutoff_deg_thr{int(t)}dB"] = round(mat.cutoff_deg(name, lobe_deg, t), 1)
        rows.append(row)
    return pd.DataFrame(rows)


def plot_fresnel():
    theta = np.linspace(0, 89, 500)
    fig, ax = plt.subplots(figsize=(style.HALF_WIDTH, 2.4))
    ax.axhline(1.0, color=style.MATERIAL_COLOR["metal"], lw=1.5)
    ax.text(2, 0.96, "metal (PEC), TE = TM", va="top", fontsize=6)
    for name in ("glass", "PET", "acrylic", "PP"):
        eps, c = mat.MATERIALS[name], style.MATERIAL_COLOR[name]
        te, tm = mat.fresnel_power(eps, theta)
        ax.plot(theta, te, color=c, label=f"{name} (ε={eps:g})")
        ax.plot(theta, tm, color=c, ls="--")
        b = mat.brewster_deg(name)
        ax.plot([b], [0], marker="o", ms=4, color=c, clip_on=False, zorder=5)
    ax.plot([], [], color=style.MUTED, label="TE (solid)")
    ax.plot([], [], color=style.MUTED, ls="--", label="TM (dashed)")
    ax.plot([], [], color=style.MUTED, marker="o", ls="", ms=4, label="Brewster angle")
    ax.set(xlim=(0, 90), ylim=(0, 1.05), xlabel="Incidence angle (deg)",
           ylabel="Power reflectivity |Γ|²")
    ax.grid(axis="y")
    ax.legend(loc="center left", bbox_to_anchor=(0.0, 0.62))
    ax.set_title("Fresnel reflectivity at 77–81 GHz (approx. ε)", loc="left")
    return style.save(fig, "fresnel.png")


def run():
    style.setup()
    table = material_table()
    table.to_csv(style.RESULTS / "material_table.csv", index=False)
    sheets = pd.DataFrame([mat.sheet_prediction(m, d, td)
                           for m, d in MEASURED_SHEETS for td in TAN_DELTAS])
    sheets.to_csv(style.RESULTS / "sheet_predictions.csv", index=False)
    plot_fresnel()
    print(table.to_string(index=False))
    print(sheets.to_string(index=False))
    return {"material_table": table.to_dict(orient="records"),
            "sheet_predictions": sheets.to_dict(orient="records")}


if __name__ == "__main__":
    run()
