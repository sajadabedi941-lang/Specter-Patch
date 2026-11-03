#!/usr/bin/env python3
"""PAC-3 appearance stage: attach archive TEL meshes to Object USAPAC3 Draw.

Does not rewrite CommandSet.ini, CommandButton.ini, Weapon.ini, OCL files,
S400ECommandSet, US_M1120.ini, FCS modules, Deploy/Pack behaviors, Patriot,
NASAMS, ART ONE, or existing ART TWO entries. UsaPac3Car_w is not packed.
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
ARCHIVE = ROOT / "docs/specter-usapac3/archive/failed-impl"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"

BEFORE_DATA_SHA = "a8a4eb2f31976a9aacc1b9a716de876b349a69a9bce8859daae301c454a4f7a8"
BEFORE_ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
THAAD_SHA = "b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f"
WEAPON_SHA = "a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8"
CS_SHA = "87af44ffbbf33cf6fb1a7c1b15c0fcce52b6826891ae40e736cad669453d6404"
CB_SHA = "1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c"
OCL_SHA = "e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5"

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"
WPN_KEY = r"data\ini\weapon.ini"
CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
OCL_KEY = r"data\ini\objectcreationlist.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
OCLU_KEY = r"data\ini\objectcreationlist_usapac3.ini"

KEEP_ART = {
    r"art\w3d\us_m1120.w3d": None,
    r"art\w3d\us_m1120d.w3d": None,
    r"art\w3d\us_m1120_a.w3d": None,
    r"art\w3d\us_m1120_ad.w3d": None,
    r"art\w3d\abpatriot.w3d": None,
    r"art\w3d\pac3_sudarb.w3d": None,
    r"art\textures\abnpatriot02.dds": None,
}

ART_ADD = [
    (r"Art\W3D\UsaPac3Car.W3D", ARCHIVE / "Art/W3D/UsaPac3Car.W3D", False),
    (r"Art\W3D\UsaPac3Car_d.W3D", ARCHIVE / "Art/W3D/UsaPac3Car_d.W3D", False),
    (r"Art\W3D\UsaPac3F.W3D", ARCHIVE / "Art/W3D/UsaPac3F.W3D", False),
    (r"Art\W3D\UsaPac3F_d.W3D", ARCHIVE / "Art/W3D/UsaPac3F_d.W3D", False),
    (r"Art\W3D\pac3mis_m.W3D", ARCHIVE / "Art/W3D/pac3mis_m.W3D", True),
    (r"Art\Textures\usaPAC3TRUCKmap.dds", ARCHIVE / "Art/Textures/usaPAC3TRUCKmap.dds", False),
    (r"Art\Textures\usaPAC3TRUCKmap_d.dds", ARCHIVE / "Art/Textures/usaPAC3TRUCKmap_d.dds", False),
    (r"Art\Textures\ampac3map.dds", ARCHIVE / "Art/Textures/ampac3map.dds", False),
    (r"Art\Textures\ampac3map_d.dds", ARCHIVE / "Art/Textures/ampac3map_d.dds", False),
    (r"Art\Textures\ampac3mapBaCK.dds", ARCHIVE / "Art/Textures/ampac3mapBaCK.dds", False),
    (r"Art\Textures\pac3missilemap.dds", ARCHIVE / "Art/Textures/pac3missilemap.dds", False),
]

HEADER = (
    b"; SPECTER PATCH - USAPAC3 independent functional stage 1.\r\n"
    b"; Unique CommandSet / Deploy OCL / CombatMode / FireControlSystem.\r\n"
    b"; Draw uses archive PAC-3 TEL meshes. Does not redefine Object US_THAAD.\r\n"
    b"\r\n"
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


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin-1")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin-1") + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def strip_animation(blob: bytes) -> bytes:
    out = bytearray()
    pos = 0
    removed = 0
    while pos + 8 <= len(blob):
        cid, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        pe = pos + 8 + size
        if pe > len(blob):
            fail("truncated W3D chunk")
        if cid == 0x200:
            removed += 1
            pos = pe
            continue
        out += blob[pos:pe]
        pos = pe
    if pos != len(blob):
        fail("trailing W3D bytes")
    if removed == 0:
        return blob
    if removed != 1:
        fail(f"expected one ANIMATION container, removed {removed}")
    return bytes(out)


def w3d_has_anim(blob: bytes) -> bool:
    pos = 0
    while pos + 8 <= len(blob):
        cid, raw = struct.unpack_from("<II", blob, pos)
        size = raw & 0x7FFFFFFF
        pe = pos + 8 + size
        if cid == 0x200:
            return True
        pos = pe
    return False


def patch_object(obj: bytes) -> bytes:
    text = obj
    while text.startswith(b";") or text.startswith(b"\r\n"):
        nl = text.find(b"\n")
        if nl < 0:
            break
        line = text[: nl + 1]
        if line.startswith(b"Object "):
            break
        if line.startswith(b";") or line.strip() == b"":
            text = text[nl + 1 :]
            continue
        break
    if not text.startswith(b"Object USAPAC3"):
        fail("object header")

    repls = [
        (
            b"    ConditionState            = DEPLOYED\r\n"
            b"      Model                   = US_M1120_A\r\n"
            b"      Animation               = US_M1120_A.US_M1120_A\r\n"
            b"      AnimationMode           = ONCE\r\n"
            b"      Flags                   = START_FRAME_LAST\r\n"
            b"    End\r\n"
            b"    ConditionState            = DEPLOYED REALLYDAMAGED\r\n"
            b"      Model                   = US_M1120_AD\r\n"
            b"      Animation               = US_M1120_AD.US_M1120_AD\r\n"
            b"      AnimationMode           = ONCE\r\n"
            b"      Flags                   = START_FRAME_LAST\r\n"
            b"    End\r\n",
            b"    ; UsaPac3F has no ANIMATION chunk (spawnfix3). Do not name a clip.\r\n"
            b"    ConditionState            = DEPLOYED\r\n"
            b"      Model                   = UsaPac3F\r\n"
            b"    End\r\n"
            b"    ConditionState            = DEPLOYED REALLYDAMAGED\r\n"
            b"      Model                   = UsaPac3F_d\r\n"
            b"    End\r\n",
        ),
        (
            b"    DefaultConditionState\r\n"
            b"      Model                   = US_M1120\r\n"
            b"      Animation               = US_M1120.US_M1120\r\n"
            b"      AnimationMode           = ONCE\r\n"
            b"      Flags                   = START_FRAME_LAST\r\n"
            b"    End\r\n"
            b"    ConditionState            = REALLYDAMAGED\r\n"
            b"      Model                   = US_M1120D\r\n"
            b"      Animation               = US_M1120D.US_M1120D\r\n"
            b"      AnimationMode           = ONCE\r\n"
            b"      Flags                   = START_FRAME_LAST\r\n"
            b"    End\r\n"
            b"    ConditionState            = RUBBLE\r\n"
            b"      Model                   = US_M1120D\r\n"
            b"    End\r\n",
            b"    DefaultConditionState\r\n"
            b"      Model                   = UsaPac3F\r\n"
            b"    End\r\n"
            b"    ConditionState            = REALLYDAMAGED\r\n"
            b"      Model                   = UsaPac3F_d\r\n"
            b"    End\r\n"
            b"    ConditionState            = RUBBLE\r\n"
            b"      Model                   = UsaPac3F_d\r\n"
            b"    End\r\n",
        ),
        (b"      Model                   = US_M1120D", b"      Model                   = UsaPac3Car_d"),
        (b"      Animation               = US_M1120D.US_M1120D", b"      Animation               = UsaPac3Car_d.UsaPac3Car_d"),
        (b"      Model                   = US_M1120\r\n", b"      Model                   = UsaPac3Car\r\n"),
        (b"      Animation               = US_M1120.US_M1120", b"      Animation               = UsaPac3Car.UsaPac3Car"),
        (b"    LeftFrontTireBone         = Tire01", b"    LeftFrontTireBone         = TIRE01"),
        (b"    RightFrontTireBone        = Tire03", b"    RightFrontTireBone        = TIRE03"),
        (b"    LeftRearTireBone          = Tire06", b"    LeftRearTireBone          = TIRE06"),
        (b"    RightRearTireBone         = Tire08", b"    RightRearTireBone         = TIRE08"),
        (b"    MidLeftFrontTireBone      = Tire02", b"    MidLeftFrontTireBone      = TIRE02"),
        (b"    MidRightFrontTireBone     = Tire04", b"    MidRightFrontTireBone     = TIRE04"),
        (b"    MidLeftRearTireBone       = Tire05", b"    MidLeftRearTireBone       = TIRE05"),
        (b"    MidRightRearTireBone      = Tire07", b"    MidRightRearTireBone      = TIRE07"),
    ]
    for old, new in repls:
        if old not in text:
            fail(f"missing draw fragment {old[:80]!r}")
        text = text.replace(old, new)

    if b"US_M1120" in text:
        fail("US_M1120 leftover in USAPAC3.ini")
    if b"UsaPac3Car_w" in text:
        fail("UsaPac3Car_w referenced")
    if b"Animation               = UsaPac3F" in text:
        fail("DEPLOYED still names UsaPac3F clip")
    if b"CommandSet           = USAPAC3CommandSet\r\n" not in text:
        fail("lost mobile CommandSet")
    if b"CommandSet           = USAPAC3CommandSet_Deployed\r\n" not in text:
        fail("lost combat CommandSet")
    if b"Model                   = THAAD_FCS" not in text:
        fail("FCS draw rewritten")
    if b"Weapon            = PRIMARY   8x_LRSAM_THAAD" not in text:
        fail("AA FCS weapon rewritten")
    if b"OCL = FINAL    OCL_USAPAC3_Deployed\r\n" not in text:
        fail("deploy OCL rewritten")
    return HEADER + text


def main() -> int:
    if sha_file(DATA) != BEFORE_DATA_SHA:
        fail("input DATA is not specter-usapac3-commandset-fix packed BIG")
    if sha_file(ART2) != BEFORE_ART2_SHA:
        fail("input ART TWO is not cleanup/commandset-fix ART")

    raw, entries = read_big(DATA)
    file_map = {n: raw[o : o + s] for n, o, s in entries}
    by = {key(n): n for n in file_map}

    for k, expected in (
        (THAAD_KEY, THAAD_SHA),
        (WPN_KEY, WEAPON_SHA),
        (CS_KEY, CS_SHA),
        (CB_KEY, CB_SHA),
        (OCL_KEY, OCL_SHA),
    ):
        got = sha256(file_map[by[k]])
        if got != expected:
            fail(f"protected {k} sha {got} != {expected}")

    old_obj = file_map[by[OBJ_KEY]]
    wep = file_map[by[WEP_KEY]]
    oclu = file_map[by[OCLU_KEY]]
    new_obj = patch_object(old_obj)
    file_map[by[OBJ_KEY]] = new_obj

    if sha256(file_map[by[THAAD_KEY]]) != THAAD_SHA:
        fail("US_M1120.ini mutated")
    if sha256(file_map[by[CS_KEY]]) != CS_SHA:
        fail("CommandSet.ini mutated")
    if sha256(file_map[by[CB_KEY]]) != CB_SHA:
        fail("CommandButton.ini mutated")
    if sha256(file_map[by[WPN_KEY]]) != WEAPON_SHA:
        fail("Weapon.ini mutated")
    if sha256(file_map[by[OCL_KEY]]) != OCL_SHA:
        fail("ObjectCreationList.ini mutated")
    if file_map[by[WEP_KEY]] != wep:
        fail("Weapon_USAPAC3.ini mutated")
    if file_map[by[OCLU_KEY]] != oclu:
        fail("ObjectCreationList_USAPAC3.ini mutated")

    out_data = build_big(file_map)
    DATA.write_bytes(out_data)

    art_raw, art_ents = read_big(ART2)
    art_map = {n: art_raw[o : o + s] for n, o, s in art_ents}
    art_by = {key(n): n for n in art_map}
    keep_sha = {}
    for k in KEEP_ART:
        if k not in art_by:
            fail(f"missing protected ART {k}")
        keep_sha[k] = sha256(art_map[art_by[k]])

    if any("usapac3car" in key(n) or "usapac3f" in key(n) or "pac3mis_m" in key(n) for n in art_map):
        fail("PAC-3 meshes already in ART TWO")

    for store, src, strip in ART_ADD:
        if not src.is_file():
            fail(f"missing archive {src}")
        blob = src.read_bytes()
        if strip:
            blob = strip_animation(blob)
            if w3d_has_anim(blob):
                fail(f"{src.name} still has ANIMATION")
        if store.lower().endswith(".w3d") and "f.w3d" in store.lower():
            if w3d_has_anim(blob):
                fail(f"{store} still has ANIMATION chunk")
        if key(store) in art_by:
            fail(f"would overwrite existing ART {store}")
        art_map[store] = blob

    if r"Art\W3D\UsaPac3Car_w.W3D" in art_map or key(r"Art\W3D\UsaPac3Car_w.W3D") in {key(n) for n in art_map}:
        fail("UsaPac3Car_w packed")

    for k, digest in keep_sha.items():
        if sha256(art_map[art_by[k]]) != digest:
            fail(f"protected ART mutated {k}")

    out_art = build_big(art_map)
    ART2.write_bytes(out_art)

    DRAW.mkdir(parents=True, exist_ok=True)
    overlay = ROOT / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini"
    overlay.write_bytes(new_obj)
    (DRAW / "USAPAC3.ini").write_bytes(new_obj)
    (ROOT / "docs/specter-usapac3/independent/USAPAC3.ini").write_bytes(new_obj)
    (ROOT / "docs/specter-usapac3/base/USAPAC3.ini").write_bytes(new_obj)
    (MERGED / "_SPEC_DATA_ONE.big.sha256").write_text(f"{sha256(out_data)}  _SPEC_DATA_ONE.big\n", encoding="ascii")
    (MERGED / "_SPEC_ART_TWO.big.sha256").write_text(f"{sha256(out_art)}  _SPEC_ART_TWO.big\n", encoding="ascii")
    (DRAW / "_SPEC_DATA_ONE.big").write_bytes(out_data)
    (DRAW / "_SPEC_ART_TWO.big").write_bytes(out_art)

    print("DATA", sha256(out_data), len(out_data), "entries", len(file_map))
    print("ART2", sha256(out_art), len(out_art), "entries", len(art_map))
    print("object", sha256(new_obj), len(new_obj))
    print("THAAD unchanged", THAAD_SHA)
    print("CommandSet.ini unchanged", CS_SHA)
    print("ART TWO existing meshes unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
