#!/usr/bin/env python3
"""USA HeavyAirBase support aircraft — donor DATA recovery + ART import.

ORIGINAL DONOR DATA recovered from DONOR_INI.rar (America.ini):
  USAC17GlobalMaster  -> AmericaJetC17Globemaster (IUAC17HXNew)
  avionE737           -> AmericaJetE737AEW (KVE737) + E-3 StealthDetector
  E2avionHE           -> E2avionHE (AVHawk + AVHawk_P) + E-3 StealthDetector
  USAHelixV22         -> USAHelixV22 (AVOsprey family) VTOL transport

AC-130 frozen. E-3 preserved (not duplicated). CSF untouched.
"""
from __future__ import annotations

import hashlib
import re
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
DONOR = Path("/tmp/donor_art_extract/Art")
OBJ = ROOT / "Data/INI/Object/Specter/United States Of America"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_HEAVY_SUPPORT_RECONSTRUCT.zip"
OUT_HASH = ROOT / "Release/DATA_USA_HEAVY_SUPPORT_RECONSTRUCT_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_HEAVY_SUPPORT_RECONSTRUCT_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_HEAVY_SUPPORT_RECONSTRUCT_REPORT.txt"
VERIFY = MASTER / "_extract_usa_heavy_support_reconstruct_verify"
GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_FROZEN = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

HEAVY_CS = """CommandSet America_HeavyAirBaseCommandSet
  1  = Command_ConstructAmericaJetB2Spirit
  2  = Command_ConstructAmericaJetB21
  3  = Command_ConstructAmericaJetB52H
  4  = Command_ConstructAmericaJetB1R
  5  = Command_ConstructAmericaJetE3AWACS
  6  = Command_Upgrade_NuclearTipWarhead2
  7  = Command_ConstructAmericaJetAC130
  8  = Command_ConstructAmericaJetC17Globemaster
  9  = Command_ConstructAmericaJetE737AEW
  10 = Command_ConstructAmericaE2avionHE
  11 = Command_ConstructAmericaV22
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

BUTTONS = {
    "Command_ConstructAmericaJetC17Globemaster": """CommandButton Command_ConstructAmericaJetC17Globemaster
  Command       = UNIT_BUILD
  Object        = AmericaJetC17Globemaster
  TextLabel     = CONTROLBAR:C17GlobalMaster
  ButtonImage   = C17GlobalMaster
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:C17GlobalMasterif
End
""",
    "Command_ConstructAmericaJetE737AEW": """CommandButton Command_ConstructAmericaJetE737AEW
  Command       = UNIT_BUILD
  Object        = AmericaJetE737AEW
  TextLabel     = CONTROLBAR:E737
  ButtonImage   = avionE737
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:E737if
End
""",
    "Command_ConstructAmericaE2avionHE": """CommandButton Command_ConstructAmericaE2avionHE
  Command       = UNIT_BUILD
  Object        = E2avionHE
  TextLabel     = CONTROLBAR:E2avionHE
  ButtonImage   = E2avionHE
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:E2avionHEif
End
""",
    "Command_ConstructAmericaV22": """CommandButton Command_ConstructAmericaV22
  Command       = UNIT_BUILD
  Object        = USAHelixV22
  TextLabel     = CONTROLBAR:V22
  ButtonImage   = V22
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:V22if
End
""",
}

MAPPED = """
MappedImage C17GlobalMaster
  Texture = C17GlobalMasterTB.tga
  TextureWidth = 150
  TextureHeight = 113
  Coords = Left:0 Top:0 Right:150 Bottom:113
  Status = NONE
End

MappedImage avionE737
  Texture = avionE737.tga
  TextureWidth = 140
  TextureHeight = 111
  Coords = Left:0 Top:0 Right:140 Bottom:111
  Status = NONE
End

MappedImage E2avionHE
  Texture = AvionE2.tga
  TextureWidth = 150
  TextureHeight = 114
  Coords = Left:0 Top:0 Right:150 Bottom:114
  Status = NONE
