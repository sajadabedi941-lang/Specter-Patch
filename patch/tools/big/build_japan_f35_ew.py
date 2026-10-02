#!/usr/bin/env python3
"""Japan aircraft completion + global F-35A/B donor visuals.

Uses existing packed/donor ART only. Does not touch CommandCenter, VT72B,
PlayerTemplate, Science, or airfield buildings. Does not invent meshes.
"""

from __future__ import annotations

import hashlib
import re
import struct
import sys
from pathlib import Path

SRC_DATA = Path("/tmp/japan_airforce_final/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/japan_airforce_final/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/japan_f35_ew")
DONOR_EA6 = Path("/tmp/donor_prowler")

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

# Invisible / wrong F-35 stems -> proven JSF donor
F35_MODEL_MAP = {
    "ENF35A": "AVF-35",
    "JP_F35B": "AVF-35",
    "JP_F35B_D": "AVF-35_D",
    "LSFUSAF35A": "AVF-35",
    "LSFUSAF35Ad": "AVF-35_D",
    "LSFUSAF35Ak": "AVF-35_E",
    "JPF35A": "AVF-35",
    "JPF35Ad": "AVF-35_D",
    "JPF35Ak": "AVF-35_E",
}

F35B_OBJECTS = (
    "BritainJetF35B",
    "ItalyJetF35B",
    "NatoJetF35B",
    "JapanJetF35B",
    "SouthKoreaJetF35B",
    "AmericaJetF35BJSF",
)

F35A_OBJECTS = (
    "GermanyJetF35A",
    "ItalyJetF35A",
    "JapanJetF35A",
    "SouthKoreaJetF35A",
    "TurkeyJetF35A",
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
  11 = Command_ConstructJapanJetF18G
  12 = Command_ConstructJapanJetF14Tomcat
  13 = Command_ConstructJapanJetF35Japon
  14 = Command_ConstructJapanJetEA6B
End
"""

AA_SET = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AmericaF35C_AA_AIM120
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F35C
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""

F15J_AA = """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F22A
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End"""

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
    "JapanJetF35B": AA_SET,
    "JapanJetF15J": F15J_AA,
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
    Weapon = SECONDARY GBU38_JDAM_F16C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
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
    "JapanJetF35Japon": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM120D_BVR_MRAAM_F35C
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU38_JDAM_F16C
    PreferredAgainst = SECONDARY VEHICLE STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
    "JapanJetF14Tomcat": """  WeaponSet
    Conditions = None
    Weapon = PRIMARY AIM54A_BVR_AALRM
    PreferredAgainst = PRIMARY AIRCRAFT
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9M_Sidewinder_HSSRAAM
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
}

BUTTON_F18G = """CommandButton Command_ConstructJapanJetF18G
  Command       = UNIT_BUILD
  Object        = JapanJetF18G
  TextLabel     = CONTROLBAR:ConstructJapanJetF18G
  ButtonImage   = Nat_ea18g
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetF18G
End
"""

BUTTON_EA6B = """CommandButton Command_ConstructJapanJetEA6B
  Command       = UNIT_BUILD
  Object        = JapanJetEA6B
  TextLabel     = CONTROLBAR:ConstructJapanJetEA6B
  ButtonImage   = USAEA6Prowler
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ToolTipJapanJetEA6B
End
"""

MAPPED_PROWLER = """MappedImage USAEA6Prowler
  Texture = USAEA6Prowler.tga
  TextureWidth = 870
  TextureHeight = 713
  Coords = Left:0 Top:0 Right:870 Bottom:713
  Status = NONE
End
"""

