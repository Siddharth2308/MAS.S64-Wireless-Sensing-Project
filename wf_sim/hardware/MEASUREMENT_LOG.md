# Measurement notebook: IWR1443BOOST ground-truth tests

Running record of every hardware session: what was measured, setup, results, and what we concluded.
Raw data: `logs/session_<id>.txt` (readable per-frame log) and `data/session_<id>/<label>.npz` (full range
profiles + config). Plan and background: `PROTOCOL.md`. Model predictions: `../results/sheet_predictions.csv`.

---

## Setup (common to all sessions)

| Item | Details |
|---|---|
| Radar | TI **IWR1443BOOST** (77–81 GHz, 3 TX / 4 RX on board; config uses TX1+TX3, all 4 RX). No DCA1000 capture board, so no raw ADC data |
| Firmware | TI mmWave SDK **2.01** out-of-box demo (xWR14xx), was already on the board |
| Antenna beam | ±28° horizontal, ±14° vertical (3 dB), from TI user guide SWRU518D |
| Power | Bench supply, 5.0 V via barrel jack; current limit used: ___ A (fill in), measured draw idle / running: ___ / ___ A |
| Host | Linux laptop; TI Cloud Agent + mmWave Demo Visualizer (Chrome) for first bring-up; then our logger (`iwr_logger.py`) |
| Config | Exported from the Visualizer ("best range resolution"): `iwr1443_range_profile.cfg` |
| Key config values | range resolution 4.4 cm (bin spacing 4.09 cm), max range ≈ 9 m, 100 ms frames (10 fps), **static clutter removal off**, range profile output on, TX back-off 0 dB, RX gain 30 dB |
| Data used | Zero-Doppler **range profile** (log magnitude, dB, arbitrary reference) from the demo's UART output |

### Bring-up issues and fixes
1. **"Cannot open serial port"** in the Visualizer → Ubuntu's ModemManager was probing `/dev/ttyACM*`; stopped it.
2. **Data port stuck "connecting"** → normal until a config is sent.
3. **Config could not be re-sent** after the first run → the demo needs a board reset (NRST) before re-configuring.
4. **Our logger: config line garbled** (`adcbufCfg` arrived as `bufCfg`) → the logger sent lines before the board's
   prompt returned. Fixed: wait for "Done" + prompt, 50 ms pause, retry garbled lines.

### Materials on hand

| Item | Size | Thickness | Use |
|---|---|---|---|
| SMT solder stencil (stainless sheet in aluminium frame) | large | thin | Session 1 only. **Not used further**: frame adds echoes, wrong size |
| Aluminium plate | 22.5 × 39 cm | 6 mm | Linearity / saturation tests; Experiment B back plate |
| Glass ("Spectrum" art glass, coloured) | 30.5 × 30.5 cm | 4 mm | Experiment A + B |
| Opaque plastic, "feels like acrylic" (identity unconfirmed) | 30.5 × 30.5 cm | 3 mm | Experiment A + B |
| Kitchen foil (to tape over a sheet) | — | — | Same-size metal reference for Experiment A |

Model predictions for these sheets (dB relative to metal at normal incidence):

| Sheet | Thick-material model (simulator) | Thin-sheet model, lossless | Thin-sheet, tanδ = 0.01 | Two-way transmission, lossless → tanδ 0.01 |
|---|---|---|---|---|
| Glass 4 mm (ε ≈ 6) | −7.5 | −7.0 (band −19.6 … −4.0) | −7.6 | −1.9 → −3.5 |
| Acrylic 3 mm (ε ≈ 2.6) | −12.6 | −7.2 (band −7.5 … −7.0) | −7.5 | −1.9 → −2.5 |

---

## Session 1: sanity check, metal stencil, hand-held: `session_20261030_174336`

**Goal:** confirm our logger reads the radar correctly (distance axis, decoding, stability).
**Setup:** SMT stencil (in frame), **hand-held**, facing the radar at nominal 30 / 40 / 50 cm. Search window 25–60 cm.

| Segment | Frames | Peak | Peak at | Frame std |
|---|---|---|---|---|
| plate_40cm | 29 | 138.6 dB | 45.0 cm | 0.00 dB |
| plate_30cm | 30 | 139.3 dB | 36.8 cm | 0.05 dB |
| plate_50cm | 25 | 139.5 dB | 53.1 cm | 0.07 dB |
| removed | — | not recorded | | |

**Findings**
- ✅ Logger works end to end: config, decoding, range axis.
- ✅ Peak follows the plate. A constant **+5–7 cm offset** (uncalibrated range bias + reference point); irrelevant for level comparisons.
- ✅ Very stable (< 0.1 dB frame to frame).
- ✅ Background away from the plate ≈ 80–90 dB, so about 50 dB of headroom.
- Multipath: second peak at about 2× the plate distance (radar → plate → radar → plate).
- ⚠️ **Same level (≈ 139 dB) at all three distances**, suspicious of receiver saturation (or hand alignment). → Session 2.

