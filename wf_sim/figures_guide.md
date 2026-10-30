# Figures guide

What each figure shows, how to read it, what it means, and its caveats. All results come from our
**simplified geometric simulator, not Wave-Former's**. Numbers are from `run_all.py` on 2026-10-30
(deterministic, so a rerun gives the same values).

Quick map:

| Figure | Proposal | One-line takeaway |
|---|---|---|
| `pipeline_diagram.png` | both | what we built vs what Wave-Former does; where A and B plug in |
| `visibility_schematic.png` | both | why most of an object is invisible to mmWave |
| `fresnel.png` + `material_table.csv` | A | material → reflectivity R0 → cutoff angle (17° metal … 10° PP) |
| `orientation_heatmap_<obj>.png` | B | coverage barely changes with pose, but *which* surface is seen does |
| `orientation_examples_<obj>.png` | B | what the partial cloud looks like at best/worst pose |
| `orientation_summary.png` | B | pose sensitivity of all 9 objects at once |
| `orientation_extended_tilt.png` | B | big changes happen past ~40° tilt |
| `material_jar_partials.png` | A | transmission through glass reveals the inside of the jar |
| `material_jar_coverage.png` | A | numbers for the above: cutoff effect small, transmission effect large |
| `iwr_validation.png` | A | real radar: glass ≈ plastic in brightness; both transmit; simulator's thick-material model is off |

---

## 1. `pipeline_diagram.png`: what we built

- **Top row (blue, built):** mesh with part materials → pose → surface samples → specular test against the radar
  grid → occlusion/transmission → noise → partial cloud. The material table feeds the specular test.
- **Bottom row (grey dashed, not reproduced):** Wave-Former's shape-completion network (PoinTr), and its real-data
  inference path (SAR → mmNorm → candidate partials).
- **Tags:** **A** marks the steps Proposal A changes (per-part materials, material table, transmission). **B**
  marks the step Proposal B changes (pose).
- **Use in the report:** the "Progress Made / system design" figure. It makes clear we built stage 1 only.

## 2. `visibility_schematic.png`: the visibility rule

- Side view of a bottle under the radar aperture (black bar, 40 cm above). The shaded wedge at each point is the
  "normal ± cutoff" cone (metal ≈ 17°).
- **Cap top:** the normal points straight up, the cone hits the aperture, so it's **seen**.
  **Shoulder:** the cone just reaches the aperture edge, so it's **partly seen**.
  **Side wall:** the normal points sideways, so the echo misses every radar position and it's **not seen**.
- **Meaning:** mmWave reflects like a mirror, so only surfaces facing the radar are seen. Typically that's **4–23%
  of an object's surface** in our runs. That's why Wave-Former needs shape completion at all.
- **Caveat:** schematic, not to scale for the cone lengths. Real radars also see edges (diffraction), which we don't model.

## 3. `fresnel.png` and `results/material_table.csv`: materials (Proposal A)

- **Plot:** power reflectivity |Γ|² vs incidence angle for glass, PET and PP (TE solid, TM dashed; dots = Brewster
  angle). Metal is the flat line at 1.
- **Read the left edge (0°):** that's what a monostatic radar sees. **Metal 1.0 (0 dB), glass 0.18 (−7.5 dB),
  PET 0.07 (−11.4 dB), PP 0.04 (−13.8 dB).**
- **Table:** turns R0 into a cutoff angle with our detection rule. With the default −20 dB threshold:
  **metal 17.2°, glass 13.6°, PET 11.2°, PP 9.6°**. With −15 dB: 14.9 / 10.5 / 7.2 / 4.3°. With −25 dB:
  19.2 / 16.0 / 14.1 / 12.9°.
  Acrylic (ε = 2.6, added for the IWR tests): R0 −12.6 dB, cutoff 10.4°.
- **`results/sheet_predictions.csv`:** thin-sheet predictions for the sheets we measure (glass 4 mm, acrylic 3 mm).
  The thick-material and thin-sheet models agree for glass (−7.5 vs −7.0 dB) but differ by about 5 dB for acrylic
  (−12.6 vs −7.2 dB). The IWR measurement decides which one is right.
