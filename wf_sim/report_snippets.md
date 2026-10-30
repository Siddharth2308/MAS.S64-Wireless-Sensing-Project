# Progress Report 1: section notes (both proposals)

Bullet suggestions for each section of the course guidelines (2–4 pages, due Oct 30, PDF to Fadel + Nazish).
**These are notes for you to write from, not report text.** Pick what fits; each figure has a ready caption at
the end. Details for every figure are in `figures_guide.md`, and assumptions are in `README.md`.

Rule for every mention of results: say it's **our simplified geometric model inspired by Wave-Former's
description, not Wave-Former's simulator**.

---

## 1. Background & Motivation (short, ~½ page)

Shared:
- Wave-Former (Dodds et al.) completes 3D shapes of occluded objects from mmWave. mmWave reflects specularly,
  so the radar sees only the surfaces facing it (our sim: about **4–23% of the surface**).
- It is trained **only on synthetic partial point clouds**: keep points whose normals face the radar, on the
  radar-facing side, apply **randomized angle cutoffs to mimic materials**, add noise. Train PoinTr to complete them.
- Both proposals ask whether that synthetic data matches reality in a way that matters.

Proposal A (Material-Aware):
- Real objects mix materials (metal lid on a glass jar). The synthetic data gives **one random cutoff per
  object**, with no notion of parts or of materials that block vs let the signal through.
- Approach: per-part materials in the data generator → retrain → compare with the baseline and a random-material control.

Proposal B (Orientation-Robust):
- Real objects lie at arbitrary poses. Unknown how Wave-Former sets training orientations (open question).
- The MITO real-world evaluation set is **mostly upright**: 102 of ~136 capture-pose folders are `0_0_0`.
- Approach: measure degradation vs yaw/tilt (turntable rig) → retrain with randomized orientations.

## 2. Progress Made (~1 page, diagrams welcome)

- **Simulator built** (`wf_sim`), a simplified re-implementation of Wave-Former's partial-cloud generation stage
  → `figs/pipeline_diagram.png`, `figs/visibility_schematic.png`
  - 31 × 23 synthetic aperture (60 × 45 cm, 40 cm above the object), specular test, occlusion by ray casting, 2 mm noise
  - **Our extension (A):** cutoff angle **derived from material** (Fresnel R0 + detection threshold) instead of
    random; **per-part** materials; optional **transmission** through glass/plastic (metal blocks)
  - **Pose control (B):** yaw/tilt sweeps with fixed surface samples, so we can measure *which* surface is seen
    (overlap metric), not just how much
- **Objects:** 4 procedural (bottle with cap, hollow mug with handle, hollow glass jar with metal lid, box) and
  **5 real YCB meshes from the MITO dataset** (cracker box, soup can, mustard bottle, bleach cleanser, mug)
- **Validation:** 8 physics tests: plate visible/invisible, sphere matches analytic cap, occlusion, material
  ordering, transmission. All pass.
- **Code reading:** checked MITO's open-source simulator (same lab) and found a fixed 5° specular threshold and a
  separate edge model, with no material parameter (`pipeline_notes.md`). Wave-Former code: no access yet.
- **Hardware ground truth (IWR1443BOOST, no DCA1000, so no raw data / SAR):** brought up TI's demo firmware and
  wrote our own logger (UART decoding, labelled start/stop recording, text log + raw range profiles). Ran 5 sessions
  (`hardware/MEASUREMENT_LOG.md`):
  - sanity checks: distance tracking, stability < 0.1 dB, background 35 dB below metal
  - **found receiver saturation** (a metal plate reads the same ~139 dB from 40 to 120 cm) → reduced TX power (18 dB back-off)
  - **Experiment A:** reflectivity of 3 mm plastic and 4 mm glass vs aluminium at 40 cm
  - **Experiment B:** two-way transmission through each sheet (aluminium plate behind)
  → *setup photos here* (radar + sheet at 40 cm; transmission arrangement)
- **Simulator extended** with a thin-sheet (slab) material model incl. absorption, motivated by the measurements

## 3. Initial Results (~1–1½ pages, quantitative)

Materials (A): `fresnel.png` + table
- Thick-material reflectivity vs metal: **glass −7.5 dB, PET −11.4 dB, PP −13.8 dB** → cutoffs **17° / 14° /
  11° / 10°** (metal / glass / PET / PP at −20 dB threshold)

Orientation (B): `orientation_heatmap_021_bleach_cleanser.png` (panel b) + `orientation_extended_tilt.png`
- Within ±30° tilt, **coverage barely changes** (bleach 3.6–6.5%, mustard 5.1–7.0%, cracker box 8.1–8.9%)
- …but **which surface is visible changes**: overlap with the upright view drops to **39%** at 30° tilt for the
  bleach and mustard bottles (soup can 84%, cracker box 91%)
