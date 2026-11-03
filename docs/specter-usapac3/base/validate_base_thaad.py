#!/usr/bin/env python3
"""Static validation for USAPAC3 stage-1 THAAD clone. Zero Hour is not run."""
from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

ROOT = Path("/workspace")
MERGED = ROOT / "docs/specter-usapac3/merged"
DATA = MERGED / "_SPEC_DATA_ONE.big"
ART2 = MERGED / "_SPEC_ART_TWO.big"
BASE_OBJ = ROOT / "docs/specter-usapac3/base/USAPAC3.ini"
BASE_WEP = ROOT / "docs/specter-usapac3/base/Weapon_USAPAC3.ini"
OVERLAY_OBJ = (
    ROOT / "patch/Data/INI/Object/Specter/United States Of America/AirDefense/USAPAC3.ini"
)
OVERLAY_WEP = ROOT / "patch/Data/INI/Weapon_USAPAC3.ini"

CLEAN_ART2_SHA = "2a65d89d60db9696a2b3a69df5a1c7cb173e10de027e7be6aedb6ba3cb47ae38"
CLEAN_ART1_SHA = "15ffb0dcbf6e0a02e8ece6421efac1331c391b48d8afa6b108550df89653df66"
CLEAN_THAAD_NEEDLE = b"Object US_THAAD\r\n"

OBJ_KEY = r"data\ini\object\specter\united states of america\airdefense\usapac3.ini"
WEP_KEY = r"data\ini\weapon_usapac3.ini"
CS_KEY = r"data\ini\commandset.ini"
CB_KEY = r"data\ini\commandbutton.ini"
THAAD_KEY = r"data\ini\object\specter\united states of america\airdefense\us_m1120.ini"


def fail(msg: str) -> None:
    print("FAIL:", msg)
    sys.exit(1)


