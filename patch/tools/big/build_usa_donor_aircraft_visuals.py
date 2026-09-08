#!/usr/bin/env python3
"""Apply exact New-Donor USA aircraft visuals discovered in the audit pass.

ART from New Donor only. DATA is cloned/adapted Specter objects (no donor
Weapon/Armor/Locomotor/Science/PlayerTemplate copy).

Does not touch National Ground Forces, War Factory, CommandCenter, VT72B,
PlayerTemplate, or Science.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/national_ground_runtime/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/national_ground_runtime/_SPEC_ART_ONE.big")
DONOR = Path("/tmp/new_donor_extract/New folder")
OUT_DIR = Path("/tmp/usa_donor_aircraft_visuals")

LOCKED_PATHS = {
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
}

# Overlay CommandSets must never be added; live bars live in CommandSet.ini.
DO_NOT_PACK_OVERLAY = {
    r"data\ini\commandset_japan.ini",
    r"data\ini\commandset_southkorea.ini",
    r"data\ini\commandset_vietnam.ini",
}

F35B_OBJECTS = {
    "AmericaJetF35BJSF",
    "BritainJetF35B",
    "ItalyJetF35B",
    "JapanJetF35B",
    "NatoJetF35B",
    "SouthKoreaJetF35B",
}

# Dedicated F-35A objects plus NATO/clone F35C files that actually use US_F35A.
F35A_OBJECTS = {
    "JapanJetF35A",
    "SouthKoreaJetF35A",
    "GermanyJetF35A",
    "ItalyJetF35A",
    "TurkeyJetF35A",
    "JapanJetF35Japon",
    "BritainJetF35C",
    "FranceJetF35C",
    "GermanyJetF35C",
    "ItalyJetF35C",
    "NatoJetF35C",
    "SwedenJetF35C",
    "TurkeyJetF35C",
    "UkraineJetF35C",
    "BritainJetF35C_AA",
    "FranceJetF35C_AA",
    "GermanyJetF35C_AA",
    "ItalyJetF35C_AA",
    "NatoJetF35C_AA",
    "SwedenJetF35C_AA",
    "TurkeyJetF35C_AA",
    "UkraineJetF35C_AA",
    "IsraelJetF35IAdirPenetrator",
    "IsraelJetF35I_AA",
    "AirF_AmericaJetStealthFighter",
}

GROWLER_OBJECTS = {
    "AmericaJetEA18G",
    "AmericaJetEA18G_AI",
    "BritainJetEA18G",
    "FranceJetEA18G",
    "GermanyJetEA18G",
    "ItalyJetEA18G",
    "NatoJetEA18G",
    "SwedenJetEA18G",
    "TurkeyJetEA18G",
    "UkraineJetEA18G",
    "JapanJetF18G",
}

PROWLER_OBJECTS = {
    "JapanJetEA6B",
    "AmericaJetF18Prowler",
}

DONOR_ART = {
    "00PMBeta993.big": [
        r"Art\w3d\AVLightn.W3D",
        r"Art\w3d\AVLightn_D.W3D",
        r"Art\w3d\AVLightn_A1.W3D",
        r"Art\Textures\AVLightn.dds",
        r"Art\Textures\AVLightn_D.dds",
        r"Art\Textures\AVPatron.dds",
        r"Art\Textures\aim7.dds",
        r"Art\Textures\avjetafterburner.dds",
        r"Art\Textures\avjetafterburner2.dds",
        r"Art\Textures\abpatemp_m.dds",
        r"Art\w3d\EA6.W3D",
        r"Art\Textures\EA6.tga",
        r"Art\Textures\AmericaF35BJSF.tga",
        r"Art\Textures\AmericaF35BJSFTB.tga",
        r"Art\Textures\USAEA6Prowler.tga",
        r"Art\Textures\USAEA6ProwlerTB.tga",
        # EA6.W3D samples these texture names; F18SEA.W3D itself is NOT imported.
        r"Art\Textures\F18SEA_1.tga",
        r"Art\Textures\A6_3.tga",
    ],
    "00PMBeta999.big": [
        r"Art\w3d\LSFUSAF35A.W3D",
        r"Art\w3d\LSFUSAF35Ad.W3D",
        r"Art\w3d\LSFUSAF35Ak.W3D",
        r"Art\Textures\f35.dds",
        r"Art\Textures\f35d.dds",
        r"Art\Textures\f35k.dds",
        r"Art\Textures\F35tb.tga",
        r"Art\w3d\LSFEA18G.W3D",
        r"Art\w3d\LSFEA18Gd.W3D",
        r"Art\w3d\LSFEA18Gk.W3D",
        r"Art\Textures\LSFEA18G.dds",
        r"Art\Textures\LSFEA18Gd.dds",
        r"Art\Textures\LSFEA18Gk.dds",
        r"Art\Textures\EA18GTB.tga",
        r"Art\Textures\UsaAirMissileMap.dds",
        r"Art\Textures\housecolor2.dds",
    ],
}

# Rejected donor identities (documented, never packed as aircraft bodies):
#   Variant B Growler: USAautreF18G / EA18G.W3D / UsaEA18Map.dds / USAF18G.tga
#   Hornet meshes: AmF18A.W3D / F18SEA.W3D
#   AVF-35.W3D as the F-35B body
#   chj10_r.W3D (unrelated donor mesh)
#   usa_helipilot.dds (not sampled by the requested W3Ds)

EA6B_WEAPON = """Weapon Specter_Weapon_EA6B_GuidedBomb
  PrimaryDamage = 1100.0
  PrimaryDamageRadius = 48.0
  SecondaryDamage = 90.0
  SecondaryDamageRadius = 80.0
  ScatterRadius = 14.0
  AttackRange = 920.0
  MinimumAttackRange = 90.0
  PreAttackDelay = 2800
  PreAttackType = PER_ATTACK
  AcceptableAimDelta = 20
  DamageType = ARMOR_PIERCING
  DeathType = EXPLODED
  WeaponSpeed = 9999
  ProjectileObject = GBU24_GuidedBombObject
  FireFX = FX_AuroraBombLaunch
  ProjectileDetonationFX = FX_FreeFallBombsDetonation
  RadiusDamageAffects = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots = 2200
  ClipSize = 6
  ClipReloadTime = 28000
  AutoReloadsClip = RETURN_TO_BASE
  ShowsAmmoPips = Yes
  ProjectileCollidesWith = STRUCTURES
  AntiGround = Yes
  AntiAirborneVehicle = No
  LeechRangeWeapon = Yes
