"""Explanatory diagrams: simulator pipeline and the visibility rule (schematic)."""
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Polygon, Wedge

from sim import materials as mat, style
from sim.style import plt

BOX_FILL = "#eef4fc"
GREY_FILL = "#f3f3f1"


def _box(ax, x, y, w, h, text, fill=BOX_FILL, edge=style.BLUE, dashed=False, size=6):
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.008",
                                fc=fill, ec=edge, lw=0.9, ls="--" if dashed else "-"))
    ax.text(x, y, text, ha="center", va="center", fontsize=size, color=style.INK,
            linespacing=1.25)


def _arrow(ax, p0, p1, color=style.MUTED, dashed=False):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=7, lw=0.9,
                                 color=color, ls="--" if dashed else "-",
                                 shrinkA=0, shrinkB=0))


def _tag(ax, x, y, letter, color):
    ax.text(x, y, f" {letter} ", ha="center", va="center", fontsize=5.5, color="white",
            fontweight="bold", bbox=dict(boxstyle="round,pad=0.25", fc=color, ec="none"))


def pipeline():
    fig, ax = plt.subplots(figsize=(7.0, 2.9))
    ax.set(xlim=(-0.01, 1.01), ylim=(0, 1))
    ax.axis("off")

    ax.text(0.0, 0.97, "Built: simplified partial-cloud simulator (wf_sim)", fontsize=7,
            fontweight="bold", va="top")
    _tag(ax, 0.62, 0.95, "A", style.ORANGE)
    ax.text(0.635, 0.95, "Proposal A: per-part materials / transmission", fontsize=5.5,
            va="center")
    _tag(ax, 0.62, 0.885, "B", style.AQUA)
    ax.text(0.635, 0.885, "Proposal B: object orientation", fontsize=5.5, va="center")

    w, h, y = 0.14, 0.22, 0.66
    xs = np.linspace(0.075, 0.925, 6)
    steps = ["3D mesh\n+ part labels\n+ material per part",
             "Pose\nRz(yaw) Rx(tilt),\nre-seat on table",
             "Sample 20k\nsurface points\n+ normals",
             "Specular test\n(31×23 radar grid)\nΔ ≤ Δc(material)",
             "Occlusion ray\n(metal blocks;\nglass may pass)",
             "+2 mm noise\n→ partial\npoint cloud"]
    for x, txt in zip(xs, steps):
        _box(ax, x, y, w, h, txt, size=5.5)
    for a, b in zip(xs[:-1], xs[1:]):
        _arrow(ax, (a + w / 2, y), (b - w / 2, y))
    _tag(ax, xs[0] + w / 2 - 0.012, y + h / 2, "A", style.ORANGE)
    _tag(ax, xs[1] + w / 2 - 0.012, y + h / 2, "B", style.AQUA)
    _tag(ax, xs[4] + w / 2 - 0.012, y + h / 2, "A", style.ORANGE)

    # material table feeding the specular test
    cut = ", ".join(f"{m} {mat.cutoff_deg(m):.0f}°" for m in mat.MATERIALS)
    _box(ax, xs[3], 0.36, 0.38, 0.12,
         f"Material table: Fresnel R0 → cutoff Δc\n({cut})", size=5.5)
    _arrow(ax, (xs[3], 0.42), (xs[3], y - h / 2))
    _tag(ax, xs[3] + 0.19 - 0.012, 0.42, "A", style.ORANGE)

    # Wave-Former stage that we did not reproduce
    ax.text(0.0, 0.25, "Not reproduced (Wave-Former, from the paper)", fontsize=7,
            fontweight="bold", va="top", color=style.MUTED)
    yb, hb = 0.08, 0.13
    grey = dict(fill=GREY_FILL, edge=style.MUTED, dashed=True, size=5.5)
    _box(ax, 0.19, yb, 0.30, hb, "real scan (inference): SAR image →\nmmNorm normals → candidate partials", **grey)
    _box(ax, 0.57, yb, 0.20, hb, "PoinTr shape completion\n(trained on ~25K objects)", **grey)
    _box(ax, 0.88, yb, 0.18, hb, "complete 3D shape\n(Chamfer / F-score)", **grey)
    _arrow(ax, (0.19 + 0.15, yb), (0.57 - 0.10, yb), dashed=True)
    _arrow(ax, (0.57 + 0.10, yb), (0.88 - 0.09, yb), dashed=True)
    # training data: down from the partial cloud, left, then into the completion box
    y_route = 0.215
    ax.plot([xs[5], xs[5], 0.62], [y - h / 2, y_route, y_route], color=style.MUTED,
            lw=0.9, ls="--")
    _arrow(ax, (0.62, y_route), (0.62, yb + hb / 2), dashed=True)
    ax.text(xs[5] + 0.008, 0.40, "training\ndata", fontsize=5, color=style.MUTED, va="center")
    return style.save(fig, "pipeline_diagram.png")


