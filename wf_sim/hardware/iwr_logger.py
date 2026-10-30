"""Configure the IWR1443BOOST out-of-box demo and log range profiles.

  python -m hardware.iwr_logger live                       # alignment: live peak
  python -m hardware.iwr_logger session                    # labelled segments, Enter to start/stop
  python -m hardware.iwr_logger record --exp A --material glass --angle 10
  python -m hardware.iwr_logger record --exp B --material glass --label with_sheet

Each recording is saved as hardware/data/<exp>/<name>.npz with the range
profiles (frames x bins, dB), the range axis, and metadata (JSON). A session
also writes a text log to hardware/logs/session_<time>.txt and one .npz per
segment to hardware/data/session_<time>/.
"""
import argparse
import json
import threading
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import serial

from hardware import tlv

HERE = Path(__file__).resolve().parent
DEFAULT_CFG = HERE / "iwr1443_range_profile.cfg"


PROMPT = b"mwDemo:/>"


def _command(cli, line, timeout=3.0):
    """Send one CLI line and return the board's reply.

    The board drops characters that arrive before it has printed its next
    prompt, so wait for "Done"/an error *and* the prompt after it."""
    cli.reset_input_buffer()
    cli.write((line + "\n").encode())
    reply, t0, t_answer = b"", time.time(), None
    while time.time() - t0 < timeout:
        reply += cli.read(cli.in_waiting or 1)
        for marker in (b"Done", b"Error", b"not recognized"):
            k = reply.rfind(marker)
            if k >= 0:
                t_answer = t_answer or time.time()
                if PROMPT in reply[k:] or time.time() - t_answer > 0.3:
                    time.sleep(0.05)
                    return reply.decode(errors="replace")
    return reply.decode(errors="replace")


def send_cfg(cli, cfg_text, retries=2):
    """Send the cfg line by line; stop on the first error the board reports."""
    for line in cfg_text.splitlines():
        line = line.strip()
        if not line or line.startswith("%"):
            continue
        for attempt in range(retries + 1):
            text = _command(cli, line)
            if "Done" in text or "not recognized" not in text:
                break
            time.sleep(0.2)                     # garbled line: let the CLI settle, resend
        if "Done" not in text and not line.startswith("sensorStop"):
            raise RuntimeError(f"cfg line failed: {line!r}\nboard said: {text.strip()!r}\n"
                               "Press the board's reset button (NRST) before retrying.")


def check_cfg(cfg_text):
    for line in cfg_text.splitlines():
        tok = line.split()
        if tok and tok[0] == "clutterRemoval" and tok[-1] != "0":
            raise SystemExit("clutterRemoval is enabled in the cfg: it removes static "
                             "targets like our plate. Set its last field to 0.")


def open_ports(args):
    cli = serial.Serial(args.cli, 115200, timeout=0.05)
    data = serial.Serial(args.data, 921600, timeout=0.05)
    cfg_text = Path(args.cfg).read_text()
    check_cfg(cfg_text)
    send_cfg(cli, cfg_text)
    return cli, data, cfg_text


def frames(data, stream=None):
    """Yield parsed packets that contain a range profile, forever."""
    stream = stream or tlv.PacketStream()
    t_last = time.time()
    while True:
        for pkt in stream.feed(data.read(data.in_waiting or 1)):
            t_last = time.time()
            if tlv.TLV_RANGE_PROFILE in pkt["tlvs"]:
                yield pkt
            else:
                print("packet without range profile: enable logMagRange in guiMonitor")
        if time.time() - t_last > 5:
            raise RuntimeError("no packets for 5 s: check the data port and that the "
                               "cfg ends with sensorStart")


def peak_in_window(rp_db, rng, rmin, rmax):
    sel = (rng >= rmin) & (rng <= rmax)
    k = np.flatnonzero(sel)[np.argmax(rp_db[sel])]
    return rng[k], rp_db[k]


