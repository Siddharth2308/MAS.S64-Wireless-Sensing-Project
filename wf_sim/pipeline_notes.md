# Pipeline notes (Task 1)

**Status: Wave-Former code — pending access.** We do not have the Wave-Former
repository or checkpoint. Nothing below is a claim about Wave-Former's code.

Section 1 lists the open questions. Section 2 records what we *did* verify in the
code of the same lab's earlier systems (MITO, mmNorm), clearly labelled as such.
Wave-Former may or may not reuse any of it.

---

## 1. Open questions for Wave-Former (pending access)

| # | Question | Why it matters | Answer |
|---|---|---|---|
| Q1 | How are training object orientations set: fixed, a predefined set, or randomized? Over what ranges (yaw, tilt)? | Decides whether Proposal B's gap is real. Our sim shows the visible surface changes a lot with tilt (overlap with upright ≈ 40% at ±30° for bottles). | pending access |
| Q2 | Where do specularity, angle cutoffs and material effects enter partial generation, and what parameter ranges are used (the paper says horizontal/vertical cutoffs are randomized)? Is occlusion modelled? | Decides how hard Proposal A's per-part extension is, and how to set our sim's cutoffs to match. | pending access |
| Q3 | How does evaluation align reconstructions to ground truth: translation only, or is rotation fitted? | If rotation is fitted, orientation errors may be partly hidden in the metric, which matters for Proposal B. | pending access |
| Q4 | Is a pretrained checkpoint available, and what command runs inference on one object? | Needed to measure reconstruction quality (Chamfer, F-score), not just input coverage. | pending access |
| Q5 | Aperture geometry used to generate training partials (height above object, size, spacing)? | Our sim uses 0.60 × 0.45 m at 0.40 m (from our handoff); MITO's simulator uses a 0.2 m radar height (see 2.1). | pending access |

Who to ask: course staff (Fadel Adib's group wrote MITO, mmNorm and Wave-Former).

---

## 2. Verified in related code (MITO / mmNorm, *not* Wave-Former)

Paths are relative to `Project/`.

### 2.1 MITO simulator (`MITO_Codebase/src/simulation/`)

| Fact | Where |
|---|---|
| Three separate simulations per object: **specular**, **edges**, **diffuse** | `run_simulation.py:99`, `:105`, `:111` |
| Specular threshold used for the released runs: **5°** (class default 3°) | `run_simulation.py:99`; default in `simulator.py:23` |
| Edge model: vertices on faces whose adjacency angle exceeds a threshold (**20°** in the runs) | `simulator.py:46–55`, `run_simulation.py:105` |
| Specular rule, per radar position: angle between vertex normal and radar→vertex vector < threshold, **or within threshold of 180°** (accepts flipped normals) | `simulator.py:119–130` |
| Occlusion: per radar position with `psbody.mesh.visibility_compute` | `simulator.py:112` |
| Visible vertices then feed an RF channel simulation and the same SAR imaging used for real data (so MITO outputs SAR images, not point clouds) | `simulator.py:134–157` |
| Radar height **0.2 m** ("Same as real-world experiments") | `simulator.py:66` |
| Aperture: `[230 (270 for large objects), floor(0.55 / step)]` positions, `step = c / f_min / 4` | `simulator.py:67–68` |
| Pose: per-object offset + requested angles, applied as x/y/z rotations | `run_simulation.py:77`, `:90` |
| Simulation noise set to 0.0 in the released script | `run_simulation.py:73` |
| No material parameter anywhere in the specular rule (one threshold for all objects) | `simulator.py:119–130` |

**Comparison with our simulator:**
- Same idea: a point counts if its normal points close enough to some radar position, and it isn't occluded.
- MITO uses one fixed threshold (5°). Ours derives it from the material: 10–17°, so our coverage numbers are higher.
  A 5° threshold would shrink every visible region. Our trends (pose sensitivity, transmission) should survive, but
  the absolute percentages would not.
- MITO also has an **edge** model (diffraction from sharp edges), which we don't. It would add visible points at
  rims and corners, for example the jar lid edge or the box corners.
- We don't simulate the RF channel or form images. We go straight to a point cloud, as the Wave-Former paper
  describes for its training data.

### 2.2 MITO dataset (`MITO_Dataset/`, the evaluation set Wave-Former uses per its paper)

- 104 object folders. Real captures sit in `<object>/robot_collected/<x>_<y>_<z>/`, simulations in `<object>/simulation/<x>_<y>_<z>/`.
- Counting the `robot_collected` pose folders: **102 of ~136 are `0_0_0`**. The rest are a scattering of
  single poses (e.g. `90_90_270`, `0_0_180`). So real-world evaluation is mostly at one canonical pose per object.
- Meshes (`uniform_10000.stl`) are Git LFS files. We downloaded five (cracker box, soup can, mustard bottle,
  bleach cleanser, mug) with `hf download`: meters, z up, about 20k faces.

### 2.3 mmNorm (`mmNorm/src/data_processing/`)

- Pipeline: `mmwave_normal_estimation.py` (normals from mmWave) → `sdf.py` (RSDF) → `isosurface_optimization.py`
  (final surface), run by `mmwave_reconstruction.sh` (per its README).
- Needs a GPU and the Dropbox dataset. Not run here.

---

## 3. What to do when access arrives

1. Answer Q1–Q5 with file and function references. Write "not found" when unsure.
2. Set our sim's cutoffs and aperture to Wave-Former's values, and rerun `run_all.py` to see which conclusions survive.
3. If there's a checkpoint: run inference on our simulated partials at upright vs tilted poses (Proposal B), and on
   uniform vs per-part material partials (Proposal A). That gives reconstruction-quality numbers instead of coverage.