def visibility_schematic():
    """Side view (cm) of a bottle under the aperture with three example points."""
    h_ap, half_x = 40.0, 30.0
    top = 23.5
    z_ap = top + h_ap
    dc = mat.cutoff_deg("metal")
    fig, ax = plt.subplots(figsize=(style.HALF_WIDTH, 3.3))

    # aperture
    ax.plot([-half_x, half_x], [z_ap, z_ap], color=style.INK, lw=2.5, solid_capstyle="butt")
    ax.text(0, z_ap + 1.5, "synthetic aperture: radar positions (60 cm wide in x)",
            ha="center", fontsize=5.5)
    # bottle outline (body, shoulder, neck, cap)
    outline = np.array([[-3.5, 0], [3.5, 0], [3.5, 16], [1.2, 19], [1.2, 22], [1.4, 22],
                        [1.4, top], [-1.4, top], [-1.4, 22], [-1.2, 22], [-1.2, 19],
                        [-3.5, 16]])
    ax.add_patch(Polygon(outline, closed=True, fc="#e9e8e3", ec=style.MUTED, lw=0.8))
    ax.axhline(0, color=style.MUTED, lw=0.6)

    def example(p, normal_deg_from_up, ok, label, label_xy, reach):
        p = np.array(p)
        t = np.radians(normal_deg_from_up)
        n = np.array([np.sin(t), np.cos(t)])
        # cutoff cone around the normal (drawn up to the aperture height or 25 cm)
        c = style.AQUA if ok else style.ORANGE
        ax.add_patch(Wedge(p, reach, 90 - normal_deg_from_up - dc,
                           90 - normal_deg_from_up + dc, fc=c, alpha=0.22, ec="none"))
        ax.annotate("", p + 7 * n, p, arrowprops=dict(arrowstyle="-|>", color=c, lw=1.2))
        ax.plot(*p, "o", ms=4, color=c, mec="white", mew=0.6, zorder=5)
        ax.annotate(label, p, label_xy, fontsize=5.5, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=style.MUTED, lw=0.5))

    example((0, top), 0, True, "cap top: normal points at\nthe aperture → seen", (8, 50), 40)
    example((2.35, 17.5), 52.5, True, "shoulder: cone just reaches\nthe aperture edge → partly seen",
            (9, 33), 56)
    example((3.5, 8), 90, False, "side wall: echo goes sideways,\nmisses every radar position\n→ not seen",
            (10, 12), 14)
    ax.text(-29, 4, f"shaded cone = normal ± Δc\n(metal Δc ≈ {dc:.0f}°)", fontsize=5.5,
            color=style.MUTED)
    ax.set(xlim=(-32, 32), ylim=(-2, z_ap + 5), xlabel="x (cm)", ylabel="z (cm)")
    ax.set_aspect("equal")
    ax.set_title("Visibility rule (schematic, not to Wave-Former's spec)", loc="left")
    return style.save(fig, "visibility_schematic.png")


def run():
    style.setup()
    pipeline()
    visibility_schematic()
    return {}


if __name__ == "__main__":
    run()