def cmd_live(args):
    _, data, cfg = open_ports(args)
    rng = None
    for pkt in frames(data):
        rp = tlv.range_profile_db(pkt["tlvs"][tlv.TLV_RANGE_PROFILE])
        if rng is None:
            rng = tlv.range_axis_from_cfg(cfg, len(rp))
            print(f"{len(rp)} range bins, bin spacing {rng[1] * 100:.2f} cm")
        r, p = peak_in_window(rp, rng, args.rmin, args.rmax)
        bar = "#" * int(max(0, p - args.floor_db))
        print(f"frame {pkt['frame']:6d}  peak {p:6.1f} dB at {100 * r:5.1f} cm  {bar}")


def cmd_record(args):
    _, data, cfg = open_ports(args)
    profiles, frame_ids, t = [], [], []
    gen = frames(data)
    for _ in range(args.skip):                  # let the chirps settle
        next(gen)
    for pkt in gen:
        profiles.append(tlv.range_profile_db(pkt["tlvs"][tlv.TLV_RANGE_PROFILE]))
        frame_ids.append(pkt["frame"])
        t.append(time.time())
        if len(profiles) >= args.frames:
            break
    rp = np.array(profiles)
    rng = tlv.range_axis_from_cfg(cfg, rp.shape[1])
    meta = dict(exp=args.exp, material=args.material, angle_deg=args.angle,
                distance_cm=args.distance, thickness_mm=args.thickness,
                label=args.label, notes=args.notes, cfg=cfg,
                time=datetime.now().isoformat(timespec="seconds"))
    name = args.material + (f"_{args.angle:g}deg" if args.angle is not None else "") \
        + (f"_{args.label}" if args.label else "")
    out = HERE / "data" / args.exp / f"{name}.npz"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists() and not args.overwrite:
        k = 2
        while (out.parent / f"{name}_rep{k}.npz").exists():
            k += 1
        out = out.parent / f"{name}_rep{k}.npz"
    np.savez(out, range_profile_db=rp, range_m=rng, frame=np.array(frame_ids),
             host_time=np.array(t), meta=json.dumps(meta))
    r, p = peak_in_window(np.median(rp, axis=0), rng, args.rmin, args.rmax)
    print(f"saved {out.relative_to(HERE)}: {len(rp)} frames, "
          f"median peak {p:.1f} dB at {100 * r:.1f} cm")


