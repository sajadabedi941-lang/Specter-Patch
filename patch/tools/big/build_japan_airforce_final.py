#!/usr/bin/env python3
"""Japan Air Force final completion pass.

Surgical DATA inject only. Never mutates CommandCenter, VT72B, PlayerTemplate,
Science, or airfield *building* objects. Never packs overlay CommandSet_Japan.ini.
Never copies donor DATA. Uses packed Specter ART stems already in _SPEC_ART_ONE.big.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/jp_sk_vn_donor_art/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/jp_sk_vn_donor_art/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/japan_airforce_final")

LOCKED_PATHS = (
    r"Data\INI\PlayerTemplate.ini",
    r"Data\INI\Science.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\Japan_VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Tracked\VT72B.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_CommandCenter.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Iraq_CommandCenter.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_Airfield.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_LargeAirBase.ini",
    r"Data\INI\Object\Specter\Japan Self-Defense Forces\Buildings\Japan_HeavyAirBase.ini",
)

LOCKED_COMMANDSETS = (
    "Japan_VT72BCommandSet",
    "SouthKorea_VT72BCommandSet",
    "Vietnam_VT72BCommandSet",
    "Japan_CommandCenterCommandSet",
    "SouthKorea_CommandCenterCommandSet",
    "Vietnam_CommandCenterCommandSet",
    "SouthKorea_AirfieldCommandSet",
    "SouthKorea_HeavyAirBaseCommandSet",
    "Vietnam_AirfieldCommandSet",
    "Vietnam_HeavyAirBaseCommandSet",
)

DO_NOT_PACK = (
    r"Data\INI\CommandSet_Japan.ini",
    r"Data\INI\CommandSet_SouthKorea.ini",
    r"Data\INI\CommandSet_Vietnam.ini",
)

FIGHTER_BAR = """CommandSet Japan_AirfieldCommandSet
  1 = Command_ConstructJapanJetF35A
  2 = Command_ConstructJapanJetF35B
  3 = Command_ConstructJapanJetF15J
  4 = Command_ConstructJapanJetF15DJ
  5 = Command_ConstructJapanJetF2A
  6 = Command_ConstructJapanJetF2B
  7 = Command_ConstructJapanJetF2Kai
  8 = Command_ConstructJapanJetF4EJKai
  9 = Command_ConstructJapanJetX2Shinshin
  10 = Command_ConstructJapanJetF16
  11 = Command_ConstructJapanJetFA18
  12 = Command_ConstructJapanJetFX
  13 = Command_ConstructJapanJetF35Japon
  14 = Command_ConstructJapanJetF14Tomcat
End
"""

HEAVY_BAR = """CommandSet Japan_HeavyAirBaseCommandSet
  1 = Command_ConstructJapanJetE2D
  2 = Command_ConstructJapanJetC2
  3 = Command_ConstructJapanJetC130H
  4 = Command_ConstructJapanUAVRQ4
  5 = Command_ConstructJapanHelicopterAH64D
  6 = Command_ConstructJapanHelicopterUH60J
  7 = Command_ConstructJapanHelicopterCH47J
  8 = Command_ConstructJapanJetV22
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

NEW_COMMANDSETS = """
CommandSet JapanC130HBomberCommandSet
  1 = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet JapanUAVRQ4CommandSet
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet JapanAH64DCommandSet
  1 = Command_FireMainWeapon
  2 = Command_FireJapanAH64Hydra
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet JapanUH60JCommandSet
  1 = Command_FireMainWeapon
  12 = Command_AttackMove
  13 = Command_Guard
  14 = Command_Stop
End

CommandSet JapanCH47JTransportCommandSet
  1 = Command_TransportExit
  2 = Command_TransportExit
  3 = Command_TransportExit
  4 = Command_TransportExit
  5 = Command_TransportExit
  6 = Command_TransportExit
  7 = Command_TransportExit
  8 = Command_TransportExit
  9 = Command_ChinookUnload
  14 = Command_Stop
End
"""

BUTTON_F35JAPON = """CommandButton Command_ConstructJapanJetF35Japon
  Command       = UNIT_BUILD
  Object        = JapanJetF35Japon
  TextLabel     = CONTROLBAR:ConstructJapanJetF35Japon
  ButtonImage   = Nat_f35a
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetF35Japon
End
"""

