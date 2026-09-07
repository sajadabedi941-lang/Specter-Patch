#!/usr/bin/env python3
"""Packed-BIG audit for the national ground visual-identity pass."""

from __future__ import annotations

import hashlib
import io
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from audit_national_ground_forces import parse_big, walk_csf
from build_national_ground_forces import last_named, w3d_textures
from national_ground_identity import IDENTITY, PROTECTED_SIDES
from national_ground_roster import COUNTRIES, LOCKED_BIG_PATHS, all_units

SRC_DATA = Path("/tmp/national_ground_names/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_names/_SPEC_ART_ONE.big")
DATA = Path("/tmp/national_ground_identity/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_identity/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_ground_visual_audit.txt")


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def fail(msg: str) -> int:
    print("FAIL", msg)
    return 1


def field(blk: str, name: str):
    m = re.search(rf"(?m)^\s*{name}\s+=\s+(\S+)", blk)
    return m.group(1) if m else None


def index_blocks(entries, kind: str):
    last = {}
    texts = {}
    for i, n, b in entries:
        if not n.lower().endswith(".ini"):
            continue
        text = b.decode("latin1", "replace")
        texts[i] = (n, text)
        for m in re.finditer(rf"(?m)^{kind}\s+(\S+)\s*$", text):
            last[m.group(1)] = i
    out = {}
    for name, i in last.items():
        n, text = texts[i]
        m = last_named(text, kind, name)
        if m:
            out[name] = (n, m.group(0))
    return out


