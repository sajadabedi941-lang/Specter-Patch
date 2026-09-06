#!/usr/bin/env python3
"""Replace Japan/South Korea air rosters and rework USA C-17.

Does not patch the previous Japan/Korea packer. This rebuilds from
current packed DATA:

- Disable every old JP/KR air object (fighters, helis, transports, leftovers).
- Empty France-style airfield / heavy-base bars, then add the approved list.
- Point Japan/SK PlayerTemplate UI at the France/NATO shortcut bar.
- C-17 becomes a flying carrier: spawn cargo + ground CreateObject unload.
  No CombatDrop, no parachute DeliverPayload, no DeliverPayloadAI on the jet.

ART is copied from the current packed ART (donor meshes already present).
CSF append uses length-prefixed RTS strings only (no trailing 00 00).
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/japan_korea_airforce/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/japan_korea_airforce/_SPEC_ART_ONE.big")
C17_INI = Path(
    "/workspace/patch/Data/INI/Object/Specter/United States Of America/AmericaJetC17Visual.ini"
)
OUT_DIR = Path("/tmp/japan_korea_reset_c17")

JAPAN_AIRFIELD = """
CommandSet Japan_AirfieldCommandSet
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
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

JAPAN_HEAVY = """
CommandSet Japan_HeavyAirBaseCommandSet
  1 = Command_ConstructJapanJetE767
  2 = Command_ConstructJapanJetE2D
  3 = Command_ConstructJapanJetC2
  4 = Command_ConstructJapanJetC130H
  5 = Command_ConstructJapanUAVRQ4
  6 = Command_ConstructJapanHelicopterAH64D
  7 = Command_ConstructJapanHelicopterUH60J
  8 = Command_ConstructJapanHelicopterCH47J
  9 = Command_ConstructJapanJetV22
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SK_AIRFIELD = """
CommandSet SouthKorea_AirfieldCommandSet
  1 = Command_ConstructSouthKoreaJetF35A
  2 = Command_ConstructSouthKoreaJetF35B
  3 = Command_ConstructSouthKoreaJetKF21
  4 = Command_ConstructSouthKoreaJetF15KSlam
  5 = Command_ConstructSouthKoreaJetF16C
  6 = Command_ConstructSouthKoreaJetF16D
  7 = Command_ConstructSouthKoreaJetFA50
  8 = Command_ConstructSouthKoreaJetFA50Blk20
  9 = Command_ConstructSouthKoreaJetT50
  10 = Command_ConstructSouthKoreaJetF4E
  11 = Command_ConstructSouthKoreaJetF5E
  12 = Command_ConstructSouthKoreaJetKF21Blk2
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

SK_HEAVY = """
CommandSet SouthKorea_HeavyAirBaseCommandSet
  1 = Command_ConstructSouthKoreaJetE737
  2 = Command_ConstructSouthKoreaJetRC800
  3 = Command_ConstructSouthKoreaJetC130H
  4 = Command_ConstructSouthKoreaJetCN235
  5 = Command_ConstructSouthKoreaUAVRQ4
  6 = Command_ConstructSouthKoreaJetAH64E
  7 = Command_ConstructSouthKoreaJetUH60P
  8 = Command_ConstructSouthKoreaHelicopterKUH1
  9 = Command_ConstructSouthKoreaJetCH47
  10 = Command_ConstructSouthKoreaHelicopterLAH
  13 = Command_SetRallyPoint
  14 = Command_Sell
End
"""

C17_COMMANDSET = """
CommandSet AmericaC17StarlifterCommandSet
  1 = Command_AmericaC17SafeUnload
  13 = Command_Guard
  14 = Command_Stop
End
"""

C17_OCL = """
ObjectCreationList OCL_AmericaC17SafeUnload
  CreateObject
    ObjectNames = AmericaTankCrusader
    Count = 4
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Offset = X:40 Y:-30 Z:0
  End
  CreateObject
    ObjectNames = AmericaVehicleM2A3Busk3
    Count = 2
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Offset = X:20 Y:30 Z:0
  End
  CreateObject
    ObjectNames = AmericaInfantryRanger
    Count = 15
    IgnorePrimaryObstacle = Yes
    Disposition = LIKE_EXISTING
    Offset = X:0 Y:0 Z:0
  End
End
"""

C17_BUTTON = """
CommandButton Command_AmericaC17SafeUnload
  Command           = SPECIAL_POWER
  SpecialPower      = SpecialPowerAmericaC17SafeUnload
  Options           = OK_FOR_MULTI_SELECT NEED_TARGET_POS
  TextLabel         = CONTROLBAR:AmericaC17SafeUnload
  ButtonImage       = C17GlobalMaster
  ButtonBorderType  = ACTION
  DescriptLabel     = CONTROLBAR:ToolTipAmericaC17SafeUnload
  InvalidCursorName = GenericInvalid
End
"""

