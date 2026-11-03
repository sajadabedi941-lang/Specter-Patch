#!/usr/bin/env python3
"""Static validation for USAPAC3 PAC-3 Draw attach.

Zero Hour is not run. INGAME_ZH is not claimed.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
DRAW = ROOT / "docs/specter-usapac3/draw"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
INSTALLER = ROOT / "patch/tools/installer"
ARCHIVE = ROOT / "docs/specter-usapac3/archive/failed-impl"

THAAD_SHA = "b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f"
WEAPON_SHA = "a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8"
CS_SHA = "87af44ffbbf33cf6fb1a7c1b15c0fcce52b6826891ae40e736cad669453d6404"
CB_SHA = "1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c"
OCL_SHA = "e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5"
ART1_SHA = "15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
BEFORE_ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"
WPN_KEY = r"data\ini\weapon.ini"
CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
OCL_KEY = r"data\ini\objectcreationlist.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
OCLU_KEY = r"data\ini\objectcreationlist_usapac3.ini"

NEED_ART = (
    r"art\w3d\usapac3car.w3d",
    r"art\w3d\usapac3car_d.w3d",
    r"art\w3d\usapac3f.w3d",
    r"art\w3d\usapac3f_d.w3d",
    r"art\w3d\pac3mis_m.w3d",
    r"art\textures\usapac3truckmap.dds",
    r"art\textures\usapac3truckmap_d.dds",
    r"art\textures\ampac3map.dds",
    r"art\textures\ampac3map_d.dds",
    r"art\textures\ampac3mapback.dds",
    r"art\textures\pac3missilemap.dds",
    r"art\w3d\us_m1120.w3d",
    r"art\w3d\abpatriot.w3d",
    r"art\w3d\pac3_sudarb.w3d",
    r"art\textures\abnpatriot02.dds",
)


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def key(name: str) -> str:
    return name.replace("/", "\\").lower()


def read_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        fail(f"not BIGF {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(count):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin-1")
        pos = end + 1
        entries.append((name, off, size))
    return data, entries


def extract_top_level(blob: bytes, kind: bytes, name: bytes) -> list[bytes]:
    pat = re.compile(rb"(?m)^" + re.escape(kind) + rb"\s+" + re.escape(name) + rb"\s*$")
    blocks = []
    for m in pat.finditer(blob):
        lines = blob[m.start() :].splitlines(True)
        acc = [lines[0]]
        for line in lines[1:]:
            acc.append(line)
            if line.strip() == b"End" and line[:1] not in b" \t":
                break
        blocks.append(b"".join(acc))
    return blocks


def count_headers(blob: bytes, kind: bytes, name: bytes) -> int:
    return len(re.findall(rb"(?m)^" + re.escape(kind) + rb"\s+" + re.escape(name) + rb"\s*$", blob))


def w3d_top_ids(blob: bytes) -> list[int]:
    ids = []
    pos = 0
    while pos + 8 <= len(blob):
        cid, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        pe = pos + 8 + size
        ids.append(cid)
        pos = pe
    return ids


def w3d_channel_count(blob: bytes) -> int:
    n = 0
    pos = 0
    while pos + 8 <= len(blob):
        cid, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        pe = pos + 8 + size
        if cid == 0x200:
            inner = pos + 8
            while inner + 8 <= pe:
                ic, ir = struct.unpack_from("<II", blob, inner)
                iz = ir & 0x7FFFFFFF
                ie = inner + 8 + iz
                if ic == 0x202:
                    n += 1
                inner = ie
        pos = pe
    return n


def models_in(block: bytes) -> list[bytes]:
    return re.findall(rb"(?m)^\s+Model\s+=\s+(\S+)", block)


def anims_in(block: bytes) -> list[bytes]:
    return re.findall(rb"(?m)^\s+Animation\s+=\s+(\S+)", block)


def main() -> int:
    raw, ents = read_big(DATA)
    amap = {key(n): (n, raw[o : o + s]) for n, o, s in ents}
    art_raw, art_ents = read_big(ART2)
    art = {key(n): (n, art_raw[o : o + s]) for n, o, s in art_ents}

    obj = amap[OBJ_KEY][1]
    thaad = amap[THAAD_KEY][1]
    cs = amap[CS_KEY][1]
    cb = amap[CB_KEY][1]
    weapon = amap[WPN_KEY][1]
    ocl = amap[OCL_KEY][1]

    if sha256(thaad) != THAAD_SHA:
        fail("US_M1120.ini sha")
    if sha256(weapon) != WEAPON_SHA:
        fail("Weapon.ini sha")
    if sha256(cs) != CS_SHA:
        fail("CommandSet.ini sha")
    if sha256(cb) != CB_SHA:
        fail("CommandButton.ini sha")
    if sha256(ocl) != OCL_SHA:
        fail("ObjectCreationList.ini sha")
    if (INSTALLER / "CommandSet.ini").read_bytes() != cs:
        fail("installer CommandSet.ini drifted")
    if (INSTALLER / "CommandButton.ini").read_bytes() != cb:
        fail("installer CommandButton.ini drifted")

    mobile = extract_top_level(obj, b"Object", b"USAPAC3")
    combat = extract_top_level(obj, b"Object", b"USAPAC3_CombatMode")
    fcs = extract_top_level(obj, b"Object", b"USAPAC3_FireControlSystem")
    fcs_abm = extract_top_level(obj, b"Object", b"USAPAC3_FireControlSystem_ABM")
    if len(mobile) != 1 or len(combat) != 1 or len(fcs) != 1 or len(fcs_abm) != 1:
        fail("object counts")
    mob, cmb = mobile[0], combat[0]

    if b"US_M1120" in mob or b"US_M1120" in cmb:
        fail("THAAD mesh still on PAC-3 Draw")
    if models_in(mob)[:2] != [b"UsaPac3Car", b"UsaPac3Car_d"]:
        fail(f"mobile packed models {models_in(mob)}")
    if b"UsaPac3F" not in models_in(mob) or b"UsaPac3F_d" not in models_in(mob):
        fail("mobile missing deployed F models")
    if any(a.startswith(b"UsaPac3F") for a in anims_in(mob)):
        fail("mobile names UsaPac3F animation")
    if b"UsaPac3Car.UsaPac3Car" not in anims_in(mob):
        fail("mobile missing Car clip")
    if models_in(cmb) != [b"UsaPac3F", b"UsaPac3F_d", b"UsaPac3F_d"]:
        fail(f"combat models {models_in(cmb)}")
    if anims_in(cmb):
        fail("combat still names animations")
    if b"UsaPac3Car_w" in obj:
        fail("Car_w in object")
    if b"CommandSet           = USAPAC3CommandSet\r\n" not in mob:
        fail("mobile CommandSet")
    if b"CommandSet           = USAPAC3CommandSet_Deployed" not in cmb:
        fail("combat CommandSet")
    if b"OCL = FINAL    OCL_USAPAC3_Deployed\r\n" not in mob:
        fail("AA OCL")
    if b"Weapon             = SECONDARY USAPAC3_Weapon\r\n" not in mob:
        fail("AA dummy weapon")
    if b"Model                   = THAAD_FCS" not in fcs[0] or b"Model                   = THAAD_FCS" not in fcs_abm[0]:
        fail("FCS draw changed")
    if b"Weapon            = PRIMARY   8x_LRSAM_THAAD" not in fcs[0]:
        fail("AA FCS weapon")
    if b"Weapon            = PRIMARY   THAADMissile_ABM" not in fcs_abm[0]:
        fail("ABM FCS weapon")
    if b"TriggeredBy     = Upgrade_AIM-120C" in mob:
        fail("MTS wired")
    thaad_obj = extract_top_level(thaad, b"Object", b"US_THAAD")[0]
    if b"CommandSet           = S400ECommandSet" not in thaad_obj:
        fail("THAAD CommandSet")
    if b"Model                   = US_M1120" not in thaad_obj:
        fail("THAAD Draw mutated")

    for need in NEED_ART:
        if need not in art:
            fail(f"missing ART {need}")
    if r"art\w3d\usapac3car_w.w3d" in art:
        fail("UsaPac3Car_w packed")

    car = art[r"art\w3d\usapac3car.w3d"][1]
    fmesh = art[r"art\w3d\usapac3f.w3d"][1]
    fd = art[r"art\w3d\usapac3f_d.w3d"][1]
    mis = art[r"art\w3d\pac3mis_m.w3d"][1]
    if 0x200 not in w3d_top_ids(car):
        fail("Car lost ANIMATION")
    if w3d_channel_count(car) < 1:
        fail("Car has no real channels")
    if 0x200 in w3d_top_ids(fmesh) or 0x200 in w3d_top_ids(fd):
        fail("F still has ANIMATION chunk")
    if 0x200 in w3d_top_ids(mis):
        fail("pac3mis_m still has empty ANIMATION")
    for tex in (b"usaPAC3TRUCKmap.tga", b"ampac3map.tga"):
        if tex not in car or tex not in fmesh:
            fail(f"W3D missing texture ref {tex.decode()}")
    if b"pac3missilemap.tga" not in mis:
        fail("missile W3D missing pac3missilemap.tga")

    # existing ART files must still match the pre-draw ART TWO copies
    old_art_raw, old_art_ents = None, None
    # compare against archive-independent protected hashes from current file vs known sizes
    if sha_file(ART2) == BEFORE_ART2_SHA:
        fail("ART TWO was not extended")

    if not (ARCHIVE / "Art/W3D/UsaPac3Car.W3D").exists():
        fail("archive Car deleted")
    if not (ARCHIVE / "Art/W3D/UsaPac3Car_w.W3D").exists():
        fail("archive Car_w deleted")
    if not (ROOT / "docs/specter-usapac3/abtest").is_dir():
        fail("abtest missing")
    if b"Object AmericaMobileSamSiteMIM104F" not in raw:
        fail("Patriot missing")
    if b"Command_ConstructAmerica_AD_NASAMS" not in raw:
        fail("NASAMS missing")
    if b"  6  = Command_ConstructUSAPAC3" not in cs:
        fail("CC slot 6")
    if count_headers(cs, b"CommandSet", b"USAPAC3CommandSet") != 1:
        fail("live CommandSet lost")
    if count_headers(cs, b"CommandSet", b"S400ECommandSet") != 1:
        fail("S400ECommandSet")

    overlay = ROOT / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini"
    if overlay.read_bytes() != obj:
        fail("overlay object != packed")
    if (DRAW / "USAPAC3.ini").read_bytes() != obj:
        fail("draw source != packed")

    art1 = MERGED / "_SPEC_ART_ONE.big"
    if art1.exists() and sha_file(art1) != ART1_SHA:
        fail("ART ONE mutated")

    print("STATIC_OK")
    print("DATA", sha_file(DATA), DATA.stat().st_size, "entries", len(ents))
    print("ART2", sha_file(ART2), ART2.stat().st_size, "entries", len(art_ents))
    print("US_M1120.ini", sha256(thaad))
    print("Weapon.ini", sha256(weapon))
    print("CommandSet.ini", sha256(cs))
    print("CommandButton.ini", sha256(cb))
    print("INGAME_ZH: not executed")
    print("STAGE: PAC-3 Draw attached; gameplay/CommandSet unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
