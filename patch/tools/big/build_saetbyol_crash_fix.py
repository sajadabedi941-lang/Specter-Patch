#!/usr/bin/env python3
"""Replace only NorthKoreaUAVSaetbyol.ini in the global-update DATA BIG.

Crash causes in the previous clone:
1) VisionRange/ShroudClearingRange regex wrote garbage tokens I00 / J00
   (Python replacement \\11100 parsed as octal 'I' + '00').
2) E3 four-engine ParticleSysBones (ENGINE01-04) on AVReaper, which only
   has Wingtip/CHASSIS bones like the working Dozor-600 draw.
3) Invented AVReaper.AVReaper animation (packed Dozor does not use it).
4) Side = France leftover. E3G_CommandSet includes BGM109 strike.
"""
from __future__ import annotations

import hashlib
import re
import struct
from pathlib import Path

SRC_DATA = Path("/tmp/aircraft_global_update/_SPEC_DATA_ONE.big")
SRC_ART = Path("/tmp/aircraft_global_update/_SPEC_ART_ONE.big")
OUT_DIR = Path("/tmp/saetbyol_crash_fix")
TARGET = r"data\ini\object\specter\north korea\airforce\northkoreauavsaetbyol.ini"

SAETBYOL_INI = """Object NorthKoreaUAVSaetbyol
Scale = 1.45

  SelectPortrait         = Dozor600
  ButtonImage            = Dozor600

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor = Yes

    DefaultConditionState
      Model               = AVReaper
    End

    ConditionState        = JETEXHAUST
      Model               = AVReaper
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = JETEXHAUST JETAFTERBURNER
      Model               = AVReaper
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = REALLYDAMAGED
      Model               = AVReaper_D
      ParticleSysBone     = CHASSIS JetSmoke
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = AVReaper_D
      ParticleSysBone     = CHASSIS JetSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = AVReaper_D
      ParticleSysBone     = CHASSIS JetSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End

    ConditionState        = RUBBLE
      Model               = AVReaper_D1
      HideSubObject       = None
      ShowSubObject       = None
    End
  End

  DisplayName         = OBJECT:NorthKoreaUAVSaetbyol
  EditorSorting       = VEHICLE
  Side                = NorthKorea
  TransportSlotCount  = 0
  VisionRange         = 1100
  ShroudClearingRange = 1200
  BuildCost           = 4200
  BuildTime           = 36.0
  ExperienceValue     = 50 50 100 150
  IsTrainable         = No
  CommandSet          = AmericaE3AWACSCommandSet

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
  KindOf = PRELOAD CAN_CAST_REFLECTIONS SELECTABLE VEHICLE SCORE AIRCRAFT REVEALS_ENEMY_PATHS

  ArmorSet
    Conditions = None
    Armor = AirplaneArmor
    DamageFX = None
  End

  Body = ActiveBody ModuleTag_02
    MaxHealth     = 1100.0
    InitialHealth = 1100.0
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
    Mass = 350.0
  End

  Behavior = TransitionDamageFX ModuleTag_08
    ReallyDamagedParticleSystem1 = Bone:Smoke RandomBone:Yes PSys:SmokeSmallContinuous01
    ReallyDamagedFXList1 = Loc: X:0 Y:0 Z:0 FXList:FX_MIGDamageTransition
  End

  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 5
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 500
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 3
  End
  Locomotor = SET_NORMAL Saturn_AL-41F
  Locomotor = SET_TAXIING BasicJetTaxiLocomotor

  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End

  Behavior = StealthDetectorUpdate ModuleTag_AWACS_StealthDetect
    DetectionRate  = 1500
    DetectionRange = 3600
    CanDetectWhileGarrisoned = No
    CanDetectWhileContained  = No
    ExtraForbiddenKindOf = UNATTACKABLE
  End

  Behavior = OCLSpecialPower ModuleTag_E3_SAR
    SpecialPowerTemplate = AmericaE3TargetedSARScan
    OCL                  = OCL_AmericaE3TargetedSARScan
    CreateLocation       = CREATE_AT_LOCATION
  End

  Geometry            = Box
  GeometryIsSmall     = Yes
  GeometryMajorRadius = 18.0
  GeometryMinorRadius = 9.0
  GeometryHeight      = 6.0
  Shadow              = SHADOW_VOLUME
  ShadowSizeX         = 72
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


BLOCK_OPEN = re.compile(
    r"(?i)^\s*(Object(?:Reskin)?\s+\S+|Draw\s*=|DefaultConditionState\b|"
    r"ConditionState\s*=|Behavior\s*=|Body\s*=|ArmorSet\b|WeaponSet\b|"
    r"UnitSpecificSounds\b|Prerequisites\b)"
)


def validate_ini(text: str) -> list[str]:
    errors = []
    # garbage tokens from the broken regex
    for tok in ("I00", "J00"):
        if re.search(rf"(?m)^{tok}\b", text) or re.search(rf"(?m)^\s+{tok}\b", text):
            errors.append(f"garbage token {tok}")
    depth = 0
    stack = []
    for i, raw in enumerate(text.splitlines(), 1):
        line = raw.split(";", 1)[0].rstrip()
        if not line.strip():
            continue
        if re.match(r"(?i)^\s*End\b", line):
            if depth <= 0:
                errors.append(f"line {i}: extra End")
            else:
                depth -= 1
                stack.pop()
            continue
        if BLOCK_OPEN.match(line):
            depth += 1
            stack.append((i, line.strip()[:60]))
            continue
        if "=" not in line and not re.match(r"(?i)^\s*(Object|End)\b", line):
            # Scale at object root is Scale = x; already has =
            errors.append(f"line {i}: not a key=value or block: {line.strip()[:80]}")
    if depth != 0:
        errors.append(f"unclosed blocks depth={depth} last={stack[-1:]}")
    if "Object NorthKoreaUAVSaetbyol" not in text:
        errors.append("missing Object NorthKoreaUAVSaetbyol")
    if "CAN_ATTACK" in text:
        errors.append("CAN_ATTACK present")
    if re.search(r"(?im)^WeaponSet\b", text) or re.search(r"(?im)^\s*WeaponSet\b", text):
        errors.append("WeaponSet present")
    if re.search(r"(?im)^\s*Weapon\s*=", text):
        errors.append("Weapon = present")
    if "REVEALS_ENEMY_PATHS" not in text:
        errors.append("missing REVEALS_ENEMY_PATHS")
    if "StealthDetectorUpdate" not in text:
        errors.append("missing StealthDetectorUpdate")
    if not re.search(r"(?im)^\s*VisionRange\s*=", text):
        errors.append("missing VisionRange")
    if not re.search(r"(?im)^\s*ShroudClearingRange\s*=", text):
        errors.append("missing ShroudClearingRange")
    if re.search(r"(?im)ENGINE0[3-4]", text):
        errors.append("E3 engine bones on AVReaper")
    if "AVReaper.AVReaper" in text:
        errors.append("invalid AVReaper.AVReaper animation")
    if "Side                = France" in text or re.search(r"(?im)^\s*Side\s*=\s*France\b", text):
        errors.append("Side still France")
    if "AmericaE3AWACSCommandSet" not in text:
        errors.append("CommandSet not AmericaE3AWACSCommandSet")
    return errors


def main() -> int:
    errors = validate_ini(SAETBYOL_INI)
    print("=== INI PARSER ===")
    if errors:
        for e in errors:
            print(" FAIL", e)
        return 1
    print("INI_PARSE_OK")

    data_entries = parse_big(SRC_DATA)
    art_entries = parse_big(SRC_ART)
    found = False
    out_data = []
    blob = SAETBYOL_INI.replace("\n", "\r\n").encode("latin1")
    for n, b in data_entries:
        key = n.replace("/", "\\").lower()
        if key == TARGET:
            out_data.append((n, blob))
            found = True
            print("replaced", n, "old", len(b), "new", len(blob))
        else:
            out_data.append((n, b))
    if not found:
        print("TARGET MISSING")
        return 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    data_big = build_big_ordered(out_data)
    art_big = build_big_ordered(art_entries)
    (OUT_DIR / "_SPEC_DATA_ONE.big").write_bytes(data_big)
    (OUT_DIR / "_SPEC_ART_ONE.big").write_bytes(art_big)
    dsha = hashlib.sha256(data_big).hexdigest()
    asha = hashlib.sha256(art_big).hexdigest()
    print("DATA", dsha, len(data_big))
    print("ART ", asha, len(art_big), "(unchanged bytes from source ART)")
    (OUT_DIR / "SHA256.txt").write_text(f"DATA {dsha}\nART  {asha}\n")
    Path("/opt/cursor/artifacts/saetbyol_ini_parse.txt").write_text(
        "INI_PARSE_OK\n" + "\n".join(SAETBYOL_INI.splitlines()[:8]) + "\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