End
"""

GROWLER_WEAPONS = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY ALQ_99_RadarJamming
    PreferredAgainst = PRIMARY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AGM88G_AARGM-ER
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY AIM9X_HOBS_SRAAM_F35C
    PreferredAgainst = TERTIARY AIRCRAFT
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
"""

CSF_LABELS = {
    "CONTROLBAR:F18G": "F/A-18G Growler",
    "CONTROLBAR:F18Gif": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "CONTROLBAR:autreF18G": "F/A-18G Growler",
    "CONTROLBAR:autreF18Gif": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "CONTROLBAR:EA18G": "EA-18G Growler",
    "CONTROLBAR:EA18Gif": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "CONTROLBAR:EA6Prowler": "EA-6B Prowler",
    "CONTROLBAR:EA6Prowleri": "Heavy precision strike. Six guided bombs.",
    "CONTROLBAR:EA6Prowlerif": "Heavy precision strike. Six guided bombs.",
    "CONTROLBAR:F35BJSF": "F-35B JSF",
    "CONTROLBAR:F35BJSFif": "Air-to-air F-35B. AIM-120 and AIM-9X.",
    "CONTROLBAR:AmericaF35BJSF": "F-35B JSF",
    "CONTROLBAR:AmericaF35BJSFif": "Air-to-air F-35B. AIM-120 and AIM-9X.",
    "CONTROLBAR:ConstructAmericaJetF18Prowler": "EA-6B Prowler",
    "CONTROLBAR:ToolTipAmericaJetF18Prowler": "Heavy precision strike. Six guided bombs.",
    "CONTROLBAR:ConstructAmericaJetEA18G": "EA-18G Growler",
    "CONTROLBAR:ToolTipAmericaJetEA18G": "Electronic warfare Growler. ALQ-99 jamming, AGM-88, AIM-9X.",
    "OBJECT:AmericaJetF18Prowler": "EA-6B Prowler",
    "OBJECT:EA18G": "EA-18G Growler",
    "OBJECT:AmericaJetF35BJSF": "F-35B JSF",
    "OBJECT:JapanJetEA6B": "EA-6B Prowler",
    "OBJECT:JapanJetF18G": "EA-18G Growler",
    "CONTROLBAR:ConstructNatoJetF35B": "F-35B JSF",
    "CONTROLBAR:ToolTipNatoJetF35B": "Air-to-air F-35B. AIM-120 and AIM-9X.",
    "CONTROLBAR:ConstructTurkeyJetF35A": "F-35A Lightning II",
    "CONTROLBAR:ToolTipTurkeyJetF35A": "Turkish F-35A. Air-to-air missiles and strike weapons.",
}


