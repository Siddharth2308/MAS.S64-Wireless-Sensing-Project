"""DCA1000 processing checks on synthetic captures (no hardware needed)."""
import zlib
from pathlib import Path

import numpy as np
import pytest

from hardware import dca_process as dca
from hardware.iwr_logger import pick_ports
from sim import materials as mat

CFG = dca.parse_cfg((Path(dca.__file__).parent / "iwr1443_txbo18.cfg").read_text(encoding="utf-8"))


def _write_capture(path, range_m, frames=20, amp=8000, tail=0):
    """Point target at range_m, in the on-disk layout I1..I4 Q1..Q4."""
    n = CFG["n_samples"]
    t = np.arange(n) / CFG["fs"]
    f0 = CFG["f_center"] - CFG["slope"] * (n - 1) / CFG["fs"] / 2
    phase = 4 * np.pi * (f0 + CFG["slope"] * t) * range_m / dca.C
    s = amp * np.exp(1j * phase)
    n_chirps = frames * CFG["chirps_per_frame"]
    rng = np.random.default_rng(0)
    iq = np.tile(s, (n_chirps, dca.N_RX, 1)) + rng.normal(0, 5, (n_chirps, dca.N_RX, n)) \
        + 1j * rng.normal(0, 5, (n_chirps, dca.N_RX, n))
    iq = iq.transpose(0, 2, 1)                               # chirps, samples, rx
    out = np.concatenate([iq.real, iq.imag], axis=2).astype("<i2")
    with open(path, "wb") as f:
        out.tofile(f)
        f.write(b"\0\0" * tail)


def test_cfg_values():
    assert CFG["n_samples"] == 240 and CFG["n_tx"] == 2 and CFG["chirps_per_frame"] == 32
    assert CFG["bin_m"] == pytest.approx(0.0409, abs=0.0002)
    assert CFG["lambda_m"] * 1e3 == pytest.approx(3.785, abs=0.01)


def test_summary_finds_target(tmp_path):
    f = tmp_path / "a.bin"
    _write_capture(f, 0.45)
    res, _, _ = dca.analyze(f, CFG)
    assert res["peak_cm"] == pytest.approx(45, abs=2.1)
    assert res["frames"] == 20 and res["complete"] and res["clip_pct"] == 0
    assert len(set(res["rx_peak_bins"].split())) == 1
    assert res["phase_std_deg"] < 1


def test_clipping_and_incomplete_are_flagged(tmp_path):
    f = tmp_path / "a.bin"
    _write_capture(f, 0.45, amp=32700, tail=7)
    res, _, _ = dca.analyze(f, CFG)
    assert res["clip_pct"] > 0 and not res["complete"]


@pytest.mark.parametrize("moved_mm", [0.5, 1.0])
def test_phase_shift_matches_physics(tmp_path, moved_mm):
    a, b = tmp_path / "a.bin", tmp_path / "b.bin"
    _write_capture(a, 0.45)
    _write_capture(b, 0.45 + moved_mm * 1e-3)
    delta, _ = dca.phase_shift(a, b, CFG)
    expected = (dca.expected_shift_deg(moved_mm, CFG) + 180) % 360 - 180
    assert np.abs((delta - expected + 180) % 360 - 180).max() < 3


def _write_response(path, range_m, gain=1.0, frames=5, noise=2.0, seed=0):
    """Target at range_m whose echo is scaled per sample by a complex gain(f)."""
    n = CFG["n_samples"]
    t = np.arange(n) / CFG["fs"]
    f = CFG["f_center"] + CFG["slope"] * (t - (n - 1) / CFG["fs"] / 2)
    s = 8000 * gain(f) * np.exp(1j * 4 * np.pi * f * range_m / dca.C) if callable(gain) \
        else 8000 * gain * np.exp(1j * 4 * np.pi * f * range_m / dca.C)
    n_chirps = frames * CFG["chirps_per_frame"]
    rng = np.random.default_rng(seed)
    iq = np.tile(s, (n_chirps, dca.N_RX, 1)) + rng.normal(0, noise, (n_chirps, dca.N_RX, n)) \
        + 1j * rng.normal(0, noise, (n_chirps, dca.N_RX, n))
    iq = iq.transpose(0, 2, 1)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.concatenate([iq.real, iq.imag], axis=2).astype("<i2").tofile(path)


def _sheet_gain(eps, d_mm, mode):
    def gain(f):
        r, t = mat.slab_coefficients(eps, d_mm, f)
        if mode == "r":
            return r
        # two-way through the sheet, relative to the same distance of air
        return (t * np.exp(1j * 2 * np.pi * f * d_mm * 1e-3 / dca.C)) ** 2
    return gain


def _capture(root, mode, sample, n, range_m, gain=1.0):
    path = root / f"E5_{mode}_{sample}_{n}" / "adc_data.bin"
    _write_response(path, range_m, gain, seed=zlib.crc32(path.parent.name.encode()))
    return path


def test_reflection_matches_sheet_model(tmp_path):
    jitter = [0.0, 0.3, -0.2]                                # re-placement, mm
    for n, dx in enumerate(jitter):
        _capture(tmp_path, "r", "alu", n, 0.45 + dx * 1e-3)
        _capture(tmp_path, "r", "glass", n, 0.45 + dx * 1e-3, _sheet_gain(6.0, 4.0, "r"))
    res, f = dca.analyze_reflection(dca._group_captures(tmp_path, "r"), CFG)
    model = 10 * np.log10(np.abs(mat.slab_coefficients(6.0, 4.0, f)[0]) ** 2)
    assert res["alu"]["level_db"].mean() == pytest.approx(0, abs=0.1)
    assert np.sqrt(np.mean((res["glass"]["curves"].mean(axis=0) - model) ** 2)) < 2.5


def test_transmission_loss_and_path(tmp_path):
    for n in range(3):
        _capture(tmp_path, "t", "none", n, 0.654)
        _capture(tmp_path, "t", "plastic", n, 0.654, _sheet_gain(2.6, 3.0, "t"))
        _capture(tmp_path, "t", "glass", n, 0.654, _sheet_gain(6.0, 4.0, "t"))
    res, f = dca.analyze_transmission(dca._group_captures(tmp_path, "t"), CFG)
    assert res["none"]["level_db"].mean() == pytest.approx(0, abs=0.1)
    for name, eps, d in [("plastic", 2.6, 3.0), ("glass", 6.0, 4.0)]:
        model = 10 * np.log10(np.mean(np.abs(mat.slab_coefficients(eps, d, f)[1]) ** 4))
        assert res[name]["level_db"].mean() == pytest.approx(model, abs=0.5)
    # the path estimate ranks them correctly (glass ~5.8 mm, plastic ~1.8 mm if no internal echoes)
    assert res["glass"]["path_mm"].mean() > res["plastic"]["path_mm"].mean()


def test_separation_rule():
    assert dca.separation([1.0, 1.1, 0.9], [3.0, 3.1, 2.9]) == pytest.approx(20, rel=0.01)
    assert dca.separation([1.0, 2.0, 3.0], [1.5, 2.5, 3.5]) < 3
    assert np.isnan(dca.separation([1.0], [2.0, 3.0]))


class _Port:
    def __init__(self, device, description):
        self.device, self.description = device, description


def test_pick_ports_windows_names():
    ports = [_Port("COM3", "Intel Active Management"),
             _Port("COM7", "XDS110 Class Auxiliary Data Port (COM7)"),
             _Port("COM6", "XDS110 Class Application/User UART (COM6)")]
    assert pick_ports(ports) == ("COM6", "COM7")
    assert pick_ports([_Port("COM3", "other")]) is None
