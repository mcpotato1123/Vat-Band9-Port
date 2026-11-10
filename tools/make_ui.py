import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "src", "common")
UI = os.path.join(OUT, "ui")
W, H = 336, 480
BTN_W, BTN_H = 168, 36

BAR = (255, 255, 255)
PLATE = (181, 178, 156)
PLATE_HI = (253, 253, 247)
INK = (20, 21, 18)


def font(size, serif=True):
    cands = ([r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\simfang.ttf"] if serif
             else [r"C:\Windows\Fonts\msyh.ttc"])
    cands.append(r"C:\Windows\Fonts\msyh.ttc")
    for p in cands:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


def cover(im, w, h, x_bias=0.5, y_bias=0.5):
    im = im.convert("RGB")
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = max(w, int(sw * s + 0.5)), max(h, int(sh * s + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    x = int((nw - w) * x_bias)
    y = int((nh - h) * y_bias)
    return im.crop((x, y, x + w, y + h))


def save(im, path, colors=96, alpha=False):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if alpha:
        q = im.convert("RGBA").quantize(colors=colors, method=Image.FASTOCTREE)
    else:
        q = im.convert("RGB").quantize(colors=colors, method=Image.MEDIANCUT,
                                       dither=Image.FLOYDSTEINBERG)
    q.save(path, "PNG", optimize=True)


def button(label, path):
    im = Image.new("RGBA", (BTN_W, BTN_H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rectangle([3, 1, 8, BTN_H - 2], fill=BAR)
    d.rectangle([16, 0, BTN_W - 1, BTN_H - 1], fill=(96, 90, 74, 150))
    d.rectangle([17, 1, BTN_W - 2, BTN_H - 2], fill=PLATE)
    d.line([18, 2, BTN_W - 3, 2], fill=PLATE_HI)
    for y in range(7, BTN_H - 3, 5):
        d.line([19, y, BTN_W - 4, y], fill=(172, 169, 148))
    f = font(17)
    tw = d.textlength(label, font=f)
    d.text(((17 + BTN_W - 2 - tw) / 2, 6), label, font=f, fill=INK)
    save(im, path, colors=48, alpha=True)


def main():
    os.makedirs(UI, exist_ok=True)
    art = Image.open("_ui_extract/gui/地雷主菜单.png")

    # full-bleed title background: 336x480 cover, heroine kept on the right
    save(cover(art, W, H, x_bias=0.55, y_bias=0.42), os.path.join(OUT, "title_bg.png"), 160)

    # official logo (already has alpha)
    logo = Image.open("_ui_extract/gui/拆迁地球及爱情事故_粉1280px.png").convert("RGBA")
    lw = 210
    lh = int(logo.size[1] * lw / logo.size[0])
    save(logo.resize((lw, lh), Image.LANCZOS), os.path.join(OUT, "logo.png"), 160, alpha=True)

    # launcher icon from the same framing, with rounded corners
    big = cover(art, 336, 336, x_bias=0.62, y_bias=0.1)
    face = big.crop((96, 20, 96 + 192, 20 + 192)).convert("RGBA")
    mask = Image.new("L", (192, 192), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, 191, 191], radius=44, fill=255)
    icon = Image.new("RGBA", (192, 192), (0, 0, 0, 0))
    icon.paste(face, (0, 0), mask)
    save(icon, os.path.join(OUT, "icon.png"), 128, alpha=True)

    labels = [("开始", "start"), ("继续", "load"), ("章节", "chapter"),
              ("CG 鉴赏", "extra"), ("设置", "config"), ("退出", "exit")]
    for text, name in labels:
        button(text, os.path.join(UI, name + ".png"))

    im = Image.new("RGB", (156, 88), (36, 37, 31))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 155, 87], outline=(66, 67, 55))
    d.text((68, 28), "?", font=font(30), fill=(97, 91, 60))
    im.quantize(colors=16, method=Image.MEDIANCUT).save(os.path.join(UI, "locked.png"), "PNG", optimize=True)

    for p in ("title_bg.png", "logo.png", "icon.png"):
        print(p, os.path.getsize(os.path.join(OUT, p)) // 1024, "KB")


if __name__ == "__main__":
    main()