def parse_big(path: Path):
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise ValueError(f"Not BIGF: {path}")
    nfiles = struct.unpack(">I", data[8:12])[0]
    off = 16
    entries = []
    for _ in range(nfiles):
        eoff, esz = struct.unpack_from(">II", data, off)
        off += 8
        end = data.index(b"\x00", off)
        name = data[off:end].decode("latin1")
        off = end + 1
        entries.append((name, data[eoff : eoff + esz]))
    return entries


def build_big_ordered(entries):
    header_size = 16
    encoded = [(n.encode("latin1"), b) for n, b in entries]
    for nb, _blob in encoded:
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for nb, blob in encoded:
        index.append((nb, offset, len(blob)))
        blobs.append(blob)
        offset += len(blob)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(encoded))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def decode(blob: bytes) -> str:
    if blob[:2] == b"\xff\xfe":
        return blob.decode("utf-16-le")
    return blob.decode("latin1")


def encode(text: str, orig: bytes) -> bytes:
    if orig[:2] == b"\xff\xfe":
        return orig[:2] + text.encode("utf-16-le")
    return text.encode("latin1")


def split_objects(text: str):
    parts = re.split(r"(?m)(?=^(?:Object|ObjectReskin)\s+\S+)", text)
    return parts


def object_name(part: str) -> str:
    m = re.match(r"(?m)^(?:Object|ObjectReskin)\s+(\S+)", part)
    return m.group(1) if m else ""


def replace_models(part: str, mapping: dict[str, str]) -> str:
    def sub(m):
        val = m.group(2)
        return m.group(1) + mapping.get(val, val)

    return re.sub(r"(?im)^(\s*Model\s*=\s*)(\S+)", sub, part)


def remap_launch_bones(part: str, mapping: dict[tuple[str, str], str]) -> str:
    """mapping keys are (slot_upper, old_bone_upper) -> new_bone."""

    def sub(m):
        slot = m.group(2)
        bone = m.group(3)
        new = mapping.get((slot.upper(), bone.upper()), bone)
        return f"{m.group(1)}{slot} {new}"

    return re.sub(
        r"(?im)^(\s*WeaponLaunchBone\s*=\s*)(\S+)\s+(\S+)",
        sub,
        part,
    )


def ensure_growler_weapons(part: str) -> str:
    if "AGM88G_AARGM-ER" in part and "AIM9X_HOBS_SRAAM" in part:
        return part
    n = nl(part)
    block = GROWLER_WEAPONS.replace("\n", n)
    # Replace the first un-upgraded WeaponSet if it is ALQ-only.
    pat = re.compile(
        r"(?ms)^(\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n).*?^(\s*End\s*)$",
    )
    m = pat.search(part)
    if m:
        return part[: m.start()] + block + part[m.end() :]
    # Insert before ArmorSet
    m2 = re.search(r"(?m)^(\s*ArmorSet\b)", part)
    if m2:
        return part[: m2.start()] + block + n + part[m2.start() :]
    return part


def ensure_launch_bones(part: str, lines: list[str]) -> str:
    if "WeaponLaunchBone" in part:
        return part
    n = nl(part)
    inject = n.join(["      " + ln if not ln.startswith(" ") else ln for ln in lines])
    return re.sub(
        r"(?im)^(\s*DefaultConditionState\s*\n(?:.*\n)*?\s*Model\s*=\s*\S+\s*\n)",
        lambda m: m.group(1) + inject + n,
        part,
        count=1,
    )


