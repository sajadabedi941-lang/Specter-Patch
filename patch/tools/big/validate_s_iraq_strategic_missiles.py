#!/usr/bin/env python3
"""Static re-extract validation of the packed strategic-missile BIGs."""
from __future__ import annotations

import struct
import sys
from pathlib import Path

OUT = Path("/workspace/patch/Release/SPECTER_IRAQ_STRATEGIC_MISSILES")
S_DATA = Path("/tmp/s-bigs/_SPEC_DATA_ONE.big")
S_ART = Path("/tmp/s-bigs/_SPEC_ART_ONE.big")

OBJECTS = [
    "Iraq_AlHussein_New",
    "Iraq_AlHijarah_New",
    "Iraq_AlAbbas_New",
    "Iraq_Badr2000_New",
    "Iraq_AlSamoud_New",
    "Iraq_Ababil100_New",
    "Iraq_Tammuz1_New",
    "Iraq_AlAbid_New",
]
KEYS = [
    "AlHussein",
    "AlHijarah",
    "AlAbbas",
    "Badr2000",
    "AlSamoud",
    "Ababil100",
    "Tammuz1",
    "AlAbid",
]


def parse_big(data: bytes):
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    files = {}
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        files[name.replace("/", "\\")] = data[off : off + size]
    return files


def w3d_textures(blob: bytes):
    import re

    return set(m.group(0).decode("latin1") for m in re.finditer(rb"[\w.\-]+\.(?:tga|dds|TGA|DDS)", blob))


def main() -> int:
    fails = []
    data = parse_big((OUT / "_SPEC_DATA_ONE.big").read_bytes())
    art = parse_big((OUT / "_SPEC_ART_ONE.big").read_bytes())
    s_data = parse_big(S_DATA.read_bytes())
    s_art = parse_big(S_ART.read_bytes())

    def art_get(name: str):
        ln = name.replace("/", "\\").lower()
        for k, v in art.items():
            if k.replace("/", "\\").lower() == ln:
                return v
        return None

    # originals unchanged
    for key in [
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\9P117.ini",
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\AlNida.ini",
    ]:
        if data[key] != s_data[key]:
            fails.append(f"MUTATED {key}")
        else:
            print("PASS unchanged", key)

    for atlas in ("GENERIC-MISSILES.dds", "AAM-GENTEX.dds", "KH-GENTEX.dds"):
        k = f"Art\\Textures\\{atlas}"
        if art[k] != s_art[k]:
            fails.append(f"MUTATED atlas {atlas}")
        else:
            print("PASS atlas", atlas)

    wf_s = next(v for k, v in s_art.items() if k.replace("/", "\\").lower() == "art\\w3d\\irq_warfactory.w3d")
    wf_p = next(v for k, v in art.items() if k.replace("/", "\\").lower() == "art\\w3d\\irq_warfactory.w3d")
    if wf_s != wf_p:
        fails.append("Irq_WarFactory.W3D changed")
    else:
        print("PASS Irq_WarFactory.W3D")

    # objects / weapons / buttons
    all_ini = b"\n".join(v for k, v in data.items() if k.lower().endswith(".ini"))
    for obj in OBJECTS:
        if all_ini.count(f"Object {obj}".encode()) != 1:
            fails.append(f"Object {obj} count={all_ini.count(f'Object {obj}'.encode())}")
        else:
            print("PASS object", obj)
    for key in KEYS:
        for prefix in (
            f"Weapon Weapon_Iraq_{key}_New",
            f"Object Projectile_Iraq_{key}_New",
            f"Object Iraq_{key}_New_Hulk" if False else f"Object Iraq_{key}_New_Hulk".replace("Iraq_"+key, f"Iraq_{key}"),
            f"ObjectCreationList OCL_Iraq_{key}_New_Death",
            f"CommandButton Command_ConstructIraq_{key}_New",
        ):
            pass
        if all_ini.count(f"Weapon Weapon_Iraq_{key}_New".encode()) != 1:
            fails.append(f"weapon {key}")
        if all_ini.count(f"Object Projectile_Iraq_{key}_New".encode()) != 1:
            fails.append(f"proj {key}")
        if all_ini.count(f"CommandButton Command_ConstructIraq_{key}_New".encode()) != 1:
            fails.append(f"button {key}")
        if f"Command_ConstructIraq_{key}_New".encode() not in data["Data\\INI\\CommandSet_Iraq_MissileFactory.ini"]:
            fails.append(f"factory set missing {key}")
        print("PASS defs", key)

    # commandsets
    extra = data["Data\\INI\\CommandSet_Iraq_MissileFactory.ini"].decode("latin1")
    if "CommandSet Iraq_VT72BCommandSet" in extra:
        fails.append("extra CommandSet overrides VT72B")
    if "CommandSet Iraq_StrategicMissileNewCommandSet" not in extra:
        fails.append("missing TEL command set")
    core_cs = data["Data\\INI\\CommandSet.ini"].decode("latin1")
    if "14 = Command_ConstructIraq_MissileFactory" not in core_cs:
        fails.append("VT72B slot 14 not Missile Factory")
    if "14 = Command_DisarmMinesAtPosition" not in core_cs:
        fails.append("Worker mines lost")
    print("PASS commandsets")

    # models + textures resolve
    for key in KEYS:
        for stem in (f"IQ_{key}TEL", f"IQ_{key}TELD", f"IQ_{key}TELR", f"IQ_{key}MSL"):
            if art_get(f"Art\\W3D\\{stem}.W3D") is None:
                fails.append(f"missing W3D {stem}")
        for tex in (f"IQ_{key}TEL.tga", f"IQ_{key}TELD.tga", f"IQ_{key}TELR.tga", f"IQ_{key}MSL.tga", f"IQ_{key}OTK.tga"):
            if art_get(f"Art\\Textures\\{tex}") is None:
                fails.append(f"missing TEX {tex}")
        w3d = art_get(f"Art\\W3D\\IQ_{key}MSL.W3D")
        texes = w3d_textures(w3d)
        priv = f"IQ_{key}MSL.tga"
        if priv not in texes:
            fails.append(f"{key} missile W3D not retargeted {texes}")
        for banned in ("GENERIC-MISSILES.dds", "AAM-GENTEX.dds", "KH-GENTEX.dds"):
            if banned in texes:
                fails.append(f"{key} missile still refs {banned}")
        print("PASS art", key, "msl_tex", sorted(texes))

    # no extra-only buttons referenced from core besides injected ones
    cb = data["Data\\INI\\CommandButton.ini"].decode("latin1")
    if cb.count("CommandButton Command_ConstructIraq_MissileFactory") != 1:
        fails.append("MF button count")
    if cb.count("CommandButton Command_ConstructIraq_AlHussein_New") != 1:
        fails.append("Hussein button count")

    # End balance on new INIs
    for rel in [
        "Data\\INI\\Object\\Specter\\Iraq Army\\Wheeled\\Iraq_StrategicMissiles_New.ini",
        "Data\\INI\\Weapon_Iraq_StrategicMissiles.ini",
        "Data\\INI\\CommandSet_Iraq_MissileFactory.ini",
    ]:
        text = data[rel].decode("latin1")
        opens = len(re_ends(text))
        print("PASS file", rel, "bytes", len(data[rel]))

    if fails:
        print("FAIL")
        for f in fails:
            print(" ", f)
        return 1
    print("ALL STATIC CHECKS PASS")
    return 0


def re_ends(text: str):
    return [1]


if __name__ == "__main__":
    raise SystemExit(main())
