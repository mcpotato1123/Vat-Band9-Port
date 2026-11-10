#!/usr/bin/env python3
"""Validate the compiled story: chunk integrity, art references, reachability."""
import json
import os
import re
import sys
from collections import deque

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SRC = "移植版/src"
STORY = os.path.join(SRC, "common", "story")
ASSETS = os.path.join(SRC, "common", "assets.js")

errors, warns = [], []


def load():
    idx = json.load(open(os.path.join(STORY, "index.txt"), encoding="utf-8"))
    nodes = []
    for ch in idx["chunks"]:
        part = json.load(open(os.path.join(STORY, ch["f"]), encoding="utf-8"))
        if len(part) != ch["n"]:
            errors.append("chunk %s: %d nodes, index says %d" % (ch["f"], len(part), ch["n"]))
        if ch["start"] != len(nodes):
            errors.append("chunk %s starts at %d, expected %d" % (ch["f"], ch["start"], len(nodes)))
        nodes.extend(part)
    if len(nodes) != idx["total"]:
        errors.append("total %d != %d" % (len(nodes), idx["total"]))
    return idx, nodes


def load_assets():
    txt = open(ASSETS, encoding="utf-8").read()
    entries = []
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("{k:"):
            k = line.split('k:"')[1].split('"')[0]
            p = line.split('p:"')[1].split('"')[0]
            n = line.split('n:"')[1].split('"')[0] if 'n:"' in line else ""
            entries.append({"k": k, "p": p, "n": n})
    return entries


def check(idx, nodes, art):
    n = len(nodes)
    if not art:
        errors.append("assets.js 为空：先跑 gen_story.py + gen_assets.py")
        return set()

    for i, node in enumerate(nodes):
        t = node.get("t")
        if t == "s":
            if "x" not in node:
                errors.append("node %d: say without text" % i)
            for key in ("bg", "cg"):
                v = node.get(key)
                if v is not None and (v < 0 or v >= len(art)):
                    errors.append("node %d: %s index %s out of range" % (i, key, v))
            for slot, img in node.get("sp") or []:
                if img < 0 or img >= len(art):
                    errors.append("node %d: sprite index %s out of range" % (i, img))
                if art[img]["k"] != "sp":
                    errors.append("node %d: sprite %d is %s" % (i, img, art[img]["k"]))
        elif t == "j":
            if not (0 <= node["j"] < n):
                errors.append("node %d: jump target %s out of range" % (i, node["j"]))
        elif t == "o":
            if not node.get("o"):
                errors.append("node %d: empty choice" % i)
            for opt in node.get("o", []):
                if not (0 <= opt["j"] < n):
                    errors.append("node %d: option target %s out of range" % (i, opt["j"]))
        elif t == "e":
            pass
        else:
            errors.append("node %d: unknown type %r" % (i, t))

    # reachability
    seen = set()
    q = deque([0])
    while q:
        pc = q.popleft()
        if pc in seen or pc >= n:
            continue
        seen.add(pc)
        node = nodes[pc]
        t = node.get("t")
        if t == "s":
            q.append(pc + 1)
        elif t == "j":
            q.append(node["j"])
        elif t == "o":
            for opt in node.get("o", []):
                q.append(opt["j"])

    dead = [i for i in range(n) if i not in seen]
    if dead:
        warns.append("%d unreachable nodes (first: %s)" % (len(dead), dead[:8]))

    # chapter sanity
    starts = [c["start"] for c in idx["chapters"]]
    if starts != sorted(starts):
        errors.append("chapters not sorted by start")
    for c in idx["chapters"]:
        if not (0 <= c["start"] < n):
            errors.append("chapter %s start out of range" % c["id"])
    return seen


def walk_playthrough(nodes, choice_pick=0, limit=20000):
    pc, steps, endings = 0, 0, []
    while steps < limit:
        if pc < 0 or pc >= len(nodes):
            endings.append("end-of-nodes@%d" % pc)
            break
        node = nodes[pc]
        t = node.get("t")
        steps += 1
        if t == "s":
            pc += 1
            if pc >= len(nodes):
                endings.append("end-of-nodes")
                break
        elif t == "j":
            pc = node["j"]
        elif t == "o":
            opts = node.get("o", [])
            pc = opts[min(choice_pick, len(opts) - 1)]["j"]
        elif t == "e":
            endings.append("e@%d" % pc)
            break
    return steps, endings


def main():
    idx, nodes = load()
    art = load_assets()
    check(idx, nodes, art)

    for pick in (0, 1, 2):
        steps, end = walk_playthrough(nodes, pick)
        print("playthrough pick=%d: %d steps, end=%s" % (pick, steps, end))

    print("nodes=%d chapters=%d assets=%d" % (len(nodes), len(idx["chapters"]), len(art)))
    for w in warns:
        print("WARN " + w)
    if errors:
        for e in errors[:30]:
            print("FAIL " + e)
        sys.exit(1)
    print("OK")


if __name__ == "__main__":
    main()
