# Project context

Same files on Linux and Windows (`Project/` is on a shared NTFS partition). Claude Code's memory doesn't carry across, so this file does.

## How to work with me
- **Plan first, no sprees:** discuss before starting anything new. Report what you did and why after each significant step, then wait for my OK.
- **Report writing:** default to section bullets, figures and figure guides. Write full prose only when I ask, in my style (`../Paper Review- WiTrack.md`, plain with concrete numbers).
- **Docs:** short, to-the-point bullets.
- **Git:** don't commit or push unless I ask.
- **Downloaded pickles:** MITO `.pkl` files can run code when loaded. Scan first, and keep to the numpy-only allowlist.

## Project
- MAS.S64 (MIT), with Ivan Wren. Builds on Wave-Former (mmWave 3D shape completion).
- **Proposal A:** per-part materials in synthetic training data. **Proposal B:** orientation robustness.
- **Staff feedback (Nov):** report and proposal graded A. Their points:
  - Our "glass ≈ plastic" conclusion is problematic. Resolve it with data; don't repeat it.
  - Proposal A is about **reflectivity**, not transmission.
  - Their plan: (1) analyse Wave-Former results on multi-material objects, (2) label objects with materials, (3) flat surfaces of 2 materials, (4) proceed, possibly with Nazish supervising.
- **Our response plan** (`Feedback Response & Plan.pdf` in `Project/`):
  - Part 1, core: multi-material dataset, Wave-Former recall/precision on multi-material objects, material labels, flat-surface tests (vary thickness and finish), mmRender material properties.
  - Part 2: orientation-variant objects and next-best angles.
- **Split:** Siddharth on hardware (E0-E5). Ivan on ML and simulation (multi-material analysis, labels, checkpoint or PoinTr baseline).
- No Wave-Former code or checkpoint yet. `wf_sim` is **our simplified model, not Wave-Former's simulator**; always say so.
- **Deadlines:** presentation / Progress Report 2 on **Fri Nov 20**, final presentation on Dec 7.

## Findings so far
- **Reflectivity vs aluminium (on-chip, superseded by DCA E5):** 3 mm plastic -9.0 dB, 4 mm glass -8.7 dB. The on-chip dB was compressed (E4), so this doesn't show glass ≈ plastic. Don't repeat it.
- **Two-way transmission:** plastic -2.8 dB, glass -5.6 dB. Simulator assumed -1.0 / -3.4 dB (no absorption).
- **Simulated orientation:** at 30° tilt, overlap with upright falls to 39% (bleach, mustard). Yaw alone barely matters.
- **Open:** metal read about 139 dB from 40 to 120 cm (saturation). 18 dB back-off lowered readings only about 7 dB, so the absolute dB scale is uncalibrated.
  - **DCA E1 (Nov 19):** raw ADC is far from clipping at bo18 (max ~167 of 32767), yet the level still barely changes 40 → 60 cm. Likely the chip's IF high-pass filters, not saturation (hypothesis).
  - **DCA E4 (Nov 19):** raw data is linear for bo0-12 (about -6.5 dB per 6 dB step); bo18 is about 9 dB below that line. The on-chip demo compressed (7 dB for 18 dB). **Use bo6 for E5.**
- **DCA E5 (Nov 19, 5 re-placements each, bo6):** 3 mm glass -11.9 ± 2.2 dB, 3 mm acrylic -6.7 ± 1.7, 3 mm epoxy glass -6.7 ± 1.6, 6 mm glass -8.0 ± 1.0, 7 mm acrylic -21.9 ± 3.9 (vs aluminium).
  - Glass vs acrylic at 3 mm: means differ by 5.2 dB (p = 0.004), but a single capture's level doesn't separate them (placement sd 1-2 dB). The frequency shape does (post-hoc).
  - Acrylic and epoxy are indistinguishable. Thickness matters as much as material. Details: `MEASUREMENT_LOG.md` Session 6.
