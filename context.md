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
- **Reflectivity vs aluminium (on-chip):** 3 mm plastic -9.0 dB, 4 mm glass -8.7 dB. Thick-material model predicted 5 dB apart.
  - **Don't claim they're the same, or that the thin-sheet model matches.** One sample each, no repeats, uncalibrated scale. E5 decides.
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
- **DCA1000 works (Nov 19).** First raw capture `test_plate_40` matches Studio's peak; setup via `studio_setup_txbo18.lua`. Fixes (flash erase, ramp end 57.1 us, firewall): `debug.md`; results: `MEASUREMENT_LOG.md` Session 6. Next: E0-E4, then E5.
- **E5 focus is reflection.** Transmission is secondary. Add a second thickness, and brushed vs mirror metal as a control (should look identical at 77 GHz).
- **If the DCA won't work by mid-afternoon:** note where it's stuck. Fall back to on-chip glass vs plastic with 5 re-placements each at TX back-off 18.
- **Week to Nov 20:**
  - Thu-Sat: E0-E5.
  - Sun-Mon: more material pairs, and Ivan's multi-material analysis.
  - Tue: figures. Wed: slides. Thu: rehearse.
- **Presentation:** hardware (which materials separate, with repeats), multi-material analysis, orientation sim (short), next steps.
- Glass vs plastic reflection level differed by only 0.3 dB on-chip, and re-placement repeatability is unmeasured. E5 tests both, plus frequency and phase.
- `hardware/dca_process.py` is tested only on synthetic data, not real captures yet.
- **Raw format:** int16, I1 I2 I3 I4 Q1 Q2 Q3 Q4 (matches MITO's loader for this chip).
- Using the demo again with `iwr_logger`: restore run-mode jumpers (normally SOP0 only).

## Later
- Scanner: arm (UR10-class, access not confirmed) or a home-built rail/gantry.
- SAR: test MITO's imaging on their sample raw data first, then real objects (bottle upright vs tilted, lidded jar).
- MITO vs simulator comparison: **on hold**. 150 MB of images are in `mito_download/` (git-ignored), not analysed.
- Ask Laura/staff for the Wave-Former checkpoint and per-object results; otherwise a small PoinTr baseline.
- **mmRender** is cloned in `Project/mmRender/` (git-ignored). It's a CUDA renderer (needs nvcc, `setup.py --cuda-arch`). Not reviewed yet, and not tried on Windows.

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
- `wf_sim/hardware/`: `dca_process.py`, `iwr_logger.py`, `MEASUREMENT_LOG.md`, `PROTOCOL.md`, configs, data.