---

## Session 2: distance series (linearity check), aluminium plate: `session_20261030_182219`

**Goal:** check whether the level falls with distance (linear receiver) or stays flat (saturation).
**Setup:** aluminium plate 22.5 × 39 cm, **standing on its short edge** (39 cm tall), centre at about radar height,
aligned at each distance by turning it to maximise the live peak; steadied by hand from behind.
Search window 25–150 cm.

| Segment | Frames | Peak | Peak at | Frame std | Note |
|---|---|---|---|---|---|
| removed | 32 | 121.2 dB | 134.9 cm | 1.66 dB | background: strong reflector in the room at ≈ 1.35 m |
| plate_40cm | 45 | 137.7 dB | 45.0 cm | 0.22 dB | |
| plate_60cm | 65 | 137.7 dB | 65.4 cm | 4.50 dB | plate moved during recording → redone |
| platte_60cm (redo) | 30 | 139.3 dB | 65.4 cm | 0.56 dB | use this one |
| plate_80cm | 42 | 139.2 dB | 85.9 cm | 0.56 dB | |
| plate_100cm | 58 | 137.0 dB | 106.3 cm | 4.25 dB | first frames ramp 127 → 139 dB (still being placed) |
| plate_120cm | 66 | 138.1 dB | 126.7 cm | 4.28 dB | moved during recording |

Background (removed) at the plate positions: 103 dB @ 45 cm, 115 dB @ 65–86 cm, 113 dB @ 106 cm, 106 dB @ 127 cm.

**Findings**
- ✅ Distance tracking correct at every position (same +5 cm offset).
- ❌ **Level flat at ≈ 137–139 dB from 40 to 120 cm.** A flat plate (mirror) should lose **≥ 9.5 dB** over 3× the
  distance (1/(2d)²), and a small target 19 dB. Every segment tops out at the same **ceiling ≈ 139.5 dB**.
- **Conclusion: the receive chain saturates** for a metal plate anywhere in 40–120 cm at full TX power and 30 dB
  RX gain. Material comparisons against metal would be compressed or meaningless until the signal is reduced.
- The far-range noise floor (6–10 m) does not rise with the plate present (87–90 dB vs 91 dB empty).
- Lesson for the protocol: rest the plate on a support; small hand movements cause 4 dB jitter.

---

## Session 3: TX power back-off test

**Goal:** find the TX back-off that brings the metal plate below the saturation ceiling.
**Setup:** aluminium plate at 40 cm, aligned once, **not touched between runs**. One run per config, NRST before each.

| Config | Back-off | Label | Peak | Frame std | Notes |
|---|---|---|---|---|---|
| `iwr1443_txbo0.cfg` | 0 dB | bo0 | 138.66 dB at 49.1 cm | 0.04 dB | session `184203` |
| `iwr1443_txbo0.cfg` | 0 dB | *(labelled "bo6" by mistake)* | 138.66 dB at 49.1 cm | 0.02 dB | session `184203`, actually a **0 dB repeat**: identical, so repeatable |
| `iwr1443_txbo6.cfg` | 6 dB | b06 | 136.97 dB at 45.0 cm | 0.03 dB | session `184402` (−1.7 vs 0 dB) |
| `iwr1443_txbo12.cfg` | 12 dB | bo12 | 133.86 dB at 45.0 cm | 0.00 dB | session `184502` (−4.8 vs 0 dB) |
| `iwr1443_txbo18.cfg` | 18 dB | bo18 | 131.51 dB at 45.0 cm | 0.04 dB | session `184550` (−7.2 vs 0 dB) |

**Result:** the board accepted every back-off value, and the reading falls steadily, but **only by 7.2 (logger) dB
for 18 dB of nominal back-off** (steps: −1.7, −3.1, −2.4 per 6 dB). The far-range floor (6–10 m) fell similarly:
89.0 → 86.7 → 83.4 → 80.5 (−8.5 for 18 dB). The peak sits between bins 11–12 (45–49 cm) and stayed put.

**Interpretation (open):** the readings drop less than one-for-one. Possible causes:
(1) still compressed (saturated) at all settings; (2) our dB conversion of the range profile is off by a factor of
about 2–2.5 (never checked against the Visualizer); (3) the back-off code is not 1 dB per step on this device.
The far-range floor falling by a similar amount argues against (1) alone. Next: an independent scale check with a
small target whose distance law is known.

**Original expectation:** the reading stays near 139 dB while saturated, then drops 1 dB per dB of back-off once the receiver is
linear. The first one-for-one setting is what Experiments A and B use. If the board rejects non-zero back-off,
fall back to lowering RX gain.

---

## Session 4: Experiment A (reduced), reflectivity at 0°: `session_20261030_185358`

**Setup:** config **bo18**. Each item leaning upright on books, front face at 40 cm (reads 45 cm), aligned for max
peak, nobody touching during recording. **Metal reference = the 6 mm aluminium plate** (no foil available, so
sizes differ: plate 22.5 × 39 cm, sheets 30.5 × 30.5 cm; acceptable at 0° because all are much larger than the
reflecting zone). **No rotation sweep** (no turntable), so H2 is deferred.