- Beyond 30°, coverage jumps: **mustard 6% → 29%, bleach 4% → 28%** lying down. Box goes the other way (23% → 16%)
- **Upright is close to the worst case** for tall objects, and it's the pose most real captures use

Per-part materials (A): `material_jar_partials.png` + `material_jar_coverage.png`
- Upright / 20° tilt: only the lid is visible in every condition (metal lid hides the opening; glass walls reflect away)
- On its side: per-part cutoffs change little (lid 6.6 → 7.3%); **transmission through glass doubles body
  visibility (10.4 → 20.2%)** by revealing the inner far wall

Hardware validation (A): `iwr_validation.png`
- Reflectivity vs aluminium at normal incidence: **plastic 3 mm −9.0 dB, glass 4 mm −8.7 dB**, nearly equal.
  The simulator's thick-material model predicts acrylic −12.6 vs glass −7.5 (**5 dB apart**). The thin-sheet model
  (front/back interference) predicts both ≈ −8 dB ✓. This conclusion doesn't depend on the dB-scale calibration.
- Two-way transmission: **plastic −2.8 dB, glass −5.6 dB.** Both sheets let most of the signal through (≈ 52 % / 28 %
  of power). The simulator assumed −1.0 / −3.4 dB (no absorption); the thin-sheet model with a small loss tangent
  matches (−3.1 / −5.9)
- **Jar recalibrated with the measured glass loss:** the transmission effect survives unchanged (body 10.4 → 20.2 %),
  because the revealed inner wall faces the radar squarely; about 2.6 dB of margin remains before it would disappear
- **Takeaway for A:** a wall's radar brightness depends on its **thickness and absorption** as much as its material
  name, so per-part materials should carry thickness + loss

"What hasn't worked / what we learned" (the guidelines ask for this):
- **Yaw alone barely matters** for upright objects. A turntable-only experiment (B as proposed) would show little,
  so B should include **tilt** (≥ 45°)
- **Per-part cutoff angles alone have a small effect.** Flat faces are either seen or not; only curved surfaces
  respond. A's stronger lever is **block (metal) vs pass (glass)**
- Flat-topped objects (box, jar) are insensitive within ±30°, so pick tall/curved objects for experiments
- Our cutoffs (10–17°) are much looser than MITO's 5°, so absolute coverage numbers are model-dependent;
  trends are the result
- **Hardware:** the radar **saturated** on a metal plate at full power (identical readings 40–120 cm). We caught it
  with a distance test and reduced TX power, but 18 dB of nominal back-off lowered readings by only ~7 dB. Either still
  compressed, or our dB scaling or the back-off steps differ from nominal, so **absolute dB values are uncalibrated**
  (relative comparisons at the same setting are fine). Bring-up lessons: Linux ModemManager grabs the serial port;
  the demo needs a reset before re-configuring; config lines must be paced
- No turntable / same-size metal reference yet, so the **angular falloff test (H2) is still open**

## 4. Outstanding Challenges (~½ page)

- **No Wave-Former code/checkpoint:** can't measure reconstruction quality (Chamfer/F-score), only input
  coverage. Plan: request from course staff; fallback: train a small PoinTr on our simulated partials.
- **No DCA1000 capture board:** no SAR imaging or real partial clouds. Plan: use the IWR's on-chip range profile
  for material ground truth now; ask for lab rig (UR5e + capture) time for scans.
- **Simulator parameters only partly validated:** reflectivity and transmission are measured (thin-sheet model +
  loss fits). Lobe width / angular falloff (H2) and the absolute dB scale are not yet. Plan: rotation sweep with a
  turntable and same-size metal reference; scale check with a small target (coin) at known distances.
- **Thin walls (now measured):** real containers have 2–4 mm walls. Measurements confirm thin-wall interference and
  absorption matter (glass ≈ plastic in brightness). The thin-sheet model exists in code but isn't yet used inside
  the partial-cloud generator (needs per-part thickness).
- **Unknowns about Wave-Former's data generation** (orientation ranges, cutoff ranges, occlusion, eval alignment)
  are listed in `pipeline_notes.md`. The answers decide how big each proposal's gap really is.
- (B) Real objects at large tilts need a stable rig: foam wedges/tilting stand.

## 5. Next Steps & Timeline

Suggested only; adjust with Ivan.

By **Nov 20** (Progress Report 2):
- Put the thin-sheet model (thickness + loss per part) into the partial-cloud generator; rerun the jar experiment
- IWR: rotation sweep (H2) with a 3D-printed turntable + same-size metal reference; dB-scale check (coin test);
  more materials (PET bottle wall, PP container)
