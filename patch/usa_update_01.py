#!/usr/bin/env python3
"""SPECTER1 USA Update 01.

Baseline: current follow-up _SPEC_DATA_ONE.big + original SPECTER1 _SPEC_ART_ONE.big.
Does not restart from clean SPECTER1 DATA. Does not import donor DATA.
"""
from __future__ import annotations

import hashlib
import re
import struct
import zipfile
from pathlib import Path

SRC_DATA = Path("/workspace/patch/Release/SPECTER1_IRAQ_LIVEPATH/_SPEC_DATA_ONE.big")
SRC_ART = Path(
    "/tmp/SPECTER1_IRAQ_LIVE_20260914/SPECTER FINAL (GeneralsMode.com)/_SPEC_ART_ONE.big"
)
DONOR_DIR = Path("/tmp/donor_heli")
OUT_DIR = Path("/tmp/SPECTER1_USA_UPDATE_01")
WS_OUT = Path("/workspace/patch/Release/SPECTER1_USA_UPDATE_01")

P_F117 = r"Data\INI\Object\Specter\United States Of America\AmericaJetF117Clean.ini"
P_EA6 = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaJetF18Prowler.ini"
P_F35 = r"Data\INI\Object\Specter\United States Of America\Airforce\F35C_AA.ini"
P_C17 = r"Data\INI\Object\Specter\United States Of America\AmericaJetC17Visual.ini"
P_AIRFIELD = r"Data\INI\Object\Specter\United States Of America\Buildings\Airfield.ini"
P_LARGE = r"Data\INI\Object\Specter\United States Of America\Buildings\America_LargeAirBase.ini"
P_HEAVY = r"Data\INI\Object\Specter\United States Of America\Buildings\America_HeavyAirBase.ini"
P_AN124 = r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\RussiaJetAn124.ini"
P_CSF = r"Data\English\generals.csf"
P_CMDSET = r"Data\INI\CommandSet.ini"
P_CMDBTN = r"Data\INI\CommandButton.ini"
P_AH1Z = r"Data\INI\Object\Specter\United States Of America\Airforce\AmericaHelicopterAH1Z.ini"
P_USA01 = r"Data\INI\Object\Specter\United States Of America\USA_Update_01.ini"

IRAQ_PROTECTED = [
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_MirageF1-Bq.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MK.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\Iraq_Su-24MR.ini",
    r"Data\INI\Object\Specter\Iraq Army\Airforce\IraqJetL159.ini",
    r"Data\INI\Object\Specter\Iraq Army\Wheeled\AbbasLauncher.ini",
    r"Data\INI\Object\Specter\Iraq Army\APC\BTR90.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_LargeAirBase.ini",
    r"Data\INI\Object\Specter\Iraq Army\Buildings\Iraq_HeavyAirBase.ini",
    r"Data\INI\Object\Specter\Armed Forces Of Russian Federation\Airforce\TU22M3M.ini",
]

F35_HIDE = "JAFTERBURNED CYLINDER02 CYLINDER03 TURBO EX01 EX02"

USA01_INI = """; SPECTER1 USA Update 01
; Unique CommandButton / CommandSet / MappedImage names.
; INIZHZ cannot last-win these names. No donor DATA.

MappedImage AH1ZTB
  Texture = AH1ZTB.tga
  TextureWidth = 150
  TextureHeight = 118
  Coords = Left:0 Top:0 Right:150 Bottom:118
  Status = NONE
End

CommandButton Command_ConstructAmericaHelicopterAH1Z
  Command       = UNIT_BUILD
  Object        = AmericaHelicopterAH1Z
  TextLabel     = CONTROLBAR:ConstructAmericaHelicopterAH1Z
  ButtonImage   = AH1ZTB
  ButtonBorderType        = BUILD
  DescriptLabel           = CONTROLBAR:ToolTipAmericaHelicopterAH1Z
End

; INIZHZ AmericaAirfieldCommandSet with $1600 Strike Eagle (AuterF22) removed
; from slot 6. Other live Airfield slots unchanged.
CommandSet AmericaAirfieldCommandSet_USA01
  1 = Command_ConstructAmericaJetRaptor
  2 = Command_ConstructAmericaVehicleComanche
  3 = Command_ConstructAmericaJetAurora
  4 = Command_ConstructAmericaJetStealthFighter
  5 = Command_ConstructAmericaJetF35C_AA
  6 = Command_ConstructAmericaHelicopterAH1Z
  7 = Command_UpgradeComancheRocketPods
  8 = Command_UpgradeAmericaLaserMissiles
  9 = Command_UpgradeAmericaCountermeasures
  10 = Command_UpgradeAmericaBunkerBusters
  13 = Command_SetRallyPoint
  14 = Command_Sell
End

; Follow-up DATA America_LargeAirBaseCommandSet with $1600 Strike Eagle
; (AuterF22) removed from slot 14. Other LargeAirBase slots unchanged.
CommandSet America_LargeAirBaseCommandSet_USA01
  1  = Command_ConstructAmericaJetRaptor
  2  = Command_ConstructAmericaVehicleComanche
  3  = Command_ConstructAmericaJetAurora
  4  = Command_ConstructAmericaJetA10C
  5  = Command_ConstructAmericaJetF-16C_AG
  6  = Command_ConstructAmericaJetF-15E_AA
  7  = Command_ConstructAmericaJetF-22A_AA
  8  = Command_UpgradeAmericaCountermeasures
  9  = Command_ConstructAmericaJetF18Prowler
  10  = Command_ConstructAmericaJetEA18
  11  = Command_ConstructAmericaJetF35C
  12  = Command_ConstructAmericaJetF35C_AA
  13 = Command_ConstructAmericaJetF117
  14 = Command_ConstructAmericaHelicopterAH1Z
End
"""

