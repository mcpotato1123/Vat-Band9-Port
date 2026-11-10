#!/usr/bin/env python3
"""Convert unpacked art into Band 9 Pro sized palette PNGs.

Backgrounds and CGs keep their original 16:9 framing (whole image, letterboxed
into a 336x189 box) instead of being cropped to portrait.

Reads  tools/_build/art.json  (written by gen_story.py)
Writes src/common/img/{b,s,c,t}/NNN.png and rewrites assets.js.
"""
import json
import os
import shutil
import sys

from PIL import Image, ImageFilter

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC_JS = os.path.join(REPO, "src", "common", "assets.js")
ART_JSON = os.path.join(REPO, "tools", "_build", "art.json")
IMG_DIR = os.path.join(REPO, "src", "common", "img")
CG_DIR = os.path.join("_unpacked_cg", "images", "cg")

SCREEN_W = 336
BG_H = 220                 # 336 x 220 fill, crops the sides of the 16:9 source
SPRITE_W, SPRITE_H = 143, 220   # == the window between HUD strip and panel
THUMB_W, THUMB_H = 156, 88
GAL_W, GAL_H = 533, 300          # full 16:9 CG at the scene-window height
BG_COLORS, SP_COLORS, CG_COLORS, THUMB_COLORS, GAL_COLORS = 160, 160, 160, 64, 160
BUDGET_MB = 16.0


def load_entries():
    return json.load(open(ART_JSON, encoding="utf-8"))


def scan_cg_files():
    out = {}
    if not os.path.isdir(CG_DIR):
        return out
    for f in sorted(os.listdir(CG_DIR)):
        if f.lower().endswith((".png", ".jpg")):
            out[os.path.splitext(f)[0]] = os.path.join(CG_DIR, f)
    return out