def cmd_session(args):
    """Labelled segments: the radar streams continuously, but frames are only
    logged between the START and STOP key presses."""
    _, data, cfg = open_ports(args)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = HERE / "logs" / f"session_{stamp}.txt"
    seg_dir = HERE / "data" / f"session_{stamp}"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = open(log_path, "w", buffering=1)
    lock = threading.Lock()
    t0 = time.time()
    st = dict(mode="idle", rng=None, frames=[], error=None, stop=False, last_idle=0.0)

    def write(line):
        with lock:
            log.write(line + "\n")

    write(f"# session {stamp}  cfg={args.cfg}  window={args.rmin}-{args.rmax} m")
    write("# columns: t_s  frame  peak_dB  peak_cm  window_median_dB")

    def reader():
        try:
            for pkt in frames(data):
                if st["stop"]:
                    return
                rp = tlv.range_profile_db(pkt["tlvs"][tlv.TLV_RANGE_PROFILE])
                if st["rng"] is None:
                    st["rng"] = tlv.range_axis_from_cfg(cfg, len(rp))
                    write(f"# {len(rp)} range bins, spacing {100 * st['rng'][1]:.2f} cm")
                rng = st["rng"]
                r, p = peak_in_window(rp, rng, args.rmin, args.rmax)
                med = np.median(rp[(rng >= args.rmin) & (rng <= args.rmax)])
                now = time.time() - t0
                if st["mode"] == "recording":
                    with lock:
                        st["frames"].append((pkt["frame"], now, rp))
                    write(f"{now:.2f}\t{pkt['frame']}\t{p:.2f}\t{100 * r:.1f}\t{med:.2f}")
                    print(f"  REC frame {pkt['frame']:6d}  peak {p:6.1f} dB at {100 * r:5.1f} cm")
                elif st["mode"] == "setup" and now - st["last_idle"] > 1.0:
                    st["last_idle"] = now
                    print(f"  (setup, not logged) peak {p:6.1f} dB at {100 * r:5.1f} cm")
        except Exception as e:  # report in the main thread and the log
            st["error"] = e
            write(f"# ERROR {e}")

    threading.Thread(target=reader, daemon=True).start()
    print(f"\nLogging to {log_path.relative_to(HERE.parent)}")
    try:
        while st["error"] is None:
            label = input("\nLabel for next segment (e.g. plate_40cm), or q to finish: ").strip()
            if label.lower() == "q":
                break
            if not label:
                continue
            st["mode"] = "setup"
            input(f"Set up '{label}' (live peak shown below), then press Enter to START\n")
            with lock:
                st["frames"] = []
                st["mode"] = "recording"
            write(f"# START {label}  {datetime.now().isoformat(timespec='seconds')}")
            input("Recording... press Enter to STOP\n")
            with lock:
                st["mode"] = "idle"
                seg = st["frames"]
            if not seg:
                write(f"# STOP {label}  (no frames)")
                print("no frames recorded")
                continue
            rp = np.array([f[2] for f in seg])
            rng = st["rng"]
            peaks = np.array([peak_in_window(x, rng, args.rmin, args.rmax)[1] for x in rp])
            r, p = peak_in_window(np.median(rp, axis=0), rng, args.rmin, args.rmax)
            summary = (f"n={len(rp)}  median_peak={p:.2f} dB at {100 * r:.1f} cm  "
                       f"frame_peak_std={peaks.std():.2f} dB")
            write(f"# STOP {label}  {summary}")
            print(f"--> {label}: {summary}")
            seg_dir.mkdir(parents=True, exist_ok=True)
            np.savez(seg_dir / f"{label}.npz", range_profile_db=rp, range_m=rng,
                     frame=np.array([f[0] for f in seg]),
                     host_time=np.array([f[1] for f in seg]),
                     meta=json.dumps(dict(label=label, session=stamp, cfg=cfg,
                                          rmin=args.rmin, rmax=args.rmax)))
    except KeyboardInterrupt:
        print("\ninterrupted")
    finally:
        st["stop"] = True
        if st["error"] is not None:
            print(f"ERROR: {st['error']}")
        write(f"# END  {datetime.now().isoformat(timespec='seconds')}")
        log.close()
        print(f"log saved: {log_path.relative_to(HERE.parent)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cli", default="/dev/ttyACM0", help="config/CLI port (115200 baud)")
    ap.add_argument("--data", default="/dev/ttyACM1", help="data port (921600 baud)")
    ap.add_argument("--cfg", default=str(DEFAULT_CFG))
    ap.add_argument("--rmin", type=float, default=0.25, help="peak search window (m)")
    ap.add_argument("--rmax", type=float, default=0.60)
    sub = ap.add_subparsers(dest="cmd", required=True)

    live = sub.add_parser("live", help="print the peak every frame (for alignment)")
    live.add_argument("--floor-db", type=float, default=60.0, help="bar-graph zero")
    live.set_defaults(func=cmd_live)

    ses = sub.add_parser("session", help="labelled segments, Enter to start/stop, text log")
    ses.set_defaults(func=cmd_session)

    rec = sub.add_parser("record", help="record N frames to an .npz file")
    rec.add_argument("--exp", required=True, help="A (angle sweep), B (transmission), C ...")
    rec.add_argument("--material", required=True, help="metal, glass, PET, PP, empty ...")
    rec.add_argument("--angle", type=float, help="plate rotation (deg)")
    rec.add_argument("--distance", type=float, default=40.0, help="radar-target (cm)")
    rec.add_argument("--thickness", type=float, help="sheet thickness (mm)")
    rec.add_argument("--label", default="", help="extra tag, e.g. with_sheet")
    rec.add_argument("--notes", default="")
    rec.add_argument("--frames", type=int, default=50)
    rec.add_argument("--skip", type=int, default=5)
    rec.add_argument("--overwrite", action="store_true")
    rec.set_defaults(func=cmd_record)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