C17_SPECIALPOWER = """
SpecialPower SpecialPowerAmericaC17SafeUnload
  Enum               = SPECIAL_HELIX_NAPALM_BOMB
  ReloadTime         = 20000
  RadiusCursorRadius = 80
End
"""

BUTTONS = [
    ("Command_ConstructJapanJetF35A", "JapanJetF35A", "SPEC_JapanJetF35A", "F-35A Lightning II"),
    ("Command_ConstructJapanJetF35B", "JapanJetF35B", "SPEC_JapanJetF35B", "F-35B Lightning II"),
    ("Command_ConstructJapanJetF15J", "JapanJetF15J", "SPEC_JapanF15J", "F-15J Eagle"),
    ("Command_ConstructJapanJetF15DJ", "JapanJetF15DJ", "SPEC_JapanJetF15DJ", "F-15DJ Eagle"),
    ("Command_ConstructJapanJetF2A", "JapanJetF2A", "SPEC_JapanF2A", "Mitsubishi F-2A"),
    ("Command_ConstructJapanJetF2B", "JapanJetF2B", "SPEC_JapanF2B", "Mitsubishi F-2B"),
    ("Command_ConstructJapanJetF2Kai", "JapanJetF2Kai", "SPEC_JapanF2Kai", "F-2 Anti-Ship"),
    ("Command_ConstructJapanJetF4EJKai", "JapanJetF4EJKai", "SPEC_JapanF4EJKai", "F-4EJ Kai"),
    ("Command_ConstructJapanJetX2Shinshin", "JapanJetX2Shinshin", "SPEC_JapanX2Shinshin", "X-2 Shinshin"),
    ("Command_ConstructJapanJetF16", "JapanJetF16", "SPEC_SouthKoreaJetF16C", "F-16 Japan"),
    ("Command_ConstructJapanJetFA18", "JapanJetFA18", "SPEC_JapanJetFX", "F/A-18 Japan"),
    ("Command_ConstructJapanJetFX", "JapanJetFX", "SPEC_JapanJetFX", "Future Fighter FX"),
    ("Command_ConstructJapanJetE767", "JapanJetE767", "E2avionHE", "E-767 AWACS"),
    ("Command_ConstructJapanJetE2D", "AmericaJetE2Visual", "E2avionHE", "E-2D Hawkeye"),
    ("Command_ConstructJapanJetC2", "JapanJetC2", "SPEC_JapanC130H", "Kawasaki C-2"),
    ("Command_ConstructJapanJetC130H", "JapanJetC130H", "SPEC_JapanC130H", "C-130 Hercules"),
    ("Command_ConstructJapanUAVRQ4", "JapanUAVRQ4", "SPEC_JapanRQ4", "RQ-4 Global Hawk"),
    ("Command_ConstructJapanHelicopterAH64D", "JapanHelicopterAH64D", "Nat_ah64e", "AH-64D Apache"),
    ("Command_ConstructJapanHelicopterUH60J", "JapanHelicopterUH60J", "SSChinookUnload", "UH-60J Black Hawk"),
    ("Command_ConstructJapanHelicopterCH47J", "JapanHelicopterCH47J", "SSChinookUnload", "CH-47J Chinook"),
    ("Command_ConstructJapanJetV22", "AmericaJetV22Visual", "C17GlobalMaster", "V-22 Osprey"),
    ("Command_ConstructSouthKoreaJetF35A", "SouthKoreaJetF35A", "SPEC_SouthKoreaJetF35A", "F-35A Lightning II"),
    ("Command_ConstructSouthKoreaJetF35B", "SouthKoreaJetF35B", "SPEC_SouthKoreaJetF35A", "F-35B Lightning II"),
    ("Command_ConstructSouthKoreaJetKF21", "SouthKoreaJetKF21", "SPEC_SouthKoreaJetKF21", "KF-21 Boramae"),
    ("Command_ConstructSouthKoreaJetF15KSlam", "SouthKoreaJetF15KSlam", "SPEC_SouthKoreaJetF15KSlam", "F-15K Slam Eagle"),
    ("Command_ConstructSouthKoreaJetF16C", "SouthKoreaJetF16C", "SPEC_SouthKoreaJetF16C", "KF-16C"),
    ("Command_ConstructSouthKoreaJetF16D", "SouthKoreaJetF16D", "SPEC_SouthKoreaJetF16D", "KF-16D"),
    ("Command_ConstructSouthKoreaJetFA50", "SouthKoreaJetFA50", "SPEC_SouthKoreaJetFA50", "FA-50 Fighting Eagle"),
    ("Command_ConstructSouthKoreaJetFA50Blk20", "SouthKoreaJetFA50Blk20", "SPEC_SouthKoreaJetFA50", "FA-50 Block 20"),
    ("Command_ConstructSouthKoreaJetT50", "SouthKoreaJetT50", "SPEC_SouthKoreaJetT50", "TA-50"),
    ("Command_ConstructSouthKoreaJetF4E", "SouthKoreaJetF4E", "SPEC_SouthKoreaJetF4E", "F-4E Phantom"),
    ("Command_ConstructSouthKoreaJetF5E", "SouthKoreaJetF5E", "SPEC_SouthKoreaJetF5E", "F-5E Tiger II"),
    ("Command_ConstructSouthKoreaJetKF21Blk2", "SouthKoreaJetKF21Blk2", "SPEC_SouthKoreaJetKF21Blk2", "KF-21 Block II"),
    ("Command_ConstructSouthKoreaJetRC800", "SouthKoreaJetRC800", "E2avionHE", "RC-800 Recon"),
    ("Command_ConstructSouthKoreaJetCN235", "SouthKoreaJetCN235", "SPEC_JapanC130H", "CN-235 Transport"),
    ("Command_ConstructSouthKoreaUAVRQ4", "AmericaUAVGlobalHawk", "SPEC_JapanRQ4", "RQ-4 Global Hawk"),
    ("Command_ConstructSouthKoreaHelicopterKUH1", "SouthKoreaHelicopterKUH1", "SSChinookUnload", "KUH-1 Surion"),
    ("Command_ConstructSouthKoreaHelicopterLAH", "SouthKoreaHelicopterLAH", "Nat_ah64e", "LAH"),
]