def patch_f35b(part: str) -> str:
    part = replace_models(
        part,
        {"AVF-35": "AVLightn", "AVF-35_D": "AVLightn_D", "AVF-35_E": "AVLightn_D"},
    )
    part = remap_launch_bones(
        part,
        {
            ("PRIMARY", "WEAPONA01"): "LASERPL01",
            ("PRIMARY", "WEAPONA"): "LASERPL01",
            ("PRIMARY", "WEAPON01"): "LASERPL01",
            ("SECONDARY", "WEAPONA01"): "LASERPL02",
            ("SECONDARY", "WEAPONA"): "LASERPL02",
            ("SECONDARY", "WEAPON01"): "LASERPL02",
            ("TERTIARY", "WEAPONA01"): "LASERPL01",
            ("TERTIARY", "WEAPON01"): "LASERPL01",
        },
    )
    part = re.sub(
        r"(?im)^(\s*ConditionState\s*=\s*REALLYDAMAGED(?:[^\n]*)\n\s*Model\s*=\s*)AVLightn\b",
        r"\1AVLightn_D",
        part,
    )
    part = re.sub(
        r"(?im)^(\s*SelectPortrait\s*=\s*)SPEC_SouthKoreaJetF35A\b",
        r"\1AmericaF35BJSF",
        part,
    )
    part = re.sub(
        r"(?im)^(\s*ButtonImage\s*=\s*)SPEC_SouthKoreaJetF35A\b",
        r"\1AmericaF35BJSF",
        part,
    )
    return part


def patch_f35a(part: str) -> str:
    part = replace_models(
        part,
        {
            "US_F35A": "LSFUSAF35A",
            "JPF35A": "LSFUSAF35A",
            "JPF35Ad": "LSFUSAF35Ad",
            "JPF35Ak": "LSFUSAF35Ad",
        },
    )
    # damaged default often reused US_F35A; map remaining US_F35A already done.
    # If only default was US_F35A, add damaged LOD when REALLYDAMAGED still LSFUSAF35A.
    part = re.sub(
        r"(?im)^(\s*ConditionState\s*=\s*REALLYDAMAGED(?:[^\n]*)\n\s*Model\s*=\s*)LSFUSAF35A\b",
        r"\1LSFUSAF35Ad",
        part,
    )
    part = re.sub(
        r"(?im)^(\s*ConditionState\s*=\s*RUBBLE(?:[^\n]*)\n\s*Model\s*=\s*)LSFUSAF35A\b",
        r"\1LSFUSAF35Ad",
        part,
    )
    part = remap_launch_bones(
        part,
        {
            ("PRIMARY", "WEAPONA01"): "MISSILEA01",
            ("PRIMARY", "WEAPONA"): "MISSILEA01",
            ("PRIMARY", "WEAPON01"): "MISSILEA01",
            ("SECONDARY", "WEAPONA01"): "MISSILEB01",
            ("SECONDARY", "WEAPONA"): "MISSILEB01",
            ("SECONDARY", "WEAPON01"): "MISSILEB01",
            ("TERTIARY", "WEAPONA01"): "MISSILEA02",
            ("TERTIARY", "WEAPONA"): "MISSILEA02",
            ("TERTIARY", "WEAPON01"): "MISSILEA02",
        },
    )
    part = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)Nat_f35a\b", r"\1F35", part)
    part = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)Nat_f35a\b", r"\1F35", part)
    return part


def patch_growler(part: str) -> str:
    part = replace_models(
        part,
        {"US_EA18G": "LSFEA18G", "US_EA18Gd": "LSFEA18Gd", "US_EA18Gk": "LSFEA18Gk"},
    )
    part = re.sub(
        r"(?im)^(\s*ConditionState\s*=\s*REALLYDAMAGED(?:[^\n]*)\n\s*Model\s*=\s*)LSFEA18G\b",
        r"\1LSFEA18Gd",
        part,
    )
    part = re.sub(
        r"(?im)^(\s*ConditionState\s*=\s*RUBBLE(?:[^\n]*)\n\s*Model\s*=\s*)LSFEA18G\b",
        r"\1LSFEA18Gd",
        part,
    )
    part = remap_launch_bones(
        part,
        {
            ("PRIMARY", "WEAPONA01"): "WEAPONA01",
            ("SECONDARY", "WEAPONA01"): "MISSILEA01",
            ("TERTIARY", "WEAPONA01"): "MISSILEB01",
        },
    )
    part = ensure_launch_bones(
        part,
        [
            "WeaponLaunchBone    = PRIMARY WEAPONA01",
            "WeaponLaunchBone    = SECONDARY MISSILEA01",
            "WeaponLaunchBone    = TERTIARY MISSILEB01",
        ],
    )
    part = ensure_growler_weapons(part)
    # Variant A cameo: EA18GTB.tga
    part = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", r"\1EA18GTB", part, count=1)
    part = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1EA18GTB", part, count=1)
    return part


