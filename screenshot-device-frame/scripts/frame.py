#!/usr/bin/env python3
"""Frame a screenshot inside an iPhone / iPad / Mac bezel.

  python3 frame.py shot.png -d 17promax --canvas 1290x2796 --bg "#0b1220" --bg2 "#1d4ed8" --shadow
"""
import argparse, os, sys
from PIL import Image, ImageFilter
from bezel import ALIAS, FDIR, background, color, find_frame, holes


def render(shot, fp, out, a):
    bbox, mask, frame = holes(fp)
    hw, hh = bbox[2] - bbox[0], bbox[3] - bbox[1]

    img = Image.open(shot).convert("RGB")
    k = max(hw / img.width, hh / img.height)      # cover: scale then center-crop
    img = img.resize((round(img.width * k), round(img.height * k)), Image.LANCZOS)
    l, t = (img.width - hw) // 2, (img.height - hh) // 2
    screen = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    screen.paste(img.crop((l, t, l + hw, t + hh)), (bbox[0], bbox[1]))

    if a.canvas:
        cw, ch = (int(v) for v in a.canvas.lower().split("x"))
    else:
        ch, cw = a.out_height, round(a.out_height * a.aspect)
    scale = a.device_width / frame.width if a.device_width else (ch * a.device_ratio) / frame.height
    nw, nh = round(frame.width * scale), round(frame.height * scale)

    canvas = Image.new("RGBA", (cw, ch), (0, 0, 0, 0))
    if a.bg_image:
        bg = Image.open(a.bg_image).convert("RGB")
        s = max(cw / bg.width, ch / bg.height)
        bg = bg.resize((round(bg.width * s), round(bg.height * s)), Image.LANCZOS)
        canvas.paste(bg.crop(((bg.width - cw) // 2, (bg.height - ch) // 2,
                              (bg.width - cw) // 2 + cw, (bg.height - ch) // 2 + ch)), (0, 0))
    else:
        canvas = background(cw, ch, color(a.bg), color(a.bg2) if a.bg2 else None, a.angle)

    ox, oy = (cw - nw) // 2 + a.offset_x, (ch - nh) // 2 + a.offset_y
    if a.shadow:
        blur = max(2, round(nw * 0.035))
        q = 4                                    # blur at 1/4 res then upscale: >10x faster
        sw, sh_ = max(1, nw // q), max(1, nh // q)
        pad = max(2, blur // q) * 2
        lay = Image.new("L", (sw + pad * 2, sh_ + pad * 2), 0)
        lay.paste(frame.resize((sw, sh_), Image.LANCZOS).split()[3], (pad, pad))
        lay = lay.filter(ImageFilter.GaussianBlur(max(1, blur // q)))
        lay = lay.resize((nw + pad * 2 * q, nh + pad * 2 * q), Image.LANCZOS)
        sh = Image.new("RGBA", lay.size, (0, 0, 0, 0))
        sh.putalpha(lay.point(lambda v: int(v * a.shadow_opacity)))
        canvas.alpha_composite(sh, (ox - pad * q + a.shadow_offset, oy - pad * q + a.shadow_offset))

    reg = Image.new("RGBA", (nw, nh), (0, 0, 0, 0))
    reg.paste(screen.resize((nw, nh), Image.LANCZOS), (0, 0), mask.resize((nw, nh), Image.LANCZOS))
    canvas.alpha_composite(reg, (ox, oy))                                   # screen, clipped to cutout
    canvas.alpha_composite(frame.resize((nw, nh), Image.LANCZOS), (ox, oy))  # bezel on top

    if out.endswith(("/", os.sep)):
        out += "{name}.png"
    out = out.format(name=os.path.splitext(os.path.basename(shot))[0])
    os.makedirs(os.path.dirname(os.path.abspath(out)) or ".", exist_ok=True)
    if out.lower().endswith(".png") and color(a.bg) is None and not a.bg_image:
        canvas.save(out, optimize=True)
    elif out.lower().endswith((".jpg", ".jpeg")):
        canvas.convert("RGB").save(out, quality=95, optimize=True)
    else:
        canvas.convert("RGB").save(out, optimize=True)
    return out, canvas.size


def main():
    p = argparse.ArgumentParser(description="frame screenshots in iPhone / iPad / Mac bezels")
    p.add_argument("shots", nargs="*", help="screenshot file(s)")
    p.add_argument("-d", "--device", default="17promax", help="alias or frame-name fragment")
    p.add_argument("-o", "--out", default="framed-{name}.png", help="{name} = source basename")
    p.add_argument("--canvas", help="WxH, e.g. 1290x2796")
    p.add_argument("--out-height", type=int, default=1800, help="output height (default 1800)")
    p.add_argument("--aspect", type=float, default=1.0, help="width/height, 0.5625 = 9:16")
    p.add_argument("--device-ratio", type=float, default=0.9, help="bezel height / canvas height")
    p.add_argument("--device-width", type=int, help="bezel width in px")
    p.add_argument("--bg", default="#0f172a", help="background color, or 'transparent'")
    p.add_argument("--bg2", help="second color -> linear gradient")
    p.add_argument("--angle", type=float, default=135, help="gradient angle")
    p.add_argument("--bg-image", help="use an image as background")
    p.add_argument("--shadow", action="store_true", help="add drop shadow")
    p.add_argument("--shadow-opacity", type=float, default=0.45)
    p.add_argument("--shadow-offset", type=int, default=18)
    p.add_argument("--offset-x", type=int, default=0)
    p.add_argument("--offset-y", type=int, default=0)
    p.add_argument("--list", action="store_true", help="list frame aliases")
    a = p.parse_args()

    if a.list:
        for k, v in sorted(ALIAS.items()):
            print("  %-10s %s" % (k, v))
        print("\n-d also accepts a filename fragment. frame dir: " + FDIR)
        return

    fp = find_frame(a.device)
    for s in a.shots:
        out, size = render(s, fp, a.out, a)
        print("OK %s -> %s (%dx%d) frame=%s" % (s, out, size[0], size[1], os.path.basename(fp)))


if __name__ == "__main__":
    main()