AH1Z_INI = """;==============================================================================
; AmericaHelicopterAH1Z - AH-1Z Viper / Super Cobra
;
; ART  = donor LSFAH1Z family only (W3D + textures + cameo). No donor DATA.
; DATA = SPECTER1 USA AmericaVehicleComanche skeleton, without
;        turret-contain, object-swap upgrades, or extra spawn riders.
;==============================================================================

Object AmericaHelicopterAH1Z
Scale = 0.92
  SelectPortrait         = AH1ZTB
  ButtonImage            = AH1ZTB
  UpgradeCameo1 = Upgrade_AmericaCountermeasures

  Draw = W3DModelDraw ModuleTag_01
    OkToChangeModelColor               = Yes
    ProjectileBoneFeedbackEnabledSlots = PRIMARY
    DefaultConditionState
      Model                           = LSFAH1Z
      Animation                       = LSFAH1Z.LSFAH1Z
      AnimationMode                   = LOOP
      Turret                          = TURRET01
      WeaponMuzzleFlash               = PRIMARY MUZZLE01
      WeaponFireFXBone                = PRIMARY MUZZLE01
      WeaponFireFXBone                = SECONDARY WEAPONB01
      WeaponLaunchBone                = SECONDARY MISSILE01
      WeaponFireFXBone                = TERTIARY ROCKETPOD01
      WeaponLaunchBone                = TERTIARY ROCKETPOD01
    End
    ConditionState = REALLYDAMAGED
      Model                           = LSFAH1Zd
      Animation                       = LSFAH1Zd.LSFAH1Zd
      AnimationMode                   = LOOP
      Turret                          = TURRET01
      WeaponMuzzleFlash               = PRIMARY MUZZLE01
      WeaponFireFXBone                = PRIMARY MUZZLE01
      WeaponFireFXBone                = SECONDARY WEAPONB01
      WeaponLaunchBone                = SECONDARY MISSILE01
      WeaponFireFXBone                = TERTIARY ROCKETPOD01
      WeaponLaunchBone                = TERTIARY ROCKETPOD01
    End
    ConditionState = RUBBLE
      Model                           = LSFAH1Zk
      Animation                       = LSFAH1Zk.LSFAH1Zk
      AnimationMode                   = LOOP
      Turret                          = TURRET01
      WeaponMuzzleFlash               = PRIMARY MUZZLE01
      WeaponFireFXBone                = PRIMARY MUZZLE01
      WeaponFireFXBone                = SECONDARY WEAPONB01
      WeaponLaunchBone                = SECONDARY MISSILE01
      WeaponFireFXBone                = TERTIARY ROCKETPOD01
      WeaponLaunchBone                = TERTIARY ROCKETPOD01
    End
    OkToChangeModelColor = Yes
  End

  DisplayName         = OBJECT:AmericaHelicopterAH1Z
  EditorSorting       = VEHICLE
  Side                = America
  TransportSlotCount  = 0
  VisionRange         = 650.0
  ShroudClearingRange = 550
  Prerequisites
  End
  WeaponSet
    Conditions          = None
    Weapon              = PRIMARY     GenericHeliGunnerSight
    PreferredAgainst    = PRIMARY     INFANTRY VEHICLE
    AutoChooseSources   = PRIMARY     FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon              = SECONDARY   8x_MRATGM_AGM114L
    PreferredAgainst    = SECONDARY   VEHICLE STRUCTURE
    AutoChooseSources   = SECONDARY   FROM_PLAYER FROM_SCRIPT FROM_AI
    Weapon              = TERTIARY    70mm_Hydra_AH64E
    PreferredAgainst    = TERTIARY    INFANTRY STRUCTURE VEHICLE
    AutoChooseSources   = TERTIARY    FROM_PLAYER FROM_SCRIPT FROM_AI
  End
  ArmorSet
    Conditions      = None
    Armor           = ComancheArmor_P
    DamageFX        = None
  End
  ArmorSet
    Conditions            = PLAYER_UPGRADE
    Armor                 = CountermeasuresComancheArmor_P
    DamageFX              = None
  End
  BuildCost           = 1500
  BuildTime           = 20
  ExperienceValue     = 50 50 100 200
  ExperienceRequired  = 0 100 200 400
  IsTrainable         = Yes
  CommandSet          = GenericAttackHelicopterHoverCommandSet

  VoiceSelect           = ComancheVoiceSelect
  VoiceMove             = ComancheVoiceMove
  VoiceGuard            = ComancheVoiceMove
  VoiceAttack           = ComancheVoiceAttack
  SoundAmbient          = ComancheAmbientLoop
  SoundAmbientRubble    = NoSound
  UnitSpecificSounds
    VoiceCreate         = ComancheVoiceCreate
    SoundEject          = PilotSoundEject
    VoiceEject          = PilotVoiceEject
    Afterburner         = RaptorAfterburner
    VoiceGarrison       = ComancheVoiceMove
    TurretMoveStart     = NoSound
    TurretMoveLoop      = NoSound
    VoiceFireRocketPods = ComancheVoiceAttackRocket
  End

  RadarPriority   = UNIT
  KindOf          = PRELOAD CAN_CAST_REFLECTIONS CAN_ATTACK SELECTABLE VEHICLE SCORE AIRCRAFT PRODUCED_AT_HELIPAD
  Behavior = ExperienceScalarUpgrade ModuleTag_03
    TriggeredBy = Upgrade_AmericaAdvancedTraining
    AddXPScalar = 1.0
  End
  Body = ActiveBody ModuleTag_04
    MaxHealth       = 520.0
    InitialHealth   = 520.0
  End
  Behavior = FXListDie ModuleTag_05
    DeathFX = FX_ComancheStartDeath
  End
  Behavior = JetAIUpdate ModuleTag_0v3321
    MinHeight                     = 10
    NeedsRunway                   = No
    KeepsParkingSpaceWhenAirborne = No
    AutoAcquireEnemiesWhenIdle    = Yes
    Turret
      TurretTurnRate              = 72
      TurretPitchRate             = 30
      MinPhysicalPitch            = -25
      AllowsPitch                 = No
      RecenterTime                = 120
      GroundUnitPitch             = -15
      ControlledWeaponSlots       = PRIMARY SECONDARY TERTIARY
    End
  End
  Locomotor = SET_NORMAL    T700_GE_701D_B2
  Locomotor = SET_TAXIING   BasicHelicopterTaxiLocomotor
  Behavior = PhysicsBehavior ModuleTag_07
    Mass = 50.0
  End
  Behavior = PointDefenseLaserUpdate ModuleTag_ALQ135
    WeaponTemplate        = AN/ALQ-135
    PrimaryTargetTypes    = SMALL_MISSILE BALLISTIC_MISSILE
    ScanRate              = 700
    ScanRange             = 350
    PredictTargetVelocityFactor = 3.0
  End
  Behavior = CreateObjectDie ModuleTag_Deletion
    DeathTypes   = NONE +EXTRA_6
    CreationList = None
  End
  Behavior = HelicopterSlowDeathBehavior ModuleTag_08
    DestructionDelay                = 99999999
    SpiralOrbitTurnRate             = 140.0
    SpiralOrbitForwardSpeed         = 350.0
    SpiralOrbitForwardSpeedDamping  = .9999
    MaxBraking                      = 190
    SoundDeathLoop                  = ComancheDamagedLoop
    MinSelfSpin                     = 100
    MaxSelfSpin                     = 300
    SelfSpinUpdateDelay             = 100
    SelfSpinUpdateAmount            = 10
    FallHowFast                     = 12.0%
    MinBladeFlyOffDelay             = 1500
    MaxBladeFlyOffDelay             = 1500
    AttachParticle                  = SootySmokeTrail
    AttachParticleBone              = ROTORS02
    BladeObjectName                 = ComancheBlades
    BladeBoneName                   = ROTOR
    FXBlade                         = FX_HelicopterBladeExplosion
    OCLBlade                        = OCL_HelicopterBladeExplosion
    FXHitGround                     = FX_HelicopterHitGround
    OCLHitGround                    = OCL_HelicopterHitGround
    FXFinalBlowUp                   = FX_GroundedHelicopterBlowUp
    OCLFinalBlowUp                  = OCL_GroundedHelicopterBlowUp
    DelayFromGroundToFinalDeath     = 1500
    FinalRubbleObject               = ComancheRubbleHull
  End
  Behavior                = ArmorUpgrade ModuleTag_Armor01
    TriggeredBy           = Upgrade_AmericaCountermeasures
  End
  Behavior                = CountermeasuresBehavior ModuleTag_10
    TriggeredBy           = Upgrade_AmericaCountermeasures
    FlareTemplateName     = CountermeasureFlare
    FlareBoneBaseName     = Flare
    VolleySize            = 2
    VolleyArcAngle        = 80.0
    VolleyVelocityFactor  = 3.0
    DelayBetweenVolleys   = 1000
    NumberOfVolleys       = 4
    ReloadTime            = 4000
    EvasionRate           = 30%
    ReactionLaunchLatency = 0
    MissileDecoyDelay     = 80
  End
  Behavior                = CountermeasuresBehavior ModuleTag_Chaff
    TriggeredBy           = Upgrade_AmericaCountermeasures
    FlareTemplateName     = CountermeasureCHAFF
    FlareBoneBaseName     = Flare
    VolleySize            = 2
    VolleyArcAngle        = 80.0
    VolleyVelocityFactor  = 5.0
    DelayBetweenVolleys   = 800
    NumberOfVolleys       = 3
    ReloadTime            = 3000
    EvasionRate           = 25%
    ReactionLaunchLatency = 0
    MissileDecoyDelay     = 70
  End
  Behavior = FlammableUpdate ModuleTag_21
    AflameDuration = 5000
    AflameDamageAmount = 3
    AflameDamageDelay = 500
  End
  Behavior = FireWeaponWhenDamagedBehavior ModuleTag_RS
    StartsActive                = Yes
    ReactionWeaponPristine      = RadarWaveEmitter
    ReactionWeaponDamaged       = RadarWaveEmitter
    ReactionWeaponReallyDamaged = RadarWaveEmitter
    ReactionWeaponRubble        = RadarWaveEmitter
    DamageTypes                 = NONE +MICROWAVE
  End
  Geometry = BOX
  GeometryMajorRadius = 25.0
  GeometryMinorRadius = 15.0
  GeometryHeight = 25.0
  GeometryIsSmall = No
  Shadow = SHADOW_VOLUME
  ShadowSizeX = 89
End
"""