| Segment | Frames | Level at 45 cm | vs metal | Frame std |
|---|---|---|---|---|
| alu_40 | 111 | 131.61 dB | 0 (ref) | 0.11 dB |
| plastic_40 (opaque, 3 mm) | 316 | 122.58 dB | **−9.0 dB** | 0.00 dB |
| glass_40 (art glass, 4 mm) | 133 | 122.86 dB | **−8.7 dB** | 0.00 dB |
| empty_40 | 106 | 96.99 dB | −34.6 dB | 0.13 dB |
| alu_40_end | 127 | 131.51 dB | drift −0.1 dB | 0.03 dB |

**Comparison with models** (dB vs metal):

| Sheet | Measured | Thick-material (simulator) | Thin-sheet model, plausible ε range |
|---|---|---|---|
| Plastic 3 mm | −9.0 | −11.0 … −13.8 (ε 3.2 … 2.3) | −7.2 … −10.7 (ε 2.3–3.2) ✓ |
| Glass 4 mm | −8.7 | −6.9 … −7.9 (ε 7 … 5.5) | −3 … −12 (very sensitive to ε) |

**Findings**
- ✅ Very clean data: drift 0.1 dB over 5 min, frame noise ≤ 0.1 dB, background 35 dB below metal.
- **Glass and plastic reflect almost the same (0.3 dB apart).** The simulator's thick-material model predicts glass
  ≈ 5 dB brighter than acrylic. This holds whatever the dB scale factor turns out to be.
- Plastic (−9.0) fits the **thin-sheet model** and sits ≥ 2 dB above every thick-material prediction.
  Glass is inconclusive (the thin-sheet prediction swings ±5 dB with ε).
- **Implication for Proposal A:** a real wall's brightness depends on its **thickness as much as its material**,
  so per-part materials should carry wall thickness. The thick-material simulator mis-ranks thin walls.
- Caveats: dB scale not yet independently calibrated (Session 3 question); metal may still be mildly compressed at
  bo18, which would make the true metal–sheet gap larger.

---

## Session 5: Experiment B, transmission: `session_20261030_191359`

**Setup:** config **bo18**, search window 55–80 cm. Aluminium plate at 60 cm (reads 65.4 cm, bin 16), aligned once,
never moved. One sheet at a time at 40 cm, square to the radar, leaning on books. Loss = plate level with the sheet −
plate level alone (mean of start and end).

| Segment | Frames used | Plate level | Two-way loss | Sheet's own echo (45 cm) |
|---|---|---|---|---|
| t_alu_only | 70 | 130.67 dB | ref | 94.1 dB (nothing there) |
| t_plastic | 76 | 127.56 dB | **−2.8 dB** (−2.5 … −3.1 vs start/end) | 124.2 dB |
| t_glass | **141 of 169**: glass fell at frame 141, later frames discarded | 124.83 dB | **−5.6 dB** (−5.3 … −5.8) | 123.1 dB |
| t_alu_only_end | 86 | 130.10 dB | drift −0.6 dB over 6 min | 93.1 dB |

**Comparison with models** (two-way, dB):

| Sheet | Measured | Simulator (2 interfaces, no absorption) | Thin-sheet model |
|---|---|---|---|
| Plastic 3 mm | −2.8 | −1.0 | −1.3 … −1.9 lossless; −2.4 … −3.1 with tanδ 0.02 ✓ |
| Glass 4 mm | −5.6 | −3.4 | −1.9 lossless (ε 6); **−5.1 … −5.6 with tanδ 0.02–0.03** ✓ |

**Findings**
- ✅ **H3 confirmed qualitatively:** both sheets pass most of the signal. The plate behind stays strong: about 52 %
  of the power through plastic and about 28 % through glass (two-way). Seeing through glass and plastic is real.
- ❌ **The simulator underestimates the loss by about 2 dB per sheet.** It ignores absorption. A thin-sheet model with
  a modest loss tangent (≈ 0.02 plastic, 0.02–0.03 coloured glass) matches both.
- **Implication for Proposal A:** the jar's "transmission doubles visible body" result (sim: 10.4 → 20.2 %) is an
  upper bound. **Rerun with the measured loss (≈ 1.1 dB extra per glass face): body coverage unchanged at
  20.2 %**, because the revealed inner wall faces the radar within 8° (≈ 2.6 dB margin to the threshold).
  Figure: `figs/iwr_validation.png`; numbers: `results/iwr_validation.csv`.
- Sheet echoes at 40 cm (124.2 / 123.1 dB) are consistent with Session 4's reflectivity (122.6 / 122.9 dB).
- Not measured: a metal sheet in front (blocking case). Expected to block almost completely.

---

## Session 6 (Nov 19): DCA1000 bring-up and first raw capture: `data/dca/test_plate_40`

**Setup (differs from Sessions 1–5)**