KEEP_BUILDABLE = {obj for _b, obj, _i, _p in BUTTONS}


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


def replace_named_block(text: str, kind: str, name: str, replacement: str) -> str:
    pat = rf"(?ms)^{kind}\s+{re.escape(name)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{kind} {name} not found")
    return text[: m.start()] + to_nl(replacement, nl(text)).rstrip() + text[m.end() :]


def append_if_missing(text: str, needle: str, block: str) -> str:
    if needle in text:
        return text
    newline = nl(text)
    return text.rstrip("\r\n") + newline + newline + to_nl(block, newline)


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


def stub_old_air_object(text: str) -> str:
    """Replace leftover air files with empty disabled stubs. Keep names so maps parse."""
    objs = re.findall(r"(?m)^Object\s+(\S+)", text)
    if any(obj in KEEP_BUILDABLE for obj in objs):
        return text
    stubs = []
    for obj in objs:
        stubs.append(
            f"Object {obj}\r\n"
            f"  Buildable = No\r\n"
            f"  Side = Neutral\r\n"
            f"  EditorSorting = SYSTEM\r\n"
            f"  KindOf = PRELOAD IGNORED_IN_GUI\r\n"
            f"  Body = ActiveBody ModuleTag_01\r\n"
            f"    MaxHealth = 1.0\r\n"
            f"    InitialHealth = 1.0\r\n"
            f"  End\r\n"
            f"  Geometry = Box\r\n"
            f"  GeometryMajorRadius = 1.0\r\n"
            f"  GeometryMinorRadius = 1.0\r\n"
            f"  GeometryHeight = 1.0\r\n"
            f"End\r\n"
        )
    return "".join(stubs) if stubs else "  Buildable = No\r\n"


def is_jp_kr_air_ini(name: str) -> bool:
    key = norm(name)
    if not key.endswith(".ini"):
        return False
    air_dirs = (
        r"data\ini\object\specter\japan self-defense forces\airforce" + "\\",
        r"data\ini\object\specter\republic of korea armed forces\airforce" + "\\",
        r"data\ini\object\specter\south korean armed forces\airforce" + "\\",
    )
    return any(key.startswith(d) for d in air_dirs)


def fighter_ini(obj, side, portrait, models, primary, secondary, scale, cost, time, bones=("WeaponA", "WeaponA")):
    alive, dmg, rub = models
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {alive}
      WeaponLaunchBone = PRIMARY {bones[0]}
      WeaponLaunchBone = SECONDARY {bones[1]}
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 720.0
  ShroudClearingRange = 240.0
  WeaponSet
    Conditions = None
    Weapon = PRIMARY {primary}
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY {secondary}
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  BuildCost = {cost}
  BuildTime = {time}
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


