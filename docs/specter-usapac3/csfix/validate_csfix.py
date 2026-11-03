#!/usr/bin/env python3
"""Static validation: USAPAC3 CommandSets on the live CommandSet.ini path.

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
CSFIX = ROOT / "docs/specter-usapac3/csfix"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
INSTALLER = ROOT / "patch/tools/installer"

ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
ART1_SHA = "15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
THAAD_SHA = "b56d62cdb44d0d3e582df51aeee56fcb25a447397983e8ced5788a4520dae92f"
WEAPON_SHA = "a8eb8340aecd1bd04147e97b4b5ce218f91233464178c34c66ff2cc003c5d6b8"
BEFORE_CS_SHA = "f6d9616febbf4eeb2720f6029a7089e7ce1f3d31a576d4f097c738348be9d223"
CB_SHA = "1870f1118e20e64b9f4186c49dd561884296ddda9fb7b2caa90bd9f26e8eb65c"
OCL_SHA = "e284d55c2b96fcb8c6aa585d155ba94b9f6fbbe1810f30cde96e3ef6bc16cff5"
OCLZ_SHA = "ee88eb90ee1ac12d1127daaf19529f1477b21987582f1102ffbb2a60b3ad79ad"

S400E_SHA = {
    b"S400ECommandSet": "d705077266291cb18edabec56bf1696c011682cca1f191227dc81563a02d6143",
    b"S400E_MTS_CommandSet": "f695dce4f6c1800374abb6959c075433d2f965580fec153bb5f7c1d0fe8e5998",
    b"S400ECommandSet_Deployed": "94c34b1ee20f3673ef7367ddcb145d06dc3318a87f4873d0b402a288c9785307",
    b"S400ECommandSet_AA": "f5166929304af7750478939e33a186ef319115a6f076e4e9f9637e32e34f4559",
    b"S400ECommandSet_ABM": "f512e16d145e583d9b20670fd66f6153ec94b61431fccffe22173688f0bf98bd",
}
OVERLAY_S400E_SHA = {
    b"S400ECommandSet": "327d1e31c7c29fc1b9b8d26c7ef198751239e2890c45faf35e12beffe93f7b95",
    b"S400E_MTS_CommandSet": "ad52ed14c13b2c1d015cb8ba501229e8a06f9b104ce4a3f654195b0c5f362149",
    b"S400ECommandSet_Deployed": "4bd3ab4b7c41e341b4b9d075a2895b3715a35e9beec5e03e01a4f871304501b2",
    b"S400ECommandSet_AA": "dcaa14f6a272770d1a853e15f0db422aaa2c8d9d04b1020cbfbc653452538a11",
    b"S400ECommandSet_ABM": "a2e8f4fc0af392dc369301a2a41b31007aea47027deadb0afa1db100c4af1c4c",
}

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
OCLU_KEY = r"data\ini\objectcreationlist_usapac3.ini"
CSU_KEY = r"data\ini\commandset_usapac3.ini"
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

REQUIRED_BUTTONS = (
    b"Command_Stop",
    b"Command_ADS_MTS_SWITCH",
    b"Command_AADS_AA_Mode",
    b"Command_AADS_ABM_Mode",
    b"Command_ADSCombatMode",
    b"Command_ADS_ABM_CombatMode",
    b"Command_FireControlPack",
    b"Command_ConstructUSAPAC3",
)

SET_BUTTONS = {
    b"USAPAC3CommandSet": (b"Command_ADS_MTS_SWITCH", b"Command_AADS_AA_Mode", b"Command_AADS_ABM_Mode", b"Command_Stop"),
    b"USAPAC3CommandSet_AA": (b"Command_ADSCombatMode", b"Command_Stop"),
    b"USAPAC3CommandSet_ABM": (b"Command_ADS_ABM_CombatMode", b"Command_Stop"),
    b"USAPAC3CommandSet_Deployed": (b"Command_FireControlPack", b"Command_Stop"),
}


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


def commands_in_set(block: bytes) -> list[bytes]:
    return re.findall(rb"(?m)^\s*\d+\s*=\s*(\S+)", block)


def main() -> int:
    raw, ents = read_big(DATA)
    amap = {key(n): (n, raw[o : o + s]) for n, o, s in ents}

    if CSU_KEY in amap:
        fail("CommandSet_USAPAC3.ini still packed; duplicate-name crash risk")
    for need in (OBJ_KEY, WEP_KEY, OCLU_KEY, THAAD_KEY, CS_KEY, CB_KEY, OCL_KEY, WPN_KEY):
        if need not in amap:
            fail(f"missing packed {need}")

    obj = amap[OBJ_KEY][1]
    wep = amap[WEP_KEY][1]
    oclu = amap[OCLU_KEY][1]
    thaad = amap[THAAD_KEY][1]
    cs = amap[CS_KEY][1]
    cb = amap[CB_KEY][1]
    ocl = amap[OCL_KEY][1]
    oclz = amap[OCLZ_KEY][1]
    weapon = amap[WPN_KEY][1]

    if sha256(cs) == BEFORE_CS_SHA:
        fail("CommandSet.ini still the 748 file without USAPAC3CommandSet")

    for name in UNIQUE_SETS:
        if count_headers(cs, b"CommandSet", name) != 1:
            fail(f"live CommandSet.ini missing {name.decode()}")
        extra = [
            n
            for n, o, s in ents
            if count_headers(raw[o : o + s], b"CommandSet", name) and key(n) != CS_KEY
        ]
        if extra:
            fail(f"{name.decode()} also packed in {extra}")

    for name, digest in S400E_SHA.items():
        blocks = extract_top_level(cs, b"CommandSet", name)
        if len(blocks) != 1:
            fail(f"{name.decode()} count {len(blocks)}")
        if sha256(blocks[0]) != digest:
            fail(f"{name.decode()} mutated")

    for btn in REQUIRED_BUTTONS:
        if count_headers(cb, b"CommandButton", btn) != 1:
            fail(f"CommandButton {btn.decode()} count {count_headers(cb, b'CommandButton', btn)}")

    for set_name, buttons in SET_BUTTONS.items():
        block = extract_top_level(cs, b"CommandSet", set_name)[0]
        found = commands_in_set(block)
        for btn in buttons:
            if btn not in found:
                fail(f"{set_name.decode()} missing {btn.decode()}")
            if count_headers(cb, b"CommandButton", btn) != 1:
                fail(f"{set_name.decode()} names undefined {btn.decode()}")

    init = extract_top_level(cs, b"CommandSet", b"USAPAC3CommandSet")[0]
    if commands_in_set(init) != [
        b"Command_ADS_MTS_SWITCH",
        b"Command_AADS_AA_Mode",
        b"Command_AADS_ABM_Mode",
        b"Command_Stop",
    ]:
        fail(f"initial menu slots {commands_in_set(init)}")

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
    if b"TriggeredBy     = Upgrade_AIM-120C" in mob:
        fail("MTS unexpectedly wired")
    if b"S400ECommandSet" in mob:
        fail("mobile still uses S400E")

    combat = extract_top_level(obj, b"Object", b"USAPAC3_CombatMode")
    if len(combat) != 1:
        fail("CombatMode count")
    if b"CommandSet           = USAPAC3CommandSet_Deployed" not in combat[0]:
        fail("combat CommandSet")
    if b"OCL = FINAL    OCL_USAPAC3_Pack" not in combat[0]:
        fail("pack OCL")

    if sha256(thaad) != THAAD_SHA:
        fail("US_M1120.ini sha")
    if sha256(weapon) != WEAPON_SHA:
        fail("Weapon.ini sha")
    if sha256(cb) != CB_SHA:
        fail("CommandButton.ini sha")
    if sha256(ocl) != OCL_SHA:
        fail("ObjectCreationList.ini sha")
    if sha256(oclz) != OCLZ_SHA:
        fail("OCL ZZZZ sha")
    thaad_obj = extract_top_level(thaad, b"Object", b"US_THAAD")[0]
    if b"CommandSet           = S400ECommandSet" not in thaad_obj:
        fail("THAAD CommandSet mutated")

    overlay_cs = (ROOT / "patch/Data/INI/CommandSet.ini").read_bytes()
    installer_cs = (INSTALLER / "CommandSet.ini").read_bytes()
    merged_cs = (MERGED / "CommandSet.ini").read_bytes()
    if installer_cs != cs:
        fail("installer CommandSet.ini != packed")
    if merged_cs != cs:
        fail("merged CommandSet.ini != packed")
    if (INSTALLER / "CommandButton.ini").read_bytes() != cb:
        fail("installer CommandButton.ini drifted")
    if len(cs) <= 450860:
        fail("CommandSet.ini was not extended")
    if sha256(cs[:450860]) != BEFORE_CS_SHA:
        fail("CommandSet.ini prefix is not the 748 file")

    for name, digest in OVERLAY_S400E_SHA.items():
        blocks = extract_top_level(overlay_cs, b"CommandSet", name)
        if len(blocks) != 1 or sha256(blocks[0]) != digest:
            fail(f"overlay {name.decode()} mutated")
    for name in UNIQUE_SETS:
        if count_headers(overlay_cs, b"CommandSet", name) != 1:
            fail(f"overlay CommandSet.ini missing {name.decode()}")

    unique_src = ROOT / "patch/Data/INI/CommandSet_USAPAC3.ini"
    indep_src = ROOT / "docs/specter-usapac3/independent/CommandSet_USAPAC3.ini"
    if not unique_src.exists() or not indep_src.exists():
        fail("prior PAC-3 unique CommandSet source deleted")
    for name in UNIQUE_SETS:
        if count_headers(unique_src.read_bytes(), b"CommandSet", name) != 1:
            fail(f"overlay unique source lost {name.decode()}")

    if sha_file(ART2) != ART2_SHA:
        fail("ART TWO mutated")
    art1 = MERGED / "_SPEC_ART_ONE.big"
    if art1.exists() and sha_file(art1) != ART1_SHA:
        fail("ART ONE mutated")
    if b"UsaPac3" in obj or b"pac3mis" in obj:
        fail("New Donor in object")
    if not (ROOT / "docs/specter-usapac3/archive/failed-impl/Art/W3D/UsaPac3Car.W3D").exists():
        fail("failed-impl archive missing")
    if not (ROOT / "docs/specter-usapac3/abtest").is_dir():
        fail("abtest missing")
    if b"Object AmericaMobileSamSiteMIM104F" not in raw:
        fail("Patriot missing")
    if b"Command_ConstructAmerica_AD_NASAMS" not in raw:
        fail("NASAMS missing")
    if b"  6  = Command_ConstructUSAPAC3" not in cs:
        fail("CC slot 6 lost")

    hq = (ROOT / "patch/Data/INI/CommandSet_FactionExpansion_Armies.ini").read_text("latin-1")
    if "6 = Command_ConstructAmerica_AD_NASAMS" not in hq:
        fail("HQ NASAMS")
    if "Command_ConstructUSAPAC3" in hq:
        fail("HQ USAPAC3")

    zip_path = CSFIX / "SPECTER_USAPAC3_COMMANDSET_FIX.zip"
    if zip_path.exists():
        import zipfile

        with zipfile.ZipFile(zip_path) as zf:
            names = set(zf.namelist())
            for need in (
                "_SPEC_DATA_ONE.big",
                "CommandSet.ini",
                "CommandButton.ini",
                "Data/INI/CommandSet.ini",
                "Launch_Specter.bat",
            ):
                if need not in names:
                    fail(f"ZIP missing {need}")
            zip_cs = zf.read("CommandSet.ini")
            zip_data_cs = zf.read("Data/INI/CommandSet.ini")
            if zip_cs != cs or zip_data_cs != cs:
                fail("ZIP CommandSet.ini != packed")
            if sha256(zf.read("CommandButton.ini")) != CB_SHA:
                fail("ZIP CommandButton.ini drifted")

    print("STATIC_OK")
    print("DATA", sha_file(DATA), DATA.stat().st_size, "entries", len(ents))
    print("ART2", sha_file(ART2), ART2.stat().st_size)
    print("US_M1120.ini", sha256(thaad))
    print("Weapon.ini", sha256(weapon))
    print("CommandSet.ini", sha256(cs), "bytes", len(cs))
    print("CommandButton.ini", sha256(cb))
    print("ObjectCreationList.ini", sha256(ocl))
    print("INGAME_ZH: not executed")
    print("STAGE: USAPAC3 CommandSets registered in live CommandSet.ini")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
