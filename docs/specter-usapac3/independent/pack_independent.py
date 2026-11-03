#!/usr/bin/env python3
"""PAC-3 independent CommandSet / Deploy / OCL / FCS stage.

Does not rewrite US_M1120.ini, S400ECommandSet, OCL_THAAD_*, Weapon.ini,
S400R_Deploy, ART ONE, ART TWO, Patriot, NASAMS, failed-impl, or abtest.
"""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
INDEP = ROOT / "docs/specter-usapac3/independent"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"

BEFORE_DATA_SHA = "d56e8701941606d847a580de0617e9066555c154fadedaff82b215f10ffc73f2"
ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
THAAD_SHA = "b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f"
WEAPON_SHA = "a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8"
CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
CB_SHA = "1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c"
OCL_SHA = "e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5"
OCLZ_SHA = "ee88eb90ee1ac12d1127daaf19529f1477b21987582f1102ffbb2a60b3ad79ad"

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"
CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
OCL_KEY = r"data\ini\objectcreationlist.ini"
OCLZ_KEY = r"data\ini\objectcreationlist_zzzz_zzgmadabm.ini"
WPN_KEY = r"data\ini\weapon.ini"

CS_STORE = r"Data\INI\CommandSet_USAPAC3.ini"
OCL_STORE = r"Data\INI\ObjectCreationList_USAPAC3.ini"
OBJ_STORE = r"Data\INI\Object\Specter\United States Of America\AirDefense\USAPAC3.ini"
WEP_STORE = r"Data\INI\Weapon_USAPAC3.ini"

OBJ_HEADER = (
    b"; SPECTER PATCH - USAPAC3 independent functional stage 1.\r\n"
    b"; Unique CommandSet / Deploy OCL / CombatMode / FireControlSystem.\r\n"
    b"; Draw remains live THAAD US_M1120. Does not redefine Object US_THAAD.\r\n"
    b"\r\n"
)

WEP_HEADER = (
    b"; SPECTER PATCH - USAPAC3 independent dummy deploy/pack weapons.\r\n"
    b"; Cloned from S400R_Deploy / S400R_Deploy_ABM / S400R_Pack. Weapon.ini untouched.\r\n"
    b"\r\n"
)

CS_BLOB = b"""\
; SPECTER PATCH - USAPAC3-only CommandSets.
; Does not redefine the shared THAAD ADS CommandSets.

CommandSet USAPAC3CommandSet
  1 = Command_ADS_MTS_SWITCH
  3 = Command_AADS_AA_Mode
  5 = Command_AADS_ABM_Mode
  14 = Command_Stop
End

CommandSet USAPAC3CommandSet_AA
  6  = Command_ADSCombatMode
  14 = Command_Stop
End

CommandSet USAPAC3CommandSet_ABM
  6  = Command_ADS_ABM_CombatMode
  14 = Command_Stop
End

CommandSet USAPAC3CommandSet_Deployed
  13 = Command_FireControlPack
  14 = Command_Stop
End
""".replace(b"\n", b"\r\n")

OCL_BLOB = b"""\
; SPECTER PATCH - USAPAC3 independent deploy/pack OCLs.
; Does not redefine OCL_THAAD_Deployed / OCL_THAAD_Deployed_ABM / OCL_THAAD_Pack.
; AirdefenseLinkRestarter is shared SPECTER AD glue, not a THAAD unit.

ObjectCreationList OCL_USAPAC3_Deployed
  CreateObject
    ObjectNames           = USAPAC3_FireControlSystem
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = AirdefenseLinkRestarter
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = USAPAC3_CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End

ObjectCreationList OCL_USAPAC3_Deployed_ABM
  CreateObject
    ObjectNames           = USAPAC3_FireControlSystem_ABM
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = AirdefenseLinkRestarter
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
  CreateObject
    ObjectNames           = USAPAC3_CombatMode
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End

ObjectCreationList OCL_USAPAC3_Pack
  CreateObject
    ObjectNames           = USAPAC3
    Disposition           = LIKE_EXISTING
    IgnorePrimaryObstacle = Yes
    Count                 = 1
  End
End
""".replace(b"\n", b"\r\n")


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
    lines = blob[matches[0].start() :].splitlines(True)
    acc = [lines[0]]
    for line in lines[1:]:
        acc.append(line)
        if line.strip() == b"End" and line[:1] not in b" \t":
            break
    return b"".join(acc)


