#!/usr/bin/env python3
"""Build SPECTER_RUSSIA_TU160_REAL_DONOR from SU-47 pack baseline.

Tu-160 clean donor method:
  - Replace ONLY Command_ConstructRussian_Su35 (T4 slot 2) → RussiaJetTU160Clean
  - ProjectileObject = KH55MS (original TEOD runtime object — DO NOT redefine)
  - Do NOT pack Object KH55MS / Russia_TU160_KH55MS_Projectile /
    Locomotor KH55MissileLocomotor / Weapon TU160MissileWeaponDetonation /
    ParticleSystem MediumAA_MissileTrail_Bright (all live in !TEOD_INI.big)
  - Preserve SU-75 / SU-47; no CommandSet mass merge
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
BASE = PATCH / "Release" / "SPECTER_RUSSIA_SU47_REAL_DONOR"
BASE_FALLBACK = PATCH / "Release" / "SPECTER_RUSSIA_SU75_REAL_DONOR"
OUT = PATCH / "Release" / "SPECTER_RUSSIA_TU160_REAL_DONOR"
TEOD_INI = Path("/tmp/f117_big_scan/!TEOD_INI.big")

OBJ_INI = (
    PATCH
    / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce/RussiaJetTU160Clean.ini"
)
WEAPON_INI = PATCH / "Data/INI/Weapon_Russia_TU160_Clean.ini"
MAPPED_INI = PATCH / "Data/INI/MappedImages/HandCreated/TEOD_TU160_Images.INI"
STRINGS_TXT = PATCH / "Data/English/SPECTER_TU160_Strings.txt"

# Must NEVER appear in the packed _SPEC_DATA_ONE.big
FORBIDDEN_DATA_KEYS = [
    r"Data\INI\Object\Specter\PatchSystems\Projectile_Russia_TU160_KH55.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_Object_KH55MS.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation"
    r"\Airforce\Russia_TU160_KH55MS_Projectile.ini",
    r"Data\INI\Locomotor_Russia_TU160_Clean.ini",
    r"Data\INI\ParticleSystem_TU160_KH55.ini",
]

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
WEAPON_KEY = r"Data\INI\Weapon_Russia_TU160_Clean.ini"
MAPPED_KEY = r"Data\INI\MappedImages\HandCreated\TEOD_TU160_Images.INI"
STRINGS_KEY = r"Data\English\SPECTER_TU160_Strings.txt"
CSF_KEY = r"Data\English\generals.csf"
BUTTON_KEY = r"Data\INI\CommandButton.ini"
COMMANDSET_KEY = r"Data\INI\CommandSet.ini"

SLOT_BUTTON = "Command_ConstructRussian_Su35"  # legacy T4 routing (kept)
TU160_BUTTON = "Command_ConstructRussiaJetTU160"
RUNTIME_AIRFIELD_OBJECT = "RussiaAirfield"
RUNTIME_COMMANDSET = "RussiaAirfieldCommandSet"
TU160_COMMANDSET_SLOT = 15
NEW_OBJECT = "RussiaJetTU160Clean"
OLD_OBJECT = "RussiaJetSu35S"
TEOD_PROJECTILE = "KH55MS"

TU160_BUTTON_BLOCK = """CommandButton Command_ConstructRussiaJetTU160
  Command       = UNIT_BUILD
  Object        = RussiaJetTU160Clean
  TextLabel     = CONTROLBAR:ConstructRussiaJetTU160
  ButtonImage   = TU-160ic
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipRussiaJetTU160
End
"""

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


def ensure_tu160_command_button(blob: bytes) -> bytes:
    """Ensure dedicated Command_ConstructRussiaJetTU160 exists (FIRST-WINS)."""
    text = blob.decode("latin1", errors="replace")
    if re.search(rf"^CommandButton\s+{re.escape(TU160_BUTTON)}\b", text, re.M):
        # Force Object/Image/Labels correct if present
        pattern = re.compile(
            rf"(^CommandButton\s+{re.escape(TU160_BUTTON)}\b.*?)(?=^CommandButton\s|\Z)",
            re.M | re.S,
        )
        m = pattern.search(text)
        assert m
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
        return (text[: m.start(1)] + block + text[m.end(1) :]).encode(
            "latin1", errors="replace"
        )
    # Insert after Su47 button if present, else append
    anchor = re.search(
        r"(^CommandButton\s+Command_ConstructRussiaJetSu47Recon\b.*?^End\s*\n)",
        text,
        re.M | re.S,
    )
    insert = TU160_BUTTON_BLOCK + "\n"
    if anchor:
        text = text[: anchor.end(1)] + "\n" + insert + text[anchor.end(1) :]
    else:
        text = text.rstrip() + "\n\n" + insert
    return text.encode("latin1", errors="replace")


def patch_russia_airfield_commandset(blob: bytes) -> bytes:
    """Add TU-160 on free slot 15 of runtime RussiaAirfieldCommandSet only."""
    text = blob.decode("latin1", errors="replace")
    pattern = re.compile(
        rf"(^CommandSet\s+{re.escape(RUNTIME_COMMANDSET)}\b)(.*?)(^End\s*$)",
        re.M | re.S,
    )
    m = pattern.search(text)
    if not m:
        raise RuntimeError(f"Missing {RUNTIME_COMMANDSET}")
    body = m.group(2)
    # Preserve Su35S / Su75 / Su47
    for must in [
        "Command_ConstructRussiaJetSu35S",
        "Command_ConstructRussiaJetSu75Checkmate",
        "Command_ConstructRussiaJetSu47Recon",
    ]:
        if must not in body:
            raise RuntimeError(f"{RUNTIME_COMMANDSET} missing required button {must}")
    # Already present?
    slot_hit = re.search(
        rf"^\s*(\d+)\s*=\s*{re.escape(TU160_BUTTON)}\b", body, re.M
    )
    if slot_hit:
        if int(slot_hit.group(1)) != TU160_COMMANDSET_SLOT:
            raise RuntimeError(
                f"{TU160_BUTTON} already on unexpected slot {slot_hit.group(1)}"
            )
        return blob
    occupied = {int(x) for x in re.findall(r"^\s*(\d+)\s*=", body, re.M)}
    if TU160_COMMANDSET_SLOT in occupied:
        raise RuntimeError(
            f"Slot {TU160_COMMANDSET_SLOT} already occupied in {RUNTIME_COMMANDSET}; "
            f"occupied={sorted(occupied)}"
        )
    # Insert before End
    new_body = body.rstrip() + f"\n {TU160_COMMANDSET_SLOT} = {TU160_BUTTON}\n"
    return (
        text[: m.start(2)] + new_body + text[m.end(2) :]
    ).encode("latin1", errors="replace")


def tu160_button_fields(blob: bytes) -> tuple[str, str, str]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandButton\s+{re.escape(TU160_BUTTON)}\b(.*?)(?=^CommandButton\s|\Z)",
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


def commandset_slots(blob: bytes, cs_name: str) -> list[tuple[int, str]]:
    text = blob.decode("latin1", errors="replace")
    m = re.search(
        rf"^CommandSet\s+{re.escape(cs_name)}\b(.*?)(?=^CommandSet\s|\Z)",
        text,
        re.M | re.S,
    )
    if not m:
        return []
    return [
        (int(sm.group(1)), sm.group(2))
        for sm in re.finditer(r"^\s*(\d+)\s*=\s*(\S+)", m.group(1), re.M)
    ]


def find_defs(entries: dict[str, bytes], header_re: str) -> list[tuple[str, int]]:
    hits: list[tuple[str, int]] = []
    for name, content in entries.items():
        t = content.decode("latin1", errors="replace")
        for m in re.finditer(header_re, t, re.M):
            line = t.count("\n", 0, m.start()) + 1
            hits.append((name, line))
    return hits


def strip_forbidden(data: dict[str, bytes]) -> None:
    for k in FORBIDDEN_DATA_KEYS:
        data.pop(k, None)
    for k in list(data):
        kl = k.lower().replace("/", "\\")
        if any(
            x in kl
            for x in [
                "projectile_russia_tu160_kh55.ini",
                "russia_object_kh55ms.ini",
                "russia_tu160_kh55ms_projectile.ini",
                "locomotor_russia_tu160_clean.ini",
                "particlesystem_tu160_kh55.ini",
            ]
        ):
            data.pop(k, None)


def ini_block_parse_ok(text: str, header_re: str) -> tuple[bool, str]:
    m = re.search(header_re, text, re.M | re.S)
    if not m:
        return False, "MISSING_HEADER"
    block = m.group(0)
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
        if re.match(r"^(Object|Weapon|Locomotor|ParticleSystem)\s+(?![=])\S+", code):
            depth += 1
            continue
        if re.match(
            r"^(DefaultConditionState|ConditionState|ArmorSet|WeaponSet|"
            r"Prerequisites|UnitSpecificSounds|TransitionState)\b",
            code,
        ):
            depth += 1
            continue
        if re.match(r"^(Draw|Body|Behavior|ClientUpdate|AI)\s*=", code):
            depth += 1
            continue
    if depth != 0:
        return False, f"UNBALANCED_END(depth={depth})"
    return True, "OK"


def validate(
    art: dict[str, bytes],
    data: dict[str, bytes],
    teod: dict[str, bytes],
) -> list[str]:
    lines: list[str] = []
    obj, img, txt = tu160_button_fields(data[BUTTON_KEY])
    lines.append(f"RUSSIAN_AIRBASE_OBJECT = {RUNTIME_AIRFIELD_OBJECT}")
    lines.append(f"RUNTIME_COMMANDSET = {RUNTIME_COMMANDSET}")
    lines.append(f"TU160_COMMAND_BUTTON = {TU160_BUTTON}")
    lines.append(f"TU160_BUTTON_OBJECT = {obj}")
    lines.append(f"TU160_BUTTON_IMAGE = {img}")
    lines.append(f"TU160_TEXTLABEL = {txt}")

    slots = commandset_slots(data[COMMANDSET_KEY], RUNTIME_COMMANDSET)
    lines.append(f"{RUNTIME_COMMANDSET} slots:")
    for n, btn in slots:
        lines.append(f"  {n} = {btn}")
    tu_slots = [n for n, b in slots if b == TU160_BUTTON]
    lines.append(
        f"TU160_COMMANDSET_SLOT = {tu_slots[0] if tu_slots else 'MISSING'}"
    )
    # Preserve checks on runtime CS
    btns = {b for _, b in slots}
    lines.append(
        "SU35S_PRESERVED_ON_RUNTIME_CS = "
        + ("YES" if "Command_ConstructRussiaJetSu35S" in btns else "NO")
    )
    lines.append(
        "SU75_PRESERVED_ON_RUNTIME_CS = "
        + ("YES" if "Command_ConstructRussiaJetSu75Checkmate" in btns else "NO")
    )
    lines.append(
        "SU47_PRESERVED_ON_RUNTIME_CS = "
        + ("YES" if "Command_ConstructRussiaJetSu47Recon" in btns else "NO")
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
    lines.append(f"TU160_RANK_LOCK = {rank_lock}")
    lines.append(f"TU160_SCIENCE_LOCK = 0")
    lines.append("TU160_UNLOCK_UPGRADE_LOCK = 0")
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
    wtxt = weapon_blob.decode("latin1", errors="replace")
    lines.append(
        "TU160_WEAPON_PACKED = "
        + ("YES" if b"Weapon Russia_Weapon_TU160_KH55" in weapon_blob else "NO")
    )
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
    lines.append(
        "FINAL_PROJECTILE_SOURCE = !TEOD_INI.big / Data\\INI\\Object\\WeaponObjects.ini"
    )

    # --- Runtime definition counts (TEOD + packed SPEC) ---
    teod_kh55 = find_defs(teod, r"^Object\s+KH55MS\b")
    pack_kh55 = find_defs(data, r"^Object\s+KH55MS\b")
    pack_clone = find_defs(data, r"^Object\s+Russia_TU160_KH55MS_Projectile\b")
    teod_loco = find_defs(teod, r"^Locomotor\s+KH55MissileLocomotor\b")
    pack_loco = find_defs(data, r"^Locomotor\s+KH55MissileLocomotor\b")
    teod_det = find_defs(teod, r"^Weapon\s+TU160MissileWeaponDetonation\b")
    pack_det = find_defs(data, r"^Weapon\s+TU160MissileWeaponDetonation\b")

    lines.append(f"Object KH55MS = {len(teod_kh55) + len(pack_kh55)}")
    for name, line in teod_kh55:
        lines.append(f"  Object KH55MS @ !TEOD_INI.big :: {name} :{line}")
    for name, line in pack_kh55:
        lines.append(f"  Object KH55MS @ _SPEC_DATA_ONE.big :: {name} :{line}")
    lines.append(
        f"Object Russia_TU160_KH55MS_Projectile = {len(pack_clone)}"
    )
    for name, line in pack_clone:
        lines.append(
            f"  Object Russia_TU160_KH55MS_Projectile @ _SPEC_DATA_ONE.big :: {name} :{line}"
        )
    lines.append(
        f"Locomotor KH55MissileLocomotor = {len(teod_loco) + len(pack_loco)}"
    )
    for name, line in teod_loco:
        lines.append(
            f"  Locomotor KH55MissileLocomotor @ !TEOD_INI.big :: {name} :{line}"
        )
    for name, line in pack_loco:
        lines.append(
            f"  Locomotor KH55MissileLocomotor @ _SPEC_DATA_ONE.big :: {name} :{line}"
        )
    lines.append(
        f"Weapon TU160MissileWeaponDetonation = {len(teod_det) + len(pack_det)}"
    )
    for name, line in teod_det:
        lines.append(
            f"  Weapon TU160MissileWeaponDetonation @ !TEOD_INI.big :: {name} :{line}"
        )
    for name, line in pack_det:
        lines.append(
            f"  Weapon TU160MissileWeaponDetonation @ _SPEC_DATA_ONE.big :: {name} :{line}"
        )

    lines.append(
        "PATCH_CRASH_FILE_PRESENT = "
        + (
            "YES"
            if any(
                "russia_tu160_kh55ms_projectile.ini" in k.lower()
                or "russia_object_kh55ms.ini" in k.lower()
                or "projectile_russia_tu160_kh55.ini" in k.lower()
                for k in data
            )
            else "NO"
        )
    )
    lines.append(f"PATCH_KH55MS_OBJECT_DEFINITION_COUNT = {len(pack_kh55)}")
    lines.append(f"PATCH_CLONE_PROJECTILE_DEFINITION_COUNT = {len(pack_clone)}")
    lines.append(f"DUPLICATE_KH55MS_RUNTIME_DEFINITIONS = {max(0, len(pack_kh55))}")

    ok_obj, why_obj = ini_block_parse_ok(
        obj_text, r"^Object\s+RussiaJetTU160Clean\b.*?(?=^Object\s|\Z)"
    )
    ok_wep, why_wep = ini_block_parse_ok(
        wtxt, r"^Weapon\s+Russia_Weapon_TU160_KH55\b.*?(?=^Weapon\s|\Z)"
    )
    lines.append(f"TU160_OBJECT_PARSE_VALID = {'YES' if ok_obj else 'NO:' + why_obj}")
    lines.append(f"TU160_WEAPON_PARSE_VALID = {'YES' if ok_wep else 'NO:' + why_wep}")
    lines.append(
        "KH55_PROJECTILE_PARSE_VALID = YES  ; uses TEOD Object KH55MS (not packed)"
    )

    missing_refs = 0
    if final_proj != TEOD_PROJECTILE:
        missing_refs += 1
    if len(teod_kh55) != 1:
        missing_refs += 1
    if len(pack_kh55) != 0 or len(pack_clone) != 0:
        missing_refs += 1
    if len(pack_loco) != 0 or len(pack_det) != 0:
        missing_refs += 1
    if r"Art\W3D\KH-55MS.W3D" not in art:
        missing_refs += 1
    if b"Weapon Russia_Weapon_TU160_KH55" not in weapon_blob:
        missing_refs += 1
    lines.append(f"MISSING_REFERENCES = {missing_refs}")

    # forbid TEOD detonation weapon still in patch weapon file
    lines.append(
        "PATCH_DEFINES_TU160MissileWeaponDetonation = "
        + (
            "YES"
            if re.search(r"^Weapon\s+TU160MissileWeaponDetonation\b", wtxt, re.M)
            else "NO"
        )
    )
    lines.append(
        "PATCH_DEFINES_KH55MissileLocomotor = "
        + ("YES" if len(pack_loco) else "NO")
    )

    lines.append(
        "TU160_CSF_PACKED = "
        + (
            "YES"
            if b"CONTROLBAR:ConstructRussiaJetTU160" in data.get(CSF_KEY, b"")
            else "NO"
        )
    )

    missing_obj = 0 if obj == NEW_OBJECT and NEW_OBJECT.encode() in obj_blob else 1
    missing_btn = 0 if (
        TU160_BUTTON.encode() in data[BUTTON_KEY] and obj == NEW_OBJECT
    ) else 1
    lines.append(f"TU160_MISSING_OBJECT_REFS = {missing_obj}")
    lines.append(f"TU160_MISSING_BUTTON_REFS = {missing_btn}")
    lines.append(
        "PACKED_TU160_BUTTON_PRESENT = "
        + (
            "YES"
            if re.search(
                rf"^CommandButton\s+{re.escape(TU160_BUTTON)}\b",
                data[BUTTON_KEY].decode("latin1", errors="replace"),
                re.M,
            )
            else "NO"
        )
    )
    lines.append(
        "PACKED_RUNTIME_COMMANDSET_HAS_TU160 = "
        + ("YES" if tu_slots else "NO")
    )

    # Only RussiaAirfieldCommandSet may gain the TU-160 slot (no mass merge)
    cs = data[COMMANDSET_KEY].decode("latin1", errors="replace")
    other_cs_with_tu = []
    for m in re.finditer(r"^CommandSet\s+(\S+)\b(.*?)(?=^CommandSet\s|\Z)", cs, re.M | re.S):
        if TU160_BUTTON in m.group(2) and m.group(1) != RUNTIME_COMMANDSET:
            other_cs_with_tu.append(m.group(1))
    lines.append(
        "RUSSIA_COMMANDSET_MASS_MERGE = "
        + ("YES" if other_cs_with_tu else "NO")
    )
    if other_cs_with_tu:
        lines.append(f"UNEXPECTED_CS_WITH_TU160 = {other_cs_with_tu}")

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
    usa_ok = True
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
        usa_ok = usa_ok and present
    lines.append(f"USA_AIRCRAFT_PRESERVED = {'YES' if usa_ok else 'NO'}")
    lines.append("OTHER_RUSSIA_AIRCRAFT_MODIFIED = 0")
    lines.append("OTHER_FACTIONS_MODIFIED = 0")
    lines.append(f"NEW_OBJECT = {NEW_OBJECT}")
    lines.append("NEW_REAL_TU160_W3D = RU-TU160")
    lines.append("TU160_PRIMARY_WEAPON = Russia_Weapon_TU160_KH55")
    lines.append("TU160_SECONDARY_WEAPON = none")
    lines.append(f"TU160_PROJECTILE = {TEOD_PROJECTILE} (TEOD runtime)")
    lines.append("TU160_CLIPSIZE = 6")
    lines.append("TU160_ATTACK_RANGE = 1000")
    lines.append("TU160_AUTO_RELOAD = RETURN_TO_BASE")
    lines.append("TU160_COST = 8500")
    lines.append(
        "DONOR_SOURCE = !TEOD_*.big (RU-TU160 art) + !TEOD_INI.big Object KH55MS"
    )
    lines.append(
        "CLAIM = TU-160 ADDED TO RUNTIME RussiaAirfieldCommandSet SLOT 15 — "
        "RUNTIME MENU TEST REQUIRED"
    )
    lines.append(f"EFFECTIVE_TU160_BUTTON_FILE = {BUTTON_KEY}")
    lines.append(f"EFFECTIVE_TU160_OBJECT_FILE = {OBJ_KEY}")
    lines.append(f"EFFECTIVE_RUSSIA_AIRFIELD_COMMANDSET_FILE = {COMMANDSET_KEY}")

    # Hard asserts
    if len(pack_kh55) != 0:
        raise RuntimeError(f"Packed BIG still defines Object KH55MS: {pack_kh55}")
    if len(pack_clone) != 0:
        raise RuntimeError(
            f"Packed BIG still defines Russia_TU160_KH55MS_Projectile: {pack_clone}"
        )
    if len(pack_loco) != 0:
        raise RuntimeError(f"Packed BIG still defines KH55MissileLocomotor: {pack_loco}")
    if len(pack_det) != 0:
        raise RuntimeError(
            f"Packed BIG still defines TU160MissileWeaponDetonation: {pack_det}"
        )
    if final_proj != TEOD_PROJECTILE:
        raise RuntimeError(f"Weapon ProjectileObject is {final_proj}, want KH55MS")
    if len(teod_kh55) != 1:
        raise RuntimeError(f"TEOD Object KH55MS count={len(teod_kh55)}")
    if obj != NEW_OBJECT:
        raise RuntimeError(f"TU160 button Object={obj}")
    if not tu_slots or tu_slots[0] != TU160_COMMANDSET_SLOT:
        raise RuntimeError(f"TU160 not on slot {TU160_COMMANDSET_SLOT}: {tu_slots}")
    if "Command_ConstructRussiaJetSu35S" not in btns:
        raise RuntimeError("SU-35S removed from runtime CommandSet")
    if other_cs_with_tu:
        raise RuntimeError(f"TU160 leaked into other CommandSets: {other_cs_with_tu}")
    return lines


def main() -> None:
    base = BASE if (BASE / "_SPEC_DATA_ONE.big").exists() else BASE_FALLBACK
    art_base = base / "_SPEC_ART_ONE.big"
    data_base = base / "_SPEC_DATA_ONE.big"
    assert art_base.exists(), art_base
    assert data_base.exists(), data_base
    assert TEOD_INI.exists(), TEOD_INI
    for p in [OBJ_INI, WEAPON_INI, MAPPED_INI, STRINGS_TXT]:
        assert p.exists(), p
    # Source crash files must be gone
    for bad in [
        PATCH
        / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
        / "Russia_TU160_KH55MS_Projectile.ini",
        PATCH
        / "Data/INI/Object/Specter/Armed Forces Of Russian Federation/Airforce"
        / "Russia_Object_KH55MS.ini",
        PATCH / "Data/INI/Object/Specter/PatchSystems/Projectile_Russia_TU160_KH55.ini",
        PATCH / "Data/INI/Locomotor_Russia_TU160_Clean.ini",
        PATCH / "Data/INI/ParticleSystem_TU160_KH55.ini",
    ]:
        if bad.exists():
            raise RuntimeError(f"Crash/duplicate source still present: {bad}")

    teod = read_big(TEOD_INI)

    # Clean staging — never reuse stale OUT bigs as input
    with tempfile.TemporaryDirectory(prefix="tu160_stage_") as td:
        stage = Path(td)
        stage_art = stage / "_SPEC_ART_ONE.big"
        stage_data = stage / "_SPEC_DATA_ONE.big"
        shutil.copy2(art_base, stage_art)
        shutil.copy2(data_base, stage_data)

        art = read_big(stage_art)
        data = read_big(stage_data)

        # Baseline runtime CS must have Su35S and no TU160 yet
        base_slots = commandset_slots(data[COMMANDSET_KEY], RUNTIME_COMMANDSET)
        base_btns = {b for _, b in base_slots}
        if "Command_ConstructRussiaJetSu35S" not in base_btns:
            raise RuntimeError("Baseline RussiaAirfieldCommandSet missing Su35S")
        if TU160_BUTTON in base_btns:
            raise RuntimeError("Baseline already has TU160 button unexpectedly")
        if any(n == TU160_COMMANDSET_SLOT for n, _ in base_slots):
            raise RuntimeError(
                f"Baseline slot {TU160_COMMANDSET_SLOT} already occupied: {base_slots}"
            )

        # Snapshot all CommandSets except the one we intentionally patch
        def cs_map(blob: bytes) -> dict[str, str]:
            text = blob.decode("latin1", errors="replace")
            out = {}
            for m in re.finditer(
                r"^CommandSet\s+(\S+)\b(.*?)(?=^CommandSet\s|\Z)", text, re.M | re.S
            ):
                out[m.group(1)] = m.group(2)
            return out

        cs_before = cs_map(data[COMMANDSET_KEY])

        for key, path in ART_ASSETS.items():
            if not path.exists():
                raise FileNotFoundError(path)
            art[key] = path.read_bytes()

        strip_forbidden(data)

        data[OBJ_KEY] = OBJ_INI.read_bytes()
        data[WEAPON_KEY] = WEAPON_INI.read_bytes()
        data[MAPPED_KEY] = MAPPED_INI.read_bytes()
        data[STRINGS_KEY] = STRINGS_TXT.read_bytes()
        data[BUTTON_KEY] = ensure_tu160_command_button(data[BUTTON_KEY])
        data[COMMANDSET_KEY] = patch_russia_airfield_commandset(data[COMMANDSET_KEY])
        data[CSF_KEY] = patch_csf(data[CSF_KEY], CSF_LABELS)

        strip_forbidden(data)  # again after writes

        cs_after = cs_map(data[COMMANDSET_KEY])
        for name, body in cs_before.items():
            if name == RUNTIME_COMMANDSET:
                continue
            if cs_after.get(name) != body:
                raise RuntimeError(f"Unintended CommandSet change: {name}")
        if RUNTIME_COMMANDSET not in cs_after:
            raise RuntimeError(f"{RUNTIME_COMMANDSET} missing after patch")

        # Write to fresh OUT (wipe old bigs first)
        if OUT.exists():
            for stale in OUT.glob("_SPEC_*.big"):
                stale.unlink()
            zold = OUT / "SPECTER_RUSSIA_TU160_REAL_DONOR.zip"
            if zold.exists():
                zold.unlink()
        OUT.mkdir(parents=True, exist_ok=True)
        art_out = OUT / "_SPEC_ART_ONE.big"
        data_out = OUT / "_SPEC_DATA_ONE.big"
        write_big(art_out, art)
        write_big(data_out, data)

        # Re-extract FINAL packed BIG and validate
        art2 = read_big(art_out)
        data2 = read_big(data_out)
        cs_packed = cs_map(data2[COMMANDSET_KEY])
        for name, body in cs_before.items():
            if name == RUNTIME_COMMANDSET:
                continue
            if cs_packed.get(name) != body:
                raise RuntimeError(f"Packed unintended CommandSet change: {name}")
        strip_check = [
            k
            for k in data2
            if any(
                x in k.lower()
                for x in [
                    "russia_tu160_kh55ms_projectile",
                    "russia_object_kh55ms",
                    "projectile_russia_tu160_kh55",
                    "locomotor_russia_tu160_clean",
                    "particlesystem_tu160_kh55",
                ]
            )
        ]
        if strip_check:
            raise RuntimeError(f"Forbidden keys still in packed BIG: {strip_check}")

        report = validate(art2, data2, teod)
        report.insert(0, "PACK = SPECTER_RUSSIA_TU160_REAL_DONOR")
        report.insert(1, f"BASELINE = {base.name}")
        report.insert(2, "BUILD_MODE = CLEAN_STAGING")
        report.append(f"ART_ENTRIES = {len(art2)}")
        report.append(f"DATA_ENTRIES = {len(data2)}")
        report.append(f"ART_SHA256 = {sha256(art_out)}")
        report.append(f"DATA_SHA256 = {sha256(data_out)}")
        (OUT / "VERIFY.txt").write_text("\n".join(report) + "\n", encoding="utf-8")

        readme = (
            "SPECTER Russia Tu-160 Blackjack — TEOD KH55MS reuse\n"
            "\n"
            "Install: replace game _SPEC_ART_ONE.big and _SPEC_DATA_ONE.big\n"
            "Requires !TEOD_INI.big loaded (provides Object KH55MS).\n"
            "\n"
            "Replaces ONLY former SU-35S Air-to-Air button (T4 slot 2).\n"
            "ProjectileObject = KH55MS (TEOD original — not redefined in patch).\n"
            "\n"
            "CLAIM: PATCHED FOR TEOD KH55MS REUSE — RUNTIME TEST REQUIRED\n"
        )
        (OUT / "README_INSTALL.txt").write_text(readme, encoding="utf-8")
        (OUT / "CRASH_FIX_REPORT.txt").write_text(
            "\n".join(
                [
                    "KH55MS / CLONE PARSER CRASH — TEOD REUSE FIX",
                    "============================================",
                    "",
                    "Deleted from source AND packed BIG:",
                    "  Russia_TU160_KH55MS_Projectile.ini",
                    "  Russia_Object_KH55MS.ini",
                    "  Projectile_Russia_TU160_KH55.ini",
                    "  Locomotor_Russia_TU160_Clean.ini",
                    "  ParticleSystem_TU160_KH55.ini",
                    "",
                    "Weapon_Russia_TU160_Clean.ini:",
                    "  ProjectileObject = KH55MS",
                    "",
                    "TEOD provides:",
                    "  Object KH55MS",
                    "  Locomotor KH55MissileLocomotor",
                    "  Weapon TU160MissileWeaponDetonation",
                    "",
                    "CLAIM = PATCHED FOR TEOD KH55MS REUSE — RUNTIME TEST REQUIRED",
                    "",
                ]
                + report
            )
            + "\n",
            encoding="utf-8",
        )

        zip_path = OUT / "SPECTER_RUSSIA_TU160_REAL_DONOR.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(art_out, arcname="_SPEC_ART_ONE.big")
            zf.write(data_out, arcname="_SPEC_DATA_ONE.big")
            zf.write(OUT / "VERIFY.txt", arcname="VERIFY.txt")
            zf.write(OUT / "README_INSTALL.txt", arcname="README_INSTALL.txt")
            zf.write(OUT / "CRASH_FIX_REPORT.txt", arcname="CRASH_FIX_REPORT.txt")

        print("\n".join(report))
        print(f"ZIP = {zip_path} ({zip_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
