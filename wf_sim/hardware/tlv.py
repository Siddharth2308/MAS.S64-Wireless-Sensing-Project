"""Parser for the TI mmWave SDK out-of-box demo UART output (TLV packets).

Packet = magic word + header + TLVs. The header is 36 bytes on older SDKs
(xWR14xx, SDK 1.x) and 40 bytes on newer ones (adds subFrameNumber), and
SDK versions differ on whether a TLV length includes its 8-byte header. We
try each layout and keep the one whose TLVs tile the packet consistently,
so the same code works without knowing the SDK version.

TLV types used here: 1 = detected points, 2 = range profile (zero-Doppler
log-magnitude, uint16 in Q9 log2 units).
"""
import struct

import numpy as np

MAGIC = bytes([2, 1, 4, 3, 6, 5, 8, 7])
TLV_POINTS, TLV_RANGE_PROFILE, TLV_NOISE_PROFILE = 1, 2, 3
VALID_TYPES = set(range(1, 12))

# log2 magnitude in Q9 -> dB. Check against the TI Demo Visualizer once.
RANGE_PROFILE_Q = 9
DB_PER_LOG2 = 20 * np.log10(2)


def _walk_tlvs(pkt, header_len, length_includes_header):
    num_tlvs = struct.unpack_from("<I", pkt, 32)[0]
    off, tlvs = header_len, []
    for _ in range(num_tlvs):
        if off + 8 > len(pkt):
            return None
        t, length = struct.unpack_from("<II", pkt, off)
        payload = length - 8 if length_includes_header else length
        if t not in VALID_TYPES or payload < 0 or off + 8 + payload > len(pkt):
            return None
        tlvs.append((t, pkt[off + 8: off + 8 + payload]))
        off += 8 + payload
    # remaining bytes may only be alignment padding (< 32)
    return tlvs if len(pkt) - off < 32 else None


def parse_packet(pkt):
    """Return dict(frame, tlvs={type: payload}) or None if no layout fits."""
    if len(pkt) < 40 or not pkt.startswith(MAGIC):
        return None
    frame = struct.unpack_from("<I", pkt, 20)[0]
    for header_len in (36, 40):
        for incl in (False, True):
            tlvs = _walk_tlvs(pkt, header_len, incl)
            if tlvs is not None:
                return dict(frame=frame, tlvs=dict(tlvs))
    return None


def range_profile_db(payload, q=RANGE_PROFILE_Q):
    raw = np.frombuffer(payload, dtype="<u2").astype(float)
    return raw / 2 ** q * DB_PER_LOG2


def detected_points(payload):
    """(K, 3) xyz in meters, best effort for both SDK point formats."""
    if len(payload) >= 4:
        n, qfmt = struct.unpack_from("<HH", payload, 0)
        if len(payload) == 4 + 12 * n:          # SDK 1.x/2.x: int16 Q-format
            rec = np.frombuffer(payload[4:], dtype="<i2").reshape(n, 6)
            return rec[:, 3:6].astype(float) / 2 ** qfmt
    if len(payload) % 16 == 0:                  # SDK 3.x: float x, y, z, v
        return np.frombuffer(payload, dtype="<f4").reshape(-1, 4)[:, :3].astype(float)
    return np.zeros((0, 3))


class PacketStream:
    """Accumulates raw bytes from the data port and yields parsed packets."""

    def __init__(self):
        self.buf = bytearray()

    def feed(self, data):
        self.buf += data
        out = []
        while True:
            i = self.buf.find(MAGIC)
            if i < 0:
                del self.buf[:-len(MAGIC)]
                return out
            if len(self.buf) - i < 16:
                del self.buf[:i]
                return out
            total = struct.unpack_from("<I", self.buf, i + 12)[0]
            if total < 40 or total > 1 << 20:
                del self.buf[:i + 1]                # false magic match
                continue
            if len(self.buf) - i < total:
                del self.buf[:i]
                return out
            pkt = bytes(self.buf[i:i + total])
            del self.buf[:i + total]
            parsed = parse_packet(pkt)
            if parsed is not None:
                out.append(parsed)


def range_axis_from_cfg(cfg_text, n_bins):
    """Range of each bin (m) from the profileCfg line, or None.

    profileCfg fields: id startFreq idle adcStart rampEnd txPower txPhase
    freqSlope(MHz/us) txStart numAdcSamples sampleRate(ksps) ...
    """
    for line in cfg_text.splitlines():
        tok = line.split()
        if tok and tok[0] == "profileCfg" and len(tok) >= 12:
            slope = float(tok[8]) * 1e12            # Hz/s
            n_adc = int(tok[10])
            fs = float(tok[11]) * 1e3               # samples/s
            n_fft = 1 << (n_adc - 1).bit_length()
            dr = 3e8 * fs / (2 * slope * n_fft)
            return np.arange(n_bins) * dr
    return None