BUTTON_F14 = """CommandButton Command_ConstructJapanJetF14Tomcat
  Command       = UNIT_BUILD
  Object        = JapanJetF14Tomcat
  TextLabel     = CONTROLBAR:ConstructJapanJetF14Tomcat
  ButtonImage   = SPEC_IranJetF14AM
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetF14Tomcat
End
"""

BUTTON_AH64_HYDRA = """CommandButton Command_FireJapanAH64Hydra
  Command           = FIRE_WEAPON
  WeaponSlot        = TERTIARY
  Options           = OK_FOR_MULTI_SELECT NEED_TARGET_POS
  TextLabel         = CONTROLBAR:FireJapanAH64Hydra
  ButtonImage       = SSRocketAttack
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:ToolTipFireJapanAH64Hydra
  RadiusCursorType  = ATTACK_SCATTER_AREA
  InvalidCursorName = GenericInvalid
End
"""

C130_WEAPON = """Weapon Japan_Weapon_C130H_HeavyBomb
  PrimaryDamage           = 900.0
  PrimaryDamageRadius     = 90.0
  AttackRange             = 1100
  MinimumAttackRange      = 250
  AcceptableAimDelta      = 40
  DamageType              = EXPLOSION
  DeathType               = EXPLODED
  WeaponSpeed             = 999999999
  ProjectileObject        = GBU-31V2
  FireFX                  = FX_AuroraBombLaunch
  ProjectileDetonationOCL = OCL_MK84Warhead
  RadiusDamageAffects     = ALLIES ENEMIES NEUTRALS NOT_SIMILAR
  DelayBetweenShots       = 400
  ClipSize                = 8
  ClipReloadTime          = 30000
  AutoReloadsClip         = RETURN_TO_BASE
  ShowsAmmoPips           = Yes
  ProjectileCollidesWith  = STRUCTURES
  AntiAirborneVehicle     = No
  AntiGround              = Yes
  ShockWaveAmount         = 180.0
  ShockWaveRadius         = 90.0
  ShockWaveTaperOff       = 0.33
End
"""

WEAPONSETS = {
    "JapanJetF35A": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V2_JDAM_F35C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF35B": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM9X_HOBS_SRAAM_F35C
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY Gbu-12II_Paveway
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF15J": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F22A
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF15DJ": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V2_JDAM_F15E
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF2A": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY Japan_Weapon_ASM2_F2A
    PreferredAgainst = PRIMARY VEHICLE STRUCTURE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V2_JDAM_F35C
    PreferredAgainst = SECONDARY STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF2B": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY Gbu-12II_Paveway
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF2Kai": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY Japan_Weapon_ASM2_F2A
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF4EJKai": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY Japan_Weapon_Sparrow_F4EJ
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY Gbu-12II_Paveway
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetX2Shinshin": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F22A
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF16": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM-9X_F16C
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V1_JDAM_F16C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetFA18": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 1x_AGM65F_FA18F
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetFX": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AGM88G_AARGM-ER
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
}

CSF_LABELS = {
    "OBJECT:JapanJetF35Japon": "F-35 Japon",
    "OBJECT:JapanJetF14Tomcat": "F-14 Tomcat",
    "CONTROLBAR:ConstructJapanJetF35Japon": "Build F-35 Japon",
    "CONTROLBAR:ToolTipJapanJetF35Japon": "Stealth multirole fighter. AIM missiles and guided bombs.",
    "CONTROLBAR:ConstructJapanJetF14Tomcat": "Build F-14 Tomcat",
    "CONTROLBAR:ToolTipJapanJetF14Tomcat": "Air-superiority fighter. Phoenix and Sidewinder missiles. No ground bombs.",
    "CONTROLBAR:FireJapanAH64Hydra": "Fire Hydra Rockets",
    "CONTROLBAR:ToolTipFireJapanAH64Hydra": "Fire air-to-ground Hydra rockets.",
}