- **Biggest gap:** nothing yet shows these input changes hurt reconstruction.
- Plastic identity is unconfirmed. Details: `wf_sim/hardware/MEASUREMENT_LOG.md`.

## Current work
- **Hardware (Nov 19): E0-E5 Part 1 done** on the DCA1000. Setup: `studio_setup_txbo18.lua`, then `studio_set_backoff.lua` (bo6). Fixes: `debug.md`. Results: `MEASUREMENT_LOG.md` Session 6. `dca_process.py` now runs on real captures.
  - Not done: E5 Part 2 (transmission, optional), caliper thicknesses (nominal values used), setup photos, 2-material flat surfaces (plastic in front of metal).
- **YCB material labels (Nov 20): done.** `wf_sim/materials/ycb_materials.csv`: 72 objects (mmRender's YCB list), 104 parts, all validated by Siddharth against YCB photos. Details: `wf_sim/materials/README.md`.
  - Open: blank area_share on 027 skillet and 070 wood blocks. Mug/bowl/plate are one set but labelled plastic/plastic/ceramic (could be enamel steel). Some notes still say "check".
- **mmRender (Ivan):** no material term yet (equal-weight points). Plan for staff:
  - Task: per-point reflectivity from labels (part → material → reflectivity; E5 values for glass/acrylic/epoxy, model estimates for the rest).
  - Expected: plastic/glass parts render weaker than metal (up to ~15 dB in E5).
  - Metrics: rendered vs real (MITO) radar images, before vs after; later reconstruction recall/precision on multi-material objects.
  - Not created yet: `material_reflectivity.csv` (E5 measured + assumed values).
- **Presentation Nov 20:** hardware (E5 summary, E4 back-off, E1), labels, mmRender plan, gaps. Figure picks: `dca_E5_summary.png`, `dca_E4_backoff.png`, `dca_E1_40_vs_60.png`, plus a setup photo.
- **Raw format:** int16, I1 I2 I3 I4 Q1 Q2 Q3 Q4 (matches MITO's loader for this chip).
- Using the demo again with `iwr_logger`: restore run-mode jumpers (normally SOP0 only).

## Later
- Scanner: arm (UR10-class, access not confirmed) or a home-built rail/gantry.
- SAR: test MITO's imaging on their sample raw data first, then real objects (bottle upright vs tilted, lidded jar).
- MITO vs simulator comparison: **on hold**. 150 MB of images are in `mito_download/` (git-ignored), not analysed.
- Ask Laura/staff for the Wave-Former checkpoint and per-object results; otherwise a small PoinTr baseline.
- **mmRender** is cloned in `Project/mmRender/` (git-ignored; never commit it). It's a CUDA renderer (needs nvcc, `setup.py --cuda-arch`). Not tried on Windows. Ivan is working on it.

## Windows setup (first time)
Install Python 3.10+ (tested with 3.12). The Linux `.venv` won't work on Windows, so create a separate one:
```powershell
cd <drive>:\...\Project\wf_sim
py -m venv .venv-win
.venv-win\Scripts\activate
pip install -r requirements.txt
python -m pytest -q
```
Expect 24 tests to pass. They have only been run on Linux so far. Then start `claude` in `Project\`, where `CLAUDE.md` loads this file.

For capture, install mmWave Studio and MATLAB Runtime 8.5.1. Windows problems: `debug.md`.

## Key files
- `experiment.md`: current experiments. `debug.md`: Windows troubleshooting.
- `README.md`: general setup. `OVERVIEW.md`: high-level status (updated Nov 12, includes staff feedback). `report.md`, `wf_sim/report_snippets.md`, `wf_sim/figures_guide.md`: report material.
- `wf_sim/hardware/`: `dca_process.py`, `watch_peak.py`, Studio `.lua` scripts, `iwr_logger.py`, `MEASUREMENT_LOG.md`, `PROTOCOL.md`, configs, data.
- `wf_sim/materials/`: YCB material labels, `label_ui.py`, `fetch_photos.py` (see its README).
