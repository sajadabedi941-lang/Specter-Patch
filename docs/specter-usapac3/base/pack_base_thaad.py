#!/usr/bin/env python3
"""Stage-1 USAPAC3: clone packed Object US_THAAD into a new independent object.

Does not import New Donor art. Does not rewrite US_THAAD, Patriot, NASAMS,
other countries, F-117, B-21, or ART ONE.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
BASE = ROOT / "docs/specter-usapac3/base"
DATA = MERGED / "_SPEC_DATA_ONE.big"

CLEAN_DATA_SHA = "3527ea062da9ab27c9902665238398ae0f29d985b6d342617449784a51bdda1a"
CLEAN_ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
CLEAN_CS_SHA = "a23df0bc1d6995dadfe3844fffed36e0c12821c1a985f7c03b0d88dc5b795a87"
CLEAN_CB_SHA = "d012daf5578f468da904e25008cc0f186de320f0b3ae6349fe4e8c2d3a6f4b36"

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"

OBJ_HEADER = (
    b"; SPECTER PATCH - USAPAC3 stage 1 base unit.\r\n"
    b"; Gameplay cloned from packed Object US_THAAD in US_M1120.ini.\r\n"
    b"; Draw/models are live THAAD (US_M1120). No New Donor art.\r\n"
    b"; Does not redefine Object US_THAAD.\r\n"
    b"\r\n"
)

WEP_HEADER = (
    b"; SPECTER PATCH - USAPAC3 weapons.\r\n"
    b"; Cloned from packed Weapon S400R_Deploy / S400R_Deploy_ABM in Weapon.ini.\r\n"
    b"; Those weapons have no ProjectileObject; no USAPAC3_Projectile is created.\r\n"
    b"\r\n"
)

BUTTON = (
    b"\r\n"
    b"; SPECTER PATCH USAPAC3 construct button. Must be in CommandButton.ini\r\n"
    b"; so CommandSet.ini AmericaCommandCenterCommandSet slot 6 can resolve it.\r\n"
    b"\r\n"
    b"CommandButton Command_ConstructUSAPAC3\r\n"
    b"  Command            = UNIT_BUILD\r\n"
    b"  Object             = USAPAC3\r\n"
    b"  TextLabel          = CONTROLBAR:ConstructUSAPAC3\r\n"
    b"  ButtonImage        = us_thaad\r\n"
    b"  ButtonBorderType   = BUILD\r\n"
    b"  DescriptLabel      = CONTROLBAR:ToolTipConstructUSAPAC3\r\n"
    b"End\r\n"
)

CC_OLD = (
    b"CommandSet AmericaCommandCenterCommandSet\r\n"
    b"  1  = Command_ConstructAmericaDozer\r\n"
    b" 12  = Command_ConstructAmericaVehicleUH60\r\n"
)
CC_NEW = (
    b"CommandSet AmericaCommandCenterCommandSet\r\n"
    b"  1  = Command_ConstructAmericaDozer\r\n"
    b"  6  = Command_ConstructUSAPAC3\r\n"
    b" 12  = Command_ConstructAmericaVehicleUH60\r\n"
)
CC_OLD_LF = CC_OLD.replace(b"\r\n", b"\n")
CC_NEW_LF = CC_NEW.replace(b"\r\n", b"\n")

LOOSE_CS = [
    ROOT / "patch/tools/installer/CommandSet.ini",
    ROOT / "patch/Data/INI/CommandSet.ini",
]
LOOSE_CB = [
    ROOT / "patch/tools/installer/CommandButton.ini",
]


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


def extract_top_level(blob: bytes, kind: bytes, name: bytes) -> bytes:
    pat = re.compile(rb"(?m)^" + re.escape(kind) + rb"\s+" + re.escape(name) + rb"\s*$")
    matches = list(pat.finditer(blob))
    if len(matches) != 1:
        fail(f"expected 1 {kind.decode()} {name.decode()}, got {len(matches)}")
    start = matches[0].start()
    lines = blob[start:].splitlines(True)
    acc = [lines[0]]
    for line in lines[1:]:
        acc.append(line)
        if line.strip() == b"End" and line[:1] not in b" \t":
            break
    return b"".join(acc)


def clone_object(thaad: bytes) -> bytes:
    body = thaad
    if not body.startswith(b"Object US_THAAD"):
        fail("THAAD block header")
    body = body.replace(b"Object US_THAAD", b"Object USAPAC3", 1)
    body = body.replace(b"DisplayName          = OBJECT:M1120", b"DisplayName          = OBJECT:USAPAC3", 1)
    body = body.replace(
        b"    Weapon             = SECONDARY S400R_Deploy\r\n"
        b"    Weapon             = TERTIARY  S400R_Deploy_ABM\r\n",
        b"    Weapon             = SECONDARY USAPAC3_Weapon\r\n"
        b"    Weapon             = TERTIARY  USAPAC3_Weapon_ABM\r\n",
        1,
    )
    if b"S400R_Deploy" in body:
        # LF variant
        body = body.replace(
            b"    Weapon             = SECONDARY S400R_Deploy\n"
            b"    Weapon             = TERTIARY  S400R_Deploy_ABM\n",
            b"    Weapon             = SECONDARY USAPAC3_Weapon\n"
            b"    Weapon             = TERTIARY  USAPAC3_Weapon_ABM\n",
            1,
        )
    if b"S400R_Deploy" in body:
        fail("weapon rename failed")
    prereq = re.compile(
        rb"  Prerequisites\r?\n"
        rb"    Object = AmericaStrategyCenter \S+\r?\n"
        rb"  End\r?\n"
    )
    body, n = prereq.subn(b"", body, count=1)
    if n != 1:
        fail(f"Prerequisites strip count {n}")
    body = body.replace(b"  BuildCost            = 3000", b"  BuildCost            = 3876", 1)
    body = body.replace(b"  BuildTime            = 22.0", b"  BuildTime            = 18.6", 1)
    if b"BuildCost            = 3876" not in body or b"BuildTime            = 18.6" not in body:
        fail("cost/time replace failed")
    if b"Prerequisites" in body or b"Science" in body:
        fail("prereq/science leftover in object")
    if b"Generic8x8Locomotor" not in body:
        fail("locomotor missing")
    if b"W3DTruckDraw" not in body or b"Model                   = US_M1120" not in body:
        fail("THAAD draw missing")
    if b"UsaPac3" in body or b"pac3mis" in body:
        fail("New Donor art leaked into object")
    return OBJ_HEADER + body


def clone_weapons(wep_ini: bytes) -> bytes:
    a = extract_top_level(wep_ini, b"Weapon", b"S400R_Deploy")
    b = extract_top_level(wep_ini, b"Weapon", b"S400R_Deploy_ABM")
    a = a.replace(b"Weapon S400R_Deploy", b"Weapon USAPAC3_Weapon", 1)
    b = b.replace(b"Weapon S400R_Deploy_ABM", b"Weapon USAPAC3_Weapon_ABM", 1)
    if b"ProjectileObject" in a or b"ProjectileObject" in b:
        fail("THAAD deploy weapon unexpectedly has a projectile")
    return WEP_HEADER + a + b"\r\n" + b + (b"" if b.endswith(b"\n") else b"\r\n")


def patch_commandset(blob: bytes) -> bytes:
    if CC_OLD in blob:
        if blob.count(CC_OLD) != 1:
            fail("CC_OLD count")
        return blob.replace(CC_OLD, CC_NEW, 1)
    if CC_OLD_LF in blob:
        if blob.count(CC_OLD_LF) != 1:
            fail("CC_OLD_LF count")
        return blob.replace(CC_OLD_LF, CC_NEW_LF, 1)
    fail("AmericaCommandCenterCommandSet block not found")


def patch_commandbutton(blob: bytes) -> bytes:
    if b"CommandButton Command_ConstructUSAPAC3" in blob:
        fail("CommandButton already has USAPAC3")
    return blob.rstrip(b"\r\n") + b"\r\n" + BUTTON


def main() -> int:
    if sha_file(DATA) != CLEAN_DATA_SHA:
        fail("input DATA is not the cleaned pack; refusing to clone from a dirty tree")
    art2 = MERGED / "_SPEC_ART_TWO.big"
    if art2.exists() and sha_file(art2) != CLEAN_ART2_SHA:
        fail("ART TWO changed; stage 1 must not touch ART")

    raw, entries = read_big(DATA)
    file_map = {n: raw[o : o + s] for n, o, s in entries}
    by = {key(n): n for n in file_map}

    thaad_name = by[THAAD_KEY]
    thaad_file = file_map[thaad_name]
    thaad_sha = sha256(thaad_file)
    thaad_obj = extract_top_level(thaad_file, b"Object", b"US_THAAD")

    wep_name = by[r"data\ini\weapon.ini"]
    obj_blob = clone_object(thaad_obj)
    wep_blob = clone_weapons(file_map[wep_name])

    BASE.mkdir(parents=True, exist_ok=True)
    (BASE / "USAPAC3.ini").write_bytes(obj_blob)
    (BASE / "Weapon_USAPAC3.ini").write_bytes(wep_blob)

    overlay_obj = (
        ROOT
        / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini"
    )
    overlay_wep = ROOT / "patch/Data/INI/Weapon_USAPAC3.ini"
    overlay_obj.parent.mkdir(parents=True, exist_ok=True)
    overlay_obj.write_bytes(obj_blob)
    overlay_wep.write_bytes(wep_blob)

    cs_name = by[CS_KEY]
    cb_name = by[CB_KEY]
    if sha256(file_map[cs_name]) != CLEAN_CS_SHA:
        fail("packed CommandSet.ini is not the cleaned file")
    if sha256(file_map[cb_name]) != CLEAN_CB_SHA:
        fail("packed CommandButton.ini is not the cleaned file")

    new_cs = patch_commandset(file_map[cs_name])
    new_cb = patch_commandbutton(file_map[cb_name])
    if len(re.findall(rb"(?m)^CommandSet\s+AmericaCommandCenterCommandSet\s*$", new_cs)) != 1:
        fail("duplicate CC CommandSet")
    if new_cs.count(b"  6  = Command_ConstructUSAPAC3") != 1:
        fail("slot 6 missing")
    if b"Command_ConstructAmericaDozer" not in new_cs:
        fail("CC dozer lost")

    file_map[cs_name] = new_cs
    file_map[cb_name] = new_cb
    # keep original path separators from the BIG for existing entries
    obj_store = "Data\\INI\\Object\\Specter\\United States Of America\\AirDefense\\USAPAC3.ini"
    wep_store = "Data\\INI\\Weapon_USAPAC3.ini"
    if key(obj_store) in by or key(wep_store) in by:
        fail("USAPAC3 path already in DATA")
    file_map[obj_store] = obj_blob
    file_map[wep_store] = wep_blob

    # US_M1120.ini must be byte-identical
    if sha256(file_map[thaad_name]) != thaad_sha:
        fail("US_M1120.ini mutated")

    out = build_big(file_map)
    DATA.write_bytes(out)
    (MERGED / "_SPEC_DATA_ONE.big.sha256").write_text(
        f"{sha256(out)}  _SPEC_DATA_ONE.big\n", encoding="ascii"
    )
    (MERGED / "CommandSet.ini").write_bytes(new_cs)
    (MERGED / "CommandButton.ini").write_bytes(new_cb)
    (MERGED / "CommandSet.ini.sha256").write_text(
        f"{sha256(new_cs)}  CommandSet.ini\n", encoding="ascii"
    )
    (MERGED / "CommandButton.ini.sha256").write_text(
        f"{sha256(new_cb)}  CommandButton.ini\n", encoding="ascii"
    )

    for path in LOOSE_CS:
        blob = path.read_bytes()
        if b"Command_ConstructUSAPAC3" in blob:
            fail(f"{path} already patched")
        path.write_bytes(patch_commandset(blob))
    # installer CommandButton may differ by trailing newline from packed; write packed result
    for path in LOOSE_CB:
        path.write_bytes(new_cb)

    print("packed", sha256(out), "bytes", len(out), "entries", len(file_map))
    print("object", sha256(obj_blob), "bytes", len(obj_blob))
    print("weapon", sha256(wep_blob), "bytes", len(wep_blob))
    print("CommandSet", sha256(new_cs))
    print("CommandButton", sha256(new_cb))
    print("THAAD file unchanged", thaad_sha)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