def norm(name: str) -> str:
    return name.replace("/", "\\")


def read_big_list(path: Path) -> list[tuple[str, bytes]]:
    data = path.read_bytes()
    if data[:4] != b"BIGF":
        raise SystemExit(f"not BIGF: {path}")
    count = struct.unpack(">I", data[8:12])[0]
    pos = 16
    entries: list[tuple[str, bytes]] = []
    for _ in range(count):
        off, size = struct.unpack_from(">II", data, pos)
        pos += 8
        end = data.index(b"\x00", pos)
        name = data[pos:end].decode("latin1", errors="replace")
        pos = end + 1
        entries.append((name, data[off : off + size]))
    return entries


def build_big_ordered(entries: list[tuple[str, bytes]]) -> bytes:
    header_size = 16
    encoded_names: list[bytes] = []
    for name, _ in entries:
        nb = name.encode("latin1", errors="replace")
        encoded_names.append(nb)
        header_size += 8 + len(nb) + 1
    offset = header_size
    index = []
    blobs = []
    for (name, content), nb in zip(entries, encoded_names):
        content = bytes(content)
        index.append((nb, offset, len(content)))
        blobs.append(content)
        offset += len(content)
    out = bytearray()
    out += b"BIGF"
    out += struct.pack(">I", offset)
    out += struct.pack(">I", len(entries))
    out += struct.pack(">I", header_size)
    for nb, off, size in index:
        out += struct.pack(">II", off, size)
        out += nb + b"\x00"
    for blob in blobs:
        out += blob
    return bytes(out)


def find_index(entries: list[tuple[str, bytes]], target: str) -> int:
    t = norm(target).lower()
    hits = [i for i, (n, _) in enumerate(entries) if norm(n).lower() == t]
    if len(hits) != 1:
        raise SystemExit(f"{target}: expected 1 packed path, got {len(hits)}")
    return hits[0]


def text_of(entries, target) -> str:
    return entries[find_index(entries, target)][1].decode("utf-8", errors="replace")


def bytes_of(entries, target) -> bytes:
    return entries[find_index(entries, target)][1]


def set_bytes(entries, target, blob: bytes) -> None:
    i = find_index(entries, target)
    name = entries[i][0]
    entries[i] = (name, blob)


