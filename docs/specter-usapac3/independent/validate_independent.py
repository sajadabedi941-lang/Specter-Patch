#!/usr/bin/env python3
"""Static validation for USAPAC3 independent CommandSet/Deploy/OCL/FCS.

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
INDEP = ROOT / "docs/specter-usapac3/independent"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"

ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
ART1_SHA = "15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
THAAD_SHA = "b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f"
WEAPON_SHA = "a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8"
CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
CB_SHA = "1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c"
OCL_SHA = "e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5"
OCLZ_SHA = "ee88eb90ee1ac12d1127daaf19529f1477b21987582f1102ffbb2a60b3ad79ad"

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
CSU_KEY = r"data\ini\commandset_usapac3.ini"
OCLU_KEY = r"data\ini\objectcreationlist_usapac3.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"
CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
OCL_KEY = r"data\ini\objectcreationlist.ini"
OCLZ_KEY = r"data\ini\objectcreationlist_zzzz_zzgmadabm.ini"
WPN_KEY = r"data\ini\weapon.ini"

UNIQUE_SETS = (
    b"USAPAC3CommandSet",
    b"USAPAC3CommandSet_AA",
    b"USAPAC3CommandSet_ABM",
    b"USAPAC3CommandSet_Deployed",
)
UNIQUE_OCLS = (
    b"OCL_USAPAC3_Deployed",
    b"OCL_USAPAC3_Deployed_ABM",
    b"OCL_USAPAC3_Pack",
)
UNIQUE_OBJS = (
    b"USAPAC3_CombatMode",
    b"USAPAC3_FireControlSystem",
    b"USAPAC3_FireControlSystem_ABM",
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


def ocl_created_objects(block: bytes) -> list[bytes]:
    return re.findall(rb"ObjectNames\s+=\s+(\S+)", block)


def main() -> int:
    raw, ents = read_big(DATA)
    amap = {key(n): (n, raw[o : o + s]) for n, o, s in ents}

    for need in (OBJ_KEY, WEP_KEY, CSU_KEY, OCLU_KEY, THAAD_KEY, CS_KEY, CB_KEY, OCL_KEY, WPN_KEY):
        if need not in amap:
            fail(f"missing packed {need}")

    obj = amap[OBJ_KEY][1]
    wep = amap[WEP_KEY][1]
    csu = amap[CSU_KEY][1]
    oclu = amap[OCLU_KEY][1]
    thaad = amap[THAAD_KEY][1]
    cs = amap[CS_KEY][1]
    cb = amap[CB_KEY][1]
    ocl = amap[OCL_KEY][1]
    oclz = amap[OCLZ_KEY][1]
    weapon = amap[WPN_KEY][1]

    # 1 unique CommandSet names, no collision with packed CommandSet.ini
    for name in UNIQUE_SETS:
        if count_headers(csu, b"CommandSet", name) != 1:
            fail(f"unique set missing {name.decode()}")
        if count_headers(cs, b"CommandSet", name) != 0:
            fail(f"{name.decode()} collides with CommandSet.ini")
        extra = [
            n
            for n, o, s in ents
            if count_headers(raw[o : o + s], b"CommandSet", name)
            and key(n) != CSU_KEY
        ]
        if extra:
            fail(f"{name.decode()} also in {extra}")

    s400_count = count_headers(cs, b"CommandSet", b"S400ECommandSet")
    if s400_count != 1:
        fail(f"S400ECommandSet count {s400_count}")

    # 2/3 AA and ABM chains
    mobile = extract_top_level(obj, b"Object", b"USAPAC3")
    if len(mobile) != 1:
        fail("Object USAPAC3 count")
    mob = mobile[0]
    if b"CommandSet           = USAPAC3CommandSet" not in mob:
        fail("mobile CommandSet")
    if b"TriggeredBy     = Upgrade_AADS_AA_Mode" not in mob or b"CommandSet      = USAPAC3CommandSet_AA" not in mob:
        fail("AA CommandSetUpgrade")
    if b"TriggeredBy     = Upgrade_AADS_ABM_Mode" not in mob or b"CommandSet      = USAPAC3CommandSet_ABM" not in mob:
        fail("ABM CommandSetUpgrade")
    if b"S400ECommandSet" in mob:
        fail("mobile still uses S400E")
    if b"1 = Command_ADS_MTS_SWITCH" not in csu:
        fail("MTS still on unique initial set")
    if b"TriggeredBy     = Upgrade_AIM-120C" in mob:
        fail("MTS unexpectedly wired")

    aa_set = extract_top_level(csu, b"CommandSet", b"USAPAC3CommandSet_AA")[0]
    abm_set = extract_top_level(csu, b"CommandSet", b"USAPAC3CommandSet_ABM")[0]
    dep_set = extract_top_level(csu, b"CommandSet", b"USAPAC3CommandSet_Deployed")[0]
    if b"Command_ADSCombatMode" not in aa_set:
        fail("AA deploy button")
    if b"Command_ADS_ABM_CombatMode" not in abm_set:
        fail("ABM deploy button")
    if b"Command_FireControlPack" not in dep_set:
        fail("Pack button")

    # 4 Deploy and Pack
    if b"OCL = FINAL    OCL_USAPAC3_Deployed\r\n" not in mob:
        fail("AA deploy OCL")
    if b"OCL = FINAL    OCL_USAPAC3_Deployed_ABM\r\n" not in mob:
        fail("ABM deploy OCL")
    if b"OCL_THAAD_Deployed" in mob:
        fail("mobile still uses THAAD deploy OCL")
    combat = extract_top_level(obj, b"Object", b"USAPAC3_CombatMode")
    if len(combat) != 1:
        fail("CombatMode count")
    cmb = combat[0]
    if b"CommandSet           = USAPAC3CommandSet_Deployed" not in cmb:
        fail("combat CommandSet")
    if b"Weapon             = SECONDARY USAPAC3_Weapon_Pack" not in cmb:
        fail("pack weapon")
    if b"OCL = FINAL    OCL_USAPAC3_Pack" not in cmb:
        fail("pack OCL")
    if b"OCL_THAAD_Pack" in cmb or b"S400ECommandSet" in cmb:
        fail("combat still THAAD-named")

    if count_headers(wep, b"Weapon", b"USAPAC3_Weapon") != 1:
        fail("USAPAC3_Weapon")
    if count_headers(wep, b"Weapon", b"USAPAC3_Weapon_ABM") != 1:
        fail("USAPAC3_Weapon_ABM")
    if count_headers(wep, b"Weapon", b"USAPAC3_Weapon_Pack") != 1:
        fail("USAPAC3_Weapon_Pack")
    if re.search(rb"(?m)^\s*ProjectileObject\s*=", wep):
        fail("dummy weapons gained ProjectileObject")

    # 5 new OCLs create no THAAD objects
    for name in UNIQUE_OCLS:
        blocks = extract_top_level(oclu, b"ObjectCreationList", name)
        if len(blocks) != 1:
            fail(f"OCL count {name.decode()}")
        created = ocl_created_objects(blocks[0])
        for item in created:
            if item.startswith(b"US_THAAD") or item.startswith(b"THAAD_") or item.startswith(b"S400R_"):
                fail(f"{name.decode()} creates THAAD object {item.decode()}")
        extra = [
            n
            for n, o, s in ents
            if count_headers(raw[o : o + s], b"ObjectCreationList", name) and key(n) != OCLU_KEY
        ]
        if extra:
            fail(f"{name.decode()} also in {extra}")

    aa_created = ocl_created_objects(extract_top_level(oclu, b"ObjectCreationList", b"OCL_USAPAC3_Deployed")[0])
    abm_created = ocl_created_objects(extract_top_level(oclu, b"ObjectCreationList", b"OCL_USAPAC3_Deployed_ABM")[0])
    pack_created = ocl_created_objects(extract_top_level(oclu, b"ObjectCreationList", b"OCL_USAPAC3_Pack")[0])
    if b"USAPAC3_FireControlSystem" not in aa_created or b"USAPAC3_CombatMode" not in aa_created:
        fail("AA OCL objects")
    if b"USAPAC3_FireControlSystem_ABM" not in abm_created or b"USAPAC3_CombatMode" not in abm_created:
        fail("ABM OCL objects")
    if b"THAAD_FireControlSystem" in aa_created or b"THAAD_FireControlSystem_ABM" in abm_created:
        fail("THAAD FCS in unique OCL")
    if b"US_THAAD_CombatMode" in aa_created + abm_created + pack_created:
        fail("US_THAAD_CombatMode in unique OCL")
    if pack_created != [b"USAPAC3"]:
        fail(f"pack OCL objects {pack_created}")

    # original THAAD OCLs still spawn THAAD
    thaad_aa = extract_top_level(ocl, b"ObjectCreationList", b"OCL_THAAD_Deployed")
    if len(thaad_aa) != 1 or b"US_THAAD_CombatMode" not in thaad_aa[0] or b"THAAD_FireControlSystem" not in thaad_aa[0]:
        fail("OCL_THAAD_Deployed mutated")

    # 6 FCS weapons
    fcs_aa = extract_top_level(obj, b"Object", b"USAPAC3_FireControlSystem")
    fcs_abm = extract_top_level(obj, b"Object", b"USAPAC3_FireControlSystem_ABM")
    if len(fcs_aa) != 1 or len(fcs_abm) != 1:
        fail("FCS counts")
    if b"Weapon            = PRIMARY   8x_LRSAM_THAAD" not in fcs_aa[0]:
        fail("AA FCS weapon")
    if b"Weapon            = PRIMARY   THAADMissile_ABM" not in fcs_abm[0]:
        fail("ABM FCS weapon")
    if count_headers(weapon, b"Weapon", b"8x_LRSAM_THAAD") != 1:
        fail("shared AA missile missing")
    if count_headers(weapon, b"Weapon", b"THAADMissile_ABM") != 1:
        fail("shared ABM missile missing")

    # 7 THAAD originals unchanged
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
    if sha256(oclz) != OCLZ_SHA:
        fail("OCL ZZZZ sha")
    if b"Object USAPAC3" in thaad:
        fail("USAPAC3 leaked into US_M1120.ini")
    if count_headers(weapon, b"Weapon", b"S400R_Deploy") != 1:
        fail("S400R_Deploy")
    if count_headers(weapon, b"Weapon", b"S400R_Deploy_ABM") != 1:
        fail("S400R_Deploy_ABM")
    thaad_obj = extract_top_level(thaad, b"Object", b"US_THAAD")[0]
    if b"CommandSet           = S400ECommandSet" not in thaad_obj:
        fail("THAAD CommandSet mutated")
    if b"Weapon             = SECONDARY S400R_Deploy" not in thaad_obj:
        fail("THAAD weapons mutated")

    # 8 packed == overlay == independent sources
    for src, blob in (
        (INDEP / "USAPAC3.ini", obj),
        (INDEP / "Weapon_USAPAC3.ini", wep),
        (INDEP / "CommandSet_USAPAC3.ini", csu),
        (INDEP / "ObjectCreationList_USAPAC3.ini", oclu),
        (ROOT / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini", obj),
        (ROOT / "patch/Data/INI/Weapon_USAPAC3.ini", wep),
        (ROOT / "patch/Data/INI/CommandSet_USAPAC3.ini", csu),
        (ROOT / "patch/Data/INI/ObjectCreationList_USAPAC3.ini", oclu),
        (ROOT / "docs/specter-usapac3/base/USAPAC3.ini", obj),
        (ROOT / "docs/specter-usapac3/base/Weapon_USAPAC3.ini", wep),
    ):
        if src.read_bytes() != blob:
            fail(f"{src} != packed")

    inst_cs = (ROOT / "patch/tools/installer/CommandSet.ini").read_bytes()
    inst_cb = (ROOT / "patch/tools/installer/CommandButton.ini").read_bytes()
    if inst_cs != cs:
        fail("installer CommandSet.ini drifted")
    if inst_cb != cb:
        fail("installer CommandButton.ini drifted")
    if (MERGED / "CommandSet.ini").read_bytes() != cs:
        fail("merged CommandSet.ini drifted")
    if (MERGED / "CommandButton.ini").read_bytes() != cb:
        fail("merged CommandButton.ini drifted")

    # 9 ART unchanged, no New Donor in live object
    if sha_file(ART2) != ART2_SHA:
        fail("ART TWO mutated")
    art1 = MERGED / "_SPEC_ART_ONE.big"
    if art1.exists() and sha_file(art1) != ART1_SHA:
        fail("ART ONE mutated")
    if b"UsaPac3" in obj or b"pac3mis" in obj:
        fail("New Donor in object")
    art_raw, art_ents = read_big(ART2)
    for n, o, s in art_ents:
        low = n.lower()
        if "usapac3car" in low or "usapac3f" in low or "pac3mis_m" in low:
            fail(f"ART TWO has {n}")
    keys = {key(n) for n, o, s in art_ents}
    for keep in (
        r"art\w3d\us_m1120.w3d",
        r"art\w3d\abpatriot.w3d",
        r"art\w3d\pac3_sudarb.w3d",
        r"art\textures\abnpatriot02.dds",
    ):
        if keep not in keys:
            fail(f"missing ART {keep}")

    # 10 no deleted live files; archive/abtest still present
    if not (ROOT / "docs/specter-usapac3/archive/failed-impl/Art/W3D/UsaPac3Car.W3D").exists():
        fail("failed-impl archive missing")
    if not (ROOT / "docs/specter-usapac3/abtest").is_dir():
        fail("abtest missing")
    if b"Object AmericaMobileSamSiteMIM104F" not in raw:
        fail("Patriot missing")
    if b"Command_ConstructAmerica_AD_NASAMS" not in raw:
        fail("NASAMS missing")
    if b"AmericaJetF117Clean" not in raw or b"AmericaJetB21Clean" not in raw:
        fail("F-117/B-21 missing")
    if b"  6  = Command_ConstructUSAPAC3" not in cs:
        fail("CC slot 6 lost")

    hq = (ROOT / "patch/Data/INI/CommandSet_FactionExpansion_Armies.ini").read_text("latin-1")
    if "6 = Command_ConstructAmerica_AD_NASAMS" not in hq:
        fail("HQ NASAMS")
    if "Command_ConstructUSAPAC3" in hq:
        fail("HQ USAPAC3")

    print("STATIC_OK")
    print("DATA", sha_file(DATA), DATA.stat().st_size, "entries", len(ents))
    print("ART2", sha_file(ART2), ART2.stat().st_size)
    print("US_M1120.ini", sha256(thaad))
    print("Weapon.ini", sha256(weapon))
    print("CommandSet.ini", sha256(cs))
    print("CommandButton.ini", sha256(cb))
    print("ObjectCreationList.ini", sha256(ocl))
    print("INGAME_ZH: not executed")
    print("STAGE: independent CommandSet/Deploy/OCL/FCS; Draw still US_M1120")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
