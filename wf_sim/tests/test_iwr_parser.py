"""Parser checks on synthetic packets (no hardware needed)."""
import struct

import numpy as np
import pytest

from hardware import tlv


def _packet(header_len, length_includes_header, rp_raw, frame=7):
    body = b""
    for t, payload in [(tlv.TLV_RANGE_PROFILE, rp_raw.astype("<u2").tobytes()),
                       (tlv.TLV_POINTS, struct.pack("<HH", 1, 9) +
                        struct.pack("<HhHhhh", 10, 0, 500, 512, 1024, -256))]:
        length = len(payload) + (8 if length_includes_header else 0)
        body += struct.pack("<II", t, length) + payload
    n_hdr_words = (header_len - 8) // 4
    total = header_len + len(body)
    total += (-total) % 32                       # SDK pads to 32 bytes
    words = [0x01020304, total, 0x1443, frame, 0, 1, 2] + [0] * (n_hdr_words - 7)
    pkt = tlv.MAGIC + struct.pack(f"<{n_hdr_words}I", *words) + body
    return pkt + b"\0" * (total - len(pkt))


@pytest.mark.parametrize("header_len", [36, 40])
@pytest.mark.parametrize("incl", [False, True])
def test_parse_layouts(header_len, incl):
    rp_raw = np.arange(256) * 40
    p = tlv.parse_packet(_packet(header_len, incl, rp_raw))
    assert p is not None and p["frame"] == 7
    db = tlv.range_profile_db(p["tlvs"][tlv.TLV_RANGE_PROFILE])
    np.testing.assert_allclose(db, rp_raw / 512 * 20 * np.log10(2))
    pts = tlv.detected_points(p["tlvs"][tlv.TLV_POINTS])
    np.testing.assert_allclose(pts, [[1.0, 2.0, -0.5]])


def test_stream_handles_garbage_and_split_reads():
    rp_raw = np.full(128, 1000)
    raw = b"\x07junk" + _packet(36, False, rp_raw, frame=1) + _packet(36, False, rp_raw, frame=2)
    s = tlv.PacketStream()
    out = []
    for i in range(0, len(raw), 37):             # arbitrary chunking
        out += s.feed(raw[i:i + 37])
    assert [p["frame"] for p in out] == [1, 2]


def test_range_axis():
    cfg = "profileCfg 0 77 7 7 58 0 0 68 1 256 5000 0 0 30\n"
    rng = tlv.range_axis_from_cfg(cfg, 256)
    # 3e8 * 5e6 / (2 * 68e12 * 256) = 4.31 cm per bin
    assert rng[1] == pytest.approx(0.0431, rel=1e-2)
