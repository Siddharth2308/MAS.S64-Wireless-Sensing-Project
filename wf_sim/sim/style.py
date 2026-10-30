"""Shared figure style: half-page width, 300 dpi, colorblind-safe palette.

Categorical slots are fixed-order (validated for CVD separation); assign by
entity, never cycle. Heatmaps use viridis (single-direction lightness).
"""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
FIGS = ROOT / "figs"
RESULTS = ROOT / "results"

HALF_WIDTH = 3.5  # inches
BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
CATEGORICAL = [BLUE, ORANGE, AQUA, YELLOW]
GRAY = "#b9b8b2"
INK = "#2b2b29"
MUTED = "#6b6a64"

MATERIAL_COLOR = {"metal": INK, "glass": BLUE, "PET": ORANGE, "PP": AQUA, "acrylic": YELLOW}
PART_COLOR = {"body": BLUE, "lid": ORANGE, "cap": ORANGE, "handle": ORANGE}

SIM_NOTE = "Simplified geometric model (not Wave-Former's simulator)"


def setup():
    FIGS.mkdir(exist_ok=True)
    RESULTS.mkdir(exist_ok=True)
    plt.rcParams.update({
        "font.size": 7, "axes.titlesize": 7, "axes.labelsize": 7,
        "xtick.labelsize": 6, "ytick.labelsize": 6, "legend.fontsize": 6,
        "axes.edgecolor": MUTED, "axes.labelcolor": INK, "text.color": INK,
        "xtick.color": MUTED, "ytick.color": MUTED,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": False, "grid.color": "#e4e3de", "grid.linewidth": 0.5,
        "lines.linewidth": 1.5, "savefig.dpi": 300, "savefig.bbox": "tight",
        "legend.frameon": False,
    })


def save(fig, name):
    path = FIGS / name
    fig.savefig(path)
    plt.close(fig)
    return path
