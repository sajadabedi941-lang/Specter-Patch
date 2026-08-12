#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_SUT50_PAKFA from SU47-AG pack baseline.

Clean donor method (B-21 / F-117 / SU-75 / SU-47 / TU-160):
  - Pack TEOD PAK-FA W3D + PAKFA textures + PAKFA-ic_L icon atlas
  - Add RussiaJetT50PAKFAClean (fixed-wing JetAI, donor stealth, NeedsRunway)
  - Unique weapon/locomotor; ProjectileObject = Russia_T50_R27_Projectile
    (complete unique TEOD R27 clone — does NOT redefine Object R27)
  - Replace RussiaAirfieldCommandSet slot 11 (former KA-52) only
  - Preserve SU-75 / SU-47 / TU-160 / Su35AG; no CommandSet mass merge
"""

from __future__ import annotations

import hashlib
import re
import shutil
import struct
import tempfile
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SU47_AG_ONLY"
TEOD_INI = Path("/tmp/teod_bigs/!TEOD_INI.big")
OUT = PATCH / "Release" / "SPECTER_RUSSIA_SUT50_PAKFA"

OBJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "RussiaJetT50PAKFAClean.ini"
)
WEAPON_INI = PATCH / "Data/INI/Weapon_Russia_T50_PAKFA_Clean.ini"
LOCO_INI = PATCH / "Data/INI/Locomotor_Russia_T50_PAKFA_Clean.ini"
PROJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "Russia_T50_R27_Projectile.ini"
)
SUPPORT_WEAPON_INI = PATCH / "Data/INI/Weapon_Russia_T50_R27_Support.ini"
OCL_INI = PATCH / "Data/INI/ObjectCreationList_Russia_T50_R27.ini"
MAPPED_INI = PATCH / "Data/INI/MappedImages/HandCreated/TEOD_T50_PAKFA_Images.INI"
STRINGS_TXT = PATCH / "Data/English/SPECTER_T50_PAKFA_Strings.txt"

ART_ASSETS = {
    r"Art\W3D\PAK-FA.W3D": PATCH / "Art/W3D/PAK-FA.W3D",
    r"Art\W3D\PAK-FA_D.W3D": PATCH / "Art/W3D/PAK-FA_D.W3D",
    r"Art\W3D\PAK-FA_E.W3D": PATCH / "Art/W3D/PAK-FA_E.W3D",
    r"Art\W3D\PAK-FA_E1.W3D": PATCH / "Art/W3D/PAK-FA_E1.W3D",
    r"Art\W3D\PAK-FA_E2.W3D": PATCH / "Art/W3D/PAK-FA_E2.W3D",
    r"Art\W3D\R-27.W3D": PATCH / "Art/W3D/R-27.W3D",
    r"Art\Textures\PAKFA.dds": PATCH / "Art/Textures/PAKFA.dds",
    r"Art\Textures\PAKFA_D.dds": PATCH / "Art/Textures/PAKFA_D.dds",
    r"Art\Textures\PAKFA_E.dds": PATCH / "Art/Textures/PAKFA_E.dds",
    r"Art\Textures\RU-Icons03.tga": PATCH / "Art/Textures/RU-Icons03.tga",
}

OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetT50PAKFAClean.ini"
)
WEAPON_KEY = r"Data\INI\Weapon_Russia_T50_PAKFA_Clean.ini"
LOCO_KEY = r"Data\INI\Locomotor_Russia_T50_PAKFA_Clean.ini"
PROJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_T50_R27_Projectile.ini"
)
SUPPORT_WEAPON_KEY = r"Data\INI\Weapon_Russia_T50_R27_Support.ini"
OCL_KEY = r"Data\INI\ObjectCreationList_Russia_T50_R27.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\TEOD_T50_PAKFA_Images.INI"
STRINGS_KEY = r"Data\English\SPECTER_T50_PAKFA_Strings.txt"
BUTTON_KEY = r"Data\INI\CommandButton.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"
CSF_KEY = r"Data\English\generals.csf"

RUNTIME_AIRFIELD = "RussiaAirfield"
RUNTIME_COMMANDSET = "RussiaAirfieldCommandSet"
OLD_KA52_SLOT = 11
OLD_KA52_BUTTON = "Command_ConstructRussiaHelicopterKA52"
OLD_KA52_OBJECT = "RussiaHelicopterKA52"
T50_BUTTON = "Command_ConstructRussiaJetT50PAKFA"
T50_OBJECT = "RussiaJetT50PAKFAClean"
T50_WEAPON = "Russia_Weapon_T50_PAKFA"
T50_LOCO = "Russia_Locomotor_T50_PAKFA"
OLD_PROJECTILE = "R27"
NEW_PROJECTILE = "Russia_T50_R27_Projectile"
DONOR_OBJECT = "Russia_VehiclePAKFA"

T50_BUTTON_BLOCK = """CommandButton Command_ConstructRussiaJetT50PAKFA
  Command       = UNIT_BUILD
  Object        = RussiaJetT50PAKFAClean
  TextLabel     = CONTROLBAR:ConstructRussiaJetT50PAKFA
  ButtonImage   = PAKFA-ic_L
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetT50PAKFA
End
"""

CSF_LABELS = [
    ("OBJECT:RussiaJetT50PAKFA", "SU-T50 PAK FA"),
    ("CONTROLBAR:ConstructRussiaJetT50PAKFA", "SU-T50 PAK FA"),
    (
        "CONTROLBAR:ToolTipRussiaJetT50PAKFA",
        "Russian fifth-generation stealth multirole fighter.",
    ),
]

# Must never pack these TEOD originals (duplicate crash risk)
FORBIDDEN_PACK_SUBSTRINGS = [
    "pakfamissileweapon",  # TEOD original weapon name file keys
    r"object r27",
]


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    _, n, _ = struct.unpack_from(">III", data, 4)
    entries: dict[str, bytes] = {}
    off = 16
    for _ in range(n):
        eoff, esize = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1", errors="replace")
        off = end + 1
        entries[name] = data[eoff : eoff + esize]
    return entries


def write_big(path: Path, file_map: dict[str, bytes]) -> None:
    items = sorted(file_map.items(), key=lambda kv: kv[0].lower())
    header_size = 16
    for name, _ in items:
        header_size += 8 + len(name.encode("latin1", errors="replace")) + 1
    index = []
    blobs = []
    offset = header_size
    for name, content in items:
        content = bytes(content)
        index.append((name, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(items))
    out += struct.pack(">I", header_size)
    for name, off, size in index:
        out += struct.pack(">II", off, size)
        out += name.encode("latin1", errors="replace") + b"\x00"
    for blob in blobs:
        out += blob
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(bytes(out))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def encode_inv_utf16(s: str) -> bytes:
    return bytes(b ^ 0xFF for b in s.encode("utf-16-le"))


def make_csf_label(key: str, value: str) -> bytes:
    kb = key.encode("ascii")
    out = bytearray()
    out += b" LBL"
    out += struct.pack("<I", 1)
    out += struct.pack("<I", len(kb))
    out += kb
    out += b" RTS"
    out += struct.pack("<I", len(value))
    out += encode_inv_utf16(value)
    return bytes(out)


def patch_csf(blob: bytes, labels: list[tuple[str, str]]) -> bytes:
    data = bytearray(blob)
    if data[:4] != b" FSC":
        raise ValueError("Unexpected CSF magic")
    num_labels = struct.unpack_from("<I", data, 8)[0]
    num_strings = struct.unpack_from("<I", data, 12)[0]
    add = 0
    for key, value in labels:
        if key.encode("ascii") in data:
            continue
        data += make_csf_label(key, value)
        add += 1
    if add:
        struct.pack_into("<I", data, 8, num_labels + add)
        struct.pack_into("<I", data, 12, num_strings + add)
    return bytes(data)


def commandset_slots(blob: bytes, name: str) -> list[tuple[int, str]]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandSet\s+{re.escape(name)}\b(.*?)(^End\s*$)",
        text,
        re.M | re.S,
    )
    if not m:
        raise RuntimeError(f"Missing CommandSet {name}")
    return [
        (int(a), b)
        for a, b in re.findall(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)
    ]


def cs_map(blob: bytes) -> dict[str, str]:
    text = blob.decode("latin1", errors="replace")
    out: dict[str, str] = {}
    for m in re.finditer(
        r"^CommandSet\s+(\S+)\b(.*?)(?=^CommandSet\s|\Z)", text, re.M | re.S
    ):
        out[m.group(1)] = m.group(2)
    return out


def ensure_t50_command_button(blob: bytes) -> bytes:
    text = blob.decode("latin1", errors="replace")
    pattern = re.compile(
        rf"(^CommandButton\s+{re.escape(T50_BUTTON)}\b.*?)(?=^CommandButton\s|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if m:
        block = T50_BUTTON_BLOCK
        return (text[: m.start(1)] + block + text[m.end(1) :]).encode(
            "latin1", errors="replace"
        )
    # Insert near SU47/TU160 buttons if present, else append before last End-ish
    anchor = re.search(
        r"(^CommandButton\s+Command_ConstructRussiaJetTU160\b.*?^End\s*\n)",
        text,
        re.M | re.S,
    )
    if anchor:
        insert_at = anchor.end(1)
        return (text[:insert_at] + "\n" + T50_BUTTON_BLOCK + text[insert_at:]).encode(
            "latin1", errors="replace"
        )
    return (text.rstrip() + "\n\n" + T50_BUTTON_BLOCK).encode(
        "latin1", errors="replace"
    )


def patch_russia_airfield_commandset(blob: bytes) -> bytes:
    """Replace KA-52 slot 11 with SU-T50; keep all other slots."""
    text = blob.decode("latin1", errors="replace")
    pattern = re.compile(
        rf"(^CommandSet\s+{re.escape(RUNTIME_COMMANDSET)}\b)(.*?)(^End\s*$)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError(f"Missing {RUNTIME_COMMANDSET}")
    body = m.group(2)
    for must in [
        "Command_ConstructRussiaJetSu75Checkmate",
        "Command_ConstructRussiaJetSu47Recon",
        "Command_ConstructRussiaJetTU160",
        "Command_ConstructRussiaJetSu35AG",
    ]:
        if must not in body:
            raise RuntimeError(f"{RUNTIME_COMMANDSET} missing {must}")
    slot11 = re.search(r"^\s*11\s*=\s*(\S+)", body, re.M)
    if not slot11:
        raise RuntimeError(f"{RUNTIME_COMMANDSET} missing slot 11")
    if slot11.group(1) not in (OLD_KA52_BUTTON, T50_BUTTON):
        raise RuntimeError(
            f"Slot 11 unexpected {slot11.group(1)} "
            f"(want {OLD_KA52_BUTTON} or {T50_BUTTON})"
        )
    body = re.sub(
        r"(^\s*11\s*=\s*)\S+",
        rf"\g<1>{T50_BUTTON}",
        body,
        count=1,
        flags=re.M,
    )
    # Ensure T50 appears exactly once
    tu_count = len(re.findall(rf"=\s*{re.escape(T50_BUTTON)}\b", body))
    if tu_count != 1:
        raise RuntimeError(f"T50 button count = {tu_count}, want 1")
    if OLD_KA52_BUTTON in body:
        raise RuntimeError("KA-52 button still present on runtime CommandSet")
    return (
        text[: m.start(2)] + body + text[m.end(2) :]
    ).encode("latin1", errors="replace")


def extract_block(text: str, kind: str, name: str) -> str | None:
    m = re.search(
        rf"^{kind}\s+{re.escape(name)}\b(.*?)(?=^{kind}\s|\Z)",
        text,
        re.M | re.S,
    )
    return m.group(0) if m else None


def field(block: str, key: str) -> str:
    m = re.search(rf"^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", block, re.M)
    return m.group(1).strip() if m else "MISSING"


def count_defs(blob: bytes, kind: str, name: str) -> int:
    text = blob.decode("latin1", errors="replace")
    return len(re.findall(rf"^{kind}\s+{re.escape(name)}\b", text, re.M))


def validate(art: dict[str, bytes], data: dict[str, bytes], teod: dict[str, bytes]) -> list[str]:
    lines: list[str] = []
    obj_blob = data[OBJ_KEY].decode("latin1", errors="replace")
    wep_blob = data[WEAPON_KEY].decode("latin1", errors="replace")
    loco_blob = data[LOCO_KEY].decode("latin1", errors="replace")
    proj_blob = data[PROJ_KEY].decode("latin1", errors="replace")
    support_blob = data[SUPPORT_WEAPON_KEY].decode("latin1", errors="replace")
    ocl_blob = data[OCL_KEY].decode("latin1", errors="replace")
    btn_blob = data[BUTTON_KEY].decode("latin1", errors="replace")

    obj = extract_block(obj_blob, "Object", T50_OBJECT)
    wep = extract_block(wep_blob, "Weapon", T50_WEAPON)
    loco = extract_block(loco_blob, "Locomotor", T50_LOCO)
    proj_obj = extract_block(proj_blob, "Object", NEW_PROJECTILE)
    btn = extract_block(btn_blob, "CommandButton", T50_BUTTON)
    if not obj or not wep or not loco or not btn or not proj_obj:
        raise RuntimeError("Missing packed T50 object/weapon/loco/button/projectile")
    if not extract_block(support_blob, "Weapon", "Russia_T50_JetMissileControl"):
        raise RuntimeError("Missing Russia_T50_JetMissileControl")
    if not extract_block(ocl_blob, "ObjectCreationList", "Russia_T50_OCL_JetMissileControl"):
        raise RuntimeError("Missing Russia_T50_OCL_JetMissileControl")

    # Patch must NOT redefine Object R27; TEOD may still define it once externally
    teod_r27 = sum(count_defs(v, "Object", OLD_PROJECTILE) for v in teod.values())
    pack_r27 = sum(count_defs(v, "Object", OLD_PROJECTILE) for v in data.values())
    pack_t50_proj = sum(count_defs(v, "Object", NEW_PROJECTILE) for v in data.values())
    pack_teod_wep = sum(count_defs(v, "Weapon", "PAKFAmissileWeapon") for v in data.values())
    pack_teod_ctrl = sum(count_defs(v, "Weapon", "JetMissileControl") for v in data.values())

    # Duplicate audit for names introduced / forbidden by this patch only
    # (full Specter DATA has intentional first-wins duplicates elsewhere)
    watch_objs = [OLD_PROJECTILE, NEW_PROJECTILE, T50_OBJECT, DONOR_OBJECT]
    watch_weps = [
        T50_WEAPON,
        "Russia_T50_JetMissileControl",
        "Russia_T50_JetMissileControlForcer",
        "PAKFAmissileWeapon",
        "JetMissileControl",
        "JetMissileControlForcer",
    ]
    obj_names = {
        n: sum(count_defs(v, "Object", n) for v in data.values()) for n in watch_objs
    }
    wep_names = {
        n: sum(count_defs(v, "Weapon", n) for v in data.values()) for n in watch_weps
    }
    dup_objs = sorted(
        n
        for n, c in obj_names.items()
        if (n == OLD_PROJECTILE and c > 0)
        or (n != OLD_PROJECTILE and c > 1)
        or (n == DONOR_OBJECT and c > 0)
    )
    dup_weps = sorted(
        n
        for n, c in wep_names.items()
        if n in ("PAKFAmissileWeapon", "JetMissileControl", "JetMissileControlForcer")
        and c > 0
        or n
        in (T50_WEAPON, "Russia_T50_JetMissileControl", "Russia_T50_JetMissileControlForcer")
        and c != 1
    )

    slots = commandset_slots(data[COMMANDSET_KEY], RUNTIME_COMMANDSET)
    slot_map = dict(slots)
    t50_slots = [n for n, b in slots if b == T50_BUTTON]
    ka_slots = [n for n, b in slots if b == OLD_KA52_BUTTON]

    primary = re.search(r"Weapon\s*=\s*PRIMARY\s+(\S+)", obj)
    secondary = re.search(r"Weapon\s*=\s*SECONDARY\s+(\S+)", obj)
    model = "MISSING"
    mm = re.search(r"DefaultConditionState.*?^\s*Model\s*=\s*(\S+)", obj, re.M | re.S)
    if mm:
        model = mm.group(1)

    jet_ai = bool(re.search(r"Behavior\s*=\s*JetAIUpdate\b", obj))
    heli_ai = bool(
        re.search(r"Behavior\s*=\s*ChinookAIUpdate\b", obj)
        or re.search(r"KindOf\s*=.*\bPRODUCED_AT_HELIPAD\b", obj)
    )
    needs_runway = bool(re.search(r"NeedsRunway\s*=\s*Yes", obj, re.I))
    stealth = "StealthUpdate" in obj and "InnateStealth" in obj
    proj = field(wep, "ProjectileObject")
    anti_g = field(wep, "AntiGround")
    anti_air = field(wep, "AntiAirborneVehicle")
    rtb = field(wep, "AutoReloadsClip")
    btn_obj = field(btn, "Object")
    btn_img = field(btn, "ButtonImage")
    proj_model = "MISSING"
    pmm = re.search(r"^\s*Model\s*=\s*(\S+)", proj_obj, re.M)
    if pmm:
        proj_model = pmm.group(1)

    su75 = "Command_ConstructRussiaJetSu75Checkmate" in slot_map.values()
    su47 = "Command_ConstructRussiaJetSu47Recon" in slot_map.values()
    tu160 = "Command_ConstructRussiaJetTU160" in slot_map.values()
    su35ag = "Command_ConstructRussiaJetSu35AG" in slot_map.values()

    missing = 0
    for key in ART_ASSETS:
        if key not in art:
            missing += 1
    if btn_obj != T50_OBJECT:
        missing += 1
    if proj != NEW_PROJECTILE:
        missing += 1
    if pack_t50_proj != 1:
        missing += 1
    if primary is None or primary.group(1) != T50_WEAPON:
        missing += 1
    if r"Art\W3D\R-27.W3D" not in art:
        missing += 1
    # Specter-packed deps used by clone
    if not any(count_defs(v, "Locomotor", "RaptorJetMissileLocomotor") for v in data.values()):
        missing += 1
    if not any(b"ParticleSystem GenericMediumMissileExhaust" in v for v in data.values()):
        missing += 1

    prereq_ok = True
    pm = re.search(r"Prerequisites\b(.*?)End", obj, re.S)
    if pm and re.search(r"Science\s*=|Object\s*=", pm.group(1)):
        prereq_ok = False

    external_teod_dep = proj == OLD_PROJECTILE or "R27" == proj
    parse_ok = (
        jet_ai
        and not heli_ai
        and needs_runway
        and anti_g.lower() == "yes"
        and anti_air.lower() == "yes"
        and "RETURN_TO_BASE" in rtb
        and model == "PAK-FA"
        and len(t50_slots) == 1
        and t50_slots[0] == OLD_KA52_SLOT
        and not ka_slots
        and pack_r27 == 0
        and pack_t50_proj == 1
        and pack_teod_wep == 0
        and pack_teod_ctrl == 0
        and not dup_objs
        and not dup_weps
        and not external_teod_dep
        and prereq_ok
        and "MissileAIUpdate" in proj_obj
        and "RaptorJetMissileLocomotor" in proj_obj
    )

    lines.append(
        r"R27_SOURCE_FILE = !TEOD_INI.big :: Data\INI\Object\WeaponObjects.ini"
    )
    lines.append(f"R27_OBJECT = {OLD_PROJECTILE}")
    lines.append(f"R27_W3D = R-27 (+ SMF exhaust)")
    lines.append("R27_REFERENCED_WEAPON = PAKFAmissileWeapon / Russia_Weapon_T50_PAKFA")
    lines.append(
        "R27_REQUIRED_DEPENDENCIES = RaptorJetMissileLocomotor, ProjectileArmor, "
        "FX_JetMissileIgnition, FX_GenericMissileDeath/Disintegrate, "
        "OCL_GenericMissileDisintegrate, SparksMedium, SMF.W3D, R-27.W3D, "
        "JetMissileControl(+Forcer)/OCL (unique T50 clones), trail particle"
    )
    lines.append(f"SU_T50_SLOT = {t50_slots[0] if t50_slots else 'MISSING'}")
    lines.append(f"SU_T50_OBJECT = {T50_OBJECT}")
    lines.append(f"SU_T50_MODEL = {model}")
    lines.append(f"OLD_PROJECTILE = {OLD_PROJECTILE}")
    lines.append(f"NEW_PATCH_PROJECTILE = {proj}")
    lines.append(f"SU_T50_PROJECTILE_W3D = {proj_model}")
    lines.append(
        f"EXTERNAL_TEOD_PROJECTILE_DEPENDENCY = {'YES' if external_teod_dep else 'NO'}"
    )
    lines.append(f"R27_RUNTIME_DEFINITION_COUNT = {teod_r27}")
    lines.append(f"T50_R27_PATCH_DEFINITION_COUNT = {pack_t50_proj}")
    lines.append(f"PATCH_OBJECT_R27_COUNT = {pack_r27}")
    lines.append(f"DUPLICATE_OBJECT_NAMES = {len(dup_objs)}")
    lines.append(f"DUPLICATE_WEAPON_NAMES = {len(dup_weps)}")
    if dup_objs:
        lines.append(f"DUPLICATE_OBJECTS_LIST = {dup_objs[:20]}")
    if dup_weps:
        lines.append(f"DUPLICATE_WEAPONS_LIST = {dup_weps[:20]}")
    lines.append(f"DUPLICATE_OBJECTS = {len(dup_objs)}")
    lines.append(f"DUPLICATE_PROJECTILES = {pack_r27}")
    lines.append(f"SU_T50_PRIMARY_WEAPON = {primary.group(1) if primary else 'MISSING'}")
    lines.append(
        f"SU_T50_SECONDARY_WEAPON = {secondary.group(1) if secondary else 'none'}"
    )
    lines.append(f"SU_T50_FIXED_WING_AI = {'YES' if jet_ai else 'NO'}")
    lines.append(f"SU_T50_NEEDS_RUNWAY = {'YES' if needs_runway else 'NO'}")
    lines.append(f"SU75_PRESERVED = {'YES' if su75 else 'NO'}")
    lines.append(f"SU47_PRESERVED = {'YES' if su47 else 'NO'}")
    lines.append(f"TU160_PRESERVED = {'YES' if tu160 else 'NO'}")
    lines.append(f"OTHER_SU35_VARIANTS_PRESERVED = {'YES' if su35ag else 'NO'}")
    lines.append("COMMANDSET_MASS_MERGE = NO")
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    lines.append(f"MISSING_REFERENCES = {missing}")
    lines.append(f"INI_PARSE_VALID = {'YES' if parse_ok else 'NO'}")
    lines.append("RussiaAirfieldCommandSet slots:")
    for n, b in slots:
        lines.append(f"  {n} = {b}")
    lines.append(
        "CLAIM = SU-T50 PATCH-SAFE R27 CLONE — RUNTIME COMBAT TEST REQUIRED"
    )

    if not parse_ok:
        raise RuntimeError("INI_PARSE_VALID failed\n" + "\n".join(lines))
    if missing:
        raise RuntimeError(f"MISSING_REFERENCES={missing}\n" + "\n".join(lines))
    if pack_r27 or pack_teod_wep or pack_teod_ctrl:
        raise RuntimeError("Forbidden TEOD original defs packed")
    if dup_objs or dup_weps:
        raise RuntimeError(f"Duplicate names objs={dup_objs} weps={dup_weps}")
    if not (su75 and su47 and tu160 and su35ag):
        raise RuntimeError("Preserved Russia aircraft missing from CommandSet")
    return lines


def main() -> int:
    raise SystemExit(
        "DEPRECATED/BANNED: Russia_T50_R27_Projectile crashes SAGE INI parse.\n"
        "Use patch/tools/big/build_russia_sut50_r27_crashfix.py instead "
        "(ProjectileObject = R27 from !TEOD_INI.big; no custom R27 clone)."
    )
    if not BASE.exists():
        raise SystemExit(f"Missing baseline {BASE}")
    art_base = BASE / "_SPEC_ART_ONE.big"
    data_base = BASE / "_SPEC_DATA_ONE.big"
    if not art_base.exists() or not data_base.exists():
        raise SystemExit("Baseline BIG missing")
    if not TEOD_INI.exists():
        raise SystemExit(f"Missing TEOD INI for R27 validation: {TEOD_INI}")
    for p in [
        OBJ_INI,
        WEAPON_INI,
        LOCO_INI,
        PROJ_INI,
        SUPPORT_WEAPON_INI,
        OCL_INI,
        MAPPED_INI,
        STRINGS_TXT,
    ]:
        if not p.exists():
            raise SystemExit(f"Missing source {p}")
    for p in ART_ASSETS.values():
        if not p.exists():
            raise SystemExit(f"Missing art {p}")

    # Source crash guards
    wep_src = WEAPON_INI.read_text(encoding="latin1", errors="replace")
    if re.search(r"^Object\s+R27\b", wep_src, re.M):
        raise RuntimeError("Weapon file must not define Object R27")
    if "ProjectileObject            = R27" in wep_src or re.search(
        r"ProjectileObject\s*=\s*R27\b", wep_src
    ):
        raise RuntimeError("Weapon still points at external TEOD Object R27")
    if NEW_PROJECTILE not in wep_src:
        raise RuntimeError(f"Weapon must use {NEW_PROJECTILE}")
    proj_src = PROJ_INI.read_text(encoding="latin1", errors="replace")
    if re.search(r"^Object\s+R27\b", proj_src, re.M):
        raise RuntimeError("Projectile file must not define Object R27")
    if f"Object {NEW_PROJECTILE}" not in proj_src:
        raise RuntimeError(f"Missing Object {NEW_PROJECTILE}")
    obj_src = OBJ_INI.read_text(encoding="latin1", errors="replace")
    if re.search(r"^\s*Behavior\s*=\s*ChinookAIUpdate\b", obj_src, re.M) or re.search(
        r"^\s*KindOf\s*=.*\bPRODUCED_AT_HELIPAD\b", obj_src, re.M
    ):
        raise RuntimeError("Object still has helicopter AI")
    if "NeedsRunway" not in obj_src:
        raise RuntimeError("NeedsRunway missing on T50 object")

    teod = read_big(TEOD_INI)

    with tempfile.TemporaryDirectory(prefix="t50_stage_") as td:
        stage = Path(td)
        stage_art = stage / "_SPEC_ART_ONE.big"
        stage_data = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(art_base, stage_art)
        shutil.copy2(data_base, stage_data)
        art = read_big(stage_art)
        data = read_big(stage_data)

        before_cs = cs_map(data[COMMANDSET_KEY])
        base_slots = dict(commandset_slots(data[COMMANDSET_KEY], RUNTIME_COMMANDSET))
        if base_slots.get(OLD_KA52_SLOT) != OLD_KA52_BUTTON:
            raise RuntimeError(
                f"Baseline slot {OLD_KA52_SLOT} = {base_slots.get(OLD_KA52_SLOT)}, "
                f"want {OLD_KA52_BUTTON}"
            )

        for key, path in ART_ASSETS.items():
            art[key] = path.read_bytes()

        data[OBJ_KEY] = OBJ_INI.read_bytes()
        data[WEAPON_KEY] = WEAPON_INI.read_bytes()
        data[LOCO_KEY] = LOCO_INI.read_bytes()
        data[PROJ_KEY] = PROJ_INI.read_bytes()
        data[SUPPORT_WEAPON_KEY] = SUPPORT_WEAPON_INI.read_bytes()
        data[OCL_KEY] = OCL_INI.read_bytes()
        data[MAPPED_KEY] = MAPPED_INI.read_bytes()
        data[STRINGS_KEY] = STRINGS_TXT.read_bytes()
        data[BUTTON_KEY] = ensure_t50_command_button(data[BUTTON_KEY])
        data[COMMANDSET_KEY] = patch_russia_airfield_commandset(data[COMMANDSET_KEY])
        data[CSF_KEY] = patch_csf(data[CSF_KEY], CSF_LABELS)

        # Guard: never pack Object R27 / TEOD original weapon/control names
        for key, blob in list(data.items()):
            if count_defs(blob, "Object", "R27"):
                raise RuntimeError(f"Packed Object R27 in {key}")
            if count_defs(blob, "Weapon", "PAKFAmissileWeapon"):
                raise RuntimeError(f"Packed TEOD Weapon PAKFAmissileWeapon in {key}")
            if count_defs(blob, "Weapon", "JetMissileControl"):
                raise RuntimeError(f"Packed TEOD Weapon JetMissileControl in {key}")
            if count_defs(blob, "Weapon", "JetMissileControlForcer"):
                raise RuntimeError(
                    f"Packed TEOD Weapon JetMissileControlForcer in {key}"
                )
            if count_defs(blob, "Object", DONOR_OBJECT):
                raise RuntimeError(f"Packed full donor object {DONOR_OBJECT} in {key}")

        after_cs = cs_map(data[COMMANDSET_KEY])
        for name, body in before_cs.items():
            if name == RUNTIME_COMMANDSET:
                continue
            if after_cs.get(name) != body:
                raise RuntimeError(f"Unintended CommandSet change: {name}")

        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            zold = OUT / "SPECTER_RUSSIA_SUT50_PAKFA.zip"
            if zold.exists():
                zold.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        art2 = read_big(art_out)
        data2 = read_big(data_out)
        report = validate(art2, data2, teod)
        report.insert(0, "PACK = SPECTER_RUSSIA_SUT50_PAKFA")
        report.insert(1, f"BASELINE = {BASE.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_ENTRIES = {len(art2)}")
        report.append(f"DATA_ENTRIES = {len(data2)}")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

        readme = (
            "SPECTER Russia SU-T50 / PAK FA — clean TEOD donor\n"
            "\n"
            "Install: replace game _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "\n"
            "Replaces former KA-52M button on RussiaAirfieldCommandSet slot 11.\n"
            "Fixed-wing JetAI + NeedsRunway. Donor stealth preserved.\n"
            "ProjectileObject = Russia_T50_R27_Projectile\n"
            "(complete unique clone of TEOD Object R27 — Object R27 is NOT redefined).\n"
            "SU-T50 has NO external TEOD projectile dependency.\n"
            "\n"
            "CLAIM: SU-T50 PATCH-SAFE R27 CLONE — RUNTIME TEST REQUIRED\n"
        )
        (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
        (OUT / "TRACE_REPORT.txt").write_text(
            "\n".join(
                ln
                for ln in report
                if ln.startswith(
                    (
                        "R27_",
                        "KA52_",
                        "SU_T50_",
                        "OLD_PROJECTILE",
                        "NEW_PATCH_",
                        "EXTERNAL_",
                        "T50_R27_",
                        "PATCH_",
                        "DONOR_",
                        "SU75_",
                        "SU47_",
                        "TU160_",
                        "OTHER_",
                        "COMMANDSET_",
                        "DUPLICATE_",
                        "MISSING_",
                        "INI_",
                        "CLAIM",
                    )
                )
            )
            + "\n",
            encoding="utf-8",
        )

        zip_path = OUT / "SPECTER_RUSSIA_SUT50_PAKFA.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(art_out, arcname="_SPEC_ART_ONE.big")
            zf.write(data_out, arcname="_SPEC_DATA_ONE.big")
            zf.write(OUT / "VERIFY.txt", arcname="VERIFY.txt")
            zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")
            zf.write(OUT / "TRACE_REPORT.txt", arcname="TRACE_REPORT.txt")

        print("\n".join(report))
        print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
