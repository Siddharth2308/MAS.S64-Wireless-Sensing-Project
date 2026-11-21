r"""Copy and resize the figures/photos used by build_deck.js into presentation/assets/.

  wf_sim\.venv-win\Scripts\python.exe presentation\prep_assets.py      (from Project/)

Photos: EXIF-rotated, max 1600 px, JPEG. Figures: copied as PNG. Also makes two slide versions:
  e5_levels.png  : E5 per-capture levels + mean ± sd, re-plotted from dca_materials.csv with larger fonts
  e5_curves.png  : right panel cropped from dca_E5_summary.png
"""
import csv
import shutil
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, ImageOps

P = Path(__file__).resolve().parent.parent           # Project/
A = P / "presentation" / "assets"
A.mkdir(parents=True, exist_ok=True)
FIGS, LOGS, IMG = P / "wf_sim/figs", P / "wf_sim/hardware/logs", P / "Images"
YCB = P / "wf_sim/materials/photos"
SHOT = Path(r"C:\Users\siddh\OneDrive\Pictures\Screenshots\Screenshot 2026-11-20 123107.png")

figures = {
    "pipeline.png": FIGS / "pipeline_diagram.png",
    "visibility.png": FIGS / "visibility_schematic.png",
    "jar_partials.png": FIGS / "material_jar_partials.png",
    "fresnel.png": FIGS / "fresnel.png",
    "iwr_validation.png": FIGS / "iwr_validation.png",
    "e0_plate_vs_empty.png": LOGS / "dca_plate_vs_empty.png",
    "e1_40_vs_60.png": LOGS / "dca_E1_40_vs_60.png",
    "e2_still.png": LOGS / "dca_E2_still.png",
    "e4_backoff.png": LOGS / "dca_E4_backoff.png",
    "studio_postproc.png": LOGS / "studio_postproc_test_plate_40.png",
}
photos = {
    # stage 1 (Oct 30, on-chip)
    "s1_radar.jpg": IMG / "PXL_20261030_194931781.jpg",
    "s1_sheets.jpg": IMG / "PXL_20261030_221645099.jpg",
    "s1_distance.jpg": IMG / "PXL_20261030_224142930.jpg",
    "s1_transmission.jpg": IMG / "PXL_20261030_231934918.jpg",
    # stage 2 (Nov 19, DCA1000)
    "s2_stack.jpg": IMG / "33403.jpg",
    "s2_bench.jpg": IMG / "33400.jpg",
    "s2_layout.jpg": IMG / "35119.jpg",
    "s2_mark60.jpg": IMG / "35120.jpg",
    "s2_alu.jpg": IMG / "35121.jpg",
    "s2_glass.jpg": IMG / "35197.jpg",
    "s2_acrylic.jpg": IMG / "35199.jpg",
    "s2_white.jpg": IMG / "35207.jpg",
    "s2_glass_side.jpg": IMG / "35196.jpg",
}
ycb = {"ycb_fork.jpg": "030_1.jpg", "ycb_skillet.jpg": "027_1.jpg", "ycb_drill.jpg": "035_1.jpg",
       "ycb_mug.jpg": "025_2.jpg", "ycb_clamp.jpg": "052_1.jpg", "ycb_bleach.jpg": "021_1.jpg"}

for out, src in figures.items():
    shutil.copy(src, A / out)
for out, src in photos.items():
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    im.thumbnail((1600, 1600))
    im.save(A / out, quality=85)
for out, src in ycb.items():                          # crop the turntable area (object sits near centre)
    im = Image.open(YCB / src).convert("RGB")
    w, h = im.size
    im.crop((int(w * .22), int(h * .18), int(w * .78), int(h * .82))).save(A / out, quality=88)
if SHOT.exists():                                    # keep the part of the UI with content (photo + rows)
    im = Image.open(SHOT).convert("RGB")
    im.crop((0, 0, im.size[0], int(im.size[1] * 0.66))).save(A / "label_ui.png")
for n in ("s2_alu.jpg", "s2_glass.jpg", "s2_acrylic.jpg", "s2_white.jpg"):   # square crops for the E5 grid
    im = Image.open(A / n)
    w, h = im.size
    s = min(w, h)
    im.crop(((w - s) // 2, (h - s) // 2, (w + s) // 2, (h + s) // 2)).save(A / n.replace(".jpg", "_sq.jpg"), quality=85)

# E5 right panel (curves across the band), cropped from the existing summary figure
im = Image.open(LOGS / "dca_E5_summary.png")
w, h = im.size
im.crop((int(w * .5), 0, w, h)).save(A / "e5_curves.png")

# E5 levels, re-plotted larger for slides (same data as dca_E5_summary.png left panel)
order = [("alu", "Al"), ("alurot", "Al 90°"), ("glass3", "Glass\n3 mm"), ("glass6", "Glass\n6 mm"),
         ("acrylic3", "Acrylic\n3 mm"), ("acrylic6", "Acrylic\n7 mm"), ("epoxy3", "Epoxy\n3 mm")]
lv = defaultdict(list)
with open(LOGS / "dca_materials.csv", newline="") as f:
    for r in csv.DictReader(f):
        if r["mode"] == "reflection":
            lv[r["sample"]].append(float(r["level_db"]))
plt.rcParams.update({"font.family": "Arial", "font.size": 15})
fig, ax = plt.subplots(figsize=(8, 5), dpi=200)
rng = np.random.default_rng(0)
for k, (s, lab) in enumerate(order):
    v = np.array(lv[s])
    col = "#55636c" if s.startswith("alu") else "#c2410c"
    ax.scatter(k + rng.uniform(-.12, .12, len(v)), v, s=30, color=col, alpha=.55, zorder=2)
    ax.errorbar(k + .28, v.mean(), yerr=v.std(ddof=1), fmt="o", color="#1f2a33", capsize=5, ms=7, zorder=3)
    m = 0.0 if abs(v.mean()) < 0.05 else v.mean()
    ax.annotate(f"{m:.1f}", (k + .36, v.mean()), va="center", fontsize=12, color="#1f2a33")
    print(f"{s}: {v.mean():.2f} ± {v.std(ddof=1):.2f} (n={len(v)})")
ax.set_xticks(range(len(order)), [l for _, l in order])
ax.set_ylabel("Reflection vs aluminium (dB)")
ax.axhline(0, color="#999", lw=.8, zorder=1)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
ax.grid(axis="y", color="#e5e5e5", lw=.8)
ax.set_xlim(-.5, len(order) - .2)
fig.tight_layout()
fig.savefig(A / "e5_levels.png")
import json                                           # pixel sizes, for aspect-correct placement in build_deck.js
sizes = {p.name: Image.open(p).size for p in A.iterdir() if p.suffix in (".png", ".jpg")}
(A / "sizes.json").write_text(json.dumps(sizes, indent=1))
print("assets:", len(sizes))
