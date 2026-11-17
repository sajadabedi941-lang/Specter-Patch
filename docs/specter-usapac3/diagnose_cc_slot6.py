#!/usr/bin/env python3
"""Dump live America Command Center path from packed DATA / ART BIGs."""
from __future__ import annotations

import re
import struct
from pathlib import Path

MERGED_DATA = Path("/workspace/docs/specter-usapac3/merged/_SPEC_DATA_ONE.big")
MERGED_ART2 = Path("/workspace/docs/specter-usapac3/merged/_SPEC_ART_TWO.big")
ORIG_DATA = Path("/tmp/spec-art-live/_SPEC_DATA_ONE.unified.big")
ORIG_ART2 = Path("/tmp/spec-art-live/_SPEC_ART_TWO.big")
PATCH = Path("/workspace/patch")


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name.replace("/", "\\"), off, size))
    return data, entries


def by_key(raw, entries):
    out = {}
    for name, off, size in entries:
        out[name.replace("/", "\\").lower()] = (name, raw[off : off + size])
    return out


def extract_block(text: str, kind: str, name: str) -> str | None:
    pat = re.compile(
        rf"(?im)^{kind}\s+{re.escape(name)}\s*\n(.*?)(?:^End\s*$)",
        re.S | re.M,
    )
    m = pat.search(text)
    if not m:
        return None
    return m.group(0)


def slots_of(block: str) -> dict[int, str]:
    out = {}
    for m in re.finditer(r"(?m)^\s*(\d+)\s*=\s*(\S+)", block):
        out[int(m.group(1))] = m.group(2)
    return out


def find_object_files(amap, needle: str):
    hits = []
    n = needle.lower().encode("latin-1")
    for key, (name, blob) in amap.items():
        if not key.endswith(".ini"):
            continue
        if n in blob.lower():
            hits.append(name)
    return hits


