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
- [ ] Back up `hardware/` (not under version control)
