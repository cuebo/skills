#!/usr/bin/env python3
"""Bezel assets + screen-cutout detection. Used by frame.py."""
import json, math, os, re, sys, urllib.parse, urllib.request
from PIL import Image
import holefit

HERE = os.path.dirname(os.path.abspath(__file__))
FDIR = os.path.join(HERE, "frames")
CACHE = os.path.join(HERE, ".holes.json")
VER = "1772014847"   # pinned frameit-frames gh-pages build
BASE = "https://raw.githubusercontent.com/fastlane/frameit-frames/gh-pages/" + VER

ALIAS = {
    "17promax": "Apple iPhone 17 Pro Max Deep Blue.png",
    "17pro": "Apple iPhone 17 Pro Silver.png",
    "17": "Apple iPhone 17 Black.png",
    "16promax": "Apple iPhone 16 Pro Max Black Titanium.png",
    "16pro": "Apple iPhone 16 Pro Black Titanium.png",
    "16": "Apple iPhone 16 Black.png",
    "14pro": "Apple iPhone 14 Pro Black.png",
    "13": "Apple iPhone 13 Midnight.png",
    "se": "Apple iPhone SE Black.png",
    "ipad": "Apple iPad Pro (11-inch) Space Gray.png",
    "macbook": "Apple MacBook Pro 16 Space Gray.png",
}


def fetch(name):
    dest = os.path.join(FDIR, name)
    if os.path.exists(dest) and os.path.getsize(dest) > 5000:
        return dest
    os.makedirs(FDIR, exist_ok=True)
    url = "%s/%s" % (BASE, urllib.parse.quote(name))
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "frame"})
            with urllib.request.urlopen(req, timeout=90) as r:
                data = r.read()
            if len(data) < 5000:
                raise IOError("too small, probably 404")
            open(dest, "wb").write(data)
            print("downloaded %s (%dKB)" % (name, len(data) // 1024), file=sys.stderr)
            return dest
        except Exception as e:
            print("  retry %d/4: %s" % (i + 1, e), file=sys.stderr)
    raise SystemExit("download failed: %s\nput the PNG into %s manually" % (name, FDIR))


def find_frame(name):
    if os.path.isfile(name):
        return name
    key = re.sub(r"[\s\-_.]", "", name.lower())
    if name.lower() in ALIAS:
        return fetch(ALIAS[name.lower()])
    if name.lower().endswith(".png"):
        return fetch(name)
    names = [f for f in os.listdir(FDIR) if f.endswith(".png")] if os.path.isdir(FDIR) else []
    hits = [f for f in names if key in re.sub(r"[\s\-_.]", "", f.lower())]
    if len(hits) == 1:
        return fetch(hits[0])
    if not hits:
        raise SystemExit("no frame %r. aliases: %s" % (name, ", ".join(sorted(ALIAS))))
    raise SystemExit("%r matched several, be specific: %s" % (name, ", ".join(sorted(hits)[:8])))


def holes(fp):
    '''Screen cutout: (bbox, rounded+antialiased L mask, RGBA frame).

    MUST delegate to holefit: it keeps only the transparent component enclosed by
    the phone body. Building the mask as `bbox rectangle AND alpha<threshold`
    instead also catches the four transparent corners outside the rounded body,
    so a square-cornered screenshot leaks past the bezel there.
    Never cache this as a rectangle; never re-implement it inline.
    '''
    c = holefit.cached(fp)
    return c['b'], c['mask'], Image.open(fp).convert('RGBA')


def color(s):
    s = s.strip().lower()
    if s in ("white", "black"):
        return (255, 255, 255) if s == "white" else (0, 0, 0)
    if s == "transparent":
        return None
    s = s.lstrip("#")
    if len(s) == 3:
        s = "".join(c * 2 for c in s)
    if len(s) != 6:
        raise SystemExit("bad color: " + s)
    return tuple(int(s[i:i + 2], 16) for i in (0, 2, 4))


def background(w, h, c1, c2, angle):
    """Solid / linear gradient / transparent. Gradient is computed at 64x64 then upscaled."""
    if c1 is None:
        return Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if c2 is None:
        return Image.new("RGBA", (w, h), tuple(c1) + (255,))
    n = 64
    small = Image.new("RGB", (n, n))
    p = small.load()
    rad = math.radians(angle)
    dx, dy = math.cos(rad), math.sin(rad)
    span = abs(dx) * n + abs(dy) * n
    for y in range(n):
        for x in range(n):
            t = min(1.0, max(0.0, ((x - n / 2) * dx + (y - n / 2) * dy) / span + 0.5))
            p[x, y] = tuple(round(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return small.resize((w, h), Image.BICUBIC).convert("RGBA")
