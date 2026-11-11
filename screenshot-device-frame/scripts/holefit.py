#!/usr/bin/env python3
'''Screen-cutout detection for bezel PNGs.

A bezel PNG is transparent in two places that are identical by alpha alone:
  * the screen hole, enclosed by the phone body
  * the margin outside the phone silhouette
So 'bbox intersected with transparent' also grabs the four corners that sit
outside the rounded body, and a square-cornered screenshot leaks past the bezel
there. Fix: keep only the connected transparent component that is the hole.
'''
import hashlib, json, os
import numpy as np
from PIL import Image, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
MDIR = os.path.join(HERE, '.masks')
CACHE = os.path.join(HERE, '.holes.json')


def _label(passable):
    '''Run-length connected components (4-conn). Int32 labels, 0 = background.'''
    h, w = passable.shape
    parent = [0]

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    rows, nid = [], 1
    for y in range(h):
        idx = np.flatnonzero(np.diff(np.concatenate(
            ([0], passable[y].astype(np.int8), [0]))))
        cur = []
        for x0, x1 in zip(idx[0::2], idx[1::2]):
            cur.append((int(x0), int(x1), nid))
            parent.append(nid)
            nid += 1
        prev = rows[-1] if rows else []
        i = j = 0
        while i < len(prev) and j < len(cur):
            a0, a1, aid = prev[i]
            b0, b1, bid = cur[j]
            if a1 > b0 and b1 > a0:
                union(aid, bid)
            if a1 <= b1:
                i += 1
            else:
                j += 1
        rows.append(cur)

    lab = np.zeros((h, w), np.int32)
    for y, cur in enumerate(rows):
        for x0, x1, rid in cur:
            lab[y, x0:x1] = find(rid)
    return lab


def compute(fp):
    '''Return (bbox, L mask) for the screen hole, corners rounded and antialiased.'''
    im = Image.open(fp).convert('RGBA')
    a = np.array(im.split()[3], dtype=np.uint8)
    passable = a < 16
    lab = _label(passable)

    ids, cnt = np.unique(lab[passable], return_counts=True)
    border = np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])
    outside = set(int(v) for v in np.unique(border) if v)
    best, bestn = 0, -1
    for i, c in zip(ids.tolist(), cnt.tolist()):
        if i not in outside and c > bestn:
            best, bestn = i, c
    if best == 0:                                   # hole touches border: take biggest
        best = int(ids[int(cnt.argmax())])

    hole = lab == best
    ys, xs = np.nonzero(hole)
    bbox = [int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1]

    # 1px outward so the screen tucks under the antialiased bezel rim (no bg hairline)
    core = Image.fromarray((hole * 255).astype(np.uint8), 'L').filter(ImageFilter.MaxFilter(3))
    soft = Image.fromarray(255 - a, 'L').point(lambda v: min(255, v * 2))
    mask = Image.composite(soft, Image.new('L', im.size, 0), core)
    return bbox, mask


def cached(fp):
    '''{b: bbox, mask: L mask}. Mask is cached as PNG: recomputing costs seconds.'''
    st = os.stat(fp)
    k = os.path.abspath(fp)
    cache = {}
    if os.path.exists(CACHE):
        try:
            cache = json.load(open(CACHE))
        except Exception:
            cache = {}
    mp = os.path.join(MDIR, hashlib.sha1(k.encode()).hexdigest()[:16] + '.png')
    hit = cache.get(k)
    if (hit and hit.get('m') == st.st_mtime and hit.get('s') == st.st_size
            and hit.get('k') == mp and os.path.exists(mp)):
        return {'b': hit['b'], 'mask': Image.open(mp).convert('L')}
    bbox, mask = compute(fp)
    os.makedirs(MDIR, exist_ok=True)
    mask.save(mp, optimize=True)
    cache[k] = {'m': st.st_mtime, 's': st.st_size, 'b': bbox, 'k': mp}
    json.dump(cache, open(CACHE, 'w'))
    return {'b': bbox, 'mask': mask}
