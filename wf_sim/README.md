# wf_sim: a simplified Wave-Former-style partial-cloud simulator

> **This is a simplified geometric model inspired by the Wave-Former paper's description of its training data.
> It is NOT Wave-Former's simulator and does not reproduce Wave-Former's code or results.** We don't have
> Wave-Former's code (see `pipeline_notes.md`).

**What it does:** takes a 3D mesh, puts a virtual mmWave radar aperture above it, and works out which surface
points the radar would detect. The output is a **partial point cloud**, the kind of input Wave-Former's
shape-completion network receives.

**What it's for:** measuring how that input changes with object **orientation** (Proposal B) and with
**per-part materials** (Proposal A), before any network training.

**What it doesn't do:** no neural network, no shape completion, no SAR imaging. All results are about the
*input* side (coverage and which surface is visible), not reconstruction quality.

See `figs/pipeline_diagram.png` for the big picture and `figs/visibility_schematic.png` for the visibility rule.
`figures_guide.md` explains every figure, and `report_snippets.md` has section-by-section notes for the progress report.

---

## Install and run

```bash
cd Project/wf_sim
source .venv/bin/activate && unset PYTHONPATH     # ROS's PYTHONPATH breaks the venv on this machine
python run_all.py            # regenerates every figure + CSV (~6–7 min, 12 threads)
python run_all.py --quick    # everything except the orientation sweep (~15 s)
python -m pytest -q          # 15 tests: simulator physics + IWR parser
```

Fresh setup (another machine):
```bash
python3 -m venv .venv && .venv/bin/pip install numpy scipy trimesh matplotlib pandas pytest rtree embreex pyserial huggingface_hub
```
`embreex` is optional (about 10× faster ray casting); without it trimesh falls back to `rtree`.

Single experiments: `python -m experiments.fresnel_plot`, `python -m experiments.orientation_sweep`,
`python -m experiments.material_jar`, `python -m experiments.pipeline_diagram`.