def support_ini(obj, side, portrait, models, scale, kind="AWACS"):
    alive, dmg, rub = models
    extra = ""
    if kind == "AWACS":
        extra = (
            "  Behavior = StealthDetectorUpdate ModuleTag_AWACS\n"
            "    DetectionRate = 1800\n"
            "    DetectionRange = 2700\n"
            "  End\n"
        )
        kof = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS"
        cmd = "AmericaE2AWACSCommandSet"
    elif kind == "TRANSPORT":
        extra = (
            "  Behavior = TransportContain ModuleTag_Cargo\n"
            "    Slots = 16\n"
            "    DamagePercentToUnits = 100%\n"
            "    AllowInsideKindOf = INFANTRY VEHICLE\n"
            "    ForbidInsideKindOf = AIRCRAFT HUGE_VEHICLE\n"
            "    ExitDelay = 100\n"
            "    NumberOfExitPaths = 1\n"
            "  End\n"
        )
        kof = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT TRANSPORT"
        cmd = "GenericCommandSet"
    else:
        kof = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS"
        cmd = "GenericCommandSet"
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {alive}
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 800.0
  ShroudClearingRange = 800.0
  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End
  BuildCost = 4000
  BuildTime = 28.0
  CommandSet = {cmd}
  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  KindOf = {kof}
  Body = ActiveBody ModuleTag_02
    MaxHealth = 600.0
    InitialHealth = 600.0
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
    Mass = 400.0
  End
  Behavior = JetAIUpdate ModuleTag_09
    NeedsRunway = Yes
    AutoAcquireEnemiesWhenIdle = No
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    MinHeight = 1
  End
  Locomotor = SET_NORMAL D30-F6_JetLocomotor
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor
{extra}  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 28.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 8.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def heli_ini(obj, side, portrait, models, scale, attack=False):
    alive, dmg, rub = models
    wpn = ""
    kof = "PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD"
    cmd = "AmericaVehicleChinookCommandSet"
    if attack:
        wpn = (
            "  WeaponSet\n"
            "    Conditions = None\n"
            "    Weapon = PRIMARY GenericHeliGunnerSight\n"
            "    Weapon = SECONDARY 70mm_Hydra_AH64E\n"
            "  End\n"
        )
        kof = "PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE TRANSPORT AIRCRAFT SCORE PRODUCED_AT_HELIPAD"
        cmd = "GenericAttackHelicopterHoverCommandSet"
    return f"""Object {obj}
  Buildable = Yes
  Scale = {scale}
  SelectPortrait = {portrait}
  ButtonImage = {portrait}
  Draw = W3DModelDraw ModuleTag_01
    DefaultConditionState
      Model = {alive}
    End
    ConditionState = REALLYDAMAGED
      Model = {dmg}
    End
    ConditionState = RUBBLE
      Model = {rub}
    End
    OkToChangeModelColor = Yes
  End
  DisplayName = OBJECT:{obj}
  EditorSorting = VEHICLE
  Side = {side}
  VisionRange = 250.0
  {wpn}  ArmorSet
    Conditions = None
    Armor = ChinookArmor
    DamageFX = None
  End
  BuildCost = 1600
  BuildTime = 16.0
  CommandSet = {cmd}
  VoiceSelect = ChinookVoiceSelect
  VoiceMove = ChinookVoiceMove
  KindOf = {kof}
  Body = ActiveBody ModuleTag_03
    MaxHealth = 480.0
    InitialHealth = 480.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_HelicopterStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_09ai
    MinHeight = 10
    NeedsRunway = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle = {"Yes" if attack else "No"}
  End
  Locomotor = SET_NORMAL ChinookLocomotor
  Locomotor = SET_TAXIING BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = HelicopterSlowDeathBehavior ModuleTag_08
    DestructionDelay = 99999999
    SpiralOrbitTurnRate = 140.0
    SpiralOrbitForwardSpeed = 350.0
    SpiralOrbitForwardSpeedDamping = .9999
    MaxBraking = 190
    SoundDeathLoop = ComancheDamagedLoop
    MinSelfSpin = 100
    MaxSelfSpin = 300
    SelfSpinUpdateDelay = 100
    SelfSpinUpdateAmount = 10
    FallHowFast = 12.0%
    MinBladeFlyOffDelay = 1500
    MaxBladeFlyOffDelay = 1500
    FXHitGround = FX_HelicopterHitGround
    OCLHitGround = OCL_HelicopterHitGround
    FXFinalBlowUp = FX_GroundedHelicopterBlowUp
    OCLFinalBlowUp = OCL_GroundedHelicopterBlowUp
    DelayFromGroundToFinalDeath = 1500
    FinalRubbleObject = ChinookRubbleHull
  End
  Geometry = BOX
  GeometryMajorRadius = 20.0
  GeometryMinorRadius = 6.0
  GeometryHeight = 12.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 45
End
"""