def patch_prowler(part: str) -> str:
    part = replace_models(part, {"US_EA18G": "EA6", "LSFEA18G": "EA6"})
    part = remap_launch_bones(
        part,
        {
            ("PRIMARY", "WEAPONA01"): "BOMB01",
            ("PRIMARY", "WEAPONA02"): "BOMB01",
            ("SECONDARY", "WEAPONA01"): "BOMB02",
            ("SECONDARY", "WEAPONA02"): "BOMB02",
            ("PRIMARY", "BOMB01"): "BOMB01",
        },
    )
    part = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", r"\1EA6Prowler", part, count=1)
    part = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1EA6Prowler", part, count=1)
    n = nl(part)
    ws = (
        f"  WeaponSet{n}"
        f"    Conditions = None{n}"
        f"    Weapon = PRIMARY Specter_Weapon_EA6B_GuidedBomb{n}"
        f"    PreferredAgainst = PRIMARY STRUCTURE VEHICLE{n}"
        f"    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI{n}"
        f"  End{n}"
    )
    part, nsub = re.subn(
        r"(?ms)^(\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n).*?^(\s*End\s*)$",
        ws,
        part,
    )
    if nsub == 0 and "Specter_Weapon_EA6B_GuidedBomb" not in part:
        m2 = re.search(r"(?m)^(\s*ArmorSet\b)", part)
        if m2:
            part = part[: m2.start()] + ws + n + part[m2.start() :]
    return part


def patch_object_file(blob: bytes) -> bytes:
    text = decode(blob)
    parts = split_objects(text)
    changed = False
    out = []
    for part in parts:
        name = object_name(part)
        orig = part
        if name in F35B_OBJECTS:
            part = patch_f35b(part)
        elif name in F35A_OBJECTS:
            part = patch_f35a(part)
        elif name in GROWLER_OBJECTS:
            part = patch_growler(part)
        elif name in PROWLER_OBJECTS:
            part = patch_prowler(part)
        if part != orig:
            changed = True
        out.append(part)
    if not changed:
        return blob
    return encode("".join(out), blob)


MISSING_BUTTONS = {
    "Command_ConstructNatoJetF35B": """CommandButton Command_ConstructNatoJetF35B
  Command       = UNIT_BUILD
  Object        = NatoJetF35B
  TextLabel     = CONTROLBAR:ConstructNatoJetF35B
  ButtonImage   = SPEC_NatoJetF35B
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipNatoJetF35B
End
""",
    "Command_ConstructTurkeyJetF35A": """CommandButton Command_ConstructTurkeyJetF35A
  Command       = UNIT_BUILD
  Object        = TurkeyJetF35A
  TextLabel     = CONTROLBAR:ConstructTurkeyJetF35A
  ButtonImage   = SPEC_TurkeyJetF35A
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipTurkeyJetF35A
End
""",
}


GROWLER_BUTTONS = [
    "Command_ConstructAmericaJetEA18",
    "Command_ConstructAmericaJetEA18_AI",
    "Command_ConstructBritainJetEA18G",
    "Command_ConstructFranceJetEA18G",
    "Command_ConstructGermanyJetEA18G",
    "Command_ConstructItalyJetEA18G",
    "Command_ConstructNatoJetEA18G",
    "Command_ConstructSwedenJetEA18G",
    "Command_ConstructTurkeyJetEA18G",
    "Command_ConstructUkraineJetEA18G",
    "Command_ConstructJapanJetF18G",
]

PROWLER_BUTTONS = [
    "Command_ConstructAmericaJetF18Prowler",
    "Command_ConstructJapanJetEA6B",
]