- **Meaning:** a weaker reflector has less signal margin, so it must face the radar more squarely to be detected.
  This is our physics-based replacement for Wave-Former's *randomized* cutoffs.
- **Caveats:** permittivities are approximate. Thick-material reflectivity is assumed; thin walls can differ by up
  to ±8 dB. The threshold choice changes the cutoffs a lot for weak reflectors (PP: 4° to 13°).

## 4. `orientation_heatmap_<obj>.png`: pose sensitivity (Proposal B)

Both panels use yaw (0–345°) on x and tilt (−30…+30°) on y. Each cell is one pose. Material is metal.

- **(a) Coverage:** the % of surface area detected. × marks the worst pose.
- **(b) Overlap with upright:** of the surface visible at this pose and at the upright pose combined, the % seen in
  both (Jaccard). 100% means the same patch is seen; low means a different part of the object is seen.
- **Key numbers** (overlap averaged over yaw, at |tilt| = 0 / 10 / 20 / 30°):

  | Object | Coverage range | Overlap 0° | 10° | 20° | 30° |
  |---|---|---|---|---|---|
  | bleach cleanser | 3.6–6.5% | 89% | 78% | 62% | **39%** |
  | mustard bottle | 5.1–7.0% | 68% | 59% | 48% | **39%** |
  | YCB mug | 10.6–12.0% | 93% | 89% | 83% | 74% |
  | tomato soup can | 10.5–11.5% | 97% | 94% | 90% | 84% |
  | cracker box | 8.1–8.9% | 98% | 98% | 96% | 91% |
  | procedural mug | 8.4–9.1% | 96% | 95% | 93% | 90% |
  | bottle (procedural) | 3.3–6.2% | 35% | 31% | 32% | 32% |
  | jar_lid, box | constant (7.6%, 23.2%) | 100% | 100% | 100% | 100% |

- **Meaning:** within ±30°, *how much* is seen barely changes. For tall curved objects, **what is seen changes a
  lot**: at 30° tilt, about 60% of the visible surface of the bleach/mustard bottles differs from the upright view.
  A completion model trained mostly on one pose would get unfamiliar inputs. That's the core argument for B.
- **Read the stripes:** the faint repeating pattern along yaw comes from the aperture being a rectangle
  (60 × 45 cm). Leaning the object toward the long vs the short side of the aperture changes what is caught.
- **Caveats:** the procedural bottle's low overlap *even at 0° tilt* happens because its visible region is a thin
  band right at the cutoff edge, so small changes flip it. That's real in the model but threshold-sensitive, so
  don't headline it. The box and jar have flat tops that stay visible within ±30°, so they show no effect.

## 5. `orientation_examples_<obj>.png`: what the partial clouds look like

- 2 × 2 grid: best pose (top row) and worst pose (bottom row), seen from above (left) and from the side (right).
  Grey is the full surface (subsampled) and blue is the detected partial cloud.
- **Example, bleach:** worst (yaw 60°, tilt 20°) is 3.6%, mostly the cap/shoulder. Best (yaw 300°, tilt 30°) is
  6.5%, which also catches part of the upper body and a patch near the base.
- **Use:** a concrete picture of the network's input. Pair one example with its heatmap.

## 6. `orientation_summary.png`: all objects together

- One row per object. The blue bar runs from min to max coverage over 168 poses, the dark dot is the mean, and
  the orange tick is upright.
- **Read:** a long bar means pose-sensitive. A tick at the left end means upright is near the worst pose. A dot
  with no bar means insensitive in ±30°.
- **Meaning:** flat-topped objects (box 23%) are easy. Tall curved objects (bottles 4–7%) give the network very
  little, and their coverage depends on pose.

## 7. `orientation_extended_tilt.png`: beyond ±30° (Proposal B)

- One panel per object. Tilt runs from 0° (upright) to 90° (lying down). The line is coverage averaged over
  4 yaws and the band is min–max. The grey shading is the ±30° range of the main sweep.
- **Key numbers (0° → 90°):** mustard 6% → 29%, bleach 4% → 28%, bottle 4% → 23%, soup can 11% → 22%,
  box 23% → 16% (big top face turns away), mugs and jar change little (stay within about 8–13%).
