# MAS.S64 project: Material- and Orientation-Aware Wave-Former

Siddharth Kulkarni, Ivan Wren · MAS.S64 Wireless Sensing and Physical AI (MIT, Fall 2026)

Two proposals building on Wave-Former (mmWave 3D shape completion):
**(A)** per-part materials in the synthetic training data, **(B)** robustness to object orientation.
This repo has our simplified partial-cloud simulator, IWR1443BOOST measurements, and the progress report.

| Path | What |
|---|---|
| `report.md` | Progress Report 1 outline: sections, figures, bullet notes |
| `wf_sim/` | Simulator, experiments, figures, results ([details](wf_sim/README.md)) |
| `wf_sim/hardware/` | IWR1443BOOST logger, protocol, measurement notebook, raw recordings |
| `IWR14483/profile.cfg` | Radar config exported from the TI Visualizer |
| `Images/` | Setup photos |

---

## Setup

### 1. Python environment
Python 3.10+ (tested with 3.12, Linux).

```bash
cd wf_sim
python3 -m venv .venv
.venv/bin/pip install numpy scipy trimesh matplotlib pandas pytest rtree embreex pyserial huggingface_hub
source .venv/bin/activate
unset PYTHONPATH          # only needed if ROS (or anything else) sets PYTHONPATH in your shell
python -m pytest -q       # 15 tests should pass
```
`embreex` is optional (about 10× faster ray casting). Without it trimesh falls back to `rtree`.

### 2. YCB meshes (not in the repo)
The 5 real-object meshes come from the MITO dataset and are git-ignored (third-party data). Without them everything
still runs, on the 4 procedural objects only. To download them (needs a free Hugging Face account):

```bash
cd wf_sim
source .venv/bin/activate
hf auth login             # once; paste a token from huggingface.co/settings/tokens
for obj in 003_cracker_box 005_tomato_soup_can 006_mustard_bottle 021_bleach_cleanser 025_mug; do
  hf download SignalKinetics/MITO_Dataset "$obj/uniform_10000.stl" --repo-type dataset --local-dir ../ycb_download
  cp "../ycb_download/$obj/uniform_10000.stl" "meshes/$obj.stl"
done
```
Any other `.stl`/`.obj` placed in `wf_sim/meshes/` is picked up automatically as a single-part object.

### 3. Run
```bash
cd wf_sim && source .venv/bin/activate && unset PYTHONPATH
python run_all.py            # all figures + CSVs (~5–6 min)
python run_all.py --quick    # everything except the orientation sweep (~15 s)
```
Outputs go to `wf_sim/figs/` and `wf_sim/results/`. See `wf_sim/figures_guide.md` for what each figure shows.

### 4. Reference repos (optional, git-ignored)
Cloned for reading only (the same lab's earlier systems). Not needed to run anything:
```bash
git clone git@github.com:signalkinetics/MITO_Codebase.git
git clone git@github.com:signalkinetics/mmNorm.git
git clone https://huggingface.co/datasets/SignalKinetics/MITO_Dataset   # Git LFS files; meshes are pointers until pulled
```
What we learned from them: `wf_sim/pipeline_notes.md`.

---

## Hardware (IWR1443BOOST), only to take new measurements

Existing recordings are already in `wf_sim/hardware/data/` and `logs/`. To record new ones:

1. **Power:** 5 V barrel jack (bench supply ~2.5 A limit; check polarity first), then micro-USB. Two ports appear:
   `/dev/ttyACM0` (config), `/dev/ttyACM1` (data). Your user must be in the `dialout` group.
2. **Firmware:** TI mmWave SDK out-of-box demo (xWR14xx, SDK 2.01). Ours was preloaded; otherwise flash it with
   TI UniFlash (SOP jumpers per the EVM user guide).
3. **Linux:** stop ModemManager, which grabs the serial ports: `sudo systemctl stop ModemManager`.
4. **Config:** `wf_sim/hardware/iwr1443_range_profile.cfg` (from the TI mmWave Demo Visualizer; static clutter removal
   off). For metal targets use the reduced-power variant `iwr1443_txbo18.cfg` (full power saturates the receiver).
5. **Record** (press the board's NRST button before each run):
   ```bash
   cd wf_sim && source .venv/bin/activate && unset PYTHONPATH
   python -m hardware.iwr_logger --cfg hardware/iwr1443_txbo18.cfg session
   ```
   Type a label, set up (live peak shown), Enter to start, Enter to stop, `q` to finish.

Details: `wf_sim/hardware/PROTOCOL.md` (plan, troubleshooting) and `wf_sim/hardware/MEASUREMENT_LOG.md` (every
session, setup and results).

---

## Not in the repo (git-ignored)

| What | Why | How to get it |
|---|---|---|
| `wf_sim/.venv/` | ~500 MB, machine-specific | step 1 |
| `wf_sim/meshes/*.stl` | MITO dataset (third-party) | step 2 |
| `MITO_Codebase/`, `mmNorm/`, `MITO_Dataset/` | separate repos | step 4 |
| `ycb_download/` | raw download cache | created by step 2 |
| `Datasheets/` | TI PDFs (copyrighted) | ti.com: *IWR1443BOOST User's Guide (SWRU518)* |

> **Note:** our simulator is a simplified geometric model inspired by the Wave-Former paper's description. It is not
> Wave-Former's simulator. We don't have Wave-Former's code.