| Item | Details |
|---|---|
| Capture | **DCA1000EVM** (FPGA 2.9 [Record]) via the 60-pin **ribbon cable**, Ethernet to PC; raw ADC, 16 bit, complex 1x, 4 LVDS lanes |
| Host | Windows 11, mmWave Studio 2.1.1.0, Rf eval firmware loaded to RAM each power-up |
| Setup | One-click script `studio_setup_txbo18.lua` (reset → firmware → SPI → RF → profile/chirps/frame → DCA) |
| Chirp | Same as demo cfg: 77 GHz start, slope 70 (Studio rounds to 70.0057) MHz/µs, 240 samples at 4884 ksps, RX gain 30 dB, **TX back-off 18 dB**. **Ramp end 57.1 µs** (demo: 57.14, see fix 5) |
| Frame | chirp 0 = TX1, chirp 1 = TX3, 16 loops, 100 ms; 20 frames |
| Scene | Aluminium plate (22.5 × 39 cm) at ~40 cm, hand-placed (test capture only, not E1) |

**Bring-up issues and fixes** (details in `../../debug.md`)

| # | Symptom | Cause / fix |
|---|---|---|
| 1 | RS232 connect fails | Jumpers wrong → dev mode **SOP0 + SOP1 closed, SOP2 open** |
| 2 | "Power on one Device at a time!" on SPI Connect | Devices Detected = 0 → refresh until 1 |
| 3 | SPI Connect: MSS version 0.0.0.0, PowerOn RESP TIMEOUT, "MSS Power Up async event was not received"; RF Power-up error −2 | Fixed by **UniFlash 9.7.1 "Format SFLASH"** in flash mode (SOP0 + SOP2), then back to dev mode (Nov 19, 14:52). Likely cause: the demo in flash got in the way |
| 4 | Re-doing every GUI step after each power-cycle | Wrote `studio_setup_txbo18.lua` |
| 5 | Script: ProfileConfig "RAMP END FREQUENCY IS NOT WITHIN VCO RANGE" (error 46) | 77 + 70.006 × 57.14 µs = 81.0001 GHz > 81 GHz limit → ramp end **57.1 µs** (80.997 GHz). ADC window ends at 56.1 µs, so sampled band unchanged |
| 6 | Capture: 0 packets received; PostProc error `calc_rel_offset_and_file_name` | Windows Firewall (Ethernet on **Public**) dropped the DCA's UDP data → inbound rule for UDP 4096/4098 from 192.168.33.180 only |
| 7 | Studio file picker needs an existing file | Create an empty `adc_data.bin` first |
| 8 | `adc_data.bin` 0 bytes right after capture; PostProc `calc_rel_offset_and_file_name` error on good captures (E3) | DCA writes `adc_data_Raw_0.bin`, which becomes `adc_data.bin` seconds later, even when PostProc fails. Wait; check file size and packet log, ignore the PostProc error |

**First capture: `test_plate_40`** (20 frames)

| Check | Result |
|---|---|
| Packets | 1688 received, 0 out of sequence, 0 zero-filled |
| File | 2,457,600 bytes = 20 frames × 32 chirps × 240 samples × 4 RX × 4 B ✅ |
| `complete` / `clip_pct` | True / 0 ✅ |
| `max_adc` | **181** of 32767 (about −45 dBFS) |
| Peak (ours) | 34.3 dB re 1 count at **49.0 cm** (bin 12); RX bins 11 12 12 11 |
| Peak (Studio PostProc) | ~0.46 m on the 1D FFT, detection at ~0.5 m, 0°; ~−55 dBFS |
| Double bounce | ~86–87 cm, ~5 dB below the plate (both tools) |
| Stability (2 s) | level std 0.03 dB; phase std 0.17° (0.9 µm), range 0.73° |

Figures:
- Our processing: [`logs/dca_test_plate_40.png`](logs/dca_test_plate_40.png) (range profile + phase vs time)
- Studio PostProc, full window: [`logs/studio_postproc_test_plate_40.png`](logs/studio_postproc_test_plate_40.png)
- Studio 1D FFT, enlarged: [`logs/studio_postproc_test_plate_40_1dfft.png`](logs/studio_postproc_test_plate_40_1dfft.png)

**Findings**
- ✅ **Full raw-data chain works** (radar → LVDS → DCA → Ethernet → `adc_data.bin`). First real data for
  `dca_process.py`: its peak matches Studio's within one bin, so lane order, I/Q format and range scale are right.
- ✅ Second peak at about twice the plate range is the plate–radar–plate double bounce; ~8 cm peak is TX–RX leakage.
- **RX bins 11/12 split:** plate sits between two bins with near-equal levels. Not a fault; the script's warning is
  stricter than needed.
- **Range offset:** reads 46–49 cm for ~40 cm. Not yet known if fixed; E1 (40 → 60 cm) checks it. Distance was not
  measured carefully (hand-placed).
