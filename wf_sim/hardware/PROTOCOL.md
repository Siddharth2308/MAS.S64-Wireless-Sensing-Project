# IWR1443BOOST ground-truth tests for the simulator

We only have the IWR1443BOOST (no DCA1000 capture board), so no raw ADC data
and no SAR imaging. The out-of-box demo still streams a **range profile**
(received power vs distance) over USB. That is enough to test the physics our
simulator assumes:

| # | Hypothesis (simulator assumption) | Experiment |
|---|---|---|
| H1 | Materials reflect in the order metal > glass > PET > PP, at roughly the predicted levels | A: plate at 0° |
| H2 | All materials have the **same angular falloff, shifted down by R0**; this is the only reason their cutoff angles differ | A: angle sweep |
| H3 | Dielectric sheets pass the radar with a few dB of loss; metal blocks | B: transmission |

What we **cannot** test without the capture board: SAR images, 3D partial
point clouds, mmNorm normals, running Wave-Former on real data.

---

## 0. Gear checklist

- [ ] IWR1443BOOST + **5 V / ≥2.5 A barrel-jack supply** (USB alone is not enough) + micro-USB cable
- [ ] Flat sheets, **all cut to the same size** (e.g. 15 × 15 cm):
  - metal: aluminium/steel sheet, or kitchen foil glued *smooth* onto stiff cardboard (foil side to radar)
  - glass: picture-frame pane
  - PET or acrylic sheet (write down which; acrylic is not in our table)
  - PP: cutting board or PP sheet
- [ ] For experiment B: one **larger** dielectric sheet of each type (≥ 25 × 25 cm), and a small metal plate (≈ 10 × 10 cm)
- [ ] Calipers or a ruler for **sheet thickness** (this matters a lot, see §5)
- [ ] Rotating stand (lazy susan, or a cardboard disc on a pin) + **printed protractor** taped under it
- [ ] Clips or a slot to hold sheets upright, so every sheet sits in the same place
- [ ] Tape measure, phone for photos

## 1. One-time setup (≈ 1 h the first time)

1. **Flash the out-of-box demo** (`xwr14xx_mmw_demo.bin` from the TI mmWave SDK) with TI UniFlash.
   SOP jumpers select flashing vs running. Per the EVM user guide this is usually *flash = SOP0 + SOP2 fitted*,
   *run = SOP0 only*, but **check the guide for your board revision**. Power-cycle after changing jumpers.
2. Open the **TI mmWave Demo Visualizer** (dev.ti.com, needs TI Cloud Agent), connect, and choose:
   - best range resolution, max range ≈ 2–5 m, frame rate ≈ 10 fps
   - plots: enable **range profile**
   - **disable clutter / static removal** if offered (it would remove our static plate)
3. Check that a metal plate at 40 cm shows a clear peak in the range-profile plot.
4. **Save config to PC** and save it as `wf_sim/hardware/iwr1443_range_profile.cfg`.
5. **Close the Visualizer**, because only one program can use the serial ports at a time.

## 2. Sanity checks with our logger (10 min)

From `Project/wf_sim`:

```bash
source .venv/bin/activate && unset PYTHONPATH     # PYTHONPATH from ROS breaks the venv
ls /dev/ttyACM*                                   # expect two ports: ACM0 = config, ACM1 = data
python -m hardware.iwr_logger live                # prints the peak each frame
```

- [ ] Metal plate at 40 cm: peak at ≈ 40 cm (a few cm offset is normal; note it).
- [ ] Move the plate to 30 / 50 cm: the peak follows.
- [ ] Remove the plate: the peak drops by **≥ 20 dB** (otherwise there is clutter: clear the area behind).
- [ ] The dB value roughly matches the Visualizer's range-profile plot (checks our dB scaling; if it is
      consistently off by a factor, tell Claude and we fix `RANGE_PROFILE_Q` in `tlv.py`).

If the ports differ: `--cli /dev/ttyACMx --data /dev/ttyACMy`. If the peak is outside 25–60 cm, use `--rmin/--rmax`.

## 3. Experiment A: reflectivity and angular falloff (≈ 45 min)

```
   radar (boresight horizontal)            sheet on rotating stand
   ┌──────┐                                   │  ← rotation axis vertical,
   │ IWR  │ ───────────── 40 cm ───────────── │    through the sheet's front face
   └──────┘                                   │    sheet centre at radar height
                                   nothing else within ~1.5 m behind the sheet
```

1. Radar on a box, boresight horizontal, pointing into open space. Sheet centre at the radar's height, 40 cm away
   (antenna face to sheet front).
2. **Find 0°** with the metal sheet: run `live`, rotate in small steps, and stop where the peak is highest.
   Mark that as 0° on the protractor. Keep the stand fixed from now on.
3. Record the empty scene once:
   `python -m hardware.iwr_logger record --exp A --material empty`
