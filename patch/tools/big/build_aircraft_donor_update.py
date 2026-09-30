#!/usr/bin/env python3
"""Apply the discovered aircraft donor-update. ART from New Folder only.

Does not touch PlayerTemplate, Science, War Factory, or ground CommandSets.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/usa_donor_aircraft_visuals/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/usa_donor_aircraft_visuals/_SPEC_ART_ONE.big")
DONOR = Path("/tmp/new_donor_extract/New folder")
OUT_DIR = Path("/tmp/aircraft_donor_update")

LOCKED_PATHS = {
    r"data\ini\playertemplate.ini",
    r"data\ini\science.ini",
}

DONOR_ART = {
    "00PMBeta999.big": [
        r"Art\w3d\CHJH7A.W3D",
        r"Art\w3d\ChJh7a_r.W3D",
        r"Art\Textures\chfbc.dds",
        r"Art\Textures\FEIBAOtb.tga",
        r"Art\Textures\JIAN11TB.tga",
        r"Art\Textures\LSFUSAF15E.dds",
        r"Art\Textures\LSFUSAF15Ed.dds",
        r"Art\w3d\LSFUSAF15E.W3D",
        r"Art\w3d\LSFUSAF15Ed.W3D",
        r"Art\w3d\LSFUSAF15Ek.W3D",
        r"Art\Textures\F15TB.tga",
        r"Art\w3d\LSFSU35.W3D",
        r"Art\w3d\LSFSU35d.W3D",
        r"Art\Textures\SU35TB.tga",
    ],
}

WEAPON_BLOCKS = {
    "Specter_Weapon_JH7A2_Bomb6": """Weapon Specter_Weapon_JH7A2_Bomb6
  PrimaryDamage           = 850
  PrimaryDamageRadius     = 48.0
  SecondaryDamage         = 100.0
  SecondaryDamageRadius   = 50.0
  ScatterRadius           = 80.0
  AttackRange             = 550.0
  AcceptableAimDelta      = 45
  DamageType              = EXPLOSION
  DeathType               = BURNED
  WeaponSpeed             = 9999
  ProjectileObject        = Fab-250
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = FX_ThermobaricWarheadExplosion
  ProjectileDetonationOCL = OCL_ThermobaricFire
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 1
  ClipSize                = 6
  ClipReloadTime          = 13000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiGround              = Yes
  AntiAirborneVehicle     = No
End
""",
    "Specter_Weapon_JH7A2_Bomb4": """Weapon Specter_Weapon_JH7A2_Bomb4
  PrimaryDamage           = 850
  PrimaryDamageRadius     = 48.0
  SecondaryDamage         = 100.0
  SecondaryDamageRadius   = 50.0
  ScatterRadius           = 80.0
  AttackRange             = 550.0
  AcceptableAimDelta      = 45
  DamageType              = EXPLOSION
  DeathType               = BURNED
  WeaponSpeed             = 9999
  ProjectileObject        = Fab-250
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationFX  = FX_ThermobaricWarheadExplosion
  ProjectileDetonationOCL = OCL_ThermobaricFire
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 1
  ClipSize                = 4
  ClipReloadTime          = 13000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiGround              = Yes
  AntiAirborneVehicle     = No
End
""",
    "Specter_Weapon_SU34MF_Bomb6": """Weapon Specter_Weapon_SU34MF_Bomb6
  PrimaryDamage               = 1300.0
  PrimaryDamageRadius         = 90.0
  SecondaryDamage             = 10.0
  SecondaryDamageRadius       = 20.0
  AttackRange                 = 1450
  MinimumAttackRange          = 400.0
  AcceptableAimDelta          = 45
  DamageType                  = ARMOR_PIERCING
  DeathType                   = EXPLODED
  WeaponSpeed                 = 250
  ProjectileObject            = Gorm_E2_BombObject
  ProjectileDetonationFX      = FX_Jiny_HE_Explosion
  RadiusDamageAffects         = ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots           = 720
  ClipSize                    = 6
  ClipReloadTime              = 50000
  AutoReloadsClip             = RETURN_TO_BASE
  ProjectileCollidesWith      = ENEMIES STRUCTURES
  AntiAirborneVehicle         = No
  AntiGround                  = Yes
  AntiAirborneInfantry        = No
  ShowsAmmoPips               = Yes
