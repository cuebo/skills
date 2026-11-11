#!/usr/bin/env python3
"""Corner-leak regression check.

Renders a solid red screenshot and a solid black one with a transparent background.
The black render gives the phone silhouette; any red pixel outside it means the
screen mask is leaking past the rounded body.

  python3 scripts/verify.py -d 17promax --canvas 1290x2796
"""
import argparse, os, subprocess, sys, tempfile

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
FRAME = os.path.join(HERE, "frame.py")


def render(shot, out, device, canvas):
    subprocess.run([sys.executable, FRAME, shot, "-d", device, "--canvas", canvas,
                    "--bg", "transparent", "-o", out], check=True, cwd=HERE,
                   stdout=subprocess.DEVNULL)


def main():
    p = argparse.ArgumentParser(description="check for screenshot corner leak")
    p.add_argument("-d", "--device", default="17promax")
    p.add_argument("--canvas", default="1290x2796", help="output canvas WxH")
    p.add_argument("--shot-size", help="fake screenshot size WxH, default = canvas")
    p.add_argument("--tol", type=int, default=20, help="allowed leak pixels (antialiasing)")
    a = p.parse_args()

    w, h = (int(v) for v in (a.shot_size or a.canvas).lower().split("x"))
    d = tempfile.mkdtemp(prefix="verify-frame-")
    red, blk = os.path.join(d, "red.png"), os.path.join(d, "black.png")
    Image.new("RGB", (w, h), (255, 0, 0)).save(red)
    Image.new("RGB", (w, h), (0, 0, 0)).save(blk)
    rout, sout = os.path.join(d, "red-out.png"), os.path.join(d, "sil.png")
    render(red, rout, a.device, a.canvas)
    render(blk, sout, a.device, a.canvas)

    sil = np.array(Image.open(sout).split()[3])
    rgb = np.array(Image.open(rout).convert("RGB")).astype(int)
    red_px = (rgb[:, :, 0] > 200) & (rgb[:, :, 1] < 60) & (rgb[:, :, 2] < 60)
    leak = int((red_px & (sil < 8)).sum())
    ok = leak <= a.tol
    print("%s leak=%d px (tol %d) device=%s" % ("PASS" if ok else "FAIL", leak, a.tol, a.device))
    if not ok:
        ys, xs = np.nonzero(red_px & (sil < 8))
        print("  leaking bbox=%s" % ((int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())),))
        print("  hint: bezel.holes() must delegate to holefit.cached(), not a bbox rectangle")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
