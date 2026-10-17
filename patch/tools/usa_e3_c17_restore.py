#!/usr/bin/env python3
"""Restore buildable AmericaJetE3Visual + AmericaJetC17Visual on HeavyAirBase.

- Rewrite both Objects from AmericaJetE737Visual flight template (Specter-safe)
- Ensure ACTIVE CommandButton.ini UNIT_BUILD buttons
- Ensure America_HeavyAirBaseCommandSet slots 5 (E-3) and 8 (C-17)
- Freeze E-737 Scale 0.8, E-2 Scale 3.932, HeavyAirBase 3x2, other aircraft
DATA-only (ART already has E3 + IUAC17HXNew).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import struct
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "Release/SPECTER_MASTER"
DATA_BIG = MASTER / "_SPEC_DATA_ONE.big"
ART_BIG = MASTER / "_SPEC_ART_ONE.big"
STAGE = MASTER / "_stage_usa_e3_c17_restore"
VERIFY = MASTER / "_extract_usa_e3_c17_restore_verify"
OUT_ZIP = ROOT / "Release/SPECTER_MASTER_DATA_USA_E3_C17_RESTORE.zip"
OUT_HASH = ROOT / "Release/DATA_USA_E3_C17_RESTORE_HASHES.txt"
OUT_URL = ROOT / "Release/DATA_USA_E3_C17_RESTORE_DOWNLOAD.txt"
OUT_REPORT = ROOT / "Release/DATA_USA_E3_C17_RESTORE_REPORT.txt"
SRC_DIR = ROOT / "Data/INI/Object/Specter/United States Of America"

GOOD_CSF = "e5be6c4e3bc96eb0792592c2bd6a3edc0e8a094d531024dfb50b0626fc1484b3"
AC130_SHA = "6933bbca1f6e036324e159170c369b2be523017a678b4b39dd88535a3a75343a"

E737_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE737Visual.ini"
)
E2_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE2Visual.ini"
)
E3_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3Visual.ini"
)
C17_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetC17Visual.ini"
)
AC130_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetAC130.ini"
)
V22_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetV22Visual.ini"
)
HEAVY_KEY = (
    "Data\\INI\\Object\\Specter\\United States Of America\\Buildings\\"
    "America_HeavyAirBase.ini"
)
CS_KEY = "Data\\INI\\CommandSet.ini"
CB_KEY = "Data\\INI\\CommandButton.ini"
CSF_KEY = "Data\\English\\generals.csf"

FREEZE_KEYS = [
    CSF_KEY,
    E737_KEY,
    E2_KEY,
    AC130_KEY,
    V22_KEY,
    HEAVY_KEY,
    "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetB21Clean.ini",
    "Data\\INI\\Object\\Specter\\United States Of America\\Airforce\\B1R.ini",
]

E3_BUTTON = """CommandButton Command_ConstructAmericaJetE3Visual
  Command       = UNIT_BUILD
  Object        = AmericaJetE3Visual
  TextLabel     = CONTROLBAR:AmericaAWACS
  ButtonImage   = E3USA
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:AmericaAWACS
End
"""

C17_BUTTON = """CommandButton Command_ConstructAmericaJetC17Visual
  Command       = UNIT_BUILD
  Object        = AmericaJetC17Visual
  TextLabel     = CONTROLBAR:ConstructAmericaVehicleStarlifter
  ButtonImage   = C17GlobalMaster
  ButtonBorderType = BUILD
  DescriptLabel = CONTROLBAR:ConstructAmericaVehicleStarlifter
End
"""

E3_OBJECT = r""";==============================================================================
; AmericaJetE3Visual - USA E-3 AWACS (VISUAL / BASE ONLY) RESTORED
; Specter-safe structure + donor ART. Flight template = AmericaJetE737Visual.
; Donor DATA = NOT USED. Weapons = NONE.
; Primary W3D = E3
;==============================================================================

