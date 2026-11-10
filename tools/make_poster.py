#!/usr/bin/env python3
"""Compose a store-style poster from the real assets and the 1:1 previews."""
import os
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = "移植版/src"
PREV = "移植版/preview"
OUT = "移植版/preview/00_poster.png"
W, H = 1200, 1800

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"


def f(px, bold=False):
    p = FONT_B if bold and os.path.exists(FONT_B) else FONT
    try:
        return ImageFont.truetype(p, px)
    except Exception:
        return ImageFont.load_default()


def title_window(im, out_w, out_h, x_bias=0.55):
    """Same framing as the title screen's full-bleed background, at poster resolution."""
    im = im.convert("RGB")
    sw, sh = im.size
    win_h = sh
    win_w = int(round(win_h * out_w / out_h))
    x = int((sw - win_w) * x_bias)
    return im.crop((x, 0, x + win_w, win_h)).resize((out_w, out_h), Image.LANCZOS)


def cover(im, w, h, bias_y=0.4):
    im = im.convert("RGB")
    sw, sh = im.size
    s = max(w / sw, h / sh)
    nw, nh = max(w, int(sw * s + 0.5)), max(h, int(sh * s + 0.5))
    im = im.resize((nw, nh), Image.LANCZOS)
    x = (nw - w) // 2
    y = int((nh - h) * bias_y)
    return im.crop((x, y, x + w, y + h))


def main():
    canvas = Image.new("RGB", (W, H), "#0b0a0c")

    # backdrop: blurred key art
    key = Image.open(os.path.join(SRC, "common", "title_bg.png"))
    bg = key.convert("RGB").resize((W, int(W * key.size[1] / key.size[0])), Image.LANCZOS)
    bg = cover(key, W, H, 0.35).filter(ImageFilter.GaussianBlur(28))
    bg = cover(Image.open("_unpacked_cg/images/cg/CG10夜空月亮_3.png"), W, H, 0.4).filter(ImageFilter.GaussianBlur(30))
    canvas.paste(bg, (0, 0))
    canvas.paste(Image.new("RGB", (W, H), "#0b0a0c"), (0, 0), Image.new("L", (W, H), 205))

    d = ImageDraw.Draw(canvas, "RGBA")

    # ---- key art card (sharp crop straight from the original menu artwork) ----
    card_w, card_h = 460, 660
    card_x, card_y = (W - card_w) // 2, 96
    art = title_window(Image.open("_ui_extract/gui/地雷主菜单.png"), card_w, card_h, 0.55)
    canvas.paste(art, (card_x, card_y))
    d.rectangle([card_x, card_y, card_x + card_w, card_y + card_h],
                outline=(255, 255, 255, 40), width=2)

    # ---- official logo ----
    logo = Image.open("_ui_extract/gui/拆迁地球及爱情事故_粉1280px.png").convert("RGBA")
    lw = 560
    lh = int(logo.size[1] * lw / logo.size[0])
    logo = logo.resize((lw, lh), Image.LANCZOS)
    canvas.paste(logo, ((W - lw) // 2, 786), logo)

    # ---- subtitle ----
    d.text((W // 2, 1128), "小米手环 · 个人移植版", font=f(46, True),
           fill="#f7dfce", anchor="ma")

    # ---- four watch screens ----
    shots = [("01_title.png", "标题"), ("02_game.png", "正文"),
             ("05_cg.png", "CG 鉴赏"), ("04_chapters.png", "章节")]
    cell_w, cell_h = 250, 356
    gap = 34
    total = cell_w * 4 + gap * 3
    x0 = (W - total) // 2
    y0 = 1200
    for i, (name, cap) in enumerate(shots):
        x = x0 + i * (cell_w + gap)
        d.rounded_rectangle([x, y0, x + cell_w, y0 + cell_h], radius=30, fill="#141416",
                            outline=(255, 255, 255, 36), width=2)
        shot = Image.open(os.path.join(PREV, name)).convert("RGB")
        inner_w, inner_h = cell_w - 18, cell_h - 18
        shot = shot.resize((inner_w, inner_h), Image.LANCZOS)
        mask = Image.new("L", (inner_w, inner_h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, inner_w - 1, inner_h - 1], radius=24, fill=255)
        canvas.paste(shot, (x + 9, y0 + 9), mask)
        d.text((x + cell_w // 2, y0 + cell_h + 16), cap, font=f(26), fill="#b8a49a", anchor="ma")

    # ---- footer ----
    d.line([(W // 2 - 210, 1626), (W // 2 + 210, 1626)], fill="#eb6877", width=2)
    d.text((W // 2, 1660), "仅适用于小米手环 9 Pro", font=f(40, True), fill="#f0eee4", anchor="ma")
    d.text((W // 2, 1718), "非官方同人作品 · 请支持正版", font=f(28), fill="#8f8681", anchor="ma")

    canvas.save(OUT)
    print("poster ->", OUT, canvas.size)


if __name__ == "__main__":
    main()