CSF_LABELS = {
    "OBJECT:JapanJetF18G": "F/A-18G Growler",
    "OBJECT:JapanJetEA6B": "EA-6B Prowler",
    "CONTROLBAR:ConstructJapanJetF18G": "Build F/A-18G Growler",
    "CONTROLBAR:ToolTipJapanJetF18G": "Electronic warfare fighter. Jamming support and self-defense missiles.",
    "CONTROLBAR:ConstructJapanJetEA6B": "Build EA-6B Prowler",
    "CONTROLBAR:ToolTipJapanJetEA6B": "Heavy precision strike. Six guided bombs.",
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


def xor_csf_utf16(s: str) -> bytes:
    return bytes(b ^ 0xFF for b in s.encode("utf-16-le"))


def append_csf_labels(blob: bytes, labels: dict[str, str]) -> bytes:
    if blob[:4] != b" FSC":
        raise SystemExit("generals.csf is not CSF")
    _version, nlabels, nstrings = struct.unpack_from("<III", blob, 4)
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
    pat = r"(?ms)^[ \t]*WeaponSet\s*\r?\n.*?^[ \t]*End\s*$"
    m = re.search(pat, text)
    if not m:
        raise SystemExit("WeaponSet not found")
    return text[: m.start()] + to_nl(block, nl(text)).rstrip() + text[m.end() :]


def last_object_span(text: str, obj: str):
    hits = list(re.finditer(rf"(?ms)^Object\s+{re.escape(obj)}\s*\r?\n.*?(?=^Object\s|\Z)", text))
    return hits[-1] if hits else None


def patch_object_in_file(text: str, obj: str, fn) -> str:
    m = last_object_span(text, obj)
    if not m:
        raise SystemExit(f"Object {obj} not found")
    return text[: m.start()] + fn(m.group(0)) + text[m.end() :]


def remap_f35_visual(text: str) -> str:
    def model_sub(m):
        return m.group(1) + F35_MODEL_MAP.get(m.group(2), m.group(2))

    text = re.sub(r"(?m)^(\s*Model\s*=\s*)(\S+)", model_sub, text)
    models = set(re.findall(r"(?m)^\s*Model\s*=\s*(\S+)", text))
    if models & {"AVF-35", "AVF-35_D", "AVF-35_E"}:
        text = re.sub(r"(?m)^(\s*WeaponLaunchBone\s*=\s*\S+\s+)\S+", r"\1WEAPONA01", text)
    forbidden = models & {"ENF35A", "JP_F35B", "JP_F35B_D", "LSFUSAF35A", "LSFUSAF35Ad", "LSFUSAF35Ak", "JPF35A"}
    if forbidden:
        raise SystemExit(f"forbidden F-35 model remains {forbidden}")
    return text


def fighter_template(obj: str, portrait: str, models: tuple[str, str, str], bone: str, cost: int, time: float, scale: float, weapons: str, commandset: str) -> str:
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
  CommandSet = {commandset}
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


def patch_x2(text: str) -> str:
    text = re.sub(r"(?m)^(\s*Model\s*=\s*)LSFF22\s*$", r"\1JP_X2Shinshin", text)
    text = re.sub(r"(?m)^(\s*Model\s*=\s*)LSFF22d\s*$", r"\1JP_X2Shinshin_D", text)
    text = re.sub(r"(?m)^(\s*Model\s*=\s*)LSFF22k\s*$", r"\1JP_X2Shinshin_D", text)
    text = re.sub(r"(?m)^(\s*WeaponLaunchBone\s*=\s*\S+\s+)\S+", r"\1WEAPONA01", text)
    return replace_weaponset(text, WEAPONSETS["JapanJetX2Shinshin"])


def set_c130_clip6(text: str) -> str:
    blk = named(text, "Weapon", "Japan_Weapon_C130H_HeavyBomb")
    if not blk:
        return text
    new = re.sub(r"(?m)^(\s*ClipSize\s*=\s*)\S+", r"\g<1>6", blk, count=1)
    return replace_named_block(text, "Weapon", "Japan_Weapon_C130H_HeavyBomb", new)


def main() -> int:
    if not SRC_DATA.is_file() or not SRC_ART.is_file():
        print("missing source BIGs", file=sys.stderr)
        return 1
    if not (DONOR_EA6 / "EA6.W3D").is_file():
        print("missing donor EA6.W3D", file=sys.stderr)
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

    # Global F-35A / F-35B visual remap by scanning object files
    obj_files: dict[str, str] = {}
    for n, b in data_entries:
        if not n.lower().endswith(".ini"):
            continue
        t = b.decode("latin1", "replace")
        for obj in re.findall(r"(?m)^Object\s+(\S+)", t):
            obj_files.setdefault(obj, n)

    f35_targets = []
    for obj in (*F35A_OBJECTS, *F35B_OBJECTS):
        if obj not in obj_files:
            print("missing object", obj)
            continue
        f35_targets.append((obj, obj_files[obj]))

    touched = {}
    for obj, path in f35_targets:
        key = norm(path)

        def apply(text, o=obj):
            def inner(blk):
                blk = remap_f35_visual(blk)
                if o in F35B_OBJECTS and re.search(r"(?ms)^[ \t]*WeaponSet\s*\r?\n.*?^[ \t]*End\s*$", blk):
                    blk = replace_weaponset(blk, AA_SET)
                return blk

            return patch_object_in_file(text, o, inner)

        touched.setdefault(key, [])
        touched[key].append(apply)

    for key, fns in touched.items():
        i = index[key]
        name, blob = data_entries[i]
        text = blob.decode("latin1")
        for fn in fns:
            text = fn(text)
        data_entries[i] = (name, text.encode("latin1"))
        print("patched F-35 file", name)

    # Japan X-2: remove F-22 duplicate mesh
    mut(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini",
        patch_x2,
    )

    # Japan loadouts on remaining fighters
    for obj, wset in WEAPONSETS.items():
        if obj in ("JapanJetF35B", "JapanJetX2Shinshin"):
            continue
        path = obj_files.get(obj)
        if not path:
            print("skip loadout, missing", obj)
            continue
        mut(path, lambda t, o=obj, w=wset: patch_object_in_file(t, o, lambda blk: replace_weaponset(blk, w)))

    mut(r"Data\INI\Weapon.ini", set_c130_clip6)

    growler = fighter_template(
        "JapanJetF18G",
        "Nat_ea18g",
        ("US_EA18G", "US_EA18G", "US_EA18G"),
        "WEAPONA01",
        2600,
        15.0,
        0.92,
        """  WeaponSet
    Conditions = None
    Weapon = PRIMARY ALQ_99_RadarJamming
    PreferredAgainst = PRIMARY VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY AIM9X_HOBS_SRAAM_F22A
    PreferredAgainst = SECONDARY AIRCRAFT
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
        "EA18G_CommandSet",
    )
    prowler = fighter_template(
        "JapanJetEA6B",
        "USAEA6Prowler",
        ("EA6", "EA6", "EA6"),
        "BOMB01",
        2400,
        16.0,
        1.00,
        """  WeaponSet
    Conditions = None
    Weapon = PRIMARY GBU_31V2_JDAM_F35C
    PreferredAgainst = PRIMARY STRUCTURE VEHICLE
    AutoChooseSources = PRIMARY FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon = SECONDARY GBU_31V2_JDAM_F15E
    PreferredAgainst = SECONDARY STRUCTURE
    AutoChooseSources = SECONDARY FROM_PLAYER FROM_SCRIPT FROM_AI
  End""",
        "F22A_AA_CommandSet",
    )

    def add_or_replace(path: str, body: str):
        key = norm(path)
        blob = to_nl(body, "\r\n").encode("latin1")
        if key in index:
            i = index[key]
            data_entries[i] = (data_entries[i][0], blob)
            print("replaced", path)
        else:
            data_entries.append((path, blob))
            index[key] = len(data_entries) - 1
            print("added", path)

    add_or_replace(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF18G.ini",
        growler,
    )
    add_or_replace(
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini",
        prowler,
    )

    def patch_commandset(text: str) -> str:
        text = replace_named_block(text, "CommandSet", "Japan_AirfieldCommandSet", FIGHTER_BAR)
        after = {name: named(text, "CommandSet", name) for name in LOCKED_COMMANDSETS}
        for name, before in locked_cs_before.items():
            if after[name] != before:
                raise SystemExit(f"locked CommandSet mutated: {name}")
        bar = named(text, "CommandSet", "Japan_AirfieldCommandSet")
        if "Command_ConstructJapanJetE767" in bar:
            raise SystemExit("E-767 on fighter bar")
        if "Command_SetRallyPoint" in bar or "Command_Sell" in bar:
            raise SystemExit("rally/sell still on fighter bar")
        if "F18G" not in bar or "EA6B" not in bar or "F35Japon" not in bar or "F14Tomcat" not in bar:
            raise SystemExit("missing new Japan air slot")
        return text

    def patch_commandbutton(text: str) -> str:
        extra = []
        for name, block in (
            ("Command_ConstructJapanJetF18G", BUTTON_F18G),
            ("Command_ConstructJapanJetEA6B", BUTTON_EA6B),
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

    def patch_mapped(text: str) -> str:
        if named(text, "MappedImage", "USAEA6Prowler"):
            return replace_named_block(text, "MappedImage", "USAEA6Prowler", MAPPED_PROWLER)
        return text.rstrip("\r\n") + nl(text) + nl(text) + to_nl(MAPPED_PROWLER, nl(text))

    mut(r"Data\INI\CommandSet.ini", patch_commandset)
    mut(r"Data\INI\CommandButton.ini", patch_commandbutton)
    mut(r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI", patch_mapped)

    i = index[norm(r"Data\English\generals.csf")]
    name, blob = data_entries[i]
    new_csf = append_csf_labels(blob, CSF_LABELS)
    if new_csf != blob:
        data_entries[i] = (name, new_csf)
        print("patched generals.csf", "delta", len(new_csf) - len(blob))

    # ART inject: EA-6 donor mesh + textures (A6_3.tga alias so mesh resolves)
    art_index = {norm(n): i for i, (n, _) in enumerate(art_entries)}

    def art_put(path: str, blob: bytes):
        key = norm(path)
        if key in art_index:
            i = art_index[key]
            art_entries[i] = (art_entries[i][0], blob)
            print("replaced ART", path, len(blob))
        else:
            art_entries.append((path, blob))
            art_index[key] = len(art_entries) - 1
            print("added ART", path, len(blob))

    ea6_w3d = (DONOR_EA6 / "EA6.W3D").read_bytes()
    ea6_tga = (DONOR_EA6 / "EA6.tga").read_bytes()
    art_put(r"Art\W3D\EA6.W3D", ea6_w3d)
    art_put(r"Art\Textures\EA6.tga", ea6_tga)
    art_put(r"Art\Textures\A6_3.tga", ea6_tga)
    art_put(r"Art\Textures\USAEA6Prowler.tga", (DONOR_EA6 / "USAEA6Prowler.tga").read_bytes())

    stems = set()
    for n, _ in art_entries:
        base = n.replace("/", "\\").split("\\")[-1]
        if base.lower().endswith(".w3d"):
            stems.add(base[:-4])
    required = {"AVF-35", "AVF-35_D", "AVF-35_E", "US_F35A", "US_EA18G", "EA6", "JP_X2Shinshin", "JP_X2Shinshin_D", "LSFIRF14A", "US_CH47F", "LSFJapanAH64D", "US_UH60"}
    missing = sorted(m for m in required if m not in stems)
    if missing:
        raise SystemExit(f"required Model= missing from ART: {missing}")

    allowed_mut = {norm(p) for p in (
        r"Data\INI\CommandSet.ini",
        r"Data\INI\CommandButton.ini",
        r"Data\INI\Weapon.ini",
        r"Data\English\generals.csf",
        r"Data\INI\MappedImages\HandCreated\HandCreatedMappedImages.INI",
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetX2Shinshin.ini",
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetF18G.ini",
        r"Data\INI\Object\Specter\Japan Self-Defense Forces\Airforce\JapanJetEA6B.ini",
    )}
    # F-35 files + japan fighter loadout files
    for obj, path in obj_files.items():
        if obj in F35A_OBJECTS or obj in F35B_OBJECTS or obj in WEAPONSETS:
            allowed_mut.add(norm(path))

    src_index = {norm(n): b for n, b in zip(original_data_names, (b for _, b in parse_big(SRC_DATA)))}
    for n, blob in data_entries:
        key = norm(n)
        if key in {norm(p) for p in LOCKED_PATHS} and key in src_index and blob != src_index[key]:
            raise SystemExit(f"locked file changed {n}")
        if any(s in key for s in ("commandcenter", "vt72b", "playertemplate")) and key in src_index and blob != src_index[key]:
            raise SystemExit(f"faction-chain file changed {n}")
        if key in src_index and blob != src_index[key] and key not in allowed_mut:
            raise SystemExit(f"unexpected DATA mutation {n}")

    kept = [n for n, _ in data_entries if norm(n) in {norm(x) for x in original_data_names}]
    if kept != original_data_names:
        raise SystemExit("existing DATA entry order changed")
    kept_art = [n for n, _ in art_entries if norm(n) in {norm(x) for x in original_art_names}]
    if kept_art != original_art_names:
        raise SystemExit("existing ART entry order changed")

    for p, before in locked_before.items():
        if data_entries[index[p]][1] != before:
            raise SystemExit(f"locked blob changed {p}")

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