def new_air_objects() -> dict[str, str]:
    jp = r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce"
    sk = r"Data\INI\Object\Specter\Republic of Korea Armed Forces\Airforce"
    aa = "AmericaF35C_AA_AIM120"
    ag = "GBU_31V2_JDAM_F35C"
    return {
        rf"{jp}\JapanJetF35A.ini": fighter_ini("JapanJetF35A", "Japan", "SPEC_JapanJetF35A", ("LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak"), aa, ag, "0.90", "2600", "14.0", ("MISSILEA01", "MISSILEA01")),
        rf"{jp}\JapanJetF35B.ini": fighter_ini("JapanJetF35B", "Japan", "SPEC_JapanJetF35B", ("LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak"), aa, ag, "0.88", "2800", "15.0", ("MISSILEA01", "MISSILEA01")),
        rf"{jp}\JapanJetF15J.ini": fighter_ini("JapanJetF15J", "Japan", "SPEC_JapanF15J", ("LSFJPF15J", "LSFJPF15Jd", "LSFJPF15Jk"), aa, aa, "0.92", "2400", "14.0"),
        rf"{jp}\JapanJetF15DJ.ini": fighter_ini("JapanJetF15DJ", "Japan", "SPEC_JapanJetF15DJ", ("LSFISF15E", "LSFISF15ED", "LSFISF15ED"), aa, ag, "0.92", "2500", "14.0"),
        rf"{jp}\JapanJetF2A.ini": fighter_ini("JapanJetF2A", "Japan", "SPEC_JapanF2A", ("JPF2", "JPF2D", "JPF2K"), aa, ag, "0.90", "2200", "13.0"),
        rf"{jp}\JapanJetF2B.ini": fighter_ini("JapanJetF2B", "Japan", "SPEC_JapanF2B", ("AGMZJPF2G", "AGMZJPF2G", "AGMZJPF2G"), aa, ag, "0.90", "2200", "13.0"),
        rf"{jp}\JapanJetF2Kai.ini": fighter_ini("JapanJetF2Kai", "Japan", "SPEC_JapanF2Kai", ("LSF02TJ", "LSF02TJd", "LSF02TJk"), aa, "Japan_Weapon_ASM2_F2A", "0.90", "2400", "14.0"),
        rf"{jp}\JapanJetF4EJKai.ini": fighter_ini("JapanJetF4EJKai", "Japan", "SPEC_JapanF4EJKai", ("JPF4", "JPF4D", "JPF4K"), aa, ag, "0.88", "1800", "12.0"),
        rf"{jp}\JapanJetX2Shinshin.ini": fighter_ini("JapanJetX2Shinshin", "Japan", "SPEC_JapanX2Shinshin", ("LSFSX2", "LSFSX2d", "LSFSX2k"), aa, ag, "0.86", "3000", "16.0"),
        rf"{jp}\JapanJetF16.ini": fighter_ini("JapanJetF16", "Japan", "SPEC_SouthKoreaJetF16C", ("US_F16CJ_blk52", "US_F16CJ_blk52", "US_F16CJ_blk52"), aa, aa, "0.88", "2000", "12.0"),
        rf"{jp}\JapanJetFA18.ini": fighter_ini("JapanJetFA18", "Japan", "SPEC_JapanJetFX", ("US_FA18E", "US_FA18E", "US_FA18E"), aa, ag, "0.92", "2300", "14.0"),
        rf"{jp}\JapanJetFX.ini": fighter_ini("JapanJetFX", "Japan", "SPEC_JapanJetFX", ("CHAJ31HXNew", "CHAJ31HXNew", "CHAJ31HXNew"), aa, ag, "0.90", "3200", "16.0"),
        rf"{jp}\JapanJetE767.ini": support_ini("JapanJetE767", "Japan", "E2avionHE", ("JP_E767", "JP_E767", "JP_E767"), "1.28", "AWACS"),
        rf"{jp}\JapanJetC2.ini": support_ini("JapanJetC2", "Japan", "SPEC_JapanC130H", ("JP_C2", "JP_C2d", "JP_C2k"), "1.00", "TRANSPORT"),
        rf"{jp}\JapanJetC130H.ini": support_ini("JapanJetC130H", "Japan", "SPEC_JapanC130H", ("AVCargoPln", "AVCargoPln_D", "AVCargoPln_E"), "1.00", "TRANSPORT"),
        rf"{jp}\JapanUAVRQ4.ini": support_ini("JapanUAVRQ4", "Japan", "SPEC_JapanRQ4", ("US_RQ-4", "US_MQ-4", "US_RQ-4"), "0.80", "RECON"),
        rf"{jp}\JapanHelicopterAH64D.ini": heli_ini("JapanHelicopterAH64D", "Japan", "Nat_ah64e", ("LSFJapanAH64D", "LSFJapanAH64Dd", "LSFJapanAH64Dd"), "0.90", True),
        rf"{jp}\JapanHelicopterUH60J.ini": heli_ini("JapanHelicopterUH60J", "Japan", "SSChinookUnload", ("LSFJPUH60", "LSFJPUH60d", "LSFJPUH60k"), "0.86"),
        rf"{jp}\JapanHelicopterCH47J.ini": heli_ini("JapanHelicopterCH47J", "Japan", "SSChinookUnload", ("US_CH47F", "US_CH47F", "US_CH47F"), "0.88"),
        rf"{sk}\SouthKoreaJetF35A.ini": fighter_ini("SouthKoreaJetF35A", "SouthKorea", "SPEC_SouthKoreaJetF35A", ("LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak"), aa, ag, "0.90", "2600", "14.0", ("MISSILEA01", "MISSILEA01")),
        rf"{sk}\SouthKoreaJetF35B.ini": fighter_ini("SouthKoreaJetF35B", "SouthKorea", "SPEC_SouthKoreaJetF35A", ("LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak"), aa, ag, "0.88", "2800", "15.0", ("MISSILEA01", "MISSILEA01")),
        rf"{sk}\SouthKoreaJetKF21.ini": fighter_ini("SouthKoreaJetKF21", "SouthKorea", "SPEC_SouthKoreaJetKF21", ("LSFJ31", "LSFJ31d", "LSFJ31k"), aa, ag, "0.90", "2600", "14.0"),
        rf"{sk}\SouthKoreaJetF15KSlam.ini": fighter_ini("SouthKoreaJetF15KSlam", "SouthKorea", "SPEC_SouthKoreaJetF15KSlam", ("LSFF15K", "LSFF15Kd", "LSFF15Kd"), aa, ag, "0.94", "2600", "15.0"),
        rf"{sk}\SouthKoreaJetF16C.ini": fighter_ini("SouthKoreaJetF16C", "SouthKorea", "SPEC_SouthKoreaJetF16C", ("LSFKF16", "LSFKF16d", "LSFKF16d"), aa, ag, "0.88", "2000", "12.0"),
        rf"{sk}\SouthKoreaJetF16D.ini": fighter_ini("SouthKoreaJetF16D", "SouthKorea", "SPEC_SouthKoreaJetF16D", ("LSFKF16", "LSFKF16d", "LSFKF16d"), aa, ag, "0.88", "2000", "12.0"),
        rf"{sk}\SouthKoreaJetFA50.ini": fighter_ini("SouthKoreaJetFA50", "SouthKorea", "SPEC_SouthKoreaJetFA50", ("LSFT50", "LSFT50d", "LSFT50k"), aa, ag, "0.84", "1800", "12.0", ("Weapon01", "Weapon01")),
        rf"{sk}\SouthKoreaJetFA50Blk20.ini": fighter_ini("SouthKoreaJetFA50Blk20", "SouthKorea", "SPEC_SouthKoreaJetFA50", ("LSFT50", "LSFT50d", "LSFT50k"), aa, ag, "0.84", "1900", "12.0", ("Weapon01", "Weapon01")),
        rf"{sk}\SouthKoreaJetT50.ini": fighter_ini("SouthKoreaJetT50", "SouthKorea", "SPEC_SouthKoreaJetT50", ("LSFT50", "LSFT50d", "LSFT50k"), aa, ag, "0.84", "1700", "11.0", ("Weapon01", "Weapon01")),
        rf"{sk}\SouthKoreaJetF4E.ini": fighter_ini("SouthKoreaJetF4E", "SouthKorea", "SPEC_SouthKoreaJetF4E", ("LSFKoreaF4", "LSFKoreaF4d", "LSFKoreaF4k"), aa, ag, "0.88", "1800", "12.0", ("MISSILEA01", "MISSILEA01")),
        rf"{sk}\SouthKoreaJetF5E.ini": fighter_ini("SouthKoreaJetF5E", "SouthKorea", "SPEC_SouthKoreaJetF5E", ("LSFKoreaF5", "LSFKoreaF5d", "LSFKoreaF5k"), aa, ag, "0.80", "1400", "10.0", ("MISSILEA01", "MISSILEA01")),
        rf"{sk}\SouthKoreaJetKF21Blk2.ini": fighter_ini("SouthKoreaJetKF21Blk2", "SouthKorea", "SPEC_SouthKoreaJetKF21Blk2", ("NVJ31", "NVJ31_D", "NVJ31_E"), aa, ag, "0.90", "2800", "15.0"),
        rf"{sk}\SouthKoreaJetE737.ini": support_ini("SouthKoreaJetE737", "SouthKorea", "E2avionHE", ("KVE737", "KVE737", "KVE737"), "1.10", "AWACS"),
        rf"{sk}\SouthKoreaJetRC800.ini": support_ini("SouthKoreaJetRC800", "SouthKorea", "E2avionHE", ("SK_RC800", "SK_RC800d", "SK_RC800d"), "1.10", "RECON"),
        rf"{sk}\SouthKoreaJetC130H.ini": support_ini("SouthKoreaJetC130H", "SouthKorea", "SPEC_JapanC130H", ("US_C130H", "US_C130H", "US_C130H"), "1.00", "TRANSPORT"),
        rf"{sk}\SouthKoreaJetCN235.ini": support_ini("SouthKoreaJetCN235", "SouthKorea", "SPEC_JapanC130H", ("SK_CN235", "SK_CN235d", "SK_CN235k"), "0.82", "TRANSPORT"),
        rf"{sk}\SouthKoreaJetAH64E.ini": heli_ini("SouthKoreaJetAH64E", "SouthKorea", "Nat_ah64e", ("US_AH64E", "US_AH64E", "US_AH64E"), "0.90", True),
        rf"{sk}\SouthKoreaJetUH60P.ini": heli_ini("SouthKoreaJetUH60P", "SouthKorea", "SSChinookUnload", ("LSFKoreaUH60", "LSFKoreaUH60", "LSFKoreaUH60"), "0.86"),
        rf"{sk}\SouthKoreaHelicopterKUH1.ini": heli_ini("SouthKoreaHelicopterKUH1", "SouthKorea", "SSChinookUnload", ("SK_KUH1", "SK_KUH1d", "SK_KUH1k"), "0.88"),
        rf"{sk}\SouthKoreaJetCH47.ini": heli_ini("SouthKoreaJetCH47", "SouthKorea", "SSChinookUnload", ("US_CH47F", "US_CH47F", "US_CH47F"), "0.88"),
        rf"{sk}\SouthKoreaHelicopterLAH.ini": heli_ini("SouthKoreaHelicopterLAH", "SouthKorea", "Nat_ah64e", ("SK_LAH", "SK_LAHd", "SK_LAHk"), "0.78", True),
    }