End
""",
    "Specter_Weapon_B21A_Bomb7": """Weapon Specter_Weapon_B21A_Bomb7
  PrimaryDamage           = 2200.0
  PrimaryDamageRadius     = 70.0
  SecondaryDamage         = 400.0
  SecondaryDamageRadius   = 110.0
  AttackRange             = 2300
  MinimumAttackRange      = 500
  AcceptableAimDelta      = 50
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 9999999999
  ProjectileObject        = GBU72_GuidedBombObject
  FireFX                  = FX_AuroraBombLaunch
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 800
  ClipSize                = 7
  ClipReloadTime          = 25000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiGround              = Yes
  AntiAirborneVehicle     = No
  AntiAirborneInfantry    = No
  LeechRangeWeapon        = Yes
End
""",
}

CSF_LABELS = {
    "CONTROLBAR:ConstructChinaJetJ11Flanker": "J-11 Flanker",
    "CONTROLBAR:ToolTipChinaJetJ11Flanker": "J-11 Flanker. Six SU-34 guided bombs.",
    "OBJECT:ChinaJetJ11Flanker": "J-11 Flanker",
    "CONTROLBAR:ConstructChinaJetFEIBAO": "JH-7 Flying Leopard",
    "CONTROLBAR:ToolTipChinaJetFEIBAO": "Flying Leopard. Four JH-7A2 bombs.",
    "CONTROLBAR:FEIBAO": "JH-7 Flying Leopard",
    "OBJECT:ChinaJetFEIBAO": "JH-7 Flying Leopard",
    "CONTROLBAR:ConstructChinaBomberH6K_B21A": "H-6K Strike",
    "CONTROLBAR:ToolTipChinaBomberH6K_B21A": "H-6K. Seven B-21A guided bombs.",
    "OBJECT:ChinaBomberH6K_B21A": "H-6K Strike",
    "OBJECT:AmericaJetAuterF22": "F-15E Strike Eagle",
    "CONTROLBAR:ConstructAmericaJetAuterF22": "F-15E Strike Eagle",
    "OBJECT:AmericaJetF35C": "F-35 Lightning II",
    "CONTROLBAR:ConstructAmericaJetF35C": "F-35 Lightning II",
    "OBJECT:RussiaJetSu35S": "Su-35 Flanker",
    "CONTROLBAR:ConstructRussiaJetSu35S": "Su-35 Flanker",
    "CONTROLBAR:ConstructAmericaJetF18Prowler": "EA-6B Prowler",
    "OBJECT:AmericaJetF18Prowler": "EA-6B Prowler",
}

NEW_BUTTONS = {
    "Command_ConstructChinaJetJ11Flanker": """CommandButton Command_ConstructChinaJetJ11Flanker
  Command       = UNIT_BUILD
  Object        = ChinaJetJ11Flanker
  TextLabel     = CONTROLBAR:ConstructChinaJetJ11Flanker
  ButtonImage   = JIAN11
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipChinaJetJ11Flanker
End
""",
    "Command_ConstructChinaJetFEIBAO": """CommandButton Command_ConstructChinaJetFEIBAO
  Command       = UNIT_BUILD
  Object        = ChinaJetFEIBAO
  TextLabel     = CONTROLBAR:ConstructChinaJetFEIBAO
  ButtonImage   = FEIBAO
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipChinaJetFEIBAO
End
""",
    "Command_ConstructChinaBomberH6K_B21A": """CommandButton Command_ConstructChinaBomberH6K_B21A
  Command       = UNIT_BUILD
  Object        = ChinaBomberH6K_B21A
  TextLabel     = CONTROLBAR:ConstructChinaBomberH6K_B21A
  ButtonImage   = pla_h6k
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipChinaBomberH6K_B21A
End
""",
}

MAPPED_IMAGES = """MappedImage JIAN11
  Texture = JIAN11TB.tga
  TextureWidth = 128
  TextureHeight = 128
  Coords = Left:0 Top:0 Right:128 Bottom:128
  Status = NONE
End

MappedImage FEIBAO
  Texture = FEIBAOtb.tga
  TextureWidth = 128
  TextureHeight = 128
  Coords = Left:0 Top:0 Right:128 Bottom:128
  Status = NONE