def dump_cc(label: str, path: Path):
    print("=" * 72)
    print(label, path, "exists" if path.exists() else "MISSING", path.stat().st_size if path.exists() else "")
    if not path.exists():
        return
    raw, entries = read_big(path)
    amap = by_key(raw, entries)
    print("entries", len(entries), "bytes", len(raw))

    keys_of_interest = [
        r"data\ini\commandset.ini",
        r"data\ini\commandset_factionexpansion_armies.ini",
        r"data\ini\commandset_zzzz_usapac3.ini",
        r"data\ini\commandbutton.ini",
        r"data\ini\commandbutton_usapac3.ini",
        r"data\ini\playertemplate.ini",
        r"data\ini\playertemplate_specterpatch.ini",
        r"data\ini\object\specter\united states of america\buildings\commandcenter.ini",
        r"data\ini\object\specter\patchsystems\militaryhq\militaryhq_stockfactions.ini",
        r"data\ini\object\specter\patchsystems\airdefense\usapac3.ini",
        r"data\ini\mappedimages\handcreated\usapac3_images.ini",
        r"data\ini\weapon_usapac3.ini",
    ]
    print("-- path presence --")
    for k in keys_of_interest:
        print(f"  {'YES' if k in amap else 'NO '} {k}")

    # PlayerTemplate FactionAmerica
    for pkey in (r"data\ini\playertemplate.ini", r"data\ini\playertemplate_specterpatch.ini"):
        if pkey not in amap:
            continue
        text = amap[pkey][1].decode("latin-1", "replace")
        block = extract_block(text, "PlayerTemplate", "FactionAmerica")
        print(f"\n=== PlayerTemplate FactionAmerica in {amap[pkey][0]} ===")
        if block:
            for line in block.splitlines():
                if any(x in line for x in ("PlayerTemplate", "Side", "Starting", "Playable", "End")):
                    print(line)
        else:
            print("NO FactionAmerica block")
            # maybe different formatting
            idx = text.lower().find("factionamerica")
            print("first idx", idx)
            if idx >= 0:
                print(text[idx : idx + 800])

    # AmericaCommandCenter object
    print("\n=== files mentioning Object AmericaCommandCenter ===")
    obj_hits = []
    for key, (name, blob) in amap.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin-1", "replace")
        if re.search(r"(?im)^Object\s+AmericaCommandCenter\s*$", t):
            obj_hits.append(name)
            print("OBJECT FILE", name)
            block = extract_block(t, "Object", "AmericaCommandCenter")
            if block:
                for line in block.splitlines():
                    if re.search(r"CommandSet|DisplayName|Side|BuildCost|BuildTime|KindOf|Object ", line):
                        print(" ", line.rstrip())
    if not obj_hits:
        print("NONE")

    print("\n=== files mentioning Object America_MilitaryHQ ===")
    hq_hits = []
    for key, (name, blob) in amap.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin-1", "replace")
        if re.search(r"(?im)^Object\s+America_MilitaryHQ\s*$", t):
            hq_hits.append(name)
            print("OBJECT FILE", name)
            block = extract_block(t, "Object", "America_MilitaryHQ")
            if block:
                for line in block.splitlines():
                    if re.search(r"CommandSet|DisplayName|Side|BuildCost|KindOf|Object ", line):
                        print(" ", line.rstrip())
    print("America_MilitaryHQ present:", bool(hq_hits))

    # CommandSets
    print("\n=== AmericaCommandCenterCommandSet definitions ===")
    for key, (name, blob) in amap.items():
        if "commandset" not in key:
            continue
        t = blob.decode("latin-1", "replace")
        if re.search(r"(?im)^CommandSet\s+AmericaCommandCenterCommandSet\s*$", t):
            block = extract_block(t, "CommandSet", "AmericaCommandCenterCommandSet")
            print("FILE", name)
            print(block)
            print("slots", slots_of(block or ""))
            print("has USAPAC3", "USAPAC3" in (block or ""))

    print("\n=== America_MilitaryHQCommandSet definitions ===")
    for key, (name, blob) in amap.items():
        if "commandset" not in key:
            continue
        t = blob.decode("latin-1", "replace")
        if re.search(r"(?im)^CommandSet\s+America_MilitaryHQCommandSet\s*$", t):
            block = extract_block(t, "CommandSet", "America_MilitaryHQCommandSet")
            print("FILE", name)
            print(block)
            print("slots", slots_of(block or ""))

    print("\n=== Command_ConstructUSAPAC3 ===")
    for key, (name, blob) in amap.items():
        if "commandbutton" not in key:
            continue
        t = blob.decode("latin-1", "replace")
        if "Command_ConstructUSAPAC3" in t:
            block = extract_block(t, "CommandButton", "Command_ConstructUSAPAC3")
            print("FILE", name)
            print(block)

    print("\n=== Object USAPAC3 ===")
    for key, (name, blob) in amap.items():
        if not key.endswith(".ini"):
            continue
        t = blob.decode("latin-1", "replace")
        if re.search(r"(?im)^Object\s+USAPAC3\s*$", t):
            block = extract_block(t, "Object", "USAPAC3")
            print("FILE", name)
            if block:
                for line in block.splitlines():
                    if re.search(
                        r"Object |DisplayName|Side|BuildCost|BuildTime|Prerequisites|Science|KindOf|CommandSet |ButtonImage|SelectPortrait|MaxSimultaneous",
                        line,
                    ):
                        print(" ", line.rstrip())

    print("\n=== MappedImage USAPAC3 ===")
    for key, (name, blob) in amap.items():
        t = blob.decode("latin-1", "replace")
        if re.search(r"(?im)^MappedImage\s+USAPAC3\s*$", t):
            print("FILE", name)
            print(extract_block(t, "MappedImage", "USAPAC3"))

    # duplicate CommandSet names
    print("\n=== duplicate CommandSet names across files ===")
    names = {}
    for key, (name, blob) in amap.items():
        if "commandset" not in key or not key.endswith(".ini"):
            continue
        t = blob.decode("latin-1", "replace")
        for m in re.finditer(r"(?im)^CommandSet\s+(\S+)\s*$", t):
            names.setdefault(m.group(1), []).append(name)
    dups = {k: v for k, v in names.items() if len(v) > 1}
    print("dup count", len(dups))
    for k, v in sorted(dups.items()):
        if "America" in k or "USAPAC" in k:
            print(k, v)


def dump_art(label, path):
    print("=" * 72)
    print("ART", label, path, "exists" if path.exists() else "MISSING")
    if not path.exists():
        return
    raw, entries = read_big(path)
    amap = by_key(raw, entries)
    want = [
        r"art\w3d\usapac3car.w3d",
        r"art\w3d\usapac3car_d.w3d",
        r"art\w3d\usapac3car_w.w3d",
        r"art\w3d\usapac3f.w3d",
        r"art\w3d\usapac3f_d.w3d",
        r"art\w3d\pac3mis_m.w3d",
        r"art\textures\usapac3.tga",
        r"art\textures\usapac3tb.tga",
        r"art\textures\usapac3truckmap.dds",
        r"art\textures\ampac3map.dds",
        r"art\textures\pac3missilemap.dds",
        r"art\textures\abnpatriot02.dds",
    ]
    print("entries", len(entries), "bytes", len(raw))
    for k in want:
        print(f"  {'YES' if k in amap else 'NO '} {k}")


if __name__ == "__main__":
    dump_cc("MERGED DATA", MERGED_DATA)
    dump_cc("ORIG UNIFIED DATA", ORIG_DATA)
    dump_art("MERGED ART TWO", MERGED_ART2)
    dump_art("ORIG ART TWO", ORIG_ART2)
    print("\n=== overlay CommandSet.ini AmericaCommandCenterCommandSet ===")
    text = (PATCH / "Data/INI/CommandSet.ini").read_text(encoding="latin-1")
    block = extract_block(text, "CommandSet", "AmericaCommandCenterCommandSet")
    print(block)
    print("slots", slots_of(block or ""))