FIGHTER_PATHS = {
    "JapanJetF35A": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35A.ini",
    "JapanJetF35B": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35B.ini",
    "JapanJetF15J": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15J.ini",
    "JapanJetF15DJ": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF15DJ.ini",
    "JapanJetF2A": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2A.ini",
    "JapanJetF2B": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2B.ini",
    "JapanJetF2Kai": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF2Kai.ini",
    "JapanJetF4EJKai": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF4EJKai.ini",
    "JapanJetX2Shinshin": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini",
    "JapanJetF16": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF16.ini",
    "JapanJetFA18": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetFA18.ini",
    "JapanJetFX": r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetFX.ini",
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


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
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


def norm(name: str) -> str:
    return name.replace("/", "\\").lower()


def nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(block: str, newline: str) -> str:
    return block.replace("\r\n", "\n").replace("\n", newline).strip("\n") + newline


def named(text: str, kind: str, name: str):
    m = re.search(rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$", text)
    return m.group(0) if m else None


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def remove_named_block(text: str, kind: str, name: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        return text
    start = m.start()
    end = m.end()
    while end < len(text) and text[end] in "\r\n":
        end += 1
    return text[:start] + text[end:]


def xor_csf_utf16(s: str) -> bytes:
    return bytes(b ^ 0xFF for b in s.encode("utf-16-le"))


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
    extra = bytearray()
    add_labels = 0
    add_strings = 0
    existing = blob.upper()
    for name, value in labels.items():
        key = name.encode("latin1")
        if key.upper() in existing:
            continue
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(key))
        extra += key
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += xor_csf_utf16(value)
        add_labels += 1
        add_strings += 1
    if add_labels == 0:
        return blob
    out = bytearray(blob)
    struct.pack_into("<I", out, 8, nlabels + add_labels)
    struct.pack_into("<I", out, 12, nstrings + add_strings)
    out += extra
    return bytes(out)


def replace_weaponset(text: str, block: str) -> str:
    newline = nl(text)
    pat = r"(?ms)^[ \t]*WeaponSet\s*\r?\n.*?^[ \t]*End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit("WeaponSet not found")
    return text[: m.start()] + to_nl(block, newline).rstrip() + text[m.end() :]


def set_kv(text: str, key: str, value: str) -> str:
    pat = rf"(?m)^(\s*{re.escape(key)}\s*=\s*)\S+"
    if not re.search(pat, text):
        raise SystemExit(f"key {key} not found")
    return re.sub(pat, rf"\g<1>{value}", text, count=1)


def add_kindof(text: str, extra: str, remove: tuple[str, ...] = ()) -> str:
    m = re.search(r"(?m)^(\s*KindOf\s*=\s*)(.+)$", text)
    if not m:
        raise SystemExit("KindOf not found")
    tokens = m.group(2).split()
    for r in remove:
        if r in tokens:
            tokens.remove(r)
    if extra and extra not in tokens:
        tokens.append(extra)
    return text[: m.start()] + m.group(1) + " ".join(tokens) + text[m.end() :]


def fighter_template(obj: str, portrait: str, models: tuple[str, str, str], bone: str, cost: int, time: float, scale: float, weapons: str) -> str:
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale:.2f}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {models[0]}
      WeaponLaunchBone = PRIMARY {bone}
      WeaponLaunchBone = SECONDARY {bone}
    End
    ConditionState = REALLYDAMAGED
      Model = {models[1]}
    End
    ConditionState = RUBBLE
      Model = {models[2]}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = Japan
  VisionRange = 720.0
  ShroudClearingRange = 240.0
{weapons}
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  BuildCost = {cost}
  BuildTime = {time:.1f}
  CommandSet = F22A_AA_CommandSet
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  KindOf = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT
  Body = ActiveBody ModuleTag_02
    MaxHealth = 480.0
    InitialHealth = 480.0
  End
  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    FallHowFast = 110.0%
    FXInitialDeath = FX_RaptorDeathInitial
    OCLInitialDeath = OCL_RaptorDeathInitial
    DelaySecondaryFromInitialDeath = 500
    FXSecondary = FX_JetDeathSecondary
    OCLSecondary = OCL_RaptorDeathSecondary
    FXHitGround = FX_JetDeathHitGround
    OCLHitGround = OCL_RaptorDeathHitGround
    DelayFinalBlowUpFromHitGround = 200
    FXFinalBlowUp = FX_JetDeathFinalBlowUp
    OCLFinalBlowUp = OCL_RaptorDeathFinalBlowUp
  End
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    AutoAcquireEnemiesWhenIdle = Yes
  End
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 14.0
  GeometryMinorRadius = 7.0
  GeometryHeight = 5.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def patch_draw_models(text: str, default: str, damaged: str, rubble: str, bone: str | None = None) -> str:
    states = [
        (r"(?ms)(DefaultConditionState\s*\r?\n\s*Model\s*=\s*)\S+", default),
        (r"(?ms)(ConditionState\s*=\s*REALLYDAMAGED\s*\r?\n\s*Model\s*=\s*)\S+", damaged),
        (r"(?ms)(ConditionState\s*=\s*RUBBLE\s*\r?\n\s*Model\s*=\s*)\S+", rubble),
    ]
    for pat, model in states:
        if not re.search(pat, text):
            raise SystemExit(f"draw state missing for {model}")
        text = re.sub(pat, rf"\g<1>{model}", text, count=1)
    if bone:
        text = re.sub(r"(?m)^(\s*WeaponLaunchBone\s*=\s*\S+\s+)\S+", rf"\1{bone}", text)
    return text


def add_helo_animation(text: str, default_anim: str, damaged_anim: str, rubble_anim: str) -> str:
    newline = nl(text)

    def inject(state_pat: str, anim: str) -> None:
        nonlocal text
        m = re.search(state_pat, text)
        if not m:
            raise SystemExit(f"helo state missing for {anim}")
        block = m.group(0)
        if "Animation =" in block:
            block = re.sub(r"(?m)^(\s*Animation\s*=\s*)\S+", rf"\1{anim}", block)
            if "AnimationMode" not in block:
                block = re.sub(
                    r"(?m)^(\s*Animation\s*=\s*\S+\s*)$",
                    rf"\1{newline}      AnimationMode = LOOP",
                    block,
                    count=1,
                )
        else:
            block = re.sub(
                r"(?m)^(\s*Model\s*=\s*\S+\s*)$",
                rf"\1{newline}      Animation = {anim}{newline}      AnimationMode = LOOP",
                block,
                count=1,
            )
        text = text[: m.start()] + block + text[m.end() :]

    inject(r"(?ms)DefaultConditionState\s*\r?\n.*?^\s*End\s*$", default_anim)
    inject(r"(?ms)ConditionState\s*=\s*REALLYDAMAGED\s*\r?\n.*?^\s*End\s*$", damaged_anim)
    inject(r"(?ms)ConditionState\s*=\s*RUBBLE\s*\r?\n.*?^\s*End\s*$", rubble_anim)
    return text


def ensure_weaponset(text: str, block: str) -> str:
    newline = nl(text)
    if re.search(r"(?ms)^[ \t]*WeaponSet\s*\r?\n.*?^[ \t]*End\s*$", text):
        return replace_weaponset(text, block)
    m = re.search(r"(?m)^[ \t]*ArmorSet\s*$", text)
    if not m:
        raise SystemExit("cannot insert WeaponSet")
    return text[: m.start()] + to_nl(block, newline) + text[m.start() :]


def patch_ch47(text: str) -> str:
    text = add_helo_animation(text, "US_CH47F.US_CH47F", "US_CH47F.US_CH47F", "US_CH47F.US_CH47F")
    text = set_kv(text, "CommandSet", "JapanCH47JTransportCommandSet")
    if "TransportContain" not in text:
        newline = nl(text)
        contain = to_nl(
            """  Behavior = TransportContain ModuleTag_Cargo
    Slots = 8
    DamagePercentToUnits = 100%
    AllowInsideKindOf = INFANTRY
    ExitDelay = 50
    NumberOfExitPaths = 1
  End""",
            newline,
        )
        text = text.replace("  Shadow = SHADOW_VOLUME", contain + "  Shadow = SHADOW_VOLUME", 1)
    text = add_kindof(text, "TRANSPORT", remove=("CAN_ATTACK",))
    return text


def patch_ah64(text: str) -> str:
    text = add_helo_animation(
        text,
        "LSFJapanAH64D.LSFJapanAH64D",
        "LSFJapanAH64Dd.LSFJapanAH64Dd",
        "LSFJapanAH64Dd.LSFJapanAH64Dd",
    )
    text = ensure_weaponset(
        text,
        """  WeaponSet
    Conditions = None
    Weapon = PRIMARY 30mm_M230E1_ChainGun
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 8x_MRATGM_AGM114L
    PreferredAgainst = SECONDARY VEHICLE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = TERTIARY 70mm_Hydra_AH64E
    PreferredAgainst = TERTIARY STRUCTURE INFANTRY
    AutoChooseSources = TERTIARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    )
    text = set_kv(text, "CommandSet", "JapanAH64DCommandSet")
    text = add_kindof(text, "CAN_ATTACK", remove=("TRANSPORT",))
    text = re.sub(
        r"(?m)^(\s*AutoAcquireEnemiesWhenIdle\s*=\s*)\S+",
        r"\1Yes",
        text,
        count=1,
    )
    return text


def patch_uh60(text: str) -> str:
    text = patch_draw_models(text, "US_UH60", "US_UH60", "US_UH60")
    text = add_helo_animation(text, "US_UH60.US_UH60", "US_UH60.US_UH60", "US_UH60.US_UH60")
    text = set_kv(text, "SelectPortrait", "Nat_uh60")
    text = set_kv(text, "ButtonImage", "Nat_uh60")
    text = ensure_weaponset(
        text,
        """  WeaponSet
    Conditions = None
    Weapon = PRIMARY 30mm_M230E1_ChainGun
    PreferredAgainst = PRIMARY INFANTRY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY 70mm_Hydra_AH64E
    PreferredAgainst = SECONDARY STRUCTURE INFANTRY
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    )
    text = set_kv(text, "CommandSet", "JapanUH60JCommandSet")
    text = add_kindof(text, "CAN_ATTACK", remove=("TRANSPORT",))
    text = re.sub(
        r"(?m)^(\s*AutoAcquireEnemiesWhenIdle\s*=\s*)\S+",
        r"\1Yes",
        text,
        count=1,
    )
    return text


def patch_e767(text: str) -> str:
    return """Object JapanJetE767
  Buildable = No
  Scale = 1.00
  Side = Neutral
  EditorSorting = NONE
  KindOf = IMMOBILE IGNORED_IN_GUI
  Body = ActiveBody ModuleTag_E767Removed
    MaxHealth = 1.0
    InitialHealth = 1.0
  End
End
"""


def patch_rq4(text: str) -> str:
    text = set_kv(text, "CommandSet", "JapanUAVRQ4CommandSet")
    text = set_kv(text, "VisionRange", "2200.0")
    text = set_kv(text, "ShroudClearingRange", "2200.0")
    if "REVEALS_ENEMY_PATHS" not in text:
        text = add_kindof(text, "REVEALS_ENEMY_PATHS")
    if "StealthDetectorUpdate" not in text:
        newline = nl(text)
        det = to_nl(
            """  Behavior = StealthDetectorUpdate ModuleTag_Recon
    DetectionRate = 900
    DetectionRange = 2800
  End""",
            newline,
        )
        text = text.replace("  Geometry = Box", det + "  Geometry = Box", 1)
    return text


def patch_c130(text: str) -> str:
    text = ensure_weaponset(
        text,
        """  WeaponSet
    Conditions = None
    Weapon = PRIMARY Japan_Weapon_C130H_HeavyBomb
    PreferredAgainst = PRIMARY STRUCTURE VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    )
    text = set_kv(text, "CommandSet", "JapanC130HBomberCommandSet")
    text = set_kv(text, "Scale", "1.12")
    text = add_kindof(text, "CAN_ATTACK", remove=("TRANSPORT",))
    text = re.sub(
        r"(?ms)^  Behavior = TransportContain ModuleTag_Cargo\s*\r?\n.*?^  End\s*\r?\n",
        "",
        text,
    )
    text = re.sub(
        r"(?m)^(\s*Locomotor\s*=\s*SET_NORMAL\s+)\S+",
        r"\1C130HLocomotor",
        text,
        count=1,
    )
    text = re.sub(
        r"(?m)^(\s*AutoAcquireEnemiesWhenIdle\s*=\s*)\S+",
        r"\1No",
        text,
        count=1,
    )
    # keep single JetAIUpdate
    if text.count("AIUpdate") > 1:
        raise SystemExit("C-130 has multiple AIUpdate modules")
    return text


def patch_f35a_visual(text: str) -> str:
    text = patch_draw_models(text, "AVF-35", "AVF-35_D", "AVF-35_E", bone="WEAPONA01")
    return text


def patch_x2_visual(text: str) -> str:
    text = patch_draw_models(text, "LSFF22", "LSFF22d", "LSFF22k", bone="MISSILEA01")
    return text


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    index = {norm(n): i for i, (n, _) in enumerate(data_entries)}
    original_data_names = [n for n, _ in data_entries]
    original_art_names = [n for n, _ in art_entries]
    src_blobs = {norm(n): b for n, b in data_entries}

    for banned in DO_NOT_PACK:
        if norm(banned) in index:
            raise SystemExit(f"refusing overlay poison file {banned}")

    locked_before = {norm(p): src_blobs[norm(p)] for p in LOCKED_PATHS if norm(p) in index}
    src_cs = src_blobs[norm(r"Data\INI\CommandSet.ini")].decode("latin1")
    locked_cs_before = {name: named(src_cs, "CommandSet", name) for name in LOCKED_COMMANDSETS}

    stems = set()
    for n, _ in art_entries:
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])

    def mut(path: str, fn):
        key = norm(path)
        if key in {norm(p) for p in LOCKED_PATHS}:
            raise SystemExit(f"refusing locked path {path}")
        i = index[key]
        name, blob = data_entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            print("unchanged", path)
            return
        data_entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanHelicopterCH47J.ini",
        patch_ch47,
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanHelicopterAH64D.ini",
        patch_ah64,
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanHelicopterUH60J.ini",
        patch_uh60,
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetE767.ini",
        patch_e767,
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanUAVRQ4.ini",
        patch_rq4,
    )
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetC130H.ini",
        patch_c130,
    )
    mut(FIGHTER_PATHS["JapanJetF35A"], lambda t: replace_weaponset(patch_f35a_visual(t), WEAPONSETS["JapanJetF35A"]))
    mut(FIGHTER_PATHS["JapanJetX2Shinshin"], lambda t: replace_weaponset(patch_x2_visual(t), WEAPONSETS["JapanJetX2Shinshin"]))
    for obj, path in FIGHTER_PATHS.items():
        if obj in ("JapanJetF35A", "JapanJetX2Shinshin"):
            continue
        mut(path, lambda t, o=obj: replace_weaponset(t, WEAPONSETS[o]))

    def patch_commandset(text: str) -> str:
        text = replace_named_block(text, "CommandSet", "Japan_AirfieldCommandSet", FIGHTER_BAR)
        text = replace_named_block(text, "CommandSet", "Japan_HeavyAirBaseCommandSet", HEAVY_BAR)
        for name, block in [
            ("JapanC130HBomberCommandSet", NEW_COMMANDSETS),
        ]:
            pass
        extra_names = [
            "JapanC130HBomberCommandSet",
            "JapanUAVRQ4CommandSet",
            "JapanAH64DCommandSet",
            "JapanUH60JCommandSet",
            "JapanCH47JTransportCommandSet",
        ]
        missing = [n for n in extra_names if not named(text, "CommandSet", n)]
        if missing:
            text = text.rstrip("\r\n") + nl(text) + nl(text) + to_nl(NEW_COMMANDSETS, nl(text))
        after = {name: named(text, "CommandSet", name) for name in LOCKED_COMMANDSETS}
        for name, before in locked_cs_before.items():
            if after[name] != before:
                raise SystemExit(f"locked CommandSet mutated: {name}")
        if "Command_ConstructJapanJetE767" in named(text, "CommandSet", "Japan_HeavyAirBaseCommandSet"):
            raise SystemExit("E-767 still on heavy bar")
        if "Command_SetRallyPoint" in named(text, "CommandSet", "Japan_AirfieldCommandSet"):
            raise SystemExit("rally still on fighter bar")
        return text

    def patch_commandbutton(text: str) -> str:
        text = remove_named_block(text, "CommandButton", "Command_ConstructJapanJetE767")
        extra = []
        for name, block in (
            ("Command_ConstructJapanJetF35Japon", BUTTON_F35JAPON),
            ("Command_ConstructJapanJetF14Tomcat", BUTTON_F14),
            ("Command_FireJapanAH64Hydra", BUTTON_AH64_HYDRA),
        ):
            if named(text, "CommandButton", name):
                text = replace_named_block(text, "CommandButton", name, block)
            else:
                extra.append(block)
        if extra:
            newline = nl(text)
            text = text.rstrip("\r\n") + newline + newline + "".join(to_nl(b, newline) for b in extra)
        if named(text, "CommandButton", "Command_ConstructJapanJetE767"):
            raise SystemExit("E-767 button still present")
        return text

    def patch_weapon(text: str) -> str:
        if named(text, "Weapon", "Japan_Weapon_C130H_HeavyBomb"):
            return replace_named_block(text, "Weapon", "Japan_Weapon_C130H_HeavyBomb", C130_WEAPON)
        return text.rstrip("\r\n") + nl(text) + nl(text) + to_nl(C130_WEAPON, nl(text))

    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)
    mut(r"Data\INI\Weapon.ini", patch_weapon)

    f35j_weapons = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F35C
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU38_JDAM_F16C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""
    f35j = fighter_template(
        "JapanJetF35Japon",
        "Nat_f35a",
        ("US_F35A", "US_F35A", "US_F35A"),
        "WEAPONA01",
        2700,
        15.0,
        0.90,
        f35j_weapons,
    )
    f14_weapons = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM54A_BVR_AALRM
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9M_Sidewinder_HSSRAAM
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""
    f14 = fighter_template(
        "JapanJetF14Tomcat",
        "SPEC_IranJetF14AM",
        ("LSFIRF14A", "LSFIRF14Ad", "LSFIRF14Ad"),
        "MISSILEA01",
        2800,
        16.0,
        0.94,
        f14_weapons,
    )

    new_files = [
        (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35Japon.ini", f35j),
        (r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF14Tomcat.ini", f14),
    ]
    for path, body in new_files:
        if norm(path) in index:
            i = index[norm(path)]
            data_entries[i] = (data_entries[i][0], to_nl(body, "\r\n").encode("latin1"))
            print("replaced", path)
        else:
            data_entries.append((path, to_nl(body, "\r\n").encode("latin1")))
            index[norm(path)] = len(data_entries) - 1
            print("added", path)

    i = index[norm(r"Data\English\generals.csf")]
    name, blob = data_entries[i]
    new_csf = append_csf_labels(blob, CSF_LABELS)
    if new_csf != blob:
        data_entries[i] = (name, new_csf)
        print("patched generals.csf", "delta", len(new_csf) - len(blob))

    # validate models exist
    required_models = {
        "AVF-35",
        "AVF-35_D",
        "AVF-35_E",
        "US_F35A",
        "LSFF22",
        "LSFF22d",
        "LSFF22k",
        "LSFIRF14A",
        "LSFIRF14Ad",
        "US_CH47F",
        "LSFJapanAH64D",
        "LSFJapanAH64Dd",
        "US_UH60",
        "US_RQ-4",
        "US_MQ-4",
        "AVCargoPln",
    }
    missing = sorted(m for m in required_models if m not in stems)
    if missing:
        raise SystemExit(f"required Model= missing from packed ART: {missing}")
    for forbidden in ("JP_F35B", "ENF35A", "LSFSX2", "JPF35A"):
        # these may exist in ART but must not be used by the patched Japan objects
        pass

    allowed_mut = {
        norm(p) for p in (
            r"Data\INI\CommandSet.ini",
            r"Data\INI\CommandButton.ini",
            r"Data\INI\Weapon.ini",
            r"Data\English\generals.csf",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanHelicopterCH47J.ini",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanHelicopterAH64D.ini",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanHelicopterUH60J.ini",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetE767.ini",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanUAVRQ4.ini",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetC130H.ini",
            *FIGHTER_PATHS.values(),
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF35Japon.ini",
            r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF14Tomcat.ini",
        )
    }
    src_index = {norm(n): b for n, b in zip(original_data_names, (b for _, b in parse_big(SRC_DATA)))}
    for n, blob in data_entries:
        key = norm(n)
        if key in {norm(p) for p in LOCKED_PATHS} and key in src_index and blob != src_index[key]:
            raise SystemExit(f"locked file changed {n}")
        if key in src_index and blob != src_index[key] and key not in allowed_mut:
            raise SystemExit(f"unexpected DATA mutation {n}")
        if any(s in key for s in ("commandcenter", "vt72b", "playertemplate")) and key in src_index and blob != src_index[key]:
            raise SystemExit(f"faction-chain file changed {n}")

    kept = [n for n, _ in data_entries if norm(n) in {norm(x) for x in original_data_names}]
    if kept != original_data_names:
        raise SystemExit("existing DATA entry order changed")
    if [n for n, _ in art_entries] != original_art_names:
        raise SystemExit("ART entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    packed_data = build_big_ordered(data_entries)
    packed_art = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(packed_data)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(packed_art)
    print("wrote DATA", len(packed_data), hashlib.sha256(packed_data).hexdigest())
    print("wrote ART", len(packed_art), hashlib.sha256(packed_art).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
