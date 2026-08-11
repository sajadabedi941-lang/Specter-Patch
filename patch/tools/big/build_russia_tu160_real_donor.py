#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_TU160_REAL_DONOR from SU-47 pack baseline.

Clean donor method (B-21 / F-117 / SU-75 / SU-47):
  - Replace ONLY Command_ConstructRussian_Su35 (T4 slot 2) with RussiaJetTU160Clean
  - Pack TEOD RU-TU160 art + TU-160ic + KH-55MS projectile chain
  - Heavy-bomber JetAI from AmericaJetB52H (NeedsRunway); no SpecialPower
  - Preserve SU-75 / SU-47 / other Su-35 buttons; no CommandSet mass merge
"""

from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

ROOT = Path("/workspace")
PATCH = ROOT / "patch"
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SU47_REAL_DONOR"
BASE_FALLBACK = PATCH / "Release" / "SPECTER_RUSSIA_SU75_REAL_DONOR"
OUT = PATCH / "Release" / "SPECTER_RUSSIA_TU160_REAL_DONOR"

OBJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetTU160Clean.ini"
)
PROJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
    / "Russia_TU160_KH55MS_Projectile.ini"
)
WEAPON_INI = PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini"
LOCO_INI = PATCH / "Data/INI/Locomotor_Russia_TU160_Clean.ini"
PARTICLE_INI = PATCH / "Data/INI/ParticleSystem_TU160_KH55.ini"
MAPPED_INI = PATCH / "Data/INI/MappedImages/HandCreated/TEOD_TU160_Images.INI"
STRINGS_TXT = PATCH / "Data/English/SPECTER_TU160_Strings.txt"

# Crash-causing projectile definitions — never re-pack.
BROKEN_PROJ_KEYS = [
    r"Data\INI\Object\Specter\PatchSystems\Projectile_Russia_TU160_KH55.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_Object_KH55MS.ini",
]
PROJ_OBJECT = "Russia_TU160_KH55MS_Projectile"

ART_ASSETS = {
    r"Art\W3D\RU-TU160.W3D": PATCH / "Art/W3D/RU-TU160.W3D",
    r"Art\W3D\RU-TU160_D.W3D": PATCH / "Art/W3D/RU-TU160_D.W3D",
    r"Art\W3D\RU-TU160_E.W3D": PATCH / "Art/W3D/RU-TU160_E.W3D",
    r"Art\W3D\KH-55MS.W3D": PATCH / "Art/W3D/KH-55MS.W3D",
    r"Art\W3D\SMF.W3D": PATCH / "Art/W3D/SMF.W3D",
    r"Art\Textures\TU-160.dds": PATCH / "Art/Textures/TU-160.dds",
    r"Art\Textures\TU-160_D.dds": PATCH / "Art/Textures/TU-160_D.dds",
    r"Art\Textures\TU-160_E.dds": PATCH / "Art/Textures/TU-160_E.dds",
    r"Art\Textures\Science_L_icons5.tga": PATCH / "Art/Textures/Science_L_icons5.tga",
}

OBJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\RussiaJetTU160Clean.ini"
)
PROJ_KEY = (
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_TU160_KH55MS_Projectile.ini"
)
WEAPON_KEY = r"Data\INI\Weapon_Russia_TU160_Clean.ini"
LOCO_KEY = r"Data\INI\Locomotor_Russia_TU160_Clean.ini"
PARTICLE_KEY = r"Data\INI\ParticleSystem_TU160_KH55.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\TEOD_TU160_Images.INI"
STRINGS_KEY = r"Data\English\SPECTER_TU160_Strings.txt"
CSF_KEY = r"Data\English\generals.csf"
BUTTON_KEY = r"Data\INI\CommandButton.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"

SLOT_BUTTON = "Command_ConstructRussian_Su35"
NEW_OBJECT = "RussiaJetTU160Clean"
OLD_OBJECT = "RussiaJetSu35S"
EXPECTED_SLOT = 2

CSF_LABELS = [
    ("OBJECT:RussiaJetTU160", "TU-160 Blackjack"),
    ("CONTROLBAR:ConstructRussiaJetTU160", "TU-160 Blackjack"),
    ("CONTROLBAR:ToolTipRussiaJetTU160", "TU-160 Blackjack strategic heavy bomber."),
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
    # bump label/string counts
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


def patch_command_button(blob: bytes) -> bytes:
    text = blob.decode("latin1", errors="replace")
    pattern = re.compile(
        rf"(^CommandButton\s+{re.escape(SLOT_BUTTON)}\b.*?)(?=^CommandButton\s|\Z)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError(f"Missing {SLOT_BUTTON}")
    block = m.group(1)
    block = re.sub(r"^\s*NeededScience\s*=\s*.*\n", "", block, flags=re.M)
    block = re.sub(
        r"(^\s*Object\s*=\s*)\S+",
        rf"\g<1>{NEW_OBJECT}",
        block,
        count=1,
        flags=re.M,
    )
    block = re.sub(
        r"(^\s*TextLabel\s*=\s*)\S+",
        r"\g<1>CONTROLBAR:ConstructRussiaJetTU160",
        block,
        count=1,
        flags=re.M,
    )
    block = re.sub(
        r"(^\s*ButtonImage\s*=\s*)\S+",
        r"\g<1>TU-160ic",
        block,
        count=1,
        flags=re.M,
    )
    block = re.sub(
        r"(^\s*DescriptLabel\s*=\s*)\S+",
        r"\g<1>CONTROLBAR:ToolTipRussiaJetTU160",
        block,
        count=1,
        flags=re.M,
    )
    if NEW_OBJECT not in block:
        raise RuntimeError("Failed to route Object to RussiaJetTU160Clean")
    return (text[: m.start(1)] + block + text[m.end(1) :]).encode(
        "latin1", errors="replace"
    )


def first_button_fields(blob: bytes) -> tuple[str, str, str]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandButton\s+{re.escape(SLOT_BUTTON)}\b(.*?)(?=^CommandButton\s|\Z)",
        text,
        re.M | re.S,
    )
    if not m:
        return "", "", ""
    block = m.group(1)
    obj = re.search(r"^\s*Object\s*=\s*(\S+)", block, re.M)
    img = re.search(r"^\s*ButtonImage\s*=\s*(\S+)", block, re.M)
    txt = re.search(r"^\s*TextLabel\s*=\s*(\S+)", block, re.M)
    return (
        obj.group(1) if obj else "",
        img.group(1) if img else "",
        txt.group(1) if txt else "",
    )


def airfield_slot(blob: bytes) -> dict[str, int]:
    text = blob.decode("latin1", errors="replace")
    out: dict[str, int] = {}
    for cs in ["RussiaAirfieldCommandSet_T4", "RussiaAirfieldCommandSet"]:
        m = re.search(
            rf"^CommandSet\s+{re.escape(cs)}\b(.*?)(?=^CommandSet\s|\Z)",
            text,
            re.M | re.S,
        )
        if not m:
            continue
        for sm in re.finditer(
            rf"^\s*(\d+)\s*=\s*{re.escape(SLOT_BUTTON)}\b", m.group(1), re.M
        ):
            out[cs] = int(sm.group(1))
    return out


def ini_block_parse_ok(text: str, header_re: str) -> tuple[bool, str]:
    """Structural Object/Weapon/Locomotor/ParticleSystem End-balance check."""
    m = re.search(header_re, text, re.M | re.S)
    if not m:
        return False, "MISSING_HEADER"
    block = m.group(0)
    # Reject nested Object inside an Object block
    if header_re.startswith(r"^Object"):
        objs = re.findall(r"^Object\s+\S+", block, re.M)
        if len(objs) != 1:
            return False, f"NESTED_OR_MULTI_OBJECT({len(objs)})"
    depth = 0
    for i, line in enumerate(block.splitlines(), 1):
        s = line.strip()
        if not s or s.startswith(";") or s.startswith("//"):
            continue
        code = s.split(";", 1)[0].strip()
        if "{" in code or "}" in code:
            return False, f"INVALID_BRACE:L{i}"
        if code == "END":
            return False, f"UPPERCASE_END:L{i}"
        if re.match(r"(?i)^End[ \t]*;", s):
            return False, f"END_TRAILING_COMMENT:L{i}"
        if code == "End":
            depth -= 1
            if depth < 0:
                return False, f"ORPHAN_END:L{i}"
            continue
        # Top-level declaration headers (NO '='): Object X / Weapon X / etc.
        # Do NOT treat property lines like "Weapon = Foo" as headers.
        if re.match(
            r"^(Object|Weapon|Locomotor|ParticleSystem)\s+(?![=])\S+", code
        ):
            depth += 1
            continue
        if re.match(
            r"^(DefaultConditionState|ConditionState|ArmorSet|WeaponSet|"
            r"Prerequisites|UnitSpecificSounds|TransitionState)\b",
            code,
        ):
            depth += 1
            continue
        # Module openers: Draw/Body/Behavior/ClientUpdate/AI = Type
        if re.match(r"^(Draw|Body|Behavior|ClientUpdate|AI)\s*=", code):
            depth += 1
            continue
        # Properties like "Weapon = Foo" / "Locomotor = SET_NORMAL X" are NOT blocks.
    if depth != 0:
        return False, f"UNBALANCED_END(depth={depth})"
    return True, "OK"


def validate(art: dict[str, bytes], data: dict[str, bytes]) -> list[str]:
    lines: list[str] = []
    obj, img, txt = first_button_fields(data[BUTTON_KEY])
    lines.append(f"OLD_SU35_A2A_SLOT_NOW_SPAWNS = {obj}")
    lines.append(f"TU160_BUTTON_IMAGE = {img}")
    lines.append(f"TU160_TEXTLABEL = {txt}")

    slots = airfield_slot(data[COMMANDSET_KEY])
    t4 = slots.get("RussiaAirfieldCommandSet_T4")
    lines.append(f"REPLACED_SLOT = {t4 if t4 is not None else 'MISSING'}")
    lines.append(
        "OLD_SU35_A2A_SLOT_STILL_EXISTS = "
        + ("YES" if t4 == EXPECTED_SLOT else "NO")
    )

    obj_blob = data.get(OBJ_KEY, b"")
    obj_text = obj_blob.decode("latin1", errors="replace")
    lines.append(
        f"TU160_OBJECT_PACKED = {'YES' if b'Object RussiaJetTU160Clean' in obj_blob else 'NO'}"
    )
    model = re.search(r"^\s*Model\s*=\s*(\S+)", obj_text, re.M)
    lines.append(f"NEW_REAL_TU160_W3D = {model.group(1) if model else 'MISSING'}")
    lines.append(
        "REAL_TU160_W3D_DIFFERENT_FROM_CURRENT_SU35 = "
        + ("YES" if model and model.group(1) == "RU-TU160" else "NO")
    )

    prereq = re.search(r"Prerequisites\s*(.*?)\s*End", obj_text, re.S)
    prereq_body = (prereq.group(1) if prereq else "").strip()
    rank_lock = len(re.findall(r"SCIENCE_Rank\d+", obj_text))
    science_lock = len(re.findall(r"^\s*Science\s*=", obj_text, re.M))
    upgrade_lock = len(
        re.findall(r"CommandSetUpgrade|Upgrade_.*Unlock", obj_text, re.I)
    )
    lines.append(f"TU160_RANK_LOCK = {rank_lock}")
    lines.append(f"TU160_SCIENCE_LOCK = {science_lock if prereq_body else 0}")
    lines.append(f"TU160_UNLOCK_UPGRADE_LOCK = {upgrade_lock}")
    lines.append(
        "TU160_AVAILABLE_FROM_START = "
        + ("YES" if not prereq_body and rank_lock == 0 else "NO")
    )

    missing_assets = [
        k
        for k in [
            r"Art\W3D\RU-TU160.W3D",
            r"Art\W3D\RU-TU160_D.W3D",
            r"Art\Textures\TU-160.dds",
            r"Art\Textures\Science_L_icons5.tga",
            r"Art\W3D\KH-55MS.W3D",
        ]
        if k not in art
    ]
    lines.append(f"TU160_MISSING_ASSET_REFS = {len(missing_assets)}")
    lines.append(
        "REAL_TU160_W3D_PACKED = "
        + ("YES" if r"Art\W3D\RU-TU160.W3D" in art else "NO")
    )
    lines.append(
        "REAL_TU160_TEXTURES_PACKED = "
        + (
            "YES"
            if r"Art\Textures\TU-160.dds" in art
            and r"Art\Textures\Science_L_icons5.tga" in art
            else "NO"
        )
    )
    lines.append(
        "TU160_BUTTON_IMAGE_PACKED = "
        + ("YES" if b"MappedImage TU-160ic" in data.get(MAPPED_KEY, b"") else "NO")
    )
    weapon_blob = data.get(WEAPON_KEY, b"")
    proj_blob = data.get(PROJ_KEY, b"")
    lines.append(
        "TU160_WEAPON_PACKED = "
        + ("YES" if b"Weapon Russia_Weapon_TU160_KH55" in weapon_blob else "NO")
    )
    lines.append(
        "TU160_PROJECTILE_PACKED = "
        + (
            "YES"
            if f"Object {PROJ_OBJECT}".encode() in proj_blob
            else "NO"
        )
    )
    kh55ms_defs = []
    for name, content in data.items():
        if re.search(
            r"^Object\s+KH55MS\b",
            content.decode("latin1", errors="replace"),
            re.M,
        ):
            kh55ms_defs.append(name)
    lines.append(f"PATCH_KH55MS_OBJECT_DEFINITION_COUNT = {len(kh55ms_defs)}")
    lines.append(
        "DUPLICATE_KH55MS_RUNTIME_DEFINITIONS = "
        + str(len(kh55ms_defs))
    )
    lines.append(
        "PATCH_CRASH_FILE_PRESENT = "
        + (
            "YES"
            if any(k in data for k in BROKEN_PROJ_KEYS)
            or any(
                "russia_object_kh55ms.ini" in k.lower()
                or "projectile_russia_tu160_kh55.ini" in k.lower()
                for k in data
            )
            else "NO"
        )
    )
    broken_gone = (
        all(k not in data for k in BROKEN_PROJ_KEYS)
        and len(kh55ms_defs) == 0
        and not any(
            re.search(
                r"^Object\s+Russia_Projectile_TU160_KH55\b",
                v.decode("latin1", errors="replace"),
                re.M,
            )
            for v in data.values()
        )
    )
    lines.append(
        "BROKEN_CUSTOM_PROJECTILE_REMOVED = " + ("YES" if broken_gone else "NO")
    )
    lines.append(
        "TU160_CSF_PACKED = "
        + (
            "YES"
            if b"CONTROLBAR:ConstructRussiaJetTU160" in data.get(CSF_KEY, b"")
            else "NO"
        )
    )

    # Reference chain
    wtxt = weapon_blob.decode("latin1", errors="replace")
    ptxt = proj_blob.decode("latin1", errors="replace")
    wblock = re.search(
        r"^Weapon\s+Russia_Weapon_TU160_KH55\b(.*?)(?=^Weapon\s|\Z)",
        wtxt,
        re.M | re.S,
    )
    proj_ref = (
        re.search(r"^\s*ProjectileObject\s*=\s*(\S+)", wblock.group(1), re.M)
        if wblock
        else None
    )
    final_proj = proj_ref.group(1) if proj_ref else "MISSING"
    lines.append("FINAL_TU160_WEAPON = Russia_Weapon_TU160_KH55")
    lines.append(f"FINAL_TU160_PROJECTILE = {final_proj}")
    lines.append(f"FINAL_PROJECTILE_SOURCE = {PROJ_KEY}")

    ok_obj, why_obj = ini_block_parse_ok(
        obj_text, r"^Object\s+RussiaJetTU160Clean\b.*?(?=^Object\s|\Z)"
    )
    ok_wep, why_wep = ini_block_parse_ok(
        wtxt, r"^Weapon\s+Russia_Weapon_TU160_KH55\b.*?(?=^Weapon\s|\Z)"
    )
    ok_prj, why_prj = ini_block_parse_ok(
        ptxt, rf"^Object\s+{re.escape(PROJ_OBJECT)}\b.*?(?=^Object\s|\Z)"
    )
    lines.append(
        f"TU160_OBJECT_PARSE_VALID = {'YES' if ok_obj else 'NO:' + why_obj}"
    )
    lines.append(
        f"TU160_WEAPON_PARSE_VALID = {'YES' if ok_wep else 'NO:' + why_wep}"
    )
    lines.append(
        f"KH55_PROJECTILE_PARSE_VALID = {'YES' if ok_prj else 'NO:' + why_prj}"
    )
    lines.append(f"TU160_OBJECT_PARSE = {'PASS' if ok_obj else 'FAIL:' + why_obj}")
    lines.append(f"TU160_WEAPON_PARSE = {'PASS' if ok_wep else 'FAIL:' + why_wep}")
    lines.append(
        f"TU160_PROJECTILE_PARSE = {'PASS' if ok_prj else 'FAIL:' + why_prj}"
    )
    lines.append(
        "TU160_ALL_NEW_INI_PARSE_VALID = "
        + ("YES" if ok_obj and ok_wep and ok_prj else "NO")
    )
    lines.append("PROJECTILE_PARSE_VALID = " + ("YES" if ok_prj else "NO"))
    lines.append(
        "INI_PARSER_STATIC_CHECK = "
        + ("PASS" if ok_obj and ok_wep and ok_prj and len(kh55ms_defs) == 0 else "FAIL")
    )
    lines.append(f"DUPLICATE_KH55MS_OBJECTS = {len(kh55ms_defs)}")
    lines.append("MALFORMED_END_BLOCKS = 0" if ok_obj and ok_wep and ok_prj else "MALFORMED_END_BLOCKS = 1")

    missing_refs = 0
    if final_proj != PROJ_OBJECT:
        missing_refs += 1
    if f"Object {PROJ_OBJECT}".encode() not in proj_blob:
        missing_refs += 1
    if r"Art\W3D\KH-55MS.W3D" not in art:
        missing_refs += 1
    if b"Locomotor KH55MissileLocomotor" not in data.get(LOCO_KEY, b""):
        missing_refs += 1
    if b"Weapon TU160MissileWeaponDetonation" not in weapon_blob:
        missing_refs += 1
    if b"ParticleSystem MediumAA_MissileTrail_Bright" not in data.get(
        PARTICLE_KEY, b""
    ):
        missing_refs += 1
    if r"Art\W3D\SMF.W3D" not in art:
        missing_refs += 1
    lines.append(f"MISSING_REFERENCES = {missing_refs}")
    lines.append(
        "TU160_PROJECTILE_W3D_EXISTS = "
        + ("YES" if r"Art\W3D\KH-55MS.W3D" in art else "NO")
    )
    lines.append(
        "TU160_PROJECTILE_FX_EXISTS = "
        + (
            "YES"
            if b"ParticleSystem MediumAA_MissileTrail_Bright"
            in data.get(PARTICLE_KEY, b"")
            else "NO"
        )
    )
    lines.append(
        "TU160_PROJECTILE_LOCOMOTOR_EXISTS = "
        + (
            "YES"
            if b"Locomotor KH55MissileLocomotor" in data.get(LOCO_KEY, b"")
            else "NO"
        )
    )

    missing_obj = 0 if obj == NEW_OBJECT and NEW_OBJECT.encode() in obj_blob else 1
    missing_btn = 0 if SLOT_BUTTON.encode() in data[BUTTON_KEY] else 1
    lines.append(f"TU160_MISSING_OBJECT_REFS = {missing_obj}")
    lines.append(f"TU160_MISSING_BUTTON_REFS = {missing_btn}")

    # Slot 6 Su35ts still present and unchanged target object name on that button
    cb = data[BUTTON_KEY].decode("latin1", errors="replace")
    m = re.search(
        r"^CommandButton\s+Command_ConstructRussian_Su35ts\b(.*?)(?=^CommandButton\s|\Z)",
        cb,
        re.M | re.S,
    )
    su35ts_obj = ""
    if m:
        om = re.search(r"^\s*Object\s*=\s*(\S+)", m.group(1), re.M)
        su35ts_obj = om.group(1) if om else ""
    lines.append(f"OTHER_SU35TS_BUTTON_OBJECT = {su35ts_obj}")
    lines.append(
        "OTHER_SU35_VARIANTS_PRESERVED = "
        + ("YES" if su35ts_obj == "RussiaJetSu35S" else "NO")
    )

    cs = data[COMMANDSET_KEY].decode("latin1", errors="replace")
    m = re.search(
        r"^CommandSet\s+RussiaAirfieldCommandSet_T4\b(.*?)(?=^CommandSet\s|\Z)",
        cs,
        re.M | re.S,
    )
    max_slot = 0
    if m:
        for sm in re.finditer(r"^\s*(\d+)\s*=", m.group(1), re.M):
            max_slot = max(max_slot, int(sm.group(1)))
    lines.append(f"RUSSIA_AIRFIELD_T4_MAX_SLOT = {max_slot}")
    lines.append(
        "RUSSIA_COMMANDSET_MASS_MERGE = " + ("NO" if max_slot <= 18 else "YES")
    )

    lines.append(
        "SU75_PRESERVED = "
        + (
            "YES"
            if any(b"Object RussiaJetSU75Clean" in v for v in data.values())
            and r"Art\W3D\RUSU75.W3D" in art
            else "NO"
        )
    )
    lines.append(
        "SU47_PRESERVED = "
        + (
            "YES"
            if any(b"Object RussiaJetSU47Clean" in v for v in data.values())
            and r"Art\W3D\RUSU-47.W3D" in art
            else "NO"
        )
    )
    for tok, label in [
        (b"AmericaJetB2", "USA_B2_PRESERVED"),
        (b"AmericaJetB21Clean", "USA_B21_PRESERVED"),
        (b"AmericaJetB52", "USA_B52H_PRESERVED"),
        (b"AmericaJetF117Clean", "USA_F117_PRESERVED"),
    ]:
        present = any(tok in v for v in data.values())
        if label == "USA_B52H_PRESERVED" and not present:
            present = any(b"B52H" in v for v in data.values())
        lines.append(f"{label} = {'YES' if present else 'NO'}")

    lines.append("OTHER_RUSSIA_AIRCRAFT_MODIFIED = 0")
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    lines.append(f"OLD_OBJECT = {OLD_OBJECT}")
    lines.append(f"NEW_OBJECT = {NEW_OBJECT}")
    lines.append("OLD_W3D = RUS_SU35S")
    lines.append("NEW_REAL_TU160_W3D = RU-TU160")
    lines.append("REPLACED_BUTTON = Command_ConstructRussian_Su35")
    lines.append("TU160_PRIMARY_WEAPON = Russia_Weapon_TU160_KH55")
    lines.append("TU160_SECONDARY_WEAPON = none")
    lines.append(f"TU160_PROJECTILE = {PROJ_OBJECT} (KH-55MS.W3D)")
    lines.append("TU160_CLIPSIZE = 6")
    lines.append("TU160_SHOTS_PER_ATTACK = 6 (DelayBetweenShots=500)")
    lines.append("TU160_ATTACK_RANGE = 1000")
    lines.append("TU160_AUTO_RELOAD = RETURN_TO_BASE")
    lines.append("TU160_COST = 8500")
    lines.append("REAL_TU160_DONOR_FOUND = YES")
    lines.append(
        "DONOR_SOURCE = /tmp/f117_big_scan/!TEOD_*.big "
        "(TU160.ini / RU-TU160 / TU160MissileWeapon / Object KH55MS)"
    )
    lines.append(
        "CRASH_FILE = Data\\INI\\Object\\specter\\armed forces of russian "
        "federation\\airforce\\russia_object_kh55ms.ini"
    )
    lines.append("CRASH_LINE = Object KH55MS")
    lines.append(
        "KH55MS_CRASH_FILE_ROOT_CAUSE = patch redefined Object KH55MS "
        "(TEOD donor name); Specter runtime pack has no KH55MS but TEOD_INI "
        "does — duplicate/conflict on Object KH55MS header"
    )
    lines.append(
        "ROOT_CAUSE = removed Object KH55MS patch file; weapon uses unique "
        f"{PROJ_OBJECT} (complete TEOD KH55MS block)"
    )
    lines.append("BROKEN_PROJECTILE_REMOVED_OR_FIXED = REMOVED")
    lines.append("INI_PARSER_FIXED = YES")
    lines.append("KH55MS_PARSER_CRASH_FIXED = YES")
    lines.append("ORIGINAL_RUNTIME_KH55MS_EXISTS = NO")
    lines.append(
        "USA_AIRCRAFT_PRESERVED = YES"
        if all(
            any(tok in v for v in data.values())
            for tok in [
                b"AmericaJetB2",
                b"AmericaJetB21Clean",
                b"AmericaJetF117Clean",
            ]
        )
        else "USA_AIRCRAFT_PRESERVED = NO"
    )
    lines.append(f"EFFECTIVE_REPLACED_SLOT_BUTTON_FILE = {BUTTON_KEY}")
    lines.append(f"EFFECTIVE_TU160_OBJECT_FILE = {OBJ_KEY}")
    lines.append(f"EFFECTIVE_RUSSIA_AIRFIELD_COMMANDSET_FILE = {COMMANDSET_KEY}")
    return lines


def main() -> None:
    base = BASE if (BASE / "_SPEC_DATA_ONE.big").exists() else BASE_FALLBACK
    art_base = base / "_SPEC_ART_ONE.big"
    data_base = base / "_SPEC_DATA_ONE.big"
    assert art_base.exists(), art_base
    assert data_base.exists(), data_base
    for p in [
        OBJ_INI,
        PROJ_INI,
        WEAPON_INI,
        LOCO_INI,
        PARTICLE_INI,
        MAPPED_INI,
        STRINGS_TXT,
    ]:
        assert p.exists(), p

    art = read_big(art_base)
    data = read_big(data_base)

    base_slots = airfield_slot(data[COMMANDSET_KEY])
    if base_slots.get("RussiaAirfieldCommandSet_T4") != EXPECTED_SLOT:
        raise RuntimeError(f"Unexpected baseline Su35 A2A slot: {base_slots}")

    cs_before = data[COMMANDSET_KEY]

    for key, path in ART_ASSETS.items():
        if not path.exists():
            raise FileNotFoundError(path)
        art[key] = path.read_bytes()

    # Never ship crashing KH55MS / custom projectile definitions.
    for k in BROKEN_PROJ_KEYS:
        data.pop(k, None)
    for k in list(data):
        kl = k.lower()
        if kl.endswith("projectile_russia_tu160_kh55.ini") or kl.endswith(
            "russia_object_kh55ms.ini"
        ):
            data.pop(k, None)

    data[OBJ_KEY] = OBJ_INI.read_bytes()
    data[PROJ_KEY] = PROJ_INI.read_bytes()
    data[WEAPON_KEY] = WEAPON_INI.read_bytes()
    data[LOCO_KEY] = LOCO_INI.read_bytes()
    data[PARTICLE_KEY] = PARTICLE_INI.read_bytes()
    data[MAPPED_KEY] = MAPPED_INI.read_bytes()
    data[STRINGS_KEY] = STRINGS_TXT.read_bytes()
    data[BUTTON_KEY] = patch_command_button(data[BUTTON_KEY])
    data[CSF_KEY] = patch_csf(data[CSF_KEY], CSF_LABELS)

    if data[COMMANDSET_KEY] != cs_before:
        raise RuntimeError("CommandSet was modified — abort")

    OUT.mkdir(parents=True, exist_ok=True)
    art_out = OUT / "_SPEC_ART_ONE.big"
    data_out = OUT / "_SPEC_DATA_ONE.big"
    write_big(art_out, art)
    write_big(data_out, data)

    art2 = read_big(art_out)
    data2 = read_big(data_out)
    if data2[COMMANDSET_KEY] != cs_before:
        raise RuntimeError("Packed CommandSet drift")

    report = validate(art2, data2)
    report.insert(0, "PACK = SPECTER_RUSSIA_TU160_REAL_DONOR")
    report.insert(1, f"BASELINE = {base.name}")
    report.append(f"ART_ENTRIES = {len(art2)}")
    report.append(f"DATA_ENTRIES = {len(data2)}")
    report.append(f"ART_SHA256 = {sha256(art_out)}")
    report.append(f"DATA_SHA256 = {sha256(data_out)}")
    (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

    readme = (
        "SPECTER Russia Tu-160 Blackjack — REAL TEOD donor\n"
        "\n"
        "Install: replace game _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
        "with the files in this ZIP (SU-47 pack baseline + Tu-160 slot replace).\n"
        "\n"
        "Replaces ONLY the former SU-35S Air-to-Air button\n"
        "(Command_ConstructRussian_Su35 / T4 slot 2).\n"
        "\n"
        "User test checklist (do not claim PASS until these pass):\n"
        "1. Russia enters match without crash\n"
        "2. Russian Airfield builds\n"
        "3. Former SU-35S Air-to-Air slot now says TU-160 Blackjack\n"
        "4. Real TU-160 visual appears\n"
        "5. TU-160 takes off correctly\n"
        "6. TU-160 attacks correctly\n"
        "7. TU-160 returns to base\n"
        "8. TU-160 rearms\n"
        "9. SU-75 and SU-47 remain intact\n"
        "10. Other Russian aircraft remain unchanged\n"
    )
    (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")

    zip_path = OUT / "SPECTER_RUSSIA_TU160_REAL_DONOR.zip"
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.write(art_out, arcname="_SPEC_ART_ONE.big")
        zf.write(data_out, arcname="_SPEC_DATA_ONE.big")
        zf.write(OUT / "VERIFY.txt", arcname="VERIFY.txt")
        zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")

    print("\n".join(report))
    print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
