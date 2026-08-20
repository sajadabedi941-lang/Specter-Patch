#!/usr/bin/env python3
"""Russia Air Force expansion on uploaded art_data baseline (#370 DATA SHA).

Source of truth: patch/Release/SPECTER_MASTER/{_SPEC_DATA_ONE,_SPEC_ART_ONE}.big
extracted from art_data.part01-22.rar

Phase 1: merge donor ART visual families from patch/Art
Phase 2: Russia gameplay only (reuse USA weapon/SP/OCL chains; never modify USA Objects)

Output: full replacement BIGs in one ZIP.
"""
from __future__ import annotations

import hashlib
import re
import shutil
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
MASTER = PATCH / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
OUT = PATCH / "Release/SPECTER_MASTER_RUSSIA_AIRFORCE_EXPANSION"
VERIFY = MASTER / "_extract_russia_airforce_verify"
REPORT = PATCH / "Release/DATA_RUSSIA_AIRFORCE_EXPANSION_REPORT.txt"
HASHES = PATCH / "Release/DATA_RUSSIA_AIRFORCE_EXPANSION_HASHES.txt"
DOWNLOAD = PATCH / "Release/DATA_RUSSIA_AIRFORCE_EXPANSION_DOWNLOAD.txt"

EXPECTED_DATA_SHA = "c7062a4ab12677a2e797d1a98324b14fcefd0a0cbdbbcec0a2e527553e377c05"
AF = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce"
CS_KEY = r"Data\INI\CommandSet.ini"
CB_KEY = r"Data\INI\CommandButton.ini"

CHINOOK_SLOTS = 8
ART_REL = [
    "Art/W3D/LSFRussiaTu160.W3D",
    "Art/W3D/LSFRussiaTu160d.W3D",
    "Art/W3D/LSFRussiaTu160k.W3D",
    "Art/Textures/LSFRussiaTU160.dds",
    "Art/Textures/LSFRussiaTU160d.dds",
    "Art/Textures/LSFRussiaTU160k.dds",
    "Art/Textures/TU-160.tga",
    "Art/Textures/TU160TB.tga",
    "Art/W3D/CWCruTu95.W3D",
    "Art/W3D/CWCruTu95_d.W3D",
    "Art/W3D/CWCruTu95_k.W3D",
    "Art/Textures/CWCruTu95.dds",
    "Art/Textures/CWCruTu95_d.dds",
    "Art/Textures/CWCruTu95_k.dds",
    "Art/Textures/CWCruTU95.dds",
    "Art/Textures/CWCruTU95_d.dds",
    "Art/Textures/CWCruTU95_k.dds",
    "Art/Textures/CWCgenPropellor.dds",
    "Art/Textures/CWCgenPropellor.tga",
    "Art/Textures/CWCgenReflective.dds",
    "Art/Textures/CWCgenReflective.tga",
    "Art/Textures/Tu95.tga",
    "Art/Textures/Tu95TB.tga",
    "Art/W3D/CWCruAn124.W3D",
    "Art/W3D/CWCruAn124_b.W3D",
    "Art/Textures/CWCruAn124.dds",
    "Art/Textures/CWCruAn124Nav.dds",
    "Art/Textures/CWCruAn124NavL.dds",
    "Art/Textures/CWCruAn124NavR.dds",
    "Art/Textures/AN124.tga",
    "Art/Textures/AN124TB.tga",
    "Art/W3D/A_AN225_100.W3D",
    "Art/W3D/A_E-3_100.W3D",
    "Art/Textures/A_AN225_100.tga",
    "Art/Textures/A_E-3_100.tga",
    "Art/Textures/RussiaAN225.tga",
    "Art/Textures/RussiaAN225TB.tga",
    "Art/W3D/CWCruA50.W3D",
    "Art/Textures/CWCruA50.dds",
    "Art/Textures/CWCruA50.tga",
    "Art/Textures/RussiaA50.tga",
    "Art/Textures/RussiaA50TB.tga",
    "Art/W3D/Yier76.W3D",
    "Art/Textures/yier76.tga",
    "Art/Textures/yier76TB.tga",
    "Art/Textures/yujing1.dds",
    "Art/Textures/yujing1.tga",
    "Art/W3D/LSFRussiaYR76.W3D",
    "Art/W3D/LSFRussiaYR76d.W3D",
    "Art/W3D/LSFRussiaYR76k.W3D",
    "Art/Textures/LSFRussiaYR76.tga",
    "Art/Textures/LSFRussiaYR76d.tga",
    "Art/Textures/LSFRussiaYR76k.tga",
    "Art/Textures/CargoIL76Russia.tga",
    "Art/Textures/CargoIL76RussiaTB.tga",
]