F35A_NAT_BUTTONS = [
    "Command_ConstructBritainJetF35C",
    "Command_ConstructBritainJetF35C_AA",
    "Command_ConstructFranceJetF35C",
    "Command_ConstructFranceJetF35C_AA",
    "Command_ConstructGermanyJetF35C",
    "Command_ConstructGermanyJetF35C_AA",
    "Command_ConstructItalyJetF35C",
    "Command_ConstructItalyJetF35C_AA",
    "Command_ConstructNatoJetF35C",
    "Command_ConstructNatoJetF35C_AA",
    "Command_ConstructSwedenJetF35C",
    "Command_ConstructSwedenJetF35C_AA",
    "Command_ConstructTurkeyJetF35C",
    "Command_ConstructTurkeyJetF35C_AA",
    "Command_ConstructUkraineJetF35C",
    "Command_ConstructUkraineJetF35C_AA",
    "Command_ConstructIsraelJetF35IAdirPenetrator",
    "Command_ConstructIsraelJetF35I_AA",
]


def patch_commandbutton(blob: bytes, key: str) -> bytes:
    text = decode(blob)
    n = nl(text)

    def patch_btn(text, btn, image):
        pat = re.compile(
            rf"(?ms)^(CommandButton {re.escape(btn)}\s*\n)(.*?)(^End\s*$)",
        )
        m = pat.search(text)
        if not m:
            return text
        body = m.group(2)
        if re.search(r"(?im)^  ButtonImage\s*=", body):
            body = re.sub(r"(?im)^(  ButtonImage\s*=\s*)\S+", rf"\1{image}", body)
        else:
            body = body.rstrip() + n + f"  ButtonImage   = {image}" + n
        return text[: m.start()] + m.group(1) + body + m.group(3) + text[m.end() :]

    new = text
    for btn in GROWLER_BUTTONS:
        new = patch_btn(new, btn, "EA18GTB")
    for btn in PROWLER_BUTTONS:
        new = patch_btn(new, btn, "EA6Prowler")
    for btn in F35A_NAT_BUTTONS:
        new = patch_btn(new, btn, "F35")
    new = patch_btn(new, "Command_ConstructSouthKoreaJetF35B", "AmericaF35BJSF")

    canonical = key.replace("/", "\\").lower() == r"data\ini\commandbutton.ini"
    if canonical:
        for name, block in MISSING_BUTTONS.items():
            if re.search(rf"(?m)^CommandButton {re.escape(name)}\b", new):
                continue
            if not new.endswith(n):
                new += n
            new += n + block.replace("\n", n)

    if new == text:
        return blob
    return encode(new, blob)


MAPPED_EA18GTB = """MappedImage EA18GTB
  Texture = EA18GTB.tga
  TextureWidth = 150
  TextureHeight = 112
  Coords = Left:0 Top:0 Right:150 Bottom:112
  Status = NONE
End
"""


def patch_mapped_images(blob: bytes) -> bytes:
    text = decode(blob)
    if re.search(r"(?m)^MappedImage EA18GTB\b", text):
        return blob
    # Only the file that already owns MappedImage EA18G receives the alias.
    if not re.search(r"(?m)^MappedImage EA18G\b", text):
        return blob
    n = nl(text)
    block = MAPPED_EA18GTB.replace("\n", n)
    if not text.endswith(n):
        text += n
    return encode(text + n + block, blob)


def patch_weapon_ini(blob: bytes) -> bytes:
    text = decode(blob)
    if "Weapon Specter_Weapon_EA6B_GuidedBomb" in text:
        return blob
    n = nl(text)
    block = EA6B_WEAPON.replace("\n", n)
    if not text.endswith(n):
        text += n
    return encode(text + n + block, blob)