- **Large ADC headroom at bo18** (max 181 counts, ~−45 to −55 dBFS). Hints that the on-chip "saturation" (Sessions
  2–3) was in the demo's processing, not the ADC. **One capture; not a finding yet.** E4 tests it.
- Room clutter at ~1.5–2.5 m and ~5.7 m (Studio range-Doppler): outside the 40–60 cm test region.

**Empty-scene check: `E0_empty_20f`** (plate removed, radar not moved; 20 frames, so not the full 100-frame E0).
Note: a wall runs along the left side of the setup, ~50–90 cm away.

| Check | Result |
|---|---|
| Packets / `complete` / `clip_pct` | 1688, 0 lost / True / 0 ✅ |
| `max_adc` | 110 (leakage + room only) |
| Level at plate bins 11–12 (45–49 cm) | **−4.4 / −3.9 dB**, at the noise floor; plate was 33.8 / 34.3 → **38 dB below the plate** |
| Static background at plate bins (coherent, RX1) | **−69 to −70 dB** relative to the plate |
| Strongest echo in 25–150 cm | 8.3 dB at 147 cm (room object) |
| 0–16 cm (TX–RX leakage) | identical with and without plate (within 0.4 dB) |

Figures: [`logs/dca_plate_vs_empty.png`](logs/dca_plate_vs_empty.png) (overlay, 40–60 cm shaded),
[`logs/dca_E0_empty_20f.png`](logs/dca_E0_empty_20f.png),
Studio PostProc ("No detected points"): [`logs/studio_postproc_E0_empty_20f.png`](logs/studio_postproc_E0_empty_20f.png).

- ✅ **The side wall is not visible** in the 40–100 cm bins. Background at the plate position is ~38 dB below the plate,
  so it changes plate readings by < 0.1 dB. Background subtraction not needed for metal; may still help for weak sheets.
- Phase/level numbers for this capture are meaningless (no target; peak picked on room clutter at 147 cm).
- **Repeat `E0_empty`** (19:46, correct path, but still **20 frames**, not 100): 1688 packets, 0 lost, `complete` True,
  `max_adc` 107. 40–60 cm level −4.4 … −3.3 dB, same as run 1 within 0.4 dB; strongest echo again 8.3 dB at 147 cm.
  Figures: [`logs/dca_E0_empty.png`](logs/dca_E0_empty.png), [`logs/studio_postproc_E0_empty.png`](logs/studio_postproc_E0_empty.png).
  The 100-frame stream test moves to E1 (100-frame captures).
- This capture overwrote `C:\dca\test_plate_40` (path not changed in Studio). The plate data was already backed
  up to `data/dca/test_plate_40` at 19:36; verified the two files differ.

**E1: plate at 40 cm: `E1_plate_40`** (aluminium plate, front face **40.0 cm** from the antenna face, measured)
- Aligned with 4 × 20-frame captures (`E1_align`, using `watch_peak.py`): best 34.7 dB (hand-placed test: 34.3).
- Then 100 frames, plate untouched.

| Check | Result |
|---|---|
| Packets / `complete` / `clip_pct` | 8440, 0 zero-filled / True / 0 ✅ (100-frame stream OK; file 12,288,000 B) |
| `max_adc` | 167 |
| Peak | 34.7 dB, bin 12 (49.0 cm); interpolated **47.3 cm** → reads **+7.3 cm** long |
| RX bins | 12 12 12 11 (between bins, fine) |
| Stability (10 s) | level std 0.02 dB; phase std 0.20° (1.1 µm), range 1.3° |

Figure: [`logs/dca_E1_plate_40.png`](logs/dca_E1_plate_40.png).

**E1: plate at 60 cm: `E1_plate_60`** (front face **60.0 cm**, re-aligned with 4 × 20-frame tries, saved as
`data/dca/E1_align60`; then 100 frames)

| Check | 40 cm | 60 cm |
|---|---|---|
| Packets / `complete` / clip | 8440 / True / 0 | 8440 / True / 0 ✅ |
| `max_adc` | 167 | 162 |
| Peak range (interpolated) | 47.3 cm | **67.2 cm** |
| Offset vs tape | +7.3 cm | **+7.2 cm** |
| Peak level | 34.70 dB | **34.59 dB** (−0.11) |
| RX bins | 12 12 12 11 | 16 17 16 16 |
| Phase std / range (10 s) | 0.20° / 1.3° | 0.97° (5.1 µm) / 9.4° |

Figures: [`logs/dca_E1_40_vs_60.png`](logs/dca_E1_40_vs_60.png) (both + empty, dotted = tape distance),
[`logs/dca_E1_plate_60.png`](logs/dca_E1_plate_60.png).

**Findings**
- ✅ **E1 passes.** Peak moved **19.9 cm** for 20.0 cm. The **+7.2 cm offset is fixed** (internal delay); range scale is
  correct. No effect on comparisons at the same position.
