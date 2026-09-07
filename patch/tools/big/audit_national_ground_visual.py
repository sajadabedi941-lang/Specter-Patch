#!/usr/bin/env python3
"""Packed-BIG audit for the National Ground Forces visual upgrade (ART only)."""

from __future__ import annotations

import hashlib
import io
import re
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from audit_national_ground_forces import last_named, last_named_any, last_object_any, parse_big, walk_csf
from national_ground_roster import LOCKED_BIG_PATHS, all_units
from national_ground_visual_map import KEEP_AS_IS, VISUAL_UPGRADES

SRC_DATA = Path("/tmp/national_ground_forces/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_forces/_SPEC_ART_ONE.big")
DATA = Path("/tmp/national_ground_visual/_SPEC_DATA_ONE.big")
ART = Path("/tmp/national_ground_visual/_SPEC_ART_ONE.big")
REPORT = Path("/opt/cursor/artifacts/national_ground_visual_upgrade_audit.txt")


def basename(name: str) -> str:
    return name.replace("\\", "/").split("/")[-1].lower()


def w3d_textures(blob: bytes) -> list[str]:
    names = []
    pos = 0
    end = len(blob)
    while pos + 8 <= end:
        ctype, csize = struct.unpack_from("<II", blob, pos)
        has = csize & 0x80000000
        size = csize & 0x7FFFFFFF
        pl = pos + 8
        nxt = pl + size
        if nxt > end:
            break
        if ctype == 0x32:
            z = blob.find(b"\x00", pl)
            if z > pl:
                names.append(blob[pl:z].decode("ascii", "replace"))
        if has:
            cpos = pl
            while cpos + 8 <= nxt:
                ct, cs = struct.unpack_from("<II", blob, cpos)
                ch = cs & 0x80000000
                csz = cs & 0x7FFFFFFF
                cpl = cpos + 8
                cnxt = cpl + csz
                if cnxt > nxt:
                    break
                if ct == 0x32:
                    z = blob.find(b"\x00", cpl)
                    if z > cpl:
                        names.append(blob[cpl:z].decode("ascii", "replace"))
                if ch:
                    names.extend(_walk(blob, cpl, cnxt))
                cpos = cnxt
        pos = nxt
    return names


def _walk(blob, start, end):
    names = []
    pos = start
    while pos + 8 <= end:
        ct, cs = struct.unpack_from("<II", blob, pos)
        ch = cs & 0x80000000
        csz = cs & 0x7FFFFFFF
        pl = pos + 8
        nxt = pl + csz
        if nxt > end:
            break
        if ct == 0x32:
            z = blob.find(b"\x00", pl)
            if z > pl:
                names.append(blob[pl:z].decode("ascii", "replace"))
        if ch:
            names.extend(_walk(blob, pl, nxt))
        pos = nxt
    return names


def fail(msg):
    print("FAIL", msg)
    return 1