YCB meshes: `meshes/*.stl` are loaded automatically as single-part objects. They were downloaded from the MITO
dataset on Hugging Face (`SignalKinetics/MITO_Dataset`, `<object>/uniform_10000.stl`). They are git-ignored (third-party data);
see [../README.md](../README.md#2-ycb-meshes-not-in-the-repo) for the download commands.

---

## Layout

```
sim/
  geometry.py     rotations, pose (tilt then yaw, re-seat), aperture grid
  materials.py    permittivity table, Fresnel, R0, dB-threshold -> cutoff angle, transmission loss,
                  thin-sheet (slab) reflectivity/transmission
  objects.py      procedural objects (bottle, mug, jar_lid, box) with part labels + YCB loader
  partial.py      simulate_partial(): the visibility model -> partial cloud + masks + coverage
  style.py        figure style (half-page width, 300 dpi, colorblind-safe palette)
experiments/
  fresnel_plot.py       Task 6: Fresnel curves + material/cutoff table
  orientation_sweep.py  Task 4: coverage + overlap-with-upright vs yaw/tilt, extended tilt to 90°
  material_jar.py       Task 5: uniform vs per-part vs per-part+transmission on the lidded jar
  pipeline_diagram.py   explanatory diagrams
hardware/
  PROTOCOL.md     IWR1443BOOST ground-truth measurement plan
  iwr_logger.py   configure the radar, live alignment view, record range profiles
  tlv.py          parser for the TI demo's UART packets
tests/            test_partial.py (simulator physics), test_iwr_parser.py
meshes/           YCB .stl files
figs/             PNG, 300 dpi        results/  CSV + summary.json + run_all.log
```

Not done from the handoff: Task 7 (turntable greedy vs random), optional and deferred.

---

## How the simulator works (`sim/partial.py`)

For each of 20,000 area-weighted surface samples `p` with normal `n`:

1. **Pose** the object: `R = Rz(yaw) @ Rx(tilt)` about its centroid, then re-seat it on z = 0, centred at x = y = 0.
2. **Best radar position:** over a 31 × 23 grid (0.60 × 0.45 m, 2 cm spacing) placed 0.40 m above the object's
   top, find the position `a*` that minimises Δ = angle(n, a − p), requiring n·(a − p) > 0.
3. **Detection:** received level `L = R0_dB(material) − 4.34 (Δ / 8°)²` (dB relative to a metal plate at normal
   incidence). The point is detected if `L ≥ −20 dB`. That's equivalent to Δ ≤ Δc(material):
   **metal 17.2°, glass 13.6°, PET 11.2°, PP 9.6°.**
4. **Occlusion:** cast a ray from `p + 0.1 mm·n` to `a*`; any hit means not visible.
   With `transmission=True`, dielectric faces let the ray through at `2·10·log10(1 − R0)` dB each, and metal still blocks.
5. Add 2 mm Gaussian noise to the visible points, giving the partial cloud.
6. **Coverage** = the visible fraction of samples, which equals the visible fraction of surface area. It's reported
   in total and per part.

Samples are fixed in the object frame (same seed), so sample *i* is the same surface point at every pose. This
is what makes the **overlap-with-upright** metric possible: Jaccard of the visible sets at two poses.

---

## Assumptions (all approximate)

**Physics**
1. Pure **specular** (mirror-like) reflection under geometric optics. There's **no edge diffraction**, no
   diffuse scattering and no multipath. MITO's simulator has a separate edge model; ours doesn't.
2. Gaussian specular lobe with **8° width, the same for every material**. Materials differ *only* through R0.
   The detection threshold is **−20 dB** relative to metal at normal incidence. Both are guesses, to be calibrated
   with the IWR (`hardware/PROTOCOL.md`).
3. **R0 = normal-incidence Fresnel reflectivity of a thick (half-space) material**, using real permittivities at
   77–81 GHz: **glass ε = 6, PET ε = 3, acrylic ε = 2.6, PP ε = 2.3; metal = perfect conductor.** Losses are ignored, and so is
   the angle dependence of reflectivity (TE/TM). **Thin walls are ignored by the simulator:** a real 2–4 mm wall can reflect
   up to ±8 dB differently through front/back interference. A thin-sheet (slab) model with optional loss tangent
   exists in `sim/materials.py` (`sheet_prediction`) for comparison with the IWR measurements
   (`results/sheet_predictions.csv`), but is not yet used inside `simulate_partial`.
4. **Transmission (optional):** straight rays (no refraction), no absorption, no internal reflections; loss per
   crossed dielectric surface is 2·10·log10(1 − R0) (glass −1.7 dB, PET −0.6 dB, PP −0.4 dB). This is an upper
   bound on what shows through.

**Geometry**

5. Monostatic radar: each grid position transmits and receives. The aperture is **0.60 × 0.45 m, 0.40 m above
   the object top, 2 cm spacing**, from our handoff notes. MITO's simulator uses a 0.2 m height and ~1 mm spacing
   (`pipeline_notes.md`). A finer grid barely changes the results because the lobe (8°) is much wider than the
   angular step.
6. Only the **best** radar position per point is used for the occlusion test. A point blocked from that position
   but visible from a slightly worse one counts as invisible, which is conservative.
7. Pose: `R = Rz(yaw) Rx(tilt)` about the centroid, re-seated on the table, aperture re-centred over the object.
   **"Upright" means the mesh's own frame.** For YCB meshes we did *not* apply MITO's per-object pose offsets.
8. 20,000 samples, seed 0. Coverage has a sampling error of about ±0.2 percentage points.

**Objects**

9. Procedural objects use the handoff's sizes. **The jar body and mug are hollow (4 mm walls)** so that
   transmission has inner surfaces to reveal. The jar lid is a solid metal disc on top. The mug handle is an open
   torus segment.
10. Orientation sweeps use **uniform metal** for every object. YCB meshes are single-part.

---

## Known limitations

- Coverage numbers depend on the cutoff angles. With MITO's 5° threshold every coverage would be much lower.
  Treat **trends and comparisons** as the result, not absolute percentages.
- No reconstruction metrics: these need Wave-Former's checkpoint or our own PoinTr training.
- The orientation sweep scales poorly across processes (about 6 min instead of the ~1 min expected). Results are
  unaffected.
- Not yet validated against real measurements; that's what the IWR protocol in `hardware/` is for.
