#!/usr/bin/env python3
"""Packed BIG regression: 413/h20 baseline vs current crash-fix pack."""
from __future__ import annotations

import hashlib
import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import pack_china_heavy_aircraft as ch

CUR_DATA = Path("/tmp/aircraft_init_crash_fix/_SPEC_DATA_ONE.big")
CUR_ART = Path("/tmp/aircraft_init_crash_fix/_SPEC_ART_ONE.big")
BASE_DATA = Path("/tmp/baseline414/iconfix/_SPEC_DATA_ONE.big")  # PR #413 published DATA
BASE_ART = Path("/tmp/dl/_SPEC_ART_H20.big")  # ART reused at #413/#414 era
OUT = Path("/workspace")


def walk_chunks(blob: bytes, pos: int, end: int, out: list[int]) -> None:
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        payload = csize & 0x7FFFFFFF
        container = bool(csize & 0x80000000)
        hdr_end = pos + 8
        payload_end = hdr_end + payload
        if payload_end > len(blob) + 8:
            break
        out.append(ctype)
        if container:
            walk_chunks(blob, hdr_end, min(payload_end, len(blob)), out)
            pos = payload_end
        else:
            pos = payload_end
        if payload_end <= hdr_end:
            break


def load_big(path: Path):
    entries, raw = ch.read_big(path)
    files = {}
    order = []
    for name, off, size in entries:
        key = ch.norm_key(name)
        files[key] = (name.replace("/", "\\"), raw[off : off + size])
        order.append(key)
    return files, order


def w3d_info(blob: bytes) -> dict:
    types: list[int] = []
    walk_chunks(blob, 0, len(blob), types)
    anim = sum(1 for t in types if t in (0x200, 0x280, 0x2C0))
    tex = []
    for m in re.finditer(rb"([\w\-\. ]+\.(?:tga|dds|TGA|DDS))\x00", blob):
        tex.append(m.group(1).decode("latin1"))
    return {"size": len(blob), "nchunks": len(types), "anim": anim, "tex": sorted(set(tex))}


OBJ_RE = re.compile(r"^Object(?:Reskin)?\s+(\S+)", re.M)


def objects_in(text: str):
    out = []
    for m in OBJ_RE.finditer(text):
        nxt = OBJ_RE.search(text, m.end())
        block = text[m.start() : nxt.start() if nxt else len(text)]
        out.append((m.group(1), block))
    return out