def strip_stage1_header(obj: bytes) -> bytes:
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
        fail("object header after strip")
    return text


def patch_mobile(obj: bytes) -> bytes:
    body = strip_stage1_header(obj)
    repls = [
        (b"CommandSet      = S400ECommandSet_AA", b"CommandSet      = USAPAC3CommandSet_AA"),
        (b"CommandSet      = S400ECommandSet_ABM", b"CommandSet      = USAPAC3CommandSet_ABM"),
        (b"CommandSet           = S400ECommandSet", b"CommandSet           = USAPAC3CommandSet"),
        (b"OCL = FINAL    OCL_THAAD_Deployed_ABM", b"OCL = FINAL    OCL_USAPAC3_Deployed_ABM"),
        (b"OCL = FINAL    OCL_THAAD_Deployed", b"OCL = FINAL    OCL_USAPAC3_Deployed"),
    ]
    for old, new in repls:
        if old not in body:
            fail(f"missing {old!r}")
        body = body.replace(old, new, 1)
    if b"S400ECommandSet" in body:
        fail("S400ECommandSet leftover on mobile object")
    if b"OCL_THAAD_Deployed" in body:
        fail("OCL_THAAD_Deployed leftover on mobile object")
    if b"Model                   = US_M1120" not in body:
        fail("Draw lost")
    if b"UsaPac3" in body:
        fail("New Donor leaked")
    return OBJ_HEADER + body


def clone_combat(thaad_file: bytes) -> bytes:
    block = extract_top_level(thaad_file, b"Object", b"US_THAAD_CombatMode")
    block = block.replace(b"Object US_THAAD_CombatMode", b"Object USAPAC3_CombatMode", 1)
    block = block.replace(b"DisplayName          = OBJECT:M1120", b"DisplayName          = OBJECT:USAPAC3", 1)
    block = block.replace(
        b"    Weapon             = SECONDARY S400R_Pack",
        b"    Weapon             = SECONDARY USAPAC3_Weapon_Pack",
        1,
    )
    block = block.replace(
        b"  CommandSet           = S400ECommandSet_Deployed",
        b"  CommandSet           = USAPAC3CommandSet_Deployed",
        1,
    )
    block = block.replace(b"OCL = FINAL    OCL_THAAD_Pack", b"OCL = FINAL    OCL_USAPAC3_Pack", 1)
    if b"S400ECommandSet" in block or b"S400R_Pack" in block or b"OCL_THAAD_Pack" in block:
        fail("combat clone still names THAAD command/pack")
    if b"US_THAAD_CombatMode" in block:
        fail("combat clone still named US_THAAD_CombatMode")
    if b"Model                   = US_M1120" not in block:
        fail("combat Draw lost")
    if b"DeathWeapon          = FCS_POWER_ZERO_Pack" not in block:
        fail("FCS pack-kill lost")
    return block


def clone_fcs(thaad_file: bytes, src: bytes, dst: bytes, weapon: bytes) -> bytes:
    block = extract_top_level(thaad_file, b"Object", src)
    if src not in block.splitlines()[0]:
        fail("fcs header")
    block = block.replace(b"Object " + src, b"Object " + dst, 1)
    if b"Weapon            = PRIMARY   " + weapon not in block and b"Weapon            = PRIMARY " + weapon not in block:
        # THAAD uses extra spaces: PRIMARY   8x_LRSAM_THAAD / PRIMARY   THAADMissile_ABM
        if weapon not in block:
            fail(f"FCS missing weapon {weapon.decode()}")
    if b"Object " + src in block:
        fail("src object name leftover")
    return block