def sha_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def main() -> int:
    raw, ents = read_big(DATA)
    amap = {key(n): (n, raw[o : o + s]) for n, o, s in ents}

    if OBJ_KEY not in amap:
        fail("packed Object USAPAC3 path missing")
    if WEP_KEY not in amap:
        fail("packed Weapon_USAPAC3.ini missing")

    obj = amap[OBJ_KEY][1]
    wep = amap[WEP_KEY][1]
    cs = amap[CS_KEY][1]
    cb = amap[CB_KEY][1]
    thaad_file = amap[THAAD_KEY][1]

    defs = re.findall(rb"(?m)^Object\s+USAPAC3\s*$", raw)
    # count only Object USAPAC3 headers, not substring USAPAC3_Weapon
    obj_files = [
        n
        for n, o, s in ents
        if re.search(rb"(?m)^Object\s+USAPAC3\s*$", raw[o : o + s])
    ]
    if len(obj_files) != 1:
        fail(f"Object USAPAC3 winning files: {obj_files}")
    if len(defs) != 1:
        fail(f"Object USAPAC3 defs={len(defs)}")

    if not re.search(rb"(?m)^Object\s+USAPAC3\s*$", obj):
        fail("packed object header")
    if b"Draw = W3DTruckDraw ModuleTag_01" not in obj:
        fail("Draw")
    for model in (b"US_M1120\r\n", b"US_M1120D\r\n", b"US_M1120_A\r\n", b"US_M1120_AD\r\n"):
        if model not in obj and model.replace(b"\r\n", b"\n") not in obj:
            fail(f"missing model {model}")
    if b"UsaPac3" in obj or b"pac3mis" in obj or b"ampac3" in obj.lower():
        fail("New Donor art in object")
    if b"DeployStyleAIUpdate" not in obj:
        fail("AI")
    if b"Generic8x8Locomotor" not in obj:
        fail("loco")
    if b"BuildCost            = 3876" not in obj:
        fail("cost")
    if b"BuildTime            = 18.6" not in obj:
        fail("time")
    if b"Side                 = America" not in obj:
        fail("side")
    if b"Prerequisites" in obj:
        fail("Prerequisites present")
    if re.search(rb"(?m)^\s*Science\s*=", obj):
        fail("Science on object")
    if b"Weapon             = SECONDARY USAPAC3_Weapon" not in obj:
        fail("secondary weapon")
    if b"Weapon             = TERTIARY  USAPAC3_Weapon_ABM" not in obj:
        fail("tertiary weapon")
    if b"S400R_Deploy" in obj:
        fail("object still names THAAD weapons")
    if b"Locomotor = SET_NORMAL      Generic8x8Locomotor" not in obj:
        fail("locomotor line")
    if b"OCL_THAAD_Deployed" not in obj:
        fail("deploy OCL")
    if b"CommandSet           = S400ECommandSet" not in obj:
        fail("unit CommandSet")

    wep_defs = re.findall(rb"(?m)^Weapon\s+USAPAC3_Weapon\s*$", wep)
    abm_defs = re.findall(rb"(?m)^Weapon\s+USAPAC3_Weapon_ABM\s*$", wep)
    if len(wep_defs) != 1 or len(abm_defs) != 1:
        fail("weapon def counts")
    if re.search(rb"(?m)^\s*ProjectileObject\s*=", wep):
        fail("unexpected projectile on cloned deploy weapons")
    extra_wep = [
        n
        for n, o, s in ents
        if re.search(rb"(?m)^Weapon\s+USAPAC3_Weapon\s*$", raw[o : o + s])
        and key(n) != WEP_KEY
    ]
    if extra_wep:
        fail(f"duplicate weapon files {extra_wep}")

    # CommandButton before CommandSet reference: both in first-win ControlBar files
    if not re.search(rb"(?m)^CommandButton\s+Command_ConstructUSAPAC3\s*$", cb):
        fail("button missing")
    if cb.count(b"CommandButton Command_ConstructUSAPAC3") != 1:
        fail("button count")
    if not re.search(
        rb"(?m)^CommandButton\s+Command_ConstructUSAPAC3\s*$\r?\n"
        rb"  Command\s+=\s+UNIT_BUILD\s*$\r?\n"
        rb"  Object\s+=\s+USAPAC3\s*$",
        cb,
    ):
        fail("button Object")
    if re.search(rb"(?m)^\s*Science\s*=", cb.split(b"CommandButton Command_ConstructUSAPAC3")[1].split(b"End")[0]):
        fail("Science on button")
    extra_btn = [
        n
        for n, o, s in ents
        if b"CommandButton Command_ConstructUSAPAC3" in raw[o : o + s]
        and key(n) != CB_KEY
    ]
    if extra_btn:
        fail(f"duplicate button files {extra_btn}")

    m = re.search(
        rb"CommandSet AmericaCommandCenterCommandSet\r?\n(.*?)End",
        cs,
        re.S,
    )
    if not m:
        fail("CC missing")
    block = m.group(1)
    if b"6  = Command_ConstructUSAPAC3" not in block:
        fail("slot 6")
    if b"1  = Command_ConstructAmericaDozer" not in block:
        fail("slot 1")
    if b"12  = Command_ConstructAmericaVehicleUH60" not in block:
        fail("slot 12")
    if len(re.findall(rb"(?m)^CommandSet\s+AmericaCommandCenterCommandSet\s*$", cs)) != 1:
        fail("duplicate CC set")

    # THAAD original unchanged
    thaad_objs = extract_top_level(thaad_file, b"Object", b"US_THAAD")
    if len(thaad_objs) != 1:
        fail("US_THAAD count in US_M1120.ini")
    if b"BuildCost            = 3000" not in thaad_objs[0]:
        fail("THAAD cost mutated")
    if b"Object USAPAC3" in thaad_file:
        fail("USAPAC3 leaked into US_M1120.ini")
    if b"Weapon             = SECONDARY S400R_Deploy" not in thaad_objs[0]:
        fail("THAAD weapons mutated")

    # overlay matches packed
    if not BASE_OBJ.exists() or BASE_OBJ.read_bytes() != obj:
        fail("base USAPAC3.ini != packed")
    if not BASE_WEP.exists() or BASE_WEP.read_bytes() != wep:
        fail("base Weapon_USAPAC3.ini != packed")
    if not OVERLAY_OBJ.exists() or OVERLAY_OBJ.read_bytes() != obj:
        fail("overlay object != packed")
    if not OVERLAY_WEP.exists() or OVERLAY_WEP.read_bytes() != wep:
        fail("overlay weapon != packed")

    loose_cs = (MERGED / "CommandSet.ini").read_bytes()
    if loose_cs != cs:
        fail("merged CommandSet.ini != packed")
    loose_cb = (MERGED / "CommandButton.ini").read_bytes()
    if loose_cb != cb:
        fail("merged CommandButton.ini != packed")
    inst_cs = (ROOT / "patch/tools/installer/CommandSet.ini").read_bytes()
    if inst_cs != cs:
        fail("installer CommandSet.ini != packed")
    inst_cb = (ROOT / "patch/tools/installer/CommandButton.ini").read_bytes()
    if inst_cb != cb:
        fail("installer CommandButton.ini != packed")

    # HQ overlay still NASAMS, no USAPAC3
    hq = (ROOT / "patch/Data/INI/CommandSet_FactionExpansion_Armies.ini").read_text("latin-1")
    if "6 = Command_ConstructAmerica_AD_NASAMS" not in hq:
        fail("HQ NASAMS")
    if "Command_ConstructUSAPAC3" in hq:
        fail("HQ has USAPAC3")
    if "5 = Command_ConstructAmerica_AD_THAAD" not in hq:
        fail("HQ THAAD")
    if "4 = Command_ConstructAmerica_AD_Patriot" not in hq:
        fail("HQ Patriot")

    # ART TWO unchanged, no New Donor PAC-3
    if sha_file(ART2) != CLEAN_ART2_SHA:
        fail("ART TWO mutated")
    art_raw, art_ents = read_big(ART2)
    for n, o, s in art_ents:
        low = n.lower()
        if "usapac3" in low or "pac3mis_m" in low or "ampac3" in low:
            fail(f"ART TWO has {n}")
    keys = {key(n) for n, o, s in art_ents}
    for keep in (
        r"art\w3d\us_m1120.w3d",
        r"art\w3d\us_m1120_a.w3d",
        r"art\w3d\abpatriot.w3d",
        r"art\w3d\pac3_sudarb.w3d",
    ):
        if keep not in keys:
            fail(f"missing ART {keep}")

    art1 = MERGED / "_SPEC_ART_ONE.big"
    if art1.exists() and sha_file(art1) != CLEAN_ART1_SHA:
        fail("ART ONE mutated")

    # Patriot / NASAMS still present
    if b"Object AmericaMobileSamSiteMIM104F" not in raw:
        fail("Patriot truck missing")
    if b"Command_ConstructAmerica_AD_NASAMS" not in raw:
        fail("NASAMS command missing")
    if b"AmericaJetF117Clean" not in raw:
        fail("F-117 missing")
    if b"AmericaJetB21Clean" not in raw:
        fail("B-21 missing")

    print("STATIC_OK")
    print("DATA", sha_file(DATA), DATA.stat().st_size, "entries", len(ents))
    print("ART2", sha_file(ART2), ART2.stat().st_size)
    print("CommandSet", sha_file(MERGED / "CommandSet.ini"))
    print("CommandButton", sha_file(MERGED / "CommandButton.ini"))
    print("Object USAPAC3 defs=1 path=", amap[OBJ_KEY][0])
    print("INGAME_ZH: not executed")
    print("STAGE: base THAAD clone; New Donor look not applied")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