- **Level barely changes with distance (−0.1 dB for 40 → 60 cm), with no clipping.** A large plate (mirror) should lose
  ~3.1 dB (1/R²). Likely cause: the chip's IF **high-pass filters** (175 + 350 kHz). Near targets have a low IF
  (221 kHz at 47 cm, 314 kHz at 67 cm) and are cut more. Ideal first-order filters predict −0.2 dB total: matches.
  - This is a **hypothesis from one pair of distances**, not tested.
  - It also gives a non-saturation explanation for the flat on-chip readings in Session 2 (filters predict −2.3 dB
    from 40 to 120 cm). E4 (back-off steps at one position) tests linearity directly.
  - **For E5:** compare samples only at the same distance. Then the filter effect cancels.
- Phase is noisier at 60 cm (0.97°) but still well under E2's 10° target.

**E2: stability: `E2_still`** (plate moved back from 60 to 40 cm and re-aligned; 600 frames = 60 s, nobody touching)

| Check | Result |
|---|---|
| Packets / `complete` / clip | 50638, 0 zero-filled / True / 0 ✅ (60 s stream OK; 73,728,000 B) |
| Peak | 34.43 dB at bin 12 (E1 at 40 cm: 34.70) |
| Level std | 0.028 dB |
| Phase std | **0.18° (0.9 µm)**, range 0.99° ✅ (target < 10°) |
| Slow drift | 0.006°/s = 0.36° over 60 s (≈ 1.8 µm/min, likely thermal); detrended std 0.15° |
| Per 10 s block | std 0.13–0.17° in every block |

Figure: [`logs/dca_E2_still.png`](logs/dca_E2_still.png).
- ✅ **E2 passes by a factor of ~50.** Phase is stable to under 1 µm over a minute, so E3's 1 mm move (~185° expected)
  will stand far above noise.
- Re-placing the plate at 40 cm (after the 60 cm test) changed the level by **−0.27 dB** vs E1. One re-placement only;
  E5's 5 repeats per sample measure this properly.

**E3: move the plate ~1 mm: `E3_before` → `E3_after`** (100 frames each, no reconfiguration in between; plate moved
~1 mm **towards** the radar by hand against a ruler, by eye, no spacer)