def clone_weapons(wep_ini: bytes) -> bytes:
    a = extract_top_level(wep_ini, b"Weapon", b"S400R_Deploy")
    b = extract_top_level(wep_ini, b"Weapon", b"S400R_Deploy_ABM")
    c = extract_top_level(wep_ini, b"Weapon", b"S400R_Pack")
    a = a.replace(b"Weapon S400R_Deploy", b"Weapon USAPAC3_Weapon", 1)
    b = b.replace(b"Weapon S400R_Deploy_ABM", b"Weapon USAPAC3_Weapon_ABM", 1)
    c = c.replace(b"Weapon S400R_Pack", b"Weapon USAPAC3_Weapon_Pack", 1)
    for blob, label in ((a, b"AA"), (b, b"ABM"), (c, b"PACK")):
        if re.search(rb"(?m)^\s*ProjectileObject\s*=", blob):
            fail(f"{label.decode()} dummy unexpectedly has ProjectileObject")
    return WEP_HEADER + a + b"\r\n" + b + b"\r\n" + c + (b"" if c.endswith(b"\n") else b"\r\n")


def write_text(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> int:
    if sha_file(DATA) != BEFORE_DATA_SHA:
        fail("input DATA is not specter-usapac3-base-thaad packed BIG")
    if sha_file(ART2) != ART2_SHA:
        fail("ART TWO changed; this stage must not touch ART")

    raw, entries = read_big(DATA)
    file_map = {n: raw[o : o + s] for n, o, s in entries}
    by = {key(n): n for n in file_map}

    for k, expected in (
        (THAAD_KEY, THAAD_SHA),
        (WPN_KEY, WEAPON_SHA),
        (CS_KEY, CS_SHA),
        (CB_KEY, CB_SHA),
        (OCL_KEY, OCL_SHA),
        (OCLZ_KEY, OCLZ_SHA),
    ):
        got = sha256(file_map[by[k]])
        if got != expected:
            fail(f"protected {k} sha {got} != {expected}")

    thaad_file = file_map[by[THAAD_KEY]]
    old_obj = file_map[by[OBJ_KEY]]
    wep_ini = file_map[by[WPN_KEY]]

    mobile = patch_mobile(old_obj)
    combat = clone_combat(thaad_file)
    fcs_aa = clone_fcs(thaad_file, b"THAAD_FireControlSystem", b"USAPAC3_FireControlSystem", b"8x_LRSAM_THAAD")
    fcs_abm = clone_fcs(
        thaad_file,
        b"THAAD_FireControlSystem_ABM",
        b"USAPAC3_FireControlSystem_ABM",
        b"THAADMissile_ABM",
    )
    obj_blob = mobile.rstrip(b"\r\n") + b"\r\n\r\n" + combat + b"\r\n" + fcs_aa + b"\r\n" + fcs_abm
    if not obj_blob.endswith(b"\n"):
        obj_blob += b"\r\n"
    wep_blob = clone_weapons(wep_ini)

    for needle, label in (
        (b"Object USAPAC3\r\n", "mobile"),
        (b"Object USAPAC3_CombatMode\r\n", "combat"),
        (b"Object USAPAC3_FireControlSystem\r\n", "fcs aa"),
        (b"Object USAPAC3_FireControlSystem_ABM\r\n", "fcs abm"),
        (b"CommandSet           = USAPAC3CommandSet\r\n", "cs"),
        (b"CommandSet      = USAPAC3CommandSet_AA\r\n", "cs aa"),
        (b"CommandSet      = USAPAC3CommandSet_ABM\r\n", "cs abm"),
        (b"CommandSet           = USAPAC3CommandSet_Deployed\r\n", "cs deployed"),
        (b"OCL = FINAL    OCL_USAPAC3_Deployed\r\n", "ocl aa"),
        (b"OCL = FINAL    OCL_USAPAC3_Deployed_ABM\r\n", "ocl abm"),
        (b"OCL = FINAL    OCL_USAPAC3_Pack\r\n", "ocl pack"),
        (b"Weapon            = PRIMARY   8x_LRSAM_THAAD\r\n", "aa weapon"),
        (b"Weapon            = PRIMARY   THAADMissile_ABM\r\n", "abm weapon"),
    ):
        if needle not in obj_blob:
            fail(f"object blob missing {label}: {needle!r}")

    if obj_blob.count(b"Object USAPAC3\r\n") != 1:
        fail("mobile object count")
    if b"US_THAAD_CombatMode" in obj_blob or b"THAAD_FireControlSystem" in obj_blob:
        fail("THAAD object names leaked into USAPAC3.ini")
    if b"S400ECommandSet" in obj_blob:
        fail("S400E leftover")

    INDEP.mkdir(parents=True, exist_ok=True)
    write_text(INDEP / "USAPAC3.ini", obj_blob)
    write_text(INDEP / "Weapon_USAPAC3.ini", wep_blob)
    write_text(INDEP / "CommandSet_USAPAC3.ini", CS_BLOB)
    write_text(INDEP / "ObjectCreationList_USAPAC3.ini", OCL_BLOB)

    overlay_obj = ROOT / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini"
    overlay_wep = ROOT / "patch/Data/INI/Weapon_USAPAC3.ini"
    overlay_cs = ROOT / "patch/Data/INI/CommandSet_USAPAC3.ini"
    overlay_ocl = ROOT / "patch/Data/INI/ObjectCreationList_USAPAC3.ini"
    write_text(overlay_obj, obj_blob)
    write_text(overlay_wep, wep_blob)
    write_text(overlay_cs, CS_BLOB)
    write_text(overlay_ocl, OCL_BLOB)
    write_text(ROOT / "docs/specter-usapac3/base/USAPAC3.ini", obj_blob)
    write_text(ROOT / "docs/specter-usapac3/base/Weapon_USAPAC3.ini", wep_blob)

    # Protected packed keys stay byte-identical
    file_map[by[OBJ_KEY]] = obj_blob
    file_map[by[WEP_KEY]] = wep_blob
    if key(CS_STORE) in by or key(OCL_STORE) in by:
        fail("unique CommandSet/OCL path already packed")
    file_map[CS_STORE] = CS_BLOB
    file_map[OCL_STORE] = OCL_BLOB

    if sha256(file_map[by[THAAD_KEY]]) != THAAD_SHA:
        fail("US_M1120.ini mutated")
    if sha256(file_map[by[WPN_KEY]]) != WEAPON_SHA:
        fail("Weapon.ini mutated")
    if sha256(file_map[by[CS_KEY]]) != CS_SHA:
        fail("CommandSet.ini mutated")
    if sha256(file_map[by[CB_KEY]]) != CB_SHA:
        fail("CommandButton.ini mutated")
    if sha256(file_map[by[OCL_KEY]]) != OCL_SHA:
        fail("ObjectCreationList.ini mutated")
    if sha256(file_map[by[OCLZ_KEY]]) != OCLZ_SHA:
        fail("ObjectCreationList_ZZZZ_ZZGmAdAbm.ini mutated")

    out = build_big(file_map)
    DATA.write_bytes(out)
    (MERGED / "_SPEC_DATA_ONE.big.sha256").write_text(
        f"{sha256(out)}  _SPEC_DATA_ONE.big\n", encoding="ascii"
    )

    print("packed", sha256(out), "bytes", len(out), "entries", len(file_map))
    print("object", sha256(obj_blob), "bytes", len(obj_blob))
    print("weapon", sha256(wep_blob), "bytes", len(wep_blob))
    print("commandset unique", sha256(CS_BLOB))
    print("ocl unique", sha256(OCL_BLOB))
    print("THAAD file unchanged", THAAD_SHA)
    print("ART TWO unchanged", ART2_SHA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