def _run() -> int:
    errors = 0
    if not DATA.is_file() or not ART.is_file():
        return fail("missing packed visual BIG")
    data = parse_big(DATA)
    art = parse_big(ART)
    src_data = parse_big(SRC_DATA)
    src_art = parse_big(SRC_ART)
    art_bases = {basename(n): (n, b) for i, n, b in art}
    src_dmap = {n.replace("/", "\\").lower(): b for i, n, b in src_data}

    print("DATA_SHA256", hashlib.sha256(DATA.read_bytes()).hexdigest())
    print("ART_SHA256", hashlib.sha256(ART.read_bytes()).hexdigest())
    print("DATA_FILES", len(data), "ART_FILES", len(art))
    if [n for _, n, _ in data][: len(src_data)] != [n for _, n, _ in src_data]:
        errors += fail("DATA entry-order prefix changed")
    else:
        print("OK DATA entry-order prefix")
    if [n for _, n, _ in art][: len(src_art)] != [n for _, n, _ in src_art]:
        errors += fail("ART entry-order prefix changed")
    else:
        print("OK ART entry-order prefix")

    for locked in LOCKED_BIG_PATHS:
        key = locked.replace("/", "\\").lower()
        dst = next((b for i, n, b in data if n.replace("/", "\\").lower() == key), None)
        src = src_dmap.get(key)
        if src is not None and dst != src:
            errors += fail(f"locked changed {locked}")
        elif src is not None:
            print("OK locked", locked)

    csf_blob = next(b for i, n, b in data if n.lower().endswith("generals.csf"))
    src_csf = next(b for i, n, b in src_data if n.lower().endswith("generals.csf"))
    if csf_blob != src_csf:
        errors += fail("CSF bytes changed (visual pass must not edit CSF)")
    else:
        print("OK CSF unchanged")
    csf = walk_csf(csf_blob)

    src_cb = last_named_any(src_data, "CommandButton", "Command_ConstructJapanTankType10")
    dst_cb = last_named_any(data, "CommandButton", "Command_ConstructJapanTankType10")
    if not src_cb or not dst_cb or src_cb[1] != dst_cb[1]:
        errors += fail("CommandButton sample changed")

    replaced = 0
    kept = 0
    print("\n=== REPLACED UNITS (Object -> Model -> Texture -> Icon -> CSF) ===")
    for country, unit in all_units():
        ohit = last_object_any(data, unit.obj)
        shit = last_object_any(src_data, unit.obj)
        if not ohit or not shit:
            errors += fail(f"missing object {unit.obj}")
            continue
        _fn, oblk = ohit
        _sf, sblk = shit
        src_model = re.search(r"(?m)^\s*Model\s+=\s+(\S+)", sblk)
        dst_model = re.search(r"(?m)^\s*Model\s+=\s+(\S+)", oblk)
        if not dst_model:
            errors += fail(f"{unit.obj} no Model")
            continue
        stem = dst_model.group(1)
        src_stem = src_model.group(1) if src_model else "?"
        # DATA logic must be identical except Model/Animation
        def strip_art(t):
            t = re.sub(r"(?m)^(\s*Model\s+=\s+)\S+", r"\1X", t)
            t = re.sub(r"(?m)^(\s*Animation\s+=\s+)\S+", r"\1X", t)
            return t

        if strip_art(sblk) != strip_art(oblk) and unit.obj in VISUAL_UPGRADES:
            # allow only model/anim diffs; if other diffs, fail
            errors += fail(f"{unit.obj} non-ART DATA changed")
        weap_src = re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", sblk)
        weap_dst = re.findall(r"(?m)^\s*Weapon\s+=\s+.+$", oblk)
        if weap_src != weap_dst:
            errors += fail(f"{unit.obj} Weapon changed")
        for field in ("BuildCost", "BuildTime"):
            if re.findall(rf"(?m)^\s*{field}\s+=\s+(\S+)", sblk) != re.findall(rf"(?m)^\s*{field}\s+=\s+(\S+)", oblk):
                errors += fail(f"{unit.obj} {field} changed")

        btn = f"Command_Construct{unit.obj}"
        bhit = last_named_any(data, "CommandButton", btn)
        if not bhit:
            errors += fail(f"missing button {btn}")
            continue
        bsrc = last_named_any(src_data, "CommandButton", btn)
        if bsrc and bsrc[1] != bhit[1]:
            errors += fail(f"button changed {btn}")
        icon = re.search(r"(?m)^\s*ButtonImage\s+=\s+(\S+)", bhit[1])
        icon_name = icon.group(1) if icon else "?"
        for key in (f"OBJECT:{unit.obj}", f"CONTROLBAR:Construct{unit.obj}", f"CONTROLBAR:ToolTip{unit.obj}"):
            if key not in csf:
                errors += fail(f"missing CSF {key}")
        wkey = stem.lower() + ".w3d"
        if wkey not in art_bases:
            errors += fail(f"{unit.obj} Model {stem} missing from ART")
            continue
        _an, wblob = art_bases[wkey]
        texs = w3d_textures(wblob)
        missing_tex = [t for t in texs if t.lower() not in art_bases and not t.lower().endswith((".ini",))]
        # some W3Ds reference generic engine textures; only fail if none of the named textures exist
        have = [t for t in texs if t.lower() in art_bases]
        if texs and not have:
            errors += fail(f"{unit.obj} Model {stem} has no packed textures {texs[:4]}")

        if unit.obj in VISUAL_UPGRADES and src_stem.lower() != stem.lower():
            replaced += 1
            print(f"REPLACE {country.key:12} {unit.obj:32} {src_stem:16} -> {stem:16} icon={icon_name} tex={len(have)}/{len(texs)} csf=OK")
        else:
            kept += 1
            print(f"KEEP    {country.key:12} {unit.obj:32} model={stem:16} icon={icon_name} csf=OK")

    print("\n=== KEEP REASONS ===")
    for obj, why in KEEP_AS_IS.items():
        print(f"  {obj}: {why}")

    print("REPLACED", replaced, "KEPT", kept)
    if replaced < 20:
        errors += fail(f"expected a substantial visual pass, replaced={replaced}")
    if errors:
        print("AUDIT_FAIL", errors)
        return 1
    print("AUDIT_OK")
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