End

MappedImage V22
  Texture = LSFV22TB.tga
  TextureWidth = 150
  TextureHeight = 116
  Coords = Left:0 Top:0 Right:150 Bottom:116
  Status = NONE
End
"""

ART_FILES = [
    # C-17
    ("Art\\W3D\\IUAC17HXNew.W3D", DONOR / "w3d" / "IUAC17HXNew.W3D"),
    ("Art\\Textures\\IUCC17THXNew.dds", DONOR / "Textures" / "IUCC17THXNew.dds"),
    ("Art\\Textures\\C17GlobalMaster.tga", DONOR / "Textures" / "C17GlobalMaster.tga"),
    ("Art\\Textures\\C17GlobalMasterTB.tga", DONOR / "Textures" / "C17GlobalMasterTB.tga"),
    ("Art\\Textures\\MeCHousecolor.dds", DONOR / "Textures" / "MeCHousecolor.dds"),
    # E-737
    ("Art\\W3D\\KVE737.W3D", DONOR / "w3d" / "KVE737.W3D"),
    ("Art\\Textures\\KVE737.dds", DONOR / "Textures" / "KVE737.dds"),
    ("Art\\Textures\\avionE737.tga", DONOR / "Textures" / "avionE737.tga"),
    ("Art\\Textures\\avionE737TB.tga", DONOR / "Textures" / "avionE737TB.tga"),
    # E2avionHE / AVHawk (donor model family for E2avionHE)
    ("Art\\W3D\\AVHawk.W3D", DONOR / "w3d" / "AVHawk.W3D"),
    ("Art\\W3D\\AVHawk_D.W3D", DONOR / "w3d" / "AVHawk_D.W3D"),
    ("Art\\W3D\\AVHawk_D1.W3D", DONOR / "w3d" / "AVHawk_D1.W3D"),
    ("Art\\W3D\\AVHawk_P.W3D", DONOR / "w3d" / "AVHawk_P.W3D"),
    ("Art\\Textures\\AvHawk.dds", DONOR / "Textures" / "AvHawk.dds"),
    ("Art\\Textures\\AvHawk_D.dds", DONOR / "Textures" / "AvHawk_D.dds"),
    ("Art\\Textures\\AvHawk_D1.dds", DONOR / "Textures" / "AvHawk_D1.dds"),
    ("Art\\Textures\\E2avionHE.tga", DONOR / "Textures" / "E2avionHE.tga"),
    ("Art\\Textures\\E2avionHETB.tga", DONOR / "Textures" / "E2avionHETB.tga"),
    ("Art\\Textures\\AmericaE2avion.tga", DONOR / "Textures" / "AmericaE2avion.tga"),
    ("Art\\Textures\\AvionE2.tga", DONOR / "Textures" / "AvionE2.tga"),
    # Osprey / AVOsprey
    ("Art\\W3D\\AVOsprey.W3D", DONOR / "w3d" / "AVOsprey.W3D"),
    ("Art\\W3D\\AVOsprey_D.W3D", DONOR / "w3d" / "AVOsprey_D.W3D"),
    ("Art\\W3D\\AVOsprey_A1.W3D", DONOR / "w3d" / "AVOsprey_A1.W3D"),
    ("Art\\W3D\\AVOsprey_A2.W3D", DONOR / "w3d" / "AVOsprey_A2.W3D"),
    ("Art\\W3D\\AVOsprey_A3.W3D", DONOR / "w3d" / "AVOsprey_A3.W3D"),
    ("Art\\W3D\\AVOsprey_A4.W3D", DONOR / "w3d" / "AVOsprey_A4.W3D"),
    ("Art\\W3D\\AVOsprey_DA1.W3D", DONOR / "w3d" / "AVOsprey_DA1.W3D"),
    ("Art\\W3D\\AVOsprey_DA2.W3D", DONOR / "w3d" / "AVOsprey_DA2.W3D"),
    ("Art\\W3D\\AVOsprey_DA3.W3D", DONOR / "w3d" / "AVOsprey_DA3.W3D"),
    ("Art\\W3D\\AVOsprey_DA4.W3D", DONOR / "w3d" / "AVOsprey_DA4.W3D"),
    ("Art\\Textures\\AVOsprey.dds", DONOR / "Textures" / "AVOsprey.dds"),
    ("Art\\Textures\\AVOsprey_D.dds", DONOR / "Textures" / "AVOsprey_D.dds"),
    ("Art\\Textures\\AVOsprey_H.dds", DONOR / "Textures" / "AVOsprey_H.dds"),
    ("Art\\Textures\\AVOsprey_P.dds", DONOR / "Textures" / "AVOsprey_P.dds"),
    ("Art\\Textures\\LSFV22TB.tga", DONOR / "Textures" / "LSFV22TB.tga"),
    ("Art\\Textures\\V22.tga", DONOR / "Textures" / "V22.tga"),
]


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path):
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries = []
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        entries.append((name, off, size))
    return entries, data


def build_big(file_map: dict[str, bytes]) -> bytes:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16 + sum(8 + len(n.encode("latin1")) + 1 for n, _ in items)
    offset = header_size
    index, blobs = [], []
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray(b"BIGF")
    out += struct.pack(">III", offset, len(items), header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1") + b"\x00"
    for b in blobs:
        out += b
    return bytes(out)


def patch_commandset(cs: str) -> str:
    pat = re.compile(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n.*?^End\s*$",
        re.M | re.S,
    )
    if not pat.search(cs):
        raise SystemExit("Heavy CS missing")
    return pat.sub(HEAVY_CS.rstrip(), cs, count=1)


def ensure_buttons(cb: str) -> str:
    for name, block in BUTTONS.items():
        if re.search(rf"^CommandButton\s+{re.escape(name)}\s*$", cb, re.M):
            cb = re.sub(
                rf"CommandButton\s+{re.escape(name)}\s*\n.*?^End\s*$",
                block.rstrip(),
                cb,
                count=1,
                flags=re.M | re.S,
            )
        else:
            anchor = re.search(
                r"CommandButton\s+Command_ConstructAmericaJetAC130\s*\n.*?^End\s*$",
                cb,
                re.M | re.S,
            )
            if not anchor:
                raise SystemExit("AC130 button missing for anchor")
            cb = cb[: anchor.end()] + "\n\n" + block + cb[anchor.end() :]
    return cb


def ensure_mapped(mi: str) -> str:
    for name in ["C17GlobalMaster", "avionE737", "E2avionHE", "V22"]:
        block_m = re.search(
            rf"^MappedImage\s+{re.escape(name)}\s*\n.*?^End\s*$",
            MAPPED,
            re.M | re.S,
        )
        block = block_m.group(0)
        if re.search(rf"^MappedImage\s+{re.escape(name)}\s*$", mi, re.M):
            mi = re.sub(
                rf"MappedImage\s+{re.escape(name)}\s*\n.*?^End\s*$",
                block,
                mi,
                count=1,
                flags=re.M | re.S,
            )
        else:
            mi = mi.rstrip() + "\n\n" + block + "\n"
    return mi


def append_ini_once(blob: bytes, marker: bytes, addition: str) -> bytes:
    text = blob.decode("latin1")
    if marker.decode("latin1") in text:
        # replace existing named block if present
        name = marker.decode("latin1").split(None, 1)[1] if b" " in marker else ""
        kind = marker.decode("latin1").split()[0]
        if name and re.search(rf"^{kind}\s+{re.escape(name)}\s*$", text, re.M):
            text = re.sub(
                rf"^{kind}\s+{re.escape(name)}\s*\n.*?^End\s*$",
                addition.rstrip(),
                text,
                count=1,
                flags=re.M | re.S,
            )
            return text.encode("latin1")
    return (text.rstrip() + "\n\n" + addition.strip() + "\n").encode("latin1")


def main() -> None:
    dentries, dblob = read_big(DATA_BIG)
    aentries, ablob = read_big(ART_BIG)
    dmap = {n.replace("/", "\\"): dblob[o : o + s] for n, o, s in dentries}
    amap = {n.replace("/", "\\"): ablob[o : o + s] for n, o, s in aentries}

    if sha256(dmap["Data\\English\\generals.csf"]) != GOOD_CSF:
        raise SystemExit("CSF is not known-good — abort")

    ac130_key = (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
    )
    if sha256(dmap[ac130_key]) != AC130_FROZEN:
        raise SystemExit("AC-130 changed unexpectedly — abort freeze")

    # Snapshot E-3 presence
    usa = dmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
    ]
    assert b"Object AmericaJetE3AWACS" in usa
    e3_sha = sha256(usa)

    large_cs = re.search(
        r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)End",
        dmap["Data\\INI\\CommandSet.ini"].decode("latin1"),
        re.S,
    ).group(1)

    # Objects
    for fname, key_name in [
        ("AmericaJetC17Globemaster.ini", "AmericaJetC17Globemaster.ini"),
        ("AmericaJetE737AEW.ini", "AmericaJetE737AEW.ini"),
        ("E2avionHE.ini", "E2avionHE.ini"),
        ("USAHelixV22.ini", "USAHelixV22.ini"),
    ]:
        src = OBJ / fname
        if not src.exists():
            raise SystemExit(f"missing {src}")
        dmap[
            f"Data\\INI\\Object\\Specter\\United States Of America\\{key_name}"
        ] = src.read_bytes()

    # CommandSet / Button / MappedImage
    cs = patch_commandset(dmap["Data\\INI\\CommandSet.ini"].decode("latin1"))
    # inject C17 + V22 commandsets
    cs_add = Path("/tmp/donor_C17GlobalMasterCommandSet.ini").read_text()
    v22_cs = Path("/tmp/donor_AmericaVehicleV22CommandSet.ini").read_text()
    if "C17GlobalMasterCommandSet" not in cs:
        cs = cs.rstrip() + "\n\n" + cs_add.strip() + "\n"
    else:
        cs = re.sub(
            r"CommandSet\s+C17GlobalMasterCommandSet\s*\n.*?^End\s*$",
            cs_add.strip(),
            cs,
            count=1,
            flags=re.M | re.S,
        )
    if "AmericaVehicleV22CommandSet" not in cs:
        cs = cs.rstrip() + "\n\n" + v22_cs.strip() + "\n"
    else:
        cs = re.sub(
            r"CommandSet\s+AmericaVehicleV22CommandSet\s*\n.*?^End\s*$",
            v22_cs.strip(),
            cs,
            count=1,
            flags=re.M | re.S,
        )
    large2 = re.search(
        r"CommandSet\s+America_LargeAirBaseCommandSet\s*\n(.*?)End", cs, re.S
    ).group(1)
    assert large2 == large_cs
    dmap["Data\\INI\\CommandSet.ini"] = cs.encode("latin1")

    cb = dmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    for btn in [
        "Command_ConstructAmericaJetB2Spirit",
        "Command_ConstructAmericaJetE3AWACS",
        "Command_ConstructAmericaJetAC130",
    ]:
        assert re.search(rf"^CommandButton\s+{btn}\s*$", cb, re.M), btn
    # Ensure E3 button still targets AmericaJetE3AWACS
    e3b = re.search(
        r"CommandButton\s+Command_ConstructAmericaJetE3AWACS\s*\n(.*?)End", cb, re.S
    )
    assert e3b and "AmericaJetE3AWACS" in e3b.group(0)
    dmap["Data\\INI\\CommandButton.ini"] = ensure_buttons(cb).encode("latin1")

    mi_key = "Data\\INI\\MappedImages\\HandCreated\\HandCreatedMappedImages.INI"
    dmap[mi_key] = ensure_mapped(dmap[mi_key].decode("latin1")).encode("latin1")

    # Locators / Armor
    loco_key = "Data\\INI\\Locomotor.ini"
    loco = dmap[loco_key]
    for path, marker in [
        (
            Path("/tmp/donor_C17GlobalMasterLocomotor.ini"),
            b"Locomotor C17GlobalMasterLocomotor",
        ),
        (Path("/tmp/donor_LSFV22Locomotor.ini"), b"Locomotor LSFV22Locomotor"),
    ]:
        loco = append_ini_once(loco, marker, path.read_text())
    dmap[loco_key] = loco

    armor_key = "Data\\INI\\Armor.ini"
    dmap[armor_key] = append_ini_once(
        dmap[armor_key],
        b"Armor V22Armor",
        Path("/tmp/donor_V22Armor.ini").read_text(),
    )

    # ART
    added = []
    for dest, src in ART_FILES:
        if not src.exists():
            raise SystemExit(f"Missing donor ART {src}")
        # always refresh these donor assets
        amap[dest] = src.read_bytes()
        added.append(dest)

    # Optional AVOsprey .tga referenced by A-models
    for tga in ["AVOsprey.tga", "AVOsprey_P.tga", "AVOsprey_H.tga", "AVOsprey_D.tga"]:
        src = DONOR / "Textures" / tga
        if src.exists():
            dest = f"Art\\Textures\\{tga}"
            amap[dest] = src.read_bytes()
            added.append(dest)

    new_data = build_big(dmap)
    new_art = build_big(amap)
    DATA_BIG.write_bytes(new_data)
    ART_BIG.write_bytes(new_art)

    # Verify
    import shutil

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    VERIFY.mkdir(parents=True)
    ve, vb = read_big(DATA_BIG)
    vmap = {n.replace("/", "\\"): vb[o : o + s] for n, o, s in ve}
    ae, ab = read_big(ART_BIG)
    anames = {n.lower().replace("/", "\\") for n, _, _ in ae}

    assert sha256(vmap["Data\\English\\generals.csf"]) == GOOD_CSF
    assert sha256(vmap[ac130_key]) == AC130_FROZEN
    assert (
        sha256(
            vmap[
                "Data\\INI\\Object\\Specter\\United States Of America\\USA_System.ini"
            ]
        )
        == e3_sha
    )

    vcs = vmap["Data\\INI\\CommandSet.ini"].decode("latin1")
    hm = re.search(
        r"CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)End", vcs, re.S
    )
    body = hm.group(1)
    for need in [
        "Command_ConstructAmericaJetB2Spirit",
        "Command_ConstructAmericaJetB21",
        "Command_ConstructAmericaJetB52H",
        "Command_ConstructAmericaJetB1R",
        "Command_ConstructAmericaJetE3AWACS",
        "Command_Upgrade_NuclearTipWarhead2",
        "Command_ConstructAmericaJetAC130",
        "Command_ConstructAmericaJetC17Globemaster",
        "Command_ConstructAmericaJetE737AEW",
        "Command_ConstructAmericaE2avionHE",
        "Command_ConstructAmericaV22",
        "Command_SetRallyPoint",
        "Command_Sell",
    ]:
        assert need in body, need

    # no duplicate C17 / AWACS
    assert body.count("C17") == 1
    assert body.count("E3AWACS") == 1
    assert "Command_ConstructAmericaJetAC130" in body

    vcb = vmap["Data\\INI\\CommandButton.ini"].decode("latin1")
    for btn, obj in [
        ("Command_ConstructAmericaJetC17Globemaster", "AmericaJetC17Globemaster"),
        ("Command_ConstructAmericaJetE737AEW", "AmericaJetE737AEW"),
        ("Command_ConstructAmericaE2avionHE", "E2avionHE"),
        ("Command_ConstructAmericaV22", "USAHelixV22"),
        ("Command_ConstructAmericaJetAC130", "AmericaJetAC130"),
        ("Command_ConstructAmericaJetE3AWACS", "AmericaJetE3AWACS"),
    ]:
        m = re.search(rf"CommandButton\s+{btn}\s*\n(.*?)End", vcb, re.S)
        assert m and "UNIT_BUILD" in m.group(0) and obj in m.group(0), btn

    checks = {
        "AmericaJetC17Globemaster.ini": [
            b"Object AmericaJetC17Globemaster",
            b"IUAC17HXNew",
            b"TransportContain",
            b"Ignore_Prerequisites",
        ],
        "AmericaJetE737AEW.ini": [
            b"Object AmericaJetE737AEW",
            b"KVE737",
            b"StealthDetectorUpdate",
            b"Ignore_Prerequisites",
        ],
        "E2avionHE.ini": [
            b"Object E2avionHE",
            b"AVHawk",
            b"StealthDetectorUpdate",
            b"Ignore_Prerequisites",
        ],
        "USAHelixV22.ini": [
            b"Object USAHelixV22",
            b"AVOsprey",
            b"ChinookAIUpdate",
            b"TransportContain",
            b"Ignore_Prerequisites",
        ],
    }
    for fname, needles in checks.items():
        blob = vmap[
            f"Data\\INI\\Object\\Specter\\United States Of America\\{fname}"
        ]
        for n in needles:
            assert n in blob, (fname, n)
        assert b"SCIENCE_Rank4" not in blob
        assert b"AmericaStrategyCenter" not in blob

    # C17 weapons none
    c17 = vmap[
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Globemaster.ini"
    ]
    assert b"Weapon = PRIMARY" not in c17
    assert b"HUGE_VEHICLE" in c17  # MBT capable

    for need in [
        "art\\w3d\\iuac17hxnew.w3d",
        "art\\w3d\\kve737.w3d",
        "art\\w3d\\avhawk.w3d",
        "art\\w3d\\avhawk_p.w3d",
        "art\\w3d\\avosprey.w3d",
        "art\\w3d\\avosprey_a1.w3d",
        "art\\textures\\kve737.dds",
        "art\\textures\\avosprey.dds",
        "art\\textures\\avhawk.dds",
        "art\\textures\\lsfv22tb.tga",
        "art\\textures\\avione2.tga",
        "art\\w3d\\us_ac130w.w3d",
    ]:
        assert need in anames, need

    assert b"C17GlobalMasterLocomotor" in vmap["Data\\INI\\Locomotor.ini"]
    assert b"LSFV22Locomotor" in vmap["Data\\INI\\Locomotor.ini"]
    assert b"Armor V22Armor" in vmap["Data\\INI\\Armor.ini"]

    report = []
    report.append("USA HEAVY SUPPORT — DONOR DATA RECOVERY + ART IMPORT")
    report.append("")
    report.append("SOURCE: DONOR_INI.rar / INI/object/America.ini (+ CommandButton/Set/Locomotor/Armor)")
    report.append("")
    report.append("--- C-17 Globemaster ---")
    report.append("Original donor DATA found = YES (Object USAC17GlobalMaster)")
    report.append("Real donor ART used = YES (IUAC17HXNew)")
    report.append("Behavior source = donor USAC17GlobalMaster (JetAI + TransportContain Slots=40 Allow INFANTRY VEHICLE HUGE_VEHICLE)")
    report.append("Final Object = AmericaJetC17Globemaster")
    report.append("Primary W3D = IUAC17HXNew")
    report.append("CommandButton = Command_ConstructAmericaJetC17Globemaster")
    report.append("HeavyAirBase slot = 8")
    report.append("Role = HEAVY STRATEGIC TRANSPORT")
    report.append("Weapons = NONE")
    report.append("Transport/radar functionality = TransportContain load/unload (MBT via HUGE_VEHICLE)")
    report.append("Buildable = YES")
    report.append("")
    report.append("--- E-737 ---")
    report.append("Original donor DATA found = YES (Object avionE737)")
    report.append("Real donor ART used = YES (KVE737)")
    report.append("Behavior source = donor avionE737 + StealthDetectorUpdate from working AmericaJetE3AWACS")
    report.append("Final Object = AmericaJetE737AEW")
    report.append("Primary W3D = KVE737")
    report.append("CommandButton = Command_ConstructAmericaJetE737AEW")
    report.append("HeavyAirBase slot = 9")
    report.append("Role = AEW&C / AIRBORNE EARLY WARNING")
    report.append("Weapons = NONE (donor ECM weapons stripped — missing Specter weapon deps)")
    report.append("Transport/radar functionality = Vision 1000 / Shroud 1610 + StealthDetectorUpdate")
    report.append("Buildable = YES")
    report.append("")
    report.append("--- E2avionHe ---")
    report.append("Original donor DATA found = YES (Object E2avionHE)")
    report.append("Real donor ART used = YES (AVHawk + AVHawk_P propeller family; icons E2avionHE/AvionE2)")
    report.append("Identity = E-2 Hawkeye (icons confirm; donor Object uses AVHawk turboprop/prop mesh)")
    report.append("Behavior source = donor E2avionHE + StealthDetectorUpdate from AmericaJetE3AWACS")
    report.append("Final Object = E2avionHE")
    report.append("Primary W3D = AVHawk")
    report.append("CommandButton = Command_ConstructAmericaE2avionHE")
    report.append("HeavyAirBase slot = 10")
    report.append("Role = AEW / carrier-style airborne radar")
    report.append("Weapons = NONE")
    report.append("Transport/radar functionality = Vision 1000 / Shroud 1610 + StealthDetectorUpdate")
    report.append("Buildable = YES")
    report.append("")
    report.append("--- Osprey ---")
    report.append("Original donor DATA found = YES (Object USAHelixV22)")
    report.append("Real donor ART used = YES (AVOsprey family)")
    report.append("Variant = V-22 / MV-22 tiltrotor (AVOsprey + LSFV22 icons)")
    report.append("Behavior source = donor USAHelixV22 (ChinookAIUpdate + LSFV22Locomotor + TransportContain Slots=10)")
    report.append("Final Object = USAHelixV22")
    report.append("Primary W3D = AVOsprey")
    report.append("CommandButton = Command_ConstructAmericaV22")
    report.append("HeavyAirBase slot = 11")
    report.append("Role = VTOL / TILTROTOR TRANSPORT")
    report.append("Weapons = NONE")
    report.append("Transport/radar functionality = infantry+light vehicle transport; Forbid HUGE_VEHICLE (no MBT)")
    report.append("Buildable = YES")
    report.append("")
    report.append("AC-130 CHANGED = NO")
    report.append("E-3 DUPLICATED = NO")
    report.append("C-17 DUPLICATED = NO")
    report.append("")
    report.append("America_HeavyAirBaseCommandSet:")
    report.append(hm.group(0))
    report.append("")
    report.append(f"ART files packed: {len(added)}")
    report.append(f"CSF sha256 unchanged = {GOOD_CSF}")
    report.append(f"AC130 sha256 unchanged = {AC130_FROZEN}")

    OUT_REPORT.write_text("\n".join(report) + "\n", encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
        z.write(ART_BIG, "_SPEC_ART_ONE.big")

    dsha, asha = sha256(DATA_BIG), sha256(ART_BIG)
    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={dsha}\n_SPEC_ART_ONE.big sha256={asha}\n"
        f"ART count={len(added)}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{OUT_ZIP}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print("DATA", dsha)
    print("ART", asha)
    print("URL", url)
    print("\n".join(report))


if __name__ == "__main__":
    main()
