"""Download a few real photos of each YCB object for label_ui.py.

  python materials/fetch_photos.py            (from Project/wf_sim; needs Pillow)
  python materials/fetch_photos.py 025 030    (only these ids)

Source: the official YCB server (ycb-benchmarks S3). The per-object high-res archive is 1.6 GB, so we
stream it and stop after N_PHOTOS images (its order is random, so they are different cameras/angles;
about 3 MB each). Nothing is extracted to disk: only .jpg bytes are read and re-saved, shrunk.
If an object has no high-res archive, falls back to the google_16k texture image (unwrapped, patchy).
Saves materials/photos/<id>_<k>.jpg. Objects that already have photos are skipped (re-run to resume).
"""
import csv
import io
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
PHOTOS = HERE / "photos"
BASE = "http://ycb-benchmarks.s3-website-us-east-1.amazonaws.com/data/"
N_PHOTOS = 4
MAX_SIDE = 1200


def server_names():
    with urllib.request.urlopen(BASE + "objects.json", timeout=30) as r:
        return json.load(r)["objects"]


def match(oid, names):
    """Our id ('025', '065a') -> server name ('025_mug', '065-a_cups'); first variant if ours has none."""
    key = oid[:3] + ("-" + oid[3:] if len(oid) > 3 else "")
    hits = [n for n in names if n[:len(key)] == key and (len(n) == len(key) or n[len(key)] in "_-")]
    return hits[0] if hits else None


def save_image(data, path):
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im.thumbnail((MAX_SIDE, MAX_SIDE))
    im.save(path, quality=88)


def stream_images(url, n, suffix):
    """Yield the bytes of the first n images in a remote .tgz, without downloading the rest."""
    with urllib.request.urlopen(url, timeout=60) as r, tarfile.open(fileobj=r, mode="r|gz") as tf:
        got = 0
        for m in tf:
            if m.isfile() and m.name.lower().endswith(suffix):
                yield tf.extractfile(m).read()
                got += 1
                if got >= n:
                    return


def sources(name):
    # objects.json says '027-skillet' but the archives are '027_skillet': try both spellings
    for nm in dict.fromkeys([name, name.replace("-", "_", 1)]):
        yield f"{BASE}berkeley/{nm}/{nm}_berkeley_rgb_highres.tgz", N_PHOTOS, ".jpg", "photos"
    for nm in dict.fromkeys([name, name.replace("-", "_", 1)]):
        yield f"{BASE}google/{nm}_google_16k.tgz", 1, "texture_map.png", "texture"


def fetch(oid, name):
    last = "no images in archive"
    for url, n, suffix, label in sources(name):
        try:
            k = 0
            for k, data in enumerate(stream_images(url, n, suffix), 1):
                save_image(data, PHOTOS / f"{oid}_{k}.jpg")
            if k:
                return f"{k} {label}"
        except Exception as e:                       # 404 or dropped connection: try the next source
            last = f"{type(e).__name__}: {e}"
    return f"FAILED ({last})"


def main():
    PHOTOS.mkdir(exist_ok=True)
    with open(HERE / "ycb_materials.csv", newline="", encoding="utf-8") as f:
        ids = list(dict.fromkeys(r["id"] for r in csv.DictReader(f)))
    if sys.argv[1:]:
        ids = [i for i in ids if i in sys.argv[1:]]
    names = server_names()
    for oid in ids:
        if any(PHOTOS.glob(f"{oid}_*.jpg")):
            print(f"{oid}: already have photos, skip")
            continue
        name = match(oid, names)
        if not name:
            print(f"{oid}: not on the YCB server")
            continue
        print(f"{oid} ({name}): {fetch(oid, name)}", flush=True)


if __name__ == "__main__":
    main()
