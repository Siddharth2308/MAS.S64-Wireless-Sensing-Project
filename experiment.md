# DCA1000 experiments

## Files to run
| What | Where |
|---|---|
| Capture | TI mmWave Studio (Windows) |
| Process one capture | `python -m hardware.dca_process summary <bin> --label <name>` |
| Phase change between two captures | `python -m hardware.dca_process shift <before.bin> <after.bin> --moved-mm 1` |
| Compare materials (E5) | `python -m hardware.dca_process materials C:\dca` |
| Results | `hardware/logs/dca_summary.csv`, `dca_<label>.png`, `dca_materials.csv`, `dca_material_pairs.csv`, `dca_materials.png` |
| Windows problems | `debug.md` |

Run commands in PowerShell from `Project\wf_sim`, after `.venv-win\Scripts\activate` (first-time setup: `context.md`).

## Setup
- **IWR1443BOOST:** on its stand at the table edge, antenna facing along the tape measure, boresight horizontal.
- **DCA1000:** connected to the IWR by the 60-pin ribbon cable, placed behind the radar.
- **Power:** 5 V; set the supply current limit to 2.5–3 A.
- **USB:** IWR XDS110 and DCA1000 FTDI to the PC. **Ethernet:** DCA1000 to the PC.
- **Jumpers:** photo first, then set Development mode: **SOP0 and SOP1 closed, SOP2 open** (board manual Table 5). Power-cycle after changing.
- **Aluminium plate (22.5 x 39 cm):** tall side up, centre at antenna height, on a non-metal support. Distance is antenna face to plate.
- **Clear space:** nothing else within 1.5 m in front. Stand behind the radar during captures.