OBJ_SRC = {
    "RussiaJetTU160Clean": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetTU160Clean.ini",
    "RussiaJetTu95Visual": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetTu95Visual.ini",
    "RussiaJetAn124Visual": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetAn124Visual.ini",
    "RussiaJetAn225Visual": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetAn225Visual.ini",
    "RussiaJetA50Visual": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetA50Visual.ini",
    "RussiaJetAvionIL76Visual": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetAvionIL76Visual.ini",
    "RussiaJetCargoIL76Visual": PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetCargoIL76Visual.ini",
}


def sha256(p: Path | bytes) -> str:
    return hashlib.sha256(p if isinstance(p, bytes) else Path(p).read_bytes()).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF", path
    n = struct.unpack(">I", data[8:12])[0]
    pos = 16
    out: dict[str, bytes] = {}
    for _ in range(n):
        off, size = struct.unpack(">II", data[pos : pos + 8])
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1")
        pos = end + 1
        out[name.replace("/", "\\")] = data[off : off + size]
    return out


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


def dec(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def enc(t: str) -> bytes:
    return t.encode("utf-8")


def replace_or_append_commandset(text: str, name: str, block: str) -> str:
    pat = re.compile(rf"(?ms)^CommandSet\s+{re.escape(name)}\s*\n.*?(?=^CommandSet\s|\Z)")
    block = block.rstrip() + "\n\n"
    if pat.search(text):
        return pat.sub(block, text, count=1)
    return text.rstrip() + "\n\n" + block


def replace_or_append_commandbutton(text: str, name: str, block: str) -> str:
    pat = re.compile(rf"(?ms)^CommandButton\s+{re.escape(name)}\s*\n.*?(?=^CommandButton\s|\Z)")
    block = block.rstrip() + "\n\n"
    if pat.search(text):
        return pat.sub(block, text, count=1)
    return text.rstrip() + "\n\n" + block


def set_field(obj: str, field: str, value: str) -> str:
    pat = re.compile(rf"(?m)^(\s*){re.escape(field)}\s*=\s*.*$")
    if pat.search(obj):
        return pat.sub(rf"\1{field} = {value}", obj, count=1)
    # insert after Side or DisplayName
    m = re.search(r"(?m)^(\s*Side\s*=\s*.*)$", obj)
    if m:
        return obj[: m.end()] + f"\n  {field} = {value}" + obj[m.end() :]
    return obj


def ensure_kindof(obj: str, flags: list[str], remove: list[str] | None = None) -> str:
    remove = remove or []

    def repl(m: re.Match[str]) -> str:
        indent = m.group(1)
        parts = m.group(2).split()
        for r in remove:
            parts = [p for p in parts if p != r]
        for f in flags:
            if f not in parts:
                parts.append(f)
        return f"{indent}KindOf = {' '.join(parts)}"

    return re.sub(r"(?m)^(\s*)KindOf\s*=\s*(.+)$", repl, obj, count=1)


def upsert_weaponset_primary(obj: str, weapon: str) -> str:
    # Remove existing WeaponSet blocks then insert one PRIMARY
    obj = re.sub(r"(?ms)^\s*WeaponSet\s*\n.*?^\s*End\s*\n", "", obj)
    block = (
        f"  WeaponSet\n"
        f"    Conditions = None\n"
        f"    Weapon = PRIMARY {weapon}\n"
        f"  End\n"
    )
    m = re.search(r"(?m)^(\s*CommandSet\s*=\s*.*)$", obj)
    if m:
        return obj[: m.end()] + "\n" + block + obj[m.end() :]
    m = re.search(r"(?m)^(\s*KindOf\s*=\s*.*)$", obj)
    if m:
        return obj[: m.end()] + "\n" + block + obj[m.end() :]
    return obj + "\n" + block


def remove_weaponsets(obj: str) -> str:
    return re.sub(r"(?ms)^\s*WeaponSet\s*\n.*?^\s*End\s*\n", "", obj)


def upsert_transport(obj: str, slots: int) -> str:
    obj = re.sub(
        r"(?ms)^\s*Behavior\s*=\s*TransportContain\b.*?^\s*End\s*\n",
        "",
        obj,
    )
    block = (
        f"  Behavior = TransportContain ModuleTag_RussiaCargo\n"
        f"    Slots                 = {slots}\n"
        f"    DamagePercentToUnits  = 100%\n"
        f"    AllowInsideKindOf     = INFANTRY VEHICLE\n"
        f"    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE\n"
        f"    ExitDelay             = 100\n"
        f"    NumberOfExitPaths     = 1\n"
        f"  End\n"
    )
    m = re.search(r"(?m)^(\s*Geometry\s*=\s*.*)$", obj)
    if m:
        return obj[: m.start()] + block + "\n" + obj[m.start() :]
    return obj + "\n" + block


def upsert_ocl_special(obj: str, tag: str, sp: str, ocl: str) -> str:
    obj = re.sub(
        rf"(?ms)^\s*Behavior\s*=\s*OCLSpecialPower\s+{re.escape(tag)}\b.*?^\s*End\s*\n",
        "",
        obj,
    )
    block = (
        f"  Behavior = OCLSpecialPower {tag}\n"
        f"    SpecialPowerTemplate = {sp}\n"
        f"    OCL                  = {ocl}\n"
        f"    CreateLocation       = CREATE_AT_LOCATION\n"
        f"  End\n"
    )
    m = re.search(r"(?m)^(\s*Behavior\s*=\s*JetAIUpdate\b)", obj)
    if m:
        return obj[: m.start()] + block + obj[m.start() :]
    return obj + "\n" + block


def upsert_stealth(obj: str, tag: str, detection_range: int) -> str:
    obj = re.sub(
        rf"(?ms)^\s*Behavior\s*=\s*StealthDetectorUpdate\s+{re.escape(tag)}\b.*?^\s*End\s*\n",
        "",
        obj,
    )
    block = (
        f"  Behavior = StealthDetectorUpdate {tag}\n"
        f"    DetectionRate             = 1800\n"
        f"    DetectionRange            = {detection_range}\n"
        f"    CanDetectWhileGarrisoned  = No\n"
        f"    CanDetectWhileContained   = No\n"
        f"    ExtraForbiddenKindOf      = UNATTACKABLE\n"
        f"  End\n"
    )
    m = re.search(r"(?m)^(\s*Behavior\s*=\s*JetAIUpdate\b)", obj)
    if m:
        return obj[: m.start()] + block + obj[m.start() :]
    return obj + "\n" + block


def set_jetai_ammo_damage(obj: str, value: str) -> str:
    if re.search(r"(?m)^\s*OutOfAmmoDamagePerSecond\s*=", obj):
        return re.sub(
            r"(?m)^(\s*OutOfAmmoDamagePerSecond\s*=\s*).*$",
            rf"\g<1>{value}",
            obj,
        )
    return re.sub(
        r"(?ms)(Behavior\s*=\s*JetAIUpdate\b.*?)(^\s*End\s*$)",
        rf"\1    OutOfAmmoDamagePerSecond = {value}\n\2",
        obj,
        count=1,
    )


def apply_tu160(obj: str) -> str:
    obj = ensure_kindof(obj, ["CAN_ATTACK"])
    obj = set_field(obj, "CommandSet", "GenericTacticalBomberCommandSet")
    obj = upsert_weaponset_primary(obj, "AmericaB2A10TonBombWeapon")
    obj = set_jetai_ammo_damage(obj, "10%")
    return obj


def apply_tu95(obj: str) -> str:
    obj = ensure_kindof(obj, ["CAN_ATTACK"])
    obj = set_field(obj, "CommandSet", "RussiaJetTu95CommandSet")
    obj = upsert_weaponset_primary(obj, "AmericaB52FifteenBombLineWeapon")
    obj = set_jetai_ammo_damage(obj, "10%")
    return obj


def apply_a50(obj: str) -> str:
    obj = remove_weaponsets(obj)
    obj = ensure_kindof(obj, [], remove=["CAN_ATTACK"])
    obj = set_field(obj, "CommandSet", "RussiaJetA50VisualCommandSet")
    obj = set_field(obj, "VisionRange", "810")
    obj = set_field(obj, "ShroudClearingRange", "810")
    obj = upsert_ocl_special(
        obj,
        "ModuleTag_RussiaA50SAR",
        "AmericaE737TargetedSARScan",
        "OCL_AmericaE737TargetedSARScan",
    )
    obj = upsert_stealth(obj, "ModuleTag_RussiaA50Stealth", 2700)
    obj = set_jetai_ammo_damage(obj, "0%")
    return obj


def apply_an225(obj: str) -> str:
    obj = remove_weaponsets(obj)
    obj = ensure_kindof(obj, [], remove=["CAN_ATTACK"])
    obj = set_field(obj, "CommandSet", "RussiaJetAn225VisualCommandSet")
    obj = set_field(obj, "VisionRange", "1200")
    obj = set_field(obj, "ShroudClearingRange", "1200")
    obj = upsert_ocl_special(
        obj,
        "ModuleTag_RussiaAn225SAR",
        "AmericaE3TargetedSARScan",
        "OCL_AmericaE3TargetedSARScan",
    )
    obj = upsert_stealth(obj, "ModuleTag_RussiaAn225Stealth", 4000)
    obj = set_jetai_ammo_damage(obj, "0%")
    return obj


def apply_transport(obj: str, slots: int) -> str:
    obj = remove_weaponsets(obj)
    obj = ensure_kindof(obj, ["TRANSPORT"], remove=["CAN_ATTACK"])
    obj = set_field(obj, "CommandSet", "C17GlobalMasterCommandSet")
    obj = upsert_transport(obj, slots)
    obj = set_jetai_ammo_damage(obj, "0%")
    return obj


HEAVY_CS = """CommandSet Russia_HeavyAirBaseCommandSet
  1  = Command_ConstructRussiaJetTU160
  2  = Command_ConstructRussiaJetTu95Visual
  3  = Command_ConstructRussiaJetAn124Visual
  4  = Command_ConstructRussiaJetAn225Visual
  5  = Command_ConstructRussiaJetA50Visual
  6  = Command_ConstructRussiaJetAvionIL76Visual
  7  = Command_ConstructRussiaJetCargoIL76Visual
  8  = Command_ConstructRussiaJetTu22M3M
  9  = Command_ConstructRussiaJetSu47Recon
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

LARGE_CS = """CommandSet Russia_LargeAirBaseCommandSet
  1  = Command_ConstructRussiaJetSu75Checkmate
  2  = Command_ConstructRussiaJetSu35S
  3  = Command_ConstructRussiaJetSu30SM2
  4  = Command_ConstructRussiaJetSU25T
  5  = Command_ConstructRussiaJetSu35AG
  6  = Command_ConstructRussiaJetMig31K
  7  = Command_ConstructRussiaHelicopterMi28N
  8  = Command_ConstructRussiaHelicopterKA52
  9  = Command_ConstructRussiaJetSu57AA
  10 = Command_ConstructRussiaJetSu34
  11 = Command_ConstructRussiaJetSU24M2
  12 = Command_ConstructRussiaJetSU24MP
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

EXTRA_CS = {
    "RussiaJetTu95CommandSet": """CommandSet RussiaJetTu95CommandSet
  1  = Command_AmericaB52CarpetStrike
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""",
    "RussiaJetA50VisualCommandSet": """CommandSet RussiaJetA50VisualCommandSet
  1  = Command_E737SARScan
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""",
    "RussiaJetAn225VisualCommandSet": """CommandSet RussiaJetAn225VisualCommandSet
  1  = Command_E3SARScan
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End
""",
}

BUTTONS = {
    "Command_ConstructRussiaJetTU160": """CommandButton Command_ConstructRussiaJetTU160
  Command       = UNIT_BUILD
  Object        = RussiaJetTU160Clean
  TextLabel     = CONTROLBAR:ConstructRussiaJetTU160
  ButtonImage   = TU-160
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTU160
End
""",
    "Command_ConstructRussiaJetTu95Visual": """CommandButton Command_ConstructRussiaJetTu95Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetTu95Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetTu95Visual
  ButtonImage   = Tu95
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTu95Visual
End
""",
    "Command_ConstructRussiaJetAn124Visual": """CommandButton Command_ConstructRussiaJetAn124Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetAn124Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetAn124Visual
  ButtonImage   = AN124
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAn124Visual
End
""",
    "Command_ConstructRussiaJetAn225Visual": """CommandButton Command_ConstructRussiaJetAn225Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetAn225Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetAn225Visual
  ButtonImage   = RussiaAN225
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAn225Visual
End
""",
    "Command_ConstructRussiaJetA50Visual": """CommandButton Command_ConstructRussiaJetA50Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetA50Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetA50Visual
  ButtonImage   = RussiaA50
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetA50Visual
End
""",
    "Command_ConstructRussiaJetAvionIL76Visual": """CommandButton Command_ConstructRussiaJetAvionIL76Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetAvionIL76Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetAvionIL76Visual
  ButtonImage   = yier76
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetAvionIL76Visual
End
""",
    "Command_ConstructRussiaJetCargoIL76Visual": """CommandButton Command_ConstructRussiaJetCargoIL76Visual
  Command       = UNIT_BUILD
  Object        = RussiaJetCargoIL76Visual
  TextLabel     = CONTROLBAR:ConstructRussiaJetCargoIL76Visual
  ButtonImage   = CargoIL76Russia
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetCargoIL76Visual
End
""",
}

# Ensure Su-24/Su-34 buttons keep real aircraft icons
BUTTON_ICON_FIXES = {
    "Command_ConstructRussiaJetSu34": "rus_su34",
    "Command_ConstructRussiaJetSU24M2": "rus_su24m2",
    "Command_ConstructRussiaJetSU24MP": "rus_su24mp",
}


def extract_object(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^Object\s+{re.escape(name)}\s*\n.*?(?=^Object\s|\Z)", text)
    assert m, name
    return m.group(0)


def usa_frozen_hashes(data_map: dict[str, bytes]) -> dict[str, str]:
    keys = []
    for k in data_map:
        lk = k.lower()
        if any(
            x in lk
            for x in [
                "americajetb2a.ini",
                "usa_system.ini",
                "americajete737visual.ini",
                "americajete3visual.ini",
                "ch47f.ini",
                "americajetc17visual.ini",
            ]
        ):
            # only USA paths
            if "united states of america" in lk or k.lower().endswith("usa_system.ini"):
                keys.append(k)
            elif k.lower().endswith("ch47f.ini") and "united states of america" in lk:
                keys.append(k)
    # force exact known keys
    forced = [
        r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini",
        r"Data\INI\Object\Specter\United States Of America\USA_System.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetE737Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\AmericaJetE3Visual.ini",
        r"Data\INI\Object\Specter\United States Of America\Airforce\CH47F.ini",
        r"Data\INI\Weapon.ini",
        r"Data\INI\ObjectCreationList.ini",
        r"Data\INI\SpecialPower.ini",
    ]
    out = {}
    for k in forced:
        if k in data_map:
            out[k] = sha256(data_map[k])
    return out


def main() -> None:
    assert DATA_BIG.is_file() and ART_BIG.is_file()
    base_data_sha = sha256(DATA_BIG)
    base_art_sha = sha256(ART_BIG)
    assert (
        base_data_sha == EXPECTED_DATA_SHA
    ), f"Baseline DATA SHA mismatch: {base_data_sha}"

    data_map = read_big(DATA_BIG)
    art_map = read_big(ART_BIG)
    usa_before = usa_frozen_hashes(data_map)

    # Snapshot B52 object text for later content check
    usa_sys = dec(data_map[r"Data\INI\Object\Specter\United States Of America\USA_System.ini"])
    b52_before = extract_object(usa_sys, "AmericaJetB52H")
    b2a_before = dec(
        data_map[r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"]
    )

    # --- Phase 1 ART ---
    imported_art = []
    for rel in ART_REL:
        src = PATCH / rel
        assert src.is_file(), src
        key = rel.replace("/", "\\")
        art_map[key] = src.read_bytes()
        imported_art.append(key)

    # MappedImages / strings helpers if present
    extra_data_files = [
        (
            r"Data\INI\MappedImages\HandCreated\Russia_DonorAircraftIcons.INI",
            PATCH / "Data/INI/MappedImages/HandCreated/Russia_DonorAircraftIcons.INI",
        ),
        (
            r"Data\INI\MappedImages\HandCreated\TEOD_TU160_Images.INI",
            PATCH / "Data/INI/MappedImages/HandCreated/TEOD_TU160_Images.INI",
        ),
        (
            r"Data\English\SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt",
            PATCH / "Data/English/SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt",
        ),
    ]
    for key, src in extra_data_files:
        if src.is_file():
            data_map[key] = src.read_bytes()

    # --- Phase 2 DATA objects ---
    transformers = {
        "RussiaJetTU160Clean": apply_tu160,
        "RussiaJetTu95Visual": apply_tu95,
        "RussiaJetA50Visual": apply_a50,
        "RussiaJetAn225Visual": apply_an225,
        "RussiaJetAn124Visual": lambda o: apply_transport(o, CHINOOK_SLOTS * 8),
        "RussiaJetAvionIL76Visual": lambda o: apply_transport(o, CHINOOK_SLOTS * 4),
        "RussiaJetCargoIL76Visual": lambda o: apply_transport(o, CHINOOK_SLOTS * 6),
    }
    for obj_name, src in OBJ_SRC.items():
        text = src.read_text(encoding="utf-8", errors="replace")
        # ensure single object body
        if f"Object {obj_name}" not in text:
            raise SystemExit(f"Missing Object {obj_name} in {src}")
        # apply transform on full file (single-object files)
        text = transformers[obj_name](text)
        key = rf"{AF}\{obj_name}.ini"
        # normalize filename for Tu160
        if obj_name == "RussiaJetTU160Clean":
            key = rf"{AF}\RussiaJetTU160Clean.ini"
        data_map[key] = enc(text)
        # also write back to patch for audit
        src.write_text(text, encoding="utf-8")

    # CommandSet.ini — Russia only (+ new aircraft CS)
    cs = dec(data_map[CS_KEY])
    cs = replace_or_append_commandset(cs, "Russia_HeavyAirBaseCommandSet", HEAVY_CS)
    cs = replace_or_append_commandset(cs, "Russia_LargeAirBaseCommandSet", LARGE_CS)
    for name, block in EXTRA_CS.items():
        cs = replace_or_append_commandset(cs, name, block)
    data_map[CS_KEY] = enc(cs)

    # CommandButton.ini — add construct buttons; fix Su-24/34 icons if present
    cb = dec(data_map[CB_KEY])
    for name, block in BUTTONS.items():
        cb = replace_or_append_commandbutton(cb, name, block)
    for btn, icon in BUTTON_ICON_FIXES.items():
        pat = re.compile(
            rf"(?ms)^(CommandButton\s+{re.escape(btn)}\s*\n.*?)(^\s*ButtonImage\s*=\s*).*$",
            re.M,
        )
        if pat.search(cb):
            cb = pat.sub(rf"\1\2{icon}", cb, count=1)
    data_map[CB_KEY] = enc(cb)

    # USA freeze check before build
    usa_after_edit = usa_frozen_hashes(data_map)
    for k, h in usa_before.items():
        assert usa_after_edit.get(k) == h, f"USA file changed unexpectedly: {k}"
    usa_sys2 = dec(data_map[r"Data\INI\Object\Specter\United States Of America\USA_System.ini"])
    assert extract_object(usa_sys2, "AmericaJetB52H") == b52_before
    assert (
        dec(data_map[r"Data\INI\Object\Specter\United States Of America\AmericaJetB2A.ini"])
        == b2a_before
    )

    # Build BIGs
    OUT.mkdir(parents=True, exist_ok=True)
    new_data = build_big(data_map)
    new_art = build_big(art_map)
    out_data = OUT / "_SPEC_DATA_ONE.big"
    out_art = OUT / "_SPEC_ART_ONE.big"
    out_data.write_bytes(new_data)
    out_art.write_bytes(new_art)

    # Re-extract verify
    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vdata = read_big(out_data)
    vart = read_big(out_art)

    checks = []

    def ok(msg: str, cond: bool) -> None:
        checks.append((msg, cond))
        print(("PASS" if cond else "FAIL"), msg)

    # USA unchanged content hashes against original baseline map values
    for k, h in usa_before.items():
        ok(f"USA frozen {k}", sha256(vdata[k]) == h)

    # Russia objects
    for obj_name in transformers:
        key = rf"{AF}\{obj_name}.ini"
        ok(f"object present {obj_name}", key in vdata)
        txt = dec(vdata[key])
        if obj_name == "RussiaJetTU160Clean":
            ok("Tu-160 B2A weapon", "AmericaB2A10TonBombWeapon" in txt)
            ok("Tu-160 CAN_ATTACK", "CAN_ATTACK" in txt)
        if obj_name == "RussiaJetTu95Visual":
            ok("Tu-95 B52 weapon", "AmericaB52FifteenBombLineWeapon" in txt)
            ok("Tu-95 CS", "RussiaJetTu95CommandSet" in txt)
        if obj_name == "RussiaJetA50Visual":
            ok("A-50 E737 SP", "AmericaE737TargetedSARScan" in txt)
            ok("A-50 E737 OCL", "OCL_AmericaE737TargetedSARScan" in txt)
            ok("A-50 no weaponset", "WeaponSet" not in txt)
            ok("A-50 vision 810", re.search(r"VisionRange\s*=\s*810", txt) is not None)
        if obj_name == "RussiaJetAn225Visual":
            ok("An-225 E3 SP", "AmericaE3TargetedSARScan" in txt)
            ok("An-225 E3 OCL", "OCL_AmericaE3TargetedSARScan" in txt)
            ok("An-225 vision 1200", re.search(r"VisionRange\s*=\s*1200", txt) is not None)
        if obj_name == "RussiaJetAn124Visual":
            ok("An-124 slots 64", re.search(r"Slots\s*=\s*64\b", txt) is not None)
            ok("An-124 TRANSPORT", "TRANSPORT" in txt)
            ok("An-124 no WeaponSet", "WeaponSet" not in txt)
        if obj_name == "RussiaJetAvionIL76Visual":
            ok("avion slots 32", re.search(r"Slots\s*=\s*32\b", txt) is not None)
        if obj_name == "RussiaJetCargoIL76Visual":
            ok("cargo slots 48", re.search(r"Slots\s*=\s*48\b", txt) is not None)

    cs_v = dec(vdata[CS_KEY])
    ok(
        "Heavy CS Tu-160",
        "Command_ConstructRussiaJetTU160" in extract_cs(cs_v, "Russia_HeavyAirBaseCommandSet"),
    )
    heavy = extract_cs(cs_v, "Russia_HeavyAirBaseCommandSet")
    large = extract_cs(cs_v, "Russia_LargeAirBaseCommandSet")
    ok("Su34 moved to Large", "Command_ConstructRussiaJetSu34" in large)
    ok("SU24M2 moved to Large", "Command_ConstructRussiaJetSU24M2" in large)
    ok("SU24MP moved to Large", "Command_ConstructRussiaJetSU24MP" in large)
    ok("Su34 not on Heavy", "Command_ConstructRussiaJetSu34" not in heavy)
    ok("SU24M2 not on Heavy", "Command_ConstructRussiaJetSU24M2" not in heavy)
    ok("SU24MP not on Heavy", "Command_ConstructRussiaJetSU24MP" not in heavy)

    # ART assets present
    for key in imported_art:
        ok(f"ART {key}", key in vart)

    failed = [m for m, c in checks if not c]
    assert not failed, f"Verification failed: {failed}"

    data_sha = sha256(new_data)
    art_sha = sha256(new_art)
    zip_path = OUT / "SPECTER_MASTER_RUSSIA_AIRFORCE_EXPANSION.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(out_data, "_SPEC_DATA_ONE.big")
        zf.write(out_art, "_SPEC_ART_ONE.big")
    zip_sha = sha256(zip_path)

    # Also place master copies for convenience
    (MASTER / "_SPEC_DATA_ONE.big").write_bytes(new_data)
    (MASTER / "_SPEC_ART_ONE.big").write_bytes(new_art)

    report = f"""RUSSIA AIR FORCE EXPANSION = PACKED FULL BUILD READY FOR USER TEST

1. BASELINE
- Source: uploaded art_data.part01-22.rar
- Recovered DATA SHA256 (pre-change) = {base_data_sha}
- Recovered ART  SHA256 (pre-change) = {base_art_sha}
- Matches historical #370 DATA SHA = YES

2. USA UNCHANGED = YES
- AmericaJetB2A unchanged
- AmericaJetB52H (FifteenBombLine) unchanged
- AmericaJetE737Visual unchanged
- AmericaJetE3Visual unchanged
- CH47F Chinook unchanged
- Weapon.ini / ObjectCreationList.ini / SpecialPower.ini hashes unchanged

3. DONOR ART IMPORTED
{chr(10).join('- ' + k for k in imported_art)}

4. RUSSIA DATA CHANGES
- Tu-160: AmericaB2A10TonBombWeapon (B-2A fire chain reuse)
- Tu-95: AmericaB52FifteenBombLineWeapon + RussiaJetTu95CommandSet (B-52 carpet button reuse)
- A-50: AmericaE737TargetedSARScan + OCL_AmericaE737TargetedSARScan + Vision/Shroud 810 + Stealth 2700
- An-225: AmericaE3TargetedSARScan + OCL_AmericaE3TargetedSARScan + Vision/Shroud 1200 + Stealth 4000
- An-124: TransportContain Slots=64 (8x Chinook), no WeaponSet
- avionIL76: TransportContain Slots=32 (4x Chinook)
- cargoIL76: TransportContain Slots=48 (6x Chinook)
- Su-34 / SU24M2 / SU24MP moved Heavy -> Large (Fighter) AirBase
- Russia_HeavyAirBaseCommandSet rebuilt for 7 heavy aircraft + Tu22/Su47 retained

5. MODIFIED FILES (runtime keys)
- Data\\INI\\CommandSet.ini (Russia CS + new aircraft CS only)
- Data\\INI\\CommandButton.ini (Russia construct buttons)
- Data\\INI\\Object\\...\\Airforce\\RussiaJet*.ini (7 aircraft)
- Art\\W3D\\* / Art\\Textures\\* (donor visual families)
- MappedImages / SPECTER_RUSSIA_AIRCRAFT_EXPANSION_Strings.txt helpers

6. FINAL HASHES
_SPEC_DATA_ONE.big SHA256 = {data_sha}
_SPEC_DATA_ONE.big SIZE   = {len(new_data)}
_SPEC_ART_ONE.big  SHA256 = {art_sha}
_SPEC_ART_ONE.big  SIZE   = {len(new_art)}
ZIP SHA256 = {zip_sha}
ZIP PATH   = {zip_path}

7. CONFIRM
Built from uploaded art_data complete runtime (#370 DATA identity).
USA preserved. Other factions' Objects not edited.
Re-extract verification: ALL CHECKS PASS.

Do not claim in-game success. User performs final runtime test.
"""
    REPORT.write_text(report, encoding="utf-8")
    HASHES.write_text(
        f"BASELINE_DATA={base_data_sha}\n"
        f"BASELINE_ART={base_art_sha}\n"
        f"_SPEC_DATA_ONE.big={data_sha}\n"
        f"_SPEC_ART_ONE.big={art_sha}\n"
        f"ZIP={zip_sha}\n",
        encoding="utf-8",
    )
    DOWNLOAD.write_text(str(zip_path) + "\n", encoding="utf-8")
    print(report)


def extract_cs(text: str, name: str) -> str:
    m = re.search(rf"(?ms)^CommandSet\s+{re.escape(name)}\s*\n.*?(?=^CommandSet\s|\Z)", text)
    return m.group(0) if m else ""


if __name__ == "__main__":
    main()