Object AmericaJetE3Visual

  SelectPortrait         = E3USA
  ButtonImage            = E3USA

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes

    DefaultConditionState
      Model = E3
    End

    ConditionState = JETEXHAUST
      Model = E3
    End

    ConditionState = REALLYDAMAGED
      Model = E3
    End

    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = E3
    End

    ConditionState = RUBBLE
      Model = E3
    End
  End

  DisplayName = OBJECT:Airfield
  EditorSorting = VEHICLE
  Side = America
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300
  Prerequisites
  End
  Buildable = Ignore_Prerequisites

  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End

  BuildCost = 6000
  BuildTime = 45
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericTacticalBomberCommandSet

  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = AdvancedFightEngineLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = RaptorVoiceCreate
    SoundEject = PilotSoundEject
    VoiceEject = PilotVoiceEject
    Afterburner = RaptorAfterburner
    VoiceLowFuel = RaptorVoiceLowFuel
    VoiceGarrison = RaptorVoiceMove
  End

  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT

  Body = ActiveBody ModuleTag_02
    MaxHealth = 400.0
    InitialHealth = 400.0
  End

  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
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
    Mass = 500.0
  End

  Behavior = TransitionDamageFX ModuleTag_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End

  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End
  Locomotor = SET_NORMAL F100_PW_229
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor

  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End

  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""