- Wave-Former access → answer Q1–Q5; if a checkpoint is available, run it on our simulated partials:
  upright vs tilted (B), uniform vs per-part (A) → first **reconstruction-quality** numbers
- If no access: train a small PoinTr baseline on simulated partials (ShapeNet/YCB subset)
- (B) build the tilt + turntable rig; (A) collect mixed-material objects

By **Dec 7** (final):
- (A) retrain with per-part materials + transmission vs baseline vs random-material control; evaluate on real or
  simulated mixed-material objects
- (B) retrain with randomized orientations (incl. large tilts); evaluate degradation vs pose
- Real scans on the lab rig if time allows; final presentation

---

## Figure captions (1–2 sentences each)

- **pipeline_diagram:** Our simplified partial-cloud simulator (top) re-implements the training-data stage
  described for Wave-Former and extends it with material-derived, per-part cutoffs and optional transmission (A)
  and controlled object pose (B); Wave-Former's completion network (bottom) is not reproduced.
- **visibility_schematic:** In our geometric model a surface point is detected only if its normal lies within the
  material's cutoff angle of some radar position and the path is unobstructed; side walls reflect away and stay
  invisible (schematic).
- **fresnel:** Fresnel power reflectivity at 77–81 GHz for approximate permittivities (glass 6, PET 3, PP 2.3);
  the normal-incidence values set each material's cutoff angle in our simplified simulator.
- **orientation_heatmap (bleach):** Coverage (a) and overlap of the visible surface with the upright view (b)
  over 168 poses in our simplified simulator: coverage stays at 3.6–6.5% while overlap falls to ~40% at ±30° tilt.
- **orientation_extended_tilt:** Simulated coverage vs tilt up to 90° (mean over yaw, band = range); tall
  objects jump from ~5% to ~28% once their sides face the radar, so ±30° (shaded) is the least informative range.
- **orientation_summary:** Range of simulated coverage over 168 poses per object (dot = mean, tick = upright);
  flat-topped objects are insensitive, tall curved ones are both sparse and pose-dependent.
- **orientation_examples (bleach):** Simulated partial clouds (blue) at the best and worst pose, from above and
  from the side; most of the surface (grey) is invisible to the specular radar.
- **material_jar_partials:** Simulated partial clouds of a glass jar with a metal lid (orange = lid, blue = body);
  only with transmission through glass does the inner far wall appear (bottom right two panels), also when the glass
  loss is set to our measured value.
- **iwr_validation:** IWR1443BOOST measurements vs material models: reflectivity relative to aluminium (a) and two-way
  transmission (b) for a 3 mm plastic and a 4 mm glass sheet; the simulator's thick-material assumption (orange)
  misses both, a thin-sheet model with small absorption (blue, line = permittivity range) matches.
- **material_jar_coverage:** Visible area per part in our simplified simulator: per-part cutoffs change the lid
  rim slightly (6.6 → 7.3%) while transmission doubles the visible body (10.4 → 20.2%) when the jar lies on its side,
  unchanged when the transmission loss is calibrated to our measurement.

## Key numbers (copy-paste)

| Quantity | Value |
|---|---|
| Cutoff angle, −20 dB (metal / glass / PET / PP) | 17.2° / 13.6° / 11.2° / 9.6° |
| R0 vs metal (glass / PET / PP) | −7.5 / −11.4 / −13.8 dB |
| Visible surface, upright (YCB) | bleach 4.3%, mustard 6.9%, cracker box 8.6%, soup can 10.5%, mug 11.8% |
| Overlap with upright at ±30° tilt | bleach 39%, mustard 39%, mug 74%, soup can 84%, cracker box 91% |
| Coverage 0° → 90° tilt | mustard 6 → 29%, bleach 4 → 28%, soup can 11 → 22%, box 23 → 16% |
| Jar on its side, body visible (uniform / per-part / +transmission) | 10.4 / 10.4 / 20.2% |
| Measured reflectivity vs aluminium (plastic 3 mm / glass 4 mm) | −9.0 / −8.7 dB (thick-material model: −12.6 / −7.5) |
| Measured two-way transmission (plastic / glass) | −2.8 / −5.6 dB (simulator assumed −1.0 / −3.4) |
| Measurement stability / drift | < 0.1 dB frame-to-frame; 0.1–0.6 dB over 5–6 min |
| Radar saturation | metal plate ≈ 139 dB at every distance 40–120 cm at full power |
| MITO real captures at canonical pose | 102 of ~136 pose folders |
| MITO simulator specular threshold | 5° (fixed, no material term) |