def main() -> int:
    print("load current DATA")
    cur_d, _ = load_big(CUR_DATA)
    print("load base DATA 413")
    base_d, _ = load_big(BASE_DATA)
    print("load current ART")
    cur_a, _ = load_big(CUR_ART)
    print("load base ART h20")
    base_a, _ = load_big(BASE_ART)

    cur_w3d = {}
    cur_tex = set()
    for k, (n, b) in cur_a.items():
        leaf = n.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            cur_w3d[leaf[:-4]] = w3d_info(b)
        if leaf.endswith((".tga", ".dds")):
            cur_tex.add(leaf)
    base_w3d = {}
    for k, (n, b) in base_a.items():
        leaf = n.split("\\")[-1].lower()
        if leaf.endswith(".w3d"):
            base_w3d[leaf[:-4]] = w3d_info(b)

    # new/changed DATA files
    new_files = []
    changed_files = []
    for k, (n, b) in cur_d.items():
        if k not in base_d:
            new_files.append(k)
        elif hashlib.sha256(b).digest() != hashlib.sha256(base_d[k][1]).digest():
            changed_files.append(k)
    print("new DATA files", len(new_files), "changed", len(changed_files))

    e7 = []  # animation on no-anim W3D, PRELOAD
    e7_new = []
    missing_model_preload = []
    radar = []
    w3d_lost_anim = []

    # ART W3Ds that lost animation vs baseline
    for key, info in cur_w3d.items():
        old = base_w3d.get(key)
        if old and old["anim"] > 0 and info["anim"] == 0:
            w3d_lost_anim.append((key, old["anim"], old["size"], info["size"]))
        if key not in base_w3d:
            pass

    print("W3Ds that LOST animation vs h20 ART", len(w3d_lost_anim))
    for row in w3d_lost_anim[:30]:
        print(" LOSTANIM", row)

    # new W3Ds
    new_w3d = [k for k in cur_w3d if k not in base_w3d]
    print("new W3Ds vs h20", len(new_w3d))

    def analyze_block(obj, fn, block, is_new_file):
        models = re.findall(r"^\s*Model\s*=\s*(\S+)", block, re.M)
        anims = re.findall(r"^\s*Animation\s*=\s*(\S+)", block, re.M)
        kindm = re.search(r"KindOf\s*=\s*(.+)", block)
        kind = kindm.group(1).strip() if kindm else ""
        preload = "PRELOAD" in kind
        if kindm and re.search(r"\bRADAR\b", kind):
            radar.append((obj, fn, kind[:80]))
        if preload:
            for md in set(models):
                if md.lower() in ("none",):
                    continue
                if md.lower() not in cur_w3d:
                    # may live in EnglishZH
                    missing_model_preload.append((obj, fn, md, "not_in_spec_art"))
        if not anims:
            return
        bad = []
        for md in set(models):
            k = md.lower()
            if k not in cur_w3d:
                continue
            if cur_w3d[k]["anim"] > 0:
                continue
            for an in anims:
                if an.split(".", 1)[0].lower() == k:
                    bad.append((md, an, cur_w3d[k]["size"], cur_w3d[k]["anim"]))
        if bad:
            # was this exact animation already in 413 for same object?
            in_base = False
            # search base object
            for bk, (bn, bb) in base_d.items():
                if not bk.endswith(".ini"):
                    continue
                if obj in bb.decode("latin1", errors="replace"):
                    bt = bb.decode("latin1", errors="replace")
                    for o2, b2 in objects_in(bt):
                        if o2 == obj and any(an in b2 for _, an, *_ in bad):
                            in_base = True
            rec = {
                "obj": obj,
                "file": fn,
                "bad": bad,
                "preload": preload,
                "new_file": is_new_file,
                "in_414_same_anim": in_base,
            }
            e7.append(rec)
            if not in_base:
                e7_new.append(rec)

    for k, (n, b) in cur_d.items():
        if not k.endswith(".ini"):
            continue
        t = b.decode("latin1", errors="replace")
        is_new = k not in base_d
        for obj, block in objects_in(t):
            analyze_block(obj, n, block, is_new)

    print("E-7-class total", len(e7), "NEW vs 413", len(e7_new), "PRELOAD new", sum(1 for r in e7_new if r["preload"]))
    print("--- NEW E-7-class PRELOAD ---")
    for r in e7_new:
        if r["preload"]:
            print(r["obj"], r["file"], r["bad"][:2], "new_file", r["new_file"])

    # TEOD names
    teod = [
        "uvmirage", "nvj31", "nvj-20", "nvj16", "nvjh-7a", "avf-35", "avf-18",
        "avf16", "pak-fa", "su-37", "uvmig-21", "nvj-10", "avcargopln",
        "nvj-10d", "uvmirage_d", "uvmirage_e",
    ]
    print("\n--- TEOD W3D anim ---")
    for name in teod:
        info = cur_w3d.get(name)
        print(name, info if info else "MISSING")

    summary = {
        "new_data_files": len(new_files),
        "changed_data_files": len(changed_files),
        "new_w3d": len(new_w3d),
        "w3d_lost_anim": w3d_lost_anim,
        "e7_total": len(e7),
        "e7_new": e7_new,
        "radar": radar,
        "missing_model_preload_n": len(missing_model_preload),
    }
    Path("/tmp/post414_summary.json").write_text(json.dumps(summary, indent=2, default=str))
    print("wrote /tmp/post414_summary.json")
    # dump new_files aircraft-ish
    air_new = [k for k in new_files if any(s in k for s in ("airforce", "rotary", "airbase", "helicopter"))]
    print("new air-related DATA files", len(air_new))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