C17_OBJECT = r""";==============================================================================
; AmericaJetC17Visual - USA C-17 Globemaster (VISUAL / BASE ONLY) RESTORED
; Specter-safe structure + donor ART. Flight template = AmericaJetE737Visual.
; Donor DATA = NOT USED. Weapons = NONE. Cargo = NOT YET.
; Primary W3D = IUAC17HXNew
;==============================================================================

Object AmericaJetC17Visual

  SelectPortrait         = C17GlobalMaster
  ButtonImage            = C17GlobalMaster

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes

    DefaultConditionState
      Model = IUAC17HXNew
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = Engine02 JetBlackTrailThin
      ParticleSysBone = Engine03 JetBlackTrailThin
      ParticleSysBone = Engine04 JetBlackTrailThin
    End

    ConditionState = JETEXHAUST
      Model = IUAC17HXNew
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = Engine02 JetBlackTrailThin
      ParticleSysBone = Engine03 JetBlackTrailThin
      ParticleSysBone = Engine04 JetBlackTrailThin
    End

    ConditionState = REALLYDAMAGED
      Model = IUAC17HXNew
      ParticleSysBone = Smoke01 JetSmoke
    End

    ConditionState = REALLYDAMAGED JETEXHAUST
      Model = IUAC17HXNew
      ParticleSysBone = Smoke01 JetSmoke
      ParticleSysBone = Engine01 JetBlackTrailThin
      ParticleSysBone = Engine02 JetBlackTrailThin
    End

    ConditionState = RUBBLE
      Model = IUAC17HXNew
    End
  End

  DisplayName = OBJECT:Starlifter
  EditorSorting = VEHICLE
  Side = America
  TransportSlotCount = 0
  VisionRange = 300.0
  ShroudClearingRange = 300
  Prerequisites
  End
  Buildable = Ignore_Prerequisites

  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End

  BuildCost = 7000
  BuildTime = 50
  ExperienceValue = 50 50 100 150
  IsTrainable = No
  CommandSet = GenericTacticalBomberCommandSet

  VoiceSelect = RaptorVoiceSelect
  VoiceMove = RaptorVoiceMove
  VoiceGuard = RaptorVoiceAirPatrol
  SoundAmbient = AdvancedFightEngineLoop
  SoundAmbientRubble = NoSound
  UnitSpecificSounds
    VoiceCreate = RaptorVoiceCreate
    SoundEject = PilotSoundEject
    VoiceEject = PilotVoiceEject
    Afterburner = RaptorAfterburner
    VoiceLowFuel = RaptorVoiceLowFuel
    VoiceGarrison = RaptorVoiceMove
  End

  RadarPriority = UNIT
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT

  Body = ActiveBody ModuleTag_02
    MaxHealth = 500.0
    InitialHealth = 500.0
  End

  Behavior = JetSlowDeathBehavior ModuleTag_05
    FXOnGroundDeath = FX_JetOnGroundDeath
    OCLOnGroundDeath = OCL_RaptorDeathFinalBlowUp
    DestructionDelay = 99999999
    RollRate = 0.2
    RollRateDelta = 100%
    PitchRate = 0.0
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
    Mass = 500.0
  End

  Behavior = TransitionDamageFX ModuleTag_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End

  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End
  Locomotor = SET_NORMAL F100_PW_229
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor

  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End

  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 10.0
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def sha256(b: bytes | Path) -> str:
    data = b if isinstance(b, bytes) else Path(b).read_bytes()
    return hashlib.sha256(data).hexdigest()


def read_big(path: Path) -> dict[str, bytes]:
    data = path.read_bytes()
    assert data[:4] == b"BIGF"
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


def write_tree(file_map: dict[str, bytes], root: Path) -> None:
    if root.exists():
        shutil.rmtree(root)
    for name, content in file_map.items():
        path = root / name.replace("\\", "/")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def read_tree(root: Path) -> dict[str, bytes]:
    out = {}
    for p in root.rglob("*"):
        if p.is_file():
            out[str(p.relative_to(root)).replace("/", "\\")] = p.read_bytes()
    return out


def count_obj(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^Object\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def count_btn(dmap: dict[str, bytes], name: str) -> int:
    pat = re.compile(rf"(?m)^CommandButton\s+{re.escape(name)}\s*$")
    return sum(
        len(pat.findall(v.decode("latin1")))
        for k, v in dmap.items()
        if k.lower().endswith(".ini")
    )


def upsert_button(cb: str, name: str, block: str) -> str:
    m = re.search(
        rf"(?ms)^CommandButton\s+{re.escape(name)}\s*\n(.*?)(?=^CommandButton\s+\S+\s*$|\Z)",
        cb,
    )
    if m:
        return cb[: m.start()] + block + cb[m.end() :]
    # insert near other AmericaJet visual construct buttons
    anchor = re.search(
        r"(?ms)^CommandButton\s+Command_ConstructAmericaJetE737Visual\s*\n.*?^End\s*$",
        cb,
    )
    if not anchor:
        anchor = re.search(
            r"(?ms)^CommandButton\s+Command_ConstructAmericaJetAC130\s*\n.*?^End\s*$",
            cb,
        )
    assert anchor
    return cb[: anchor.end()] + "\n\n" + block + cb[anchor.end() :]


def ensure_heavy_slots(cs: str) -> str:
    m = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)(?=^CommandSet\s+\S+\s*$|\Z)",
        cs,
    )
    if not m:
        raise SystemExit("America_HeavyAirBaseCommandSet missing")
    block = m.group(0)
    # required slots
    required = {
        "5": "Command_ConstructAmericaJetE3Visual",
        "8": "Command_ConstructAmericaJetC17Visual",
    }
    new_block = block
    for slot, btn in required.items():
        if re.search(rf"(?m)^\s*{slot}\s*=\s*{re.escape(btn)}\s*$", new_block):
            continue
        # replace existing slot line if present
        if re.search(rf"(?m)^\s*{slot}\s*=\s*\S+\s*$", new_block):
            new_block, n = re.subn(
                rf"(?m)^(\s*{slot}\s*=\s*)\S+(\s*)$",
                rf"\1{btn}\2",
                new_block,
                count=1,
            )
            assert n == 1
        else:
            raise SystemExit(f"slot {slot} missing entirely")
    # freeze other expected slots
    assert "1  = Command_ConstructAmericaJetB2Spirit" in new_block or re.search(
        r"(?m)^\s*1\s*=\s*Command_ConstructAmericaJetB2Spirit\s*$", new_block
    )
    assert re.search(
        r"(?m)^\s*9\s*=\s*Command_ConstructAmericaJetE737Visual\s*$", new_block
    )
    assert re.search(
        r"(?m)^\s*7\s*=\s*Command_ConstructAmericaJetAC130\s*$", new_block
    )
    return cs[: m.start()] + new_block + cs[m.end() :]


def upload_zip(path: Path) -> str:
    proc = subprocess.run(
        [
            "curl",
            "-sF",
            "reqtype=fileupload",
            "-F",
            "time=72h",
            "-F",
            f"fileToUpload=@{path}",
            "https://litterbox.catbox.moe/resources/internals/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    url = (proc.stdout or "").strip()
    if url.startswith("http"):
        return url
    servers = json.loads(
        subprocess.run(
            ["curl", "-s", "https://api.gofile.io/servers"],
            capture_output=True,
            text=True,
            timeout=60,
        ).stdout
    )
    server = servers["data"]["servers"][0]["name"]
    up = subprocess.run(
        [
            "curl",
            "-s",
            "-F",
            f"file=@{path}",
            f"https://{server}.gofile.io/uploadFile",
        ],
        capture_output=True,
        text=True,
        timeout=600,
    )
    data = json.loads(up.stdout)
    return data["data"]["downloadPage"]


def main() -> None:
    dmap = read_big(DATA_BIG)
    amap = read_big(ART_BIG)
    assert sha256(dmap[CSF_KEY]) == GOOD_CSF
    # AC130 may have been modified by flight template; freeze file bytes from current
    freeze = {k: dmap[k] for k in FREEZE_KEYS if k in dmap}

    # Pre-audit
    pre = {
        "e3_obj": count_obj(dmap, "AmericaJetE3Visual"),
        "c17_obj": count_obj(dmap, "AmericaJetC17Visual"),
        "e3_btn": count_btn(dmap, "Command_ConstructAmericaJetE3Visual"),
        "c17_btn": count_btn(dmap, "Command_ConstructAmericaJetC17Visual"),
        "stale_e3awacs": count_obj(dmap, "AmericaJetE3AWACS"),
        "stale_usae3": count_obj(dmap, "USAE3"),
    }
    cs_before = dmap[CS_KEY].decode("latin1")
    m = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)(?=^CommandSet\s+\S+\s*$|\Z)",
        cs_before,
    )
    pre_slot5 = re.search(r"(?m)^\s*5\s*=\s*(\S+)", m.group(0)).group(1)
    pre_slot8 = re.search(r"(?m)^\s*8\s*=\s*(\S+)", m.group(0)).group(1)

    assert "Art\\W3D\\E3.W3D" in amap
    assert "Art\\W3D\\IUAC17HXNew.W3D" in amap
    assert "Art\\Textures\\E3USA.tga" in amap or "Art\\Textures\\E3USATB.tga" in amap
    assert "Art\\Textures\\C17GlobalMasterTB.tga" in amap
    assert "Art\\Textures\\avE3.tga" in amap

    e737 = dmap[E737_KEY].decode("latin1")
    e2 = dmap[E2_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*Scale\s*=\s*0\.8\s*$", e737)
    assert re.search(r"(?m)^\s*Scale\s*=\s*3\.932\s*$", e2)
    assert "Locomotor = SET_NORMAL F100_PW_229" in e737

    # Write restored objects
    dmap[E3_KEY] = E3_OBJECT.encode("latin1")
    dmap[C17_KEY] = C17_OBJECT.encode("latin1")

    # Buttons in ACTIVE CommandButton.ini
    cb = dmap[CB_KEY].decode("latin1")
    cb = upsert_button(cb, "Command_ConstructAmericaJetE3Visual", E3_BUTTON)
    cb = upsert_button(cb, "Command_ConstructAmericaJetC17Visual", C17_BUTTON)
    dmap[CB_KEY] = cb.encode("latin1")

    # CommandSet slots
    cs = ensure_heavy_slots(dmap[CS_KEY].decode("latin1"))
    dmap[CS_KEY] = cs.encode("latin1")

    # Remove stale broken objects if any
    for stale in (
        "Data\\INI\\Object\\Specter\\United States Of America\\AmericaJetE3AWACS.ini",
        "Data\\INI\\Object\\Specter\\United States Of America\\USAE3.ini",
    ):
        if stale in dmap:
            del dmap[stale]

    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "AmericaJetE3Visual.ini").write_bytes(dmap[E3_KEY])
    (SRC_DIR / "AmericaJetC17Visual.ini").write_bytes(dmap[C17_KEY])

    if STAGE.exists():
        shutil.rmtree(STAGE)
    write_tree(dmap, STAGE / "in")
    staged = read_tree(STAGE / "in")
    for k, blob in freeze.items():
        assert staged[k] == blob, f"freeze mutated: {k}"
    new_data = build_big(staged)
    DATA_BIG.write_bytes(new_data)

    if VERIFY.exists():
        shutil.rmtree(VERIFY)
    vmap = read_big(DATA_BIG)
    write_tree(vmap, VERIFY / "out")

    for k, blob in freeze.items():
        assert vmap[k] == blob, f"freeze broken: {k}"
    assert sha256(vmap[CSF_KEY]) == GOOD_CSF

    assert count_obj(vmap, "AmericaJetE3Visual") == 1
    assert count_obj(vmap, "AmericaJetC17Visual") == 1
    assert count_obj(vmap, "AmericaJetE3AWACS") == 0
    assert count_obj(vmap, "USAE3") == 0
    assert count_btn(vmap, "Command_ConstructAmericaJetE3Visual") == 1
    assert count_btn(vmap, "Command_ConstructAmericaJetC17Visual") == 1

    cs2 = vmap[CS_KEY].decode("latin1")
    m2 = re.search(
        r"(?ms)^CommandSet\s+America_HeavyAirBaseCommandSet\s*\n(.*?)(?=^CommandSet\s+\S+\s*$|\Z)",
        cs2,
    )
    assert re.search(
        r"(?m)^\s*5\s*=\s*Command_ConstructAmericaJetE3Visual\s*$", m2.group(0)
    )
    assert re.search(
        r"(?m)^\s*8\s*=\s*Command_ConstructAmericaJetC17Visual\s*$", m2.group(0)
    )

    cb2 = vmap[CB_KEY].decode("latin1")
    for name, obj in (
        ("Command_ConstructAmericaJetE3Visual", "AmericaJetE3Visual"),
        ("Command_ConstructAmericaJetC17Visual", "AmericaJetC17Visual"),
    ):
        mm = re.search(
            rf"(?ms)^CommandButton\s+{re.escape(name)}\s*\n(.*?)(?=^CommandButton\s+\S+\s*$|\Z)",
            cb2,
        )
        assert mm and f"Object        = {obj}" in mm.group(0)
        assert "UNIT_BUILD" in mm.group(0)

    e3 = vmap[E3_KEY].decode("latin1")
    c17 = vmap[C17_KEY].decode("latin1")
    assert "Model = E3" in e3
    assert "Model = IUAC17HXNew" in c17
    assert "Locomotor = SET_NORMAL F100_PW_229" in e3
    assert "Locomotor = SET_NORMAL F100_PW_229" in c17
    assert "WeaponSet" not in e3 and "WeaponSet" not in c17
    assert "TransportContain" not in c17
    assert re.search(r"(?m)^\s*Scale\s*=\s*0\.8\s*$", vmap[E737_KEY].decode("latin1"))
    assert re.search(r"(?m)^\s*Scale\s*=\s*3\.932\s*$", vmap[E2_KEY].decode("latin1"))
    heavy = vmap[HEAVY_KEY].decode("latin1")
    assert re.search(r"(?m)^\s*NumRows\s*=\s*3\s*$", heavy)
    assert re.search(r"(?m)^\s*NumCols\s*=\s*2\s*$", heavy)

    report = []
    report.append("USA E3 + C17 RESTORE = PASS (structural readiness)")
    report.append("")
    report.append("PRE-AUDIT (packed runtime before restore rewrite):")
    report.append(f"AmericaJetE3Visual Object count = {pre['e3_obj']}")
    report.append(f"AmericaJetC17Visual Object count = {pre['c17_obj']}")
    report.append(f"E-3 build button count = {pre['e3_btn']}")
    report.append(f"C-17 build button count = {pre['c17_btn']}")
    report.append(f"America_HeavyAirBaseCommandSet Slot 5 = {pre_slot5}")
    report.append(f"America_HeavyAirBaseCommandSet Slot 8 = {pre_slot8}")
    report.append(f"Stale AmericaJetE3AWACS = {pre['stale_e3awacs']}")
    report.append(f"Stale USAE3 = {pre['stale_usae3']}")
    report.append("")
    report.append("E-3:")
    report.append("Object = AmericaJetE3Visual")
    report.append("W3D = E3")
    report.append("BuildButton = Command_ConstructAmericaJetE3Visual")
    report.append("HeavyAirBase Slot = 5")
    report.append("Donor ART = YES")
    report.append("Donor DATA = NO")
    report.append("Build chain resolves = YES")
    report.append("Flight template = AmericaJetE737Visual")
    report.append("Weapons = NONE")
    report.append("")
    report.append("C-17:")
    report.append("Object = AmericaJetC17Visual")
    report.append("W3D = IUAC17HXNew")
    report.append("BuildButton = Command_ConstructAmericaJetC17Visual")
    report.append("HeavyAirBase Slot = 8")
    report.append("Donor ART = YES")
    report.append("Donor DATA = NO")
    report.append("E-737 flight structure used = YES")
    report.append("Build chain resolves = YES")
    report.append("Weapons = NONE")
    report.append("Cargo = NOT YET")
    report.append("")
    report.append("POST-VERIFY:")
    report.append(
        f"AmericaJetE3Visual = {count_obj(vmap, 'AmericaJetE3Visual')}"
    )
    report.append(
        f"AmericaJetC17Visual = {count_obj(vmap, 'AmericaJetC17Visual')}"
    )
    report.append(
        f"Command_ConstructAmericaJetE3Visual = {count_btn(vmap, 'Command_ConstructAmericaJetE3Visual')}"
    )
    report.append(
        f"Command_ConstructAmericaJetC17Visual = {count_btn(vmap, 'Command_ConstructAmericaJetC17Visual')}"
    )
    report.append("")
    report.append("E-737 Scale = 0.8 preserved = YES")
    report.append("E-2 Scale = 3.932 preserved = YES")
    report.append("HeavyAirBase 3+3 changed = NO")
    report.append("Other aircraft changed = NO")
    report.append("Other factions changed = NO")
    report.append("ART changed = NO")
    report.append(f"DATA sha256 = {sha256(DATA_BIG)}")
    report.append(
        "NOTE = In-game button/aircraft not launched here; structural readiness only."
    )

    text = "\n".join(report) + "\n"
    OUT_REPORT.write_text(text, encoding="utf-8")
    (VERIFY / "VERIFY.txt").write_text(text, encoding="utf-8")

    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(DATA_BIG, "_SPEC_DATA_ONE.big")
    with zipfile.ZipFile(OUT_ZIP) as z:
        assert z.namelist() == ["_SPEC_DATA_ONE.big"]

    OUT_HASH.write_text(
        f"_SPEC_DATA_ONE.big sha256={sha256(DATA_BIG)}\nZIP={OUT_ZIP.name}\n",
        encoding="utf-8",
    )
    url = upload_zip(OUT_ZIP)
    OUT_URL.write_text(url + "\n", encoding="utf-8")
    print(text)
    print("Download =", url)


if __name__ == "__main__":
    main()