- **Meaning:** the ±30° range is the *calm zone*. The big changes happen at 40–60°, when long sides start facing
  the radar. Upright is close to the *worst* case for tall objects, and most real MITO captures are upright
  (102 of ~136 pose folders).
- **For B's plan:** test tilts beyond 30° (e.g. 45°, 60°, 90°), not just turntable yaw.

## 8. `material_jar_partials.png`: lidded jar (Proposal A)

- Grid: rows are poses (upright, tilt 20°, on its side) and columns are conditions (uniform glass; per-part: metal
  lid + glass body; per-part + transmission with ideal lossless glass; per-part + transmission with the glass loss
  **measured** in IWR session 5). Orange is visible lid, blue is visible body, grey is the full surface.
- **Read:**
  - **Upright and 20°:** only the lid top is seen in all three conditions. The lid covers the opening, and the
    glass side walls reflect away.
  - **On its side:** a strip along the top of the glass wall plus the lid's rounded edge.
  - **Right column only:** an extra **inner** strip appears. It's the inside of the far wall, seen *through* the
    near glass wall.
- **Meaning:** what changes the partial cloud most is **which parts block (metal) vs pass (glass)** the radar,
  not the cutoff angle.

## 9. `material_jar_coverage.png`: the numbers

| Pose | Body: uniform / per-part / +trans. | Lid: uniform / per-part / +trans. |
|---|---|---|
| upright | 0 / 0 / 0% | 37.1 / 37.1 / 37.1% |
| tilt 20° | 0 / 0 / 0% | 37.1 / 37.1 / 37.1% |
| on its side | **10.4 / 10.4 / 20.2%** | **6.6 / 7.3 / 7.3%** |

- **Cutoff effect (uniform → per-part):** only the lid's curved rim changes (6.6 → 7.3%). A flat face is either
  seen or not, and a few degrees of cutoff don't flip it. Only curved surfaces respond.
- **Transmission effect:** body visibility **doubles (10.4 → 20.2%)**, and these are surfaces that a
  one-material-per-object model can't produce. The metal lid still blocks everything behind it (body = 0% upright).
- **For A's plan:** frame the per-part idea around **occlusion/transmission per material**, not only per-part cutoffs.
- **Calibrated (4th group):** with the glass loss set to our measurement (−5.6 dB two-way for 4 mm, about 1.1 dB
  extra per surface), the body stays at **20.2%**. The revealed inner wall faces the radar within 8°, so it stays
  above threshold with about 2.6 dB to spare. The effect would vanish only at about 5 dB extra loss per surface.

## 10. `iwr_validation.png`: real radar vs material models (Proposal A)

- Two panels, dB relative to the 6 mm aluminium plate. **Black = measured** with the IWR1443BOOST (error bar = drift
  between the start and end metal readings), **orange = simulator's thick-material assumption**, **blue = thin-sheet
  model** with a small loss tangent (blue line = range over plausible permittivities).
- **(a) Reflectivity at normal incidence, 40 cm:** plastic 3 mm −9.0 dB, glass 4 mm −8.7 dB. They're nearly equal,
  while the thick-material model says glass should be 5 dB brighter (−7.5 vs −12.6). The thin-sheet model gets both
  (−7.8 / −8.2).
- **(b) Two-way transmission** (plate at 60 cm, sheet at 40 cm): plastic −2.8 dB, glass −5.6 dB. The simulator assumed
  −1.0 / −3.4 because it has no absorption; the thin-sheet model with loss gives −3.1 / −5.9.
- **Meaning:** what makes a wall bright or see-through is its **thickness and absorption** as much as its material.
  For A, per-part materials should carry thickness + loss. "Glass passes, metal blocks" holds on real hardware.
- **Caveats:**
  - absolute dB scale not independently calibrated (see `hardware/MEASUREMENT_LOG.md`, session 3); the "glass ≈
    plastic" result is scale-independent
  - the metal reference is a different size than the sheets (fine at 0°)
  - the plastic's exact type is unconfirmed
  - one sample per material, at one angle (0°)
