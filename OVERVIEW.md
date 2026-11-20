# Project overview

**Status: Nov 12, 2026.** MAS.S64, Siddharth Kulkarni and Ivan Wren.

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

### Radar measurements (IWR1443BOOST, on-chip range profile)
| Test | Result | What it means |
|---|---|---|
| Reflection vs aluminium | 3 mm plastic -9.0 dB, 4 mm glass -8.7 dB. Thick-material model predicted -12.6 / -7.5 dB. | One sample each, no repeats, so this doesn't show they're the same. E5 tests it. |
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
- **Glass vs plastic:** the 0.3 dB gap is smaller than we can trust until we measure how repeatable re-placing a sheet is.
- **Thin-sheet model:** close to the one plastic reading, but that isn't a validation. For glass, the prediction swings about ±5 dB with permittivity.
- **Metal blocking:** assumed in the simulator, not measured.
- **Coverage percentages:** our cutoffs (10-17°) are looser than MITO's 5°, so trust the trends, not the exact values.
- **Samples:** one sheet per material, at one angle. The plastic's identity is unconfirmed.

## What we're doing next
| Step | Why | Status |
|---|---|---|
| **E0-E2:** raw capture checks with the DCA1000 | Confirm the data is correct and the phase is stable | Scripts ready, no captures yet |
| **E3:** move the plate 1 mm | Check that phase tracks real motion, which SAR imaging depends on | Not started |
| **E4:** redo the power test on raw data | Settle the saturation and dB-scale question | Not started |
| **E5:** repeated reflection captures: glass, plastic, metal, brushed-metal control | Find out if we can tell materials apart, and how repeatable the readings are | Not started |
| **Multi-material analysis (Ivan)** | Do multi-material objects reconstruct worse in Wave-Former? Label MITO objects by material | Not started |
| **Get reconstruction numbers** | Close the biggest gap. Ask staff for the Wave-Former checkpoint, otherwise train a small PoinTr baseline. | Not started |
| **SAR imaging:** MITO's sample raw data, then real objects | Compare real partial views with simulation (bottle upright vs tilted, lidded jar) | Later, needs a scanner |

**What E5 decides for Proposal A:**
- **Materials separate, even across thicknesses:** measure per-part material values for the simulator.
- **They separate only with known thickness:** calibrate per sheet and model thickness.
- **Only metal vs non-metal separates:** narrow Proposal A to "blocks vs passes".

## Deadlines
- **Nov 20:** presentation / Progress Report 2
- **Dec 7:** final presentation

## More detail
- Measurements: `wf_sim/hardware/MEASUREMENT_LOG.md`
- Experiment steps: `experiment.md`
- Figures: `wf_sim/figures_guide.md`
- Setup: `README.md`
