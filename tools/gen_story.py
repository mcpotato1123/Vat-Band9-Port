#!/usr/bin/env python3
"""Compile the Ren'Py script into Band-friendly progressive story nodes.

Input : 解包/对话/对话表.csv        speaker + text keyed by source line
        解包/脚本源码/script.rpy   structure (show / hide / menu / jump)
        解包/立绘 解包/背景 _unpacked_cg/images/cg   art inventory
Output: 移植版/src/common/story/index.txt, chunk-*.txt
        移植版/src/common/assets.js
        tools/_build/story_report.json

Node schema
  {"t":"s","n":<speaker>,"x":<text>,"bg":<idx>,"sp":[[slot,idx]],"cg":<idx>}
  {"t":"o","p":<prompt>,"o":[{"x":<text>,"j":<node index>}]}
  {"t":"j","j":<node index>}
  {"t":"e"}
"""
import csv
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

GAME = "解包"
SRC = os.path.join(GAME, "脚本源码", "script.rpy")
CSV = os.path.join(GAME, "对话", "对话表.csv")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = REPO
BUILD = os.path.join(REPO, "tools", "_build")
CHUNK = 400

CHAPTER_TITLES = {
    "start": "序章",
    "c1r1": "第一章 · 第一幕",
    "c1r2": "第一章 · 第二幕",
    "c1r3": "第一章 · 第三幕",
    "c1r4": "第一章 · 第四幕",
    "c2r1": "第二章 · 第一幕",
    "c2r2": "第二章 · 第二幕",
    "c2r3": "第二章 · 第三幕",
    "c3r1": "第三章 · 第一幕",
    "c3r2": "第三章 · 第二幕",
    "c3r3": "第三章 · 第三幕",
}
CN_TAG = {
    "陈蝶蕊": "cdr", "许清北": "xqb", "基伯": "gc", "基卡": "gc",
    "奥罗拉": "ai", "谢姐": "xj", "店长": "dz", "孙膑": "sb",
    "老师": "ls", "李大爷": "ldy",
}

SHIP = ["start", "c1r1", "c1r2", "c1r3", "c1r4", "c2r1", "c2r2", "c2r3", "c3r1", "c3r2", "c3r3"]

SLOTS = {"cdr": 2, "xqb": 1, "gc": 0, "ai": 1, "xj": 2, "dz": 0, "ls": 0,
         "nsa": 0, "nva": 0, "nvb": 0, "sb": 0, "ldy": 0, "lnn": 0,
         "temp_xqb1": 1, "temp_xqb2": 1}


def norm(s):
    return re.sub(r"[\s_]+", "_", s.strip()).lower()


def squash(s):
    return re.sub(r"[^0-9a-z\u4e00-\u9fff]", "", s.lower())


def inventory():
    art = {}
    for kind, folder in (("sp", os.path.join(GAME, "立绘")),
                         ("bg", os.path.join(GAME, "背景")),
                         ("cg", os.path.join("_unpacked_cg", "images", "cg"))):
        if not os.path.isdir(folder):
            continue
        for f in sorted(os.listdir(folder)):
            if f.lower().endswith((".png", ".jpg")):
                art.setdefault(norm(os.path.splitext(f)[0]), (kind, os.path.join(folder, f), os.path.splitext(f)[0]))
    return art


def load_char_images():
    """character variable -> Ren'Py image tag (Character(..., image="cdr"))."""
    path = os.path.join(GAME, "脚本源码", "CharacterDefines.rpy")
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8", errors="replace"):
        m = re.search(r"define\s+(\w+)\s*=\s*Character\(", line)
        if not m:
            continue
        im = re.search(r'image\s*=\s*"([^"]+)"', line)
        if im:
            out[m.group(1)] = im.group(1)
    return out