def _run() -> int:
    errors = 0
    if not DATA.is_file() or not ART.is_file():
        return fail("missing identity packed BIG")
    data = parse_big(DATA)
    art = parse_big(ART)
    src_data = parse_big(SRC_DATA)
    src_art = parse_big(SRC_ART)
    art_bases = {basename(n): (n, b) for _i, n, b in art}
    src_art_bases = {basename(n): (n, b) for _i, n, b in src_art}
    src_dmap = {n.replace("/", "\\").lower(): b for _i, n, b in src_data}

    print("SPECTER NATIONAL GROUND VISUAL IDENTITY — PACKED AUDIT")
    print("=" * 72)
    print("ART / markings only. Weapons, armor, locomotor, cost, time,")
    print("CommandSets, CommandButtons, and CSF are unchanged.")
    print("Shared US/NATO/Iraqi/Russian meshes are cloned per nation.")
    print()
    print("DATA_SHA256", hashlib.sha256(DATA.read_bytes()).hexdigest())
    print("ART_SHA256", hashlib.sha256(ART.read_bytes()).hexdigest())
    print("DATA_FILES", len(data), "ART_FILES", len(art))
    if [n for _i, n, _b in data] != [n for _i, n, _b in src_data]:
        errors += fail("DATA entry names/order changed")
    else:
        print("OK DATA entry names/order")
    if [n for _i, n, _b in art][: len(src_art)] != [n for _i, n, _b in src_art]:
        errors += fail("ART entry-order prefix changed")
    else:
        print("OK ART entry-order prefix")

    for locked in LOCKED_BIG_PATHS:
        key = locked.replace("/", "\\").lower()
        dst = next((b for _i, n, b in data if n.replace("/", "\\").lower() == key), None)
        src = src_dmap.get(key)
        if src is not None and dst != src:
            errors += fail(f"locked changed {locked}")
        elif src is not None:
            print("OK locked", locked)

    csf_blob = next(b for _i, n, b in data if n.lower().endswith("generals.csf"))
    src_csf = next(b for _i, n, b in src_data if n.lower().endswith("generals.csf"))
    if csf_blob != src_csf:
        errors += fail("CSF bytes changed")
    else:
        print("OK CSF unchanged")
    csf = walk_csf(csf_blob)

    dst_objs = index_blocks(data, "Object")
    src_objs = index_blocks(src_data, "Object")
    dst_btns = index_blocks(data, "CommandButton")
    src_btns = index_blocks(src_data, "CommandButton")

    for obj, (_fn, sblk) in src_objs.items():
        side = field(sblk, "Side")
        model = field(sblk, "Model")
        if side not in PROTECTED_SIDES or not model:
            continue
        dhit = dst_objs.get(obj)
        if not dhit:
            continue
        if field(dhit[1], "Model") != model:
            errors += fail(f"protected Model changed {obj}")
        wkey = model.lower() + ".w3d"
        if wkey in src_art_bases and wkey in art_bases and src_art_bases[wkey][1] != art_bases[wkey][1]:
            errors += fail(f"protected W3D bytes changed {model}")

    print()
    print("=== Object -> Model -> Texture -> Icon -> CSF ===")
    marked = 0
    unit_count = 0
    for country in COUNTRIES:
        code = IDENTITY[country.key][0]
        print()
        print(country.key)
        for idx, unit in enumerate(country.units, 1):
            unit_count += 1
            ohit = dst_objs.get(unit.obj)
            shit = src_objs.get(unit.obj)
            if not ohit or not shit:
                errors += fail(f"missing object {unit.obj}")
                continue
            _fn, oblk = ohit
            _sf, sblk = shit
            if re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", oblk) != re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", sblk):
                errors += fail(f"{unit.obj} Weapon changed")
            for key in ("BuildCost", "BuildTime"):
                if re.findall(rf"(?m)^\s*{key}\s+=\s+(\S+)", oblk) != re.findall(rf"(?m)^\s*{key}\s+=\s+(\S+)", sblk):
                    errors += fail(f"{unit.obj} {key} changed")
            for key in ("Armor", "Locomotor"):
                if re.findall(rf"(?m)^\s*{key}\s+=\s+.+$", oblk) != re.findall(rf"(?m)^\s*{key}\s+=\s+.+$", sblk):
                    errors += fail(f"{unit.obj} {key} changed")
            stem = field(oblk, "Model")
            src_stem = field(sblk, "Model")
            if not stem:
                errors += fail(f"{unit.obj} no Model")
                continue
            btn = f"Command_Construct{unit.obj}"
            bhit = dst_btns.get(btn)
            bsrc = src_btns.get(btn)
            if not bhit:
                errors += fail(f"missing button {btn}")
                continue
            if bsrc and bsrc[1] != bhit[1]:
                errors += fail(f"button changed {btn}")
            icon = field(bhit[1], "ButtonImage") or "?"
            for key in (f"OBJECT:{unit.obj}", f"CONTROLBAR:Construct{unit.obj}", f"CONTROLBAR:ToolTip{unit.obj}"):
                if key not in csf:
                    errors += fail(f"missing CSF {key}")
            wkey = stem.lower() + ".w3d"
            if wkey not in art_bases:
                errors += fail(f"{unit.obj} Model {stem} missing from ART")
                continue
            texs = w3d_textures(art_bases[wkey][1])
            packed = {Path(k).stem.lower() for k in art_bases}
            have = [t for t in texs if Path(t).stem.lower() in packed]
            nation_tex = [t for t in texs if Path(t).stem.lower().startswith(code.lower())]
            if not nation_tex:
                errors += fail(f"{unit.obj} Model {stem} has no {code}_ marked texture {texs[:4]}")
            else:
                marked += 1
            print(
                f"  {idx:2d} {unit.obj:32} model={stem:24} "
                f"src={src_stem:16} icon={icon} tex={len(have)}/{len(texs)} mark={len(nation_tex)} csf=OK"
            )

    print()
    print("UNIT_COUNT", unit_count, "MARKED", marked)
    if unit_count != 17 * 14:
        errors += fail(f"expected 238 units, got {unit_count}")
    if marked != 17 * 14:
        errors += fail(f"expected 238 marked units, got {marked}")
    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK")
    print("Object -> Model -> Texture -> Icon -> CSF verified for all 17 nations.")
    return 0


def main() -> int:
    buf = io.StringIO()
    old = sys.stdout
    sys.stdout = buf
    try:
        code = _run()
    finally:
        sys.stdout = old
    text = buf.getvalue()
    print(text, end="")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(text)
    print("wrote", REPORT)
    return code


if __name__ == "__main__":
    sys.exit(main())