def set_text(entries, target, text: str) -> None:
    set_bytes(entries, target, text.encode("utf-8"))


def file_nl(text: str) -> str:
    return "\r\n" if "\r\n" in text else "\n"


def to_nl(s: str, nl: str) -> str:
    return s.replace("\r\n", "\n").replace("\n", nl)


def must_replace_once(text: str, old: str, new: str, label: str) -> str:
    nl = file_nl(text)
    old = to_nl(old, nl)
    new = to_nl(new, nl)
    n = text.count(old)
    if n != 1:
        preview = repr(old)[:220]
        raise SystemExit(f"{label}: expected exactly 1 occurrence, got {n}; OLD={preview}")
    return text.replace(old, new, 1)


def must_replace_all(text: str, old: str, new: str, label: str, expected: int | None = None) -> str:
    nl = file_nl(text)
    old = to_nl(old, nl)
    new = to_nl(new, nl)
    n = text.count(old)
    if n == 0:
        raise SystemExit(f"{label}: expected replacements, got 0")
    if expected is not None and n != expected:
        raise SystemExit(f"{label}: expected {expected} occurrences, got {n}")
    return text.replace(old, new)


def xor_wcs(s: str) -> bytes:
    out = bytearray()
    for ch in s:
        out += struct.pack("<H", ord(ch) ^ 0xFFFF)
    return bytes(out)


def csf_append(csf: bytes, labels: dict[str, str]) -> bytes:
    magic, ver, nlab, nstr, unused, lang = struct.unpack_from("<4sIIIII", csf, 0)
    if magic != b" FSC":
        raise SystemExit(f"bad CSF magic {magic!r}")
    extra = bytearray()
    for label, value in labels.items():
        lb = label.encode("ascii")
        vb = xor_wcs(value)
        extra += b" LBL"
        extra += struct.pack("<II", 1, len(lb))
        extra += lb
        extra += b" RTS"
        extra += struct.pack("<I", len(value))
        extra += vb
    header = struct.pack("<4sIIIII", magic, ver, nlab + len(labels), nstr + len(labels), unused, lang)
    return header + csf[24:] + extra


def patch_f117(text: str) -> str:
    text = must_replace_once(text, "Scale = 0.9\n", "Scale = 1.04\n", "F117 scale")
    text = must_replace_once(
        text,
        "; Visual Scale 0.9 = same USA fighter scale as F-22A / A-10C / EA-18G.\n",
        "; Visual Scale 1.04 = previous 0.9 plus ~15% (USA Update 01).\n",
        "F117 scale comment",
    )
    return text


def patch_ea6(text: str) -> str:
    # Hide the EA6.W3D HOOK subobject. Volume-shadow of the arresting hook is the
    # long line beneath the aircraft in flight. Do not rewrite the W3D.
    text = must_replace_all(
        text,
        "      Model               = EA6\n",
        "      Model               = EA6\n      HideSubObject       = HOOK\n",
        "EA6 HideSubObject HOOK",
        expected=8,
    )
    text = must_replace_once(
        text,
        "  GeometryIsSmall       = Yes\n",
        "  GeometryIsSmall       = No\n",
        "EA6 GeometryIsSmall",
    )
    return text


def patch_f35(text: str) -> str:
    hide_line = f"      HideSubObject       = {F35_HIDE}\n"

    def add_hide_after_model(block_old: str, label: str) -> None:
        nonlocal text
        if hide_line.strip() in block_old:
            raise SystemExit(f"{label}: hide already present")
        # insert HideSubObject immediately after Model line
        lines = block_old.splitlines(True)
        out = []
        inserted = False
        for ln in lines:
            out.append(ln)
            if (not inserted) and "Model" in ln and "AVLightn" in ln:
                out.append(hide_line if file_nl(text) == "\n" else hide_line.replace("\n", "\r\n"))
                inserted = True
        if not inserted:
            raise SystemExit(f"{label}: no Model line")
        new = "".join(out)
        if text.count(block_old) != 1:
            raise SystemExit(f"{label}: unique block missing")
        text = text.replace(block_old, new, 1)

    # Default / rider states with Model = AVLightn
    for old in (
        """    DefaultConditionState
      Model               = AVLightn
      WeaponLaunchBone    = PRIMARY LASERPL01
    End""",
        """    ConditionState        = RIDER1
      Model               = AVLightn
      WeaponLaunchBone    = PRIMARY LASERPL01
    End""",
        """    ConditionState        = RIDER2
      Model               = AVLightn
      WeaponLaunchBone    = PRIMARY LASERPL01
    End""",
    ):
        add_hide_after_model(old, "F35 default/rider")

    # Flying states without Model still need HideSubObject; ZH does not always inherit it.
    fly_states = [
        """    ConditionState        = JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End""",
        """    ConditionState        = RIDER1 JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End""",
        """    ConditionState        = RIDER2 JETEXHAUST
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End""",
        """    ConditionState        = JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End""",
        """    ConditionState        = RIDER1 JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End""",
        """    ConditionState        = RIDER2 JETEXHAUST JETAFTERBURNER
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
      ParticleSysBone     = Engine01 JetLenzflare
    End""",
    ]
    for old in fly_states:
        nl = file_nl(text)
        oldn = to_nl(old, nl)
        # insert hide as first property
        first_prop = "      ParticleSysBone"
        idx = oldn.find(first_prop)
        newn = oldn[:idx] + to_nl(hide_line, nl) + oldn[idx:]
        if text.count(oldn) != 1:
            raise SystemExit(f"F35 fly state unique miss: {oldn[:80]!r} count={text.count(oldn)}")
        text = text.replace(oldn, newn, 1)

    damaged = [
        """    ConditionState        = REALLYDAMAGED
      Model               = AVLightn_D
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
    End""",
        """    ConditionState        = REALLYDAMAGED JETEXHAUST
      Model               = AVLightn_D
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End""",
        """    ConditionState        = REALLYDAMAGED JETEXHAUST JETAFTERBURNER
      Model               = AVLightn_D
      ParticleSysBone     = Engine01 JetEngineDamagedSmoke
      ParticleSysBone     = Engine01 JetLenzflare
      ParticleSysBone     = Wingtip01 JetContrail
      ParticleSysBone     = Wingtip02 JetContrail
    End""",
    ]
    for old in damaged:
        add_hide_after_model(old, "F35 damaged")

    text = must_replace_all(
        text,
        "      HideSubObject       = None \n",
        f"      HideSubObject       = {F35_HIDE}\n",
        "F35 rubble HideSubObject None",
        expected=2,
    )
    text = must_replace_once(
        text,
        "  Geometry = Cylinder\n",
        "  Geometry = Box\n",
        "F35 geometry cylinder->box",
    )
    return text