End
"""


def parse_big(path: Path):
    data = path.read_bytes()
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


def replace_first_weaponset_primary(text: str, weapon: str) -> str:
    n = nl(text)
    pat = re.compile(
        r"(?ms)^(\s*WeaponSet\s*\n\s*Conditions\s*=\s*None\s*\n).*?^(\s*End\s*)$",
    )
    block = (
        f"  WeaponSet{n}"
        f"    Conditions = None{n}"
        f"    Weapon = PRIMARY {weapon}{n}"
        f"    PreferredAgainst = PRIMARY STRUCTURE VEHICLE{n}"
        f"    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI{n}"
        f"  End"
    )
    if pat.search(text):
        return pat.sub(block, text, count=1)
    return text


def replace_models(text: str, mapping: dict[str, str]) -> str:
    def sub(m):
        return m.group(1) + mapping.get(m.group(2), m.group(2))

    return re.sub(r"(?im)^(\s*Model\s*=\s*)(\S+)", sub, text)


def remap_bones(text: str, mapping: dict[tuple[str, str], str]) -> str:
    def sub(m):
        slot, bone = m.group(2), m.group(3)
        new = mapping.get((slot.upper(), bone.upper()), bone)
        return f"{m.group(1)}{slot} {new}"

    return re.sub(r"(?im)^(\s*WeaponLaunchBone\s*=\s*)(\S+)\s+(\S+)", sub, text)


def patch_prowler(text: str) -> str:
    text = re.sub(
        r"(?im)^\s*ParticleSysBone\s*=\s*(Engine01|Engine02|Wingtip01|Wingtip02)\s+\S+\s*$",
        "",
        text,
    )
    text = text.replace("Specter_Weapon_EA6B_GuidedBomb", "Specter_Weapon_JH7A2_Bomb6")
    return text


def patch_b52h(text: str) -> str:
    return text.replace("AmericaB52H_HeavyBombDrop", "China_Weapon_FAB_H6K")


def patch_starlifter(text: str) -> str:
    text = re.sub(r"(?im)^(\s*Slots\s*=\s*)\d+", r"\g<1>64", text, count=1)
    text = re.sub(
        r"(?im)^(\s*AllowInsideKindOf\s*=\s*).+$",
        r"\1INFANTRY VEHICLE",
        text,
        count=1,
    )
    text = re.sub(r"(?im)^(\s*ExitDelay\s*=\s*)\d+", r"\g<1>100", text, count=1)
    return text


def patch_auter_f22(text: str) -> str:
    text = replace_models(
        text,
        {
            "LSFF22": "LSFUSAF15E",
            "LSFF22d": "LSFUSAF15Ed",
            "LSFF22k": "LSFUSAF15Ek",
        },
    )
    text = remap_bones(
        text,
        {
            ("PRIMARY", "MISSILEA01"): "WEAPONA",
            ("SECONDARY", "MISSILEB01"): "WEAPONAB",
            ("TERTIARY", "MISSILEA01"): "MISSILEA",
        },
    )
    text = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", r"\1F15E", text, count=1)
    text = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1F15E", text, count=1)
    return replace_first_weaponset_primary(text, "China_Weapon_Bomb_Q5")


def patch_f35c(text: str) -> str:
    text = replace_models(
        text,
        {"AVF-35": "LSFUSAF35A", "AVF-35_D": "LSFUSAF35Ad", "AVF-35_E": "LSFUSAF35Ad"},
    )
    text = remap_bones(
        text,
        {
            ("PRIMARY", "WEAPONA01"): "MISSILEA01",
            ("SECONDARY", "WEAPONA01"): "MISSILEB01",
        },
    )
    text = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", r"\1F35", text, count=1)
    text = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1F35", text, count=1)
    return replace_first_weaponset_primary(text, "Specter_Weapon_SU34MF_Bomb6")


def patch_ka52(text: str) -> str:
    return text.replace(
        "ControlledWeaponSlots = PRIMARY ;SECONDARY TERTIARY",
        "ControlledWeaponSlots = PRIMARY SECONDARY TERTIARY",
        1,
    )


def patch_tu95(text: str) -> str:
    return text.replace("AmericaB52FifteenBombLineWeapon", "China_Weapon_FAB_H6K")


def patch_su35s(text: str) -> str:
    text = replace_models(text, {"RUS_SU35S": "LSFSU35"})
    text = re.sub(
        r"(?im)^(\s*ConditionState\s*=\s*REALLYDAMAGED(?:[^\n]*)\n\s*Model\s*=\s*)LSFSU35\b",
        r"\1LSFSU35d",
        text,
    )
    text = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", r"\1SU35", text, count=1)
    text = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", r"\1SU35", text, count=1)
    return replace_first_weaponset_primary(text, "Specter_Weapon_JH7A2_Bomb6")


def patch_ch5(text: str) -> str:
    text = re.sub(
        r"(?im)^(\s*KindOf\s*=\s*).+$",
        r"\1PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT",
        text,
        count=1,
    )
    n = nl(text)
    jet_ai = (
        f"  Behavior = JetAIUpdate ModuleTag_04iu{n}"
        f"    AutoAcquireEnemiesWhenIdle = Yes{n}"
        f"    OutOfAmmoDamagePerSecond = 0%{n}"
        f"    TakeoffDistForMaxLift = 0%{n}"
        f"    TakeoffPause = 500{n}"
        f"    MinHeight = 6{n}"
        f"    ParkingOffset = 3{n}"
        f"    ReturnToBaseIdleTime = 10000{n}"
        f"  End{n}"
    )
    text = re.sub(
        r"(?ms)^(\s*Behavior\s*=\s*AIUpdateInterface ModuleTag_04iu\s*\n).*?^(\s*End\s*)$",
        jet_ai,
        text,
        count=1,
    )
    text = re.sub(
        r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
        r"\1Snecma_M88_4E",
        text,
        count=1,
    )
    if "SET_TAXIING" not in text:
        text = re.sub(
            r"(?im)^(\s*Locomotor\s*=\s*SET_NORMAL\s+Snecma_M88_4E\s*)$",
            rf"\1{n}  Locomotor = SET_TAXIING BasicJetTaxiLocomotor",
            text,
            count=1,
        )
    return text


def patch_z18a(text: str) -> str:
    n = nl(text)
    block = (
        f"  Behavior = TransportContain ModuleTag_08{n}"
        f"    Slots                 = 8{n}"
        f"    AllowInsideKindOf     = INFANTRY VEHICLE{n}"
        f"    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE{n}"
        f"    ExitDelay             = 100{n}"
        f"    NumberOfExitPaths     = 1{n}"
        f"  End{n}"
    )
    return re.sub(
        r"(?ms)^(\s*Behavior\s*=\s*TransportContain ModuleTag_08\s*\n).*?^(\s*End\s*)$",
        block,
        text,
        count=1,
    )


def patch_object_file(name: str, blob: bytes) -> bytes:
    key = name.replace("/", "\\").lower()
    text = decode(blob)
    orig = text
    if key.endswith("americajetf18prowler.ini"):
        text = patch_prowler(text)
    elif key.endswith("usa_system.ini"):
        # B-52H lives here
        if "Object AmericaJetB52H" in text:
            text = patch_b52h(text)
    elif key.endswith("americajetc17visual.ini"):
        text = patch_starlifter(text)
    elif key.endswith("americajetauterf22.ini"):
        text = patch_auter_f22(text)
    elif key.endswith("\\f35c.ini") and "united states" in key:
        text = patch_f35c(text)
    elif key.endswith("ka52m.ini"):
        text = patch_ka52(text)
    elif key.endswith("russiajettu95.ini"):
        text = patch_tu95(text)
    elif key.endswith("su35s.ini") and "russian" in key:
        text = patch_su35s(text)
    elif key.endswith("\\ch5.ini"):
        text = patch_ch5(text)
    elif key.endswith("z18a.ini"):
        text = patch_z18a(text)
    if text == orig:
        return blob
    return encode(text, blob)


def clone_object(src_text: str, old: str, new: str, portrait: str, weapon: str, display: str) -> str:
    text = src_text.replace(f"Object {old}", f"Object {new}", 1)
    text = re.sub(r"(?im)^(\s*SelectPortrait\s*=\s*)\S+", rf"\1{portrait}", text, count=1)
    text = re.sub(r"(?im)^(\s*ButtonImage\s*=\s*)\S+", rf"\1{portrait}", text, count=1)
    text = re.sub(r"(?im)^(\s*DisplayName\s*=\s*)\S+", rf"\1{display}", text, count=1)
    text = replace_first_weaponset_primary(text, weapon)
    return text


def patch_commandset(blob: bytes) -> bytes:
    text = decode(blob)
    orig = text

    def set_slots(cs_name: str, slots: dict[int, str], src: str) -> str:
        m = re.search(
            rf"(?ms)^(CommandSet {re.escape(cs_name)}\s*\n)(.*?)(^End\s*$)",
            src,
        )
        if not m:
            print(f"  CommandSet missing {cs_name}")
            return src
        body = m.group(2)
        for slot, btn in slots.items():
            if re.search(rf"(?im)^\s*{slot}\s*=\s*\S+", body):
                body = re.sub(
                    rf"(?im)^(\s*{slot}\s*=\s*)\S+",
                    rf"\1{btn}",
                    body,
                    count=1,
                )
            else:
                n = nl(src)
                body = body.rstrip() + n + f"  {slot} = {btn}" + n
        return src[: m.start()] + m.group(1) + body + m.group(3) + src[m.end() :]

    fighter = {
        13: "Command_ConstructChinaJetJ15",
        14: "Command_ConstructChinaJetJ11Flanker",
    }
    aircraft = {
        13: "Command_ConstructChinaBomberH6K_B21A",
        14: "Command_ConstructChinaJetFEIBAO",
    }
    text = set_slots("PLAAirfieldCommandSet", fighter, text)
    text = set_slots("China_LargeAirBaseCommandSet", fighter, text)
    text = set_slots("China_HeavyAirBaseCommandSet", aircraft, text)
    if text == orig:
        return blob
    return encode(text, blob)


def patch_commandbutton(blob: bytes, key: str) -> bytes:
    text = decode(blob)
    n = nl(text)
    orig = text
    if key.replace("/", "\\").lower() != r"data\ini\commandbutton.ini":
        return blob
    for name, block in NEW_BUTTONS.items():
        if re.search(rf"(?m)^CommandButton {re.escape(name)}\b", text):
            continue
        if not text.endswith(n):
            text += n
        text += n + block.replace("\n", n)
    # Auter / F35C / Prowler / Su35S images
    def set_img(btn, image):
        nonlocal text
        m = re.search(
            rf"(?ms)^(CommandButton {re.escape(btn)}\s*\n)(.*?)(^End\s*$)",
            text,
        )
        if not m:
            return
        body = re.sub(r"(?im)^(  ButtonImage\s*=\s*)\S+", rf"\1{image}", m.group(2))
        text = text[: m.start()] + m.group(1) + body + m.group(3) + text[m.end() :]

    set_img("Command_ConstructAmericaJetAuterF22", "F15E")
    set_img("Command_ConstructAmericaJetF35C", "F35")
    set_img("Command_ConstructAmericaJetF18Prowler", "EA6Prowler")
    set_img("Command_ConstructRussiaJetSu35S", "SU35")
    if text == orig:
        return blob
    return encode(text, blob)


def patch_mapped(blob: bytes) -> bytes:
    text = decode(blob)
    if re.search(r"(?m)^MappedImage FEIBAO\b", text):
        return blob
    # Only the China fighter-expansion mapped-image file receives these aliases.
    if not re.search(r"(?m)^MappedImage pla_j11b\b", text):
        return blob
    n = nl(text)
    if not text.endswith(n):
        text += n
    return encode(text + n + MAPPED_IMAGES.replace("\n", n), blob)


def patch_weapon(blob: bytes) -> bytes:
    text = decode(blob)
    n = nl(text)
    added = False
    for name, block in WEAPON_BLOCKS.items():
        if f"Weapon {name}" in text:
            continue
        if not text.endswith(n):
            text += n
        text += n + block.replace("\n", n)
        added = True
    if not added:
        return blob
    return encode(text, blob)


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
            print("CSF parse abort", pos)
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
            out += sm
            out += struct.pack("<I", len(enc) // 2)
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
                print(f"  DONOR MISSING {want}")
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


def find_entry(data_map, suffix: str):
    suffix = suffix.replace("/", "\\").lower()
    for n, b in data_map.items():
        if n.replace("/", "\\").lower().endswith(suffix):
            return n, b
    return None, None


def main() -> int:
    print("Loading packed BIGs...", flush=True)
    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    data_map = {n: b for n, b in data_entries}
    art_map = {n: b for n, b in art_entries}
    data_order = [n for n, _ in data_entries]
    art_order = [n for n, _ in art_entries]

    print("Importing donor ART...", flush=True)
    imported = import_donor_art(art_map)
    print(f"  {len(imported)} ART files")
    for n in imported:
        print("   ", n)

    patched = []
    for name, blob in list(data_entries):
        key = name.replace("/", "\\").lower()
        if key in LOCKED_PATHS:
            continue
        new = blob
        if key.endswith("\\weapon.ini"):
            new = patch_weapon(blob)
        elif key == r"data\ini\commandbutton.ini":
            new = patch_commandbutton(blob, key)
        elif key.endswith("\\commandset.ini"):
            new = patch_commandset(blob)
        elif "mappedimage" in key and key.endswith(".ini"):
            new = patch_mapped(blob)
        elif key.endswith("generals.csf"):
            new = csf_upsert(blob, CSF_LABELS)
        elif "\\object\\" in key and key.endswith(".ini"):
            new = patch_object_file(name, blob)
        if new != blob:
            data_map[name] = new
            patched.append(name)

    # Clone new objects from packed sources.
    clones = []
    j11_name, j11_blob = find_entry(data_map, r"\j11b.ini")
    h6_name, h6_blob = find_entry(data_map, r"\h6k.ini")
    jh_name, jh_blob = find_entry(data_map, r"\jh7a2.ini")
    if j11_blob:
        t = clone_object(
            decode(j11_blob),
            "ChinaJetJ11B",
            "ChinaJetJ11Flanker",
            "JIAN11",
            "Specter_Weapon_SU34MF_Bomb6",
            "OBJECT:ChinaJetJ11Flanker",
        )
        new_name = r"Data\INI\Object\Specter\PLA\Airforce\ChinaJetJ11Flanker.ini"
        data_map[new_name] = encode(t, j11_blob)
        clones.append(new_name)
    if h6_blob:
        t = clone_object(
            decode(h6_blob),
            "ChinaBomberH6K",
            "ChinaBomberH6K_B21A",
            "pla_h6k",
            "Specter_Weapon_B21A_Bomb7",
            "OBJECT:ChinaBomberH6K_B21A",
        )
        new_name = r"Data\INI\Object\Specter\PLA\Airforce\ChinaBomberH6K_B21A.ini"
        data_map[new_name] = encode(t, h6_blob)
        clones.append(new_name)
    if jh_blob:
        t = clone_object(
            decode(jh_blob),
            "ChinaJetJH7A2",
            "ChinaJetFEIBAO",
            "FEIBAO",
            "Specter_Weapon_JH7A2_Bomb4",
            "OBJECT:ChinaJetFEIBAO",
        )
        t = replace_models(t, {"NVJH-7A": "CHJH7A", "NVJH-7AD": "CHJH7A", "NVJH-7AD1": "ChJh7a_r"})
        new_name = r"Data\INI\Object\Specter\PLA\Airforce\ChinaJetFEIBAO.ini"
        data_map[new_name] = encode(t, jh_blob)
        clones.append(new_name)

    print("Patched DATA:", len(patched))
    for n in patched:
        print(" ", n)
    print("New objects:", clones)

    data_out = [(n, data_map[n]) for n in data_order]
    known = set(data_order)
    for n in clones:
        if n not in known:
            data_out.append((n, data_map[n]))
            known.add(n)
    art_out = [(n, art_map[n]) for n in art_order]
    known_a = set(art_order)
    for n, b in art_map.items():
        if n not in known_a:
            art_out.append((n, b))
            known_a.add(n)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(data_out)
    art_big = build_big_ordered(art_out)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    asha = hashlib.sha256(art_big).hexdigest()
    print("DATA", dsha, len(data_big))
    print("ART ", asha, len(art_big))
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\nART  {asha}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
