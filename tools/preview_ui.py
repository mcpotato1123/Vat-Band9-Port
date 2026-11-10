#!/usr/bin/env python3
"""Composite 1:1 mockups of every page from the real assets + CSS values.

Output: 移植版/preview/*.png
"""
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = "移植版"
SRC = os.path.join(P, "src")
OUT = os.path.join(P, "preview")
W, H = 336, 480

FONT = r"C:\Windows\Fonts\msyh.ttc"
FONT_B = r"C:\Windows\Fonts\msyhbd.ttc"


def f(px, bold=False):
    p = FONT_B if bold and os.path.exists(FONT_B) else FONT
    try:
        return ImageFont.truetype(p, px)
    except Exception:
        return ImageFont.load_default()


class Canvas:
    def __init__(self, bg="#141512"):
        self.im = Image.new("RGB", (W, H), bg)
        self.d = ImageDraw.Draw(self.im, "RGBA")

    def rect(self, box, fill=None, outline=None):
        self.d.rectangle(box, fill=fill, outline=outline)

    def text(self, xy, s, px=12, color="#f0eee4", bold=False, anchor="la"):
        self.d.text(xy, s, font=f(px, bold), fill=color, anchor=anchor)

    def paste(self, path, xy, w=None, h=None, keep_alpha=False):
        if not path or not os.path.exists(path):
            return
        im = Image.open(path)
        im = im.convert("RGBA") if keep_alpha else im.convert("RGB")
        if w and h:
            im = im.resize((w, h), Image.LANCZOS)
        if keep_alpha:
            self.im.paste(im, xy, im)
        else:
            self.im.paste(im, xy)

    def save(self, name):
        os.makedirs(OUT, exist_ok=True)
        self.im.save(os.path.join(OUT, name))


def load_index():
    return json.load(open(os.path.join(SRC, "common", "story", "index.txt"), encoding="utf-8"))


def load_chunk(i):
    idx = load_index()
    ch = idx["chunks"][i]
    return json.load(open(os.path.join(SRC, "common", "story", ch["f"]), encoding="utf-8"))


def assets():
    txt = open(os.path.join(SRC, "common", "assets.js"), encoding="utf-8").read()
    out = []
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("{k:"):
            k = line.split('k:"')[1].split('"')[0]
            p = line.split('p:"')[1].split('"')[0]
            th = ""
            if ',t:"' in line:
                th = line.split(',t:"')[1].split('"')[0]
            gb = ""
            if ',g:"' in line:
                gb = line.split(',g:"')[1].split('"')[0]
            out.append({"k": k, "p": os.path.join(SRC, p.lstrip("/")),
                        "t": os.path.join(SRC, th.lstrip("/")) if th else "",
                        "g": os.path.join(SRC, gb.lstrip("/")) if gb else ""})
    return out


def wrap(text, cpl):
    out = []
    for para in text.split("\n"):
        line = para
        while len(line) > cpl:
            cut = cpl
            for k in range(8):
                ch = line[cpl - 1 - k]
                if ch in "，。！？；：、）」』…—":
                    cut = cpl - k
                    break
            out.append(line[:cut])
            line = line[cut:]
        out.append(line)
    return out


# ---------------------------------------------------------------- title
def title(art):
    c = Canvas()
    c.paste(os.path.join(SRC, "common", "title_bg.png"), (0, 0), 336, 480)
    c.text((326, 7), "V 1.0.0", 8, "#e4cfc8", anchor="ra")
    c.paste(os.path.join(SRC, "common", "logo.png"), (10, 30), 210, 118, keep_alpha=True)

    c.rect([28, 274, 144, 276], fill="#eb6877")
    names = ["start", "load", "chapter", "extra", "config", "exit"]
    for i, n in enumerate(names):
        c.paste(os.path.join(SRC, "common", "ui", n + ".png"), (10, 210 + i * 42), 168, 36, keep_alpha=True)
    c.save("01_title.png")


# ---------------------------------------------------------------- game
def game(art):
    nodes = load_chunk(3)
    node = None
    for n in nodes:
        if n.get("t") == "s" and n.get("bg", -1) >= 0 and len(n.get("sp") or []) == 2 and len(n.get("x", "")) < 70:
            node = n
            break
    node = node or next(n for n in nodes if n.get("t") == "s")

    c = Canvas()
    c.rect([0, 0, W, 252], fill="#000000")
    c.paste(art[node["bg"]]["p"], (0, 32), 336, 220)

    slots = [2, 96, 190]
    for s, i in (node.get("sp") or []):
        sp = Image.open(art[i]["p"]).convert("RGBA").resize((143, 220), Image.LANCZOS)
        c.im.paste(sp, (slots[s], 32), sp)

    c.rect([0, 0, W, 63], fill="#000000")
    c.d.rectangle([0, 0, W, 63], fill=(10, 11, 9, 0))
    c.rect([0, 0, W, 2], fill=(255, 255, 255, 26))
    c.rect([0, 0, int(W * 0.34), 2], fill="#eb6877")
    c.text((10, 8), "第一章 · 第一幕", 14, "#f7dfce")
    c.text((160, 9), "34%", 12, "#c9b3ac")
    c.text((313, 6), "≡", 30, "#f0eee4", anchor="ma")
    c.text((312, 236), "▼", 18, "#eb6877", anchor="ma")

    c.rect([0, 252, W, 480], fill=(20, 21, 18, 240))
    c.text((10, 258), node.get("n") or "旁白", 15, "#eb6877")
    c.rect([10, 282, 326, 283], fill="#5a5949")
    size = 18
    cpl = (316 - 6) // size
    lines = wrap(node.get("x", ""), cpl)[:6]
    for i, ln in enumerate(lines):
        c.text((10, 288 + i * (size + 4)), ln, size, "#f0eee4")
    c.save("02_game.png")