def fit(im, w, h, bg=(0, 0, 0)):
    """Whole image, aspect preserved, centred on a w*h canvas."""
    if im.mode in ("P", "LA", "RGBA"):
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", rgba.size, bg)
        flat.paste(rgba, mask=rgba.split()[-1])
        im = flat
    else:
        im = im.convert("RGB")
    sw, sh = im.size
    s = min(w / sw, h / sh)
    nw, nh = max(1, int(sw * s + 0.5)), max(1, int(sh * s + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), bg)
    canvas.paste(im, ((w - nw) // 2, (h - nh) // 2))
    return canvas


def cover(im, w, h, bias_y=0.45):
    """Fill w*h, cropping the overflow (used for backgrounds/CGs)."""
    if im.mode in ("P", "LA", "RGBA"):
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (0, 0, 0))
        flat.paste(rgba, mask=rgba.split()[-1])
        im = flat
    else:
        im = im.convert("RGB")
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = max(w, int(sw * s + 0.5)), max(h, int(sh * s + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * bias_y)
    return im.crop((x, y, x + w, y + h))


def sprite(im, w, h, waist=0.46):
    """Upper body only, bottom-aligned: head..waist always fits above the panel."""
    im = im.convert("RGBA")
    bb = im.getbbox()
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    if not bb:
        return canvas
    im = im.crop(bb)
    sw, sh = im.size
    # a full-body shot is much taller than wide -> keep head..waist only
    if sw / sh < 0.45:
        im = im.crop((0, 0, sw, max(1, int(sh * waist))))
        sw, sh = im.size
    s = min(h / sh, w / sw)
    nw, nh = max(1, int(sw * s + 0.5)), max(1, int(sh * s + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=50, threshold=2))
    canvas.paste(im, ((w - nw) // 2, h - nh), im)
    return canvas


def strip(im, w, h):
    """Whole image scaled to height h, then centred/padded to width w."""
    if im.mode in ("P", "LA", "RGBA"):
        rgba = im.convert("RGBA")
        flat = Image.new("RGB", rgba.size, (0, 0, 0))
        flat.paste(rgba, mask=rgba.split()[-1])
        im = flat
    else:
        im = im.convert("RGB")
    sw, sh = im.size
    nw = max(1, int(sw * h / sh + 0.5))
    im = im.resize((nw, h), Image.LANCZOS)
    canvas = Image.new("RGB", (w, h), (0, 0, 0))
    canvas.paste(im, ((w - nw) // 2, 0))
    return canvas


def contain(im, w, h, anchor="bottom"):
    im = im.convert("RGBA")
    sw, sh = im.size
    s = min(w / sw, h / sh)
    nw, nh = max(1, int(sw * s + 0.5)), max(1, int(sh * s + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    x = (w - nw) // 2
    y = h - nh if anchor == "bottom" else (h - nh) // 2
    canvas.alpha_composite(im, (x, y))
    return canvas


def save(im, path, colors, alpha):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if alpha:
        q = im.convert("RGBA").quantize(colors=colors, method=Image.FASTOCTREE)
    else:
        q = im.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT,
                                       dither=Image.FLOYDSTEINBERG)
    q.save(path, "PNG", optimize=True)


def main():
    entries = load_entries()
    if not entries:
        raise SystemExit("art.json empty - run gen_story.py first")

    # every CG in the archive joins the gallery, even if the script never shows it
    have = set(e["n"] for e in entries)
    for name, path in scan_cg_files().items():
        if name not in have:
            entries.append({"k": "cg", "p": path.replace("\\", "/"), "n": name})

    if os.path.isdir(IMG_DIR):
        shutil.rmtree(IMG_DIR)

    sizes = {"bg": 0, "sp": 0, "cg": 0}
    out = []
    for n, e in enumerate(entries):
        kind, path, name = e["k"], e["p"], e["n"]
        sub = {"bg": "b", "sp": "s", "cg": "c"}[kind]
        dest = "/common/img/%s/%03d.png" % (sub, n)
        full = os.path.join(IMG_DIR, sub, "%03d.png" % n)
        thumb = ""
        big = ""
        try:
            with Image.open(path) as im:
                if kind == "bg":
                    pic = cover(im, SCREEN_W, BG_H)
                    pic = pic.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))
                    save(pic, full, BG_COLORS, False)
                elif kind == "cg":
                    pic = cover(im, SCREEN_W, BG_H)
                    pic = pic.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))
                    save(pic, full, CG_COLORS, False)
                    tp = os.path.join(IMG_DIR, "t", "%03d.png" % n)
                    save(fit(im, THUMB_W, THUMB_H), tp, THUMB_COLORS, False)
                    thumb = "/common/img/t/%03d.png" % n
                    gp = os.path.join(IMG_DIR, "g", "%03d.png" % n)
                    gal = strip(im, GAL_W, GAL_H)
                    gal = gal.filter(ImageFilter.UnsharpMask(radius=1.1, percent=55, threshold=2))
                    save(gal, gp, GAL_COLORS, False)
                    big = "/common/img/g/%03d.png" % n
                else:
                    save(sprite(im, SPRITE_W, SPRITE_H), full, SP_COLORS, True)
        except Exception as exc:  # noqa: BLE001
            print("FAIL", path, exc)
            continue
        sizes[kind] += os.path.getsize(full)
        if thumb:
            sizes[kind] += os.path.getsize(os.path.join(IMG_DIR, "t", "%03d.png" % n))
        if big:
            sizes[kind] += os.path.getsize(os.path.join(IMG_DIR, "g", "%03d.png" % n))
        out.append((n, kind, dest, name, thumb, big))

    with open(SRC_JS, "w", encoding="utf-8") as f:
        f.write("// generated by gen_story.py + gen_assets.py\n")
        f.write("// index = story node bg / sp / cg value\n")
        f.write("export const IMG = [\n")
        for n, kind, dest, name, thumb, big in out:
            extra = (',t:"%s"' % thumb) if thumb else ""
            if big:
                extra += ',g:"%s"' % big
            f.write('  {k:"%s",p:"%s",n:"%s"%s},\n' % (kind, dest, name, extra))
        f.write("];\n")

    total = sum(sizes.values()) / 1e6
    for k, v in sizes.items():
        print("%-3s %3d files  %6.2f MB" % (k, sum(1 for e in out if e[1] == k), v / 1e6))
    print("total images: %.2f MB  (budget %.1f MB)" % (total, BUDGET_MB))
    if total > BUDGET_MB:
        print("!! over budget")


if __name__ == "__main__":
    main()
