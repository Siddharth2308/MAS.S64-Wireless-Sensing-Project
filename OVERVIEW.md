# Project overview

**Status: Nov 20, 2026.** MAS.S64, Siddharth Kulkarni and Ivan Wren.

## The idea
- Wave-Former completes 3D object shapes from mmWave radar. It trains only on synthetic partial point clouds.
- We ask whether that synthetic data misses something that matters on real objects:
  - **Proposal A:** objects with several materials, such as a glass jar with a metal lid.
  - **Proposal B:** objects that aren't upright.
- **Staff feedback:** graded A. They called "glass ≈ plastic" problematic, and said Proposal A is about reflectivity, not transmission.
- **Their suggested plan:** analyse Wave-Former on multi-material objects, label materials, test flat surfaces of 2 materials, then proceed (possibly with Nazish). Our response: `Feedback Response & Plan.pdf`.
- **Split:** Siddharth on hardware, Ivan on ML and simulation.
- We have no Wave-Former code or checkpoint.
- All simulation below uses `wf_sim`, **our simplified model, not Wave-Former's simulator**.

## What we observed

### Raw radar captures (DCA1000, Nov 19)
| Test | Result | What it means |
|---|---|---|
| E0: empty scene | Background at the plate position is 38 dB below the plate | The side wall doesn't matter |
| E1: plate at 40 vs 60 cm | Range offset +7.2 cm (constant); level nearly flat | Likely the chip's IF high-pass filters (hypothesis), not saturation |
| E2: 60 s still | Phase sd 0.18° (0.9 µm) | Stable enough for SAR |
| E3: move plate ~1 mm | Phase moves as expected (0.91 mm) | Phase tracks real motion |
| E4: TX back-off 0-18 dB | Linear for 0-12 dB (-6.5 dB per 6 dB); bo18 ~9 dB low | On-chip demo compressed dB. Use bo6. |
| E5: reflection vs aluminium, 5 re-placements | 3 mm glass -11.9 ± 2.2, 3 mm acrylic -6.7 ± 1.7, 3 mm epoxy glass -6.7 ± 1.6, 6 mm glass -8.0 ± 1.0, 7 mm acrylic -21.9 ± 3.9 dB | Glass ≠ acrylic at 3 mm (5.2 dB, p = 0.004), but one capture's level can't tell them apart; frequency shape can (post-hoc). Thickness matters as much as material. |

Details: `wf_sim/hardware/MEASUREMENT_LOG.md` Session 6.

### Radar measurements (IWR1443BOOST, on-chip range profile, earlier)
| Test | Result | What it means |
|---|---|---|
| Reflection vs aluminium | 3 mm plastic -9.0 dB, 4 mm glass -8.7 dB | Superseded by E5: the on-chip dB was compressed (E4) |
| Two-way transmission | Plastic -2.8 dB, glass -5.6 dB. Simulator assumed -1.0 / -3.4 dB. | Both pass much of the signal, but lose more than we modelled. A thin-sheet model with small absorption gives -3.1 / -5.9 dB. |
| Metal plate from 40 to 120 cm | About 139 dB at every distance | The receiver saturates at full power. |
| 18 dB TX back-off | Readings fell only about 7 dB | The absolute dB scale is uncalibrated. |

### Simulation
| Test | Result | What it means |
|---|---|---|
| Tilt up to 30° | Visible area barely changes (bleach 3.6-6.5%), but overlap with the upright view falls to 39% (bleach, mustard). | The network gets a similar amount of input, but from a different part of the object. |
| Tilt up to 90° | Visible area rises when lying down: mustard 6 to 29%, bleach 4 to 28%. | Upright is close to the worst case for tall objects. |
| Yaw only | Barely matters | A turntable alone would show little, so we need tilt. |
| Glass jar on its side | Per-part cutoffs change the lid only 6.6 to 7.3%. Transmission doubles the visible body, 10.4 to 20.2%, and stays there with the measured glass loss. | Whether a part blocks or passes the signal matters more than its cutoff angle. |

Also, 102 of about 136 real MITO capture poses are upright, so real-world testing rarely covers tilted objects.

## How far to trust this
- **Biggest gap:** nothing yet shows these input changes hurt reconstruction.
- **dB values:** the values vs metal could change once the scale is calibrated.
- **E5 placement noise:** re-placing a sheet moves its level by 1-2 dB sd (aluminium 0.6 dB). Treat ±2 dB as the uncertainty.
- **E5 thicknesses:** nominal, not measured with calipers. Only straight-on, one distance, relative to aluminium.
- **Thin-sheet model:** within 1-2 dB of the 3 mm means with textbook εr, but misses 7 mm acrylic (-16.6 vs -21.9 dB, near a null). Not fitted.
- **Material labels:** from photos; wall thickness estimated.
- **Metal blocking:** assumed in the simulator, not measured.
- **Coverage percentages:** our cutoffs (10-17°) are looser than MITO's 5°, so trust the trends, not the exact values.
- **Samples:** one sheet per material, at one angle. The plastic's identity is unconfirmed.

## What we're doing next
| Step | Why | Status |
|---|---|---|
| **E0-E4:** raw capture checks with the DCA1000 | Data correct, phase stable, dB scale | **Done** (Nov 19) |
| **E5 Part 1:** repeated reflection captures | Tell materials apart, repeatability | **Done** (Nov 19). Part 2 (transmission) skipped; calipers not done |
| **YCB material labels** | Per-part materials for the 72 YCB objects in mmRender | **Done** (Nov 20): `wf_sim/materials/` |
| **mmRender material term (Ivan)** | Per-point reflectivity from labels; compare rendered vs real (MITO) images | Planned. Needs `material_reflectivity.csv` |
| **2-material flat surfaces** | Plastic in front of metal, as staff suggested | Not started |
| **Multi-material analysis (Ivan)** | Do multi-material objects reconstruct worse in Wave-Former? | Not started |
| **Get reconstruction numbers** | Close the biggest gap. Ask staff for the Wave-Former checkpoint, otherwise train a small PoinTr baseline. | Not started |
| **SAR imaging:** MITO's sample raw data, then real objects | Compare real partial views with simulation (bottle upright vs tilted, lidded jar) | Later, needs a scanner |

**What E5 means for Proposal A:**
- Materials separate on average, but thickness changes reflection as much as material does. So per-part simulation needs material **and** thickness, not a material name alone.
- Acrylic and epoxy glass look the same; glass differs (level and frequency shape).

## Deadlines
- **Nov 20:** presentation / Progress Report 2
- **Dec 7:** final presentation

## More detail
- Measurements: `wf_sim/hardware/MEASUREMENT_LOG.md`
- Experiment steps: `experiment.md`
- Figures: `wf_sim/figures_guide.md`
- Setup: `README.md`