# ---------------------------------------------------------------- saves
def saves(art):
    c = Canvas()
    c.text((18, 12), "读档", 22, "#eeeadd")
    c.text((18, 40), "轻触栏位读取", 11, "#a4a48e")
    rows = [("01", "第一章 · 第一幕", "借给收入为零的家伙…"),
            ("02", "第一章 · 第二幕", "那我就先回去了"),
            ("03", "空栏位", "——")]
    for i, (no, cap, meta) in enumerate(rows):
        y = 62 + i * 92
        c.rect([14, y, 322, y + 84], fill="#282921")
        c.rect([14, y, 17, y + 84], fill="#a17c3b")
        c.text((26, y + 28), no, 20, "#c49342")
        c.text((66, y + 20), cap, 14, "#eeeadd")
        c.text((66, y + 46), meta, 10, "#b8ac8b")
    c.text((168, 392), "‹   1 / 10   ›", 12, "#b8ac8b", anchor="ma")
    c.d.rounded_rectangle([98, 424, 238, 464], radius=12, fill="#2c2e26", outline="#eb6877")
    c.text((168, 432), "返回", 18, "#f7dfce", anchor="ma")
    c.save("03_saves.png")


# ---------------------------------------------------------------- chapters
def chapters(art):
    idx = load_index()
    c = Canvas()
    c.text((18, 14), "章节", 22, "#eeeadd")
    c.text((18, 40), "正篇 %d 章 · 轻触跳转" % len([c for c in idx["chapters"] if not c.get("hide")]), 11, "#a4a48e")
    for i, ch in enumerate([c for c in idx["chapters"] if not c.get("hide")][:3]):
        y = 62 + i * 92
        c.rect([14, y, 322, y + 84], fill="#282921")
        c.rect([14, y, 17, y + 84], fill="#b58132")
        c.text((28, y + 24), ch["title"], 14, "#eeeadd")
        c.text((28, y + 48), "节点 %d" % ch["start"], 10, "#b8ac8b")
        c.text((300, y + 34), "›", 12, "#eb6877", anchor="ma")
    c.text((168, 392), "‹   1 / 4   ›", 12, "#b8ac8b", anchor="ma")
    c.d.rounded_rectangle([98, 424, 238, 464], radius=12, fill="#2c2e26", outline="#eb6877")
    c.text((168, 432), "返回标题", 18, "#f7dfce", anchor="ma")
    c.save("04_chapters.png")