def button_block(name: str, obj: str, image: str) -> str:
    short = name[len("Command_Construct") :] if name.startswith("Command_Construct") else obj
    return (
        f"CommandButton {name}\r\n"
        f"  Command       = UNIT_BUILD\r\n"
        f"  Object        = {obj}\r\n"
        f"  TextLabel     = CONTROLBAR:Construct{short}\r\n"
        f"  ButtonImage   = {image}\r\n"
        f"  ButtonBorderType = BUILD\r\n"
        f"  DescriptLabel = CONTROLBAR:ToolTip{short}\r\n"
        f"End\r\n"
    )


def retarget_player_template(text: str, faction: str) -> str:
    """France/NATO UI integration only. Does not copy France aircraft."""
    pat = rf"(?ms)^PlayerTemplate\s+{re.escape(faction)}\s*\r?\n.*?^End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit(f"{faction} missing")
    block = m.group(0)
    block = re.sub(
        r"(?m)^(\s*SpecialPowerShortcutWinName\s*=\s*)\S+",
        r"\1GenPowersShortcutBarUS.wnd",
        block,
    )
    return text[: m.start()] + block + text[m.end() :]


def main() -> int:
    if not SRC_DATA.is_file() or not C17_INI.is_file():
        print("missing source DATA or C-17 INI", file=sys.stderr)
        return 1
    entries = parse_big(SRC_DATA)
    index = {norm(n): i for i, (n, _) in enumerate(entries)}
    original_names = [n for n, _ in entries]
    original_count = len(entries)

    disabled = 0
    for i, (name, blob) in enumerate(entries):
        if not is_jp_kr_air_ini(name):
            continue
        text = stub_old_air_object(blob.decode("latin1"))
        entries[i] = (name, text.encode("latin1"))
        disabled += 1
    print("stubbed old JP/KR air files", disabled)

    added = new_air_objects()
    for packed_name, content in added.items():
        raw = content.replace("\n", "\r\n").encode("latin1")
        key = norm(packed_name)
        if key in index:
            entries[index[key]] = (entries[index[key]][0], raw)
            print("replaced", packed_name)
        else:
            entries.append((packed_name, raw))
            index[key] = len(entries) - 1
            print("added", packed_name)

    c17_key = norm(r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini")
    entries[index[c17_key]] = (
        entries[index[c17_key]][0],
        C17_INI.read_bytes().replace(b"\n", b"\r\n") if b"\r\n" not in C17_INI.read_bytes()[:200] else C17_INI.read_bytes(),
    )
    print("replaced C-17 flying carrier")

    def mut(path: str, fn):
        key = norm(path)
        i = index[key]
        name, blob = entries[i]
        old = blob.decode("latin1")
        new = fn(old)
        if new == old:
            raise SystemExit(f"no change {path}")
        entries[i] = (name, new.encode("latin1"))
        print("patched", path, "delta", len(new) - len(blob))

    def patch_commandset(text: str) -> str:
        text = replace_named_block(text, "CommandSet", "Japan_AirfieldCommandSet", JAPAN_AIRFIELD)
        text = replace_named_block(text, "CommandSet", "Japan_HeavyAirBaseCommandSet", JAPAN_HEAVY)
        text = replace_named_block(text, "CommandSet", "SouthKorea_AirfieldCommandSet", SK_AIRFIELD)
        text = replace_named_block(text, "CommandSet", "SouthKorea_HeavyAirBaseCommandSet", SK_HEAVY)
        text = replace_named_block(text, "CommandSet", "AmericaC17StarlifterCommandSet", C17_COMMANDSET)
        return text

    def patch_commandbutton(text: str) -> str:
        extra = []
        for name, obj, image, _pretty in BUTTONS:
            if f"CommandButton {name}" not in text:
                extra.append(button_block(name, obj, image))
        text = append_if_missing(text, "Command_AmericaC17SafeUnload", C17_BUTTON)
        if "CommandButton Command_AmericaC17ParaDrop" in text:
            text = replace_named_block(text, "CommandButton", "Command_AmericaC17ParaDrop", C17_BUTTON.replace("Command_AmericaC17SafeUnload", "Command_AmericaC17ParaDrop"))
        if extra:
            newline = nl(text)
            text = text.rstrip("\r\n") + newline + newline + "".join(
                b.replace("\r\n", newline) for b in extra
            ) + newline
        return text

    def patch_specialpower(text: str) -> str:
        return append_if_missing(text, "SpecialPowerAmericaC17SafeUnload", C17_SPECIALPOWER)

    def patch_ocl(text: str) -> str:
        if "ObjectCreationList OCL_AmericaC17SafeUnload" in text:
            text = replace_named_block(text, "ObjectCreationList", "OCL_AmericaC17SafeUnload", C17_OCL)
        else:
            text = append_if_missing(text, "OCL_AmericaC17SafeUnload", C17_OCL)
        if "ObjectCreationList OCL_AmericaC17TargetParaDrop" in text:
            text = replace_named_block(text, "ObjectCreationList", "OCL_AmericaC17TargetParaDrop", C17_OCL.replace("OCL_AmericaC17SafeUnload", "OCL_AmericaC17TargetParaDrop"))
        return text

    def patch_pt(text: str) -> str:
        text = retarget_player_template(text, "FactionJapan")
        text = retarget_player_template(text, "FactionSouthKorea")
        return text

    def patch_weapon_objects(text: str) -> str:
        if "OCL_AmericaC17TargetParaDrop" not in text:
            return text
        return text.replace("OCL_AmericaC17TargetParaDrop", "OCL_AmericaC17SafeUnload")

    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)
    mut(r"Data\INI\SpecialPower.ini", patch_specialpower)
    mut(r"Data\INI\ObjectCreationList.ini", patch_ocl)
    mut(r"Data\INI\PlayerTemplate.ini", patch_pt)
    mut(
        r"Data\INI\Object\Specter\United States Of America\USA_AirForce_WeaponObjects.ini",
        patch_weapon_objects,
    )

    labels = {
        "CONTROLBAR:AmericaC17SafeUnload": "Unload Cargo",
        "CONTROLBAR:ToolTipAmericaC17SafeUnload": "Deploy C-17 cargo onto the ground",
    }
    for name, obj, _img, pretty in BUTTONS:
        short = name[len("Command_Construct") :]
        labels[f"CONTROLBAR:Construct{short}"] = pretty
        labels[f"CONTROLBAR:ToolTip{short}"] = f"Build {pretty}"
        labels[f"OBJECT:{obj}"] = pretty
    i = index[norm(r"Data\English\generals.csf")]
    name, blob = entries[i]
    new_csf = append_csf_labels(blob, labels)
    entries[i] = (name, new_csf)
    print("patched CSF", len(new_csf) - len(blob))

    if [n for n, _ in entries][:original_count] != original_names:
        raise SystemExit("original entry order changed")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_data = OUT_DIR / "_SPEC_DATA_ONE.big"
    packed = build_big_ordered(entries)
    out_data.write_bytes(packed)
    print("wrote", out_data, "size", len(packed), "files", len(entries), "sha", hashlib.sha256(packed).hexdigest())

    if not SRC_ART.is_file():
        print("missing ART", SRC_ART, file=sys.stderr)
        return 1
    art = SRC_ART.read_bytes()
    out_art = OUT_DIR / "_SPEC_ART_ONE.big"
    out_art.write_bytes(art)
    print("copied ART", out_art, "size", len(art), "sha", hashlib.sha256(art).hexdigest())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