def patch_starlifter(text: str) -> str:
    # Keep Draw / name / portraits / USA ownership. Replace C17-only gameplay
    # with the live RussiaJetAn124 transport architecture.
    text = must_replace_once(
        text,
        "  CommandSet = AmericaC17StarlifterCommandSet\n",
        "  CommandSet = C17GlobalMasterCommandSet\n",
        "C17 CommandSet",
    )
    text = must_replace_once(
        text,
        "    MaxHealth = 500.0\n    InitialHealth = 500.0\n",
        "    MaxHealth = 550.0\n    InitialHealth = 550.0\n",
        "C17 body",
    )
    text = must_replace_once(
        text,
        "    Mass = 500.0\n",
        "    Mass = 900.0\n",
        "C17 mass",
    )
    text = must_replace_once(
        text,
        """  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 5
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 20000
    TakeoffPause = 500
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End""",
        """  Behavior = JetAIUpdate ModuleTag_09
    KeepsParkingSpaceWhenAirborne = Yes
    MinHeight = 1
    NeedsRunway = Yes
    OutOfAmmoDamagePerSecond = 0%
    ReturnToBaseIdleTime = 10000
    TakeoffPause = 1000
    TakeoffDistForMaxLift = 0%
    AutoAcquireEnemiesWhenIdle = No
    ParkingOffset = 5
  End""",
        "C17 JetAI",
    )
    def strip_block(start_pat: str, label: str) -> None:
        nonlocal text
        m = re.search(start_pat, text)
        if not m:
            raise SystemExit(f"{label}: start not found")
        start = m.start()
        end = text.find("\n  End", start)
        if end < 0:
            raise SystemExit(f"{label}: End not found")
        end = text.find("\n", end + 1)
        if end < 0:
            end = len(text)
        else:
            end += 1
        text = text[:start] + text[end:]

    strip_block(r"  ; Ground-targeted safe unload[\s\S]*?Behavior = OCLSpecialPower ModuleTag_C17SafeUnload", "C17 OCL")
    strip_block(r"  ; Cargo is onboard from spawn[\s\S]*?Behavior = TransportContain ModuleTag_StarlifterCargo", "C17 old contain")
    strip_block(r"  ; 3 small airborne escorts[\s\S]*?Behavior = SpawnBehavior ModuleTag_C17AirEscorts", "C17 spawn")
    # Insert An-124 TransportContain before Geometry
    geo = re.search(r"\r?\n  Geometry = Box", text)
    if not geo:
        raise SystemExit("C17 geometry marker missing")
    insert = to_nl(
        "\n  Behavior = TransportContain ModuleTag_StarlifterCargo\n"
        "    Slots                 = 64\n"
        "    DamagePercentToUnits  = 100%\n"
        "    AllowInsideKindOf     = INFANTRY VEHICLE\n"
        "    ForbidInsideKindOf    = AIRCRAFT HUGE_VEHICLE\n"
        "    ExitDelay             = 100\n"
        "    NumberOfExitPaths     = 1\n"
        "  End\n",
        file_nl(text),
    )
    text = text[: geo.start()] + insert + text[geo.start() :]
    text = must_replace_once(
        text,
        """  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 40.0
  GeometryMinorRadius = 10.0
  GeometryHeight = 10.0""",
        """  Geometry = Box
  GeometryIsSmall = No
  GeometryMajorRadius = 48.0
  GeometryMinorRadius = 14.0
  GeometryHeight = 12.0""",
        "C17 geometry",
    )
    if "IUAC17HXNew" not in text:
        raise SystemExit("Starlifter visual model missing after patch")
    if "C17GlobalMaster" not in text:
        raise SystemExit("Starlifter portrait missing after patch")
    if "OBJECT:Starlifter" not in text:
        raise SystemExit("Starlifter display name missing after patch")
    if "OCLSpecialPower" in text or "SpawnBehavior" in text or "InitialPayload" in text:
        raise SystemExit("Starlifter still has C17-only gameplay modules")
    if "C17GlobalMasterCommandSet" not in text:
        raise SystemExit("Starlifter missing An-124 CommandSet")
    return text


def patch_airfield(text: str) -> str:
    return must_replace_once(
        text,
        "  CommandSet          = AmericaAirfieldCommandSet\n",
        "  CommandSet          = AmericaAirfieldCommandSet_USA01\n",
        "Airfield CommandSet unique",
    )


def patch_large(text: str) -> str:
    return must_replace_once(
        text,
        "  CommandSet          = America_LargeAirBaseCommandSet\n",
        "  CommandSet          = America_LargeAirBaseCommandSet_USA01\n",
        "LargeAirBase CommandSet unique",
    )


def donor_art_entries() -> list[tuple[str, bytes]]:
    mapping = {
        "LSFAH1Z.W3D": r"Art\W3D\LSFAH1Z.W3D",
        "LSFAH1Zd.W3D": r"Art\W3D\LSFAH1Zd.W3D",
        "LSFAH1Zk.W3D": r"Art\W3D\LSFAH1Zk.W3D",
        "LSFAH1ZAIM9.W3D": r"Art\W3D\LSFAH1ZAIM9.W3D",
        "LSFAH1Z.dds": r"Art\Textures\LSFAH1Z.dds",
        "LSFAH1Zd.dds": r"Art\Textures\LSFAH1Zd.dds",
        "LSFAH1Zk.dds": r"Art\Textures\LSFAH1Zk.dds",
        "AH1ZTB.tga": r"Art\Textures\AH1ZTB.tga",
    }
    out = []
    for src, dest in mapping.items():
        p = DONOR_DIR / src
        if not p.is_file():
            raise SystemExit(f"missing donor ART {p}")
        out.append((dest, p.read_bytes()))
    return out