4. For each material (metal, glass, PET/acrylic, PP), mounted in the **same holder position**:
   - re-check 0° with `live` (should be within ±1°)
   - record angles **0, 2, 4, … 30°** (always rotate the same direction):
     ```bash
     python -m hardware.iwr_logger record --exp A --material glass --angle 0 --thickness 2.1
     python -m hardware.iwr_logger record --exp A --material glass --angle 2 --thickness 2.1
     ...
     ```
   - metal only: also record **−2° and −4°** (symmetry check)
5. Record **metal at 0° again at the very end** (drift check; it will save as `_rep2`).
6. Keep your hands and body out of the beam while it records (≈ 5 s per angle).

Optional shell loop for one material (press Enter after each rotation):
```bash
for a in $(seq 0 2 30); do read -p "set ${a} deg, Enter"; \
  python -m hardware.iwr_logger record --exp A --material glass --angle $a --thickness 2.1; done
```

## 4. Experiment B: transmission (≈ 20 min)

```
   ┌──────┐            large sheet            small metal plate
   │ IWR  │ ── 40 cm ──── ║ ─────── 20 cm ───────── ▌
   └──────┘                                       (60 cm from radar, facing it)
```

All perpendicular to the beam, centred at radar height. Use `--rmin 0.5 --rmax 0.7` so the peak search looks at
the **metal plate**, not the sheet.

For each dielectric sheet (glass, PET/acrylic, PP), plus a metal sheet as the blocking case:

```bash
python -m hardware.iwr_logger --rmin 0.5 --rmax 0.7 record --exp B --material none  --label plate_only
python -m hardware.iwr_logger --rmin 0.5 --rmax 0.7 record --exp B --material glass --label plate_plus_sheet --thickness 2.1
python -m hardware.iwr_logger --rmin 0.5 --rmax 0.7 record --exp B --material glass --label sheet_only --thickness 2.1
```

- Repeat `plate_plus_sheet` **3 times, taking the sheet out and putting it back each time** (repeatability).
- Record `plate_only` again at the end of each material (drift).
- Loss = peak(plate + sheet) − peak(plate only), at the plate's distance.

## 5. What the model predicts

**Thick material (what the simulator uses now):**

| Material | R0 vs metal | Cutoff (lobe 8°, −20 dB) | Two-way loss through a sheet (2 surfaces, no absorption) |
|---|---|---|---|
| metal | 0 dB | 17.2° | blocks |
| glass (ε = 6) | −7.5 dB | 13.6° | −3.4 dB |
| PET (ε = 3) | −11.4 dB | 11.2° | −1.3 dB |
| PP (ε = 2.3) | −13.8 dB | 9.6° | −0.8 dB |

**Thin sheets behave differently.** Reflections from the sheet's front and back surfaces interfere, so the level
depends on thickness (averaged over 77–81 GHz):

| Sheet | Reflectivity vs metal | Two-way transmission |
|---|---|---|
| glass 2 mm | −3.1 dB | −5.9 dB |
| glass 3 mm | −8.3 dB | −1.4 dB |
| PET 0.5 mm | −6.1 dB | −2.5 dB |
| PET 1 mm | −16.1 dB | −0.2 dB |
| PP 2 mm | −8.5 dB | −1.3 dB |
| PP 5 mm | −22.2 dB | −0.05 dB |

So **measure every sheet's thickness**. The analysis compares the data to both models using your measured
thickness. Real absorption in glass will make the measured loss larger than predicted.

**H2 check:** if the angle curves for all materials have the same shape and differ only by a vertical offset,
the simulator's "cutoff differs only through R0" assumption holds. The *absolute* width of the falloff also
depends on sheet size and distance, so it is not a material constant. That's why all sheets must be the same size.

## 6. Log sheet (fill in)

| Item | Value |
|---|---|
| Date / place | |
| Radar–sheet distance (A) | 40 cm |
| Sheet size (A) | |
| Metal type (sheet / foil) | |
| Glass thickness (mm) | |
| PET or acrylic? thickness (mm) | |
| PP thickness (mm) | |
| Measured 0° offset / peak range offset | |
| Anything odd (reflections, wobble) | |

## 7. Photos for the report

- [ ] Whole setup (radar, stand, protractor, distance visible)
- [ ] Radar close-up (show it is the IWR1443BOOST)
- [ ] The sheets side by side
- [ ] Experiment B arrangement
- [ ] Screenshot of the Visualizer range profile with the plate peak

## 8. Troubleshooting

| Symptom | Fix |
|---|---|
| `Permission denied: /dev/ttyACM0` | you are in `dialout` already; replug the board, or log out and back in |
| `cfg line failed` | press the board's NRST button, check the jumpers are in run mode, retry |
| `clutterRemoval is enabled` | edit the cfg: set the last number on that line to 0 |
| `no packets for 5 s` | swap `--cli`/`--data`; make sure the cfg ends with `sensorStart` |
| `packet without range profile` | re-export the cfg with the range-profile plot enabled |
| Peak jumps around | something moving in the beam, or the sheet is wobbling; clamp it |

Then send the `hardware/data/` folder (or just tell Claude it's there) and we'll generate the sim-vs-measured plots.