## Studio settings (same chirp as our demo config)
**Use the script** `wf_sim\hardware\studio_setup_txbo18.lua`; it sets everything below (working since Nov 19).
1. Dev-mode jumpers, power on, NRST. Studio as administrator; 77 GHz + XWR14xx; refresh until Devices = 1.
2. Bottom left: Browse → the `.lua` → Run!. Wait for green "Setup done".
3. Frames per test: SensorConfig → Frame → No of Frames → Set (don't rerun the script).
4. Firewall rule for the DCA must exist once per PC (`debug.md`, Network).

| Setting | Value |
|---|---|
| Firmware | `xwr12xx_xwr14xx_radarss.bin`, `xwr12xx_xwr14xx_masterss.bin` |
| ADC | 16 bit, complex 1x; RX 1-4 on; TX1, TX3 on |
| LVDS | 4 lanes |
| Profile | start 77 GHz, idle 429 us, ADC start 7 us, ramp end **57.1** us (57.14 exceeds 81 GHz), slope 70 MHz/us, TX start 1 us |
| Samples | 240 at 4884 ksps; RX gain 30 dB; **TX back-off 18 dB** |
| Chirps | chirp 0 = TX1, chirp 1 = TX3 |
| Frame | chirps 0-1, 16 loops, period 100 ms; frames set per test |

**Order:** RS232 Connect → load firmware → SPI Connect → RF Power-up → StaticConfig → RF Init → DataConfig + Setup DCA1000 → SensorConfig (Profile, Chirp, Frame) → DCA1000 ARM → Trigger Frame → PostProc.

**Save each capture as:** `C:\dca\<label>\adc_data.bin`. Create it first (`mkdir C:\dca\<label>; New-Item C:\dca\<label>\adc_data.bin -ItemType File`), select it next to DCA1000 ARM, then ARM → 2 s → Trigger Frame → PostProc. Re-arm before every trigger.

## Tests

### E0: empty scene
1. Remove the plate. Frames = 100 (10 s).
2. Capture `E0_empty`, then run:
   `python -m hardware.dca_process summary C:\dca\E0_empty\adc_data.bin --label E0_empty`

**Pass:** `frames` = 100, `complete` = True, `clip_pct` = 0.

### E1: plate at 40 cm, then 60 cm
1. Plate at 40 cm. Frames = 20, path `C:\dca\E1_align\adc_data.bin`. In a second PowerShell, run `python -m hardware.watch_peak C:\dca\E1_align --rmax 0.8`. Then ARM → Trigger, read the printed peak, nudge the plate, repeat until it stops rising.
2. Frames = 100. Capture `E1_plate_40`, then run `summary`.
3. Move to 60 cm, re-align the same way, capture `E1_plate_60`, then run `summary`.
4. Note Studio's PostProc peak range for both.

**Pass:** peak moves about 20 cm; `clip_pct` = 0; `rx_peak_bins` all equal; Studio and our peak within one bin (4 cm).

**If `clip_pct` > 0:** lower RX gain, recapture, and note the new value.

### E2: stability
1. Plate at 40 cm, aligned. Don't touch the table.
2. Frames = 600 (60 s). Capture `E2_still`, then run `summary`.

**Pass (rough guide):** `phase_std_deg` under 10° (about 50 um).

### E3: move the plate 1 mm
**Don't redo RF Init or reconfigure between these two captures.** Only re-arm and trigger.
1. Plate at 40 cm against a straight edge. Frames = 100. Capture `E3_before`.
2. Slide it exactly 1 mm away along the beam, without tilting (caliper or feeler gauge as a spacer). Capture `E3_after`.
3. Run:
   `python -m hardware.dca_process shift C:\dca\E3_before\adc_data.bin C:\dca\E3_after\adc_data.bin --moved-mm 1`

**Pass:** all RX read about ±170° (190° wrapped). RX values agree within about 20°.

### E4: redo the power test
1. Plate at 40 cm, untouched. Frames = 100.
2. Capture at TX back-off 0, 6, 12, 18 dB: `E4_bo0`, `E4_bo6`, `E4_bo12`, `E4_bo18`. Run `summary` on each.

**Check:** `clip_pct` and `max_adc` at each setting. Without clipping, `peak_db` should drop 6 dB per step.

### E5: can we tell materials apart?
**Status (Nov 19):** Part 1 done (35 captures, 5 rounds). Part 2 skipped. Calipers not done. Results: `MEASUREMENT_LOG.md` Session 6.

**Run after E0-E3 pass** (passed Nov 19). **TX back-off 6** (E4: linear, no clipping; bo18 is ~9 dB low): after the setup script, run `studio_set_backoff.lua` with `BACKOFF = 6, NUM_FRAMES = 20`. Frames = 20 per capture. Don't redo RF Init or reconfigure during a part.

**Priority:** Part 1 (reflection) is the main test, because Proposal A is about reflectivity. Run Part 2 if time allows.

**Samples** (no underscores in names):

| Name | Sheet | Size | Thickness |
|---|---|---|---|
| `alu` | aluminium, cut corner away from centre | ~40 × 23 cm | 6 mm |
| `alurot` | same plate rotated 90° (size check: should match `alu` within ~0.5 dB) | | |
| `glass3`, `glass6` | glass | 30 × 30 cm / ? | 3 mm / ~6–7 mm |
| `acrylic3`, `acrylic6` | cast acrylic (likely) | ~40 × 35 cm / ? | 3 mm / ~6–7 mm |
| `epoxy3` | epoxy glass (check: no copper) | 30 × 30 cm | 3 mm |

- **Calipers:** measure each sheet at 4 points and log mean and spread. At these thicknesses 0.1 mm can shift reflection by several dB (slab model).
- Peel any film off the acrylic. Front faces at the same distance; sheets held from the bottom edge, 30 cm empty behind.
- Optional control: if the plate's two faces differ (finish/film), capture both (`alu` vs `aluback`).

**Part 1, reflection (front face at 40 cm)**
1. Tape a straight edge to the table as a fixed stop, and fix a non-metal support behind it.
2. Against the stop, adjust the support with `alu` until `peak_db` is highest. Then leave the support and stop in place.
3. Capture in this order, fully removing and re-placing each sample every time:
   `E5_r_alu_1`, `E5_r_alurot_1`, `E5_r_glass3_1`, `E5_r_glass6_1`, `E5_r_acrylic3_1`, `E5_r_acrylic6_1`, `E5_r_epoxy3_1`, then `_2` ... `_5`.

**Part 2, transmission**
1. `alu` at 60 cm, fixed. **Don't touch it again.**
2. Tape a fixed stop for the sheets at 40 cm, between the radar and the plate.
3. Capture in this order, fully removing and re-placing each sheet every time:
   `E5_t_none_1` (no sheet), `E5_t_glass3_1`, `E5_t_acrylic3_1`, `E5_t_epoxy3_1`, then `_2` ... `_5`.

**Process:**
`python -m hardware.dca_process materials C:\dca`

**Pass:** a pair counts as separable if `separation` is 3 or more (rough guide) on any of:
- `level`: average level
- `curve`: level across frequency
- `path`: delay through the sheet, transmission only

**Control:** `alu` vs `alurot` (and `aluback` if captured) should come out **not** separable. If they separate, re-placement isn't controlled well enough, so don't trust the other pairs yet.

**Next step:**
- Separated, even across thicknesses: measure per-part material values for the simulator.
- Separated only with known thickness: calibrate per sheet, and model thickness.
- Only metal vs non-metal: narrow Proposal A to "blocks vs passes".

**Limits:**
- Usable band is about 78-80.4 GHz, because the band edges are weak.
- `path` is a rough estimate: internal echoes bias it low. In simulation it read 4.9 mm vs an ideal 5.8 (glass) and 1.0 vs 1.8 (plastic). Use it to compare samples, not as an absolute value.

## After each session
- Copy `C:\dca` to `wf_sim\hardware\data\dca\`.
- Tell Claude "done". It reads `dca_summary.csv` and updates `hardware/MEASUREMENT_LOG.md`.
- Take setup photos for the report.