def csf_upsert(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        return blob
    version, nlab, nstr, extra = struct.unpack_from("<IIII", blob, 4)
    lang = struct.unpack_from("<I", blob, 20)[0]
    pos = 24
    existing = {}
    order = []
    for _ in range(nlab):
        magic = blob[pos : pos + 4]
        if magic != b" LBL":
            print(f"CSF parse abort at label {len(order)} pos {pos} magic={magic!r}")
            return blob
        pos += 4
        nvals, namelen = struct.unpack_from("<II", blob, pos)
        pos += 8
        name = blob[pos : pos + namelen].decode("ascii", "replace")
        pos += namelen
        vals = []
        extras = []
        for _v in range(nvals):
            sm = blob[pos : pos + 4]
            pos += 4
            slen = struct.unpack_from("<I", blob, pos)[0]
            pos += 4
            raw = blob[pos : pos + slen * 2]
            pos += slen * 2
            val = bytes(b ^ 0xFF for b in raw).decode("utf-16-le", "replace")
            extra_s = ""
            if sm == b"WRTS":
                elen = struct.unpack_from("<I", blob, pos)[0]
                pos += 4
                extra_s = blob[pos : pos + elen].decode("latin1", "replace")
                pos += elen
            vals.append(val)
            extras.append((sm, extra_s))
        existing[name] = (magic, vals, extras)
        order.append(name)
    for k, v in labels.items():
        if k in existing:
            magic, vals, extras = existing[k]
            if vals:
                vals[0] = v
            else:
                vals = [v]
                extras = [(b" RTS", "")]
            existing[k] = (magic, vals, extras)
        else:
            order.append(k)
            existing[k] = (b" LBL", [v], [(b" RTS", "")])
    out = bytearray()
    out += b" FSC"
    out += struct.pack("<IIIII", version, len(order), len(order), extra, lang)
    for name in order:
        magic, vals, extras = existing[name]
        nb = name.encode("ascii")
        out += magic
        out += struct.pack("<II", len(vals), len(nb))
        out += nb
        for val, (sm, extra_s) in zip(vals, extras):
            enc = val.encode("utf-16-le")
            xored = bytes(b ^ 0xFF for b in enc)
            chars = len(enc) // 2
            out += sm
            out += struct.pack("<I", chars)
            out += xored
            if sm == b"WRTS":
                eb = extra_s.encode("latin1")
                out += struct.pack("<I", len(eb))
                out += eb
    return bytes(out)


def import_donor_art(art_map: dict[str, bytes]) -> list[str]:
    imported = []
    lower_index = {n.replace("/", "\\").lower(): n for n in art_map}
    for big_name, names in DONOR_ART.items():
        entries = parse_big(DONOR / big_name)
        idx = {n.replace("/", "\\").lower(): (n, b) for n, b in entries}
        for want in names:
            key = want.replace("/", "\\").lower()
            if key not in idx:
                print(f"  DONOR MISSING {want} in {big_name}")
                continue
            orig, blob = idx[key]
            if key in lower_index:
                art_map[lower_index[key]] = blob
                imported.append(lower_index[key] + " (overwrite)")
            else:
                art_map[orig] = blob
                lower_index[key] = orig
                imported.append(orig)
    return imported


def main() -> int:
    print("Loading packed DATA/ART...", flush=True)
    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    data_map = {n: b for n, b in data_entries}
    art_map = {n: b for n, b in art_entries}
    data_order = [n for n, _ in data_entries]
    art_order = [n for n, _ in art_entries]

    print("Importing donor ART...", flush=True)
    imported = import_donor_art(art_map)
    print(f"  {len(imported)} ART files from donor")
    for n in imported:
        print(f"    {n}")

    patched_data = []
    for name, blob in data_entries:
        key = name.replace("/", "\\").lower()
        if key in LOCKED_PATHS:
            continue
        new = blob
        if key.endswith("\\weapon.ini"):
            new = patch_weapon_ini(blob)
        elif key == r"data\ini\commandbutton.ini":
            new = patch_commandbutton(blob, key)
        elif "commandbutton" in key and key.endswith(".ini"):
            # Image remaps only; never append new CommandButton names here.
            new = patch_commandbutton(blob, key)
        elif "mappedimage" in key and key.endswith(".ini"):
            new = patch_mapped_images(blob)
        elif key.endswith("generals.csf"):
            new = csf_upsert(blob, CSF_LABELS)
        elif "\\object\\" in key and key.endswith(".ini"):
            new = patch_object_file(blob)
        if new != blob:
            data_map[name] = new
            patched_data.append(name)

    print(f"Patched DATA files: {len(patched_data)}")
    for n in patched_data:
        print(f"  {n}")

    data_out = [(n, data_map[n]) for n in data_order]
    art_out = []
    known = set()
    for n in art_order:
        art_out.append((n, art_map[n]))
        known.add(n)
    for n, b in art_map.items():
        if n not in known:
            art_out.append((n, b))
            known.add(n)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_out)
    art_big = build_big_ordered(art_out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    asha = hashlib.sha256(art_big).hexdigest()
    print("DATA", dsha, len(data_big))
    print("ART ", asha, len(art_big))
    (OUT_DIR / "SHA256.txt").write_text(
        f"DATA {dsha}\nART  {asha}\nimported {len(imported)}\npatched {len(patched_data)}\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