| Check | Result |
|---|---|
| Both captures | 8440 packets, 0 lost, `complete` True, no clipping |
| Phase change per RX | **−175.7, −177.6, −170.8, −168.5°** (spread 9.1°) |
| Expected for 1.0 mm | 190.2° (λ = 3.785 mm) → wraps to ±169.8° |
| Implied move | **0.91 mm towards** the radar (if phase = +4πR/λ, TI's convention; not verified here). Other sign → 0.98 mm away |
| Interpolated peak range | 471.8 → 470.7 mm (−1.1 mm; consistent, but too coarse alone) |
| Level | 34.47 → **36.02 dB (+1.55 dB)** |
| Phase noise | 0.17° before, 0.44° after |

Figures: [`logs/dca_E3_before.png`](logs/dca_E3_before.png), [`logs/dca_E3_after.png`](logs/dca_E3_after.png).
- ✅ **E3 passes:** all 4 RX agree within 9° (target 20°). The size matches a by-eye ~1 mm move (0.91 mm).
  Phase tracks sub-mm motion, so E5's `path` (delay through a sheet) is usable.
- Not a precise scale check: no spacer, so the true move is known only to ~±0.3 mm.
- **The hand move changed the level by +1.55 dB**, probably a slight tilt. Placement angle matters more than
  distance, so E5 needs a fixed stop and careful re-placement.
- PostProc showed its `calc_rel_offset_and_file_name` error for both captures, but the data were complete.

**E4: TX back-off 0 / 6 / 12 / 18 dB: `E4_bo*`** (plate untouched since `E3_after`; 100 frames each. bo18 = setup
script's config, captured first; 0/6/12 set with `studio_set_backoff.lua`; back-off confirmed in each capture's
`adc_data_LogFile.txt` ProfileConfig line. `E4_bo18end` = bo18 again, set by the script, captured last.)

| Back-off | `max_adc` | Peak | Step | Far-range floor | Peak − floor | Phase std |
|---|---|---|---|---|---|---|
| 0 dB | 5022 | 64.43 dB | | 18.67 | 45.8 | 0.06° |
| 6 dB | 2207 | 57.78 dB | −6.65 | 12.45 | 45.3 | 0.18° |
| 12 dB | 1049 | 51.32 dB | −6.46 | 6.96 | 44.4 | 0.09° |
| 18 dB | 196 | 36.02 dB | **−15.30** | −0.06 | 36.1 | 0.14° |
| 18 dB (end, via script) | 203 | 36.03 dB | +0.01 vs first bo18 | −0.09 | 36.1 | 0.12° |

No clipping anywhere (`clip_pct` 0; bo0 max 5022 of 32767 ≈ −16 dBFS). Plot:
[`logs/dca_E4_backoff.png`](logs/dca_E4_backoff.png).

**Findings**
- ✅ **Raw data is linear from bo0 to bo12:** −6.65 and −6.46 dB for 6 dB steps (fit −1.09 dB per dB). Both peak and
  max ADC agree.
- ❗ **bo12 → bo18 drops 15.3 dB, not 6.** bo18 sits **8.7 dB below** the bo0–12 line. So at back-off 18 the TX puts
  out ~9 dB less than its setting says. Raw ADC levels confirm it (−14.6 dB), so it's the TX, not our processing.
  - **Not a setup-order effect:** bo18 set later by the script (`E4_bo18end`) reads 36.03 dB, same as bo18 from RF Init
    (36.02). So the chip's output really is ~9 dB lower at code 18. Likely outside the calibrated back-off range
    (not checked against TI's datasheet).
  - The same reading 11 min apart (+0.01 dB) also shows **no drift** over the whole E4 run.
- **Session 3's on-chip result (7.2 dB drop for 18 dB back-off) was compression in the demo's on-chip processing.**
  The raw ADC drops 28.4 dB over the same change. So on-chip dB values are not linear.
- The far-range "floor" rises and falls with TX power, so above bo18 it's TX-related clutter or leakage, not thermal noise.
  Peak-to-floor is ~45 dB at bo0–12, but only 36 dB at bo18.
- **For E5:** use **bo6** (linear, 22 dB clipping headroom on metal, same peak-to-floor as bo0). Avoid bo18.

**E5 Part 1 (reflection), round 1: `E5_r_*_1`** (bo6, front faces against a taped stop at 40 cm, aligned on `alu`,
sheets held at the base only, acrylic film peeled both sides. Thickness nominal (not measured): 3 mm; **`glass6` = 6 mm,
`acrylic6` = 7 mm** (name kept for consistency). `alu_1` has 100 frames, others 20. All 1688/8440 packets, 0 lost, no clipping.)

| Sample | Level vs `alu` (band avg) | Across band (78–80.4 GHz) | Slab model (assumed εr, nominal t) |
|---|---|---|---|
| `alu` | 0 (57.45 dB peak, max ADC 2484) | | |
| `alurot` | **−2.78** | −3.0 … −2.2 | 0 (size check) |
| `glass3` | **−13.39** | −16.8 … −11.7 | −13.6 (εr 6.5) |
| `glass6` (6 mm) | −8.40 | −9.3 … −8.1 | −9.8 |
| `acrylic3` | **−7.16** | −7.8 … −6.8 | −7.4 (εr 2.6) |
| `acrylic6` (7 mm) | **−25.37** | −28.5 … −22.8 | −16.6 (near a null: model swings 18 dB across the band, very sensitive to εr and t) |
| `epoxy3` | **−5.94** | −7.2 … −4.8 | −6.0 (εr 4.4) |

**First look (one round, no repeats yet: not findings)**
- 3 mm sheets land within 0.3 dB of the slab model with textbook εr. Same thickness, three clearly different levels:
  glass −13.4, acrylic −7.2, epoxy −5.9. **Glass vs acrylic at 3 mm differ by 6.2 dB.** That is the opposite of the
  old on-chip "glass ≈ plastic" (on-chip dB was compressed, E4).
- Thickness changes the order: thick glass (−8.4) reflects *more* than 3 mm glass, thick acrylic (−25.4) far less
  than 3 mm acrylic. Fits the thin-sheet picture; reflection is a material + thickness property.
- ❗ **`alurot` is −2.8 dB**, not ~0. Either rotating the plate (23 vs 40 cm across the beam) matters, or this one
  re-placement was tilted. Rounds 2–5 will tell. If it stays, sample size/shape affects levels at the ~3 dB scale.
- `acrylic6` is weak (−25 dB), so static background (stop, base, room) may bias it by ~1–2 dB. Proposed: a no-sample
  capture (`E5_r_none_n`) in each later round to measure that floor.

**E5 Part 1, all 5 rounds** (35 captures, 21:29–22:22; same setup; order per round alu, alurot, acrylic3, glass3,
epoxy3, acrylic6, glass6 (round 4: alurot before alu). All `complete`, no clipping. `acrylic3_4`: its packet log
says 0 packets (a second ARM after the capture overwrote the log), but the file is full size and reads in line with
the other rounds, so kept. No `none` captures taken. Output: `logs/dca_materials.csv`, `logs/dca_material_pairs.csv`.)

| Sample | Rounds 1–5 (dB vs mean `alu`) | Mean ± sd | In-band swing (mean curve) |
|---|---|---|---|
| `alu` | −0.74, 0.39, −0.19, 0.80, −0.45 | **0.0 ± 0.6** | 0.0 |
| `alurot` | −3.52, −0.42, −0.14, −0.68, −3.75 | −1.7 ± 1.8 (two groups: ~−0.4 and ~−3.6) | 0.4 |
| `glass3` | −14.11, −13.51, −8.89, −12.53, −10.43 | **−11.9 ± 2.2** | **5.7** (rises 15 → 10 dB across band) |
| `glass6` (6 mm) | −9.19, −7.73, −6.62, −7.52, −8.82 | −8.0 ± 1.0 | 1.7 |
| `acrylic3` | −7.92, −3.87, −8.01, −6.89, −7.03 | **−6.7 ± 1.7** | 1.0 |
| `acrylic6` (7 mm) | −26.08, −22.38, −15.40, −22.48, −23.22 | −21.9 ± 3.9 | 3.8 |
| `epoxy3` | −6.69, −4.05, −7.54, −8.07, −7.16 | **−6.7 ± 1.6** | 1.4 |

Pair tests (`separation` = mean difference / larger single-capture sd, ≥ 3 = one capture tells them apart;
Welch p = are the means different; shape = `curve` metric after removing each curve's own mean, **post-hoc**, added
after seeing the data):

| Pair | Mean diff | `separation` (level) | Welch p | Shape sep |
|---|---|---|---|---|
| `alu` vs `alurot` (control) | 1.7 dB | 0.9 not separable ✅ | 0.11 | 0.6 |
| `glass3` vs `acrylic3` | **5.2 dB** | 2.4 no | **0.004** | **3.4 yes** |
| `glass3` vs `epoxy3` | 5.2 dB | 2.4 no | 0.003 | **6.5 yes** |
| `acrylic3` vs `epoxy3` | 0.0 dB | 0.0 no | 0.97 | 1.7 no |
| `glass3` vs `glass6` | 3.9 dB | 1.8 no | 0.012 | **7.0 yes** |
| `acrylic3` vs `acrylic6` | 15.2 dB | **3.9 yes** | 0.0004 | 0.4 |
| `glass6` vs `acrylic6` | 13.9 dB | **3.5 yes** | 0.0009 | 0.6 |

Figure: [`logs/dca_E5_summary.png`](logs/dca_E5_summary.png) (left: every capture + mean ± sd; right: mean curves
across the band ± sd). Script plot: [`logs/dca_materials.png`](logs/dca_materials.png).

**Findings**
- ✅ **Glass and acrylic of the same 3 mm thickness reflect differently: 5.2 dB apart on average (p = 0.004, 5 vs 5
  re-placements).** The old "glass ≈ plastic" is not supported by raw data. The on-chip result came from compressed
  dB (E4).
- ⚠️ **One capture's level alone can't tell them apart** (separation 2.4 < 3). Re-placing a sheet moves its level by
  1–2 dB sd (aluminium: 0.6 dB). Sheets are held only at the base, so tilt between placements is the likely cause.
- **The frequency shape does tell 3 mm glass apart** from acrylic and epoxy in single captures: glass rises ~5–6 dB
  across 78–80.4 GHz in every round; acrylic and epoxy are nearly flat. Tilt shifts level, not shape. Physically
  expected (glass has high εr, so a 3 mm sheet is far from a half-wave). **Post-hoc metric**: confirm on new data
  before relying on it.
- **Acrylic 3 mm and epoxy glass 3 mm are indistinguishable** here (−6.7 vs −6.7 dB, similar shape).
- **Thickness matters as much as material:** 6 mm glass reflects more than 3 mm glass; 7 mm acrylic is ~15 dB weaker
  than 3 mm acrylic. Per-part materials in simulation need thickness, not just a material name.
- Control `alu` vs `alurot` passes (not separable), but `alurot` falls into two groups (~−0.4 and ~−3.6 dB).
  Likely two placement states (rotated plate, cut corner), not a size effect. Treat ±2 dB as the placement
  uncertainty for non-aluminium samples.
- Slab model with textbook εr: matches the 3 mm means within ~1–2 dB (glass −13.6 vs −11.9; acrylic −7.4 vs −6.7;
  epoxy −6.0 vs −6.7). Misses 7 mm acrylic (−16.6 vs −21.9; it sits near a null, so it's very sensitive). Not fitted yet.
- Thickness not measured with calipers (nominal values).

---

## Photos

| Photo | File | Notes |
|---|---|---|
| Stencil used in session 1 | `~/Downloads/PXL_20261030_215226771.jpg` | |
| Setup: radar + aluminium plate at 40 cm | | |
| Radar close-up | | |
| Sheets (glass, plastic, aluminium) | | |
| Visualizer range profile screenshot | | |

---

## Open items
- [ ] Session 3 (back-off) → pick the operating config
- [ ] Re-check linearity at the chosen config (short distance series or back-off steps)
- [x] Experiment A at 0° (Session 4); [ ] rotation sweep (needs turntable + same-size metal reference)
- [x] Experiment B: aluminium plate at 60 cm behind each sheet at 40 cm (Session 5)
- [ ] Identify the opaque plastic (marking or source)
- [x] DCA1000 raw capture working (Session 6)
- [ ] DCA: E0–E4, then E5 (new samples: glass, acrylic, epoxy glass 3 mm; glass + acrylic ~6–7 mm; calipers)
- [ ] DCA range offset (46–49 cm read for ~40 cm): check with E1 at 60 cm
- [ ] Back up `hardware/` (not under version control)