# ---------------------------------------------------------------- cg
def cg(art):
    c = Canvas()
    c.text((18, 14), "CG 鉴赏", 22, "#eeeadd")
    c.text((18, 40), "9 / 44 已解锁", 11, "#a4a48e")
    cgs = [a for a in art if a["k"] == "cg"]
    for i in range(4):
        x = 12 + (i % 2) * 160
        y = 64 + (i // 2) * 140
        c.rect([x, y, x + 156, y + 132], fill="#24251f")
        if i < len(cgs):
            c.paste(cgs[i]["t"] or cgs[i]["p"], (x, y), 156, 88)
        c.text((x + 6, y + 92), ["CG1", "CG2", "CG3", "CG4"][i], 12, "#eeeadd")
        c.text((x + 146, y + 96), ["2/3", "1/3", "3/4", "2/2"][i], 10, "#b8ac8b", anchor="ra")
    c.text((168, 392), "‹    1 / 11    ›", 12, "#b8ac8b", anchor="ma")
    c.d.rounded_rectangle([98, 424, 238, 464], radius=12, fill="#2c2e26", outline="#eb6877")
    c.text((168, 432), "返回标题", 18, "#f7dfce", anchor="ma")
    c.save("05_cg.png")


# ---------------------------------------------------------------- settings
def settings(art):
    c = Canvas()
    c.text((18, 12), "设置", 22, "#eeeadd")
    c.text((18, 38), "轻触 − / + 调节 · 立即生效", 10, "#a4a48e")
    rows = [("字号", "18", True), ("播放速度", "26ms", True),
            ("自动播放", "关闭", True), ("屏幕常亮", "开", False),
            ("关于本作", "›", False)]
    for i, (lab, val, ctl) in enumerate(rows):
        y = 62 + i * 62
        c.rect([14, y, 322, y + 54], fill="#24251f")
        c.text((26, y + 16), lab, 18, "#e3e1cf")
        if ctl:
            c.text((196, y + 10), "−", 24, "#eb6877", anchor="ma")
            c.text((245, y + 17), val, 16, "#d1cbb6", anchor="ma")
            c.text((290, y + 10), "+", 24, "#eb6877", anchor="ma")
        else:
            c.text((302, y + 17), val, 16, "#eb6877", anchor="ra")
    # top edge of the preview block, clipped by the scroll viewport
    c.d.rectangle([14, 402, 322, 410], fill="#191a17", outline="#292b23")
    c.text((22, 405), "18px · 每行 17 字 · 每页 5 行", 10, "#777663")
    c.d.rounded_rectangle([98, 424, 238, 464], radius=12, fill="#2c2e26", outline="#eb6877")
    c.text((168, 432), "完成", 18, "#f7dfce", anchor="ma")
    c.save("06_settings.png")


WARN_TEXT = [
    '本作主要角色均已满18岁，平均年龄为100+岁.',
    '女主反对“自残”、“药物滥用”等行为，因此女主并非传统意义上的“地雷女”.',
    '本篇为单线单结局，所有选项均为演出效果服务，部分选项包含有整活性质的文本描述.',
    '剧情中包含无厘头黑色幽默情节，以及低俗笑话，请衡量自身体质酌情游玩.',
    '本作并非严肃文学.',
    '',
    '请确认您理解并认可以上说明.',
    '如若您无法接受，我们深表遗憾，并希望您点击右侧按钮.'
]


def warn(art):
    c = Canvas("#0b0507")
    c.paste(os.path.join(SRC, "common", "ui", "warn_top.png"), (93, 8), 150, 153, keep_alpha=True)
    top, cpl = 172, 27
    for para in WARN_TEXT:
        if para == "":
            top += 15
            continue
        line = ""
        for ch in para:
            line += ch
            if len(line) >= cpl:
                c.text((10, top), line, 11, "#d8c9c4")
                top += 15
                line = ""
        if line:
            c.text((10, top), line, 11, "#d8c9c4")
            top += 15
    c.paste(os.path.join(SRC, "common", "ui", "accept.png"), (26, 402), 120, 33, keep_alpha=True)
    c.paste(os.path.join(SRC, "common", "ui", "decline.png"), (190, 402), 120, 33, keep_alpha=True)
    c.save("09_warn.png")


def gate(art):
    c = Canvas()
    c.paste(os.path.join(SRC, "common", "title_bg.png"), (0, 0), 336, 480)
    c.d.rectangle([0, 0, W, 480], fill=(6, 5, 7, 158))
    c.text((168, 362), "点击继续", 20, "#f7dfce", anchor="ma")
    c.text((168, 396), "CLICK TO CONTINUE", 8, "#eb6877", anchor="ma")
    c.save("08_gate.png")


def confirm(art):
    c = Canvas()
    c.paste(os.path.join(SRC, "common", "title_bg.png"), (0, 0), 336, 480)
    c.d.rectangle([0, 0, W, 480], fill=(8, 6, 8, 214))
    c.text((168, 132), "是否要退出游戏？", 22, "#f7dfce", anchor="ma")
    c.paste(os.path.join(SRC, "common", "ui", "confirm.png"), (78, 210), 56, 56, keep_alpha=True)
    c.paste(os.path.join(SRC, "common", "ui", "cancel.png"), (202, 210), 56, 56, keep_alpha=True)
    c.save("07_confirm.png")


def cg_view(art):
    c = Canvas()
    c.rect([0, 0, W, 252], fill="#000000")
    cgs = [a for a in art if a["k"] == "cg" and a.get("g")]
    if cgs:
        im = Image.open(cgs[0]["g"]).convert("RGB")
        c.im.paste(im, (-98, 0))
    c.text((168, 308), "← 拖动查看全图 →", 12, "#8f8681", anchor="ma")
    c.d.ellipse([268, 10, 326, 68], fill=(12, 10, 12, 199), outline="#eb6877")
    c.text((297, 23), "×", 30, "#f7dfce", anchor="ma")
    c.text((57, 336), "‹", 28, "#d1cbb6", anchor="ma")
    c.text((168, 344), "1 / 2", 14, "#b8ac8b", anchor="ma")
    c.text((279, 336), "›", 28, "#d1cbb6", anchor="ma")
    c.save("10_cg_view.png")


def main():
    art = assets()
    title(art)
    game(art)
    saves(art)
    chapters(art)
    cg(art)
    settings(art)
    warn(art)
    gate(art)
    cg_view(art)
    confirm(art)
    print("preview ->", OUT)


if __name__ == "__main__":
    main()