def sha(p: Path | bytes) -> str:
    if isinstance(p, bytes):
        return hashlib.sha256(p).hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main() -> int:
    print("Reading DATA BIG...")
    data_orig = read_big_list(SRC_DATA)
    data = list(data_orig)
    print("Reading ART BIG...")
    art_orig = read_big_list(SRC_ART)
    art = list(art_orig)

    baseline_data_sha = sha(SRC_DATA)
    baseline_art_sha = sha(SRC_ART)
    if baseline_data_sha != "7eab1a6d80cd059050b6b186ad420863110a7a5c11162d1c89a6b4ed2957e7a8":
        raise SystemExit(f"DATA baseline SHA mismatch: {baseline_data_sha}")
    if baseline_art_sha != "2eb2ff5bc4a762aa44702ecfbd67c7e21f9986c0026fcc3fccb85ea62a8bb761":
        raise SystemExit(f"ART baseline SHA mismatch: {baseline_art_sha}")

    # DATA edits
    set_text(data, P_F117, patch_f117(text_of(data, P_F117)))
    set_text(data, P_EA6, patch_ea6(text_of(data, P_EA6)))
    set_text(data, P_F35, patch_f35(text_of(data, P_F35)))
    set_text(data, P_C17, patch_starlifter(text_of(data, P_C17)))
    set_text(data, P_AIRFIELD, patch_airfield(text_of(data, P_AIRFIELD)))
    set_text(data, P_LARGE, patch_large(text_of(data, P_LARGE)))
    set_bytes(
        data,
        P_CSF,
        csf_append(
            bytes_of(data, P_CSF),
            {
                "OBJECT:AmericaHelicopterAH1Z": "AH-1Z Viper",
                "CONTROLBAR:ConstructAmericaHelicopterAH1Z": "AH-1Z Viper",
                "CONTROLBAR:ToolTipAmericaHelicopterAH1Z": (
                    "AH-1Z Viper attack helicopter\n"
                    "20mm turret gun, Hellfire missiles, Hydra rockets\n"
                    "strong vs. infantry, tanks, vehicles\n"
                    "weak vs. MANPADS, aircraft"
                ),
            },
        ),
    )

    # New unique DATA paths (appended; original order preserved)
    existing = {norm(n).lower() for n, _ in data}
    for dest, blob in (
        (P_AH1Z, to_nl(AH1Z_INI, "\r\n").encode("utf-8")),
        (P_USA01, to_nl(USA01_INI, "\r\n").encode("utf-8")),
    ):
        if norm(dest).lower() in existing:
            raise SystemExit(f"path already packed: {dest}")
        data.append((dest, blob))

    # ART: original SPECTER1 + donor AH-1Z only. Do not rebuild unrelated ART.
    art_existing = {norm(n).lower() for n, _ in art}
    donor_art = donor_art_entries()
    for dest, blob in donor_art:
        if norm(dest).lower() in art_existing:
            raise SystemExit(f"ART path already packed: {dest}")
        art.append((dest, blob))

    # Validate An-124 untouched
    an124_i = find_index(data, P_AN124)
    if data[an124_i][1] != data_orig[find_index(data_orig, P_AN124)][1]:
        raise SystemExit("Russia An-124 was modified")

    # CommandSet.ini / CommandButton.ini untouched
    if bytes_of(data, P_CMDSET) != bytes_of(data_orig, P_CMDSET):
        raise SystemExit("CommandSet.ini was modified")
    if bytes_of(data, P_CMDBTN) != bytes_of(data_orig, P_CMDBTN):
        raise SystemExit("CommandButton.ini was modified")

    # Airbase architecture (parking bones / models) unchanged except CommandSet pointer
    heavy_i = find_index(data, P_HEAVY)
    if data[heavy_i][1] != data_orig[find_index(data_orig, P_HEAVY)][1]:
        raise SystemExit("HeavyAirBase was modified")

    for p in IRAQ_PROTECTED:
        if bytes_of(data, p) != bytes_of(data_orig, p):
            raise SystemExit(f"protected Iraq/follow-up path changed: {p}")

    orig_names = [n for n, _ in data_orig]
    new_names = [n for n, _ in data]
    if new_names[: len(orig_names)] != orig_names:
        raise SystemExit("DATA packed path order does not preserve original order")
    art_orig_names = [n for n, _ in art_orig]
    art_new_names = [n for n, _ in art]
    if art_new_names[: len(art_orig_names)] != art_orig_names:
        raise SystemExit("ART packed path order does not preserve original order")

    def changed_paths(orig, new):
        om = {norm(n).lower(): (n, b) for n, b in orig}
        nm = {norm(n).lower(): (n, b) for n, b in new}
        changed = []
        added = []
        for k, (n, b) in nm.items():
            if k not in om:
                added.append(n)
            elif om[k][1] != b:
                changed.append(n)
        missing = [om[k][0] for k in om if k not in nm]
        return changed, added, missing

    d_changed, d_added, d_missing = changed_paths(data_orig, data)
    a_changed, a_added, a_missing = changed_paths(art_orig, art)
    if d_missing or a_missing:
        raise SystemExit(f"missing packed paths DATA={d_missing} ART={a_missing}")

    allowed_data = {
        norm(p).lower()
        for p in (P_F117, P_EA6, P_F35, P_C17, P_AIRFIELD, P_LARGE, P_CSF, P_AH1Z, P_USA01)
    }
    unrelated = []
    for p in d_changed + d_added:
        pl = norm(p).lower()
        if pl not in allowed_data:
            # ignore only if USA path we intended
            unrelated.append(p)
    if unrelated:
        raise SystemExit(f"unrelated DATA path changes: {unrelated}")

    # Content checks
    f117 = text_of(data, P_F117)
    if not re.search(r"^Scale = 1\.04\s*$", f117, re.M):
        raise SystemExit("F117 scale not 1.04")
    if "Scale = 0.9" in f117:
        raise SystemExit("F117 old scale still present")
    ea6 = text_of(data, P_EA6)
    if ea6.count("HideSubObject       = HOOK") < 8:
        raise SystemExit("EA6 HOOK hide missing")
    if "GeometryIsSmall       = Yes" in ea6:
        raise SystemExit("EA6 GeometryIsSmall still Yes")
    f35 = text_of(data, P_F35)
    if "Geometry = Cylinder" in f35:
        raise SystemExit("F35 still Cylinder")
    if "Geometry = Box" not in f35:
        raise SystemExit("F35 geometry not Box")
    if f35.count("JAFTERBURNED CYLINDER02 CYLINDER03 TURBO EX01 EX02") < 10:
        raise SystemExit("F35 hide subobjects incomplete")
    if "HideSubObject       = None" in f35:
        raise SystemExit("F35 still has HideSubObject None")
    c17 = text_of(data, P_C17)
    if "CommandSet = C17GlobalMasterCommandSet" not in c17:
        raise SystemExit("Starlifter CommandSet not An-124")
    if "Model = IUAC17HXNew" not in c17:
        raise SystemExit("Starlifter visual lost")
    airfield = text_of(data, P_AIRFIELD)
    if "AmericaAirfieldCommandSet_USA01" not in airfield:
        raise SystemExit("Airfield unique CommandSet missing")
    large = text_of(data, P_LARGE)
    if "America_LargeAirBaseCommandSet_USA01" not in large:
        raise SystemExit("LargeAirBase unique CommandSet missing")
    usa01 = text_of(data, P_USA01)
    if "Command_ConstructAmerica_AuterF22" in usa01 or "Command_ConstructAmericaJetAuterF22" in usa01:
        raise SystemExit("Strike Eagle still on unique CommandSets")
    if usa01.count("Command_ConstructAmericaHelicopterAH1Z") < 3:
        raise SystemExit("AH1Z button not placed on unique CommandSets")
    ah1z = text_of(data, P_AH1Z)
    if "Model                           = LSFAH1Z" not in ah1z:
        raise SystemExit("AH1Z model missing")
    if "OverlordContain" in ah1z or "ReplaceObjectUpgrade" in ah1z:
        raise SystemExit("AH1Z still has AH64E-only modules")
    if "Weapon.ini" in ah1z:
        raise SystemExit("AH1Z unexpectedly references donor Weapon.ini")

    # Unrelated country: no non-USA object paths besides An-124 (untouched) and CSF
    unrelated_country = []
    for p in d_changed:
        pl = p.replace("\\", "/").lower()
        if "/iraq army/" in pl or "/player" in pl:
            unrelated_country.append(p)
        if "russian" in pl:
            unrelated_country.append(p)
    if unrelated_country:
        raise SystemExit(f"unrelated country changed: {unrelated_country}")

    print("Packing DATA...")
    data_blob = build_big_ordered(data)
    print("Packing ART...")
    art_blob = build_big_ordered(art)

    packed_data = read_big_list.__wrapped__ if False else None  # keep lints quiet
    rt_data = read_big_list.__doc__
    # Round-trip via temp write
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    WS_OUT.mkdir(parents=True, exist_ok=True)
    data_path = OUT_DIR / "_SPEC_DATA_ONE.big"
    art_path = OUT_DIR / "_SPEC_ART_ONE.big"
    data_path.write_bytes(data_blob)
    art_path.write_bytes(art_blob)

    rt = read_big_list(data_path)
    if [n for n, _ in rt] != [n for n, _ in data]:
        raise SystemExit("DATA round-trip name mismatch")
    if text_of(rt, P_F117) != f117:
        raise SystemExit("DATA round-trip F117 mismatch")
    rt_art = read_big_list(art_path)
    if [n for n, _ in rt_art][: len(art_orig_names)] != art_orig_names:
        raise SystemExit("ART round-trip original order lost")
    if find_index(rt_art, r"Art\W3D\LSFAH1Z.W3D") < 0:
        raise SystemExit("ART missing LSFAH1Z")

    audit = f"""SPECTER1_USA_Update_01 audit
BASELINE_DATA = {SRC_DATA}
BASELINE_DATA_SHA256 = {baseline_data_sha}
BASELINE_DATA_BYTES = {SRC_DATA.stat().st_size}
BASELINE_ART = {SRC_ART}
BASELINE_ART_SHA256 = {baseline_art_sha}
BASELINE_ART_BYTES = {SRC_ART.stat().st_size}
NEW_DATA_SHA256 = {hashlib.sha256(data_blob).hexdigest()}
NEW_DATA_BYTES = {len(data_blob)}
NEW_DATA_FILE_COUNT = {len(data)}
NEW_ART_SHA256 = {hashlib.sha256(art_blob).hexdigest()}
NEW_ART_BYTES = {len(art_blob)}
NEW_ART_FILE_COUNT = {len(art)}

USA_F117_OBJECT = AmericaJetF117Clean
OLD_SCALE = 0.9
NEW_SCALE = 1.04
USA_F117_SCALE_CHANGED = YES

REMOVED_STRIKE_EAGLE_OBJECT = AmericaJetAuterF22
REMOVED_STRIKE_EAGLE_BUTTON = Command_ConstructAmericaJetAuterF22 (DATA LargeAirBase slot 14); Command_ConstructAmerica_AuterF22 (INIZHZ AmericaAirfield slot 6)
REMOVED_FROM_COMMANDSET = America_LargeAirBaseCommandSet_USA01 ; AmericaAirfieldCommandSet_USA01
REMOVED_SLOT = 14 (America_LargeAirBase) ; 6 (AmericaAirfield)
USA_STRIKE_EAGLE_1600_REMOVED_FROM_LIVE_BAR = YES
STRIKE_EAGLE_OBJECT_DELETED = NO

DONOR_HELICOPTER_SELECTED = AH-1Z Viper / Super Cobra (LSFAH1Z)
DONOR_ART_PATHS_IMPORTED =
{chr(10).join('  ' + n for n, _ in donor_art)}
DATA_SKELETON_USED = AmericaVehicleComanche (AH64D.ini) stripped of OverlordContain/ReplaceObjectUpgrade/ObjectCreationUpgrade
USA_HELICOPTER_OBJECT = AmericaHelicopterAH1Z
USA_HELICOPTER_BUTTON = Command_ConstructAmericaHelicopterAH1Z
USA_HELICOPTER_COMMANDSET = America_LargeAirBaseCommandSet_USA01 and AmericaAirfieldCommandSet_USA01
USA_HELICOPTER_SLOT = 14 (LargeAirBase) ; 6 (Airfield)
USA_NEW_DONOR_HELICOPTER_ADDED = YES
DONOR_DATA_IMPORTED = NO
DONOR_ART_USED = YES
DONOR_DATA_USED = NO

EA6B_OBJECT = AmericaJetF18Prowler
EA6B_ARTIFACT_ROOT_CAUSE = EA6.W3D subobject HOOK remains visible; SHADOW_VOLUME + GeometryIsSmall=Yes stretched that hook into a long line under the aircraft in flight. JetLenzflare/contrails are normal engine FX, not the shadow line. W3D mesh not rewritten.
EA6B_FILES_CHANGED = {P_EA6}
EA6B_LINE_ARTIFACT_FIX_APPLIED = YES
EA6B_ART_W3D_CHANGED = NO

F35B_OBJECT = AmericaJetF35BJSF
F35B_ARTIFACT_ROOT_CAUSE = AVLightn.W3D afterburner/cylinder subobjects (JAFTERBURNED, CYLINDER02, CYLINDER03, TURBO, EX01, EX02) were never hidden, and RUBBLE states set HideSubObject=None which shows them. Geometry=Cylinder + SHADOW_VOLUME + GeometryIsSmall=Yes casts a tube/line shadow while flying. W3D mesh not rewritten.
F35B_FILES_CHANGED = {P_F35}
F35B_LINE_ARTIFACT_FIX_APPLIED = YES
F35B_ART_W3D_CHANGED = NO

USA_STARLIFTER_OBJECT = AmericaJetC17Visual
RUSSIA_AN124_REFERENCE_OBJECT = RussiaJetAn124
AN124_FUNCTION_MODULES_COPIED = CommandSet C17GlobalMasterCommandSet; TransportContain Slots=64 DamagePercentToUnits=100% (no InitialPayload); JetAIUpdate MinHeight/TakeoffPause/ReturnToBaseIdleTime; Physics Mass=900; Body MaxHealth=550; Geometry 48/14/12; removed OCLSpecialPower SpecialPowerAmericaC17SafeUnload; removed SpawnBehavior Comanche escorts
STARLIFTER_VISUAL_PRESERVED = YES
USA_STARLIFTER_USES_AN124_FUNCTIONALITY = YES
RUSSIA_AN124_CHANGED = NO

USA_F117_SCALE_CHANGED = YES
PREVIOUS_IRAQ_CHANGES_PRESERVED = YES
AIRBASE_ARCHITECTURE_CHANGED = NO
UNRELATED_COUNTRY_CHANGED_PATH_COUNT = {len(unrelated_country)}
DATA_CHANGED = YES
ART_CHANGED = YES
INGAME_TESTED = NO

DATA_CHANGED_PATHS =
{chr(10).join('  ' + p for p in d_changed)}
DATA_ADDED_PATHS =
{chr(10).join('  ' + p for p in d_added)}
ART_CHANGED_PATHS =
{chr(10).join('  ' + p for p in a_changed) if a_changed else '  (none)'}
ART_ADDED_PATHS =
{chr(10).join('  ' + p for p in a_added)}
"""
    changelog = """SPECTER1_USA_Update_01

Baseline: SPECTER1_Iraq_Followup_Final DATA (SHA256 7eab1a6d80cd059050b6b186ad420863110a7a5c11162d1c89a6b4ed2957e7a8)
plus original SPECTER1 ART (SHA256 2eb2ff5bc4a762aa44702ecfbd67c7e21f9986c0026fcc3fccb85ea62a8bb761).

USA only. Previous Iraq/follow-up gameplay is packed unchanged.

1. AmericaJetF117Clean visual Scale 0.9 -> 1.04 (~+15%). Weapons/price/armor/locomotor/button/slot unchanged.
2. Removed F-15E Strike Eagle (AmericaJetAuterF22, BuildCost 1600) from the live USA production bars. Object definition kept. Unique CommandSets replace the AuterF22 construct button in the same slots.
3. Added AmericaHelicopterAH1Z (AH-1Z Viper) using donor LSFAH1Z ART and SPECTER1 AmericaVehicleComanche gameplay skeleton. Placed in the freed Strike Eagle slots. No donor DATA imported.
4. EA-6B (AmericaJetF18Prowler): hide EA6 HOOK subobject; GeometryIsSmall=No. Fixes the flying line-shadow from the arresting-hook volume shadow. Model file not rewritten.
5. F-35B JSF (AmericaJetF35BJSF): hide AVLightn afterburner/cylinder subobjects; Geometry Cylinder -> Box. Fixes the flying line-shadow. Model file not rewritten.
6. AmericaJetC17Visual keeps Starlifter model/name/portrait/USA slot, and now uses RussiaJetAn124 transport functionality (C17GlobalMasterCommandSet + Chinook-style TransportContain). An-124 itself unchanged.

Protected: Iraq Mirage/Su-24/L-159, drones, WarFactory, Alhussien, Tu-22, MiG-21/J-7, Large/Heavy AirBase parking architecture, other countries, PlayerTemplate.
"""
    (OUT_DIR / "audit.txt").write_text(audit, encoding="utf-8")
    (OUT_DIR / "changelog.txt").write_text(changelog, encoding="utf-8")
    (WS_OUT / "audit.txt").write_text(audit, encoding="utf-8")
    (WS_OUT / "changelog.txt").write_text(changelog, encoding="utf-8")
    # Do not copy 1.2GB BIGs into git; they go in the GitHub Release ZIP only.
    zip_path = OUT_DIR / "SPECTER1_USA_Update_01.zip"
    print("Writing ZIP...")
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_STORED) as zf:
        zf.write(data_path, "_SPEC_DATA_ONE.big")
        zf.write(art_path, "_SPEC_ART_ONE.big")
        zf.write(OUT_DIR / "audit.txt", "audit.txt")
        zf.write(OUT_DIR / "changelog.txt", "changelog.txt")
    print(audit)
    print("ZIP", zip_path, zip_path.stat().st_size)
    print("DATA", data_path, len(data_blob))
    print("ART", art_path, len(art_blob))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