def load_dialogue():
    """{"正篇"|"测试": {line: (speaker, text)}}"""
    rows = {"正篇": {}, "测试": {}}
    with open(CSV, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            src = r["来源"]
            if src in rows:
                rows[src][int(r["行号"])] = (r["显示名"], r["台词"])
    return rows


class Builder:
    def __init__(self, art, dialogue):
        self.art = art
        self.dlg = dialogue
        self.nodes = []
        self.label_at = {}
        self.art_index = {}
        self.used = []
        self.unknown = {}
        self.bg = -1
        self.bg_is_cg = False
        self.sprites = {}
        self.cur = "start"
        self.synth = 0
        self.charimg = load_char_images()
        self.dlg_key = "正篇"
        self.alt = {}
        for k in self.art:
            self.alt.setdefault(squash(k), k)

    # ---- art -------------------------------------------------------
    def idx(self, base):
        k = norm(base)
        if k not in self.art_index:
            self.art_index[k] = len(self.art_index)
            self.used.append(k)
        return self.art_index[k]

    def find(self, toks):
        for n in range(min(len(toks), 4), 0, -1):
            joined = " ".join(toks[:n])
            k = norm(joined)
            if k in self.art:
                return k, self.art[k]
            sq = squash(joined)
            if sq in self.alt:
                k2 = self.alt[sq]
                return k2, self.art[k2]
        return None, None

    def show(self, body):
        body = re.sub(r"\s+with\s+.*$", "", body).rstrip(":").strip()
        toks = body.split()
        # drop Ren'Py modifiers and everything after them
        for n, t in enumerate(toks):
            if t in ("zorder", "onlayer", "at", "as", "behind"):
                toks = toks[:n]
                break
        if not toks or toks[0] in ("screen", "black", "white") or toks[0].startswith("transition"):
            return
        toks[0] = self.charimg.get(toks[0], toks[0])
        k, hit = self.find(toks)
        if not hit:
            key = " ".join(toks[:2])
            self.unknown[key] = self.unknown.get(key, 0) + 1
            return
        kind, path, base = hit
        if base.startswith("模糊"):
            return
        if kind == "bg":
            if base.endswith("_前"):
                return
            self.bg = self.idx(base)
            self.bg_is_cg = base.upper().startswith("CG")
        elif kind == "cg":
            self.bg = self.idx(base)
            self.bg_is_cg = True
            self.sprites = {}
        else:
            tag = toks[0].split("_")[0].lower()
            for cn, known in CN_TAG.items():
                if cn in base and tag != known:
                    tag = known
                    break
            self.sprites[SLOTS.get(tag, 1)] = self.idx(base)

    def hide(self, body):
        toks = body.split()
        if not toks:
            return
        tag = self.charimg.get(toks[0], toks[0]).split("_")[0].lower()
        if tag in SLOTS:
            self.sprites.pop(SLOTS[tag], None)

    # ---- nodes -----------------------------------------------------
    def add(self, node):
        self.nodes.append(node)
        return len(self.nodes) - 1

    def say(self, lineno):
        row = self.dlg.get(self.dlg_key, {}).get(lineno)
        if not row:
            return
        name, text = row
        node = {"t": "s", "n": name, "x": text}
        node["bg"] = self.bg
        node["sp"] = [] if self.bg_is_cg else [[s, i] for s, i in sorted(self.sprites.items())]
        if self.bg_is_cg and self.bg >= 0:
            node["cg"] = self.bg
        self.add(node)

    def label(self, name):
        self.label_at[name] = len(self.nodes)

    # ---- parse -----------------------------------------------------
    def block(self, lines, i, indent):
        while i < len(lines) and lines[i][0] >= indent:
            ind, text, lineno = lines[i]
            if ind > indent:
                i = self.block(lines, i, ind)
                continue
            if text.startswith("label "):
                m = re.match(r"^label\s+([A-Za-z_]\w*)\s*:", text)
                if m:
                    self.cur = m.group(1)
                    self.label(self.cur)
                i += 1
                continue
            if text.startswith("menu"):
                i = self.menu(lines, i, ind)
                continue
            m = re.match(r"^(show|scene)\s+(.+)$", text)
            if m:
                self.show(m.group(2))
                i = self.skip(lines, i, ind) if text.rstrip().endswith(":") else i + 1
                continue
            m = re.match(r"^hide\s+(.+)$", text)
            if m:
                self.hide(m.group(1))
                i += 1
                continue
            m = re.match(r"^jump\s+([A-Za-z_]\w*)$", text)
            if m:
                self.add({"t": "j", "j": m.group(1)})
                i += 1
                continue
            if re.match(r"^call\s+", text):
                i += 1
                continue
            if re.match(r"^return\b", text):
                self.add({"t": "e"})
                i += 1
                continue
            if lineno in self.dlg.get(self.dlg_key, {}):
                m = re.match(r'^([A-Za-z_]\w*)((?:\s+[^\s"]+)*)\s+"', text)
                if m and m.group(2).strip():
                    self.show(m.group(1) + " " + m.group(2).strip())
                self.say(lineno)
                i += 1
                continue
            i = self.skip(lines, i, ind) if text.endswith(":") else i + 1
        return i

    def skip(self, lines, i, indent):
        i += 1
        while i < len(lines) and lines[i][0] > indent:
            i += 1
        return i

    def menu(self, lines, i, indent):
        prompt = ""
        m = re.search(r'caption\s*=\s*"([^"]*)"', lines[i][1])
        if m:
            prompt = m.group(1)
        i += 1
        options = []
        while i < len(lines) and lines[i][0] == indent + 4:
            om = re.match(r'^"([^"]*)"\s*:\s*$', lines[i][1])
            if not om:
                i += 1
                continue
            text = om.group(1)
            j = i + 1
            while j < len(lines) and lines[j][0] > indent + 4:
                j += 1
            options.append((text, i + 1, j))
            i = j
        if not options:
            return i
        self.synth += 1
        after = "L_after_%d" % self.synth
        names = ["L_%s_%d_%d" % (self.cur, self.synth, n) for n in range(len(options))]
        pos = self.add({"t": "o", "p": prompt,
                        "o": [{"x": t, "j": nm} for (t, _, _), nm in zip(options, names)]})
        for (text, s, e), nm in zip(options, names):
            self.label(nm)
            self.block(lines, s, indent + 8)
            self.add({"t": "j", "j": after})
        self.label(after)
        return i


def main():
    art = inventory()
    dlg = load_dialogue()
    raw = open(SRC, encoding="utf-8", errors="replace").read().splitlines()
    lines = []
    for n, ln in enumerate(raw, 1):
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        lines.append((len(ln) - len(ln.lstrip()), ln.strip(), n))

    b = Builder(art, dlg)
    b.dlg_key = "正篇"
    b.block(lines, 0, lines[0][0])

    # 「我不认可」branch: label byebye lives in script_test.rpy
    test_path = os.path.join(GAME, "脚本源码", "script_test.rpy")
    if os.path.exists(test_path):
        raw_t = open(test_path, encoding="utf-8", errors="replace").read().splitlines()
        start = None
        for n, ln in enumerate(raw_t):
            if re.match(r"^label\s+byebye\s*:", ln):
                start = n
                break
        if start is not None:
            region = []
            for n in range(start, len(raw_t)):
                ln = raw_t[n]
                if n > start and re.match(r"^label\s+\w+\s*:", ln):
                    break
                if not ln.strip() or ln.lstrip().startswith("#"):
                    continue
                region.append((len(ln) - len(ln.lstrip()), ln.strip(), n + 1))
            if region:
                b.dlg_key = "测试"
                b.block(region, 0, region[0][0])
                b.dlg_key = "正篇"

    if not b.nodes or b.nodes[-1].get("t") != "e":
        b.add({"t": "e"})

    # resolve label jumps to node indices
    resolved, missing = 0, {}
    for node in b.nodes:
        if node["t"] == "j":
            tgt = node["j"]
            if tgt in b.label_at:
                node["j"] = b.label_at[tgt]
                resolved += 1
            else:
                missing[tgt] = missing.get(tgt, 0) + 1
                node["j"] = len(b.nodes) - 1
        elif node["t"] == "o":
            for o in node["o"]:
                if o["j"] in b.label_at:
                    o["j"] = b.label_at[o["j"]]
                else:
                    missing[o["j"]] = missing.get(o["j"], 0) + 1
                    o["j"] = len(b.nodes) - 1

    total = len(b.nodes)
    chapters = []
    for name in SHIP:
        if name in b.label_at:
            chapters.append({"id": name, "title": CHAPTER_TITLES.get(name, name),
                             "start": b.label_at[name]})
    if "byebye" in b.label_at:
        chapters.append({"id": "byebye", "title": "告别", "start": b.label_at["byebye"],
                         "hide": 1})

    os.makedirs(os.path.join(OUT, "src", "common", "story"), exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)

    chunks = []
    for n, start in enumerate(range(0, total, CHUNK)):
        part = b.nodes[start:start + CHUNK]
        fn = "chunk-%03d.txt" % n
        with open(os.path.join(OUT, "src", "common", "story", fn), "w", encoding="utf-8") as f:
            json.dump(part, f, ensure_ascii=False, separators=(",", ":"))
        chunks.append({"f": fn, "start": start, "n": len(part)})

    index = {"v": 1, "total": total, "chunkNodes": CHUNK,
             "chapters": chapters, "chunks": chunks}
    with open(os.path.join(OUT, "src", "common", "story", "index.txt"), "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, separators=(",", ":"))

    # asset table: index -> {k: kind, p: source path, n: base name}
    entries = []
    for k in b.used:
        kind, path, base = art[k]
        entries.append({"k": kind, "p": path.replace("\\", "/"), "n": base})
    with open(os.path.join(BUILD, "art.json"), "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=0)
    with open(os.path.join(OUT, "src", "common", "assets.js"), "w", encoding="utf-8") as f:
        f.write("// placeholder - run tools/gen_assets.py to fill with output paths\n")
        f.write("export const IMG = [];\n")

    report = {"nodes": total, "chunks": len(chunks), "chapters": chapters,
              "art": {k: 0 for k in ("bg", "sp", "cg")},
              "labels": list(b.label_at), "missingLabels": missing,
              "unknownShows": sorted(b.unknown.items(), key=lambda kv: -kv[1])[:30],
              "unresolvedJumps": resolved}
    for e in entries:
        report["art"][e["k"]] += 1
    with open(os.path.join(BUILD, "story_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    print("nodes=%d chunks=%d chapters=%d" % (total, len(chunks), len(chapters)))
    print("art:", report["art"])
    print("missing labels:", missing)
    print("unknown show (top 10):", sorted(b.unknown.items(), key=lambda kv: -kv[1])[:10])


if __name__ == "__main__":
    main()
